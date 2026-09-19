// Run the real history directory with independent occurrences of a shared record.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.resolve(__dirname,'../maintain-project-map/assets/development-history.js'),'utf8');
const prelude=String.raw`
const assert=require('node:assert/strict');
class Elem {
 constructor(tag,cls,text){this.tag=tag;this.className=cls||'';this.textContent=text||'';this.children=[];this.attrs={};this.listeners={};this.dataset={};this.open=false;}
 append(...children){this.children.push(...children);}
 setAttribute(key,value){this.attrs[key]=value;}
 addEventListener(key,fn){this.listeners[key]=fn;}
}
const el=(...a)=>new Elem(...a),add=(p,...cs)=>{p.append(...cs.filter(Boolean));return p;};
const button=(text,fn,cls)=>{const b=el('button',cls,text);b.listeners.click=fn;return b;};
const navItem=(text,active,fn)=>{const b=button(text,fn,'nav');b.setAttribute('aria-current',active?'page':'false');return b;};
const records=[{id:'HIST-test',kind:'history',title:'Task',date:'2026-09-17'},
 {id:'EXP-shared',kind:'experience',task_id:'HIST-test',title:'Same source',summary:'small text',categories:['debugging','verification'],results:['failed','passed'],modules:['reader']},
 {id:'EXP-second',kind:'experience',task_id:'HIST-test',title:'Another source',categories:['improvement'],results:['adopted'],modules:['reader']}];
const data={development_history:{}},byId=new Map(records.map(r=>[r.id,r])),treeOpen=new Map();
const archivedRecord=r=>r.documentation?.state==='archived'||r.status==='archived';
const state={mode:'history',historyView:'problems',experience:'',task:'',historyEntry:'',query:'',historyCategory:'',historyResult:'',historyModule:''};
const flatten=e=>[e,...e.children.flatMap(flatten)];
let current;const render=()=>{current=historyDirectory(historyCases(),historyRows());},closeNavigation=()=>{};
`;
const checks=String.raw`
render();
let nodes=flatten(current),debug=nodes.find(n=>n.dataset.treeKey==='history:problems/debugging'),verify=nodes.find(n=>n.dataset.treeKey==='history:problems/verification');
assert.equal(debug.open,true);assert.equal(verify.open,false);
nodes.find(n=>n.dataset.historyEntry==='problems/debugging/EXP-shared').listeners.click();
nodes=flatten(current);assert.equal(nodes.filter(n=>n.attrs['aria-current']==='page').length,1);
assert.equal(nodes.find(n=>n.dataset.treeKey==='history:problems/verification').open,false);
debug=nodes.find(n=>n.dataset.treeKey==='history:problems/debugging');debug.open=false;debug.listeners.toggle();
verify=nodes.find(n=>n.dataset.treeKey==='history:problems/verification');verify.open=true;verify.listeners.toggle();
nodes.find(n=>n.dataset.historyEntry==='problems/verification/EXP-shared').listeners.click();
nodes=flatten(current);assert.equal(nodes.find(n=>n.dataset.treeKey==='history:problems/debugging').open,false);
assert.deepEqual(nodes.filter(n=>n.attrs['aria-current']==='page').map(n=>n.dataset.historyEntry),['problems/verification/EXP-shared']);
// A valid deep link picks only its own occurrence; invalid categories are repaired.
treeOpen.clear();normalizeHistoryState();render();nodes=flatten(current);
assert.equal(nodes.find(n=>n.dataset.treeKey==='history:problems/debugging').open,false);
assert.equal(nodes.find(n=>n.dataset.treeKey==='history:problems/verification').open,true);
state.historyEntry='problems/unknown/EXP-shared';normalizeHistoryState();assert.equal(state.historyEntry,'problems/debugging/EXP-shared');
// Same canonical record also has a separate task occurrence, with no duplicated data.
openHistoryRecord('EXP-shared','tasks');nodes=flatten(current);
assert.deepEqual(nodes.filter(n=>n.attrs['aria-current']==='page').map(n=>n.dataset.historyEntry),['tasks/HIST-test/EXP-shared']);
assert.equal(records.filter(r=>r.id==='EXP-shared').length,1);
state.historyView='problems';state.historyCategory='verification';state.historyResult='failed';assert.equal(historyCases().length,1);
state.historyModule='missing';assert.equal(historyCases().length,0);
console.log('History occurrence navigation: PASS');
`;
vm.runInNewContext(prelude+source+checks,{require,console},{timeout:5000});
