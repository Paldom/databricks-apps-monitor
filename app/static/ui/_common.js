// Shared helpers for the alternative-UI concepts. Each concept HTML pulls this in.
// All concepts read the SAME live APIs the production UI uses — real data, not mockups.
export const $ = (s, r = document) => r.querySelector(s);
export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const fmt = (v, d = 0) => v == null || v === '' ? '–' : Number(v).toLocaleString('en-US', { maximumFractionDigits: d });
export const ago = ts => { if (!ts) return '–'; const s = Math.max(0, Date.now() / 1000 - ts); return s < 90 ? `${s | 0}s` : s < 5400 ? `${Math.round(s / 60)}m` : `${Math.round(s / 3600)}h`; };
export async function get(u) { const r = await fetch('../' + u.replace(/^\//, '')); if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }

export async function loadAll() {
  const [fleet, enrich, alerts] = await Promise.all([
    get('api/fleet'), get('api/fleet/enrich').catch(() => ({})), get('api/alerts').catch(() => ({ active: [], recent: [] })),
  ]);
  const E = { security: {}, reviews: {}, cost: {}, config: {}, mtd: {}, ...enrich };
  const A = alerts.active || [];
  fleet.apps.forEach(a => {
    a.alerts = A.filter(x => x.app === a.name);
    a.scan = E.security[a.name]; a.review = E.reviews[a.name];
    a.cost = E.cost[a.name]; a.mtd = E.mtd[a.name];
    try { a.tags = JSON.parse((E.config[a.name] || {}).tags_json || '{}'); } catch { a.tags = {}; }
  });
  return { fleet, enrich: E, alerts };
}

export const statusColor = s => ({ ok: '#00A972', degraded: '#E59500', down: '#D63B30', stopped: '#8B95A1', pending: '#2272B4' }[s] || '#8B95A1');
export const scoreColor = s => s >= 80 ? '#00A972' : s >= 60 ? '#E59500' : '#D63B30';

// A shared slide-over detail drawer used by every concept (overview scorecard).
export async function openDetail(name) {
  let ov;
  try { ov = await get('api/apps/' + encodeURIComponent(name) + '/overview'); } catch { ov = {}; }
  const s = ov.scan, r = ov.review, c = ov.cost_7d, m = ov.mtd, u = ov.usage, f = ov.forecast;
  let dr = $('#detail');
  if (!dr) { dr = document.createElement('div'); dr.id = 'detail'; document.body.appendChild(dr); }
  const cardRow = (label, val, sub, color) =>
    `<div class="dcard"><div class="dl">${label}</div><div class="dv" style="color:${color || 'inherit'}">${val}</div><div class="ds">${sub || ''}</div></div>`;
  dr.innerHTML = `<div class="dov" onclick="this.parentElement.remove()"></div>
    <div class="dpanel">
      <button class="dx" onclick="document.getElementById('detail').remove()">×</button>
      <h2>${esc(name)}</h2>
      <a href="${esc((window.__fleet || []).find(x => x.name === name)?.url || '#')}" target="_blank" class="dopen">open app ↗</a>
      <div class="dgrid">
        ${cardRow('Reliability', fmt((window.__fleet || []).find(x => x.name === name)?.uptime_24h, 1) + '%', 'uptime 24h', statusColor((window.__fleet || []).find(x => x.name === name)?.status))}
        ${cardRow('Code quality', s ? s.quality_score : '–', s ? (+s.findings_critical + +s.findings_high) + ' crit/high · ' + (r ? r.verdict : 'no review') : 'not scanned', s ? scoreColor(+s.quality_score) : '#8B95A1')}
        ${cardRow('Cost MTD', m ? '$' + fmt(m.mtd_usd, 2) : '–', f ? 'forecast $' + fmt(f.forecast_30d_usd, 2) : (c ? '7d $' + fmt(c.usd_7d, 2) : ''), '#2272B4')}
        ${cardRow('Adoption', u ? fmt(u.peak_dau) : '–', u ? fmt(u.requests_7d) + ' req · 7d' : '', '#6B5BD2')}
      </div>
      ${(ov.events || []).length ? `<div class="dsec">Recent activity</div>${ov.events.map(e => `<div class="devt"><span class="dpill ${e.state === 'firing' ? 'bad' : 'ok'}">${esc((e.state || '').toUpperCase())}</span> <b>${esc(e.rule)}</b> ${esc(e.message)}</div>`).join('')}` : ''}
      <div class="dfoot">Full workbench: <a href="../#/app/${encodeURIComponent(name)}/overview">open in production UI →</a></div>
    </div>`;
}

export const DETAIL_CSS = `
#detail{position:fixed;inset:0;z-index:200}
#detail .dov{position:absolute;inset:0;background:rgba(0,0,0,.4)}
#detail .dpanel{position:absolute;top:0;right:0;bottom:0;width:min(560px,94vw);background:#fff;color:#1B3139;
  box-shadow:-8px 0 40px rgba(0,0,0,.3);padding:24px 28px;overflow-y:auto;font-family:Inter,system-ui,sans-serif}
#detail .dx{position:absolute;top:14px;right:18px;border:none;background:none;font-size:24px;color:#8B95A1;cursor:pointer}
#detail h2{font-size:22px;margin:0 0 2px}
#detail .dopen{font-size:12.5px}
#detail .dgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0}
#detail .dcard{border:1px solid #E1E5EB;border-radius:10px;padding:12px 14px}
#detail .dl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#5F7281}
#detail .dv{font-size:26px;font-weight:700;margin-top:4px}
#detail .ds{font-size:12px;color:#5F7281;margin-top:2px}
#detail .dsec{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#5F7281;margin:14px 0 6px}
#detail .devt{font-size:12px;padding:5px 0;border-bottom:1px solid #EEF1F4;color:#5F7281}
#detail .dpill{font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px}
#detail .dpill.bad{background:#FCE8E6;color:#D63B30}#detail .dpill.ok{background:#E6F7EF;color:#00A972}
#detail .dfoot{margin-top:18px;font-size:12.5px;color:#5F7281}
`;
