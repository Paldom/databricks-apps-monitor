"""Workspace-qualified declared/runtime graph; unknown resource health stays unknown."""

import json
from urllib.parse import urlsplit


def resources(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def binding(resource):
    for kind, spec in resource.items():
        if kind == "name" or not isinstance(spec, dict):
            continue
        if kind == "secret":
            target = spec.get("scope") or spec.get("scope_name")
        elif kind == "postgres":
            target = spec.get("database") or spec.get("branch")
        else:
            target = next(
                (
                    spec[k]
                    for k in (
                        "name",
                        "securable_full_name",
                        "instance_name",
                        "id",
                        "job_id",
                        "experiment_id",
                        "url",
                        "host",
                    )
                    if spec.get(k)
                ),
                None,
            )
        return kind, str(target or resource.get("name") or "Unknown binding")
    return None


def _number(value):
    try:
        n = float(value)
        return n if 0 <= n < float("inf") else None
    except (TypeError, ValueError):
        return None


def _host(value):
    """A URL identifies an app across workspaces; an unqualified name does not."""
    value = str(value or "").strip()
    try:
        return urlsplit(value if "://" in value else "//" + value).hostname
    except ValueError:
        return None


def graph(apps, observed):
    nodes, edges, aliases, measurements = {}, {}, {}, {}
    hosts = {}
    workspaces = {
        str(a.get("workspace_id") or ""): a["workspace"] for a in apps if a.get("workspace")
    }
    for a in apps:
        ws = str(a.get("workspace_id") or "")
        node_id = "app:" + a["id"]
        nodes[node_id] = {
            "id": node_id,
            "app": a["id"],
            "label": a["name"],
            "type": "app",
            "workspace_id": ws,
            "workspace": a.get("workspace") or ws or "Unknown workspace",
            "health": a.get("health"),
        }
        aliases[(ws, a["name"])] = node_id
        host = _host(a.get("url"))
        if host:
            hosts.setdefault(host, set()).add(node_id)

    def app_target(ws, name, *urls):
        target = aliases.get((ws, name))
        if target:
            return target
        for value in (*urls, name):
            candidates = hosts.get(_host(value), set())
            if len(candidates) == 1:
                return next(iter(candidates))
        return None

    def resource_node(target, ws, kind, label):
        nodes.setdefault(
            target,
            {
                "id": target,
                "label": label,
                "type": kind,
                "workspace_id": ws,
                "workspace": workspaces.get(ws) or ws or "Unknown workspace",
                "health": None,
            },
        )

    def edge(source, target, evidence):
        result = edges.setdefault(
            (source, target),
            {
                "source": source,
                "target": target,
                "declared": False,
                "observed": False,
                "calls": None,
                "errors": None,
                "avg_ms": None,
                "p95_ms": None,
                "error_pct": None,
                "bindings": [],
                "peers": [],
            },
        )
        result[evidence] = True
        return result

    for a in apps:
        ws = str(a.get("workspace_id") or "")
        for r in resources(a.get("resources")):
            pair = binding(r)
            if not pair:
                continue
            kind, label = pair
            spec = r[kind]
            target_ws = str(spec.get("workspace_id") or ws)
            target = (
                app_target(target_ws, label, spec.get("url"), spec.get("host"))
                if kind == "app"
                else None
            )
            target = target or f"resource:{target_ws}:{kind}:{label}"
            resource_node(target, target_ws, kind, label)
            bindings = edge("app:" + a["id"], target, "declared")["bindings"]
            if r not in bindings:
                bindings.append(r)
            # Use typed aliases: a warehouse and endpoint can share a display name.
            aliases[(ws, kind, label)] = target
            if kind == "sql_warehouse":
                aliases[(ws, "databricks_sql/" + label)] = target
            if kind in ("database", "postgres"):
                aliases[(ws, "postgresql/" + label)] = target

    for row in observed:
        ws = str(row.get("workspace_id") or "")
        source = aliases.get((ws, row.get("name")))
        if not source:
            continue
        peer = str(row.get("dependency") or "").strip()
        if not peer:
            continue
        target = aliases.get((ws, peer)) or app_target(ws, peer)
        kind, label = "external", peer
        if peer.startswith(("databricks_sql/", "databricks/")):
            kind, label = "sql_warehouse", peer.split("/", 1)[1]
        elif "/serving-endpoints/" in peer:
            kind, label = (
                "serving_endpoint",
                peer.split("/serving-endpoints/", 1)[1].split("/", 1)[0],
            )
        elif peer.startswith("serving_endpoint/"):
            kind, label = "serving_endpoint", peer.split("/", 1)[1]
        elif peer.startswith(("postgresql/", "postgres/")):
            kind, label = "database", peer.split("/", 1)[1]
        elif "://" in peer:
            label = _host(peer) or peer
            target = target or app_target(ws, label)
        target = target or aliases.get((ws, kind, label)) or f"resource:{ws}:{kind}:{label}"
        resource_node(target, ws, kind, label)
        e = edge(source, target, "observed")
        if peer not in e["peers"]:
            e["peers"].append(peer)
        calls, errors, avg, p95 = (
            _number(row.get(k)) for k in ("calls", "errors", "avg_ms", "p95_ms")
        )
        measurements.setdefault((source, target), []).append((calls, errors, avg, p95))
    for key, samples in measurements.items():
        e = edges[key]
        calls, errors, averages, percentiles = zip(*samples, strict=True)
        e["calls"] = sum(calls) if all(n is not None for n in calls) else None
        e["errors"] = sum(errors) if all(n is not None for n in errors) else None
        e["avg_ms"] = (
            sum(c * a for c, a in zip(calls, averages, strict=True) if c) / e["calls"]
            if e["calls"] and all(a is not None or c == 0 for c, _, a, _ in samples)
            else None
        )
        e["p95_ms"] = max((p for p in percentiles if p is not None), default=None)
        e["error_pct"] = (
            100 * e["errors"] / e["calls"]
            if e["calls"] and e["errors"] is not None and e["errors"] <= e["calls"]
            else None
        )
    for node in nodes.values():
        node["dependents"] = sorted(
            {e["source"] for e in edges.values() if e["target"] == node["id"]}
        )
    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "period": "7 days",
        "latency_basis": "Worst daily p95 (not a combined 7-day percentile)",
    }
