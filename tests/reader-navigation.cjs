// Exercise the reader's actual URL state logic without a browser dependency.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const page=fs.readFileSync(path.resolve(__dirname,'../maintain-project-map/assets/reader.html'),'utf8');
const source=page.slice(page.indexOf('function writeHash'),page.indexOf('function renderContent'));
vm.runInNewContext(`
const assert=require('node:assert/strict');
const data={default_mode:'a'},state={mode:'a',focus:'first',panel:'spec',angle:'explain',tab:'current',history:false,verification:false};
const byId=new Map([['first',{status:'current',kind:'module'}],['旧 / #1',{status:'superseded',kind:'verification'}]]);
const documents=new Map([['doc-contract',{}]]),revealRecord=()=>{};
const historical=new Set(['superseded']),selected=()=>byId.get(state.focus);
const location={hash:''},calls=[];
const history={pushState:(_,__,url)=>{calls.push('push');location.hash=url;},replaceState:(_,__,url)=>{calls.push('replace');location.hash=url;}};
let ready=false;
${source}
writeHash();assert.deepEqual(calls,['replace']);
ready=true;state.mode='b';state.focus='旧 / #1';state.angle='workflow';state.panel='architecture';state.tab='gaps';writeHash();
const deep=location.hash;
assert.deepEqual(calls,['replace','push']);
writeHash();assert.equal(calls.length,2,'Rerender must not add a history entry');
Object.assign(state,{mode:'a',focus:'first',panel:'spec',angle:'explain',tab:'current'});readHash();
assert.deepEqual([state.mode,state.focus,state.panel,state.angle,state.tab],['b','旧 / #1','architecture','workflow','gaps']);
assert.equal(state.history,true);assert.equal(state.verification,true);
writeHash();assert.equal(location.hash,deep);assert.equal(calls.length,2,'Restoring a valid history entry does not branch history');
location.hash='#mode=c&record=first';readHash();assert.equal(state.mode,'c');assert.equal(state.angle,'explain');assert.equal(state.panel,'spec');assert.equal(state.tab,'current');
location.hash='#mode=bad&record=missing&panel=bad&angle=bad&tab=bad';readHash();assert.equal(state.mode,'a');assert.equal(state.focus,'first');assert.equal(state.panel,'spec');
location.hash='#mode=b&record=first&document=doc-contract&anchor=%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86';readHash();assert.equal(state.document,'doc-contract');assert.equal(state.anchor,'错误处理');writeHash();assert.equal(new URLSearchParams(location.hash.slice(1)).get('document'),'doc-contract');
assert.equal(state.documentRecord,'first');
location.hash='#mode=b&record=&document=doc-contract';readHash();assert.equal(state.documentRecord,'');writeHash();assert.equal(new URLSearchParams(location.hash.slice(1)).get('record'),'','A source opened from the overview must not acquire an unrelated return record');
location.hash='#mode=b&record=first';readHash();assert.equal(state.document,'');assert.equal(state.anchor,'');
console.log('Reader URL state: PASS (deep links, encoded IDs, history, invalid values, legacy links)');
`,{require,console,URLSearchParams},{timeout:5000});
