// No browser: execute the template's actual diagram adapter with a small DOM double.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const page = fs.readFileSync(path.resolve(__dirname, '../maintain-project-map/assets/reader.html'), 'utf8');
const source = page.slice(page.indexOf('function graphHref'), page.indexOf('function card'));
const prelude = String.raw`
const assert = require('node:assert/strict');
class Elem {
 constructor(tag,cls,text){this.tag=tag;this.className=cls||'';this.textContent=text||'';this.children=[];this.attrs={};this.listeners={};this.dataset={};}
 get childElementCount(){return this.children.length;}
 append(...cs){this.children.push(...cs);}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(k,f){this.listeners[k]=f;}
}
const el=(tag,cls,text)=>new Elem(tag,cls,text),add=(p,...cs)=>{p.append(...cs.filter(Boolean));return p;};
const button=(text,fn)=>{const e=el('button','',text);e.addEventListener('click',fn);return e;};
const ProjectMapCanvas={mount:frame=>{const stage=el('div','canvas-stage');stage.append(frame);return stage;}};
const isSystem=false,restoringSnapshot=null,state={node:''},frames=new Map();
const navigate=()=>{},historical=new Set(['retired']),statusNames={retired:'已退役'};
const byId=new Map([['R1',{id:'R1',title:'Record 1'}],['R2',{id:'R2',title:'Record 2'}]]);
const data={diagrams:{architecture:{file:'architecture.html',canonical_file:'architecture.native.html',title:'Native graph',nodes:[{id:'source-native',label:'Source',record_ids:['R1','R2']},{id:'sink-native',label:'Sink',record_ids:['R1']}],record_nodes:{R1:['source-native','sink-native']},warnings:[{code:'test',message:'Mapping warning'}],source_path:'diagrams/architecture.json',source_sha256:'hash'}}};
const flatten=e=>[e,...e.children.flatMap(flatten)];
`;
const checks = String.raw`
let view=diagram('architecture');
assert.equal(flatten(view).find(e=>e.tag==='iframe').src,'architecture.html?canvas=1');
assert.equal(flatten(view).filter(e=>e.tag==='a'&&e.href==='architecture.native.html').length,1);
view=diagram('architecture','R1');
let nodes=flatten(view),select=nodes.find(e=>e.tag==='select');
assert.equal(select.children.length,2);
const frame=nodes.find(e=>e.tag==='iframe');assert.equal(frame.src,'architecture.html?canvas=1');assert.equal(frame.dataset.targetNode,'source-native');const messages=[];frame.contentWindow={postMessage:(message)=>messages.push(message)};frames.get(frame).ready=true;
select.value='sink-native';select.listeners.change();
assert.equal(frame.dataset.targetNode,'sink-native');assert.deepEqual(messages,[{channel:'project-map/v1',type:'focus-node',node:'sink-native'}]);
assert.equal(nodes.find(e=>e.tag==='a'&&e.textContent==='打开完整图').href,'architecture.html?canvas=1#focus=sink-native');
view=diagram('architecture','unknown');
assert.equal(flatten(view).filter(e=>e.tag==='iframe').length,0);
assert.ok(flatten(view).some(e=>e.textContent.includes('尚未关联')));
state.node='sink-native';view=diagram('architecture','R1');assert.equal(flatten(view).find(e=>e.tag==='iframe').dataset.targetNode,'sink-native');state.node='';
data.diagrams.architecture={file:null,canonical_file:'old.native.html',reason:'Invalid source',errors:[{message:'Bad JSON'}]};
view=diagram('architecture');
assert.equal(flatten(view).filter(e=>['iframe','a'].includes(e.tag)).length,0);
assert.ok(flatten(view).some(e=>e.textContent==='Bad JSON'));
console.log('Native embedding behavior: PASS (focus protocol, multi-node mapping, restored focus, unmapped, failure, canonical link)');
`;
vm.runInNewContext(prelude + source + checks, { require, console }, { timeout: 5000 });
