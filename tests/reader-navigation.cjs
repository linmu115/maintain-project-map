// Exercise the current reader's real URL parser/serializer without a browser.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const page=fs.readFileSync(path.resolve(__dirname,'../maintain-project-map/assets/reader.html'),'utf8');
const source=page.slice(page.indexOf('function writeHash'),page.indexOf('/*__PROJECT_MAP_SYSTEM_READER__*/'));
vm.runInNewContext(`
const assert=require('node:assert/strict');
const defaultMode='a',isSystem=false,hasDevelopmentHistory=true;
const state={mode:'a',focus:'first',panel:'spec',angle:'explain',tab:'current',history:false,verification:false};
const byId=new Map([['first',{status:'current',kind:'module'}],['旧 / #1',{status:'superseded',kind:'verification'}],['HIST-one',{status:'current',kind:'history'}],['UPD-one',{status:'current',kind:'update'}]]);
for(const [id,record] of byId)record.id=id;
const documents=new Map([['doc-contract',{}]]),revealRecord=()=>{};
const historical=new Set(['superseded']),selected=()=>byId.get(state.focus);
const archivedRecord=r=>r.documentation?.state==='archived'||r.status==='archived',historicalRecord=r=>historical.has(r.status)||archivedRecord(r);
const location={hash:''};
${source}
state.mode='b';state.focus='旧 / #1';state.angle='workflow';state.panel='architecture';state.tab='gaps';location.hash=writeHash();
const deep=location.hash;
Object.assign(state,{mode:'a',focus:'first',panel:'spec',angle:'explain',tab:'current'});readHash();
assert.deepEqual([state.mode,state.focus,state.panel,state.angle,state.tab],['b','旧 / #1','architecture','workflow','gaps']);
assert.equal(state.history,true);assert.equal(state.verification,true);
location.hash=writeHash();assert.ok(location.hash.includes('history=1'));
location.hash='#mode=c&record=first';readHash();assert.equal(state.mode,'b');assert.equal(state.angle,'explain');assert.equal(state.panel,'spec');
location.hash='#mode=bad&record=missing&panel=bad&angle=bad&tab=bad';readHash();assert.equal(state.mode,'a');assert.equal(state.focus,'first');
location.hash='#mode=b&record=first&document=doc-contract&anchor=%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86';readHash();assert.equal(state.document,'doc-contract');assert.equal(state.anchor,'错误处理');assert.equal(new URLSearchParams(writeHash().slice(1)).get('document'),'doc-contract');
assert.equal(state.documentRecord,'first');
location.hash='#mode=b&record=&document=doc-contract';readHash();assert.equal(state.documentRecord,'');assert.equal(new URLSearchParams(writeHash().slice(1)).get('record'),'');
location.hash='#mode=b&record=HIST-one';readHash();assert.equal(state.mode,'history');assert.equal(state.task,'HIST-one');
location.hash='#mode=history&task=HIST-one&event=EVT-one&q=read';readHash();assert.equal(state.event,'EVT-one');assert.equal(new URLSearchParams(writeHash().slice(1)).get('task'),'HIST-one');
location.hash='#mode=b&record=UPD-one';readHash();assert.equal(state.mode,'updates');assert.equal(state.update,'UPD-one');
location.hash='#mode=history&experience=EXP-one&task=HIST-one&historyView=problems&historyEntry=problems%2Fverification%2FEXP-one&historyResult=failed&historyModule=reader';readHash();
const route=new URLSearchParams(writeHash().slice(1));
assert.equal(route.get('experience'),'EXP-one');assert.equal(route.get('historyEntry'),'problems/verification/EXP-one');assert.equal(route.get('historyView'),'problems');assert.equal(route.get('historyResult'),'failed');assert.equal(route.get('historyModule'),'reader');
console.log('Reader URL state: PASS');
`,{require,console,URLSearchParams},{timeout:5000});
