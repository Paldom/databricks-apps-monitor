// Shared library for the single-app DETAIL-VIEW concepts (round 3).
// Plain-language sections over the existing per-app APIs — presentation only.
import { esc, fmt, get, statusColor, scoreColor } from './_common.js';
export { esc, fmt, get, statusColor, scoreColor };

export const qp = () => Object.fromEntries(new URLSearchParams(location.hash.replace(/^#/, '')));
export const setqp = o => { location.hash = new URLSearchParams(o).toString(); };
export const tsfmt = t => t ? new Date(t).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '–';

const cache = new Map();
export async function fetchS(app, path) {
  const k = app + '|' + path;
  const url = `api/apps/${encodeURIComponent(app)}` + (path ? `/${path}` : '');
  if (!cache.has(k)) cache.set(k, get(url).catch(e => ({ __err: e.message })));
  return cache.get(k);
}

// tiny helpers -----------------------------------------------------------
export function table(cols, rows, max = 12) {
  if (!rows || !rows.length) return `<div class="hint">Checked — nothing here for this window.</div>`;
  const body = rows.slice(0, max).map(r => `<tr>${cols.map(c => `<td>${c[1](r)}</td>`).join('')}</tr>`).join('');
  const more = rows.length > max ? `<div class="hint">…and ${rows.length - max} more</div>` : '';
  return `<table class="t"><tr>${cols.map(c => `<th>${c[0]}</th>`).join('')}</tr>${body}</table>${more}`;
}
export function spark(vals, w = 420, h = 40, color = '#2563EB') {
  const v = vals.filter(x => x != null); if (v.length < 2) return '';
  const max = Math.max(...v, 1), step = w / (v.length - 1);
  const pts = v.map((x, i) => `${(i * step).toFixed(1)},${(h - 3 - (x / max) * (h - 8)).toFixed(1)}`).join(' ');
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;max-width:${w}px;height:auto"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.6"/></svg>`;
}
export const sev = s => `<span class="sev sev-${esc((s || 'info').toLowerCase())}">${esc(s || '')}</span>`;
export const kv = pairs => `<div class="kvs">${pairs.map(([k, v]) => `<div class="kv"><span>${k}</span><b>${v}</b></div>`).join('')}</div>`;
const err = d => d && d.__err ? `<div class="hint">couldn’t load: ${esc(d.__err)}</div>` : null;
// /api/apps/{name} lacks the computed status field; the fleet list has it
const stOf = (app, a) => a.status || ((window.__fleet || []).find(x => x.name === app) || {}).status || '';

// sections ----------------------------------------------------------------
// Each: id, label (plain words), question (what it answers), load(app) -> html.
export const SECTIONS = [
  { id: 'summary', label: 'Summary', question: 'How is this app doing overall?',
    async load(app) {
      const [ov, a] = await Promise.all([fetchS(app, 'overview'), fetchS(app, '')]);
      if (err(ov)) return err(ov);
      const s = ov.scan, r = ov.review, m = ov.mtd, u = ov.usage;
      const card = (l, v, sub, c) => `<div class="sc"><div class="scl">${l}</div><div class="scv" style="color:${c || 'inherit'}">${v}</div><div class="scs">${sub}</div></div>`;
      return `<div class="scgrid">
        ${card('Is it up?', (stOf(app, a) || '–').toUpperCase(), `${fmt(a.uptime_24h, 1)}% uptime · p95 ${fmt(a.p95_ms)} ms`, statusColor(stOf(app, a)))}
        ${card('Is the code safe?', s ? s.quality_score + '/100' : '–', s ? `${+s.findings_critical + +s.findings_high} serious findings · review: ${r ? r.verdict : 'pending'}` : 'not scanned yet', s ? scoreColor(+s.quality_score) : '#A1A1AA')}
        ${card('What does it cost?', m ? '$' + fmt(m.mtd_usd, 2) : '–', ov.forecast ? `heading for $${fmt(ov.forecast.forecast_30d_usd, 2)}/30d` : 'this month', '#2563EB')}
        ${card('Who uses it?', u ? fmt(u.peak_dau) : '–', u ? `peak daily users · ${fmt(u.requests_7d)} requests this week` : 'no traffic yet', '#7C3AED')}
      </div>
      ${(ov.events || []).length ? `<h4>Latest events</h4>${table([
        ['when', e => tsfmt(e.ts)], ['what', e => `<b>${esc(e.rule)}</b>`], ['state', e => sev(e.state)], ['detail', e => `<span class="wrap">${esc((e.message || '').slice(0, 110))}</span>`],
      ], ov.events, 5)}` : '<div class="hint">No recent alert events — quiet is good.</div>'}`;
    } },
  { id: 'broke', label: 'What broke', question: 'What failed recently, and does it repeat?',
    async load(app) {
      const d = await fetchS(app, 'errors?hours=24'); if (err(d)) return err(d);
      return `<h4>Recurring problems (grouped)</h4>${table([
        ['problem', g => `<span class="wrap"><b>${esc((g.sample || g.fingerprint || '').slice(0, 100))}</b></span>`],
        ['times seen', g => fmt(g.occurrences)], ['first seen', g => tsfmt(g.first_seen)], ['last seen', g => tsfmt(g.last_seen)],
      ], d.groups, 6)}
      <h4>Individual failed requests (24 h)</h4>${table([
        ['when', x => tsfmt(x.time)], ['request', x => esc(x.name)], ['HTTP', x => x.http_status || '–'],
        ['took', x => fmt(x.duration_ms) + ' ms'], ['error', x => `<span class="wrap">${esc((x.message || '').slice(0, 80))}</span>`],
      ], d.failed_requests, 8)}
      <h4>Error log lines</h4>${table([
        ['when', x => tsfmt(x.time)], ['level', x => sev(x.severity_text)], ['message', x => `<span class="wrap mono">${esc((x.body || '').slice(0, 130))}</span>`],
      ], d.error_logs, 6)}`;
    } },
  { id: 'speed', label: 'Speed & traffic', question: 'How much traffic, and how fast is it served?',
    async load(app) {
      const d = await fetchS(app, 'requests?hours=24'); if (err(d)) return err(d);
      const tl = d.timeline || [];
      return `${tl.length ? `<h4>Requests per hour</h4>${spark(tl.map(x => +x.requests))}
        <h4>p95 latency</h4>${spark(tl.map(x => +x.p95_ms), 420, 40, '#7C3AED')}` : '<div class="hint">No real traffic in this window (probes excluded).</div>'}
      <h4>Busiest routes (24 h)</h4>${table([
        ['route', r => `<span class="mono">${esc(r.route)}</span>`], ['requests', r => fmt(r.requests)],
        ['errors', r => +r.errors ? `<b style="color:#DC2626">${fmt(r.errors)}</b>` : '0'],
        ['avg', r => fmt(r.avg_ms) + ' ms'], ['p95', r => fmt(r.p95_ms) + ' ms'],
      ], d.routes, 10)}`;
    } },
  { id: 'requests', label: 'Recent requests', question: 'What did individual requests actually do?',
    async load(app) {
      const d = await fetchS(app, 'traces?hours=24'); if (err(d)) return err(d);
      return `<div class="hint" style="margin-bottom:8px">Each row is one real request; open it in the full workbench to see its trace waterfall with correlated logs.</div>
      ${table([
        ['when', x => tsfmt(x.time)], ['request', x => `<span class="mono">${esc(x.route || x.name)}</span>`],
        ['took', x => fmt(x.duration_ms) + ' ms'], ['status', x => x.status === 'error' ? sev('error') : sev('ok')],
        ['trace', x => `<a href="../#/app/${encodeURIComponent(app)}/traces" title="open in workbench">${esc((x.trace_id || '').slice(0, 8))}…</a>`],
      ], d.traces, 12)}`;
    } },
  { id: 'logs', label: 'Logs', question: 'What is the app writing to its logs?',
    async load(app) {
      const d = await fetchS(app, 'logs?hours=24'); if (err(d)) return err(d);
      return table([
        ['when', x => tsfmt(x.time)], ['level', x => sev(x.severity)],
        ['message', x => `<span class="wrap mono">${esc((x.body || '').slice(0, 150))}</span>`],
      ], d.logs, 16);
    } },
  { id: 'outside', label: 'Outside calls', question: 'Whom does this app call, and where does time go?',
    async load(app) {
      const d = await fetchS(app, 'deps'); if (err(d)) return err(d);
      return `<div class="hint" style="margin-bottom:8px">Outbound calls over 7 days — model endpoints, warehouses, other apps.</div>
      ${table([
        ['calls out to', r => `<b>${esc(r.dependency)}</b>`], ['calls', r => fmt(r.calls)],
        ['avg', r => fmt(r.avg_ms) + ' ms'], ['p95', r => fmt(r.p95_ms) + ' ms'],
        ['errors', r => +r.errors ? `<b style="color:#DC2626">${fmt(r.errors)}</b>` : '0'],
      ], d.deps, 12)}`;
    } },
  { id: 'code', label: 'Code & security', question: 'Would this code pass a production review?',
    async load(app) {
      const [s, r] = await Promise.all([fetchS(app, 'security'), fetchS(app, 'review')]);
      const scan = s && s.scan, rev = r && r.review;
      let html = '';
      if (scan) html += kv([
        ['scan score', `<span style="color:${scoreColor(+scan.quality_score)}">${scan.quality_score}/100</span>`],
        ['serious findings', `${scan.findings_critical} critical · ${scan.findings_high} high`],
        ['packages', `${scan.deps} (${scan.deps_pinned} pinned)`],
        ['freshness', scan.freshness_score != null ? scan.freshness_score + '/100' : '–'],
        ['scanned', tsfmt(scan.scanned_at)],
      ]);
      else html += '<div class="hint">Not scanned yet — the scan job runs hourly.</div>';
      if (rev) html += `<h4>The reviewer’s verdict: ${rev.verdict === 'reject' ? '✗ reject' : rev.verdict === 'approve' ? '✓ approve' : '⚠ ' + esc(rev.verdict || '')} · ${rev.score_overall}/10</h4>
        <div class="quote">“${esc((rev.summary || '').slice(0, 260))}”</div>`;
      if (s && (s.findings || []).length) html += `<h4>Top findings</h4>${table([
        ['severity', f => sev(f.severity)], ['what', f => `<span class="wrap"><b>${esc(f.title)}</b>${f.package ? ' · ' + esc(f.package) : ''}</span>`],
        ['where', f => `<span class="mono">${esc(f.file || '')}${f.line ? ':' + f.line : ''}</span>`],
      ], s.findings, 8)}`;
      return html;
    } },
  { id: 'money', label: 'Money', question: 'What does this app cost, and is it on budget?',
    async load(app) {
      const d = await fetchS(app, 'cost'); if (err(d)) return err(d);
      const daily = d.daily || [];
      return `${kv([
        ['this month', d.mtd_usd != null ? '$' + fmt(d.mtd_usd, 2) : '–'],
        ['30-day forecast', d.forecast ? '$' + fmt(d.forecast.forecast_30d_usd, 2) : '–'],
        ['budget', d.budget ? '$' + fmt(d.budget, 0) + '/mo' : 'not set'],
      ])}
      ${daily.length ? `<h4>Daily compute $</h4>${spark(daily.map(x => +x.dbu_usd || 0))}` : ''}
      ${table([
        ['date', x => String(x.date).slice(0, 10)], ['compute $', x => '$' + fmt(x.dbu_usd, 2)],
        ['AI calls', x => fmt(x.ai_calls)], ['AI tokens', x => fmt((+x.ai_input_tokens || 0) + (+x.ai_output_tokens || 0))],
      ], [...daily].reverse(), 7)}`;
    } },
  { id: 'people', label: 'People & AI', question: 'Who uses it, and what does the AI usage look like?',
    async load(app) {
      const [a, g] = await Promise.all([fetchS(app, 'analytics'), fetchS(app, 'genai')]);
      const daily = (a && a.daily) || [];
      return `${daily.length ? `<h4>Daily users</h4>${spark(daily.map(x => +x.users || 0), 420, 40, '#7C3AED')}` : '<div class="hint">No usage recorded yet.</div>'}
      <h4>Most active users (hashed)</h4>${table([
        ['user', u => `<span class="mono">${esc((u.user_hash || '').slice(0, 10))}…</span>`], ['requests', u => fmt(u.requests)],
        ['sessions', u => fmt(u.sessions)], ['active days', u => fmt(u.active_days)], ['AI tokens', u => fmt(u.tokens)],
      ], (a && a.users) || [], 6)}
      <h4>AI models used (30 d)</h4>${table([
        ['date', x => String(x.date).slice(0, 10)], ['model', x => esc(x.model)], ['calls', x => fmt(x.calls)],
        ['tokens', x => fmt((+x.input_tokens || 0) + (+x.output_tokens || 0))], ['p95', x => fmt(x.p95_ms) + ' ms'],
      ], [...((g && g.daily) || [])].reverse(), 6)}`;
    } },
  { id: 'uptime', label: 'Uptime & tests', question: 'Is it reachable, and do user journeys still pass?',
    async load(app) {
      const [a, sy] = await Promise.all([fetchS(app, ''), fetchS(app, 'synthetics')]);
      const series = (a.series || []).slice(-120);
      const live = sy && sy.live;
      return `${kv([
        ['status', `<span style="color:${statusColor(stOf(app, a))}">${(stOf(app, a) || '–').toUpperCase()}</span>`],
        ['uptime 24 h', fmt(a.uptime_24h, 1) + '%'], ['p95 probe', fmt(a.p95_ms) + ' ms'], ['errors 1 h', fmt(a.error_rate_1h, 1) + '%'],
      ])}
      ${series.length ? `<h4>Probe latency (last ${series.length} checks)</h4>${spark(series.map(p => p[3]), 420, 40, '#16A34A')}` : ''}
      <h4>Synthetic journey</h4>
      ${live ? kv([['journey', esc(live.journey || 'smoke')], ['result', live.ok ? '<span style="color:#16A34A">PASS</span>' : '<span style="color:#DC2626">FAIL</span>'], ['checked', tsfmt(live.checked_at || live.ts)]]) : '<div class="hint">No journey configured for this app.</div>'}`;
    } },
  { id: 'history', label: 'History & settings', question: 'What happened to this app, and how is it configured?',
    async load(app) {
      const [t, o] = await Promise.all([fetchS(app, 'timeline'), fetchS(app, 'ops')]);
      const cfg = o && o.config;
      return `<h4>Timeline — alerts & deployments</h4>${table([
        ['when', e => tsfmt(e.ts)], ['what', e => `<b>${esc(e.rule || e.type)}</b>`], ['state', e => sev(e.state || e.severity)],
        ['detail', e => `<span class="wrap">${esc((e.message || '').slice(0, 100))}</span>`],
      ], (t && t.events) || [], 8)}
      <h4>Deployments</h4>${table([
        ['when', d => tsfmt(d.create_time)], ['id', d => `<span class="mono">${esc((d.deployment_id || '').slice(0, 8))}</span>`], ['state', d => sev(d.state)],
      ], (o && o.deployments) || [], 5)}
      <h4>Who can access it</h4>${table([
        ['principal', p => esc(p.principal)], ['type', p => esc(p.principal_type)], ['level', p => esc(p.level)],
      ], (o && o.permissions) || [], 6)}
      ${cfg ? `<h4>Settings</h4>${kv([
        ['tags', esc(cfg.tags_json || '{}')], ['budget', cfg.budget_usd_month ? '$' + fmt(cfg.budget_usd_month, 0) + '/mo' : 'not set'],
        ['auto-stop', esc(cfg.auto_stop || 'off')],
      ])}` : ''}
      <div class="hint" style="margin-top:8px">Change tags, budget or auto-stop in the <a href="../#/app/${encodeURIComponent(app)}/ops">full workbench →</a></div>`;
    } },
];
export const SECTION = Object.fromEntries(SECTIONS.map(s => [s.id, s]));

// shared header + styles ----------------------------------------------------
export async function appList() {
  const f = await get('api/fleet'); window.__fleet = f.apps;
  return f.apps.map(a => a.name);
}
export function headerHtml(concept, app, apps) {
  return `<div class="brand"><span class="dot"></span>Apps Monitor</div><span class="tag">${concept}</span>
    <span class="crumbsep">·</span>
    <select id="appsel">${apps.map(n => `<option ${n === app ? 'selected' : ''}>${esc(n)}</option>`).join('')}</select>
    <a class="hlink" href="../">← real dashboard</a><a class="hlink" href="./">all concepts</a>`;
}
export const APP_CSS = `
:root{--font:'Inter',-apple-system,system-ui,sans-serif;--border:#E4E4E7;--muted:#F4F4F5;--text:#18181B;--sub:#52525B;--faint:#A1A1AA}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#FAFAFA;color:var(--text);font-family:var(--font);font-size:14px}
header{display:flex;align-items:center;gap:12px;padding:12px 24px;background:#fff;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10}
.brand{font-weight:700;white-space:nowrap}.brand .dot{display:inline-block;width:12px;height:12px;border-radius:3px;background:#FF3621;margin-right:8px;vertical-align:-1px}
.tag{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--sub);border:1px solid var(--border);padding:3px 8px;border-radius:5px;white-space:nowrap}
.crumbsep{color:var(--faint)}
#appsel{border:1px solid var(--border);border-radius:8px;padding:5px 9px;font-family:var(--font);font-size:13px;font-weight:600;background:#fff;color:var(--text)}
.hlink{font-size:12.5px;color:#2563EB;text-decoration:none;margin-left:auto}.hlink+.hlink{margin-left:14px}
h4{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--sub);margin:16px 0 8px}
table.t{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;border:1px solid var(--border);border-radius:8px;overflow:hidden}
table.t th{text-align:left;padding:7px 10px;color:var(--sub);font-weight:600;border-bottom:1px solid var(--border);white-space:nowrap}
table.t td{padding:6px 10px;border-bottom:1px solid var(--muted);font-variant-numeric:tabular-nums;vertical-align:top;white-space:nowrap}
table.t tr:last-child td{border-bottom:none}
.wrap{white-space:normal;word-break:break-word}.mono{font-family:'JetBrains Mono',Menlo,monospace;font-size:11px}
.hint{font-size:12.5px;color:var(--faint);padding:6px 0}
.sev{font-size:10.5px;font-weight:700;text-transform:uppercase;padding:1px 7px;border-radius:5px;background:var(--muted);color:var(--sub)}
.sev-critical,.sev-high,.sev-error,.sev-firing,.sev-failed{background:#FEF2F2;color:#DC2626}
.sev-warning,.sev-medium{background:#FEFCE8;color:#CA8A04}
.sev-ok,.sev-resolved,.sev-succeeded,.sev-info,.sev-low{background:#F0FDF4;color:#16A34A}
.kvs{display:flex;gap:0;flex-wrap:wrap;background:#fff;border:1px solid var(--border);border-radius:8px;padding:10px 0;margin-bottom:4px}
.kv{padding:2px 18px;border-right:1px solid var(--muted);font-size:12.5px;color:var(--sub);display:flex;flex-direction:column;gap:2px}
.kv:last-child{border-right:none}.kv b{font-size:15px;color:var(--text);font-variant-numeric:tabular-nums}
.quote{font-size:13px;color:var(--sub);line-height:1.6;background:var(--muted);border-radius:8px;padding:8px 12px;margin:6px 0;font-style:italic}
.scgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin-bottom:6px}
.sc{background:#fff;border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.scl{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--sub)}
.scv{font-size:26px;font-weight:700;margin-top:5px}.scs{font-size:12px;color:var(--sub);margin-top:3px}
`;
