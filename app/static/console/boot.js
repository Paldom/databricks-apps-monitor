/* Same-origin data transport. Assets and APIs remain relative to the app prefix. */
(() => {
  'use strict';
  const script = document.currentScript;
  const assetBase = new URL('.', script.src);
  const apiBase = new URL('../', assetBase);
  const demo = new URLSearchParams(location.search).get('demo') === '1';
  let started = false, busy = false;
  const loadScript = name => new Promise((resolve, reject) => {
    const el = document.createElement('script');
    el.src = new URL(name, assetBase);
    el.onload = resolve;
    el.onerror = () => { el.remove(); reject(new Error('Console assets could not load')); };
    document.body.append(el);
  });
  async function get(path) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 55000);
    try {
      const response = await fetch(new URL(path, apiBase), {signal: controller.signal, headers: {Accept: 'application/json'}});
      if (!response.ok) {
        const error = new Error(response.status === 404 ? 'Not found' : `Request failed (HTTP ${response.status})`);
        error.status = response.status;
        throw error;
      }
      return await response.json();
    } finally { clearTimeout(timeout); }
  }
  async function write(path, method='POST', body) {
    if (demo) return window.ConsoleDemo.write(path, method, body);
    const response = await fetch(new URL(path, apiBase), {method, headers:{'Content-Type':'application/json'}, ...(body===undefined?{}:{body:JSON.stringify(body)})});
    const data = await response.json().catch(()=>({}));
    if (!response.ok) throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail || `HTTP ${response.status}`));
    return data;
  }
  const read = path => demo ? Promise.resolve().then(()=>window.ConsoleDemo.get(path)) : get(path);
  window.ConsoleData = {demo, get:read, write, url:path=>new URL(path, apiBase).href, classic: new URL('classic', apiBase).href};
  async function refresh() {
    if (busy) return;
    busy = true;
    try {
      if (demo && !started) { await loadScript('demo-data.js'); await loadScript('demo-fixtures.js'); await loadScript('demo-details.js'); }
      const data = demo ? window.MOCK : await get('api/console/snapshot');
      if (!data || !Array.isArray(data.apps)) throw new Error('Invalid fleet snapshot');
      if (!started) {
        window.MOCK = data;
        await loadScript('topology.js');
        await loadScript('sections.js');
        await loadScript('app.js');
        started = true;
      } else window.ConsoleApp.refresh(data);
      window.ConsoleApp?.connection(null);
    } catch (error) {
      if (started) window.ConsoleApp.connection('Refresh failed. Showing the last successful snapshot.');
      else {
        const main = document.getElementById('main');
        main.innerHTML = '<div class="loading"><div class="notice error" role="alert"><div><h1>Snapshot could not load</h1><p>Check the connection or workspace session, then retry.</p><button class="button" id="retry-snapshot">Retry</button></div></div></div>';
        main.setAttribute('aria-busy', 'false');
        document.getElementById('retry-snapshot').onclick = refresh;
      }
    } finally { busy = false; }
  }
  window.ConsoleData.retry = refresh;
  refresh();
  if (!demo) setInterval(refresh, 60000);
})();
