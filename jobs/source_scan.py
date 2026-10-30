"""Source & dependency scan — the automated part of a code review (runs after inventory).

For every app whose active deployment hasn't been scanned yet:
  1. export its source from the workspace (bounded: text files, size caps)
  2. dependencies (Python requirements.txt + Node package.json) → OSV.dev CVE lookup
     and a Dependabot-style per-package report: installed vs latest (PyPI / npm registry),
     how far behind (patch/minor/major), and known vulnerabilities
  3. secret patterns, config/code smells (regex), bandit static analysis
  4. repo hygiene metrics → 0–100 quality score
Results land in code_scans (one row per app+deployment; deps_json holds the per-package
report) and scan_findings (one row per finding); v_scan_latest / v_findings_latest expose
the newest scan per app.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ExportFormat, ObjectType
from pyspark.sql import SparkSession

TEXT_EXT = {
    ".py",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".md",
    ".toml",
    ".cfg",
    ".ini",
    ".sql",
    ".js",
    ".html",
    ".css",
    ".sh",
}
SKIP_DIRS = {
    "node_modules",
    ".venv",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    "assets",
}
MAX_FILE = 200_000
MAX_FILES = 400

SECRET_PATTERNS = [
    ("aws access key", r"AKIA[0-9A-Z]{16}", "critical"),
    ("private key material", r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "critical"),
    ("databricks PAT", r"dapi[0-9a-f]{32}", "critical"),
    (
        "hardcoded password/secret",
        r"(?i)(?:password|passwd|secret|api_key|token)\s*=\s*[\"'][^\"'\s]{6,}[\"']",
        "high",
    ),
]

SMELL_PATTERNS = [
    ("eval()/exec() usage", r"(?<![\w.])(?:eval|exec)\(", "high"),
    ("pickle deserialization", r"pickle\.loads?\(", "medium"),
    ("TLS verification disabled", r"verify\s*=\s*False", "high"),
    ("shell=True subprocess", r"shell\s*=\s*True", "medium"),
    ("debug mode flag", r"(?i)debug\s*=\s*True", "low"),
    ("weak hash (md5/sha1)", r"hashlib\.(md5|sha1)\(", "low"),
    ("bare except", r"\n\s*except\s*:\s*\n", "low"),
]

SEV_WEIGHT = {"critical": 25, "high": 10, "medium": 5, "low": 2}


def list_source_files(w: WorkspaceClient, root: str) -> list[str]:
    out: list[str] = []
    stack = [root]
    while stack and len(out) < MAX_FILES:
        path = stack.pop()
        try:
            for obj in w.workspace.list(path):
                base = obj.path.rsplit("/", 1)[-1]
                if obj.object_type == ObjectType.DIRECTORY and base not in SKIP_DIRS:
                    stack.append(obj.path)
                elif obj.object_type in (ObjectType.FILE, ObjectType.NOTEBOOK) and (
                    Path(base).suffix.lower() in TEXT_EXT or base == "requirements.txt"
                ):
                    out.append(obj.path)
        except Exception as e:  # noqa: BLE001
            print(f"  list {path}: {e}")
    return out[:MAX_FILES]


def read_file(w: WorkspaceClient, path: str) -> str:
    try:
        resp = w.workspace.export(path, format=ExportFormat.SOURCE)
        raw = base64.b64decode(resp.content or "")
        if len(raw) > MAX_FILE:
            return ""
        return raw.decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        print(f"  export {path}: {e}")
        return ""


def parse_requirements(text: str) -> list[tuple[str, str | None]]:
    deps = []
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9_.\-\[\]]+?)(?:\[[^\]]*\])?\s*==\s*([A-Za-z0-9_.\-]+)", line)
        if m:
            deps.append((m.group(1).lower(), m.group(2)))
        else:
            name = re.split(r"[<>=!~;\s]", line)[0].lower()
            if name:
                deps.append((name, None))
    return deps


def parse_package_json(text: str) -> list[tuple[str, str | None, str]]:
    """Node deps from package.json (dependencies + devDependencies) → (name, base_version, 'npm')."""
    try:
        pkg = json.loads(text)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for section in ("dependencies", "devDependencies"):
        for name, spec in (pkg.get(section) or {}).items():
            m = re.match(r"^[\^~>=\s]*(\d[\w.\-]*)", str(spec))  # ^1.2.3 / ~1.2.3 / 1.2.3 → 1.2.3
            out.append((name.lower(), m.group(1) if m else None, "npm"))
    return out


ECO = {"pypi": ("PyPI", "requirements.txt"), "npm": ("npm", "package.json")}


def osv_lookup(deps: list[tuple[str, str | None, str]]) -> tuple[list[dict], dict]:
    """Known vulnerabilities for pinned packages (both ecosystems) → findings + per-package id map."""
    pinned = [(n, v, e) for n, v, e in deps if v]
    if not pinned:
        return [], {}
    queries = [{"package": {"name": n, "ecosystem": ECO[e][0]}, "version": v} for n, v, e in pinned]
    try:
        r = httpx.post("https://api.osv.dev/v1/querybatch", json={"queries": queries}, timeout=30)
        r.raise_for_status()
        results = r.json().get("results", [])
    except Exception as e:  # noqa: BLE001
        print(f"  OSV lookup failed (offline?): {e}")
        return [], {}
    findings, vuln_map = [], {}
    for (name, version, eco), res in zip(pinned, results, strict=False):
        for v in (res or {}).get("vulns", []):
            sev = "high"
            for s in v.get("severity", []):
                try:  # CVSS score → bucket
                    score = (
                        float(s.get("score", "0").split("/")[0])
                        if s.get("score", "").replace(".", "").isdigit()
                        else 0
                    )
                except ValueError:
                    score = 0
                sev = (
                    "critical"
                    if score >= 9
                    else "high"
                    if score >= 7
                    else "medium"
                    if score >= 4
                    else sev
                )
            db_sev = (v.get("database_specific") or {}).get("severity", "")
            if isinstance(db_sev, str) and db_sev.lower() in SEV_WEIGHT:
                sev = db_sev.lower()
            vuln_map.setdefault((name, eco), []).append(v.get("id"))
            findings.append(
                {
                    "kind": "cve",
                    "severity": sev,
                    "title": f"{v.get('id')} in {name}=={version}",
                    "detail": (v.get("summary") or v.get("details") or "")[:400],
                    "file": ECO[eco][1],
                    "line": None,
                    "package": name,
                }
            )
    return findings, vuln_map


def regex_findings(files: dict[str, str]) -> list[dict]:
    findings = []
    for path, text in files.items():
        if not path.endswith((".py", ".yaml", ".yml", ".json", ".cfg", ".ini", ".toml", ".sh")):
            continue
        for title, pattern, sev in SECRET_PATTERNS:
            for m in re.finditer(pattern, text):
                line = text[: m.start()].count("\n") + 1
                import hashlib as _hl

                _fp = _hl.sha256(m.group(0).encode()).hexdigest()[:12]
                findings.append(
                    {
                        "kind": "secret",
                        "severity": sev,
                        "title": title,
                        # never persist the matched value (review P0.3) — fingerprint only
                        "detail": f"match redacted · sha256:{_fp}",
                        "file": path.rsplit("/files/", 1)[-1],
                        "line": line,
                        "package": None,
                    }
                )
        if path.endswith(".py"):
            for title, pattern, sev in SMELL_PATTERNS:
                for m in re.finditer(pattern, text):
                    line = text[: m.start()].count("\n") + 1
                    findings.append(
                        {
                            "kind": "smell",
                            "severity": sev,
                            "title": title,
                            "detail": text.splitlines()[line - 1].strip()[:120]
                            if line <= text.count("\n") + 1
                            else "",
                            "file": path.rsplit("/files/", 1)[-1],
                            "line": line,
                            "package": None,
                        }
                    )
    return findings


def bandit_findings(files: dict[str, str]) -> list[dict]:
    py = {p: c for p, c in files.items() if p.endswith(".py")}
    if not py:
        return []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for i, (path, content) in enumerate(py.items()):
                f = Path(tmp) / f"{i}__{path.rsplit('/', 1)[-1]}"
                f.write_text(content, encoding="utf-8")
                f.with_suffix(".map").write_text(path.rsplit("/files/", 1)[-1])
            proc = subprocess.run(
                [
                    "python",
                    "-m",
                    "bandit",
                    "-r",
                    tmp,
                    "-f",
                    "json",
                    "-q",
                    "--severity-level",
                    "medium",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            data = json.loads(proc.stdout or "{}")
        out = []
        for r in data.get("results", []):
            src = Path(r["filename"]).with_suffix(".map")
            real = src.read_text() if src.exists() else Path(r["filename"]).name
            out.append(
                {
                    "kind": "bandit",
                    "severity": r.get("issue_severity", "medium").lower(),
                    "title": f"{r.get('test_id')}: {r.get('test_name')}",
                    "detail": (r.get("issue_text") or "")[:200],
                    "file": real,
                    "line": r.get("line_number"),
                    "package": None,
                }
            )
        return out
    except Exception as e:  # noqa: BLE001
        print(f"  bandit failed: {e}")
        return []


def _ver_tuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3] or [0])


def policy_findings(deps: list[tuple[str, str | None, str]], policy_path: Path) -> list[dict]:
    """Org allow/deny list + minimum-version policy (jobs/policy.json)."""
    if not policy_path.exists():
        return []
    policy = json.loads(policy_path.read_text())
    deny = {d["package"].lower(): d["reason"] for d in policy.get("denylist", [])}
    min_v = {k.lower(): v for k, v in policy.get("min_versions", {}).items()}
    out = []
    for name, ver, eco in deps:
        if name in deny:
            out.append(
                {
                    "kind": "policy",
                    "severity": "high",
                    "title": f"denylisted package: {name}",
                    "detail": deny[name],
                    "file": ECO[eco][1],
                    "line": None,
                    "package": name,
                }
            )
        elif name in min_v and ver and _ver_tuple(ver) < _ver_tuple(min_v[name]):
            out.append(
                {
                    "kind": "policy",
                    "severity": "medium",
                    "title": f"{name}=={ver} below policy minimum {min_v[name]}",
                    "detail": "org min_versions policy (jobs/policy.json)",
                    "file": ECO[eco][1],
                    "line": None,
                    "package": name,
                }
            )
    return out


def _latest_version(name: str, eco: str) -> str | None:
    try:
        if eco == "npm":
            return httpx.get(f"https://registry.npmjs.org/{name}/latest", timeout=10).json()[
                "version"
            ]
        return httpx.get(f"https://pypi.org/pypi/{name}/json", timeout=10).json()["info"]["version"]
    except Exception:  # noqa: BLE001 — offline or unknown package
        return None


def dep_report(
    deps: list[tuple[str, str | None, str]], vuln_map: dict
) -> tuple[int | None, list[dict], list[dict]]:
    """Dependabot-style report: installed vs latest per package (PyPI/npm) →
    freshness score (0–100), findings for majors behind, and per-package report rows."""
    report, findings, fresh, stale = [], [], 0, 0
    for i, (name, ver, eco) in enumerate(deps):
        vulns = vuln_map.get((name, eco), [])
        row = {
            "name": name,
            "eco": eco,
            "version": ver,
            "latest": None,
            "behind": "unpinned" if not ver else "unknown",
            "vulns": vulns[:5],
        }
        # ponytail: cap registry lookups at 60 packages per app; the rest stay "unchecked"
        if i < 60:
            row["latest"] = _latest_version(name, eco)
        else:
            row["behind"] = "unchecked"
        if ver and row["latest"]:
            cur, new = _ver_tuple(ver), _ver_tuple(row["latest"])
            row["behind"] = (
                "current"
                if cur >= new
                else "major"
                if cur[0] < new[0]
                else "minor"
                if cur[:2] < new[:2]
                else "patch"
            )
            if row["behind"] in ("current", "patch"):
                fresh += 1
            else:
                stale += 1
            if row["behind"] == "major":
                findings.append(
                    {
                        "kind": "freshness",
                        "severity": "low",
                        "title": f"{name}=={ver} is a major version behind ({row['latest']})",
                        "detail": "dependency rot — plan the upgrade",
                        "file": ECO[eco][1],
                        "line": None,
                        "package": name,
                    }
                )
        report.append(row)
    total = fresh + stale
    return (round(100 * fresh / total) if total else None), findings, report


def quality_score(findings: list[dict], metrics: dict) -> int:
    score = 100
    seen_cap: dict[str, int] = {}
    for f in findings:
        cap_key = f["kind"]
        if seen_cap.get(cap_key, 0) >= 40:  # each category can cost at most 40 points
            continue
        w = SEV_WEIGHT.get(f["severity"], 2)
        seen_cap[cap_key] = seen_cap.get(cap_key, 0) + w
        score -= w
    if not metrics.get("has_pins"):
        score -= 5
    if not metrics.get("has_tests"):
        score -= 5
    if not metrics.get("has_readme"):
        score -= 2
    return max(0, min(100, score))


def emit_alerts(
    spark,
    catalog: str,
    schema: str,
    rows: list[dict],
    *,
    owned_rules: tuple[str, ...],
    evaluated_apps: set[str] | None = None,
    unknown_keys: set[tuple[str, str]] | None = None,
) -> None:
    """Persist transitions; partial scans can only clear apps they actually evaluated."""
    from alert_state import resolving_keys
    from schema_utils import ensure_columns, workspace_column

    try:
        # Jobs and the independently deployed app use the same pure matcher.
        jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
        if jobs_dir:
            sys.path.append(str(Path(jobs_dir).parent))
        from app.mutes import is_muted

        tbl = f"`{catalog}`.`{schema}`.alert_events"
        ws = str(WorkspaceClient().get_workspace_id())
        ensure_columns(spark, tbl, {"muted": "BOOLEAN", "incident_id": "STRING"})
        workspace_column(spark, tbl, ws)
        rules = ", ".join(f":rule{i}" for i in range(len(owned_rules)))
        if not owned_rules or any(r["rule"] not in owned_rules for r in rows):
            raise ValueError("every emitted rule must be owned by this caller")
        open_keys = {
            (r["rule"], r["app"])
            for r in spark.sql(
                f"""SELECT rule, app FROM (
                  SELECT rule, app, state, row_number() OVER (
                    PARTITION BY rule, app ORDER BY ts DESC, state DESC) rn
                  FROM {tbl} WHERE source = 'job' AND workspace_id = :ws
                    AND rule IN ({rules}))
                WHERE rn = 1 AND state = 'firing'""",
                args={"ws": ws, **{f"rule{i}": rule for i, rule in enumerate(owned_rules)}},
            ).collect()
        }
        rows = list({(r["rule"], r["app"]): r for r in rows}.values())
        current = {(r["rule"], r["app"]) for r in rows}
        transitions = [
            r
            for r in rows
            if (r["rule"], r["app"]) not in open_keys or r.get("state") == "resolved"
        ]
        transitions += [
            {
                "rule": rule,
                "app": app,
                "severity": "info",
                "message": "condition cleared",
                "value": 0.0,
                "state": "resolved",
            }
            for rule, app in sorted(resolving_keys(open_keys, current, owned_rules, evaluated_apps))
            if (rule, app) not in (unknown_keys or set())
        ]
        now = datetime.now(timezone.utc)
        mutes = [
            r.asDict() if hasattr(r, "asDict") else dict(r)
            for r in spark.sql(
                f"SELECT * FROM `{catalog}`.`{schema}`.alert_mutes "
                "WHERE workspace_id = :ws AND starts_at <= now() AND ends_at > now()",
                args={"ws": ws},
            ).collect()
        ]
        full = [
            {
                **r,
                "ts": now,
                "state": r.get("state", "firing"),
                "source": "job",
                "value": float(r.get("value") or 0),
                "workspace_id": ws,
                "muted": is_muted(r["app"], r["rule"], mutes, now),
                "incident_id": None,
            }
            for r in transitions
        ]
        if full:
            spark.createDataFrame(full, schema=spark.table(tbl).schema).write.mode(
                "append"
            ).saveAsTable(tbl)
        print(f"emitted {len(full)} alert transitions")
    except Exception as e:  # noqa: BLE001 — alerting must not fail the job
        print(f"alert emit failed: {e}")


DDL_SCANS = """
CREATE TABLE IF NOT EXISTS {fq}.code_scans (
  scanned_at TIMESTAMP, name STRING, deployment_id STRING, source_path STRING,
  quality_score INT, files INT, py_loc INT, deps INT, deps_pinned INT,
  findings_critical INT, findings_high INT, findings_medium INT, findings_low INT,
  has_tests BOOLEAN, has_readme BOOLEAN, deps_json STRING,
  freshness_score INT, policy_violations INT
) COMMENT 'Per-app source scan summary (monitor source-scan job)'"""

DDL_FINDINGS = """
CREATE TABLE IF NOT EXISTS {fq}.scan_findings (
  scanned_at TIMESTAMP, name STRING, deployment_id STRING,
  kind STRING, severity STRING, title STRING, detail STRING,
  file STRING, line INT, package STRING
) COMMENT 'Individual scan findings: cve | secret | smell | bandit'"""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--force", action="store_true", help="rescan even if deployment already scanned")
    p.add_argument("--jobs-dir", default="", help="workspace path of the jobs dir (policy.json)")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    spark.sql(DDL_SCANS.format(fq=fq))
    spark.sql(DDL_FINDINGS.format(fq=fq))
    try:  # columns added after first release
        spark.sql(
            f"ALTER TABLE {fq}.code_scans ADD COLUMNS (freshness_score INT, policy_violations INT)"
        )
    except Exception:  # noqa: BLE001 — already there
        pass

    scanned = (
        {
            (r["name"], r["deployment_id"])
            for r in spark.sql(
                f"SELECT DISTINCT name, deployment_id FROM {fq}.code_scans"
            ).collect()
        }
        if not args.force
        else set()
    )

    ts = datetime.now(timezone.utc)
    scan_rows, finding_rows = [], []

    for a in w.apps.list():
        dep = a.active_deployment
        src = dep.source_code_path if dep else None
        dep_id = dep.deployment_id if dep else None
        if not src:
            continue
        if (a.name, dep_id) in scanned:
            print(f"{a.name}: deployment {dep_id} already scanned")
            continue
        print(f"scanning {a.name} ({src})")
        paths = list_source_files(w, src)
        files = {p_: c for p_ in paths if (c := read_file(w, p_))}
        if not files:
            print("  no readable source")
            continue

        req_text = next((c for p_, c in files.items() if p_.endswith("requirements.txt")), "")
        pkg_text = next(
            (c for p_, c in files.items() if p_.rsplit("/", 1)[-1] == "package.json"), ""
        )
        deps = [(n, v, "pypi") for n, v in parse_requirements(req_text)] + parse_package_json(
            pkg_text
        )
        cve_findings, vuln_map = osv_lookup(deps)
        fresh_score, fresh_findings, deps_report = dep_report(deps, vuln_map)
        findings = (
            cve_findings
            + regex_findings(files)
            + bandit_findings(files)
            + policy_findings(deps, Path(args.jobs_dir or ".") / "policy.json")
            + fresh_findings
        )

        py_loc = sum(c.count("\n") + 1 for p_, c in files.items() if p_.endswith(".py"))
        metrics = {
            "has_pins": any(v for _, v, _ in deps),
            "has_tests": any(
                "/tests/" in p_ or p_.rsplit("/", 1)[-1].startswith("test_") for p_ in files
            ),
            "has_readme": any(p_.lower().endswith("readme.md") for p_ in files),
        }
        sev_count = {
            s: sum(1 for f in findings if f["severity"] == s)
            for s in ("critical", "high", "medium", "low")
        }
        score = quality_score(findings, metrics)
        npm_n = sum(1 for _, _, e in deps if e == "npm")
        print(
            f"  score {score} · {len(findings)} findings {sev_count} · {len(deps)} deps ({npm_n} npm) · {py_loc} loc"
        )

        scan_rows.append(
            {
                "scanned_at": ts,
                "name": a.name,
                "deployment_id": dep_id,
                "source_path": src,
                "quality_score": score,
                "files": len(files),
                "py_loc": py_loc,
                "deps": len(deps),
                "deps_pinned": sum(1 for _, v, _ in deps if v),
                "findings_critical": sev_count["critical"],
                "findings_high": sev_count["high"],
                "findings_medium": sev_count["medium"],
                "findings_low": sev_count["low"],
                "has_tests": metrics["has_tests"],
                "has_readme": metrics["has_readme"],
                "deps_json": json.dumps(deps_report),
                "freshness_score": fresh_score,
                "policy_violations": sum(1 for f in findings if f["kind"] == "policy"),
            }
        )
        finding_rows += [
            {"scanned_at": ts, "name": a.name, "deployment_id": dep_id, **f} for f in findings
        ]

    if scan_rows:
        spark.createDataFrame(
            scan_rows, schema=spark.table(f"{args.catalog}.{args.schema}.code_scans").schema
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.code_scans")
    if finding_rows:
        spark.createDataFrame(
            finding_rows, schema=spark.table(f"{args.catalog}.{args.schema}.scan_findings").schema
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.scan_findings")

    emit_alerts(
        spark,
        args.catalog,
        args.schema,
        [
            {
                "rule": "critical_findings",
                "app": r["name"],
                "severity": "critical",
                "message": f"source scan: {r['findings_critical']} critical, {r['findings_high']} high findings (score {r['quality_score']})",
                "value": r["findings_critical"],
            }
            for r in scan_rows
            if r["findings_critical"] > 0
        ],
        owned_rules=("critical_findings",),
        evaluated_apps={r["name"] for r in scan_rows},
    )

    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_scan_latest
        COMMENT 'Latest source scan per app' AS
        SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY name ORDER BY scanned_at DESC) rn
                       FROM {fq}.code_scans) WHERE rn = 1""")
    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_findings_latest
        COMMENT 'Findings of the latest scan per app' AS
        SELECT f.* FROM {fq}.scan_findings f
        JOIN {fq}.v_scan_latest s ON f.name = s.name AND f.scanned_at = s.scanned_at""")
    print(f"done: {len(scan_rows)} apps scanned, {len(finding_rows)} findings")


if __name__ == "__main__":
    import sys

    # Serverless script tasks do not set __file__; the bundle provides the helper path.
    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
