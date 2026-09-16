// No browser: execute the template's actual diagram adapter with a small DOM double.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const page = fs.readFileSync(path.resolve(__dirname, '../maintain-project-map/assets/reader.html'), 'utf8');
const source = page.slice(page.indexOf('function graphHref'), page.indexOf('function card')) + page.slice(page.indexOf('function continuousDiagrams'), page.indexOf('function writeHash'));
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
assert.equal(nodes.find(e=>e.tag==='iframe').src,'architecture.html?canvas=1#focus=source-native');
select.value='sink-native';select.listeners.change();
assert.equal(nodes.find(e=>e.tag==='iframe').src,'architecture.html?canvas=1#focus=sink-native');
assert.equal(nodes.find(e=>e.tag==='a'&&e.textContent==='打开完整图').href,'architecture.html?canvas=1#focus=sink-native');
view=diagram('architecture','unknown');
assert.equal(flatten(view).filter(e=>e.tag==='iframe').length,0);
assert.ok(flatten(view).some(e=>e.textContent.includes('尚未关联')));
view=diagram('architecture','R1',true);
assert.equal(flatten(view).find(e=>e.tag==='iframe').src,'architecture.html?canvas=1&embed=1#focus=source-native');
assert.equal(flatten(view).find(e=>e.tag==='a'&&e.textContent==='打开完整图').href,'architecture.html?canvas=1#focus=source-native');
data.diagrams.architecture={file:null,canonical_file:'old.native.html',reason:'Invalid source',errors:[{message:'Bad JSON'}]};
view=diagram('architecture');
assert.equal(flatten(view).filter(e=>['iframe','a'].includes(e.tag)).length,0);
assert.ok(flatten(view).some(e=>e.textContent==='Bad JSON'));
// Exercise the actual C disclosure for a workflow-only project. Its graph is
// loaded once on expansion and uses the native workflow focus protocol.
const state={focus:'R1'},kindNames={module:'Module'};
const visible=()=>[{id:'R1',kind:'module',title:'整理内容',body_html:'<p>说明</p>'}];
const sidebar=()=>el('aside'),heading=()=>el('h1'),prose=()=>el('article'),toolbar=()=>el('nav'),tags=()=>el('span'),relations=()=>el('div'),source=()=>el('details');
const recordProse=()=>el('article');
const actualText=()=>'',gapText=()=>'';
data.project={name:'工作流项目'};
data.diagrams={workflow:{file:'workflow.html',nodes:[{id:'organize',record_ids:['R1']}],record_nodes:{R1:['organize']}}};
view=viewC();
const disclosure=flatten(view).find(e=>e.tag==='details'&&e.children.some(c=>c.tag==='summary'&&c.textContent.includes('功能路径')));
assert.equal(flatten(view).filter(e=>e.tag==='iframe').length,0);
disclosure.open=true;disclosure.listeners.toggle();
assert.deepEqual(flatten(view).filter(e=>e.tag==='iframe').map(e=>e.src),['workflow.html?canvas=1&embed=1']);
disclosure.listeners.toggle();
assert.equal(flatten(view).filter(e=>e.tag==='iframe').length,1);
// The chapter's separate entry carries the local record's native node focus.
const chapter=flatten(view).find(e=>e.tag==='article'&&e.className==='chapter');
const relatedDisclosure=flatten(chapter).find(e=>e.tag==='details'&&e.children.some(c=>c.tag==='summary'&&c.textContent.includes('功能路径')));
relatedDisclosure.open=true;relatedDisclosure.listeners.toggle();
assert.equal(flatten(chapter).find(e=>e.tag==='iframe').src,'workflow.html?canvas=1&embed=1#focus=organize');
console.log('Native embedding behavior: PASS (A/B/C, multi-node mapping, unmapped, failure, canonical link)');
`;
vm.runInNewContext(prelude + source + checks, { require, console }, { timeout: 5000 });
