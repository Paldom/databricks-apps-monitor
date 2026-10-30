/* Native workbench sections. Deep evidence is fetched only while its route is visible. */
window.ConsoleSections = C => {
  'use strict';
  const {esc,n,pct,usd,tag,appLink,link,empty,notice,metric,facts,sectionHead,pageHead,state,selectField,searchField,time,date,stamp} = C;
  const cache=new Map(), visible=new Set(), drafts=new Map(), forms=new Map(), outcomes=new Map();
  let currentApp=null, confirmation=null, message='', messageError=false, saving=false;
  const rows=v=>Array.isArray(v)?v:[];
  const parse=(v,fallback={})=>{try{return typeof v==='string'?JSON.parse(v):v||fallback;}catch{return fallback;}};
  const bool=v=>v===true||v==='true'||v===1;
  const traceLink=(id,href='#/trace/'+encodeURIComponent(id))=>`<a class="trace-id" href="${esc(href)}" title="${esc(id)}" aria-label="Open trace ${esc(id)}">${esc(String(id).length>20?String(id).slice(0,8)+'…'+String(id).slice(-4):id)}</a>`;
  const labels={threshold_ms:'Threshold (ms)',semconv_legacy_only:'Legacy HTTP attributes only',semconv_stable_only:'Stable HTTP attributes only',semconv_both:'Both HTTP attribute formats',gateway_vs_otel_tokens:'Gateway − OTel tokens',orphan_ratio_24h:'Suspected orphan spans · 24h',envelope_coverage:'Request envelope coverage',sampler_ratio:'Trace sampling rate',quality:'Signal quality',last_span_at:'Last span',last_log_at:'Last log',last_metric_at:'Last metric',last:'Latest probe',code:'HTTP status',ms:'Latency (ms)',ts:'Time · UTC',time:'Time · UTC',sli:'Indicator',slo:'Objective',target:'Target',p95_ms:'p95 (ms)',p50_ms:'p50 (ms)',avg_ms:'Average (ms)',avg_s:'Average (s)',qps:'Requests / second',max_healthy_qps:'Healthy requests / second',recommended_qps:'Recommended requests / second',at_concurrency:'Concurrent requests',py_loc:'Python lines',deps:'Packages',deps_pinned:'Pinned packages',has_tests:'Tests present',has_readme:'Readme present',checks_24h:'Checks · 24h',uptime_24h:'Reachability · 24h',ttfb_ms:'Time to first byte (ms)',window_days:'Window (days)',coverage_pct:'Evidence coverage',sql_warehouse:'SQL warehouse',serving_endpoint:'Serving endpoint',database:'Lakebase',postgres:'Lakebase Postgres',uc_securable:'Unity Catalog',secret:'Secret scope',genie_space:'Genie space',experiment:'MLflow experiment',app:'Application',external:'External host',env:'Environment',http:'HTTP status',http_status:'HTTP status',status_code:'HTTP status',level:'Permission',principal_type:'Principal type',within_budget:'Within budget',unpriced_days:'Unpriced days',review:'Review',scan:'Scan',url:'URL',error_pct:'Errors (%)',dropoff_pct:'Drop-off (%)',budget_remaining_pct:'Error budget remaining (%)',score:'Score / 100',avg_rating:'Average rating / 5',rating:'Rating / 5',relevance:'Relevance / 10',faithfulness:'Faithfulness / 10',toxicity:'Toxicity / 10',p75_cls:'Layout shift (score)',silhouette:'Cluster separation (score)',partial_week:'Incomplete week'};
  const title=(key='')=>labels[key]||String(key).replace(/([a-z0-9])([A-Z])/g,'$1 $2').replace(/[_.]+/g,' ').replace(/\b(ms|http|sql|slo|sdk|ai|uc|id|mtd|rum|dbu|otel|ttfb|pii)\b/gi,v=>({ms:'ms',otel:'OTel',dbu:'DBU'}[v.toLowerCase()]||v.toUpperCase())).replace(/\b(p\d+)\b/gi,v=>v.toLowerCase()).replace(/^./,c=>c.toUpperCase());
  const numberUnits={ms:'ms',avg_s:'s',window_days:'days',idle_hours:'hours',active_days:'days',unpriced_days:'days',qps:'req/s',max_healthy_qps:'req/s',recommended_qps:'req/s',size_bytes:'bytes',dbus:'DBU',dbus_7d:'DBU',rows_24h:'records',avg_steps:'steps',max_steps:'steps',gateway_vs_otel_tokens:'tokens'};
  const ratios=new Set(['target','envelope_coverage','orphan_ratio_24h','sampler_ratio','semconv_legacy_only','semconv_stable_only','semconv_both','share','novel_share']);
  const enums=new Set(['type','kind','rule','action','action_name','signal','state','status','verdict','behind','quality','sli','compute_state','mode','app_state','principal_type','throttle','review','category','event_name','step_name']);
  const api=(a,path='')=>'api/apps/'+encodeURIComponent(a.name)+(path?'/'+path:'');
  const safeURL=v=>/^https?:\/\//.test(v||'')?v:null;
  const external=(url,label)=>safeURL(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:esc(label);
  const identity=()=>cache.get('api/console/identity')?.data;
  const allowed=a=>!!identity()?.admin&&!a?.remote;
  const readOnly=a=>a?.remote?'Remote actions run in the feeder monitor.':identity()?.reason||'Checking administrator access; controls are read-only until verified.';
  const disabled=a=>allowed(a)?'':`disabled title="${esc(readOnly(a))}"`;
  const permission=a=>allowed(a)?'<p class="table-note">Administrator controls. Changes are enforced by the existing service APIs.</p>':notice('Read-only',esc(readOnly(a)),'');
  function request(path,force=false) {
    visible.add(path);
    let item=cache.get(path);
    if(!item||force&&!item.loading){
      item={...item,loading:true,error:null};cache.set(path,item);
      window.ConsoleData.get(path).then(data=>{item.data=data;item.error=null;}).catch(error=>{item.error=error.message;}).finally(()=>{
        item.loading=false;
        if(visible.has(path))C.render();
      });
    }
    return item;
  }
  function source(path,render) {
    const item=request(path);
    const failure=item.error?notice('Source unavailable',`${cell(item.error)} <button class="button" data-reload="${esc(path)}">Retry</button>${item.data?' Showing the last successful result.':''}`,'error'):'';
    const partial=rows(item.data?._source_errors);
    return failure+(partial.length?notice('Some evidence is unavailable',esc(partial.join(', '))+` <button class="button" data-reload="${esc(path)}">Retry</button>`,'error'):'')+(item.data!==undefined?render(item.data):item.loading?'<div class="loading" role="status"><p>Loading evidence…</p><div class="skeleton"></div></div>':'');
  }
  function begin() {visible.clear();forms.clear();currentApp=null;request('api/console/identity');}
  function refresh() {for(const path of [...visible])request(path,true);}
  function capture() {
    for(const f of document.querySelectorAll('[data-editor]'))drafts.set((document.getElementById('main').dataset.route||location.hash)+'|'+f.dataset.editor,Object.fromEntries([...f.elements].filter(el=>el.name).map(el=>[el.name,el.value])));
  }
  function restore() {
    for(const f of document.querySelectorAll('[data-editor]')){
      const draft=drafts.get(location.hash+'|'+f.dataset.editor);
      if(draft)for(const el of f.elements)if(el.name&&Object.hasOwn(draft,el.name))el.value=draft[el.name];
    }
  }
  function cell(value,key='') {
    if(value==null||value==='')return '<span class="muted">—</span>';
    if(typeof value==='string'&&/^[{[]/.test(value.trim())){
      try{return cell(JSON.parse(value),key);}catch{/* Text masks and log prefixes are not JSON. */}
      if(/^\[[A-Z_]+\]$/.test(value))return esc(title(value.slice(1,-1))+' redacted');
      return esc(value.replace(/^[{[]+|[}\]]+$/g,'').replace(/['"]([^'"]+)['"]\s*:/g,(_,k)=>title(k)+':'));
    }
    if(Array.isArray(value))return value.length?`<ul class="value-list">${value.map(v=>`<li>${cell(v,key)}</li>`).join('')}</ul>`:'<span class="muted">None reported</span>';
    if(typeof value==='object')return Object.keys(value).length?`<dl class="inline-facts">${Object.entries(value).map(([k,v])=>`<div><dt>${esc(title(k))}</dt><dd>${cell(v,k)}</dd></div>`).join('')}</dl>`:'<span class="muted">—</span>';
    if(key==='trace_id'||key==='sample_trace_id')return traceLink(value);
    if(['severity','severity_text'].includes(key))return tag(/error|critical|fatal|high/i.test(value)?'error':/warn|medium/i.test(value)?'warning':'info',title(value));
    if(key==='ok')return tag(bool(value)?'ok':'error');
    if(typeof value==='boolean')return tag('info',value?'Yes':'No');
    if(typeof value==='string'&&!Number.isFinite(Number(value))&&['state','status','verdict','behind','quality','review','app_state'].includes(key))return tag(/error|fail|reject|critical|down/i.test(value)?'error':/warn|stale|degrad|major|minor|patch|comments|firing/i.test(value)?'warning':/ok|pass|succeed|approve$|current|healthy|resolved/i.test(value)?'healthy':'info',title(value));
    if(typeof value==='string'&&/^\d{4}-\d\d-\d\d(?:T|$)/.test(value))return esc(value.length===10?date(value):stamp(value));
    if(typeof value==='number'||typeof value==='string'&&value.trim()!==''&&Number.isFinite(Number(value))){
      if(/^(time|ts|request_time|create_time|run_ts|event_time)$/.test(key)||/_(at|bucket)$/.test(key))return stamp(Number(value)*(Number(value)<1e11?1000:1));
      if(['id','job_id','experiment_id','workspace_id'].includes(key))return esc(value);
      if(['code','http','http_status','status_code'].includes(key))return `HTTP ${n(value)}`;
      if(ratios.has(key))return pct(value*100,1);
      if(/pct|uptime/.test(key))return pct(value,1);
      if(/usd|estimated_cost/.test(key))return usd(value,/per_/.test(key)?3:2);
      if(key.startsWith('score_'))return n(value,1)+' / 10';
      if(/quality_score|freshness_score/.test(key))return n(value)+' / 100';
      const unit=numberUnits[key]||(/_ms$/.test(key)?'ms':/tokens/.test(key)?'tokens':'');
      return n(value,Number.isInteger(Number(value))?0:2)+(unit?' '+unit:'');
    }
    if(enums.has(key))return esc(title(value));
    return esc(String(value).replace(/\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:\d\d)?/g,stamp));
  }
  function table(name,data,columns,overrides={},note='',heading=true) {
    const items=rows(data);
    const cols=columns.map(col=>{const [key,label]=col.split('|');return {key,label:label||title(key),num:items.some(r=>typeof r[key]==='number'),value:r=>r[key]!=null&&r[key]!==''&&Number.isFinite(Number(r[key]))?Number(r[key]):r[key],html:r=>overrides[key]?overrides[key](r):cell(r[key],key)};});
    return (heading?sectionHead(name):'')+(items.length?C.table(name,items,cols,name==='Leaderboard'?'score':cols[0].key,name==='Leaderboard'?-1:1):empty('No observations yet',note||'No records are available for this app and reporting window.'))+(note?`<p class="table-note">${esc(note)}</p>`:'');
  }
  const panel=(name,html,note='',id='')=>`<section class="deep-section" ${id?`id="${id}" tabindex="-1"`:''}>${sectionHead(name,note,id?`<a class="section-return" href="#${id.split('-')[0]}-index" data-local-anchor="${id.split('-')[0]}-index">Sections ↑</a>`:'')}${html}</section>`;
  const index=(name,items)=>`<nav class="section-index" id="${name.toLowerCase()}-index" tabindex="-1" aria-label="${esc(name)} sections">${items.map(([id,label])=>`<a href="#${id}" data-local-anchor="${id}">${esc(label)}</a>`).join('')}</nav>`;
  function series(name,data,key,unit='',labelKey='date') {
    const items=rows(data);
    return C.seriesChart(items.map((r,i)=>({ts:r[labelKey]??i,v:r[key]})),name,unit,{hourly:['time','ts'].includes(labelKey)});
  }
  function field(name,label,value='',type='text',extra='') {
    const id='edit-'+name;
    return `<label class="field" for="${id}">${esc(label)}<input id="${id}" name="${name}" type="${type}" value="${esc(value??'')}" ${extra}></label>`;
  }
  const choice=(name,label,value,options)=>`<label class="field">${esc(label)}<select name="${name}">${options.map(o=>`<option value="${esc(o)}" ${o===value?'selected':''}>${esc(o)}</option>`).join('')}</select></label>`;
  function form(id,content,label,submit,a=currentApp,blocked='') {
    forms.set(id,{submit,a,blocked});
    return `${permission(a)}${blocked?notice('Settings unavailable',esc(blocked),'error'):''}<form data-editor="${id}" class="editor" aria-label="${esc(label)}"><fieldset ${blocked?'disabled':disabled(a)}>${content}<button class="button primary" type="submit" ${saving?'disabled':''}>${esc(label)}</button></fieldset></form>`;
  }
  function action(label,path,options={}) {
    return `<button class="button" type="button" data-write="${esc(path)}" data-method="${options.method||'POST'}" ${options.confirm?`data-confirm="${esc(options.confirm)}"`:''} ${disabled(options.app||currentApp)} ${saving?'disabled':''}>${esc(label)}</button>`;
  }
  function feedback() {
    const output=message?notice(messageError?'Action failed':'Action result',cell(message),messageError?'error':''):'';
    return `<div id="action-status" role="status">${output}</div>`+(confirmation?`<section class="panel confirmation" role="alertdialog" aria-labelledby="confirm-title" tabindex="-1"><h2 id="confirm-title">${esc(confirmation.title)}</h2><p>Review this change before continuing.</p><div class="actions"><button class="button primary" data-confirm-choice="yes">Confirm</button><button class="button" data-confirm-choice="no">Cancel</button></div></section>`:'');
  }
  function confirmAction(title,run) {confirmation={title,run};C.render();document.querySelector('.confirmation')?.focus();}
  async function write(path,method='POST',body) {
    const result=await window.ConsoleData.write(path,method,body);
    const active=[...visible];cache.clear();
    for(const p of active)request(p);
    return result;
  }
  async function perform(fn) {
    if(saving)return;
    saving=true;message='Working…';messageError=false;C.render();
    try{const d=await fn();message=typeof d==='string'?d:window.ConsoleData.demo?'Demo action simulated; no workspace changes.':d?.run_id?`Job ${d.run_id} queued. Results appear after the job completes.`:'Saved. Collection or the next scheduled job will reflect the change.';}
    catch(error){message=error.message;messageError=true;}
    finally{saving=false;C.render();document.getElementById('action-status')?.scrollIntoView({block:'nearest'});}
  }
  document.addEventListener('submit',e=>{
    const f=e.target.closest('[data-editor]');if(!f)return;e.preventDefault();
    const entry=forms.get(f.dataset.editor);if(!entry||entry.blocked||!allowed(entry.a))return;
    const values=Object.fromEntries(new FormData(f));const key=location.hash+'|'+f.dataset.editor;
    perform(async()=>{const result=await entry.submit(values);drafts.delete(key);return result;});
  });
  document.addEventListener('click',e=>{
    const t=e.target.closest('button');if(!t)return;
    if(t.dataset.reload){cache.delete(t.dataset.reload);C.render();}
    if(t.dataset.write&&allowed(currentApp)){
      const run=()=>perform(async()=>{const result=await write(t.dataset.write,t.dataset.method);outcomes.set(t.dataset.write,result);return result;});
      if(t.dataset.confirm)confirmAction(t.dataset.confirm,run);else run();
    }
    if(t.dataset.confirmChoice){const c=confirmation;confirmation=null;C.render();if(t.dataset.confirmChoice==='yes')c?.run();}
    if(t.dataset.print!==undefined)window.print();
    if(t.dataset.export!==undefined)exportCompliance();
    if(t.dataset.previewPolicy!==undefined)previewPolicy();
    if(t.dataset.applyPolicy!==undefined)applyPolicy();
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&confirmation){confirmation=null;C.render();}});
  function head(a) {
    const probe=a.probe||{},u=a.usage_7d||{};
    return `<p>${esc(a.description||'')}${safeURL(a.url)?' · '+external(a.url,'Open app'):''}</p><div class="head-stats">${[
      ['Reachable · 24h',pct(probe.uptime_24h??a.last24h.uptime_pct),'operate','Ingress probe availability'],
      ['Real traffic p95 · 24h',n(a.last24h.p95_ms)+' ms','traffic','Server spans; probes excluded'],
      ['Probe RTT p95 · 24h',n(probe.p95_ms)+' ms','operate','Reachability only; not user latency'],
      ['Users · 7d',n(u.peak_dau),'usage','Peak daily users over seven days'],
      ['Probe errors · 1h',pct(probe.error_rate_1h),'errors','Failed ingress probes'],
      ['Alerts firing',n(C.appAlerts(a).length),'operate','Current unmuted alerts'],
    ].map(([label,value,tab,hint])=>`<a href="#/app/${encodeURIComponent(a.id)}/${tab}" title="${esc(hint)}"><small>${label}</small><strong>${value}</strong><span class="sr-only">${esc(hint)}</span></a>`).join('')}</div>`;
  }
  function resources(a,bindings=a.resources,heading=true) {
    const items=rows(bindings).map(r=>{
      const type=Object.keys(r).find(k=>k!=='name'&&r[k]&&typeof r[k]==='object'),spec=r[type]||{};
      const target=['securable_full_name','instance_name','database','scope','scope_name','name','id','job_id','experiment_id','url','host','branch'].find(k=>spec[k]!=null);
      return {binding:r.name,type,target:spec[target],permission:spec.permission,details:Object.fromEntries(Object.entries(spec).filter(([k])=>k!==target&&k!=='permission'))};
    });
    return table('Declared resources',items,['binding','target|Resource & permission','details|Binding details'],{
      target:r=>`<strong>${esc(title(r.type))} ${esc(r.target)}</strong>${r.permission?' · '+esc(r.permission):''}`,
      details:r=>cell(r.details),
    },'Bindings are declarations, not direct resource health checks.',heading);
  }

  function logs(data) {
    const items=rows(data).map(r=>({...r,severity:r.severity||r.severity_text||'INFO'}));
    const filtered=items.filter(r=>(!state.logsSeverity||state.logsSeverity==='all'||r.severity===state.logsSeverity)&&`${r.body} ${r.trace_id}`.toLowerCase().includes((state.logsSearch||'').toLowerCase()));
    return `<div class="toolbar">${selectField('logsSeverity','Severity',state.logsSeverity||'all',[['all','All severities'],...[...new Set(items.map(r=>r.severity))].sort().map(x=>[x,x])])}${searchField('logsSearch','Search message or trace',state.logsSearch||'','Message or trace ID')}</div>`+table('Log records',filtered,['time|Time · UTC','severity','body|Message','trace_id|Correlated trace'],{},'Latest 200 records. Search and severity filter apply to the loaded window; full messages are retained.');
  }
  function errors(d) {
    return panel('Error groups',table('Fingerprints',d.groups,['fingerprint','occurrences|Occurrences · retained history','first_seen','last_seen','sample']))+
      panel('Failed requests',table('Error spans',d.failed_requests,['time','name|Operation','duration_ms|Duration ms','http_status|HTTP','message','trace_id']))+
      panel('Error logs',table('Error log records',d.error_logs,['time','severity_text|Severity','body|Message','trace_id']));
  }
  function traces(a) {
    return panel('HTTP request traces',source(api(a,`traces?hours=${Math.min(state.range,48)}`),d=>table('Request traces',d.traces,['time','name|Operation','route','duration_ms|Duration ms','status','trace_id'],{},'Real requests; up to 50 recent traces.')))+
      panel('Agent runs · MLflow',source(api(a,'agent-traces'),d=>`<p>Experiment: ${esc(d.experiment||'No experiment bound')}</p>`+table('MLflow traces',d.traces,['request_time','trace_id','state','duration_ms','preview|Request preview','response_preview|Response preview','client_request_id','tags'],{trace_id:r=>link(`#/app/${encodeURIComponent(a.id)}/agent-trace/${encodeURIComponent(r.trace_id)}`,esc(r.trace_id),'trace-id')})));
  }
  function traffic(d) {
    return `<div class="chart-grid">${series('Requests',d.timeline,'requests','requests','ts')}${series('Latency · p50',d.timeline,'p50_ms','ms','ts')}${series('Latency · p95',d.timeline,'p95_ms','ms','ts')}${series('Errors',d.timeline,'errors','errors','ts')}</div>`+
      table('Route traffic',d.routes,['route','requests','errors','avg_ms|Average ms','p50_ms|p50 ms','p95_ms|p95 ms'])+table('Request timeline',d.timeline,['ts','requests','errors','p50_ms','p95_ms'],{},'Real server spans; probes and synthetic traffic excluded.');
  }
  function changes(d) {
    const releases=rows(d.releases).map((r,i,all)=>{
      const prev=all[i+1],valid=prev&&+prev.p95_ms>0&&r.p95_ms!=null;
      return {...r,comparison:!valid?'Unknown baseline':+r.p95_ms>1.3*prev.p95_ms||+r.error_pct>+prev.error_pct+2?'▲ Worse':+r.p95_ms<.77*prev.p95_ms?'▼ Better':'≈ Similar'};
    });
    return table('Regression by release',releases,['deployment_id','start_ts','end_ts','requests','p95_ms','error_pct','tokens','comparison'],{},'Worse: p95 >1.3× previous or error rate +2 points. Better: p95 <0.77×. Deployment timing does not prove causation.')+
      table('Incident and deployment timeline',d.events,['ts','type','state','rule','severity','muted','message'],{},'Alerts, deployments, anomalies and lifecycle events · 14 days.');
  }
  function security(a) {
    return `<div class="actions">${action('Request fresh review','api/actions/review/'+encodeURIComponent(a.name))}<button class="button" data-print>Print app review</button></div>`+permission(a)+
      panel('Source scan',source(api(a,'security'),d=>{
        const s=d.scan;
        return (s?`<div class="metrics">${metric('Quality score',n(s.quality_score)+'/100','Latest source scan')}${metric('Critical / high',`${n(s.findings_critical)} / ${n(s.findings_high)}`,'Findings, not only CVEs')}${metric('Medium / low',`${n(s.findings_medium)} / ${n(s.findings_low)}`,'Source findings')}${metric('Freshness',n(s.freshness_score)+'/100','Package versions')}</div>`+facts(['scanned_at','deployment_id','files','py_loc','deps','deps_pinned','has_tests','has_readme','policy_violations'].map(k=>[title(k),cell(s[k],k)]))+
          table('Packages · Python and npm',parse(s.deps_json,[]),['name|Package','eco|Ecosystem','version|Installed','latest','behind|Freshness','vulns|Known CVEs'],{},'Installed vs registry latest; known vulnerabilities from OSV. Unchecked packages remain unknown.'):
          empty('Not scanned yet','Refresh inventory to scan the current deployment.'))+
          table('Scan findings',d.findings,['severity','kind|Type','title|Finding','detail','file','line']);
      }))+
      panel('Automated review · advisory',source(api(a,'review'),d=>{
        const r=d.review,ov=d.overview;
        return (ov?facts([['Purpose',esc(ov.purpose)],['Technology',cell(ov.tech_stack)],['Endpoints',cell(ov.endpoints)] ]):empty('App overview pending','Purpose, technology and endpoint descriptions appear with the next review.'))+
          (r?`<div class="metrics">${metric('Overall',n(r.score_overall,1)+'/10','Advisory review')}${metric('Verdict',cell(r.verdict,'verdict'),'Automated, not human sign-off')}</div><p>${esc(r.summary)}</p>`+
            facts(['score_security','score_reliability','score_maintainability','score_cost','score_monitoring','model','reviewed_at','files_reviewed','input_tokens','output_tokens'].map(k=>[title(k),cell(r[k],k)]))+
            panel('Strengths',`<ul>${rows(parse(r.strengths_json,[])).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`)+
            table('Review findings',parse(r.findings_json,[]),['severity','area','title','recommendation']):empty('No review yet','Request a review of the current deployment.'));
      }));
  }
  function economics(d,heading=true) {
    return table('Unit economics',d.apps,['name|Application','dbu_usd|Compute $','ai_usd|AI $ estimate','total_usd|Total $ estimate','idle_usd|Idle $','usd_per_1k_requests|$/1k requests','usd_per_session|$/session','usd_per_user|$/user','usd_per_outcome|$/outcome','completions|Outcomes','unpriced_days'],{},`Last ${d.days||30} days. AI: list price, estimate. Unknown prices keep totals unknown. Idle cost means no observed requests; sampling can overstate it.`,heading);
  }
  function cost(a) {
    return source(api(a,'cost'),d=>{
      const f=d.forecast||{},daily=rows(d.daily);
      const fraction=d.budget>0&&d.mtd_usd!=null?100*d.mtd_usd/d.budget:null;
      return `<div class="metrics">${metric('Compute MTD',usd(d.mtd_usd,2),'Billing × list prices')}${metric('Monthly budget',usd(d.budget),'Configured')}${metric('30-day forecast',usd(f.forecast_30d_usd,2),`${n(f.days_observed)} days observed · linear estimate`)}${metric('Budget used',pct(fraction),'Alerts at 70% and 100%')}</div>`+
        (fraction!=null?`<progress class="budget-progress" max="100" value="${Math.min(100,fraction)}" aria-label="Monthly budget spent ${pct(fraction)}"></progress>`:'')+
        appLink(a,'operate','Edit budget settings →')+
        `<div class="chart-grid">${series('Compute / day',daily,'dbu_usd','USD')}${series('Input tokens / day',daily,'ai_input_tokens','tokens')}${series('Output tokens / day',daily,'ai_output_tokens','tokens')}</div>`+
        table('Daily cost',daily,['date','dbus|DBUs','dbu_usd|Compute $','ai_usd|AI $ estimate','ai_calls|AI calls','ai_input_tokens|Input tokens','ai_output_tokens|Output tokens'],{},'30 days. Billing lags hours. Gateway tokens are a separate reconciliation signal.');
    })+panel('Cost per outcome',source(api(a,'unit-economics'),economics));
  }
  function ai(a) {
    return `<div class="metrics">${metric('Time to first token · p95',a.genai?.ttft_p95_ms==null?'—':n(a.genai.ttft_p95_ms)+' ms','Real model traffic · rolling 24h')}${metric('Rate-limit errors',n(a.genai?.error_classes_24h?.rate_limit),'Observed model spans · rolling 24h')}</div>`+source(api(a,'genai'),d=>{
      const byDate=new Map(),models=new Map();
      for(const r of rows(d.daily)){
        const day=byDate.get(r.date)||{date:r.date,tokens:0,calls:0};day.tokens=day.tokens==null||r.input_tokens==null||r.output_tokens==null?null:day.tokens+Number(r.input_tokens)+Number(r.output_tokens);day.calls=day.calls==null||r.calls==null?null:day.calls+Number(r.calls);byDate.set(r.date,day);
        const m=models.get(r.model)||{model:r.model,calls:0,input_tokens:0,output_tokens:0,errors:0,p95_ms:null};for(const k of ['calls','input_tokens','output_tokens','errors'])m[k]=m[k]==null||r[k]==null?null:m[k]+Number(r[k]);if(r.p95_ms!=null)m.p95_ms=Math.max(m.p95_ms??0,Number(r.p95_ms));models.set(r.model,m);
      }
      return `<div class="chart-grid">${series('AI tokens / day',[...byDate.values()],'tokens','tokens')}${series('Model calls / day',[...byDate.values()],'calls','calls')}${series('Agent steps / run',d.agent_steps,'avg_steps','spans')}</div>`+
        table('Models · 30 days',[...models.values()],['model','calls','input_tokens','output_tokens','p95_ms|Worst daily p95 ms','errors'])+
        table('Daily model usage',d.daily,['date','model','calls','input_tokens','output_tokens','avg_ms','p95_ms','errors'])+
        table('Top consumers',d.top,['session_id','user_hash','calls','tokens','last_call'])+
        table('LLM error taxonomy · 7 days',d.error_taxonomy,['category','errors','last_seen','sample'])+
        table('Agent complexity',d.agent_steps,['date','avg_steps','max_steps','agent_runs'])+
        table('Runtime quality evaluations',d.quality,['ts','relevance','faithfulness','toxicity','traces_sampled','comment'],{},'LLM judge over sampled traces; advisory scores on a 0–10 scale.')+
        table('User feedback · 30 days',d.feedback,['date','n|Ratings','avg_rating','negative|Ratings ≤2'])+
        table('Recent feedback',d.feedback_recent,['ts','rating','comment','trace_id']);
    })+panel('Prompt drift',source(api(a,'drift'),d=>table('Weekly prompt clusters',d.reports,['week','samples','k|Clusters','silhouette','novel_share'],{novel_share:r=>r.novel_share==null?'Baseline unavailable':pct(r.novel_share*100)},'Optional weekly embedding job. Short prompts can cluster noisily; fewer than 50 samples are weak evidence. Embeddings add cost.')));
  }
  function usage(a) {
    return source(api(a,'analytics'),d=>{
      const users=rows(d.users),total=users.reduce((s,r)=>s+(+r.requests||0),0);
      const daily=rows(d.daily);
      return `<div class="metrics">${metric('Requests · 30d',n(daily.length?daily.reduce((s,r)=>s+(+r.requests||0),0):null),'Real traffic')}${metric('Peak DAU · 30d',n(daily.length?Math.max(...daily.map(r=>+r.users||0)):null),'Daily distinct users')}${metric('Sessions · 30d',n(daily.length?daily.reduce((s,r)=>s+(+r.sessions||0),0):null),'Sum of daily sessions')}${metric('Known users',n(users.length),'Top 50 loaded users')}</div><div class="chart-grid">${series('Requests / day',daily,'requests','requests')}${series('DAU',daily,'users','users')}${series('Sessions / day',daily,'sessions','sessions')}</div>`+
        table('Daily adoption',daily,['date','requests','users','sessions','errors','avg_ms'])+
        table('User history',users.map(u=>({...u,estimated_cost:d.mtd_usd!=null&&total?+d.mtd_usd*u.requests/total:null})),['user_hash|Hashed user','first_seen','last_seen','requests','sessions','active_days','errors','tokens','estimated_cost|Estimated $ MTD'],{estimated_cost:r=>usd(r.estimated_cost,2)},'Pseudonymous IDs. Estimated share = MTD compute × share of requests among loaded users; not an invoice. Daily distinct users are not additive.');
    });
  }
  function productSettings(a,d) {
    return panel('Outcome and token budget',facts(['throttle','tokens_today','tokens_last_hour','policy_updated_at'].map(k=>[title(k),cell(d[k],k)]))+
      form('product-settings',field('outcome_event','Outcome event',d.outcome_event,'text','maxlength="64"')+field('token_budget_day','Daily token budget',d.token_budget_day||0,'number','min="0" step="1" required'),'Save product settings',v=>write(api(a,'product-config'),'PUT',{outcome_event:v.outcome_event.trim(),token_budget_day:Number(v.token_budget_day)}),a),
      'Zero disables the token budget. Hourly policy warns at 80% or projected exhaustion and blocks at 100%. Enforcement requires SDK v2.');
  }
  function product(a) {
    return panel('Business events',source(api(a,'events'),d=>table('Observed events · 7 days',d.events,['event_name','app_version','events','sessions','last_seen'])))+
      panel('Session funnels',source(api(a,'funnels'),d=>table('Ordered funnel steps',d.steps,['funnel','app_version','step_name','sessions','dropoff_pct'],{},'Ordered events within 30 minutes. Each session counts at its deepest step; raw retention bounds this view.')+
        `<details><summary>Configure a funnel</summary>${table('Funnel specifications',d.specs,['funnel','steps'])}${form('funnel',field('funnel','Funnel name','','text','required maxlength="100"')+field('steps','Steps, separated by commas','','text','required placeholder="upload,validate,submit"'),'Save funnel',v=>write(api(a,'funnels/'+encodeURIComponent(v.funnel.trim())),'PUT',{steps:v.steps.split(',').map(s=>s.trim())}),a)}</details>`))+
      panel('Weekly cohorts',source(api(a,'cohorts'),d=>table('Retention by first observed week',d.cohorts,['cohort_week','week_number','cohort_size','retained_users','retention_pct','partial_week'],{},'First observed within raw retention; current week is incomplete. Synthetic traffic excluded.')))+
      panel('Browser experience · 7 days',source(api(a,'rum'),d=>table('RUM routes',d.routes,['date','route','page_views','p75_lcp|p75 LCP ms','p75_cls|p75 CLS','p75_inp|p75 INP ms','js_errors','fingerprint','trace_id'])))+
      panel('Guardrail samples',source(api(a,'guardrails'),d=>table('Masked findings',d.findings,['ts','kind','severity','excerpt_masked','excerpt_hash','trace_id'],{trace_id:r=>r.trace_id?link(`#/app/${encodeURIComponent(a.id)}/agent-trace/${encodeURIComponent(r.trace_id)}`,esc(r.trace_id),'trace-id'):'—'},'Sampled detection, not a complete audit. Excerpts are fixed masks; hashes group findings.')+
        table('Normalized prompt shares',d.templates,['date','template_hash','samples','daily_samples','share'],{},'New template alerts require a prior baseline and at least five daily prompts.')))+
      source(api(a,'product-config'),d=>productSettings(a,d));
  }
  function telemetry(a) {
    return source(api(a,'telemetry-health'),d=>d.health?facts(Object.entries(d.health).map(([k,v])=>[title(k),cell(v,k)]))+`<p class="table-note">Sampling and late arrivals can resemble missing parents. Orphan alerts require >20% continuously for six hours. Span-based SLOs need sampler ratio 1. Gateway minus OTel tokens is reconciliation, not extra usage.</p>`:empty('Data quality unknown','No telemetry-health snapshot is available.'));
  }
  function slos(a) {
    return source(api(a,'slo'),d=>rows(d.specs).map(s=>panel(esc(title(s.slo)),facts(['sli','target','threshold_ms','window_days','route_filter','budget_remaining_pct','observed_since','last_bucket'].map(k=>[title(k),cell(s[k],k)]))+
      series('Error budget remaining',rows(d.series).filter(r=>r.slo===s.slo),'budget_remaining_pct','%')+
      action('Delete objective',api(a,'slo/'+encodeURIComponent(s.slo)),{method:'DELETE',confirm:`Delete ${s.slo} for ${a.name}?`,app:a}))).join('')+
      (!rows(d.specs).length?empty('No objectives configured','Create an availability or latency objective below.'):'')+
      `<details><summary>Add or update an objective</summary>${form('slo',field('slo','Name','','text','required maxlength="80"')+choice('sli','SLI','availability',['availability','latency'])+field('target','Target (fraction)',.995,'number','required min="0.000001" max="0.999999" step="any"')+field('threshold_ms','Latency threshold ms','','number','min="1"')+field('window_days','Window days',28,'number','required min="1" max="90"')+field('route_filter','Route LIKE','','text','maxlength="256" placeholder="/api/%"'),'Save objective',v=>write(api(a,'slo'),'POST',{...v,target:Number(v.target),threshold_ms:v.threshold_ms?Number(v.threshold_ms):null,window_days:Number(v.window_days),route_filter:v.route_filter||null}),a)}</details><p class="table-note">Sampled real server spans; no traffic is unknown. Reusing a name updates the objective. Changing measurement starts a new series.</p>`);
  }
  function mutes(a,heading=true) {
    return source('api/actions/mute',d=>table('Maintenance windows',d.mutes,['app','rule','starts_at','ends_at','reason','created_by','id|Action'],{id:r=>r.id?action('Unmute','api/actions/mute/'+encodeURIComponent(r.id),{method:'DELETE',app:a}):'—'},'',heading)+
      form('mute',field('app','App glob',a?.name||'*','text','required maxlength="128"')+field('rule','Rule glob','*','text','required maxlength="128"')+field('reason','Reason','','text','required maxlength="1000"')+field('starts_at','Starts at (local time)','','datetime-local')+field('ends_at','Until (local time; default one hour)','','datetime-local'),'Mute notifications',v=>write('api/actions/mute','POST',{app:v.app,rule:v.rule,reason:v.reason,...(v.starts_at?{starts_at:new Date(v.starts_at).toISOString()}:{}),ends_at:v.ends_at?new Date(v.ends_at).toISOString():new Date(Date.now()+3600000).toISOString()}),a)+
      '<p class="table-note">Alerts keep evaluating and remain in the timeline. Matching notifications are suppressed.</p>');
  }
  function probe(a) {
    return source(api(a),d=>{
      const history=rows(d.series).map(r=>({time:new Date(r[0]*1000).toISOString(),ok:!!r[1],http:r[2],latency_ms:r[3]}));
      return facts(['checks_24h','uptime_24h','p95_ms','ttfb_ms','compute_state','last'].map(k=>[title(k),cell(d[k],k)]))+
        series('Probe round-trip',history,'latency_ms','ms','time')+
        `<details><summary>Probe history · last 24 hours</summary>${table('Reachability checks',history,['time','ok','http','latency_ms'])}</details>`;
    });
  }
  function journeys(a) {
    return source(api(a,`synthetics?hours=${state.range}`),d=>{
      const live=d.live;
      return (live?facts([['Journey',esc(live.journey)],['Result',tag(live.ok?'ok':'error')],['Budget',`${n(live.budget_ms)} ms · ${live.within_budget?'Met':'Exceeded'}`],['Run time',stamp(live.ts*1000)]])+table('Journey steps',live.steps,['name','ok','code|HTTP','ms|Latency ms','detail']):empty('No live journey result','The in-app runner executes configured journeys periodically.'))+
        action('Run journeys now','api/actions/run-journeys',{app:a});
    });
  }
  function operate(a) {
    const capPath='api/actions/capacity/'+encodeURIComponent(a.name),ops=render=>source(api(a,'ops'),render);
    return index('Operate',[
      ['operate-lifecycle','Lifecycle'],['operate-config','Configuration'],['operate-capacity','Capacity'],['operate-slo','Objectives (SLO)'],['operate-maintenance','Maintenance'],['operate-reach','Reachability & journeys'],['operate-resources','Resources & permissions'],['operate-telemetry','Telemetry health'],
    ])+
      panel('Lifecycle',permission(a)+`<div class="actions">${action('Start app','api/actions/appctl/'+encodeURIComponent(a.name)+'/start',{app:a})}${action('Restart app','api/actions/appctl/'+encodeURIComponent(a.name)+'/restart',{confirm:`Restart ${a.name}? Requests will be interrupted during shutdown.`,app:a})}${action('Stop app','api/actions/appctl/'+encodeURIComponent(a.name)+'/stop',{confirm:`Stop ${a.name}? Requests will be interrupted.`,app:a})}${action('Request review','api/actions/review/'+encodeURIComponent(a.name),{app:a})}</div><p class="table-note">Restart waits for shutdown before starting the app. Lifecycle actions run through the protected job; changes may take several minutes.</p>`+
        ops(d=>`<div class="detail-grid"><section>${table('Deployment history',d.deployments,['create_time','deployment_id','state','mode'])}</section><section>${table('App audit · 7d',d.audit,['event_time','user','action_name','status_code'])}</section></div>`),'','operate-lifecycle')+
      panel('Configuration',ops(d=>{
        const cfg=d.config||{},tags=parse(cfg.tags_json);
        return form('config',['team','cost_center','env','tier'].map(k=>field(k,title(k),tags[k])).join('')+field('budget_usd_month','Budget USD / month',cfg.budget_usd_month||0,'number','min="0" step="any" required')+choice('auto_stop','Auto-stop',cfg.auto_stop||'none',['none','idle','night','budget'])+field('idle_hours','Idle hours',cfg.idle_hours||24,'number','min="1" required')+field('capacity_path','Capacity fallback path',cfg.capacity_path||'','text','placeholder="/monitor/capacity"'),'Save settings',v=>write(api(a,'config'),'POST',{tags:{...tags,...Object.fromEntries(['team','cost_center','env','tier'].map(k=>[k,v[k].trim()]))},budget_usd_month:Number(v.budget_usd_month),auto_stop:v.auto_stop,idle_hours:Number(v.idle_hours),capacity_path:v.capacity_path}),a,rows(d._source_errors).includes('App configuration')?'Retry the configuration source before editing existing settings.':'')+
          `<p class="table-note">Last saved: ${cfg.updated_at?stamp(cfg.updated_at):'Never'} · ${esc(cfg.updated_by||'')}. Tags drive chargeback. Budget mode stops the app when MTD cost reaches its budget.</p>`;
      }),'','operate-config')+
      panel('Capacity',ops(d=>{
        const capacity=outcomes.get(capPath)||d.capacity;
        return action('Run capacity · 1→8 concurrent',capPath,{app:a})+'<p>Four bounded levels, about 35 seconds. The ramp stops at saturation.</p>'+(capacity?facts(['path','max_healthy_qps','at_concurrency','recommended_qps'].map(k=>[title(k),cell(capacity[k],k)]))+table('Capacity results',capacity.levels,['concurrency','requests','errors','qps','p95_ms']):empty('No capacity result','Run a capacity check to see throughput and latency.'));
      }),'','operate-capacity')+
      panel('Objectives (SLO)',slos(a),'','operate-slo')+
      panel('Maintenance',mutes(a,false),'','operate-maintenance')+
      panel('Reachability & journeys',`<div class="detail-grid"><section>${sectionHead('Ingress probes')}${probe(a)}</section><section>${sectionHead('Synthetic journeys')}${journeys(a)}</section></div>`,'','operate-reach')+
      panel('Resources & permissions',ops(d=>resources(a,d.resources?.length?d.resources:a.resources)+
        `<div class="detail-grid"><section>${table('Bound job health · 7d',d.job_health,['job_id','runs_7d','succeeded','avg_s','last_run'])}</section><section>${table('Access permissions',d.permissions,['principal','principal_type','level'])}</section></div>`),'','operate-resources')+
      panel('Telemetry health',`<div class="detail-grid"><section>${telemetry(a)}</section><section>${ops(d=>table('Export volume · 24h',d.telemetry_volume,['signal','rows_24h']))}</section></div>`,'','operate-telemetry');
  }
  function browser(a) {
    return source(api(a,'synthetics?hours=168'),d=>table('Browser checks · 7 days',d.browser,['run_ts','journey','step_name','ok','status_code|HTTP','latency_ms','within_budget','vantage','failure_stage','detail','artifact'],{artifact:r=>{
      if(!r.artifact)return '—';
      return `${safeURL(r.artifact)?external(r.artifact,'Open artifacts'):`<code>${esc(r.artifact)}</code>`}<p class="table-note">Artifact folder in Catalog Explorer → Volumes. Result: result.json. Screenshot, when captured: screenshot.png (serverless) or screen.png (external runner).</p>${safeURL(r.screenshot_url)?external(r.screenshot_url,'View screenshot'):''}`;
    }},'Playwright and external-vantage runs. No result is not a pass. The old serverless browser job is paused where browser libraries are unavailable.'));
  }
  function agentTrace(a,id) {
    return source(api(a,'agent-traces/'+encodeURIComponent(id)),d=>{
      const spans=rows(d.otel_spans),info=d.mlflow?.info||{};
      const start=Math.min(...spans.map(s=>+s.start_time_unix_nano).filter(Number.isFinite));
      const end=Math.max(...spans.map(s=>+s.end_time_unix_nano).filter(Number.isFinite));
      const byID=new Map(spans.map(s=>[s.span_id,s]));
      const depth=s=>{const seen=new Set();let level=0;while(s?.parent_span_id&&byID.has(s.parent_span_id)&&!seen.has(s.parent_span_id)){seen.add(s.parent_span_id);s=byID.get(s.parent_span_id);level++;}return Math.min(level,8);};
      return `<div class="actions">${appLink(a,'traces','← Back to traces')}${external(d.mlflow_url,'Open in MLflow')}</div>`+
        facts([['MLflow trace',`<code class="trace-id">${esc(id)}</code>`],['State',cell(info.state,'state')],['Request ID',esc(d.client_request_id)],['Request preview',cell(info.preview)],['Response preview',cell(info.response_preview)]])+
        (spans.length?`<p>${spans.length} spans · ${n((end-start)/1e6,1)} ms · ${esc([...new Set(spans.map(s=>s.service_name))].join(' → '))}</p><div class="waterfall">${spans.map(s=>{
          const left=100*(+s.start_time_unix_nano-start)/(end-start||1),width=100*(+s.end_time_unix_nano-+s.start_time_unix_nano)/(end-start||1);
          return `<div class="agent-span"><p>${tag(s.status==='error'?'error':'ok')} ${esc(s.span_type||s.kind||'OTel')} · ${esc(s.name)} · ${n((s.end_time_unix_nano-s.start_time_unix_nano)/1e6,1)} ms</p><div class="span-row" style="--depth:${depth(s)}"><span class="span-name">${esc(s.service_name)} · ${n(s.in_tokens)} → ${n(s.out_tokens)} tokens</span><svg class="span-track" viewBox="0 0 100 28" preserveAspectRatio="none" aria-label="Span timing"><rect class="span-bar ${s.status==='error'?'error':''}" x="${Math.max(0,left)}" y="9" width="${Math.max(.1,width)}" height="10"/></svg></div><details><summary>Span attributes</summary>${facts(Object.entries(parse(s.attributes)).map(([k,v])=>[esc(title(k)),cell(v,k)]))}</details></div>`;
        }).join('')}</div>`:empty('No correlated OTel spans yet','MLflow metadata is available above. OTel delivery may lag behind MLflow.'))+
        panel('Correlated logs',logs(d.logs));
    });
  }
  function overview(a) {
    const s=a.scan||{},r=a.review||{};
    const alerts=C.appAlerts(a).slice().sort((x,y)=>({critical:0,high:1,warning:2,info:3}[x.severity]??4)-({critical:0,high:1,warning:2,info:3}[y.severity]??4));
    return panel('Recommended next actions',alerts.length?alerts.map(x=>`<p>${tag(x.severity)} ${esc(x.message)} · ${nextAction(x)}</p>`).join(''):`<p>No active unmuted alerts are supplied. Review each evidence source before treating this as a readiness verdict.</p>`)+
      panel('Evidence at a glance',`<div class="detail-grid"><section>${sectionHead('Code & review',`${n(s.files)} files · ${n(s.py_loc)} Python lines · ${n(s.deps)} packages (${n(s.deps_pinned)} pinned)`)}${facts([['Scan',`${n(s.quality_score??a.security.quality_score)}/100`],['Review',cell(r.verdict||a.security.review_verdict,'verdict')],['Summary',esc(r.summary||'Not collected yet')]])}${appLink(a,'security','Scan, packages & review →')}</section><section>${sectionHead('Cost & adoption')}${facts([['Compute · 7d',usd(a.cost_7d?.usd_7d,2)],['AI calls · 7d',n(a.cost_7d?.ai_calls_7d)],['AI tokens · 7d',n(a.cost_7d?.tokens_7d)],['Peak daily users · 7d',n(a.usage_7d?.peak_dau)],['Requests · 7d',n(a.usage_7d?.requests_7d)],['Sessions · 7d',n(a.usage_7d?.sessions_7d)]])}${appLink(a,'cost','Cost detail →')} · ${appLink(a,'usage','Adoption detail →')}</section></div>`)+
      panel('Technology and tags',facts([['Tags',Object.keys(a.tags||{}).length?cell(a.tags):'untagged'],['Resources',rows(a.resources).map(r=>Object.keys(r).filter(k=>k!=='name').map(title).join(', ')).join(' · ')||'No declared resources'],['Technology',s.has_npm?'Python + npm':s.py_loc>0?'Python':'Not identified'],['Complexity',s.py_loc!=null?(s.py_loc>3000||s.deps>40?'Complex':s.py_loc>700?'Moderate':'Simple'):'Not scanned']]))+
      panel('Probe history',probe(a))+panel('Telemetry health',telemetry(a))+panel('Service objectives',slos(a));
  }
  function appSection(a,tab,extra) {
    currentApp=a;
    if(a.remote)return notice('Open the feeder monitor',`This app's deep evidence and controls remain in its workspace. ${safeURL(a.monitor_url)?external(a.monitor_url,'Open feeder console'):esc('No feeder monitor URL is configured.')}`,'');
    const views={
      overview:()=>overview(a), errors:()=>source(api(a,`errors?hours=${state.range}`),errors),
      traces:()=>traces(a), logs:()=>source(api(a,`logs?hours=${Math.min(state.range,48)}`),d=>logs(d.logs)),
      traffic:()=>source(api(a,`requests?hours=${state.range}`),traffic),
      dependencies:()=>resources(a)+source(api(a,'deps'),d=>table('Outbound peers · 7 days',rows(d.deps).map(r=>({...r,error_pct:r.calls>0?100*r.errors/r.calls:null})),['dependency','calls','avg_ms','p95_ms|Worst daily p95 ms','errors','error_pct'],{},'Observed CLIENT spans. Daily p95 values cannot be combined into an exact seven-day percentile.')),
      changes:()=>source(api(a,'timeline'),changes),security:()=>security(a),cost:()=>cost(a),ai:()=>ai(a),usage:()=>usage(a),product:()=>product(a),operate:()=>operate(a),browser:()=>browser(a),telemetry:()=>telemetry(a),
      'agent-trace':()=>agentTrace(a,extra),
    };
    return views[tab]?`<div class="deep-content" data-section="${tab}"><p class="table-note">${['errors','traffic','logs','traces','operate'].includes(tab)?`Selected window: ${['logs','traces'].includes(tab)?Math.min(state.range,48):state.range} h. `:''}Each source reports its own period. Refreshes every 60 seconds while visible.</p>${views[tab]()}</div>`:empty('Section unavailable','Select a section above.');
  }
  function fleetMeasures() {
    const apps=C.scopedApps(),cost=apps.map(a=>a.cost_7d?.usd_7d),known=cost.length&&cost.every(x=>x!=null),p=C.model().fleet_measures||{};
    const probes=apps.map(a=>a.probe||{}),errorRates=probes.map(p=>p.error_rate_1h).filter(v=>v!=null),counts=probes.reduce((v,p)=>v+(+p.checks_24h||0),0);
    const availability=counts&&probes.every(p=>p.uptime_24h!=null)?probes.reduce((v,p)=>v+p.uptime_24h*p.checks_24h,0)/counts:null;
    return `<div class="metrics">${metric('Reachability · 24h',pct(availability),'Weighted by probe count')}${metric('Local real p95 · 24h',state.workspace==='all'?n(p.real_p95_ms)+' ms':'—','Real requests; never probe RTT')}${metric('Local probe RTT p95 · 24h',state.workspace==='all'?n(p.probe_p95_ms)+' ms':'—','Pooled successful ingress probes')}${metric('Probe errors · 1h',pct(errorRates.length?errorRates.reduce((s,v)=>s+Number(v),0)/errorRates.length:null),'Mean across apps with probe evidence')}${metric('Compute · 7d',usd(known?cost.reduce((s,v)=>s+Number(v),0):null),'Billing × list price; missing rows unknown')}${metric('Critical + high findings',n(apps.length&&apps.every(a=>a.scan?.findings_critical!=null)?apps.reduce((v,a)=>v+(+a.scan.findings_critical||0)+(+a.scan.findings_high||0),0):null),'All source scan findings')}</div>`;
  }
  function catalog() {
    const apps=C.scopedApps(),tags=a=>Object.entries(a.tags||{}).map(([k,v])=>`${title(k)}: ${v}`);
    const filtered=apps.filter(a=>(state.health==='all'||C.status(a)===state.health)&&(state.team==='all'||(a.tags?.team||'untagged')===state.team)&&(!state.catalogTag||state.catalogTag==='all'||(state.catalogTag==='untagged'?!tags(a).length:tags(a).includes(state.catalogTag)))&&`${a.name} ${a.description} ${tags(a).join(' ')}`.toLowerCase().includes(state.search.toLowerCase()));
    const counts=key=>[...new Set(apps.map(key))].sort().map(x=>[x,`${x} (${apps.filter(a=>key(a)===x).length})`]);
    return pageHead('App catalog','Find apps by health, team or declared tags. Every column sorts.')+
      `<div class="toolbar">${searchField('search','Search apps and tags',state.search,'Name, description or tag')}${selectField('health','Status',state.health,[['all','All states'],...counts(C.status)])}${selectField('team','Team',state.team,[['all','All teams'],...counts(a=>a.tags?.team||'untagged')])}${selectField('catalogTag','Tag',state.catalogTag||'all',[['all','All tags'],['untagged',`untagged (${apps.filter(a=>!tags(a).length).length})`],...[...new Set(apps.flatMap(tags))].sort().map(t=>[t,`${t} (${apps.filter(a=>tags(a).includes(t)).length})`])])}<span role="status">${filtered.length} / ${apps.length} apps</span></div>`+
      C.table('App catalog',filtered,[
        {key:'name',label:'Application',html:a=>appLink(a)},
        {key:'health',label:'Health',value:a=>C.status(a),html:a=>tag(C.status(a))},
        {key:'uptime',label:'Reachable 24h',value:a=>a.last24h.uptime_pct,html:a=>pct(a.last24h.uptime_pct)},
        {key:'p95',label:'Real p95 ms',value:a=>a.last24h.p95_ms,html:a=>n(a.last24h.p95_ms)},
        {key:'errors',label:'Probe errors 1h',value:a=>a.probe?.error_rate_1h,html:a=>pct(a.probe?.error_rate_1h)},
        {key:'cost',label:'MTD $',value:a=>a.cost.mtd_usd,html:a=>appLink(a,'cost',usd(a.cost.mtd_usd,2))},
        {key:'scan',label:'Scan',value:a=>a.security.quality_score,html:a=>appLink(a,'security',n(a.security.quality_score))},
        {key:'review',label:'Review',value:a=>a.security.review_verdict,html:a=>appLink(a,'security',title(a.security.review_verdict))},
        {key:'alerts',label:'Alerts',value:a=>C.appAlerts(a).length,html:a=>n(C.appAlerts(a).length)},
        {key:'team',label:'Team',value:a=>a.tags?.team||'untagged',html:a=>esc(a.tags?.team||'untagged')},
        {key:'tags',label:'Tags',value:a=>tags(a).join(' '),html:a=>tags(a).length?tags(a).map(t=>`<span class="badge">${esc(t)}</span>`).join(' '):'untagged'},
      ],'name');
  }
  function ask() {
    const url=C.model().genie_url;
    return pageHead('Ask Genie','Ask about fleet health, cost, risk and adoption over governed gold views.')+
      (safeURL(url)?`<p class="table-note">Genie uses your workspace session. Inspect its generated SQL and sources; verify AI-generated answers. If embedding is blocked by workspace policy, ${external(url,'open the Genie space')}.</p><iframe class="genie-frame" src="${esc(url)}" title="Genie fleet assistant" allow="clipboard-write"></iframe>`:empty('Genie space not configured','Set MONITOR_GENIE_SPACE_ID on the monitor app to embed its Genie space.'));
  }
  function nextAction(x) {
    const a=C.app(x.app);if(!a)return '';
    const paths={journey_failed:['Run journeys','api/actions/run-journeys'],critical_findings:['Re-scan fleet','api/actions/refresh-inventory'],policy_violation:['Re-scan fleet','api/actions/refresh-inventory'],review_reject:['Re-review app','api/actions/review/'+encodeURIComponent(a.name)],app_stopped:['Start app','api/actions/appctl/'+encodeURIComponent(a.name)+'/start'],down:['Restart app','api/actions/appctl/'+encodeURIComponent(a.name)+'/restart'],app_down:['Restart app','api/actions/appctl/'+encodeURIComponent(a.name)+'/restart']};
    if(paths[x.rule])return action(...paths[x.rule],{app:a,...(paths[x.rule][1].endsWith('/restart')?{confirm:`Restart ${a.name}? Requests will be interrupted during shutdown.`}:{})});
    const tab=/budget|permission/.test(x.rule)?'operate':/cost|idle/.test(x.rule)?'cost':/latency/.test(x.rule)?'traces':/traffic/.test(x.rule)?'traffic':/drift|quality|token/.test(x.rule)?'ai':'overview';
    return appLink(a,tab,'Review '+title(tab)+' →');
  }
  function alertExtras() {
    return panel('Alert actions',permission(null)+C.table('Next best actions',C.model().alerts.filter(x=>x.state==='firing'&&C.scopedApps().some(a=>C.belongs(x,a))),[
      {key:'app',label:'Application',html:x=>appLink(C.app(x.app))},{key:'rule',label:'Rule',html:x=>esc(title(x.rule))},{key:'action',label:'Next action',html:nextAction}
    ],'app'))+panel('Manage maintenance',mutes(null,false))+panel('Transition history · 3 days',source('api/alerts',d=>table('Alert transitions',d.recent,['ts','app','state','severity','rule','muted','message'],{},'',false)));
  }
  function compliance() {
    const g=cache.get('api/governance')?.data;
    return C.scopedApps().map(a=>{
      const cfg=rows(g?.configs).find(r=>r.name===a.name)||{},s=a.scan||{},r=a.review||{},tags=a.tags||{};
      const checks={'Telemetry':g&&!rows(g._source_errors).includes('Telemetry coverage')?rows(g.telemetry_active).includes(a.name):null,'Scan ≥60':s.quality_score==null?null:+s.quality_score>=60,'No crit/high':s.findings_critical==null||s.findings_high==null?null:+s.findings_critical+ +s.findings_high===0,'Review accepted':!r.verdict?null:r.verdict!=='reject','Tagged':a.governance.tags_complete==null?null:!!(tags.team&&tags.cost_center),'Budget set':rows(g?._source_errors).includes('App configuration')?null:Number(cfg.budget_usd_month??a.cost.budget_usd_month)>0};
      return {name:a.name,app:a,checks,passed:Object.values(checks).filter(x=>x===true).length};
    });
  }
  function exportCompliance() {
    const data=compliance(),headers=['App','Telemetry','Scan ≥60','No crit/high','Review accepted','Tagged','Budget set','Score'];
    const md=['# Fleet compliance report — '+C.model().generated_at,'','| '+headers.join(' | ')+' |','| '+headers.map(()=>'---').join(' | ')+' |',...data.map(r=>'| '+[r.name.replaceAll('|','\\|'),...Object.values(r.checks).map(x=>x==null?'Unknown':x?'Pass':'Fail'),`${r.passed}/6`].join(' | ')+' |')].join('\n');
    const url=URL.createObjectURL(new Blob([md],{type:'text/markdown'})),a=document.createElement('a');a.href=url;a.download='compliance-report.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  let policyPreview=null;
  const policyInput=()=>{const f=document.querySelector('[data-policy]');return f?{auto_stop:f.elements.auto_stop.value,idle_hours:Number(f.elements.idle_hours.value)}:null;};
  function previewPolicy() {
    if(!allowed(null))return;const body=policyInput();
    perform(async()=>{const d=await window.ConsoleData.write('api/actions/autostop-policy','POST',{...body,dry_run:true});policyPreview={body,targets:rows(d.targets)};return `Preview: ${policyPreview.targets.length} apps — ${policyPreview.targets.join(', ')||'none'}. Review the targets, then apply.`;});
  }
  function applyPolicy() {
    if(!allowed(null))return;const body=policyInput();
    if(!policyPreview||JSON.stringify(body)!==JSON.stringify(policyPreview.body)){message='Preview these exact policy settings before applying.';messageError=true;C.render();return;}
    confirmAction(`Apply ${body.auto_stop} to ${policyPreview.targets.length} previewed apps?`,()=>perform(async()=>{const d=await write('api/actions/autostop-policy','POST',{...body,dry_run:false,expected_targets:policyPreview.targets});policyPreview=null;return `Applied to ${rows(d.applied).join(', ')||'no apps'}. The hourly lifecycle job enforces this policy.`;}));
  }
  function governance() {
    const g=source('api/governance',d=>{
      const readiness=compliance();
      return panel('Cost allocation · MTD',table('Chargeback',d.chargeback,['team','cost_center','apps','mtd_usd|Compute $','mtd_tokens|AI tokens','ai_calls'],{},'Untagged apps need team and cost center values in Operate.',false),'','governance-allocation')+
        panel('Readiness checklist',`<button class="button" data-export>Export compliance .md</button>`+C.table('Readiness',readiness,[{key:'name',label:'Application',html:r=>appLink(r.app,'operate')},...['Telemetry','Scan ≥60','No crit/high','Review accepted','Tagged','Budget set'].map(k=>({key:k,label:k,value:r=>r.checks[k],html:r=>r.checks[k]==null?tag('info','Not collected yet'):tag(r.checks[k]?'healthy':'error',r.checks[k]?'Pass':'Fail')})),{key:'passed',label:'Score',html:r=>`${r.passed}/6`}],'passed'),'','governance-readiness')+
        panel('App usage and cost · 7d',table('Usage and cost',C.scopedApps().map(a=>({...rows(d.usage).find(x=>x.name===a.name),name:a.name,usd_7d:a.cost_7d?.usd_7d,ai_calls_7d:a.cost_7d?.ai_calls_7d,tokens_7d:a.cost_7d?.tokens_7d,mtd_usd:rows(d.mtd).find(x=>x.name===a.name)?.mtd_usd,scan:a.security.quality_score,review:a.security.review_verdict})),['name','requests_7d','peak_dau','sessions_7d','usd_7d|Compute $ 7d','ai_calls_7d','tokens_7d','mtd_usd|Compute $ MTD','scan','review'],{name:r=>appLink(C.app(r.name))},'',false),'','governance-usage')+
        panel('Fleet audit · 7d',table('Platform audit',d.audit,['event_time','user','action_name','app','status_code'],{},'system.access.audit; Apps service in this workspace, collected by inventory.',false),'','governance-audit');
    });
    return pageHead('Governance & security','Cost allocation, readiness and operational controls.')+index('Governance',[['governance-allocation','Cost allocation'],['governance-readiness','Readiness'],['governance-usage','Usage & cost'],['governance-audit','Audit'],['governance-economics','Unit economics'],['governance-leaderboard','Leaderboard'],['governance-prices','Model prices'],['governance-monitor','Monitor cost'],['governance-integrations','Integrations']])+
      panel('Fleet actions',permission(null)+`<div class="actions">${action('Refresh inventory','api/actions/refresh-inventory')}${action('Run journeys','api/actions/run-journeys')}</div>`)+
      `<details><summary>Create app from the monitored template</summary>${form('provision',field('app_name','App name','','text','required pattern="(?:[a-z0-9]|-){1,30}" maxlength="30"')+field('team','Team','','text','required')+field('cost_center','Cost center','','text','required')+choice('env','Environment','dev',['dev','staging','prod']),'Create app',v=>write('api/actions/provision','POST',v),null)}</details>`+
      `<details><summary>Fleet auto-stop policy</summary>${permission(null)}<form class="editor" data-policy data-editor="policy"><fieldset ${disabled(null)}>${choice('auto_stop','Mode','idle',['idle','night','none'])}${field('idle_hours','Idle hours',24,'number','min="1" required')}<button type="button" class="button" data-preview-policy>Preview</button><button type="button" class="button" data-apply-policy>Apply previewed rule</button></fieldset></form><p>Excludes the monitor and env=prod. Idle mode requires observed request evidence. Night means 00–06 in the lifecycle job’s configured timezone. Targets are calculated for this monitor’s local fleet.</p>${policyPreview?`<p>Previewed targets: ${policyPreview.targets.map(esc).join(', ')||'None'}</p>`:''}</details>`+
      g+panel('Unit economics',source('api/unit-economics',d=>economics(d,false)),'','governance-economics')+
      panel('Active app leaderboard',source('api/leaderboard',d=>`<p class="table-note">Scores out of 100 · stopped apps excluded · ${window.ConsoleData.demo?'deterministic demo scores':'available evidence only'}.</p><details><summary>How scores are calculated</summary><p>${esc(d.formula||'Formula unavailable')}</p></details>`+table('Leaderboard',rows(d.apps).map(r=>({...r,...r.components})).sort((a,b)=>(b.score??-1)-(a.score??-1)),['name|Application','score','coverage_pct','availability','errors','latency','scan','review','cost','adoption'],{name:r=>appLink(C.app(r.name)),score:r=>`<strong>${n(r.score,1)} / 100</strong>`},'',false)),'','governance-leaderboard')+
      panel('Model prices',source('api/model-prices',d=>table('Effective prices',d.prices,['model','effective_from','input_usd_per_mtok|$/M input','output_usd_per_mtok|$/M output','source'],{},'',false)+form('prices',field('model','Model','','text','required maxlength="200"')+field('effective_from','Effective date','','date','required')+field('input_usd_per_mtok','USD / million input tokens','','number','required min="0" step="any"')+field('output_usd_per_mtok','USD / million output tokens','','number','required min="0" step="any"')+choice('source','Source','list',['list','contract']),'Save model price',v=>write('api/model-prices','PUT',{...v,input_usd_per_mtok:Number(v.input_usd_per_mtok),output_usd_per_mtok:Number(v.output_usd_per_mtok)}),null)+'<p>Estimates are recomputed by the next cost rollup. Enter 0 explicitly for free tokens.</p>'),'','governance-prices')+
      panel('Monitor self-cost',source('api/monitor/cost',d=>{
        const latest=rows(d.daily).reduce((x,r)=>r.date>x?r.date:x,''),items=rows(d.daily).filter(r=>r.date===latest),known=items.reduce((s,r)=>s+(+r.usd||0),0);
        return `<p>${latest?`${usd(known,2)} ${items.some(r=>r.usd==null)?'known subtotal':'total'} · ${date(latest)}`:'No cost data yet'}</p>`+table('Monitoring components',d.daily,['date','component','usd','input_tokens','output_tokens','basis'],{},'Billing lags. Warehouse cost is a duration-share estimate. Unpriced tokens and unknown components are excluded from known subtotal.')+table('Observed Delta storage',d.storage,['table_name','size_bytes','measured_at|Measured at']);
      }),'','governance-monitor')+
      `<details><summary>App policy and SLO editors</summary><div class="policy-links">${C.scopedApps().map(a=>`<div><strong>${esc(a.name)}</strong>${appLink(a,'product','Outcome & tokens')}${appLink(a,'operate','SLO & maintenance')}${appLink(a,'telemetry','Telemetry health')}</div>`).join('')}</div></details>`+
      panel('Integrations',facts([['Status page',link(window.ConsoleData.url('status'),'Open status page')],['Read-only MCP endpoint',window.ConsoleData.demo?'<code>https://your-monitor.example/mcp</code><small>Demo placeholder · use your deployed monitor URL</small>':`<code>${esc(window.ConsoleData.url('mcp'))}</code>`]])+'<p>MCP exposes fleet, app, cost, alert, error, trace and SLO reads.</p>','','governance-integrations');
  }
  function federation() {
    return panel('Federated fleet',source('api/reach/fleet',d=>`<p>Deployment mode: ${esc(d.mode||'standalone')}. Hourly inventory and daily usage; open each feeder monitor for live probes and trace detail.</p>`+table('Remote applications',rows(d.apps).filter(a=>state.workspace==='all'||a.workspace_name===state.workspace),['workspace_name','workspace_id','name','app_state','requests_7d','errors_7d','dbus_7d','usd_7d','snapshot_ts'],{name:r=>{
      const a=C.model().apps.find(a=>a.name===r.name&&String(a.workspace_id)===String(r.workspace_id));return a?appLink(a):esc(r.name);
    }})));
  }
  return {cell,title,begin,capture,restore,refresh,feedback,head,appSection,catalog,ask,governance,alertExtras,federation,fleetMeasures,nextAction};
};
