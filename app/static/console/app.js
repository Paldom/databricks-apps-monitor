/* Operations workbench shell; snapshot summaries plus lazy native evidence sections. */
(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const finite = v => v != null && v !== '' && Number.isFinite(Number(v));
  const numeric = v => finite(v) ? Number(v) : null;
  const list = v => Array.isArray(v) ? v.filter(x => x != null) : [];
  const record = v => v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  const fields = (v, keys) => Object.fromEntries(keys.split(' ').map(k => [k, numeric(v?.[k])]));
  function normalize(data) {
    const m = {...data};
    for (const key of ['apps','workspaces','alerts','timeline','error_groups','synthetics','maintenance_windows']) m[key] = list(m[key]);
    m.sources = record(m.sources); m.notes = record(m.notes); m.traces = record(m.traces);
    m.trace_example = m.trace_example || {};
    if (m.trace_example.trace_id) m.traces[m.trace_example.trace_id] = m.trace_example;
    m.cost = {...record(m.cost), model_prices:list(m.cost?.model_prices)};
    m.governance = {...record(m.governance), required_tags:list(m.governance?.required_tags), audit_events:list(m.governance?.audit_events)};
    m.funnel_example = {...record(m.funnel_example), by_version:record(m.funnel_example?.by_version)};
    for (const [key,value] of Object.entries(m.funnel_example.by_version)) m.funnel_example.by_version[key] = list(value).map(step=>({...step,step:String(step.step || '—')}));
    m.cohorts_example = {...record(m.cohorts_example), weeks:list(m.cohorts_example?.weeks), sizes:Array.isArray(m.cohorts_example?.sizes)?m.cohorts_example.sizes:[], retention_pct:list(m.cohorts_example?.retention_pct)};
    m.apps = m.apps.map(a => ({...a, id:a.id || a.name, name:a.name || 'Unnamed app',
      team:a.team || '—', cost_center:a.cost_center || '—', kind:a.kind || '—', workspace:a.workspace || '—',
      last24h:fields(a.last24h,'requests error_rate_pct p50_ms p95_ms p99_ms uptime_pct active_users'),
      slo:{...record(a.slo), ...fields(a.slo,'availability_target attainment_28d error_budget_remaining_pct latency_threshold_ms')},
      cost:{...record(a.cost), ...fields(a.cost,'mtd_usd dbu_usd ai_usd idle_usd budget_usd_month forecast_usd_month usd_per_1k_requests')},
      security:{...record(a.security), cve:fields(a.security?.cve,'critical high medium low'), review_verdict:a.security?.review_verdict || '—'},
      governance:record(a.governance), telemetry:{...record(a.telemetry), ...fields(a.telemetry,'envelope_coverage_pct last_span_age_s sampler_ratio orphan_span_pct')},
      series_24h:{hours:list(a.series_24h?.hours), ...Object.fromEntries(['requests','p95_ms','error_rate_pct'].map(k=>[k,Array.isArray(a.series_24h?.[k])?a.series_24h[k].map(numeric):[]]))},
      genai:a.genai?{...a.genai, models:list(a.genai.models), quality:record(a.genai.quality), feedback:record(a.genai.feedback), error_classes_24h:record(a.genai.error_classes_24h), guardrail_findings_7d:record(a.genai.guardrail_findings_7d)}:null
    }));
    m.alerts = m.alerts.map(a=>({...a, rule:a.rule || '', message:a.message || '', severity:a.severity || 'info'}));
    m.synthetics = m.synthetics.map(a=>({...a, history:Array.isArray(a.history)?a.history:[]}));
    return m;
  }
  let M = normalize(window.MOCK || {});
  window.MOCK = M;
  const esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n = (v, digits = 0) => !finite(v) ? '—' : Number(v).toLocaleString('en-US', {maximumFractionDigits: digits, minimumFractionDigits: digits});
  const usd = (v, digits = 0) => !finite(v) ? '—' : '$' + n(v, digits);
  const pct = (v, digits = 1) => !finite(v) ? '—' : n(v, digits) + '%';
  const fraction = (a,b) => finite(a) && finite(b) && Number(b)>0 ? Number(a)/Number(b)*100 : null;
  const overBudget = a => finite(a.cost.forecast_usd_month) && finite(a.cost.budget_usd_month) && a.cost.forecast_usd_month>a.cost.budget_usd_month;
  const overLatency = a => finite(a.last24h.p95_ms) && finite(a.slo.latency_threshold_ms) && a.last24h.p95_ms>a.slo.latency_threshold_ms;
  const percent = v => finite(v) ? Number(v)*100 : null;
  const sum = (items, fn) => { const values=items.map(fn); return values.length && values.every(finite) ? values.reduce((a,b)=>a+Number(b),0) : null; };
  const validDate = value => value != null && Number.isFinite(new Date(value).getTime());
  const time = value => validDate(value) ? new Date(value).toISOString().slice(11, 16) : '—';
  const date = value => validDate(value) ? new Date(value).toLocaleDateString('en-GB', {day:'2-digit', month:'short', timeZone:'UTC'}) : '—';
  const stamp = value => validDate(value) ? `${date(value)}, ${time(value)} UTC` : 'Not collected yet';
  let now = validDate(M.generated_at) ? new Date(M.generated_at).getTime() : Date.now();
  const month = () => new Date(now).toLocaleDateString('en-US',{month:'long',year:'numeric',timeZone:'UTC'});
  const age = seconds => !finite(seconds) ? 'Not collected yet' : seconds >= 3600 ? `${Math.floor(seconds/3600)}h ${Math.floor(seconds%3600/60)}m` : seconds >= 60 ? `${Math.floor(seconds/60)}m` : `${Math.floor(seconds)}s`;
  const app = name => M.apps.find(a => a.id === name) || M.apps.find(a => a.name === name && (state.workspace==='all' || a.workspace===state.workspace));
  const belongs = (row,a) => row.app === a.id || (!a.remote && row.app === a.name);
  const maintenanceApplies = (row,a) => {
    if (a.remote) return false;
    const pattern=String(row.app || '').split('').map(c=>c==='*'?'.*':c==='?'?'.':/[a-zA-Z0-9_-]/.test(c)?c:'\\'+c).join('');
    return new RegExp('^'+pattern+'$').test(a.name);
  };
  const workspace = name => M.workspaces.find(w => w.name === name) || {};
  const isStale = a => workspace(a.workspace).status !== 'OK';
  const status = a => isStale(a) || !['down','degraded','idle','stopped','healthy'].includes(a.health) ? 'stale' : a.health;
  const ranks = {critical:0, high:1, warning:2, info:3};
  const healthRanks = {down:0, degraded:1, stale:2, idle:3, healthy:4, stopped:5};
  const state = {workspace:'all', range:24, search:'', health:'all', team:'all', severity:'all', alertTab:'firing', costTeam:'all', costSearch:'', governanceFilter:'all', selectedSpan:null, logLevel:'all', funnelVersion:Object.keys(M.funnel_example.by_version)[0], sorts:{}};
  const detailState = new Map(), errorDetails = new Map();
  let connectionError = null;
  const icons = {
    fleet:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    activity:'<path d="M2 12h4l3-8 5 16 3-8h5"/>',
    bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
    cost:'<circle cx="12" cy="12" r="9"/><path d="M15 8h-4a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4H9m3-11v14"/>',
    shield:'<path d="m12 3 8 3v6c0 4-5 8-8 9-3-1-8-5-8-9V6zM8 12l3 3 5-6"/>',
    chart:'<path d="M4 3v17h17M8 15l4-5 4 2 5-7"/>',
    stack:'<path d="m12 3 10 5-10 5L2 8zM2 12l10 5 10-5M2 16l10 5 10-5"/>',
    search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
    arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',
    down:'<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>',
    warning:'<path d="m12 3 10 18H2zM12 9v5m0 3v.1"/>',
    check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    pause:'<circle cx="12" cy="12" r="9"/><path d="M9 8v8m6-8v8"/>',
    idle:'<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>',
    info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
    trace:'<path d="M4 5h13M7 10h13M7 15h8M10 20h10M4 5v10h3"/>',
    menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
    copy:'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
    external:'<path d="M14 3h7v7m0-7L10 14M10 3H3v18h18v-7"/>'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.info}</svg>`;
  const statusNames = {down:'Down',degraded:'Degraded',stale:'Unverified',healthy:'Healthy',idle:'Idle',stopped:'Stopped',critical:'Critical',high:'High',warning:'Warning',info:'Info',ok:'Passed',error:'Failed',resolved:'Resolved',muted:'Muted'};
  const statusIcon = s => ({down:'down',critical:'down',error:'down',degraded:'warning',stale:'clock',high:'warning',warning:'warning',healthy:'check',ok:'check',resolved:'check',stopped:'pause',idle:'idle',muted:'pause'}[s] || 'info');
  const tag = (s, label) => `<span class="status-label status-${esc(s)}">${icon(statusIcon(s))}${esc(label || statusNames[s] || s)}</span>`;
  const badge = (label, kind='') => `<span class="badge ${kind}">${esc(label)}</span>`;
  const link = (href,label,cls='') => `<a class="${cls}" href="${esc(href)}" ${cls==='active'?'aria-current="page"':''}>${label}</a>`;
  const appLink = (a,tab='overview',label=a?.name) => a ? link(`#/app/${encodeURIComponent(a.id)}/${tab}`,esc(label),'app-name') : esc(label);
  const scopedApps = () => M.apps.filter(a => state.workspace === 'all' || a.workspace === state.workspace);
  const scopedAlerts = () => M.alerts.filter(x => scopedApps().some(a => belongs(x,a)));
  const firing = () => scopedAlerts().filter(x => x.state === 'firing' && !x.muted).sort((a,b) => ranks[a.severity]-ranks[b.severity]);
  const appAlerts = a => M.alerts.filter(x => belongs(x,a) && x.state === 'firing' && !x.muted);
  const burn = a => appAlerts(a).find(x => x.rule.startsWith('slo_'))?.message.match(/([\d.]+)x/)?.[1];
  const currentStart = () => now - state.range * 3600000;
  const inRange = ts => new Date(ts).getTime() >= currentStart() && new Date(ts).getTime() <= now;
  const pageHead = (title,subtitle='',action='') => `<div class="page-head"><div><h1>${esc(title)}</h1>${subtitle ? `<p>${subtitle}</p>`:''}</div>${action}</div>`;
  const sectionHead = (title,sub='',action='') => `<div class="section-head"><div><h2>${title}</h2>${sub?`<p>${sub}</p>`:''}</div>${action}</div>`;
  const empty = (title,body,action='') => `<div class="empty">${icon('info')}<h3>${esc(title)}</h3><p>${esc(body)}</p>${action}</div>`;
  const notice = (title,body,tone='warning') => `<div class="notice ${tone}">${icon(tone==='error'?'down':tone==='warning'?'warning':'info')}<div><strong>${esc(title)}</strong><p>${body}</p></div></div>`;
  const metric = (title,value,detail='',tone='') => `<div class="metric"><div class="metric-label">${title}</div><div class="metric-value ${tone}">${value}</div><small>${detail}</small></div>`;
  const facts = items => `<dl class="fact-list">${items.map(([label,value])=>`<div><dt>${label}</dt><dd>${value}</dd></div>`).join('')}</dl>`;
  const breadcrumb = items => `<nav class="breadcrumbs" aria-label="Breadcrumb">${[link('#/fleet','Fleet'),...items].join('<span aria-hidden="true">/</span>')}</nav>`;
  const selectField = (id,label,value,options) => `<div class="field"><label for="${id}">${label}</label><select id="${id}" data-filter="${id}">${options.map(([v,l])=>`<option value="${esc(v)}" ${String(value)===String(v)?'selected':''}>${esc(l)}</option>`).join('')}</select></div>`;
  const searchField = (id,label,value,placeholder) => `<div class="field search"><label for="${id}">${label}</label><input type="search" id="${id}" data-filter="${id}" value="${esc(value)}" placeholder="${placeholder}"></div>`;
  function dataTable(id, rows, columns, initial, dir=1) {
    const sort = state.sorts[id] || (state.sorts[id] = {key:initial, dir});
    const col = columns.find(c=>c.key===sort.key);
    const sorted = [...rows].sort((a,b) => {
      const av = col?.value ? col.value(a) : a[sort.key], bv = col?.value ? col.value(b) : b[sort.key];
      return (typeof av === 'number' ? av-bv : String(av ?? '').localeCompare(String(bv ?? ''))) * sort.dir;
    });
    const sortId='sort-'+id.toLowerCase().replaceAll(' ','-');
    return `<div class="table-wrap"><div class="mobile-table-sort"><label for="${sortId}">Sort by</label><select id="${sortId}" data-table-sort="${id}">${columns.map(c=>`<option value="${c.key}" ${sort.key===c.key?'selected':''}>${esc(c.label)}</option>`).join('')}</select><button class="button" data-sort="${id}" data-key="${sort.key}" aria-label="Reverse sort direction">${sort.dir===1?'↑':'↓'}</button></div><table class="responsive-table" aria-label="${esc(id)}"><thead><tr>${columns.map(c=>`<th scope="col" class="${c.num?'num':''}" ${sort.key===c.key?`aria-sort="${sort.dir===1?'ascending':'descending'}"`:''}><button class="sort ${sort.key===c.key?'active':''}" data-sort="${id}" data-key="${c.key}" aria-label="Sort by ${esc(c.label)}">${esc(c.label)} ${sort.key===c.key?(sort.dir===1?'↑':'↓'):'↕'}</button></th>`).join('')}</tr></thead><tbody>${sorted.map(a=>`<tr>${columns.map(c=>`<td data-label="${esc(c.label)}" class="${c.num?'num':''}">${c.html(a)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function spark(a) {
    const values = a.series_24h.p95_ms;
    if (!values.some(finite)) return ''; 
    const max = Math.max(...values, 1);
    return `<svg class="tiny-spark" viewBox="0 0 76 24" aria-hidden="true"><path d="${values.map((v,i)=>finite(v)?`${i && finite(values[i-1])?'L':'M'}${2+i*72/Math.max(1,values.length-1)},${22-v/max*20}`:'').join(' ')}" fill="none"/></svg>`;
  }
  // Axis labels live in HTML: resizing a plot never resizes its typography.
  function seriesChart(points, title, unit, options={}) {
    const values=points.filter(p=>finite(p.v)), threshold=options.threshold;
    const header=`<div class="chart-header"><h3>${esc(title)}</h3><small>${esc(unit)}${options.cadence?' · '+esc(options.cadence):''}</small></div>`;
    if(!values.length)return `<div class="chart-block">${header}${empty('No samples','There are no measurements in this period.')}</div>`;
    const low=Math.min(0,...values.map(p=>+p.v)), high=Math.max(1,...values.map(p=>+p.v),threshold??0)*1.14;
    const start=options.start??new Date(points[0].ts).getTime(), end=options.end??new Date(points.at(-1).ts).getTime();
    const dated=Number.isFinite(start)&&Number.isFinite(end);
    const x=(p,i)=>dated&&end>start?4+(new Date(p.ts).getTime()-start)/(end-start)*272:4+i*272/Math.max(1,points.length-1);
    const y=v=>96-(v-low)/(high-low)*92;
    let pen=false;
    const path=points.map((p,i)=>{if(!finite(p.v)){pen=false;return '';}const cmd=pen?'L':'M';pen=true;return `${cmd}${x(p,i).toFixed(2)},${y(p.v).toFixed(2)}`;}).join(' ');
    const axis=v=>Math.abs(v)>=1000?n(v/1000,1)+'k':n(v,Math.abs(high-low)<10?1:0);
    const label=ts=>validDate(ts)?(options.hourly?time(ts):date(ts)):String(ts??'—');
    return `<div class="chart-block">${header}<div class="chart-frame"><div class="chart-y" aria-hidden="true">${[high,(high+low)/2,low].map(v=>`<span>${axis(v)}</span>`).join('')}</div><svg class="chart" viewBox="0 0 280 100" preserveAspectRatio="none" role="img" aria-label="${esc(title)} · ${esc(unit)}"><title>${esc(title)} · ${esc(unit)}</title>${[low,(high+low)/2,high].map(v=>`<line class="gridline" x1="0" x2="280" y1="${y(v)}" y2="${y(v)}"/>`).join('')}${threshold!=null?`<line class="target" x1="0" x2="280" y1="${y(threshold)}" y2="${y(threshold)}"/>`:''}<path class="series" d="${path}"/>${points.map((p,i)=>!finite(p.v)?'':`<circle cx="${x(p,i)}" cy="${y(p.v)}" r="1.7"><title>${esc(validDate(p.ts)?stamp(p.ts):p.ts)}: ${n(p.v,2)} ${esc(unit)}</title></circle>`).join('')}${(options.deploys||[]).map(t=>`<line class="deploy" x1="${x(t)}" x2="${x(t)}" y1="0" y2="100"><title>Deploy · ${stamp(t.ts)}</title></line>`).join('')}</svg><div class="chart-x"><span>${esc(label(dated?start:points[0].ts))}</span><span>${esc(label(dated?end:points.at(-1).ts))}${options.hourly?' UTC':''}</span></div></div>${options.note?`<p class="chart-note">${esc(options.note)}</p>`:''}</div>`;
  }
  function chart(a, key, title, unit, threshold, referenceLabel) {
    const cutoff=isStale(a)?(validDate(workspace(a.workspace).last_run)?new Date(workspace(a.workspace).last_run).getTime():currentStart()):now;
    const invalid=[];
    const points=a.series_24h.hours.map((ts,i)=>{
      const v=a.series_24h[key][i],bad=key==='error_rate_pct'&&finite(v)&&(v<0||v>100);
      if(bad&&inRange(ts))invalid.push({ts,v});
      return {ts,v:bad||new Date(ts).getTime()>cutoff?null:v};
    }).filter(p=>inRange(p.ts));
    return seriesChart(points,title,unit,{threshold,start:currentStart(),end:now,hourly:true,cadence:'hourly',deploys:M.timeline.filter(t=>belongs(t,a)&&t.type==='deploy'&&inRange(t.ts)),note:`Dashed: ${referenceLabel} ${n(threshold,1)} ${unit}.${isStale(a)?' Feed cutoff applied.':''} Deploy markers show recorded releases.`})+(invalid.length?`<p class="chart-note danger">Invalid sample excluded: ${invalid.map(p=>`${pct(p.v,2)} at ${time(p.ts)} UTC`).join(', ')}.</p>`:'');
  }
  const destinations = [['fleet','Fleet overview','fleet'],['topology','Topology','stack'],['catalog','App catalog','fleet'],['ask','Ask Genie','search'],['alerts','Alerts','bell'],['investigations','Investigations','trace'],['reliability','Reliability','activity'],['costs','Costs','cost'],['governance','Governance','shield'],['usage','Usage','chart'],['workspaces','Workspaces','stack']];
  function chrome(route) {
    const active = route === 'app' || route === 'trace' ? 'investigations' : route;
    $('#sidebar').innerHTML = `<a href="#/fleet" class="brand"><span class="brand-mark">${icon('activity')}</span>Apps Monitor</a><button class="icon-button mobile-menu" aria-label="Toggle navigation" aria-expanded="${$('#sidebar').classList.contains('open')}" data-action="menu">${icon('menu')}</button><nav aria-label="Main navigation">${destinations.map(([id,label,ic],i)=>`${i===4?'<div class="nav-divider"></div>':''}<a href="#/${id}" class="nav-link ${active===id?'active':''}" ${active===id?'aria-current="page"':''}>${icon(ic)}<span>${label}</span>${id==='alerts'?`<span class="nav-count">${firing().length}</span>`:''}</a>`).join('')}</nav><div class="sidebar-bottom"><div class="sidebar-note"><strong>${icon('stack')} ${M.workspaces.length} workspaces connected</strong>${M.workspaces.filter(w=>w.status!=='OK').length} feed needs attention<br><a href="#/workspaces">View collection health →</a></div><div class="sidebar-note" style="margin-top:var(--space-lg)"><strong>${window.ConsoleData?.demo?'Demo data':esc(M.notes.workspace || 'Workspace fleet')}</strong>${window.ConsoleData?.demo?'Offline sample':'Refreshes every 60 s'}<br>All times in UTC<br><a href="${esc(window.ConsoleData.url('status'))}">Status page</a><br><a href="${esc(window.ConsoleData?.classic || '../classic')}">Classic fallback</a></div></div>`;
    $('#topbar').innerHTML = `<div class="scope">${icon('stack')}<label class="scope-label" for="workspace-select">Scope</label><select id="workspace-select" aria-label="Workspace scope"><option value="all">All workspaces</option>${M.workspaces.map(w=>`<option ${state.workspace===w.name?'selected':''} value="${esc(w.name)}">${esc(w.name)}</option>`).join('')}</select></div><div class="top-tools"><div class="time-control">${icon('clock')}<select id="range-select" aria-label="Global time range for charts and events">${[72,24,6,1].map(v=>`<option value="${v}" ${state.range===v?'selected':''}>Last ${v} hour${v===1?'':'s'} · UTC</option>`).join('')}</select></div><button class="search-trigger" data-action="search" aria-label="Quick search, Command or Control K">${icon('search')}<span class="search-label">Quick search</span><kbd>⌘ K</kbd></button></div>`;
    $('#footer-date').textContent = `Data as of ${stamp(M.generated_at)} · Charts & events: last ${state.range}h${window.ConsoleData?.demo?' · Demo data':' · Refresh: 60 s'}`;
  }
  function feeds() {
    return `<aside class="feed-panel"><h3>Can we trust the signal?</h3>${M.workspaces.filter(w=>state.workspace==='all'||state.workspace===w.name).map(w=>`<div class="feed"><div><strong>${esc(w.name)}</strong><small>Last collection ${time(w.last_run)} UTC</small></div>${tag(w.status!=='OK'?'stale':'healthy',w.status!=='OK'?`${age(validDate(w.last_run)?(now-new Date(w.last_run))/1000:null)} stale`:'Current')}</div>`).join('')}<p>Apps on a stale feed are unverified until collection resumes.</p><a class="row-action" href="#/workspaces">Inspect feeds ${icon('arrow')}</a></aside>`;
  }
  // "Every app, at a glance": small multiples ordered by severity; healthy tiles recede, problems carry colour + icon + word.
  function glanceChart(a) {
    const st = status(a), w = 220, h = 64, top = 6, bottom = 50;
    if (a.health === 'stopped') {
      const m = M.maintenance_windows.find(x => maintenanceApplies(x,a));
      return `<div class="glance-stopped">${icon('pause')}<span>${m ? `Planned stop until ${stamp(m.ends_at)}` : 'Stopped'}</span></div>`;
    }
    const pts = a.series_24h.hours.map((ts,i)=>({ts,v:a.series_24h.error_rate_pct[i]})).filter(p=>inRange(p.ts));
    if (!pts.some(p=>finite(p.v))) return '<div class="glance-stopped">Not collected yet</div>';
    const cutoff = isStale(a) ? (validDate(workspace(a.workspace).last_run)?new Date(workspace(a.workspace).last_run).getTime():currentStart()) : now;
    const live = pts.filter(p=>new Date(p.ts).getTime()<=cutoff);
    const usable = p => finite(p.v) && p.v>=0 && p.v<=100;
    const max = Math.max(...live.filter(usable).map(p=>p.v), 1) * 1.15;
    const x = ts => (new Date(ts).getTime()-currentStart())/(now-currentStart())*w;
    const y = v => bottom - v/max*(bottom-top);
    const line = live.map((p,i)=>usable(p)?`${i && usable(live[i-1])?'L':'M'}${x(p.ts).toFixed(1)},${y(p.v).toFixed(1)}`:'').join(' ');
    const area = live.length && live.every(usable) ? `${line} L${x(live.at(-1).ts).toFixed(1)},${bottom} L${x(live[0].ts).toFixed(1)},${bottom} Z` : '';
    const deploys = M.timeline.filter(t=>belongs(t,a) && t.type==='deploy' && inRange(t.ts));
    const staleX = isStale(a) ? Math.max(0, Math.min(w, x(cutoff))) : null;
    const peak = live.filter(usable).reduce((m,p)=>p.v>m.v?p:m, {v:0});
    const id = 'hatch-' + a.id, pc = v => (v / w * 100).toFixed(1) + '%';
    const svg = `<svg class="glance-chart tone-${st}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
      <defs><pattern id="${id}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" class="hatch-line"/></pattern></defs>
      <line class="glance-base" x1="0" x2="${w}" y1="${bottom}" y2="${bottom}"/>
      ${area?`<path class="glance-area" d="${area}"/><path class="glance-line" d="${line}"/>`:''}
      ${staleX!=null?`<rect x="${staleX}" y="${top}" width="${w-staleX}" height="${bottom-top}" fill="url(#${id})"/>`:''}
      ${deploys.map(t=>`<line class="glance-deploy" x1="${x(t.ts)}" x2="${x(t.ts)}" y1="0" y2="${bottom}"/>`).join('')}
    </svg>`;
    // labels live in HTML so they don't stretch with the non-uniformly scaled SVG
    const notes = [
      ...deploys.map(t=>`<span class="glance-note note-deploy" style="${x(t.ts)/w<.35?`left:calc(${pc(x(t.ts))} + 3px)`:`right:calc(100% - ${pc(x(t.ts))} + 3px)`}">deploy ${time(t.ts)}</span>`),
      ...(staleX!=null?[`<span class="glance-note note-stale" style="right:0">no data since ${time(cutoff)}</span>`]:[]),
    ].join('');
    const label = `${a.name} error rate over the last ${state.range} hours, peak ${pct(peak.v,1)}${deploys.length?', deploy at '+deploys.map(t=>time(t.ts)).join(', ')+' UTC':''}${isStale(a)?', no data since '+time(cutoff)+' UTC':''}`;
    return `<span class="glance-plot" role="img" aria-label="${esc(label)}">${svg}${notes}<span class="glance-axis"><span>${time(currentStart())}</span><span>${time(now)} UTC</span></span></span>`;
  }
  function glanceBudget(a) {
    const b = a.slo.error_budget_remaining_pct;
    if (b == null) return '<div class="glance-budget"><span>SLO budget</span><span class="muted">—</span></div>';
    const tone = b < 0 ? 'danger' : b < 25 ? 'warning' : 'success';
    const fill = Math.max(0, Math.min(100, b));
    return `<div class="glance-budget"><span>SLO budget<span class="glance-wide"> · 28d</span></span><span class="${tone==='success'?'':tone}">${b<0?'Exhausted':pct(b,0)}</span><span class="glance-bar" role="img" aria-label="Error budget ${b<0?'exhausted':pct(b,0)+' remaining'}"><span class="glance-fill tone-${tone}" style="width:${b<0?100:fill}%"></span></span></div>`;
  }
  // how long a problem has been open, from its oldest operational alert (security findings don't date an outage)
  function since(a) {
    if (!['down','degraded','stale'].includes(status(a))) return '';
    const ops = appAlerts(a).filter(x => !['critical_findings','review_reject','permission_drift','budget_burn','prompt_drift','idle_cost'].includes(x.rule));
    if (!ops.length) return '';
    const first = ops.reduce((m,x) => new Date(x.since) < new Date(m.since) ? x : m);
    return `<span class="glance-since">since ${time(first.since)}</span>`;
  }
  function glance(apps) {
    const order = [...apps].sort((x,y)=>healthRanks[status(x)]-healthRanks[status(y)] || (x.slo.error_budget_remaining_pct ?? 999)-(y.slo.error_budget_remaining_pct ?? 999));
    const tiles = order.map(a => {
      const st = status(a), quiet = st==='healthy' && !appAlerts(a).length;
      const over = overLatency(a);
      const flags = appAlerts(a).length ? `<span class="glance-alerts">${icon('bell')}${appAlerts(a).length}</span>` : '';
      return `<a class="glance-tile tile-${st}${quiet?' is-quiet':''}" href="#/app/${encodeURIComponent(a.id)}/overview">
        <span class="glance-head">${tag(st)}${since(a)}${flags}</span>
        <span class="glance-name">${['down','degraded','stale'].includes(st)?`<span class="glance-mark mark-${st}" aria-hidden="true"></span>`:''}${esc(a.name)}</span>
        <span class="glance-meta">${esc(a.team)} · ${esc(a.workspace)} · ${esc(a.kind)}</span>
        ${glanceChart(a)}
        ${a.health==='stopped' ? '' : `<span class="glance-stats">
          <span><small>Errors</small><strong class="${a.health==='down'?'danger':a.last24h.error_rate_pct>=1?'warning':''}">${pct(a.last24h.error_rate_pct,2)}</strong></span>
          <span><small>p95</small><strong class="${over?'warning':''}">${n(a.last24h.p95_ms)} ms</strong></span>
          <span><small>Requests</small><strong>${n(a.last24h.requests)}</strong></span>
        </span>${glanceBudget(a)}`}
      </a>`;
    }).join('');
    const legend = ['down','degraded','stale','idle','healthy','stopped'].map(s=>tag(s)).join('');
    return `<section class="glance">${sectionHead('Every app, at a glance','Ordered by severity. Healthy apps recede. Each chart is the 24 h error rate; dashed line = deploy, hatched = no data from a stale feed.')}<div class="glance-grid">${tiles}</div><div class="glance-legend" aria-label="Legend">${legend}<span class="legend-key"><svg viewBox="0 0 24 10" aria-hidden="true"><line x1="12" x2="12" y1="0" y2="10" class="glance-deploy"/></svg>deploy</span><span class="legend-key"><span class="legend-hatch"></span>stale feed</span></div></section>`;
  }
  function fleet() {
    const apps = scopedApps();
    const counts = ['down','degraded','stale','healthy','idle','stopped'].map(s=>[s,apps.filter(a=>status(a)===s).length]);
    const headlines = apps.filter(a=>['down','degraded'].includes(status(a)) || a.security.review_verdict==='reject');
    const attention = headlines.sort((a,b)=>healthRanks[status(a)]-healthRanks[status(b)]).map(a=>{
      const err = M.error_groups.find(e=>belongs(e,a) && e.new_since_deploy);
      const isDown = a.health==='down';
      const summary = isDown ? `${err?`${esc(err.type)} · ${n(err.count_24h)} events in 24h.`:'Availability checks or platform state report an outage. Open the investigation to inspect evidence.'}` : a.health==='degraded' ? `${burn(a)?`${burn(a)}×`:'—'} SLO burn · ${pct(percent(a.genai?.prompt_drift_novel_share),0)} novel prompts · forecast ${usd(a.cost.forecast_usd_month)} / ${usd(a.cost.budget_usd_month)} budget.` : `${n(a.security.secrets)} secret finding · ${n(a.security.cve.high)} high CVEs. Review rejected.`;
      return `<article class="attention-row">${icon(isDown?'down':'warning')}<div><div class="attention-title">${appLink(a)}${badge(isDown?'Critical':a.health==='degraded'?(burn(a)?'SLO at risk':'Degraded'):'Review rejected',isDown?'critical':'high')}</div><p>${summary}</p><small>${esc(a.team)} · ${appAlerts(a).length} firing alerts</small></div>${link(isDown?`#/app/${encodeURIComponent(a.id)}/investigate`:`#/app/${encodeURIComponent(a.id)}/${a.health==='degraded'?'overview':'security'}`,`${isDown?'Investigate':'Review'} ${icon('arrow')}`,'row-action')}</article>`;
    }).join('');
    const rows = apps.filter(a=>(state.health==='all'||status(a)===state.health) && (state.team==='all'||a.team===state.team) && `${a.name} ${a.team} ${a.owner}`.toLowerCase().includes(state.search.toLowerCase()));
    const fleetColumns = [
      {key:'name',label:'Application',html:a=>`${appLink(a)}<small>${esc(a.team)} · ${esc(a.workspace)}</small>`},
      {key:'health',label:'Health',value:a=>healthRanks[status(a)],html:a=>`${tag(status(a))}${isStale(a)?`<small>Last: ${esc(a.health)}</small>`:a.health==='stopped'?'<small>Platform stopped</small>':''}`},
      {key:'p95',label:'p95 latency',num:true,value:a=>a.last24h.p95_ms,html:a=>a.health==='stopped'?'—':`<div class="metric-inline">${!isStale(a)?spark(a):''}<span class="${overLatency(a)?'warning':''}">${n(a.last24h.p95_ms)} ms</span></div><small>Target ≤ ${n(a.slo.latency_threshold_ms)} ms${isStale(a)?' · stale':''}</small>`},
      {key:'errors',label:'Errors · 24h',num:true,value:a=>a.last24h.error_rate_pct,html:a=>a.health==='stopped'?'—':`<span class="${a.health==='down'?'danger':''}">${pct(a.last24h.error_rate_pct,2)}</span>`},
      {key:'budget',label:'SLO budget',num:true,value:a=>a.slo.error_budget_remaining_pct ?? Infinity,html:a=>a.slo.error_budget_remaining_pct==null?'—':`<span class="${a.slo.error_budget_remaining_pct<0?'danger':''}">${a.slo.error_budget_remaining_pct<0?'Exhausted':pct(a.slo.error_budget_remaining_pct,1)}</span><small>28 days${isStale(a)?' · stale':''}</small>`},
      {key:'attention',label:'Also watch',value:a=>appAlerts(a).length,html:a=>a.security.review_verdict==='reject'?link(`#/app/${encodeURIComponent(a.id)}/security`,'Review rejected'):a.governance.permission_drift?link(`#/app/${encodeURIComponent(a.id)}/security`,'Permission drift'):a.health==='idle'?link(`#/app/${encodeURIComponent(a.id)}/cost`,`${usd(a.cost.idle_usd)} idle spend`):a.security.cve.critical?link(`#/app/${encodeURIComponent(a.id)}/security`,`${a.security.cve.critical} critical CVE`):a.genai?.prompt_drift_novel_share>=.3?link(`#/app/${encodeURIComponent(a.id)}/agents`,'Prompt drift'):a.health==='stopped'?'<span class="muted">Stopped</span>':'<span class="muted">—</span>'}
    ];
    return pageHead('Fleet overview',`<strong class="${counts[0][1]?'danger':''}">${counts[0][1]} app${counts[0][1]===1?'':'s'} down.</strong> ${counts[1][1]} degraded · ${counts[2][1]} need a fresh signal.`, `<div class="snapshot">${icon('clock')}As of ${time(M.generated_at)} UTC<br>${date(M.generated_at)} ${new Date(now).getUTCFullYear()}</div>`) +
      `<div class="summary-strip">${counts.map(([s,c])=>link(`#/fleet?health=${s}`,`<strong class="status-${esc(s)}">${c}</strong>${tag(s)}`,'summary-item')).join('')}</div>`+
      `<div class="overview-grid"><section>${sectionHead('Needs attention','Prioritized by impact; related alerts stay together.',link('#/alerts',`All ${firing().length} firing alerts ${icon('arrow')}`))}<div class="attention-list">${attention||empty('No urgent app incidents','No fresh apps are down or degraded, and no code reviews are rejected in this scope.')}</div></section>${feeds()}</div>`+
      glance(apps) +
      `<section>${sectionHead('Applications',`${apps.length} apps across ${state.workspace==='all'?M.workspaces.length:1} workspace${state.workspace==='all'?'s':''} · health first`,link('#/reliability',`SLO overview ${icon('arrow')}`))}<div class="toolbar">${searchField('search','Find an app',state.search,'App, team or owner')}${selectField('health','Health',state.health,[['all','All health states'],...counts.map(([s,c])=>[s,`${statusNames[s]} (${c})`])])}${selectField('team','Team',state.team,[['all','All teams'],...[...new Set(apps.map(a=>a.team))].sort().map(t=>[t,t])])}<span class="toolbar-end" role="status">${rows.length} of ${apps.length} apps</span></div>${rows.length?dataTable('Fleet applications',rows,fleetColumns,'health'):empty('No apps match these filters','Try a different name or clear the filters.', '<button class="button" data-action="clear-fleet">Clear filters</button>')}<p class="table-note">Latency and errors: 24h aggregates. Sparklines: 24h p95, independently scaled. SLO budget: 28 days. Stale values are last reported.</p></section>`;
  }
  function appHeader(a,tab) {
    const tabs = [['overview','Overview'],['errors','Errors'],['traces','Traces'],['logs','Logs'],['traffic','Traffic'],['dependencies','Dependencies'],['changes','Changes'],['security','Code & security'],['cost','Cost'],['ai','AI usage'],['usage','Usage'],['product','Product & guardrails'],['operate','Operate'],['browser','Browser checks'],['telemetry','Telemetry']];
    return breadcrumb([esc(a.name)])+pageHead(a.name,`${tag(status(a))} &nbsp; ${esc(a.team)} · ${esc(a.workspace)} · ${esc(a.kind)}`,link(`#/app/${encodeURIComponent(a.id)}/investigate`, `Investigate ${icon('arrow')}`,'button primary'))+
      (isStale(a)?notice('Health is unverified',`The ${esc(a.workspace)} feed last collected at ${stamp(workspace(a.workspace).last_run)}. Last reported app health: ${esc(a.health)}. Values below may be outdated.`):'')+
      (a.health==='stopped'?notice('Intentionally stopped',`${esc(M.maintenance_windows.find(w=>maintenanceApplies(w,a))?.reason || 'Platform reports this application stopped')}. ${M.maintenance_windows.find(w=>maintenanceApplies(w,a))?'Alert suppression ends '+stamp(M.maintenance_windows.find(w=>maintenanceApplies(w,a)).ends_at)+'.':'No maintenance window is recorded.'} No request or SLO observations are available.`,''):'')+
      P.head(a)+`<nav class="tabs app-tabs" aria-label="Application sections">${tabs.map(([id,label])=>link(`#/app/${encodeURIComponent(a.id)}/${id}`,label,tab===id?'active':'')).join('')}</nav>`;
  }
  function appOverview(a) {
    const s=a.slo, b=burn(a);
    const alerts=appAlerts(a);
    const slo = `<div class="metrics">${metric('Availability · 28d',pct(s.attainment_28d,3),`Target ${pct(s.availability_target,1)}`,s.attainment_28d!=null&&s.attainment_28d<s.availability_target?'danger':'')}${metric('Error budget remaining',pct(s.error_budget_remaining_pct,1),s.error_budget_remaining_pct<0?'Exhausted · negative values preserved':'28-day window',s.error_budget_remaining_pct<0?'danger':'')}${metric('Current SLO burn',b?`${b}×`:'—',b?esc(alerts.find(x=>x.rule.startsWith('slo_')).message.replace(/^.*?over /,'Over ')):'No active burn alert supplied',b?'warning':'')}${metric('Requests · 24h',n(a.last24h.requests),`${n(a.last24h.active_users)} active users`)}</div>`;
    const samples=a.series_24h.requests.filter(finite); const average=samples.length?sum(samples,v=>v)/samples.length:null;
    const chartView = a.health==='stopped'?empty('Application stopped','Current platform state is stopped. Historical observations, if any, remain in the summaries.'):
      `<div class="chart-grid">${chart(a,'p95_ms','Latency · p95','ms',s.latency_threshold_ms,'SLO threshold')}${chart(a,'requests','Request volume','req',average,'24h hourly mean')}${chart(a,'error_rate_pct','Request errors','%',a.last24h.error_rate_pct,'24h aggregate')}</div><p class="table-note">Charts use the global ${state.range}h window. Deploy markers are event records. Saturation: not supplied.</p>`;
    return slo+chartView+`<div class="detail-grid"><section>${sectionHead('What changed','Deployments and alerts in the selected time window.')}${timeline(a)}</section><section>${sectionHead('Synthetic journeys','Independent checks of the user path.')}${synthetics(a)}</section></div><div class="detail-grid"><section>${sectionHead('Application record')}${facts([['Owner',esc(a.owner)],['Inventory version',esc(a.version)],['Inventory deployment',stamp(a.deployed_at)],['Platform state',esc(a.status)],['Workspace',a.workspace]])}<p class="table-note">Inventory and event versions are displayed separately; the snapshot does not reconcile them.</p></section><section>${sectionHead('Related signals')}${facts([['Error groups',link(`#/app/${encodeURIComponent(a.id)}/investigate`,String(M.error_groups.filter(e=>belongs(e,a)).length))],['Month-to-date cost',link(`#/app/${encodeURIComponent(a.id)}/cost`,usd(a.cost.mtd_usd,2))],['Code review',link(`#/app/${encodeURIComponent(a.id)}/security`,esc(a.security.review_verdict.replaceAll('_',' ')))],['Envelope coverage',link(`#/app/${encodeURIComponent(a.id)}/telemetry`,pct(a.telemetry.envelope_coverage_pct,1))]])}</section></div>`;
  }
  function timeline(a) {
    const items=M.timeline.filter(t=>belongs(t,a)&&inRange(t.ts)).sort((a,b)=>new Date(b.ts)-new Date(a.ts));
    return items.length?`<ol class="timeline">${items.map(t=>`<li><time datetime="${t.ts}">${time(t.ts)}</time><div><p>${esc(t.text)}</p><small>${date(t.ts)} · ${esc(t.type)}</small></div></li>`).join('')}</ol>`:empty('No changes in this window','Choose a wider time range to inspect earlier activity.');
  }
  function synthetics(a) {
    const checks = M.synthetics.filter(s=>belongs(s,a));
    return checks.length?`<div class="checks">${checks.map(s=>`<div class="check-row"><div class="check-title"><strong>${esc(s.journey)}</strong>${tag(s.ok==null?'stale':s.ok?'ok':'error')}</div><small>${esc(s.vantage)} vantage · ${stamp(s.last_run)}</small><div class="history" role="img" aria-label="Last ${s.history.length} runs, oldest to newest: ${s.history.map(x=>x==null?'unknown':x?'pass':'fail').join(', ')}">${s.history.map(x=>`<span class="${x==null?'':x?'pass':'fail'}" aria-hidden="true"></span>`).join('')}</div>${s.failed_step?`<p class="danger small">${esc(s.failed_step)} · ${esc(s.failure_stage)} failure</p>`:''}</div>`).join('')}<small>Most recent check at right. Check history is the supplied run sequence.</small></div>`:empty('Synthetic checks not collected yet','Availability has no independent user-journey check in this snapshot.');
  }
  function errorGroups(a) {
    const errors=M.error_groups.filter(e=>belongs(e,a)).sort((a,b)=>b.count_24h-a.count_24h);
    return errors.length?errors.map(e=>`<article class="issue-block"><div class="inline"><h3>${esc(e.type)}</h3>${e.new_since_deploy?badge('New since deploy','warning'):''}</div><p><code>${esc(e.route)}</code></p><p>${esc(e.message)}</p><p class="muted small">${n(e.count_24h)} events · 24h · First seen ${stamp(e.first_seen)}<br>Last seen ${stamp(e.last_seen)}</p><div class="actions">${link(`#/app/${encodeURIComponent(a.id)}/error/${e.fingerprint}`,`Open error group ${icon('arrow')}`,'button')}${e.sample_trace_id?link(`#/trace/${e.sample_trace_id}?app=${a.name}`,`${e.sample_trace_id===M.trace_example.trace_id?'Example trace':'Open trace'} ${icon('trace')}`,'button'):badge('No trace reference')}</div></article>`).join(''):empty('No error groups reported','No grouped exceptions are available. A missing source means they are not collected yet.',link(`#/app/${encodeURIComponent(a.id)}/overview`,'Back to overview','button'));
  }
  function investigate(a) {
    const loading = ensureErrors(a);
    return sectionHead('Error groups','Grouped by fingerprint · counts cover 24 hours.')+loading+errorGroups(a)+`<div class="detail-grid"><section>${sectionHead('Deployment & incident timeline')}${timeline(a)}</section><section>${sectionHead('Next investigation step')}<div class="feed-panel"><p>Open an error group to inspect its trace, then compare the timeline and synthetic checks. Timing alone does not establish a cause.</p>${M.trace_example.trace_id?link(`#/trace/${M.trace_example.trace_id}`,'Open available trace →','row-action'):''}</div></section></div>`;
  }
  function errorDetail(a,fingerprint) {
    const e=M.error_groups.find(e=>belongs(e,a)&&e.fingerprint===fingerprint);
    if(!e)return detailState.get('errors:'+a.id)==='loading'?'':missing('Error group not found');
    return breadcrumb([link(`#/app/${encodeURIComponent(a.id)}/overview`,esc(a.name)),link(`#/app/${encodeURIComponent(a.id)}/investigate`,'Errors'),esc(String(e.fingerprint || '—').slice(0,8))])+pageHead(e.type,esc(e.message))+
      `<div class="metrics">${metric('Events · 24h',n(e.count_24h),esc(e.route),'danger')}${metric('First seen',time(e.first_seen),date(e.first_seen)+' · UTC')}${metric('Last seen',time(e.last_seen),date(e.last_seen)+' · UTC')}${metric('Release correlation',e.new_since_deploy==null?'Not collected yet':e.new_since_deploy?'New':'Existing','Relative to deployment')}</div>`+
      facts([['Fingerprint',`<code>${e.fingerprint}</code>`],['Example trace',e.sample_trace_id?`<code class="trace-id">${e.sample_trace_id}</code>`:'Not supplied']])+
      `<div class="actions" style="margin-top:var(--space-lg)">${e.sample_trace_id?link(`#/trace/${e.sample_trace_id}?app=${a.name}`,`Open trace ${icon('arrow')}`,'button primary'):''}${link(`#/app/${encodeURIComponent(a.id)}/investigate`,'Back to investigation','button')}</div>`+
      (e.sample_trace_id!==M.trace_example.trace_id?notice('Trace payload not supplied','This error group contains a reference only. The snapshot has no matching spans or correlated logs. The trace view preserves this missing-data state.',''):'')+
      `<div class="detail-grid"><section>${sectionHead('What changed')}${timeline(a)}</section><section>${sectionHead('User-path checks')}${synthetics(a)}</section></div>`;
  }
  function genai(a) {
    const g=a.genai;if(!g)return empty('This app has no GenAI metrics','Select an agent application to inspect model calls and evaluations.');
    return (g.prompt_drift_novel_share>=.3?notice('Prompt distribution has shifted',`${pct(percent(g.prompt_drift_novel_share),0)} of this week’s prompts fall outside last week’s clusters. Review changes alongside model errors and answer completion.`):'')+
      `<div class="metrics">${metric('Model calls · '+(esc(g.period || '24h')),n(g.calls_24h),'Across supplied models')}${metric('Input tokens · '+(esc(g.period || '24h')),n(g.input_tokens_24h),'Exact token count')}${metric('Output tokens · '+(esc(g.period || '24h')),n(g.output_tokens_24h),'Exact token count')}${metric('Time to first token · p95',`${n(g.ttft_p95_ms)} ms`,'24h · no threshold supplied')}</div><div class="detail-grid"><section>${sectionHead('Model behavior')}${facts([['Models',g.models.map(esc).join('<br>')],...Object.entries(g.error_classes_24h).map(([k,v])=>[`${esc(k.replaceAll('_',' '))} errors · 24h`,n(v)]),['Novel prompts · 7d',pct(percent(g.prompt_drift_novel_share),0)]])}</section><section>${sectionHead('Quality & guardrails')}${facts([...Object.entries(g.quality).map(([k,v])=>[esc(k),n(v,1)]),['User feedback · 7d',`${n(g.feedback.avg_stars,1)} stars · ${n(g.feedback.count_7d)} ratings`],...Object.entries(g.guardrail_findings_7d).map(([k,v])=>[`${esc(k)} findings · 7d`,n(v)])])}<p class="table-note">Judge score scales and passing thresholds are not supplied; scores are not treated as pass/fail.</p></section></div><div class="actions" style="margin-top:var(--space-lg)">${link(`#/app/${encodeURIComponent(a.id)}/investigate`,'Investigate model errors','button')}${a.name===M.trace_example.app?link(`#/trace/${M.trace_example.trace_id}?app=${a.name}`,'Open agent waterfall','button primary'):''}${a.name===M.funnel_example.app?link('#/usage','Compare answer completion','button'):''}</div>`;
  }
  function budget(a) {
    if (fraction(a.cost.mtd_usd,a.cost.budget_usd_month)==null) return '<p class="table-note">Budget comparison not collected yet.</p>';
    return `<div class="budget-track ${overBudget(a)?'over':''}" role="img" aria-label="${pct(a.cost.mtd_usd/a.cost.budget_usd_month*100,1)} of monthly budget spent"><svg viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true"><rect class="budget-fill" width="${Math.min(100,a.cost.mtd_usd/a.cost.budget_usd_month*100)}" height="12" rx="1"/></svg></div>`;
  }
  function appCost(a) {
    const c=a.cost, variance=finite(c.forecast_usd_month)&&finite(c.budget_usd_month)?c.forecast_usd_month-c.budget_usd_month:null;
    return sectionHead('Monthly spend','USD · month to date and month-end forecast.')+`<div class="metrics">${metric('Actual · MTD',usd(c.mtd_usd,2),`${pct(fraction(c.mtd_usd,c.budget_usd_month),1)} of budget used`)}${metric('Monthly budget',usd(c.budget_usd_month),month())}${metric('Forecast · estimate',usd(c.forecast_usd_month,2),variance==null?'Not collected yet':`${usd(Math.abs(variance),2)} ${variance>0?'over':'under'} budget`,variance>0?'danger':'')}${metric('Idle compute · MTD',usd(c.idle_usd,2),`${pct(fraction(c.idle_usd,c.mtd_usd),1)} of actual`)}</div>${budget(a)}`+
      (a.health==='idle'?notice('Running without real traffic',`${esc(a.name)} is idle with ${usd(c.idle_usd,2)} of idle compute recorded this month. Auto-stop policy: ${esc(a.governance.auto_stop)}. Review with ${esc(a.owner)} before stopping the app.`):'')+
      `<div class="detail-grid"><section>${sectionHead('Cost composition')}${facts([['Compute · list-price valuation',usd(c.dbu_usd,2)],['AI · token × list-price estimate',usd(c.ai_usd,2)],['Reported actual · MTD',usd(c.mtd_usd,2)],['Unit cost · per 1,000 requests',usd(c.usd_per_1k_requests,3)],['Chargeback team',esc(a.team)],['Cost center',a.cost_center]])}</section><section>${sectionHead('Cost basis')}<p>Compute is valued from billing usage at list prices. AI cost uses exact token counts multiplied by model list prices and is an estimate.</p>${[c.dbu_usd,c.ai_usd,c.mtd_usd].every(finite)&&Math.abs(c.dbu_usd+c.ai_usd-c.mtd_usd)>.01?notice('Component totals differ',`Compute plus AI is ${usd(c.dbu_usd+c.ai_usd,2)}; the reported actual is ${usd(c.mtd_usd,2)}. Both source values are preserved.`,''):''}<p class="table-note">The idle-cost alert may reflect an earlier evaluation. Its message is retained in Alerts; this view uses the app cost record.</p>${link('#/costs','Compare fleet costs →','row-action')}</section></div>`;
  }
  function security(a) {
    const s=a.security,g=a.governance;
    const related=appAlerts(a).filter(x=>['critical_findings','review_reject','permission_drift'].includes(x.rule));
    return related.map(x=>notice(x.rule.replaceAll('_',' '),esc(x.message),x.severity==='critical'?'error':'warning')).join('')+
      `<div class="metrics">${metric('Critical CVEs',n(s.cve.critical),'Latest scan',s.cve.critical?'danger':'')}${metric('High CVEs',n(s.cve.high),'Latest scan',s.cve.high?'warning':'')}${metric('Secret findings',n(s.secrets),'Latest scan',s.secrets?'danger':'')}${metric('Required tags',g.tags_complete==null?'Not collected yet':g.tags_complete?'Complete':'Incomplete',M.governance.required_tags.map(esc).join(' · '),g.tags_complete?'':'warning')}</div><div class="detail-grid"><section>${sectionHead('Production review')}${facts([['Verdict',badge(s.review_verdict.replaceAll('_',' '),s.review_verdict==='reject'?'critical':'')],['Review score',n(s.review_score)],['Quality score',n(s.quality_score)],['Medium / low CVEs',`${n(s.cve.medium)} / ${n(s.cve.low)}`],['Outdated packages',n(s.outdated_packages)],['Scan completed',stamp(s.last_scan)]])}<p class="table-note">Use the supplied review verdict; score thresholds are not available.</p></section><section>${sectionHead('Policy & ownership')}${facts([['Permission drift',g.permission_drift==null?'Not collected yet':g.permission_drift?tag('warning','Detected'):tag('healthy','None reported')],['Owner',esc(a.owner)],['Team',esc(a.team)],['Cost center',a.cost_center],['Tag coverage',g.tags_complete==null?'Not collected yet':g.tags_complete?'Complete':'Incomplete · missing keys unspecified'],['Auto-stop',esc(g.auto_stop)]])}</section></div><section style="margin-top:var(--space-xl)">${sectionHead('Audit trail')}${audit(M.governance.audit_events.filter(e=>belongs(e,a)))}</section>`;
  }
  function telemetry(a) {
    const t=a.telemetry;
    return sectionHead('Telemetry quality','Coverage measures what can be correlated across requests, spans and logs.')+
      `<div class="metrics">${metric('Envelope coverage',pct(t.envelope_coverage_pct,1),'No target supplied')}${metric('Sampling ratio',pct(percent(t.sampler_ratio),0),'Configured ratio')}${metric('Orphan spans',pct(t.orphan_span_pct,1),'Reported share of spans')}${metric('Last span age',age(t.last_span_age_s),'Relative to snapshot')}</div>`+
      facts([['SDK version',a.sdk_version?esc(a.sdk_version):'Not reported'],['OpenTelemetry export',t.otel_export==null?'Not collected yet':t.otel_export?'Observed':'Disabled'],['Workspace feed',tag(isStale(a)?'stale':'healthy',isStale(a)?'Stale':'Current')],['Last workspace collection',stamp(workspace(a.workspace).last_run)],['Platform state',esc(a.status)]])+
      (!a.sdk_version?notice('SDK version is missing','A missing SDK version does not prove that telemetry is absent. Check export and envelope coverage separately.',''):'')+
      (a.series_24h.error_rate_pct.some(v=>v>100)?notice('Invalid error-rate sample',`The source includes ${pct(Math.max(...a.series_24h.error_rate_pct),2)}. That sample is excluded from the chart, not clamped to 100%.`):'')+
      `<p class="table-note">Head-sampled traces can be incomplete. Missing trace payloads are shown explicitly instead of substituting another app’s request.</p>`;
  }
  function appPage(name,tab='overview',extra) {
    const a=app(name);if(!a)return missing('Application not found');
    if(tab==='error')return ensureErrors(a)+errorDetail(a,extra);
    tab=({investigate:'errors',agents:'ai',genai:'ai',requests:'traffic',deps:'dependencies',timeline:'changes',quality:'security',adoption:'usage',ops:'operate',probes:'operate',uptime:'operate',synthetics:'operate',uitests:'browser',playwright:'browser',review:'security',agent:'traces'})[tab]||tab;
    const allowed=['overview','errors','traces','logs','traffic','dependencies','changes','security','cost','ai','usage','product','operate','browser','telemetry','agent-trace'];
    if(!allowed.includes(tab))return missing('Application section not found');
    return appHeader(a,tab)+(tab==='overview'?appOverview(a):'')+P.appSection(a,tab,extra);
  }
  function provenance() {
    const unavailable=Object.entries(M.sources).filter(([,v])=>v!=='ok').map(([k,v])=>`${P.title(k)}: ${P.title(v)}`);
    if(connectionError) return notice('Snapshot refresh failed',`${esc(connectionError)} <button class="button" data-action="retry-snapshot">Retry</button>`,'error');
    if(M.notes.collecting) return notice('Warehouse data is loading','Live inventory and probes are available. Other sources will appear on refresh. <button class="button" data-action="retry-snapshot">Refresh now</button>','');
    return unavailable.length?notice('Partial data',`Some measurements are not collected yet. <details><summary>Source availability (${unavailable.length})</summary><p>${unavailable.map(esc).join(' · ')}</p></details>`,''):'';
  }
  function detailNotice(key, title) {
    const value=detailState.get(key);
    if(value==='loading')return `<div class="loading" role="status"><h2>Loading ${esc(title)}…</h2><div class="skeleton"></div></div>`;
    if(value==='missing')return empty(`${title} not found`,'No matching data exists in this workspace and retention window.',link('#/investigations','Back to investigations','button'));
    if(value==='error')return notice(`${title} could not load`,`The source is unavailable. <button class="button" data-action="retry-detail" data-detail="${esc(key)}">Retry</button>`,'error');
    return '';
  }
  function loadDetail(key,path,accept) {
    if(detailState.has(key))return;
    detailState.set(key,'loading');
    const request=window.ConsoleData.get(path);
    request.then(data=>{accept(data);detailState.set(key,'ok');}).catch(error=>{detailState.set(key,error.status===404||error.status===422?'missing':'error');}).finally(()=>renderPreserving());
  }
  function ensureErrors(a) {
    if(a.remote || window.ConsoleData?.demo || !M.notes.errors_top_n)return '';
    const key='errors:'+a.id;
    loadDetail(key,`api/console/apps/${encodeURIComponent(a.name)}/errors`,data=>{
      errorDetails.set(a.id,list(data.error_groups));
      M.error_groups=M.error_groups.filter(e=>!belongs(e,a)).concat(list(data.error_groups));
    });
    return detailNotice(key,'Error groups');
  }
  function tracePage(id,from) {
    const t=M.traces[id];
    if(!t) {
      loadDetail('trace:'+id,`api/console/trace/${encodeURIComponent(id)}`,data=>{M.traces[id]=data;});
      return breadcrumb([link('#/investigations','Investigations'),'Trace'])+pageHead('Trace',`<code class="trace-id">${esc(id)}</code>`)+detailNotice('trace:'+id,'Trace');
    }
    t.spans=list(t.spans).map(s=>({...s, attrs:record(s.attrs)}));t.logs=list(t.logs);
    if(!t.spans.length)return empty('Trace has no spans','Not collected yet.');
    const depth=s=>{let level=0;const seen=new Set([s.id]);while(s.parent&&!seen.has(s.parent)){seen.add(s.parent);s=t.spans.find(p=>p.id===s.parent);if(!s)break;level++;}return Math.min(level,8);};
    const selected=t.spans.find(s=>s.id===state.selectedSpan)||t.spans[0];
    const logs=t.logs.filter(l=>state.logLevel==='all'||l.severity===state.logLevel);
    return breadcrumb([link(`#/app/${esc(t.app)}/overview`,t.app),link(`#/app/${esc(t.app)}/investigate`,'Errors'),'Trace'])+
      (t.sources?.logs && t.sources.logs!=='ok'?notice('Correlated logs unavailable','The spans loaded; the log source is missing or failed.',''):'')+pageHead(t.root,`${tag(t.status==='error'?'error':t.status==='ok'?'ok':'stale',t.status==='error'?'Error':t.status==='ok'?'OK':'Unknown')} &nbsp; ${stamp(t.started_at)} · ${esc(t.app)}`,`<button class="button" data-copy="${esc(t.trace_id)}">${icon('copy')} Copy trace ID</button>`)+
      `<p class="mono small trace-id">${t.trace_id}</p>${!inRange(t.started_at)?notice('Pinned request is outside the global window','A direct trace link retains the exact request. Change the time range to include it.',''):''}`+
      `<div class="metrics">${metric('Request duration',`${n(t.duration_ms)} ms`,`${t.spans.length} spans`)}${metric('Services',n(new Set(t.spans.map(s=>s.service)).size),[...new Set(t.spans.map(s=>esc(s.service)))].join(' → '))}${metric('Failed spans',n(t.spans.filter(s=>s.status==='error').length),'Includes propagated errors','danger')}${metric('Session',esc(t.session_id),'User '+esc(t.user_hash))}</div>`+
      sectionHead('Request waterfall','Select a span to inspect its attributes. All positions use actual start times and durations.')+
      `<div class="waterfall-axis"><span>0 ms</span><span>${n(finite(t.duration_ms)?t.duration_ms/2:null)} ms</span><span>${n(t.duration_ms)} ms</span></div><div class="waterfall">${t.spans.map(s=>`<button class="span-row ${selected.id===s.id?'selected':''}" data-span="${esc(s.id)}" aria-pressed="${selected.id===s.id}" aria-label="${esc(s.kind)} ${esc(s.name)}, ${esc(s.status)}, ${s.duration_ms} milliseconds"><span class="span-name" style="--depth:${depth(s)}"><strong>${esc(s.name)}</strong><small>${esc(s.kind)} · ${esc(s.service)} · ${s.status==='error'?'× error':s.status==='ok'?'✓ ok':'? unknown'}</small></span><svg class="span-track" viewBox="0 0 1000 28" preserveAspectRatio="none" aria-hidden="true"><rect class="span-bar ${s.status==='error'?'error':''}" x="${(fraction(s.start_ms,t.duration_ms) || 0)*10}" y="9" width="${(fraction(s.duration_ms,t.duration_ms) || 0)*10}" height="10" rx="2"/></svg><span class="span-duration">${n(s.duration_ms)} ms</span></button>`).join('')}</div>`+
      `<div class="span-detail"><h3>${esc(selected.kind)} · ${esc(selected.name)}</h3>${facts([['Service',appLink(app(selected.service),'overview',selected.service)],['Start / duration',`${n(selected.start_ms)} ms / ${n(selected.duration_ms)} ms`],...Object.entries(selected.attrs).map(([k,v])=>[esc(P.title(k)),P.cell(v,k)])])}${Object.keys(selected.attrs).length?'':'<p class="table-note">No additional attributes supplied for this span.</p>'}</div>`+
      `<section style="margin-top:var(--space-xl)">${sectionHead('Correlated logs',`Same trace ID · ${t.logs.length} log records · offsets from request start`)}<div class="toolbar">${selectField('logLevel','Severity',state.logLevel,[['all','All severities'],['INFO','Info'],['WARN','Warning'],['ERROR','Error']])}</div><div class="logs">${logs.map(l=>`<div class="log-row"><span class="log-meta">+${n(l.ts_ms)} ms · ${esc(l.severity)} · ${esc(l.service)}</span><span>${esc(l.body)}</span></div>`).join('')||'<p>No logs match this severity or logs are not collected yet.</p>'}</div></section>`;
  }
  function alerts() {
    const all=scopedAlerts();
    const groups={firing:all.filter(x=>x.state==='firing'&&!x.muted),resolved:all.filter(x=>x.state==='resolved'&&!x.muted),muted:all.filter(x=>x.muted)};
    const rows=groups[state.alertTab].filter(x=>state.severity==='all'||x.severity===state.severity);
    return pageHead('Alerts',`${groups.firing.length} firing · grouped investigations are one click away.`)+
      `<nav class="tabs" aria-label="Alert state">${Object.keys(groups).map(key=>`<button data-alert-tab="${key}" class="${key===state.alertTab?'active':''}" aria-pressed="${key===state.alertTab}">${key[0].toUpperCase()+key.slice(1)} ${badge(groups[key].length)}</button>`).join('')}</nav>`+
      `<div class="toolbar">${selectField('severity','Severity',state.severity,[['all','All severities'],...Object.keys(ranks).map(s=>[s,statusNames[s]])])}<span class="toolbar-end">${rows.length} alerts</span></div>`+
      (rows.length?dataTable('Alerts',rows,[{key:'severity',label:'Severity',value:x=>ranks[x.severity],html:x=>tag(x.severity)},{key:'app',label:'Application / rule',html:x=>`${appLink(app(x.app),'investigate')}<small>${esc(P.title(x.rule))}</small>`},{key:'message',label:'Evidence',html:x=>`<div style="max-width:60ch">${esc(x.message)}</div>`},{key:'since',label:'Since · UTC',html:x=>`${time(x.since)}<small>${date(x.since)}</small>`},{key:'state',label:'State',html:x=>tag(x.muted?'muted':x.state==='resolved'?'resolved':x.severity,x.muted?'Muted':x.state==='resolved'?'Resolved':'Firing')}],'severity'):empty('No matching alerts',state.alertTab==='firing'?'No unmuted alerts are firing for this scope and severity. Broaden the filter to review other signals.':'No alerts are in this state for the selected scope.'))+
      `<section style="margin-top:var(--space-xl)">${sectionHead('Maintenance windows','Planned stops stay distinct from incidents.')}${maintenance()}</section><p class="table-note">Firing alerts persist regardless of their start time. Alert text is the original evaluation; newer app records may differ. Manage alert and application policies below or in Operate.</p>`;
  }
  function maintenance() {
    const rows=M.maintenance_windows.filter(w=>scopedApps().some(a=>maintenanceApplies(w,a)));
    return rows.length?rows.map(w=>`<div class="notice">${icon('pause')}<div><strong>${esc(w.app)} · ${esc(w.reason)}</strong><p>${stamp(w.starts_at)} → ${stamp(w.ends_at)}</p><small>Rule ${esc(P.title(w.rule))} · created by ${esc(w.created_by)} · ${new Date(w.starts_at)<=now&&new Date(w.ends_at)>=now?'Active':'Outside snapshot time'}</small><br>${link(`#/app/${w.app}/overview`,'View application →')}</div></div>`).join(''):empty('No maintenance windows','No planned alert suppression is recorded for this scope.');
  }
  function investigations() {
    const groups=M.error_groups.filter(e=>scopedApps().some(a=>belongs(e,a)));
    return pageHead('Investigations','Start with an error group, then follow the request.')+
      dataTable('Error groups',groups,[{key:'app',label:'Application',html:e=>appLink(app(e.app),'investigate')},{key:'type',label:'Error group',html:e=>`${link(`#/app/${e.app}/error/${e.fingerprint}`,esc(e.type))}<small>${esc(e.route)}</small>`},{key:'count_24h',label:'Events · 24h',num:true,html:e=>n(e.count_24h)},{key:'first_seen',label:'First seen · UTC',html:e=>stamp(e.first_seen)},{key:'trace',label:'Trace coverage',value:e=>e.sample_trace_id?0:1,html:e=>e.sample_trace_id?link(`#/trace/${e.sample_trace_id}?app=${e.app}`,'Waterfall + logs →'):e.sample_trace_id?badge('Reference only','warning'):badge('Not supplied')}],'count_24h',-1)+
      (M.trace_example.trace_id?`<div class="notice" style="margin-top:var(--space-lg)">${icon('trace')}<div><strong>A complete trace is available</strong><p>${esc(M.trace_example.app)} · ${stamp(M.trace_example.started_at)}</p>${link(`#/trace/${M.trace_example.trace_id}`,'Explore the trace →')}</div></div>`:'<p class="table-note">Fleet top error groups · select an app for its groups. Trace payloads load on demand from the local workspace.</p>');
  }
  function reliability() {
    const apps=scopedApps();
    return pageHead('Reliability','Availability objectives and error budgets · 28-day window.')+
      notice('Read stale SLOs as last reported',`Missing objectives or observations remain blank. Availability tiles use unfiltered 28-day SLOs; all configured windows and editors are available in each app’s Operate section.`,'')+
      dataTable('Reliability objectives',apps,[{key:'name',label:'Application',html:a=>`${appLink(a)}<small>${tag(status(a))}</small>`},{key:'attainment',label:'Attainment',num:true,value:a=>a.slo.attainment_28d??Infinity,html:a=>pct(a.slo.attainment_28d,3)},{key:'target',label:'Target',num:true,value:a=>a.slo.availability_target,html:a=>pct(a.slo.availability_target,1)},{key:'budget',label:'Budget remaining',num:true,value:a=>a.slo.error_budget_remaining_pct??Infinity,html:a=>`<span class="${a.slo.error_budget_remaining_pct<0?'danger':''}">${pct(a.slo.error_budget_remaining_pct,1)}</span>`},{key:'burn',label:'Active burn',num:true,value:a=>Number(burn(a)||0),html:a=>burn(a)?`${burn(a)}×`:'—'},{key:'latency',label:'Latency threshold',num:true,value:a=>a.slo.latency_threshold_ms,html:a=>`${n(a.slo.latency_threshold_ms)} ms`}],'budget')+
      `<p class="table-note">Negative remaining budget means the error budget is exhausted. Burn is shown only where an active SLO alert supplies it.</p>`;
  }
  function costs() {
    const apps=scopedApps().filter(a=>state.costTeam==='all'||a.team===state.costTeam);
    const rows=apps.filter(a=>`${a.name} ${a.team}`.toLowerCase().includes(state.costSearch.toLowerCase()));
    const total=key=>sum(apps,a=>a.cost[key]);
    const teams=[...new Set(scopedApps().map(a=>a.team))].sort();
    const teamRows=teams.map(team=>({name:team,apps:scopedApps().filter(a=>a.team===team)})).filter(t=>state.costTeam==='all'||t.name===state.costTeam).map(t=>({...t,actual:sum(t.apps,a=>a.cost.mtd_usd),budget:sum(t.apps,a=>a.cost.budget_usd_month),forecast:sum(t.apps,a=>a.cost.forecast_usd_month)}));
    const maxTeam=Math.max(...teamRows.map(t=>t.actual),1);
    return pageHead('Costs',`${month()} · USD · reported actuals, budgets and estimated forecasts.`)+
      `<div class="toolbar">${selectField('costTeam','Chargeback team',state.costTeam,[['all','All teams'],...teams.map(t=>[t,t])])}<span class="toolbar-end">${apps.length} apps in cost scope</span></div><div class="metrics">${metric('Actual spend · MTD',usd(total('mtd_usd'),2),'Sum of app cost records')}${metric('Monthly budget',usd(total('budget_usd_month')),'Allocated app budgets')}${metric('Forecast · estimate',usd(total('forecast_usd_month'),2),`${apps.filter(a=>overBudget(a)).length} apps forecast over budget`)}${metric('Idle compute · MTD',usd(total('idle_usd'),2),'Included in app costs','warning')}</div>`+
      (apps.some(a=>a.health==='idle')?notice('Review idle capacity',apps.filter(a=>a.health==='idle').map(a=>`${link(`#/app/${encodeURIComponent(a.id)}/cost`,a.name)}: ${usd(a.cost.idle_usd,2)} idle compute; auto-stop is ${esc(a.governance.auto_stop)}.`).join(' ')):'')+
      sectionHead('Spend by team','Actuals share a common scale; budget and forecast are shown in dollars.')+
      dataTable('Team costs',teamRows,[{key:'name',label:'Team',html:t=>esc(t.name)},{key:'actual',label:'Actual · MTD',num:true,html:t=>`<span class="cost-comparison">${usd(t.actual,2)}<svg class="bar-compare" viewBox="0 0 100 14" preserveAspectRatio="none" aria-hidden="true"><rect y="3" width="${finite(t.actual)?t.actual/maxTeam*100:0}" height="8"/></svg></span>`},{key:'budget',label:'Budget',num:true,html:t=>usd(t.budget)},{key:'forecast',label:'Forecast · est.',num:true,html:t=>usd(t.forecast,2)}],'actual',-1)+
      `<section style="margin-top:var(--space-xl)">${sectionHead('App costs & unit economics')}<div class="toolbar">${searchField('costSearch','Find an app',state.costSearch,'App or team')}</div>${rows.length?dataTable('Application costs',rows,[{key:'name',label:'Application',html:a=>`${appLink(a,'cost')}<small>${esc(a.team)} · ${esc(a.cost_center)}</small>`},{key:'actual',label:'Actual · MTD',num:true,value:a=>a.cost.mtd_usd,html:a=>usd(a.cost.mtd_usd,2)},{key:'budget',label:'Budget',num:true,value:a=>a.cost.budget_usd_month,html:a=>usd(a.cost.budget_usd_month)},{key:'forecast',label:'Forecast · est.',num:true,value:a=>a.cost.forecast_usd_month,html:a=>`<span class="${overBudget(a)?'danger':''}">${usd(a.cost.forecast_usd_month,2)}</span><small>${a.cost.forecast_usd_month==null||a.cost.budget_usd_month==null?'Not collected yet':overBudget(a)?'↑ Over budget':'Within budget'}</small>`},{key:'idle',label:'Idle compute',num:true,value:a=>a.cost.idle_usd,html:a=>usd(a.cost.idle_usd,2)},{key:'unit',label:'$/1k requests',num:true,value:a=>a.cost.usd_per_1k_requests??-1,html:a=>usd(a.cost.usd_per_1k_requests,3)}],'actual',-1):empty('No matching app costs','Clear the search to show all apps in this cost scope.')}</section>`+
      `<details><summary>Cost definitions & reconciliation</summary><p>Compute uses billing usage at list prices. AI uses exact tokens × list prices and is an estimate. Actual totals above sum app MTD records; daily series and component values are independent source records and may not reconcile.</p><p class="table-note">Monitoring service cost: ${usd(M.cost.monitor_self_cost_mtd_usd,2)} MTD, separate from the app total. Model-price source: ${M.cost.model_prices.map(m=>`${esc(m.model)} (${esc(m.source)}): ${usd(m.input_usd_per_mtok,2)} input / ${usd(m.output_usd_per_mtok,2)} output per million tokens`).join('; ')}.</p><p>${esc(M.notes.costs || '')}</p></details>`;
  }
  function audit(events) {
    const rows=events.filter(e=>inRange(e.ts));
    return rows.length?dataTable('Audit events',rows,[{key:'ts',label:'When · UTC',html:e=>stamp(e.ts)},{key:'app',label:'Application',html:e=>appLink(app(e.app),'security')},{key:'action',label:'Action',html:e=>`${esc(e.action)}<small>${esc(e.detail)}</small>`},{key:'user',label:'Actor',html:e=>`<span style="overflow-wrap:anywhere">${esc(e.user)}</span>`}],'ts',-1):empty('No audit events in this window','Use a wider global time range to see earlier changes.');
  }
  function governance() {
    const apps=scopedApps();
    const filter=a=>state.governanceFilter==='all'||(state.governanceFilter==='risk'&&(a.security.cve.critical||a.security.cve.high||a.security.secrets||a.security.review_verdict==='reject'))||(state.governanceFilter==='tags'&&!a.governance.tags_complete)||(state.governanceFilter==='drift'&&a.governance.permission_drift);
    const rows=apps.filter(filter);
    return pageHead('Governance & security','Runtime health and production readiness are separate decisions.')+
      `<div class="metrics">${metric('Critical CVEs',n(sum(apps,a=>a.security.cve.critical)),'Latest scans','danger')}${metric('Rejected reviews',n(apps.some(a=>a.security.review_verdict!=='—')?apps.filter(a=>a.security.review_verdict==='reject').length:null),'Supplied verdicts','warning')}${metric('Permission drift',n(apps.some(a=>a.governance.permission_drift!=null)?apps.filter(a=>a.governance.permission_drift).length:null),'Apps with changed access','warning')}${metric('Complete tag coverage',apps.some(a=>a.governance.tags_complete!=null)?`${apps.filter(a=>a.governance.tags_complete).length} / ${apps.length}`:'—','Apps with all required tags')}</div>`+
      `<div class="toolbar">${selectField('governanceFilter','Show',state.governanceFilter,[['all','All applications'],['risk','Code risk'],['tags','Incomplete tags'],['drift','Permission drift']])}</div>`+
      (rows.length?dataTable('Governance inventory',rows,[{key:'name',label:'Application',html:a=>`${appLink(a,'security')}<small>${esc(a.team)}</small>`},{key:'risk',label:'CVEs · critical / high',num:true,value:a=>a.security.cve.critical*100+a.security.cve.high,html:a=>`${n(a.security.cve.critical)} / ${n(a.security.cve.high)}`},{key:'secrets',label:'Secrets',num:true,value:a=>a.security.secrets,html:a=>n(a.security.secrets)},{key:'review',label:'Code review',value:a=>a.security.review_verdict,html:a=>badge(a.security.review_verdict.replaceAll('_',' '),a.security.review_verdict==='reject'?'critical':'')},{key:'tags',label:'Tags',value:a=>a.governance.tags_complete,html:a=>a.governance.tags_complete==null?'Not collected yet':tag(a.governance.tags_complete?'healthy':'warning',a.governance.tags_complete?'Complete':'Incomplete')},{key:'permissions',label:'Permissions',value:a=>a.governance.permission_drift,html:a=>a.governance.permission_drift==null?'Not collected yet':a.governance.permission_drift?tag('warning','Drift detected'):'No drift'}],'risk',-1):empty('No policy findings match','There are no matching findings in this workspace scope.'))+
      `<p class="table-note">Required tags: ${M.governance.required_tags.map(esc).join(', ')}. Incomplete records do not identify which keys are missing.</p><section style="margin-top:var(--space-xl)">${sectionHead('Audit trail',`Events in the global ${state.range}h window.`)}${audit(M.governance.audit_events.filter(e=>apps.some(a=>a.name===e.app)))}</section>`;
  }
  function workspaces() {
    const rows=M.workspaces.filter(w=>state.workspace==='all'||w.name===state.workspace);
    return pageHead('Workspace collection','A running app and a working monitoring feed are different signals.')+
      rows.map(w=>`<section class="issue-block"><div class="section-head"><div><h2>${esc(w.name)}</h2><p>${esc(w.region)} · ${esc(w.role)} · workspace ${esc(w.id)}</p></div>${tag(w.status!=='OK'?'stale':'healthy',w.status!=='OK'?'Feed stale':'Feed current')}</div>${facts([['Last successful collection',stamp(w.last_run)],['Collection age',age(validDate(w.last_run)?(now-new Date(w.last_run))/1000:null)],['Applications',M.apps.filter(a=>a.workspace===w.name).map(a=>appLink(a)).join(' · ')]])}${w.status!=='OK'?notice('App health cannot be verified','Inspect the workspace worker and restore collection. Last reported app values remain visible, with freshness labels.'):''}</section>`).join('')+
      `<p class="table-note">Feed status is supplied by the snapshot. Ages are calculated relative to ${stamp(M.generated_at)}.</p>`;
  }
  function usage() {
    const f=M.funnel_example, versions=Object.keys(f.by_version), steps=f.by_version[state.funnelVersion] || f.by_version[versions[0]] || [];
    const completion=fraction(steps.at(-1)?.sessions,steps[0]?.sessions);
    const c=M.cohorts_example;
    const visible=name=>name && (state.workspace==='all'||app(name)?.workspace===state.workspace);
    return pageHead('Usage & adoption','Compare answer completion and returning users without mixing their measurement periods.')+
      (visible(f.app)&&steps.length?`<section>${sectionHead('Configured funnel',`${esc(f.app)} · ${esc(f.funnel)} · measurement dates not supplied`,link(`#/app/${f.app}/agents`,'Review agent behavior →'))}<div class="toolbar">${selectField('funnelVersion','Deployment version',state.funnelVersion,versions.map(v=>[v,v]))}</div><div class="metrics">${metric('Reached final step',pct(completion,1),`Share of ${esc(steps[0]?.step)} sessions`)}${metric(esc(steps[0]?.step),n(steps[0].sessions),'Sessions in the selected version')}</div><div class="detail-grid"><div>${steps.map(s=>`<div class="funnel-row"><span class="small">${esc(String(s.step || '—').replaceAll('_',' '))}</span><div><svg class="funnel-bar" viewBox="0 0 100 22" preserveAspectRatio="none" aria-hidden="true"><rect width="${fraction(s.sessions,steps[0].sessions) || 0}" height="22"/></svg></div><small>${n(s.sessions)}</small></div>`).join('')}</div><div>${facts(versions.map(v=>[esc(v),`${pct(fraction(f.by_version[v].at(-1)?.sessions,f.by_version[v][0]?.sessions),1)} reached final step`]))}<p class="table-note">Each version has a different cohort size. Completion is the final step ÷ first step, not a matched experiment.</p></div></div></section>`:empty('Funnel not collected yet','Not collected yet. Configure a funnel in the app’s Product & guardrails section and collect business events with the gold job.'))+
      (visible(c.app)&&c.weeks.length?`<section style="margin-top:var(--space-2xl)">${sectionHead('Weekly retention',`${esc(c.app)} · returning users by cohort week`,link(`#/app/${c.app}/overview`,'View application →'))}<div class="table-wrap"><table class="heat-table ${Math.max(0,...c.retention_pct.map(r=>r.length))>6?'is-wide':''}" aria-label="Weekly cohort retention"><thead><tr><th scope="col">Cohort</th><th scope="col">Users</th>${Array.from({length:Math.max(0,...c.retention_pct.map(r=>r.length))},(_,i)=>`<th scope="col">W${i}</th>`).join('')}</tr></thead><tbody>${c.retention_pct.map((row,i)=>`<tr><th scope="row">${date(c.weeks[i])}</th><td>${n(c.sizes[i])}</td>${Array.from({length:Math.max(0,...c.retention_pct.map(r=>r.length))},(_,j)=>row[j]==null?'<td class="muted" aria-label="Not yet observed">—</td>':`<td class="heat ${row[j]>85?'dark':''}" style="--heat:${row[j]}%">${row[j]}%</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="table-note">W0 is the cohort’s first week. Blank cells have not yet been observed. These cohorts are fixed to their supplied dates. The current week is partial.</p></section>`:empty('Retention not collected yet','The gold job needs real requests with user identifiers before cohort retention is available.'));
  }
  function missing(title) { return pageHead(title)+empty('This view is unavailable','No matching data was found for this route.',link('#/fleet','Return to fleet','button')); }
  function render(focus=false) {
    P.capture(); P.begin();
    const active=document.activeElement?.id, selection=document.activeElement?.selectionStart;
    const [path,query='']=(location.hash.slice(1)||'/fleet').split('?');
    const parts=path.split('/').filter(Boolean).map(p=>{try{return decodeURIComponent(p);}catch{return p;}}), route=parts[0]||'fleet';
    const params=new URLSearchParams(query);
    if(route==='fleet'&&params.has('health') && Object.hasOwn(healthRanks,params.get('health')))state.health=params.get('health');
    chrome(route);
    const views={fleet:()=>fleet()+P.fleetMeasures(),topology:T.view,catalog:P.catalog,ask:P.ask,alerts:()=>alerts()+P.alertExtras(),investigations,reliability,costs,governance:P.governance,usage,workspaces:()=>workspaces()+P.federation(),federation:()=>workspaces()+P.federation()};
    let html;
    try { html=route==='app'?appPage(parts[1],parts[2],parts[3]):route==='trace'?tracePage(parts[1],params.get('app')):views[route]?views[route]():missing('View not found'); }
    catch(error) { console.error(error);html=notice('This view could not render','Return to the fleet or retry the snapshot.','error')+link('#/fleet','Return to fleet','button'); }
    $('#main').innerHTML=provenance()+P.feedback()+html;
    $('#main').dataset.route=location.hash; P.restore(); T.highlight(state.resource);
    $('#main').setAttribute('aria-busy','false');
    document.title=($('#main h1')?.textContent||'Fleet')+' · Apps Monitor';
    if(focus) { $('#main').focus({preventScroll:true});window.scrollTo({top:0}); }
    else if(active) { const el=document.getElementById(active);if(el){el.focus({preventScroll:true});if(el.type==='search'&&selection!=null)el.setSelectionRange(selection,selection);} }
  }
  let commandIndex=0, commandMatches=[], commandOpener;
  const commands=()=>[...destinations.map(([id,label])=>({label,detail:'View',href:'#/'+id})),...M.apps.map(a=>({label:a.name,detail:a.team+' · '+statusNames[status(a)],href:`#/app/${encodeURIComponent(a.id)}/overview`}))];
  function paletteResults() {
    const q=$('#command-input').value.toLowerCase().trim();
    commandMatches=commands().filter(x=>`${x.label} ${x.detail}`.toLowerCase().includes(q));
    commandIndex=Math.min(Math.max(0,commandIndex),Math.max(0,commandMatches.length-1));
    $('#command-results').innerHTML=commandMatches.length?commandMatches.map((x,i)=>`<button class="command-result" id="command-${i}" role="option" tabindex="-1" aria-selected="${i===commandIndex}" data-command="${i}"><span>${esc(x.label)}</span><small>${esc(x.detail)}</small></button>`).join(''):'<div class="empty"><h3>No matches</h3><p>Try an app name, team, or view such as Costs.</p></div>';
    if(commandMatches.length)$('#command-input').setAttribute('aria-activedescendant','command-'+commandIndex);else $('#command-input').removeAttribute('aria-activedescendant');
    $('#announcement').textContent=`${commandMatches.length} quick search results`;
  }
  function openPalette() { commandOpener=document.activeElement;commandIndex=0;$('#command-input').value='';paletteResults();$('#palette').showModal();$('#command-input').focus(); }
  function closePalette() { $('#palette').close();commandOpener?.focus({preventScroll:true}); }
  function runCommand(index) { const item=commandMatches[index];if(item){closePalette();location.hash=item.href;} }
  document.addEventListener('click',async event=>{
    const t=event.target.closest('button, a');if(!t)return;
    if(t.dataset.action==='retry-snapshot')window.ConsoleData.retry();
    if(t.dataset.action==='retry-detail'){detailState.delete(t.dataset.detail);render();}
    if(t.dataset.action==='search')openPalette();
    if(t.dataset.action==='menu'){const open=$('#sidebar').classList.toggle('open');t.setAttribute('aria-expanded',String(open));}
    if(t.matches('.nav-link'))$('#sidebar').classList.remove('open');
    if(t.dataset.action==='clear-fleet'){state.search='';state.health='all';state.team='all';if(location.hash.includes('?'))location.hash='#/fleet';else render();}
    if(t.dataset.sort){const id=t.dataset.sort, prev=state.sorts[id];state.sorts[id]={key:t.dataset.key,dir:prev?.key===t.dataset.key?-prev.dir:1};render();[...document.querySelectorAll(`[data-sort="${id}"][data-key="${t.dataset.key}"]`)].find(el=>el.offsetParent!==null)?.focus({preventScroll:true});$('#announcement').textContent=`Sorted by ${t.textContent.trim()}`;}
    if(t.dataset.alertTab){state.alertTab=t.dataset.alertTab;render();$(`[data-alert-tab="${state.alertTab}"]`)?.focus({preventScroll:true});}
    if(t.dataset.span){state.selectedSpan=t.dataset.span;render();$(`[data-span="${state.selectedSpan}"]`)?.focus({preventScroll:true});}
    if(t.dataset.command!=null)runCommand(Number(t.dataset.command));
    if(t.dataset.copy){try{await navigator.clipboard.writeText(t.dataset.copy);t.textContent='✓ Copied';t.dataset.state='success';setTimeout(()=>{if(t.isConnected){t.innerHTML=icon('copy')+' Copy trace ID';delete t.dataset.state;}},2500);}catch{t.textContent='Copy unavailable';$('#announcement').textContent='Clipboard is unavailable. Select the trace ID above and copy it manually.';}}
  });
  document.addEventListener('input',event=>{const key=event.target.dataset.filter;if(key&&event.target.type==='search'){state[key]=event.target.value;render();}});
  document.addEventListener('change',event=>{
    const key=event.target.dataset.filter;
    if(event.target.dataset.tableSort){state.sorts[event.target.dataset.tableSort]={key:event.target.value,dir:1};render();}
    if(key){state[key]=event.target.value;if(key==='health'&&location.hash.includes('?'))history.replaceState(null,'','#/fleet');render();}
    if(event.target.id==='workspace-select'){state.workspace=event.target.value;state.team='all';state.costTeam='all';render();}
    if(event.target.id==='range-select'){state.range=Number(event.target.value);render();$('#announcement').textContent=`Charts and events now show the last ${state.range} hours. Fixed-period summaries retain their labelled windows.`;}
  });
  document.addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){event.preventDefault();$('#palette').open?closePalette():openPalette();}});
  $('#command-input').addEventListener('input',()=>{commandIndex=0;paletteResults();});
  $('#command-input').addEventListener('keydown',event=>{if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();commandIndex=(commandIndex+(event.key==='ArrowDown'?1:-1)+commandMatches.length)%Math.max(commandMatches.length,1);paletteResults();$('#command-'+commandIndex)?.scrollIntoView({block:'nearest'});}if(event.key==='Enter'){event.preventDefault();runCommand(commandIndex);}});
  $('#close-palette').addEventListener('click',closePalette);
  $('#palette').addEventListener('click',event=>{if(event.target===$('#palette')){const r=$('#palette').getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closePalette();}});
  $('#palette').addEventListener('cancel',event=>{event.preventDefault();closePalette();});
  function renderPreserving() {
    const x=window.scrollX,y=window.scrollY;
    const open=[...document.querySelectorAll('#main details')].map(d=>d.open);
    const positions=[...document.querySelectorAll('#main .table-wrap, #main .logs')].map(el=>[el.scrollLeft,el.scrollTop]);
    render();
    document.querySelectorAll('#main details').forEach((d,i)=>{d.open=!!open[i];});
    document.querySelectorAll('#main .table-wrap, #main .logs').forEach((el,i)=>{if(positions[i]){el.scrollLeft=positions[i][0];el.scrollTop=positions[i][1];}});
    window.scrollTo(x,y);
  }
  const context={esc,n,pct,usd,time,date,stamp,seriesChart,tag,appLink,link,empty,notice,metric,facts,sectionHead,pageHead,state,selectField,searchField,table:dataTable,model:()=>M,scopedApps,app,appAlerts,belongs,status,render:renderPreserving};
  const P=window.ConsoleSections(context), T=window.ConsoleTopology(context);
  window.ConsoleApp = {
    refresh(data) {
      const traces=M.traces;
      M=normalize(data);M.traces={...traces,...M.traces};window.MOCK=M;
      now=validDate(M.generated_at)?new Date(M.generated_at).getTime():Date.now();
      for(const [id,rows] of errorDetails){M.error_groups=M.error_groups.filter(e=>!belongs(e,{id,name:id})).concat(rows);detailState.delete('errors:'+id);}
      renderPreserving(); P.refresh();
    },
    connection(error) {if(connectionError!==error){connectionError=error;renderPreserving();}}
  };
  window.addEventListener('hashchange',()=>render(true));
  render();
})();
