/* Human task narratives and explicitly opened evidence. No background fetch. */
const historyPackets=new Map(),historyExpanded=new Map();
const eventKindNames={user:'用户要求',assistant:'公开答复',tool_call:'工具调用',tool_result:'工具返回'};
const historyCategories=data.development_history?.categories||{debugging:'排错与修复',improvement:'改进',verification:'验证',exploration:'方案探索','human-correction':'人工纠偏'};
const historyResults=data.development_history?.results||{failed:'曾未通过',passed:'验证通过',adopted:'已采用',not_adopted:'未采用',pending:'待验证'};
const historyViewMemory=new Map();let historyViewRestore=null;
const historyViewFields=['historyView','historyEntry','experience','task','event','query','anchor','historyCategory','historyResult','historyModule'];
function historyMatches(r){const terms=state.query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);return terms.every(q=>[r.title,r.summary,r.body,r.date,r.applicability,r.outcome,...(r.aliases||[]),...(r.modules||[]),...(r.related_records||[])].join(' ').toLocaleLowerCase().includes(q));}
function historyRows(){
 return records.filter(r=>r.kind==='history'&&historyMatches(r))
  .sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||b.id.localeCompare(a.id));
}
function historyCases(filtered=true){return records.filter(r=>r.kind==='experience'&&(!filtered||(historyMatches(r)&&(!state.historyCategory||(r.categories||[]).includes(state.historyCategory))&&(!state.historyResult||(r.results||[]).includes(state.historyResult))&&(!state.historyModule||(r.modules||[]).includes(state.historyModule))))).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||a.title.localeCompare(b.title,'zh-CN'));}
function historyEntryFor(r,view,group=''){
 if(view==='tasks')return 'tasks/'+(r.task_id||r.id)+'/'+r.id;
 const category=(r.categories||[]).includes(group)?group:(r.categories||[])[0];
 return 'problems/'+category+'/'+r.id;
}
function normalizeHistoryState(){
 if(!['problems','tasks'].includes(state.historyView))state.historyView=state.task&&!state.experience?'tasks':historyCases(false).length?'problems':'tasks';
 const c=byId.get(state.experience);
 if(c?.kind==='experience'){
  state.task=c.task_id;
  const group=(state.historyEntry||'').split('/')[1],expected=historyEntryFor(c,state.historyView,group);
  if(state.historyEntry!==expected)state.historyEntry=expected;
 }else{
  state.experience='';
  if(byId.get(state.task)?.kind!=='history')state.task='';
  state.historyEntry=state.historyView==='tasks'&&state.task?historyEntryFor(byId.get(state.task),'tasks'):'';
 }
 if(!historyCategories[state.historyCategory])state.historyCategory='';
 if(!historyResults[state.historyResult])state.historyResult='';
}
function clearHistorySelection(){state.experience='';state.task='';state.event='';state.anchor='';state.historyEntry='';}
function openHistoryRecord(id,view=state.historyView,group=''){
 const r=byId.get(id);if(!r||!['history','experience'].includes(r.kind))return;
 state.mode='history';state.document='';state.anchor='';state.event='';state.historyView=r.kind==='history'?'tasks':view;
 state.experience=r.kind==='experience'?r.id:'';state.task=r.task_id||r.id;state.historyEntry=historyEntryFor(r,state.historyView,group);
 // Opening a document never expands other occurrences of its shared record.
 treeOpen.set('history:'+state.historyEntry.split('/').slice(0,2).join('/'),true);
 render();closeNavigation();
}
function switchHistoryView(view){
 if(view===state.historyView)return;
 historyViewMemory.set(state.historyView,capturePage());const saved=historyViewMemory.get(view);
 clearHistorySelection();state.query='';state.historyCategory='';state.historyResult='';state.historyModule='';state.historyView=view;
 if(saved?.state)for(const key of historyViewFields)state[key]=saved.state[key]||'';
 historyViewRestore=saved||null;render();historyViewRestore=null;
}
function historyViewTabs(){const nav=el('nav','history-view-tabs');nav.setAttribute('aria-label','开发历程阅读方式');for(const [view,label] of [['problems','按问题查找'],['tasks','按任务回顾']]){const b=button(label,()=>switchHistoryView(view));b.setAttribute('aria-pressed',String(state.historyView===view));nav.append(b);}return nav;}
function historyDirectory(cases,tasks){
 const nav=el('nav','history-directory');nav.setAttribute('aria-label',state.historyView==='problems'?'经验分类目录':'任务回顾目录');
 const groups=state.historyView==='problems'?Object.entries(historyCategories).map(([id,title])=>({id,title,rows:cases.filter(r=>(r.categories||[]).includes(id))})).filter(g=>g.rows.length):tasks.map(r=>({id:r.id,title:r.title,rows:[r,...cases.filter(c=>c.task_id===r.id)]}));
 for(const [index,g] of groups.entries()){
  const group=el('details','tree-group history-group'),prefix=state.historyView+'/'+g.id,key='history:'+prefix;
  group.dataset.treeKey=key;group.open=treeOpen.get(key)??(state.historyEntry?state.historyEntry.startsWith(prefix+'/'):index===0);
  treeOpen.set(key,group.open);let lastOpen=group.open;
  group.addEventListener('toggle',()=>{if(group.open!==lastOpen){treeOpen.set(key,group.open);lastOpen=group.open;}});
  const label=el('summary','tree-label',g.title);label.append(el('span','history-count',g.rows.length));group.append(label);
  for(const r of g.rows){const entry=historyEntryFor(r,state.historyView,g.id),b=navItem(r.kind==='history'?'任务全程':r.title,entry===state.historyEntry,()=>openHistoryRecord(r.id,state.historyView,g.id));b.dataset.historyEntry=entry;b.dataset.historyRecord=r.id;group.append(b);}
  nav.append(group);
 }
 return nav;
}
function historyFilters(){
 const row=el('div','history-filters');
 const modules=[...new Set(historyCases(false).flatMap(r=>r.modules||[]))].sort((a,b)=>a.localeCompare(b,'zh-CN'));
 for(const [field,label,choices] of [['historyCategory','工作类别',historyCategories],['historyResult','包含的尝试结果',historyResults],['historyModule','涉及模块',Object.fromEntries(modules.map(m=>[m,m]))]]){
  const wrap=el('label'),select=el('select');select.setAttribute('aria-label',label);select.append(add(el('option','', '全部'),null));select.firstChild.value='';
  for(const [value,text] of Object.entries(choices)){const option=el('option','',text);option.value=value;select.append(option);}select.value=state[field]||'';
  select.addEventListener('change',()=>{state[field]=select.value;clearHistorySelection();renderContent();});add(wrap,el('span','',label),select);row.append(wrap);
 }
 return row;
}
function historyBadges(r){const badges=el('div','tags');for(const value of r.categories||[])badges.append(el('span','tag',historyCategories[value]||value));for(const value of r.results||[])badges.append(el('span','tag',historyResults[value]||value));return badges;}
function historyCaseCard(r,view=state.historyView,group=''){const article=el('article','update-row history-case');add(article,historyBadges(r),el('h2','',r.title),el('p','',r.summary),el('p','history-row-meta',(r.modules||[]).join(' · ')+' ｜ '+r.outcome),button('阅读这条经验 →',()=>openHistoryRecord(r.id,view,group),'link'));return article;}
function historyDate(value){if(!value)return '时间未记录';const date=new Date(value);return Number.isNaN(date.getTime())?value:date.toLocaleString('zh-CN',{hour12:false});}
function historyDescriptor(task){return data.development_history?.tasks?.[task];}
function historyFile(task,id,offset=0){return historyDescriptor(task).folder+'/'+id+'-'+offset+'.json';}
async function loadHistoryFile(file){
 if(historyPackets.has(file))return historyPackets.get(file);
 if(!/^history\/[a-f0-9]{20}\/(index|EVT-[a-f0-9]{20}-\d+)\.json$/.test(file))throw new Error('记录位置不符合当前页面的范围。');
 if(location.protocol==='file:')throw new Error('请通过地图的本机预览地址打开，才能按需读取原始记录。');
 const url=new URL(file,location.href);
 if(url.origin!==location.origin)throw new Error('记录不在当前地图中。');
 const response=await fetch(url,{credentials:'same-origin',cache:'no-store'});
 if(!response.ok){let reason='原始记录暂不可用（'+response.status+'）。';try{reason=(await response.json()).error||reason;}catch(_){}throw new Error(reason);}
 const packet=await response.json();historyPackets.set(file,packet);return packet;
}
function historyFailure(box,error,retry){box.replaceChildren(el('p','',error.message||'读取失败'),button('重新读取',retry,'link'));}
function eventTextView(task,packet){
 const box=el('section','history-event-text'),id=packet.id;
 add(box,el('h4','',(eventKindNames[packet.kind]||packet.kind)+(packet.tool?' · '+packet.tool:'')),el('p','meta',historyDate(packet.timestamp)));
 const locationBox=el('details','history-location');
 add(locationBox,el('summary','','来源位置与指纹'),el('p','locator',packet.source.path+' : '+packet.source.line),el('p','locator','消息 '+(packet.native_id||'无宿主 ID')+(packet.call_id?' · 调用 '+packet.call_id:'')),el('p','locator','原始行 SHA-256 · '+packet.source.line_sha256),el('p','locator','文本 SHA-256 · '+packet.text_sha256));box.append(locationBox);
 const text=el('pre','history-raw'),progress=el('p','meta'),more=button('继续读取',()=>{});
 const key=task+'/'+id;let last=packet;
 function paint(){let pieces=[packet.text],next=packet.next_file;last=packet;while(next&&historyPackets.has(next)&&historyExpanded.get(key)>=last.end_offset){last=historyPackets.get(next);pieces.push(last.text);next=last.next_file;}text.textContent=pieces.join('');progress.textContent='已读 '+last.end_offset.toLocaleString()+' / '+packet.total_chars.toLocaleString()+' 字符'+(last.truncated?' · 其余尚未展开':' · 此段已读完');more.hidden=!last.next_file;}
 more.addEventListener('click',async()=>{more.disabled=true;try{const next=await loadHistoryFile(last.next_file);historyExpanded.set(key,next.end_offset);paint();}catch(error){progress.textContent=error.message;}finally{more.disabled=false;}});
 add(box,text,progress,more);if(packet.omitted_non_text_blocks)box.append(el('p','meta','此事件含 '+packet.omitted_non_text_blocks+' 个非文本块；本页未收录。'));paint();return box;
}
function evidenceBox(task,id,label){
 const details=el('details','history-evidence');details.dataset.historyEvidence=id;
 add(details,el('summary','',label),el('div','history-evidence-body'));
 const body=details.lastChild;let busy=false,done=false;
 function display(packet){
  body.replaceChildren(eventTextView(task,packet));
  const pairs=packet.pair_ids||[];
  if((packet.kind==='tool_call'||packet.kind==='tool_result')&&!pairs.length)body.append(el('p','meta','所选来源范围没有收录配对事件。'));
  for(const pairedId of pairs){const file=historyFile(task,pairedId);if(historyPackets.has(file))body.append(eventTextView(task,historyPackets.get(file)));}
  if(pairs.length)body.prepend(el('p','history-pair-label','以下按同一调用 ID 配对展示调用和返回；原文按需从 Codex 会话读取。'));
 }
 async function open(){
  if(done||busy)return;busy=true;body.replaceChildren(el('p','meta','正在读取这段依据…'));
  try{const packet=await loadHistoryFile(historyFile(task,id));await Promise.all((packet.pair_ids||[]).map(pair=>loadHistoryFile(historyFile(task,pair))));display(packet);done=true;}
  catch(error){historyFailure(body,error,open);}finally{busy=false;}
 }
 const cached=historyPackets.get(historyFile(task,id));
 if(cached&&(cached.pair_ids||[]).every(pair=>historyPackets.has(historyFile(task,pair)))){display(cached);done=true;}
 details.addEventListener('toggle',()=>{if(details.open)open();});
 if(state.event===id)details.open=true;
 return details;
}
function historyCoverage(r,descriptor){
 const c=descriptor.coverage,box=el('details','history-coverage');
 add(box,el('summary','','整理范围与来源'),el('p','',r.coverage_note||'按所选任务范围整理；叙述不是完整事件转录。'),el('p','',r.applicability||'适用版本未记录，请核查当前代码与条件。'),el('p','meta',historyDate(c.start_time)+' 至 '+historyDate(c.end_time)+' · '+c.event_count+' 个来源定位'),el('p','meta','原始消息和工具输出保留在 Codex 会话中，本地图只保存定位。点开依据时按段读取；原会话删除或内容改变时会提示不可用。'),el('p','locator',c.source_path+' : '+c.start_line+'–'+c.end_line));
 if(c.unpaired_calls.length)box.append(el('p','meta',c.unpaired_calls.length+' 组调用在所选范围内不完整。'));
 return box;
}
function allHistoryEvents(task){
 const outer=el('details','history-all-events'),box=el('div');add(outer,el('summary','','查找任务内的其他原始事件'),box);
 let rows=null,offset=0,query='';
 function paint(){
  const matched=rows.filter(e=>[e.id,e.tool,eventKindNames[e.kind],e.line].join(' ').toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  const list=el('div');for(const e of matched.slice(0,offset+15))list.append(evidenceBox(task,e.id,historyDate(e.timestamp)+' · '+(eventKindNames[e.kind]||e.kind)+(e.tool?' · '+e.tool:'')+' · 第 '+e.line+' 行'));
  content.replaceChildren(list,el('p','meta','已列出 '+Math.min(offset+15,matched.length)+' / '+matched.length+' 条。正文尚未读取；可按事件类型、工具或行号筛选。'));
  if(offset+15<matched.length)content.append(button('再显示 15 条',()=>{offset+=15;paint();}));
 }
 const input=el('input'),content=el('div');input.type='search';input.placeholder='筛选用户要求、工具名称或行号';input.setAttribute('aria-label','筛选任务原始事件');input.addEventListener('input',()=>{query=input.value;offset=0;paint();});
 async function load(){if(rows)return;box.replaceChildren(el('p','meta','正在读取事件目录…'));try{rows=await loadHistoryFile(historyDescriptor(task).index_file);box.replaceChildren(input,content);paint();}catch(error){historyFailure(box,error,load);}}
 outer.addEventListener('toggle',()=>{if(outer.open)load();});return outer;
}
function historyNarrative(r,task){
 const narrative=recordProse(r);narrative.classList.add('history-narrative');
 for(const link of narrative.querySelectorAll('a[data-history-event]')){
  const evidence=evidenceBox(task,link.dataset.historyEvent,link.textContent),p=link.parentElement;
  if(p.tagName==='P'&&p.textContent.trim()===link.textContent.trim())p.replaceWith(evidence);
  else{link.addEventListener('click',event=>{event.preventDefault();evidence.open=!evidence.open;});p.after(evidence);}
 }
 return narrative;
}
function viewDevelopmentHistory(){
 normalizeHistoryState();const cases=historyCases(),allCases=historyCases(false),tasks=historyRows();
 // A task remains discoverable when only one of its experiences matches a search.
 if(state.historyView==='tasks')for(const c of cases){const task=byId.get(c.task_id);if(task&&!tasks.some(t=>t.id===task.id))tasks.push(task);}
 const r=state.experience?byId.get(state.experience):state.historyView==='tasks'?byId.get(state.task):null;
 const s=sidebar([],state.historyView==='problems'?'按工作类别':'任务与经验'),m=el('main','main history-main');
 s.querySelector('.toolbar').before(historyViewTabs());s.querySelector('.sidebar-scroll').append(historyDirectory(cases,tasks));
 if(!r){
  if(state.historyView==='problems'){
   m.append(heading('按问题查找','从遇到的问题出发，查阅尝试、反馈和人的纠偏。','开发历程'),historyFilters());
   m.append(el('p','meta','共 '+cases.length+' 条经验；同一条经验可以属于多个类别，列表只展示一次。'));
   if(!cases.length)m.append(el('p','empty',allCases.length?'没有符合筛选条件的经验。可以清除搜索，或把类别、结果和模块改为“全部”。':'还没有独立整理的经验条目。可以切换“按任务回顾”阅读已有过程。'));
   else for(const c of cases)m.append(historyCaseCard(c,'problems',state.historyCategory));
  }else{
   m.append(heading('按任务回顾','保留一次任务的背景、推进顺序和相互关联的经验。','开发历程'));
   if(!tasks.length)m.append(el('p','empty',state.query?'没有匹配的任务。可以换一个问题或模块名称。':'还没有收录任务历程。'));
   for(const task of tasks){const article=el('article','update-row history-row');add(article,el('p','update-date',task.date),el('h2','',task.title),el('p','',task.summary),el('p','history-row-meta',task.outcome),button('阅读这次历程 →',()=>openHistoryRecord(task.id,'tasks'),'link'));m.append(article);}
  }
 }else{
  m.append(button(state.historyView==='problems'?'← 返回问题列表':'← 返回任务列表',()=>{clearHistorySelection();renderContent();},'link'));
  if(r.kind==='experience'){
   m.append(heading(r.title,r.summary,'开发历程 / '+(state.historyView==='problems'?(historyCategories[state.historyEntry.split('/')[1]]||'经验'):'任务中的经验')),historyBadges(r));
   m.append(el('p','history-row-meta',(r.modules||[]).join(' · ')+' ｜ '+r.outcome));
   const task=byId.get(r.task_id);m.append(button('所属任务：'+task.title,()=>{historyViewMemory.set(state.historyView,capturePage());state.query='';state.historyCategory='';state.historyResult='';state.historyModule='';openHistoryRecord(task.id,'tasks');},'link'));
   const coverage=el('details','history-coverage');add(coverage,el('summary','','适用条件与整理范围'),el('p','',r.applicability),el('p','',r.coverage_note));m.append(coverage,historyNarrative(r,task.id));
  }else{
   m.append(heading(r.title,r.summary,'开发历程 · '+r.date),el('p','history-row-meta',(r.modules||[]).join(' · ')+' ｜ '+r.outcome));
   const descriptor=historyDescriptor(r.id);if(descriptor)m.append(historyCoverage(r,descriptor),historyNarrative(r,r.id));else m.append(el('p','empty','这项历程的证据尚未导出。'));
   const children=allCases.filter(c=>c.task_id===r.id);if(children.length){const section=el('section','history-related');section.append(el('h2','','这次任务留下的经验'));for(const c of children)section.append(historyCaseCard(c,'tasks',r.id));m.append(section);}
  }
  const related=el('section','history-related');related.append(el('h2','','查看当前成果'));for(const id of r.related_records||[])if(byId.has(id))related.append(button(byId.get(id).title,()=>navigate(id),'link'));if(related.children.length>1)m.append(related);
  if(r.kind==='history'&&historyDescriptor(r.id))m.append(allHistoryEvents(r.id));
 }
 return add(el('div','shell'),s,m);
}
