// Run the actual reader's filtering and notice rendering, not a reimplementation.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const page=fs.readFileSync(path.resolve(__dirname,'../maintain-project-map/assets/reader.html'),'utf8');
const slice=(a,b)=>page.slice(page.indexOf(a),page.indexOf(b));
const functions=slice('function archivedRecord','document.querySelector')+
 slice('function visible','function localRef')+
 slice('function recordHeading','function documentView');
vm.runInNewContext(`
const assert=require('node:assert/strict');
const records=[{id:'active',kind:'interface',status:'current',title:'Shared keyword',body:'Current'},
 {id:'old',kind:'interface',status:'current',title:'Shared keyword',body:'Archived locator',documentation:{state:'archived',successor:'active'},archive_page:'archive/test.html'}];
const byId=new Map(records.map(r=>[r.id,r])),recordOrder=new Map(),historical=new Set(['archived','retired']);
const state={query:'keyword',history:false,verification:false};
class Elem{constructor(tag,cls,text){this.tag=tag;this.textContent=text||'';this.children=[];}append(...cs){this.children.push(...cs);}}
const el=(...a)=>new Elem(...a),add=(e,...cs)=>{e.append(...cs.filter(Boolean));return e;};
const tags=r=>el('div'),navigate=id=>state.focus=id,button=(text,fn)=>{let b=el('button','',text);b.click=fn;return b;};
const flat=e=>[e,...e.children.flatMap(flat)];
${functions}
assert.equal(visible().length,1);assert.equal(visible()[0].id,'active');
state.history=true;assert.equal(visible().length,2);
let heading=recordHeading(records[1]);let elements=flat(heading);
assert.equal(elements.find(e=>e.textContent==='查看归档原文').href,'archive/test.html');
elements.find(e=>e.textContent==='打开当前说明').click();assert.equal(state.focus,'active');
records[0].source_health={notice:'源码变化，尚未判定说明失效',changes:[{workspace_id:'src',path:'main.py',changed_dependencies:[{path:'dep.py'}]}]};
elements=flat(recordHeading(records[0]));assert.ok(elements.some(e=>e.textContent==='说明待复核'));
assert.ok(elements.some(e=>e.textContent.includes('dep.py')));
console.log('Archive scope and review notices: PASS');
`,{require,console},{timeout:5000});
