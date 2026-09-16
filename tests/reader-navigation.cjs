// Test the real URL codec and history controller with browser history semantics.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const base=path.resolve(__dirname,'../maintain-project-map/assets');
const page=fs.readFileSync(path.join(base,'reader.html'),'utf8');
const codec=page.slice(page.indexOf('function writeHash'),page.indexOf('function capturePage'));
const historySource=fs.readFileSync(path.join(base,'reader-history.js'),'utf8');
const sandbox={require,console,URLSearchParams};
vm.runInNewContext(`
const assert=require('node:assert/strict'),clone=x=>JSON.parse(JSON.stringify(x));
const data={default_mode:'a'},defaultMode='a',state={mode:'a',focus:'first',panel:'spec',angle:'explain',tab:'current',history:false,verification:false,node:'',update:'',query:''};
const byId=new Map([['first',{status:'current',kind:'module'}],['旧 / #1',{status:'superseded',kind:'verification'}]]);
const documents=new Map([['doc-contract',{}]]),revealRecord=()=>{};
const historical=new Set(['superseded']),selected=()=>byId.get(state.focus);
let isSystem=false;
const location=globalThis.location={hash:'',pathname:'/map/'};
let cursor=0;const entries=[{state:null,url:''}],events={};
globalThis.addEventListener=(type,fn)=>events[type]=fn;
globalThis.history={
 get state(){return clone(entries[cursor].state);},
 pushState(value,_,url){entries.splice(cursor+1);entries.push({state:clone(value),url});cursor++;location.hash=url;},
 replaceState(value,_,url){entries[cursor]={state:clone(value),url};location.hash=url;},
 back(){if(cursor){cursor--;location.hash=entries[cursor].url;events.popstate();}},
 forward(){if(cursor+1<entries.length){cursor++;location.hash=entries[cursor].url;events.popstate();}}
};
${historySource}
${codec}
let ui={main:0,sidebar:0,tree:[],diagrams:{}},canBack=false;
const nav=ProjectMapHistory.create('map-one',()=>clone({state,ui}),value=>{
 if(value){Object.assign(state,value.state);ui=value.ui;}else readHash();nav.commit(writeHash());
},value=>canBack=value);
nav.restoreCurrent();assert.equal(canBack,false);assert.equal(entries.length,1);
ui={main:480,sidebar:160,tree:[['core',true]],diagrams:{architecture:{focus:'node1',camera:{scale:.4,x:87,y:-34}}}};
nav.save();Object.assign(state,{mode:'updates',update:'UPD-1',query:'接入'});ui={main:0};nav.commit(writeHash());
assert.equal(canBack,true);assert.equal(entries.length,2);
ui.main=240;nav.save();Object.assign(state,{mode:'a',panel:'workflow',node:'node / #1',query:''});nav.commit(writeHash());
assert.equal(new URLSearchParams(location.hash.slice(1)).get('node'),'node / #1');
nav.back();assert.equal(state.mode,'updates');assert.equal(state.update,'UPD-1');assert.equal(state.query,'接入');assert.equal(ui.main,240);
nav.back();assert.equal(ui.main,480);assert.equal(ui.sidebar,160);assert.equal(ui.tree[0][1],true);assert.equal(ui.diagrams.architecture.camera.x,87);assert.equal(canBack,false);
history.forward();assert.equal(state.mode,'updates');assert.equal(entries.length,3,'Back/forward must not append entries');
nav.commit(writeHash());assert.equal(entries.length,3,'Same-state render must not append an entry');
// Opening an old C link preserves its record and heading without resurrecting C.
location.hash='#mode=c&record=first&anchor=details';readHash();assert.equal(state.mode,'b');assert.equal(state.anchor,'details');
location.hash='#mode=c';readHash();assert.equal(state.mode,'a');
location.hash='#mode=bad&record=missing&panel=bad&angle=bad&tab=bad';readHash();assert.equal(state.mode,'a');assert.equal(state.panel,'spec');
location.hash='#mode=b&record=旧+%2F+%231&angle=workflow&verification=1';readHash();assert.equal(state.focus,'旧 / #1');assert.equal(state.verification,true);assert.equal(state.history,true);
location.hash='#mode=b&record=first&document=doc-contract&anchor=错误处理';readHash();assert.equal(state.documentRecord,'first');assert.equal(state.anchor,'错误处理');
location.hash='#mode=b&record=&document=doc-contract';readHash();assert.equal(state.documentRecord,'');assert.equal(new URLSearchParams(writeHash().slice(1)).get('record'),'');
location.hash='#mode=b&record=first';readHash();assert.equal(state.document,'');assert.equal(state.anchor,'');assert.equal(state.node,'');
byId.set('UPD-direct',{id:'UPD-direct',kind:'update',status:'current'});
location.hash='#mode=b&record=UPD-direct';readHash();assert.equal(state.mode,'updates');assert.equal(state.update,'UPD-direct');
location.hash='#mode=a&record=UPD-direct';readHash();assert.equal(state.mode,'a','Overview links must keep their selected mode');
isSystem=true;
location.hash='#mode=a&panel=workflow';readHash();assert.equal(state.panel,'architecture');
location.hash='#mode=b&angle=workflow&record=first';readHash();assert.equal(state.angle,'architecture');
location.hash='#mode=members';readHash();assert.equal(state.mode,'members');
location.hash='#mode=b&angle=relations';readHash();assert.equal(state.angle,'relations');
console.log('Reader history and deep links: PASS');
`,sandbox,{timeout:5000});
