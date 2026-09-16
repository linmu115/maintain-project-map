'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

class Element {
  constructor(tag, doc) {
    this.tagName = tag.toUpperCase(); this.ownerDocument = doc;
    this.children = []; this.parentNode = null; this.listeners = new Map();
    this.style = {}; this.dataset = {}; this.attributes = {}; this.hidden = false;
    this.classList = { toggle: (name, enabled) => {
      const classes = new Set((this.className || '').split(' ').filter(Boolean));
      if (enabled) classes.add(name); else classes.delete(name);
      this.className = [...classes].join(' ');
    }};
  }
  appendChild(child) {
    if (child.parentNode) {
      const old = child.parentNode.children;
      old.splice(old.indexOf(child), 1);
    }
    this.children.push(child); child.parentNode = this; return child;
  }
  contains(target) { return target === this || this.children.some(c => c.contains(target)); }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }
  dispatch(type, values = {}) {
    const event = { target: this, defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; }, ...values };
    for (const listener of this.listeners.get(type) || []) listener(event);
    return event;
  }
  focus() {
    this.ownerDocument.activeElement = this;
    this.ownerDocument.dispatch('focusin', { target: this });
  }
}
const doc = new Element('document', null);
doc.ownerDocument = doc; doc.createElement = tag => new Element(tag, doc);
const context = { document: doc };
vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), context);
const gate = context.ProjectMapCanvas;
function fixture(name) {
  const frame = doc.createElement('iframe');
  frame.src = name + '.html#focus=node'; frame.title = name;
  const stage = gate.mount(frame, { label: name }); doc.appendChild(stage);
  const [sameFrame, hit, status, exit] = stage.children;
  assert.equal(sameFrame, frame);
  return { frame, stage, hit, status, exit };
}
function enabled(item, value) {
  assert.equal(item.stage.dataset.canvasActive, String(value));
  assert.equal(item.frame.style.pointerEvents, value ? 'auto' : 'none');
  assert.equal(item.frame.tabIndex, value ? 0 : -1);
  assert.equal(item.hit.hidden, value);
  assert.equal(item.status.hidden, !value); assert.equal(item.exit.hidden, !value);
}
const scenario = process.argv[3];
const item = fixture('流程图');
const originalSrc = item.frame.src;
if (scenario === 'default') {
  enabled(item, false);
  assert.equal(item.hit.tagName, 'BUTTON'); assert.equal(item.hit.type, 'button');
  for (const element of [doc, item.stage, item.hit, item.frame]) {
    assert.equal(element.listeners.has('wheel'), false);
    assert.equal(element.listeners.has('touchmove'), false);
    assert.equal(element.dispatch('wheel').defaultPrevented, false);
  }
} else if (scenario === 'select') {
  let forwarded = 0;
  item.frame.addEventListener('click', () => forwarded++);
  item.hit.dispatch('click'); enabled(item, true);
  assert.equal(doc.activeElement, item.frame);
  assert.equal(item.frame.src, originalSrc); assert.equal(forwarded, 0);
  doc.dispatch('pointerdown', { target: item.frame }); enabled(item, true);
} else if (scenario === 'outside') {
  const outside = doc.createElement('button'); doc.appendChild(outside);
  item.hit.dispatch('click');
  doc.dispatch('pointerdown', { target: outside }); enabled(item, false);
  item.hit.dispatch('click'); outside.focus(); enabled(item, false);
  assert.equal(item.frame.src, originalSrc);
} else if (scenario === 'multiple') {
  const other = fixture('架构图');
  item.hit.dispatch('click'); enabled(item, true); enabled(other, false);
  doc.dispatch('pointerdown', { target: other.hit }); enabled(item, false);
  other.hit.dispatch('click'); enabled(other, true); enabled(item, false);
  item.hit.dispatch('click'); enabled(item, true); enabled(other, false);
  gate.deactivateAll(); enabled(item, false); enabled(other, false);
} else if (scenario === 'exit') {
  item.hit.dispatch('click'); item.exit.dispatch('click'); enabled(item, false);
  assert.equal(doc.activeElement, item.hit);
  item.hit.dispatch('click');
  const escape = doc.dispatch('keydown', { key: 'Escape' });
  enabled(item, false); assert.equal(escape.defaultPrevented, true);
  assert.equal(doc.activeElement, item.hit);
  assert.equal(doc.dispatch('keydown', { key: 'Escape' }).defaultPrevented, false);
} else if (scenario === 'reset') {
  assert.equal(gate.mount(item.frame), item.stage);
  item.hit.dispatch('click'); gate.reset(); enabled(item, false);
  item.hit.dispatch('click'); enabled(item, false);
  const other = fixture('新流程图'); other.hit.dispatch('click'); enabled(other, true);
  for (const type of ['pointerdown', 'focusin', 'keydown'])
    assert.equal(doc.listeners.get(type).length, 1);
  gate.reset(); enabled(other, false); assert.equal(item.frame.src, originalSrc);
} else { throw new Error('Unknown scenario ' + scenario); }
console.log(JSON.stringify({ scenario, passed: true }));
