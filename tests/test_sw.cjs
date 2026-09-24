'use strict';
// Synthetic Cache/Fetch only; does not certify a real phone or installed Service Worker.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ROOT='https://example.test/chiang-mai/',listeners={},stores=new Map();
let network='ok',quotaFull=false,skipped=false,claimed=false,count=0;
const code=fs.readFileSync(path.join(__dirname,'..','sw.js'),'utf8');
const CACHE=code.match(/const CACHE = '([^']+)'/)[1];
function store(name){if(!stores.has(name))stores.set(name,new Map());const entries=stores.get(name);return {
 addAll:async urls=>{for(const url of urls)entries.set(url,new Response(url.endsWith('alphabet.html')?'ALPHABET':url.endsWith('practice.html')?'PRACTICE':'HOME'));},
 match:async url=>entries.get(url)?.clone(),
 put:async(url,response)=>{if(quotaFull)throw new Error('quota');entries.set(url,response.clone());}
};}
const context=vm.createContext({URL,Response,self:{registration:{scope:ROOT},addEventListener:(t,f)=>listeners[t]=f,skipWaiting:async()=>{skipped=true;},clients:{claim:async()=>{claimed=true;}}},caches:{open:async name=>store(name),keys:async()=>[...stores.keys()],delete:async name=>stores.delete(name)},fetch:async req=>{if(network==='offline')throw new Error('offline');if(network==='server-error')return new Response('SERVER ERROR',{status:503});return new Response('ONLINE:'+new URL(req.url).pathname);}});
vm.runInContext(code,context);
function check(ok,msg){assert.ok(ok,msg);count++;}
async function lifecycle(t){let p;listeners[t]({waitUntil:x=>p=x});await p;}
async function request(url,method='GET',mode='navigate'){let p;listeners.fetch({request:{url,method,mode},respondWith:x=>p=x});return p?await p:null;}
(async()=>{
 stores.set('chiangmai-ear-shell-v8',new Map());stores.set('other-app',new Map());
 await lifecycle('install');check(skipped,'Activated after successful caching');
 check(CACHE==='chiangmai-ear-shell-v9','Release cache v9');check(stores.get(CACHE).size===5,'Five assets cached');
 check(stores.get(CACHE).has(ROOT+'alphabet.html'),'Alphabet included');
 await lifecycle('activate');check(claimed,'Clients claimed');check(!stores.has('chiangmai-ear-shell-v8'),'Actual previous cache removed');check(stores.has('other-app'),'Other app caches preserved');
 network='offline';
 check(await(await request(ROOT+'alphabet.html?v=1.4.0')).text()==='ALPHABET','Alphabet fallback is alphabet');
 check(await(await request(ROOT+'practice.html?revision=9')).text()==='PRACTICE','Practice fallback remains distinct');
 check(await(await request(ROOT+'index.html')).text()==='HOME','Home fallback remains distinct');
 check(await request(ROOT+'missing.html')===null,'Unknown routes not hijacked');
 check(await request('https://elsewhere.test/alphabet.html')===null,'Other origins untouched');
 check(await request(ROOT+'alphabet.html','POST')===null,'POST untouched');
 check(await request(ROOT+'alphabet.html','GET','cors')===null,'Non-navigation untouched');
 network='server-error';check(await(await request(ROOT+'alphabet.html')).text()==='ALPHABET','Server error falls back correctly');
 network='ok';quotaFull=true;check((await(await request(ROOT+'alphabet.html')).text()).startsWith('ONLINE:'),'Quota failure preserves successful response');
 console.log(JSON.stringify({status:'PASS',assertions:count,scope:'Synthetic Cache/Fetch only; real offline navigation NOT_RUN'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
