'use strict';
// Synthetic Cache/Fetch tests only. No network requests or real SW registration.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = 'https://example.test/chiang-mai/';
const listeners = {};
const stores = new Map();
let network = 'ok', quotaFull = false, skipped = false, claimed = false;
function store(name) {
  if (!stores.has(name)) stores.set(name, new Map());
  const entries = stores.get(name);
  return {
    addAll: async urls => { for (const url of urls) entries.set(url, new Response(url.endsWith('practice.html') ? 'PRACTICE' : 'HOME')); },
    match: async url => entries.get(url)?.clone(),
    put: async (url, response) => { if (quotaFull) throw new Error('quota'); entries.set(url, response.clone()); }
  };
}
const context = vm.createContext({
  URL, Response,
  self: { registration: { scope: ROOT }, addEventListener: (type, fn) => listeners[type] = fn,
          skipWaiting: async () => { skipped = true; }, clients: { claim: async () => { claimed = true; } } },
  caches: { open: async name => store(name), keys: async () => [...stores.keys()], delete: async name => stores.delete(name) },
  fetch: async request => {
    if (network === 'offline') throw new Error('offline');
    if (network === 'server-error') return new Response('SERVER ERROR', { status: 503 });
    return new Response('ONLINE:' + new URL(request.url).pathname);
  }
});
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8'), context);
let assertions = 0;
function check(value, message) { assert.ok(value, message); assertions++; }
async function lifecycle(type) { let pending; listeners[type]({ waitUntil: p => pending = p }); await pending; }
async function request(url, method = 'GET', mode = 'navigate') {
  let pending;
  listeners.fetch({ request: { url, method, mode }, respondWith: p => pending = p });
  return pending ? await pending : null;
}
(async () => {
  stores.set('chiangmai-ear-shell-v5', new Map());
  stores.set('unrelated-app-cache', new Map());
  await lifecycle('install');
  check(skipped, 'New SW may activate after all shell assets cached');
  check(stores.get('chiangmai-ear-shell-v6').size === 4, 'Four shell assets cached');
  check(stores.get('chiangmai-ear-shell-v6').has(ROOT + 'practice.html'), 'Practice included');
  await lifecycle('activate');
  check(claimed, 'Clients claimed');
  check(!stores.has('chiangmai-ear-shell-v4'), 'Old app cache removed');
  check(stores.has('unrelated-app-cache'), 'Other caches preserved');
  network = 'offline';
  check(await (await request(ROOT + 'practice.html?revision=6')).text() === 'PRACTICE', 'Query-stripped offline practice is not home');
  check(await (await request(ROOT + 'index.html')).text() === 'HOME', 'Original page remains distinct');
  check(await request(ROOT + 'missing.html') === null, 'Unknown page not silently mapped to home');
  check(await request('https://elsewhere.test/practice.html') === null, 'External origin untouched');
  check(await request(ROOT + 'practice.html', 'POST') === null, 'POST untouched');
  check(await request(ROOT + 'practice.html', 'GET', 'cors') === null, 'Non-navigation untouched');
  network = 'server-error';
  check(await (await request(ROOT + 'practice.html')).text() === 'PRACTICE', 'Server error falls back to correct cached page');
  network = 'ok'; quotaFull = true;
  check((await (await request(ROOT + 'practice.html')).text()).startsWith('ONLINE:'), 'Quota failure does not hide a valid response');
  console.log(JSON.stringify({status:'PASS', assertions, method:'Synthetic Cache/Fetch only; real offline browser navigation NOT_RUN'}, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
