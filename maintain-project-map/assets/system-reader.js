/* System composition is a human projection; contracts remain in their owner maps. */
function systemLink(ref, label) {
  if (!ref.href) return el('span', 'meta', label || ref.title || ref.project_id);
  if (ref.href.startsWith('#')) return button(label || ref.title, () => navigate(ref.record_id || ref.id), 'link');
  if (location.protocol === 'file:') return el('span', 'meta', (label || ref.title) + ' · 请使用本地 HTTP 阅读链接');
  const link = el('a', 'system-link', label || ref.title);
  link.href = ref.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
  link.setAttribute('aria-label', (label || ref.title) + '（新标签页）');
  return link;
}
function systemMatches(item) {
  const q = state.query.trim().toLocaleLowerCase();
  return !q || JSON.stringify(item).toLocaleLowerCase().includes(q);
}
function systemCoverage(main) {
  const coverage = data.system_view?.coverage;
  if (!coverage) return;
  main.append(el('p', 'meta', `已读取 ${coverage.resolved} / ${coverage.declared} 个收录项目的快照。仅展示明确登记的关系；未登记不等于没有依赖。`));
  if (coverage.unresolved.length) main.append(el('p', 'chart-notices', '部分项目尚不可用，可在“收录项目”查看原因。'));
}
function systemMembers(main) {
  const grid = el('div', 'cards');
  for (const member of (data.system_view?.members || []).filter(systemMatches)) {
    const box = el('article', 'card');
    add(box, el('div', 'eyebrow', '独立维护的项目地图'), el('h2', '', member.name),
      el('p', '', member.role || '尚未说明在本系统中的职责。'), el('p', 'meta', '收录范围：' + member.scope),
      el('p', 'locator', member.project_id));
    if (member.reason) box.append(el('p', 'chart-notices', member.reason));
    if (member.href) box.append(systemLink(member, '进入项目 ↗'));
    grid.append(box);
  }
  main.append(grid.children.length ? grid : el('p', 'empty', '没有符合当前范围的收录项目。'));
}
function systemInterfaces(main) {
  const current = item => state.history || !historical.has(item.status);
  const rows = (data.system_view?.interfaces || []).filter(current).filter(systemMatches);
  for (const contract of rows) {
    const box = el('article', 'system-contract');
    add(box, el('div', 'eyebrow', '接口 · ' + contract.project_id),
      add(el('h2'), systemLink(contract, contract.title)), el('p', '', contract.summary),
      el('p', 'locator', contract.id + ' · ' + (statusNames[contract.status] || contract.status)));
    if (contract.interface_family) box.append(el('p', 'meta', '接口类别：' + contract.interface_family));
    for (const [key, title] of [['providers', '提供方'], ['consumers', '已登记的接入方']]) {
      const refs = contract[key] || [], section = add(el('section', 'system-endpoints'), el('h3', '', title));
      if (!refs.length) section.append(el('p', 'meta', '尚未登记。'));
      for (const ref of refs) add(section, add(el('div', 'relation'), systemLink(ref),
        el('span', 'meta', ref.project_id), ref.reason ? el('p', 'meta', ref.reason) : null));
      box.append(section);
    }
    const details = el('details', 'source');
    add(details, el('summary', '', '定义归属与快照'), el('p', 'locator', contract.path + ':' + contract.line),
      el('p', 'meta', '此处汇集摘要和关联；完整定义在提供方项目中维护。来源指纹 ' + (contract.source_sha256 || '未提供')));
    box.append(details); main.append(box);
  }
  if (!rows.length) main.append(el('p', 'empty', '没有符合当前范围的接口。'));
}
function systemRelations(main) {
  const names = {provides: '提供接口', consumes: '使用接口', depends_on: '依赖', contains: '包含', relates_to: '关联'};
  const rows = (data.system_view?.relations || []).filter(systemMatches);
  for (const relation of rows) {
    const row = el('article', 'system-contract'), endpoints = el('div', 'system-edge');
    add(endpoints, systemLink(relation.from), el('span', 'meta', names[relation.relation] || relation.relation), systemLink(relation.to));
    add(row, endpoints, el('p', 'locator', relation.from.project_id + ' → ' + relation.to.project_id));
    for (const reason of relation.reasons || [relation.reason]) if (reason) row.append(el('p', '', reason));
    if (!relation.from.known || !relation.to.known) row.append(el('p', 'meta', '有端点位于当前可读取范围之外，保留 ID 供定位。'));
    main.append(row);
  }
  if (!rows.length) main.append(el('p', 'empty', '没有符合当前范围的已登记关系。'));
}
function viewSystem() {
  const main = el('main', 'main'), items = [];
  const choose = (key, value) => {state[key] = value;state.node = '';state.document = '';state.anchor = '';renderContent();};
  let tree = null;
  if (state.mode === 'a') {
    for (const [value, title] of [['spec', '系统说明'], ['architecture', '整体组织']]) items.push([title, state.panel === value, () => choose('panel', value)]);
    if (state.panel === 'architecture') {
      main.append(heading('整体组织', '点击项目卡片查看语义护照，再从护照进入独立的项目地图。', '系统概览'));
      main.append(diagram('architecture'));
    } else {
      main.append(heading(data.project.name, '系统边界、子项目职责与共享约定。', '系统概览'));
      if (data.map_html) main.append(prose(data.map_html, 'map'));
      systemCoverage(main);
      const cards = el('div', 'cards'); visible().forEach(r => cards.append(card(r))); main.append(cards);
    }
  } else if (state.mode === 'members') {
    main.append(heading('收录项目', '项目各自维护记录与图；从这里在新标签页中打开。', '系统地图'));
    systemCoverage(main); systemMembers(main);
  } else {
    for (const [value, title] of [['interfaces', '接口目录'], ['relations', '关联关系'], ['explain', '系统记录']]) items.push([title, state.angle === value || (value === 'explain' && state.angle === 'architecture'), () => choose('angle', value)]);
    tree = {records: visible(), select: id => navigate(id)};
    if (state.angle === 'interfaces' || state.angle === 'relations') {
      main.append(heading(state.angle === 'interfaces' ? '接口目录' : '关联关系', '汇集提供方与接入方的已登记说明，点击标题打开所属地图。', '接口与关联'));
      systemCoverage(main);
      if (state.angle === 'interfaces') systemInterfaces(main); else systemRelations(main);
    } else if (documents.has(state.document)) documentView(main, documents.get(state.document));
    else {
      const record = visible().find(r => r.id === state.focus) || visible()[0];
      if (record) {
        state.focus = record.id; main.append(recordHeading(record));
        main.append(tabs([['说明与现状', state.angle === 'explain', () => choose('angle', 'explain')], ['相关结构', state.angle === 'architecture', () => choose('angle', 'architecture')]]));
        if (state.angle === 'architecture') main.append(diagram('architecture', record.id));
        else add(main, add(el('div', 'split'), add(el('article'), recordProse(record), source(record)), context(record)));
      } else main.append(el('p', 'empty', '尚无符合当前范围的系统记录。'));
    }
  }
  return add(el('div', 'shell'), sidebar(items, '系统范围', tree), main);
}
