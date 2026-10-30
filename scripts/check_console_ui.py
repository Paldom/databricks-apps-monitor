"""Offline Python Playwright audit. Optional package root reuses an installed browser tool."""

from __future__ import annotations

import argparse
import functools
import json
import re
import sys
import threading
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def navigate(page, path):
    page.evaluate("hash=>location.hash=hash", path)
    page.wait_for_timeout(60)
    page.wait_for_function("!document.querySelector('#main .skeleton')")


def assert_readable(page, path):
    text = page.locator("body").inner_text()
    assert not re.search(r"^\s*[{\[]", text, re.MULTILINE), (path, "Raw record", text)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", text), (path, "ISO timestamp", text)
    assert "file://" not in text, (path, "Local file URL")
    assert not page.locator(".chart text").count(), (path, "SVG-scaled chart text")
    assert page.locator(".chart-y").evaluate_all(
        "es=>es.every(e=>parseFloat(getComputedStyle(e).fontSize)<=12)"
    ), (path, "Oversized axis labels")
    labels = page.locator("th,dt,h2,h3").all_inner_texts()
    assert not any(re.search(r"[a-z]_[a-z]", label) for label in labels), (path, labels)


def assert_palette(page):
    ratios = page.evaluate("""() => {
      const style=getComputedStyle(document.documentElement);
      const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d',{willReadFrequently:true});
      const luminance=name=>{
        ctx.fillStyle=style.getPropertyValue('--color-'+name);ctx.fillRect(0,0,1,1);
        const rgb=[...ctx.getImageData(0,0,1,1).data].slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
        return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
      };
      const pairs=['paper','surface','wash','sidebar'].flatMap(bg=>['ink','body','muted','accent'].map(fg=>[fg,bg,4.5]));
      pairs.push(['success','success-soft',4.5],['warning','warning-soft',4.5],['danger','danger-soft',4.5],['accent','accent-soft',4.5],['accent-ink','accent',4.5],['on-dark','graphite',4.5],['dark-muted','graphite',4.5],['focus','paper',3],['control','surface',3]);
      return pairs.map(([fg,bg,minimum])=>{const a=luminance(fg),b=luminance(bg);return {fg,bg,minimum,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};});
    }""")
    assert all(r["ratio"] >= r["minimum"] for r in ratios), ratios
    return ratios


def submit(page, form, values):
    editor = page.locator(f'[data-editor="{form}"]')
    for name, value in values.items():
        editor.locator(f'[name="{name}"]').fill(value)
    editor.locator('button[type="submit"]').click()
    page.wait_for_function(
        "document.querySelector('#action-status').textContent.includes('Demo action simulated')"
    )
    page.wait_for_function("!document.querySelector('#main .skeleton')")


def demo_interactions(page, base, artifacts):
    page.goto(base)
    page.wait_for_function("window.ConsoleApp !== undefined")
    page.evaluate("""() => {
      window.demoReads=[]; window.demoWrites=[];
      const get=ConsoleData.get, write=ConsoleData.write;
      ConsoleData.get=path=>{demoReads.push(path);return get(path)};
      ConsoleData.write=(path,method,body)=>{demoWrites.push({path,method,body});return write(path,method,body)};
    }""")
    navigate(page, "#/app/claims-assistant/logs")
    assert page.evaluate("demoReads.some(p=>p.includes('/logs'))")
    assert not page.evaluate("demoReads.some(p=>p.includes('/security'))")
    page.locator('[data-filter="logsSeverity"]').select_option("ERROR")
    assert page.get_by_role("table", name="Log records").locator("tbody tr").count() > 0
    navigate(page, "#/app/claims-assistant/traffic")
    navigate(page, "#/app/claims-assistant/logs")
    assert page.evaluate("demoReads.filter(p=>p.includes('/logs')).length") == 1
    page.evaluate("ConsoleApp.refresh(window.MOCK)")
    page.wait_for_function("demoReads.filter(p=>p.includes('/logs')).length===2")
    assert page.evaluate("demoReads.filter(p=>p.includes('/requests')).length") == 1
    assert page.locator('[data-filter="logsSeverity"]').input_value() == "ERROR"

    navigate(page, "#/app/claims-assistant/operate")
    page.locator('[data-editor="config"] [name="team"]').fill("Draft team")
    page.evaluate("ConsoleApp.refresh(window.MOCK)")
    page.wait_for_timeout(100)
    assert page.locator('[data-editor="config"] [name="team"]').input_value() == "Draft team"
    submit(page, "config", {"budget_usd_month": "123", "idle_hours": "9"})
    assert (
        page.evaluate("CONSOLE_FIXTURES['api/apps/claims-assistant/ops'].config.budget_usd_month")
        == 123
    )
    assert (
        page.evaluate(
            "JSON.parse(CONSOLE_FIXTURES['api/apps/claims-assistant/ops'].config.tags_json).team"
        )
        == "Draft team"
    )
    before = page.evaluate("demoWrites.length")
    page.get_by_role("button", name="Stop app", exact=True).click()
    assert page.get_by_role("alertdialog").is_visible()
    assert page.evaluate("demoWrites.length") == before
    page.get_by_role("button", name="Cancel", exact=True).click()
    assert page.evaluate("demoWrites.length") == before
    page.get_by_role("button", name="Stop app", exact=True).click()
    page.get_by_role("button", name="Confirm", exact=True).click()
    page.wait_for_function("demoWrites.some(x=>x.path.endsWith('/stop'))")
    page.wait_for_timeout(80)
    page.get_by_role("button", name="Restart app", exact=True).click()
    page.get_by_role("button", name="Confirm", exact=True).click()
    page.wait_for_function("demoWrites.some(x=>x.path.endsWith('/restart'))")
    page.wait_for_timeout(80)
    page.get_by_role("button", name="Run capacity · 1→8 concurrent").click()
    page.wait_for_selector('table[aria-label="Capacity results"]')
    assert page.get_by_role("table", name="Capacity results").locator("tbody tr").count() == 4
    page.get_by_text("Add or update an objective", exact=True).click()
    submit(page, "slo", {"slo": "browser-audit", "target": "0.99"})
    assert page.evaluate(
        "CONSOLE_FIXTURES['api/apps/claims-assistant/slo'].specs.some(s=>s.slo==='browser-audit')"
    )
    submit(page, "mute", {"reason": "Browser audit maintenance"})
    assert page.evaluate(
        "CONSOLE_FIXTURES['api/actions/mute'].mutes.some(m=>m.reason==='Browser audit maintenance')"
    )
    row = page.get_by_role("row").filter(has_text="Browser audit maintenance")
    row.get_by_role("button", name="Unmute").click()
    page.wait_for_function(
        "!CONSOLE_FIXTURES['api/actions/mute'].mutes.some(m=>m.reason==='Browser audit maintenance')"
    )

    navigate(page, "#/app/claims-assistant/product")
    submit(page, "product-settings", {"outcome_event": "done", "token_budget_day": "512"})
    assert (
        page.evaluate(
            "CONSOLE_FIXTURES['api/apps/claims-assistant/product-config'].token_budget_day"
        )
        == 512
    )
    page.get_by_text("Configure a funnel", exact=True).click()
    submit(page, "funnel", {"funnel": "browser audit", "steps": "start,finish"})
    assert page.evaluate(
        "CONSOLE_FIXTURES['api/apps/claims-assistant/funnels'].specs.some(f=>f.funnel==='browser audit')"
    )

    navigate(page, "#/app/claims-assistant/traces")
    page.get_by_role("table", name="MLflow traces").locator("tbody a").first.click()
    page.wait_for_selector(".agent-span")
    assert page.locator(".span-track").count() > 0
    assert page.get_by_role("link", name="Open in MLflow").count() == 1
    navigate(page, "#/app/claims-assistant/traces")
    page.get_by_role("table", name="Request traces").locator("tbody a").first.click()
    page.wait_for_selector(".waterfall")
    assert page.locator("[data-span]").count() > 0

    navigate(page, "#/governance")
    with page.expect_download() as download:
        page.get_by_role("button", name="Export compliance .md").click()
    target = artifacts / "compliance-report.md"
    download.value.save_as(target)
    assert "claims-assistant" in target.read_text()
    submit(
        page,
        "prices",
        {
            "model": "audit-model",
            "effective_from": "2026-10-30",
            "input_usd_per_mtok": "0",
            "output_usd_per_mtok": "2",
        },
    )
    assert page.evaluate(
        "CONSOLE_FIXTURES['api/model-prices'].prices.some(p=>p.model==='audit-model'&&p.input_usd_per_mtok===0)"
    )
    page.get_by_text("Fleet auto-stop policy", exact=True).click()
    page.get_by_role("button", name="Preview", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#action-status').textContent.includes('Preview:')"
    )
    page.get_by_role("button", name="Apply previewed rule").click()
    page.get_by_role("button", name="Confirm", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#action-status').textContent.includes('Applied to')"
    )
    page.get_by_text("Create app from the monitored template", exact=True).click()
    submit(
        page, "provision", {"app_name": "demo-browser-audit", "team": "QA", "cost_center": "TEST"}
    )
    assert page.evaluate("demoWrites.some(w=>w.path==='api/actions/provision')")
    page.goto(base + "&readonly=1#/app/claims-assistant/operate")
    page.wait_for_selector('[data-editor="config"]')
    assert page.get_by_role("button", name="Stop app", exact=True).is_disabled()
    assert page.locator('[data-editor="config"] [name="team"]').is_disabled()
    assert page.get_by_text("This monitor is read-only for your account.", exact=False).count() > 0


def live_transport(context, base):
    """Same HTTP paths as production, fulfilled locally; no workspace calls."""
    data = json.loads(
        (ROOT / "app/static/console/demo-data.js")
        .read_text()
        .removeprefix("window.MOCK = ")
        .strip()
        .removesuffix(";")
    )
    fixtures = json.loads(
        (ROOT / "app/static/console/demo-fixtures.js")
        .read_text()
        .removeprefix("window.CONSOLE_FIXTURES = ")
        .strip()
        .removesuffix(";")
    )
    counts, failures, writes, errors = Counter(), set(), [], []
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))

    def handle(route):
        path = urlsplit(route.request.url).path.removeprefix("/prefix/")
        if path.startswith("api/"):
            counts[path] += 1
            if path in failures:
                route.fulfill(status=503, json={"detail": "Audit source unavailable"})
            elif route.request.method != "GET":
                writes.append((path, route.request.method, route.request.post_data_json))
                route.fulfill(json={"ok": True})
            else:
                payload = data if path == "api/console/snapshot" else fixtures.get(path)
                route.fulfill(status=200 if payload is not None else 404, json=payload or {})
        else:
            route.fulfill(path=str(ROOT / "app/static" / path))

    page.route("**/prefix/**", handle)
    origin = base.split("/console/")[0]
    page.goto(origin + "/prefix/console/index.html#/app/claims-assistant/logs")
    page.wait_for_selector('table[aria-label="Log records"]')
    path = "api/apps/claims-assistant/logs"
    assert counts[path] == 1
    navigate(page, "#/app/claims-assistant/traffic")
    navigate(page, "#/app/claims-assistant/logs")
    assert counts[path] == 1
    failures.add(path)
    page.evaluate("ConsoleData.retry()")
    page.wait_for_function(
        "document.querySelector('main').textContent.includes('Source unavailable')"
    )
    assert page.get_by_role("table", name="Log records").count() == 1
    assert counts["api/apps/claims-assistant/requests"] == 1
    failures.clear()
    page.get_by_role("button", name="Retry", exact=True).click()
    page.wait_for_function(
        "!document.querySelector('main').textContent.includes('Source unavailable')"
    )
    assert counts[path] == 3
    navigate(page, "#/app/claims-assistant/operate")
    page.get_by_role("button", name="Stop app", exact=True).click()
    assert not writes
    page.get_by_role("button", name="Confirm", exact=True).click()
    page.wait_for_timeout(100)
    assert writes[0][:2] == ("api/actions/appctl/claims-assistant/stop", "POST")
    page.evaluate("""() => {
      window.savedWrite=ConsoleData.write;
      ConsoleData.write=()=>Promise.reject(new Error(JSON.stringify([{type:'validation_error',msg:'Invalid request',loc:['body','target']}])))
    }""")
    page.get_by_role("button", name="Start app", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#action-status').textContent.includes('Invalid request')"
    )
    assert_readable(page, "structured action validation")
    page.evaluate("() => {ConsoleData.write=window.savedWrite;}")
    fixtures["api/apps/claims-assistant/ops"]["_source_errors"] = ["App configuration"]
    page.evaluate("ConsoleData.retry()")
    page.wait_for_function(
        "document.querySelector('main').textContent.includes('Settings unavailable')"
    )
    assert page.locator('[data-editor="config"] [name="team"]').is_disabled()
    assert (
        page.locator("a", has_text="Status page").first.get_attribute("href")
        == origin + "/prefix/status"
    )
    data["genie_url"] = origin + "/prefix/console/index.html?demo=1"
    page.evaluate("ConsoleData.retry()")
    navigate(page, "#/governance")
    assert page.locator("#governance-integrations code").inner_text() == origin + "/prefix/mcp"
    assert_readable(page, "prefixed governance")
    navigate(page, "#/ask")
    assert (
        page.locator('iframe[title="Genie fleet assistant"]').get_attribute("src")
        == data["genie_url"]
    )
    assert not errors, errors
    page.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root")
    parser.add_argument("--browser")
    args = parser.parse_args()
    if args.package_root:
        sys.path.append(args.package_root)
    from playwright.sync_api import sync_playwright

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT / "app/static"))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}/console/index.html?demo=1"
    errors, checks = [], []
    artifacts = ROOT / ".cache/console-qa"
    artifacts.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, **({"executable_path": args.browser} if args.browser else {})
            )
            context = browser.new_context()
            context.route(
                "**/*",
                lambda route: (
                    route.continue_()
                    if route.request.url.startswith(f"http://127.0.0.1:{server.server_port}/")
                    else route.abort()
                ),
            )
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.goto(base)
            page.wait_for_function("window.ConsoleApp !== undefined")
            contrast = assert_palette(page)
            routes = page.locator(".nav-link").evaluate_all("es=>es.map(e=>e.getAttribute('href'))")
            sections = [
                "overview",
                "errors",
                "traces",
                "logs",
                "traffic",
                "dependencies",
                "changes",
                "security",
                "cost",
                "ai",
                "usage",
                "product",
                "operate",
                "browser",
                "telemetry",
            ]
            for width in [1440, 390, 320, 375, 414, 768]:
                page.set_viewport_size({"width": width, "height": 1000})
                paths = routes + [
                    f"#/app/{name}/{section}"
                    for name in ["fraud-triage", "claims-assistant", "legacy-reports"]
                    for section in sections
                ]
                paths += [
                    "#/federation",
                    "#/app/fraud-triage/investigate",
                    "#/app/claims-assistant/agent-trace/tr-demo-0",
                    "#/trace/0af7651916cd43dd8448eb211c80319c",
                ]
                paths += page.evaluate(
                    "MOCK.error_groups.map(e=>'#/app/'+encodeURIComponent(e.app)+'/error/'+encodeURIComponent(e.fingerprint))"
                )
                for path in paths:
                    page.evaluate("hash=>location.hash=hash", path)
                    page.wait_for_timeout(40)
                    page.wait_for_function("!document.querySelector('#main .skeleton')")
                    page.locator("main details").evaluate_all("es=>es.forEach(e=>e.open=true)")
                    assert_readable(page, path)
                    sizes = page.evaluate(
                        "({viewport:innerWidth,body:document.body.scrollWidth,html:document.documentElement.scrollWidth,main:document.querySelector('main').scrollWidth,mainWidth:document.querySelector('main').clientWidth})"
                    )
                    assert (
                        sizes["body"] <= width + 1
                        and sizes["html"] <= width + 1
                        and sizes["main"] <= sizes["mainWidth"] + 1
                    ), (
                        width,
                        path,
                        sizes,
                        page.locator("main *").evaluate_all(
                            "es=>es.filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>[e.tagName,e.className,e.textContent.slice(0,80)]).slice(0,20)"
                        ),
                    )
                    assert not page.get_by_text("This view could not render").count(), path
                    checks.append([width, path])
                page.evaluate("location.hash='#/topology'")
                page.wait_for_timeout(60)
                assert page.locator(".topo-node").count() > 0
                identities = page.locator(".topo-node").evaluate_all(
                    "es=>es.map(e=>e.dataset.workspace+'|'+e.dataset.node)"
                )
                assert len(identities) == len(set(identities)), identities
                resource_ids = page.evaluate(
                    "MOCK.topology.nodes.filter(n=>!n.app).map(n=>[n.workspace_id,n.type,n.label].join('|'))"
                )
                assert len(resource_ids) == len(set(resource_ids))
                assert page.locator(".topo-node.target .status-stale").count() == 0
                assert page.locator(".topo-node.target").evaluate_all(
                    "es=>es.every(e=>e.innerText.includes(' / ')&&e.innerText.includes('No health signal'))"
                )
                assert page.locator(".topo-edge").count() > 0
                assert page.locator("#topology-list table").count() == 1
                node = page.locator(".topo-node.source a").first
                node.focus()
                assert page.locator(".topo-edge.highlight").count() > 0
                node.hover()
                assert page.locator(".topo-edge.highlight").count() > 0
                node.focus()
                for node in page.locator(".topo-node a, .topo-node button").all():
                    assert node.evaluate("e=>document.activeElement===e")
                    page.keyboard.press("Tab")
                page.locator(".topo-select").first.click()
                assert page.locator(".blast-radius").count() == 1
                page.screenshot(path=str(artifacts / f"topology-{width}.png"), full_page=True)
                page.locator('[data-filter="resourceType"]').select_option("sql_warehouse")
                assert (
                    page.locator(".topo-edge").count()
                    == page.locator("#topology-list tbody tr").count()
                )
                assert (
                    page.locator('.topo-node.target[data-type="sql_warehouse"]').count()
                    == page.locator(".topo-select").count()
                )
                page.locator('[data-filter="topologyTeam"]').select_option("Claims")
                assert page.locator(".topo-node.source").count() == 2
                page.locator('[data-filter="resourceType"]').select_option("all")
                page.locator('[data-filter="topologyTeam"]').select_option("all")
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.goto(base)
            page.wait_for_function("window.ConsoleApp !== undefined")
            for name, path in {
                "topology": "#/topology",
                "operate": "#/app/fraud-triage/operate",
                "governance": "#/governance",
                "deps": "#/app/claims-assistant/dependencies",
                "logs": "#/app/fraud-triage/logs",
                "alerts": "#/alerts",
            }.items():
                navigate(page, path)
                assert_readable(page, path)
                for anchor in page.locator(".section-index a").all():
                    original = page.evaluate("location.hash")
                    anchor.click()
                    target = anchor.get_attribute("data-local-anchor")
                    assert page.evaluate("document.activeElement.id") == target
                    assert page.evaluate("location.hash") == original
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(artifacts / f"after-{name}.png"), full_page=True)
            demo_interactions(page, base, artifacts)
            live_transport(context, base)
            file_context = browser.new_context()
            file_root = (ROOT / "app/static/console").as_uri() + "/"
            file_context.route(
                "**/*",
                lambda route: (
                    route.continue_() if route.request.url.startswith(file_root) else route.abort()
                ),
            )
            file_page = file_context.new_page()
            file_page.goto(file_root + "index.html?demo=1#/governance")
            file_page.wait_for_function(
                "window.ConsoleApp !== undefined && !document.querySelector('#main .skeleton')"
            )
            assert_readable(file_page, "file demo governance")
            assert (
                file_page.locator("#governance-integrations").inner_text().count("Demo placeholder")
                == 1
            )
            file_context.close()
            assert not errors, errors
            print(
                json.dumps(
                    {
                        "route_checks": len(checks),
                        "widths": [1440, 390, 320, 375, 414, 768],
                        "js_errors": errors,
                        "contrast_pairs": len(contrast),
                        "topology": "nodes, edges, hover, focus, keyboard targets, list, blast radius passed",
                        "interactions": "admin/read-only, confirmations, saves, capacity, trace drilldowns, export, lazy cache/refresh/retry and prefixed live transport passed",
                    },
                    indent=2,
                )
            )
            (artifacts / "report.json").write_text(
                json.dumps({"checks": checks, "errors": errors, "contrast": contrast}, indent=2)
            )
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
