const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), assert = require('node:assert/strict');
const code = fs.readFileSync(path.resolve(__dirname, '../maintain-project-map/assets/diagram-records.js'), 'utf8');
function run(project, blocked = false) {
  let group, opened, prevented = false;
  class Element {
    constructor() { this.children = []; this.listeners = {}; this.dataset = {}; }
    setAttribute(k, v) { this[k] = v; }
    append(...items) { this.children.push(...items); }
    replaceChildren() { this.children = []; }
    addEventListener(k, fn) { this.listeners[k] = fn; }
  }
  const node = new Element(); node.dataset = {nodeId: 'core', nodeLabel: 'Core'};
  const svg = {querySelectorAll: () => [node], querySelector: () => null};
  const chip = {hidden: false}, camera = {scale: .42, x: 73, y: -15};
  const config = {nodes: {}, projects: {core: project}, reader: 'index.html'};
  const context = {Object, Map, URLSearchParams, location: {protocol: 'http:'}, requestAnimationFrame: () => 1,
    MutationObserver: class {observe() {}},
    document: {querySelector: () => svg, createElement: () => new Element(), getElementById: id =>
      id === 'project-map-diagram-data' ? {textContent: JSON.stringify(config)} : id === 'focus-chip' ? chip : {after: g => group = g}},
    Archify: {focus: {active: () => 'core', relationship: () => null, reposition() {}}, view: {state: () => camera}},
    addEventListener() {}, open: (url, target) => {opened = {url, target, opener: 'source'};return blocked ? null : opened;}};
  context.window = context; context.parent = context;
  vm.runInNewContext(code, context);
  const link = group.children.find(e => e.className === 'map-record-button map-enter-project');
  if (link) link.listeners.click({button: 0, preventDefault: () => prevented = true});
  assert.equal(camera.scale, .42); assert.equal(camera.x, 73); assert.equal(chip.hidden, false);
  return {group, link, opened, prevented};
}
const project = {project_id: 'p-core', name: 'Core', role: 'Shared contract', open_status: 'ready', href: '__project?project=p-core&diagram=architecture'};
let result = run(project);
assert.equal(result.link.target, '_blank'); assert.equal(result.opened.url, project.href); assert.equal(result.opened.opener, null); assert.ok(result.prevented);
result = run(project, true);
assert.ok(result.group.children.some(e => e.textContent?.includes('浏览器未返回新标签页')));
result = run({project_id: 'p-core', name: 'Core', status: 'ambiguous', reason: '选择明确工作树'});
assert.equal(result.link, undefined); assert.ok(result.group.children.some(e => e.textContent === '选择明确工作树'));
console.log('Passport project entry: success, blocked feedback, unavailable target, source camera preserved');
