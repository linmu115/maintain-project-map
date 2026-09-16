/* Select an embedded diagram before it can take pointer or wheel input.
 * Parent-page scrolling is the default. This layer never consumes wheel/touch
 * events and never reloads a frame; the native viewer owns the selected camera.
 */
(function (global) {
  'use strict';
  const doc = global.document;
  const entries = new Set();
  const mounted = new WeakMap();
  let active = null;

  function selected(entry, value) {
    entry.stage.classList.toggle('is-active', value);
    entry.stage.dataset.canvasActive = String(value);
    entry.frame.style.pointerEvents = value ? 'auto' : 'none';
    entry.frame.tabIndex = value ? 0 : -1;
    entry.hit.hidden = value;
    entry.hit.setAttribute('aria-pressed', String(value));
    entry.status.hidden = !value;
    entry.exit.hidden = !value;
  }

  function deactivateAll() {
    if (!active) return;
    const previous = active;
    active = null;
    selected(previous, false);
  }

  function activate(entry) {
    if (!entries.has(entry) || active === entry) return;
    deactivateAll();
    active = entry;
    selected(entry, true);
    entry.frame.focus({ preventScroll: true });
  }

  function outside(event) {
    if (active && !active.stage.contains(event.target)) deactivateAll();
  }
  doc.addEventListener('pointerdown', outside, true);
  doc.addEventListener('focusin', outside, true);
  doc.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape' || !active) return;
    const previous = active;
    deactivateAll();
    previous.hit.focus({ preventScroll: true });
    event.preventDefault();
  });

  function mount(frame, options) {
    if (mounted.has(frame)) return mounted.get(frame).stage;
    const label = (options && options.label) || frame.title || '图形';
    const stage = doc.createElement('div');
    stage.className = 'canvas-stage';
    stage.setAttribute('role', 'group');
    stage.setAttribute('aria-label', label);
    const hit = doc.createElement('button');
    hit.type = 'button';
    hit.className = 'canvas-hit-area';
    hit.setAttribute('aria-label', '选择' + label + '画布，启用缩放和拖动');
    const hitLabel = doc.createElement('span');
    hitLabel.className = 'canvas-hit-label';
    hitLabel.textContent = '点击操作图形';
    hit.appendChild(hitLabel);
    const status = doc.createElement('span');
    status.className = 'canvas-status';
    status.textContent = '画布已选中 · 点击外部返回文档';
    status.setAttribute('role', 'status');
    const exit = doc.createElement('button');
    exit.type = 'button';
    exit.className = 'canvas-exit';
    exit.textContent = '返回文档';
    exit.setAttribute('aria-label', '取消选择' + label + '画布，返回文档滚动');
    stage.appendChild(frame);
    stage.appendChild(hit);
    stage.appendChild(status);
    stage.appendChild(exit);
    const entry = { frame, stage, hit, status, exit };
    entries.add(entry);
    mounted.set(frame, entry);
    selected(entry, false);
    hit.addEventListener('click', function () { activate(entry); });
    exit.addEventListener('click', function () {
      if (!entries.has(entry)) return;
      deactivateAll();
      hit.focus({ preventScroll: true });
    });
    return stage;
  }

  function reset() {
    deactivateAll();
    for (const entry of entries) mounted.delete(entry.frame);
    entries.clear();
  }

  global.ProjectMapCanvas = Object.freeze({ mount, deactivateAll, reset, activate: frame => { const entry=mounted.get(frame); if(entry)activate(entry); } });
})(globalThis);
