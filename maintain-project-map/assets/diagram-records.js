/* Project links extend the native passport; Archify remains the camera owner. */
(function () {
  'use strict';
  const config = JSON.parse(document.getElementById('project-map-diagram-data').textContent);
  const svg = document.querySelector('.diagram-container > svg');
  const chip = document.getElementById('focus-chip');
  if (!svg || !chip || !globalThis.Archify?.focus || !Archify.view) return;
  const nodes = new Map([...svg.querySelectorAll('[data-node-id]')].map(n => [n.dataset.nodeId, n]));
  const group = document.createElement('div');
  group.className = 'map-record-links';
  group.setAttribute('aria-label', '对应项目条目');
  document.getElementById('focus-passport-meta').after(group);
  const embedded = window.parent !== window;
  let previousFocus = null, scheduled = 0, lastSnapshot = '';
  function snapshot() {
    return { focus: Archify.focus.active(), passport: !chip.hidden, camera: Archify.view.state(),
      relation: Archify.focus.relationship()?.id || null };
  }
  function send(type, values = {}) {
    if (embedded) parent.postMessage({ channel: 'project-map/v1', type, ...values }, '*');
  }
  function passport() {
    const focused = Archify.focus.active();
    const id = typeof focused === 'string' ? focused : '';
    if (id === previousFocus) return;
    previousFocus = id;
    group.replaceChildren();
    const mappings = Object.hasOwn(config.nodes, id) ? config.nodes[id] : [];
    group.hidden = !mappings.length;
    if (!mappings.length) return;
    const label = document.createElement('a');
    label.className = 'map-node-label';
    label.textContent = nodes.get(id)?.dataset.nodeLabel || id;
    label.href = '#focus=' + encodeURIComponent(id);
    label.addEventListener('click', event => { event.preventDefault(); center(id); });
    group.append(label);
    for (const record of mappings) {
      const link = document.createElement('a');
      link.className = 'map-record-button';
      const status = {retired:'已退役',merged:'已合并',superseded:'已替代',withdrawn:'已撤回'}[record.status];
      link.textContent = record.title + (status ? ' · ' + status : '');
      link.href = config.reader + '#' + new URLSearchParams({ mode: 'b', record: record.id });
      link.dataset.recordId = record.id;
      if (embedded) link.addEventListener('click', event => {
        if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        send('navigate-record', { node: id, record: record.id, snapshot: snapshot() });
      });
      group.append(link);
    }
    Archify.focus.reposition();
  }
  function center(id) {
    const node = nodes.get(id);
    if (!node) return false;
    Archify.focus.set(id, { toggle: false, updateUrl: false, hideChip: true });
    const box = node.getBBox(), viewBox = svg.viewBox.baseVal;
    const fit = Math.min(svg.clientWidth / viewBox.width, svg.clientHeight / viewBox.height);
    // Center the card itself; do not offset the target to make room for a passport.
    const scale = Math.min(4, Math.max(0.05,
      Math.min(svg.clientWidth * 0.42 / (box.width * fit), svg.clientHeight * 0.42 / (box.height * fit))));
    Archify.view.centerAt(box.x + box.width / 2, box.y + box.height / 2, { scale, minimumScale: 0.05, instant: true });
    svg.dataset.mapCenteredNode = id;
    return true;
  }
  function restore(value) {
    if (!value || typeof value !== 'object') return;
    if (typeof value.focus === 'string' && nodes.has(value.focus)) Archify.focus.set(value.focus, { toggle: false, updateUrl: false, hideChip: value.passport === false });
    else if (Array.isArray(value.focus)) Archify.focus.setMany(value.focus.filter(id => nodes.has(id)), { toggle: false, updateUrl: false });
    else Archify.focus.clear({ updateUrl: false, preserveView: true });
    if (value.relation) Archify.focus.inspectRelationshipById(value.relation, { updateUrl: false, toggle: false });
    Archify.view.restore(value.camera);
    passport();
  }
  function schedule() {
    if (scheduled) return;
    scheduled = requestAnimationFrame(() => {
      scheduled = 0;
      passport();
      const value = snapshot(), encoded = JSON.stringify(value);
      if (encoded !== lastSnapshot) { lastSnapshot = encoded; send('snapshot', { snapshot: value }); }
    });
  }
  new MutationObserver(schedule).observe(svg, { attributes: true, attributeFilter: ['data-view-scale', 'data-focus-active'] });
  const content = svg.querySelector('[data-map-content]');
  if (content) new MutationObserver(schedule).observe(content, { attributes: true, attributeFilter: ['transform'] });
  window.addEventListener('message', event => {
    if (!embedded || event.source !== parent || event.data?.channel !== 'project-map/v1') return;
    if (event.data.type === 'focus-node') center(event.data.node);
    if (event.data.type === 'restore') restore(event.data.snapshot);
  });
  passport();
  send('ready');
  schedule();
})();
