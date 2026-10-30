/* One graph model drives the keyboard map, relationship table and blast radius. */
window.ConsoleTopology = C => {
  const {esc, tag, appLink, table, selectField, pageHead, empty, n, pct, state} = C;
  state.topologyTeam='all'; state.resourceType='all'; state.resource='';
  const labels={app:'Application',sql_warehouse:'SQL warehouse',serving_endpoint:'Model serving',job:'Job',experiment:'MLflow experiment',database:'Lakebase',postgres:'Lakebase Postgres',uc_securable:'UC securable',secret:'Secret scope',genie_space:'Genie space',external:'External host'};
  function view() {
    const M=C.model(), all=M.topology || {nodes:[],edges:[]};
    const apps=C.scopedApps().filter(a=>state.topologyTeam==='all'||a.team===state.topologyTeam);
    const sources=new Set(apps.map(a=>'app:'+a.id));
    const nodes=new Map(all.nodes.map(x=>[x.id,x]));
    const edges=all.edges.filter(e=>sources.has(e.source)&&(state.resourceType==='all'||nodes.get(e.target)?.type===state.resourceType));
    const targets=[...new Set(edges.map(e=>e.target))].map(id=>nodes.get(id)).filter(Boolean);
    const groups=[['sql_warehouse','SQL warehouses'],['serving_endpoint','Serving endpoints'],['database','Lakebase'],['job','Jobs'],['experiment','Experiments'],['uc_securable','Unity Catalog'],['secret','Secret scopes'],['genie_space','Genie spaces'],['app','Applications'],['external','External hosts']];
    const groupType=n=>n.type==='postgres'?'database':n.type;
    const order=n=>{const i=groups.findIndex(([key])=>key===groupType(n));return i<0?groups.length:i;};
    // Monitored dependency apps stay in the app column, with one identity and health.
    const appNodes=[...new Map([...apps.map(a=>nodes.get('app:'+a.id)),...targets.filter(a=>a.app)].filter(Boolean).map(a=>[a.id,a])).values()];
    const resources=targets.filter(a=>!a.app);
    const average=(values,fallback)=>values.length?values.reduce((a,b)=>a+b,0)/values.length:fallback;
    const stable=(a,b)=>(a.workspace||a.workspace_id).localeCompare(b.workspace||b.workspace_id)||a.label.localeCompare(b.label);
    appNodes.sort(stable); resources.sort((a,b)=>order(a)-order(b)||stable(a,b));
    // Alternating barycentres reduce crossings while preserving resource type groups.
    for(let pass=0;pass<4;pass++){
      const appOrder=new Map(appNodes.map((a,i)=>[a.id,i]));
      const resourceCentre=a=>average(edges.filter(e=>e.target===a.id).map(e=>appOrder.get(e.source)).filter(Number.isFinite),0);
      resources.sort((a,b)=>order(a)-order(b)||resourceCentre(a)-resourceCentre(b)||stable(a,b));
      const resourceOrder=new Map(resources.map((a,i)=>[a.id,i]));
      const appCentre=a=>average(edges.filter(e=>e.source===a.id).map(e=>resourceOrder.get(e.target)).filter(Number.isFinite),appOrder.get(a.id));
      appNodes.sort((a,b)=>appCentre(a)-appCentre(b)||stable(a,b));
    }
    let offset=32,previous=null;
    const headers=[],positions=new Map();
    resources.forEach(a=>{
      const kind=groupType(a);
      if(kind!==previous){headers.push({y:offset,label:groups.find(([k])=>k===kind)?.[1]||kind});offset+=28;previous=kind;}
      positions.set(a.id,offset+32);offset+=76;
    });
    const height=Math.max(offset,appNodes.length*76+32);
    appNodes.forEach((a,i)=>positions.set(a.id,64+i*76));
    const selected=nodes.get(state.resource), dependent=selected?apps.filter(a=>edges.some(e=>e.source==='app:'+a.id&&e.target===selected.id)):[];
    const workspace=a=>a.workspace||C.app(a.app)?.workspace||a.workspace_id||'Unknown workspace';
    const qualified=a=>`${workspace(a)} / ${a.label}`;
    const node=a=>{
      const dest=a.app?C.app(a.app):null, count=new Set(edges.filter(e=>e.target===a.id).map(e=>e.source)).size;
      const signal=dest?.health?tag(C.status(dest)):a.health?tag(a.health):tag('info','No health signal');
      const content=`<strong>${esc(dest?a.label:qualified(a))}</strong><span>${signal}${dest?' · '+esc(workspace(a)):''}</span>`;
      const attrs=`data-node="${esc(a.id)}" data-type="${esc(a.type)}" data-workspace="${esc(a.workspace_id)}" style="--node-y:${positions.get(a.id)-32}px"`;
      return `<div class="topo-node ${dest?'source':'target'}" ${attrs}>${dest?`<a href="#/app/${encodeURIComponent(a.app)}/overview">${content}</a>${count?`<button class="topo-impact" data-resource="${esc(a.id)}" aria-pressed="${state.resource===a.id}" aria-label="${esc(a.label)}: ${count} dependent applications">${count} apps depend</button>`:''}`:`<button class="topo-select" data-resource="${esc(a.id)}" aria-pressed="${state.resource===a.id}">${content}<small>${count} dependent ${count===1?'app':'apps'}</small></button>`}</div>`;
    };
    const map=`<div class="topology-map" aria-label="Dependency map" style="--graph-height:${height}px"><svg class="topology-edges" viewBox="0 0 1000 ${height}" preserveAspectRatio="none" aria-label="Declared and observed dependency edges" role="img">${edges.map(e=>{
      const y=positions.get(e.source),z=positions.get(e.target),appTarget=nodes.get(e.target)?.app;
      return `<path class="topo-edge ${e.observed?'observed':'declared'} ${e.declared&&e.observed?'both':''}" data-source="${esc(e.source)}" data-target="${esc(e.target)}" d="M 350 ${y} C ${appTarget?530:500} ${y},${appTarget?530:500} ${z},${appTarget?350:650} ${z}"><title>${esc(qualified(nodes.get(e.source)))} → ${esc(qualified(nodes.get(e.target)))}: ${e.declared?'Declared':''}${e.declared&&e.observed?' + ':''}${e.observed?`Observed · ${n(e.calls)} calls · worst daily p95 ${n(e.p95_ms)} ms · ${pct(e.error_pct)} errors`:''}</title></path>`;
    }).join('')}</svg><div class="topo-column"><h3 class="topo-heading">Applications · ${appNodes.length}</h3>${appNodes.map(node).join('')}</div><div class="topo-column"><h3 class="topo-heading">Resources · ${resources.length}</h3>${headers.map(h=>`<h4 class="topo-group" style="--node-y:${h.y}px">${esc(h.label)}</h4>`).join('')}${resources.map(node).join('')}</div></div>`;
    return pageHead('Topology','Declared resource bindings and observed CLIENT calls. Select a dependency to inspect its blast radius. Resource identities include their workspace.')+
      `<div class="toolbar">${selectField('topologyTeam','Team',state.topologyTeam,[['all','All teams'],...[...new Set(C.scopedApps().map(a=>a.team))].sort().map(x=>[x,x])])}${selectField('resourceType','Resource type',state.resourceType,[['all','All types'],...[...new Set(all.nodes.map(x=>x.type))].sort().map(x=>[x,labels[x]||x])])}<a href="#topology-list" class="button" data-local-anchor="topology-list">Jump to relationship table</a></div>`+
      `<div class="topo-legend"><span><i class="declared"></i>Dashed · declared binding</span><span><i class="observed"></i>Solid · observed call</span><span><i class="both"></i>Thick solid · declared + observed</span><span>${tag('info','No health signal')} means the resource is not directly probed</span></div>`+
      (selected?`<section class="panel blast-radius" aria-label="Blast radius"><h2>${esc(qualified(selected))} · ${dependent.length} apps in scope</h2><p>Direct dependents; this does not establish a resource outage.</p><div class="actions">${selected.app?appLink(C.app(selected.app),'overview','Open dependency app'):''}<button class="button" data-resource="">Clear selection</button></div>${table('Blast radius',dependent,[{key:'name',label:'Application',html:a=>appLink(a)},{key:'health',label:'Health',value:a=>C.status(a),html:a=>tag(C.status(a))},{key:'team',label:'Team',html:a=>esc(a.team)}],'name')}</section>`:'')+
      (appNodes.length?map:empty('No applications in scope','Change workspace or team filters.'))+
      `<section id="topology-list" tabindex="-1" class="deep-section"><h2>Dependency relationships</h2><p>${edges.length} relationships · ${esc(all.period||'7 days')} · ${esc(all.latency_basis||'Worst daily p95')}. Hover or focus any node to highlight its edges. Runtime observations are local; feeder inventories may omit bindings. A missing edge does not prove no dependency.</p>${edges.length?table('Dependency relationships',edges,[
        {key:'source',label:'Application',value:e=>nodes.get(e.source)?.label,html:e=>appLink(C.app(nodes.get(e.source)?.app))},
        {key:'target',label:'Dependency',value:e=>qualified(nodes.get(e.target)),html:e=>`<button class="button" data-resource="${esc(e.target)}">${esc(nodes.get(e.target)?.label)}</button><small>${esc(workspace(nodes.get(e.target)))}</small>`},
        {key:'type',label:'Type',value:e=>nodes.get(e.target)?.type,html:e=>esc(labels[nodes.get(e.target)?.type]||nodes.get(e.target)?.type)},
        {key:'workspace',label:'Workspace',value:e=>nodes.get(e.source)?.workspace_id,html:e=>esc(C.app(nodes.get(e.source)?.app)?.workspace||nodes.get(e.source)?.workspace_id)},
        {key:'evidence',label:'Evidence',value:e=>[e.declared?'Declared':'',e.observed?'Observed':''].join(' '),html:e=>esc([e.declared?'Declared':null,e.observed?'Observed':null].filter(Boolean).join(' + '))},
        {key:'calls',label:'Calls · 7d',num:true,html:e=>n(e.calls)},
        {key:'p95_ms',label:'Worst daily p95 ms',num:true,html:e=>n(e.p95_ms)},
        {key:'error_pct',label:'Errors %',num:true,html:e=>pct(e.error_pct)},
      ],'source'):empty('No dependencies in scope','No declared bindings or observed calls match these filters.')}</section>`;
  }
  function highlight(id) {
    document.querySelectorAll('.topo-edge').forEach(e=>{
      const match=e.dataset.source===id||e.dataset.target===id;
      e.classList.toggle('highlight',!!id&&match); e.classList.toggle('dim',!!id&&!match);
    });
  }
  for (const event of ['mouseover','focusin']) document.addEventListener(event,e=>{
    const node=e.target.closest('[data-node]'); if(node)highlight(node.dataset.node);
  });
  for (const event of ['mouseout','focusout']) document.addEventListener(event,e=>{
    if(e.target.closest('[data-node]')&&!e.relatedTarget?.closest?.('[data-node]'))highlight(state.resource);
  });
  document.addEventListener('click',e=>{
    const b=e.target.closest('[data-resource]');if(b){state.resource=b.dataset.resource;C.render();document.querySelector(`[data-resource="${CSS.escape(state.resource)}"]`)?.focus({preventScroll:true});document.querySelector('.blast-radius')?.scrollIntoView({block:'nearest'});highlight(state.resource);}
    const a=e.target.closest('[data-local-anchor]');if(a){e.preventDefault();const section=document.getElementById(a.dataset.localAnchor);section?.focus({preventScroll:true});section?.scrollIntoView({block:'start'});}
  });
  return {view,highlight};
};
