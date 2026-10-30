/* Demo transport never performs network requests. Mutations affect this page session only. */
(() => {
  const fixtures=window.CONSOLE_FIXTURES;
  const clone=v=>JSON.parse(JSON.stringify(v));
  const key=path=>decodeURI(path.split('?')[0].replace(/^\//,''));
  let seq=0;
  window.ConsoleDemo={
    get(path) {
      const k=key(path);
      if(k==='api/console/identity'&&new URLSearchParams(location.search).get('readonly')==='1')return {actor:'demo-viewer',admin:false,reason:'This monitor is read-only for your account. Ask an operator to add you to MONITOR_ADMINS.'};
      if(Object.hasOwn(fixtures,k))return clone(fixtures[k]);
      const error=new Error('No demo evidence for this request');error.status=404;throw error;
    },
    async write(path,method,body={}) {
      if(!this.get('api/console/identity').admin)throw new Error('Read-only account');
      const k=key(path),parts=k.split('/'),name=decodeURIComponent(parts[2]||''),base='api/apps/'+name;
      if(k==='api/actions/mute'&&method==='POST'){
        fixtures[k].mutes.push({id:'demo-mute-'+(++seq),starts_at:new Date().toISOString(),created_by:'demo-operator',...body});
      }else if(k.startsWith('api/actions/mute/')&&method==='DELETE'){
        fixtures['api/actions/mute'].mutes=fixtures['api/actions/mute'].mutes.filter(x=>x.id!==parts.at(-1));
      }else if(k==='api/model-prices'){
        fixtures[k].prices.push(body);
      }else if(k.endsWith('/product-config')){
        fixtures[k]={...fixtures[k],...body};
      }else if(k.includes('/funnels/')&&method==='PUT'){
        const f=decodeURIComponent(parts.at(-1));const d=fixtures[base+'/funnels'];d.specs=d.specs.filter(x=>x.funnel!==f).concat({funnel:f,steps:body.steps});
      }else if(k.endsWith('/config')){
        const cfg=fixtures[base+'/ops'].config;Object.assign(cfg,body,{tags_json:JSON.stringify(body.tags),updated_by:'demo-operator',updated_at:new Date().toISOString()});
        const a=window.MOCK.apps.find(x=>x.name===name);if(a){a.tags=body.tags;a.cost.budget_usd_month=body.budget_usd_month;a.governance.auto_stop=body.auto_stop;}
      }else if(k.endsWith('/slo')){
        const d=fixtures[k];d.specs=d.specs.filter(x=>x.slo!==body.slo).concat(body);
      }else if(k.includes('/slo/')&&method==='DELETE'){
        fixtures[base+'/slo'].specs=fixtures[base+'/slo'].specs.filter(x=>x.slo!==decodeURIComponent(parts.at(-1)));
      }else if(k==='api/actions/autostop-policy'){
        const targets=window.MOCK.apps.filter(a=>a.tags?.env!=='prod').map(a=>a.name);
        if(body.dry_run)return {targets};
        for(const app of targets)fixtures['api/apps/'+app+'/ops'].config.auto_stop=body.auto_stop;
        return {applied:targets};
      }else if(k.startsWith('api/actions/capacity/')){
        const result={path:'/monitor/capacity',max_healthy_qps:32,at_concurrency:4,recommended_qps:20.8,levels:[1,2,4,8].map(c=>({concurrency:c,requests:64*c,errors:c===8?3:0,qps:8*c,p95_ms:150*c}))};
        fixtures['api/apps/'+decodeURIComponent(parts.at(-1))+'/ops'].capacity=result;return result;
      }else if(k.startsWith('api/actions/appctl/')||k.startsWith('api/actions/review/')||['api/actions/provision','api/actions/run-journeys','api/actions/refresh-inventory'].includes(k)){
        return {run_id:'demo-'+(++seq)};
      }else throw new Error('Unsupported demo action');
      return {ok:true,demo:true};
    }
  };
})();
