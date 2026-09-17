/* Unit-only DOM/event double. No browser, network, app, or live-page access. */
'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const input = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const scenario = process.argv[2];

function close(actual, expected, message = '') {
  assert.ok(Math.abs(actual - expected) < 1e-7, `${message}: ${actual} != ${expected}`);
}
function comparable(state) {
  return { scale: state.scale, x: state.x, y: state.y, mode: state.mode };
}

function camera({ source = input.adapted, canvas = true, mobile = false, contentBounds = null } = {}) {
  const frames = new Map();
  const timers = new Map();
  const observers = [];
  let sequence = 0;
  const calls = { captures: [], scrolls: [], focusRepositions: 0 };

  class Style {
    constructor() { this.values = new Map(); this.transform = ''; }
    setProperty(key, value) { this.values.set(key, value); }
    getPropertyValue(key) { return this.values.get(key) || ''; }
    removeProperty(key) { this.values.delete(key); if (key === 'clip-path') delete this.clipPath; }
  }
  class Element {
    constructor(name, width = 0, height = 0, selectors = []) {
      this.name = name; this.clientWidth = width; this.clientHeight = height;
      this.offsetWidth = width; this.offsetHeight = height;
      this.offsetLeft = 0; this.offsetTop = 0;
      this.scrollLeft = 0; this.hidden = false;
      this.attributes = new Map(); this.listeners = new Map(); this.style = new Style();
      this.childNodes=[];
      this.selectors = new Set(selectors); this.children = new Map();
      const classes = new Set();
      this.classList = {
        add: (...names) => names.forEach(name => classes.add(name)),
        remove: (...names) => names.forEach(name => classes.delete(name)),
        contains: name => classes.has(name),
        toggle: (name, value) => {
          const wanted = value === undefined ? !classes.has(name) : Boolean(value);
          if (wanted) classes.add(name); else classes.delete(name);
          return wanted;
        },
      };
    }
    setAttribute(key, value) {
      this.attributes.set(key, String(value));
      if(key === 'viewBox' && this.viewBox){const [x,y,width,height]=String(value).split(' ').map(Number);Object.assign(this.viewBox.baseVal,{x,y,width,height});}
    }
    getAttribute(key) { return this.attributes.get(key) ?? null; }
    hasAttribute(key) { return this.attributes.has(key); }
    removeAttribute(key) { this.attributes.delete(key); }
    toggleAttribute(key, force) {
      const wanted = force === undefined ? !this.attributes.has(key) : Boolean(force);
      if (wanted) this.attributes.set(key, ''); else this.attributes.delete(key);
      return wanted;
    }
    addEventListener(type, listener, options) {
      if (!this.listeners.has(type)) this.listeners.set(type, []);
      this.listeners.get(type).push({ listener, options });
    }
    appendChild(child){this.childNodes.push(child);return child;}
    querySelector(selector) { return this.children.get(selector) || null; }
    querySelectorAll(selector) {
      if (this.name === 'svg' && selector === '[data-node-id]') return nodes;
      if (this.name === 'svg' && selector === '[data-edge-from][data-edge-to]') return [edge];
      return [];
    }
    closest(selectors) {
      return selectors.split(',').some(selector => this.selectors.has(selector.trim())) ? this : null;
    }
    getBoundingClientRect() {
      let left = 40, top = 32, width = this.clientWidth, height = this.clientHeight;
      if (this.name === 'svg') {
        const transform = transformOf(this);
        left += transform.x; top += transform.y;
        width *= transform.scale; height *= transform.scale;
      }
      return { left, top, width, height, right: left + width, bottom: top + height };
    }
    setPointerCapture(id) { calls.captures.push(id); }
    releasePointerCapture() {}
    scrollTo(options) { calls.scrolls.push(options); this.scrollLeft = options.left; }
  }
  function transformOf(element) {
    const match = element.style.transform.match(/translate\(([-\d.e+]+)px,([-\d.e+]+)px\) scale\(([-\d.e+]+)\)/);
    return match ? { x: +match[1], y: +match[2], scale: +match[3] } : { x: 0, y: 0, scale: 1 };
  }
  function getComputedStyle(element) {
    const { x, y, scale } = transformOf(element);
    return { transform: `matrix(${scale},0,0,${scale},${x},${y})`, display: element.hidden ? 'none' : 'block' };
  }
  const html = new Element('html');
  if (canvas) html.setAttribute('data-map-canvas', 'true');
  const container = new Element('container', 800, 460);
  container.setAttribute('data-wide-diagram', 'true');
  const svg = new Element('svg', 800, 400);
  svg.viewBox = { baseVal: { x: 0, y: 0, width: 1093, height: 528 } };
  if(contentBounds) svg.getBBox = () => contentBounds;
  const nav = new Element('nav', 380, 42, ['.diagram-nav']);
  const out = new Element('out'), reset = new Element('reset'), plus = new Element('in');
  const detail = new Element('detail'), percent = new Element('percent');
  const chip = new Element('chip', 0, 0, ['.focus-chip']); chip.hidden = true;
  const route = new Element('route', 0, 0, ['.route-probe']); route.hidden = true;
  reset.children.set('[data-view-detail]', detail);
  reset.children.set('[data-view-percent]', percent);
  container.children.set('svg', svg);
  container.children.set('.diagram-nav', nav);
  container.children.set('[data-view="out"]', out);
  container.children.set('[data-view="reset"]', reset);
  container.children.set('[data-view="in"]', plus);
  const node = new Element('node', 120, 70, ['[data-node-id]']);
  node.setAttribute('data-node-id', 'step-a');
  node.getBBox = () => ({ x: 120, y: 160, width: 180, height: 90 });
  const nodes = [node];
  const edge = new Element('edge', 0, 0, ['[data-relationship-hit-key]']);
  edge.setAttribute('data-edge-from', 'step-a'); edge.setAttribute('data-edge-to', 'step-b');
  const blank = new Element('blank');
  const window = new Element('window');
  window.innerWidth = mobile ? 480 : 1200;
  window.innerHeight = 600;
  window.matchMedia = () => ({ matches: true }); // Camera transitions settle immediately.
  const document = {
    createElementNS: (_,name) => new Element(name),
    documentElement: html, hidden: false,
    querySelector: selector => selector === '.diagram-container' ? container : null,
    getElementById: id => id === 'focus-chip' ? chip : id === 'route-probe' ? route : null,
  };
  class ResizeObserver {
    constructor(callback) { this.callback = callback; this.targets = []; observers.push(this); }
    observe(element) { this.targets.push(element); }
  }
  const Archify = {
    focus: { active: () => null, reposition: () => { calls.focusRepositions++; } },
  };
  const context = {
    document, window, Archify, getComputedStyle, ResizeObserver,
    viewerText: key => key,
    requestAnimationFrame: callback => { const id = ++sequence; frames.set(id, callback); return id; },
    cancelAnimationFrame: id => frames.delete(id),
    setTimeout: callback => { const id = ++sequence; timers.set(id, callback); return id; },
    clearTimeout: id => timers.delete(id),
  };
  vm.runInNewContext(source, context, { filename: 'actual-archify-camera.js', timeout: 2000 });
  function flush() {
    let budget = 50;
    while (frames.size) {
      assert.ok(budget-- > 0, 'animation-frame work must settle');
      const ready = [...frames.entries()]; frames.clear();
      ready.forEach(([id, callback]) => callback(id * 16));
    }
  }
  function dispatch(element, type, properties = {}) {
    const event = {
      type, target: blank, button: 0, pointerId: 1,
      clientX: 240, clientY: 182, deltaY: 0, deltaMode: 0,
      defaultPrevented: false, propagationStopped: false,
      preventDefault() { this.defaultPrevented = true; },
      stopPropagation() { this.propagationStopped = true; },
      ...properties,
    };
    (element.listeners.get(type) || []).forEach(({ listener }) => listener(event));
    flush();
    return event;
  }
  function drag(dx, dy, target = blank) {
    dispatch(container, 'pointerdown', { clientX: 160, clientY: 100, target });
    dispatch(container, 'pointermove', { clientX: 160 + dx, clientY: 100 + dy, target });
    dispatch(container, 'pointerup', { clientX: 160 + dx, clientY: 100 + dy, target });
  }
  flush();
  return { view: Archify.view, Archify, container, svg, nav, out, reset, plus, detail, percent,
    node, edge, blank, window, observers, calls, dispatch, drag, flush };
}

const cases = {
  bounds() {
    // Outlying edge/label, including negative coordinates: full content must
    // remain reachable after fit, zoom, pan, reset and viewport resize.
    const h=camera({contentBounds:{x:-30,y:0,width:1200,height:560}});
    assert.deepEqual(h.svg.viewBox.baseVal,{x:-42,y:-12,width:1224,height:584});
    h.view.zoomIn();h.drag(180,-90);
    assert.equal(h.svg.style.clipPath,undefined);
    assert.equal(h.svg.style.transform,'');
    const plane=h.svg.childNodes.find(n=>n.getAttribute('data-map-content'));
    assert.ok(plane.getAttribute('transform').startsWith('matrix(1.25 '));
    h.view.reset();close(h.view.logicalViewport().width,1224);
    h.observers[0].callback();h.flush();
    assert.deepEqual(h.svg.viewBox.baseVal,{x:-42,y:-12,width:1224,height:584},'Resize must not grow the source bounds repeatedly');
    const native=camera({canvas:false,contentBounds:{x:0,y:0,width:1200,height:560}});
    close(native.svg.viewBox.baseVal.width,1093);
    native.view.zoomIn();assert.ok(native.svg.style.clipPath,'Noncanvas reader keeps native clipping');
  },
  fit() {
    const h = camera();
    assert.deepEqual(comparable(h.view.state()), { scale: 1, x: 0, y: 0, mode: 'overview' });
    assert.equal(h.svg.getAttribute('preserveAspectRatio'), 'xMidYMid meet');
    assert.ok(h.container.classList.contains('is-pannable'));
    assert.equal(h.out.disabled, false);
    assert.equal(h.percent.textContent, '100%');
    close(h.view.logicalViewport().width, 1093);
    close(h.view.logicalViewport().height, 528);
  },
  wheel() {
    const h = camera();
    const event = h.dispatch(h.container, 'wheel', { deltaY: 61, clientX: 273, clientY: 201 });
    const state = h.view.state();
    close(state.scale, Math.exp(-61 * 0.0018));
    assert.ok(state.scale < 1 && state.scale > 0.75);
    assert.notEqual(state.scale * 4, Math.round(state.scale * 4));
    assert.equal(event.defaultPrevented, true);
    assert.equal(event.propagationStopped, true);
    assert.equal(h.container.listeners.get('wheel')[0].options.passive, false);
    close((273 - 40 - state.x) / state.scale, 273 - 40, 'pointer content x');
    close((201 - 32 - state.y) / state.scale, 201 - 32, 'pointer content y');
    // Root window is fixed; inner matrix must equal screen-space camera math,
    // including the letterboxing from preserveAspectRatio="meet".
    const plane=h.svg.childNodes.find(n=>n.getAttribute('data-map-content'));
    const m=plane.getAttribute('transform').slice(7,-1).split(' ').map(Number);
    const base=Math.min(800/1093,400/528),offsetY=(400-528*base)/2;
    close(base*(m[0]*420+m[4]),state.scale*base*420+state.x,'content x mapping');
    close(base*(m[3]*250+m[5])+offsetY,state.scale*(base*250+offsetY)+state.y,'content y mapping');
    assert.equal(h.svg.style.transform,'','Viewport must not move with content');
    h.drag(37, -22);
    const before = h.view.state();
    const oldX = (420 - 40 - before.x) / before.scale;
    const oldY = (300 - 32 - before.y) / before.scale;
    h.dispatch(h.container, 'wheel', { deltaY: -117, clientX: 420, clientY: 300 });
    const after = h.view.state();
    close((420 - 40 - after.x) / after.scale, oldX, 'anchored after pan x');
    close((300 - 32 - after.y) / after.scale, oldY, 'anchored after pan y');
    const line = camera(), pixels = camera();
    line.dispatch(line.container, 'wheel', { deltaY: 2, deltaMode: 1 });
    pixels.dispatch(pixels.container, 'wheel', { deltaY: 32, deltaMode: 0 });
    close(line.view.state().scale, pixels.view.state().scale, 'line wheel units');
  },
  controls() {
    const h = camera();
    for (const selector of ['.diagram-nav', '.focus-chip', '.node-finder', '.diagram-guide', '.overview-map', '.route-probe', '.semantic-lens']) {
      const target = { closest: list => list.split(',').map(s => s.trim()).includes(selector) ? target : null };
      const event = h.dispatch(h.container, 'wheel', { target, deltaY: 100 });
      assert.equal(event.defaultPrevented, false, selector);
      assert.equal(event.propagationStopped, false, selector);
      close(h.view.state().scale, 1);
    }
  },
  drag() {
    const h = camera();
    h.drag(125, -45);
    assert.deepEqual(comparable(h.view.state()), { scale: 1, x: 125, y: -45, mode: 'manual' });
    assert.equal(h.container.getAttribute('data-just-panned'), 'true');
    h.dispatch(h.container, 'wheel', { deltaY: 240 });
    const before = h.view.state();
    assert.ok(before.scale < 1);
    h.drag(-73, 84);
    const after = h.view.state();
    close(after.x - before.x, -73); close(after.y - before.y, 84);
    for (const target of [h.node, h.edge, h.nav]) {
      const state = comparable(h.view.state()), captures = h.calls.captures.length;
      h.drag(40, 20, target);
      assert.deepEqual(comparable(h.view.state()), state, target.name);
      assert.equal(h.calls.captures.length, captures, target.name);
    }
  },
  limits() {
    const h = camera();
    for (let i = 0; i < 20; i++) h.dispatch(h.container, 'wheel', { deltaY: 600 });
    close(h.view.state().scale, 0.05); assert.equal(h.out.disabled, true);
    for (let i = 0; i < 20; i++) h.dispatch(h.container, 'wheel', { deltaY: -600 });
    close(h.view.state().scale, 8); assert.equal(h.plus.disabled, true);
    h.dispatch(h.reset, 'click');
    assert.deepEqual(comparable(h.view.state()), { scale: 1, x: 0, y: 0, mode: 'overview' });
    h.dispatch(h.out, 'click'); close(h.view.state().scale, 0.75);
    h.view.zoomIn(); close(h.view.state().scale, 1);
    h.view.reset(); assert.equal(h.view.state().mode, 'overview');
  },
  resize() {
    const h = camera();
    assert.equal(h.observers.length, 1);
    assert.deepEqual(h.observers[0].targets, [h.container, h.svg, h.nav]);
    assert.equal(h.container.style.getPropertyValue('--map-canvas-nav-height'), '54px');
    h.svg.clientWidth = 640; h.svg.clientHeight = 280;
    h.nav.clientHeight = 84;
    h.observers[0].callback(); h.flush();
    assert.deepEqual(comparable(h.view.state()), { scale: 1, x: 0, y: 0, mode: 'overview' });
    assert.equal(h.container.style.getPropertyValue('--map-canvas-nav-height'), '96px');
    h.dispatch(h.container, 'wheel', { deltaY: 90 }); h.drag(37, -17);
    const before = comparable(h.view.state());
    h.svg.clientWidth = 720; h.svg.clientHeight = 360;
    h.observers[0].callback(); h.flush();
    assert.deepEqual(comparable(h.view.state()), before);
  },
  mobile() {
    const h = camera({ mobile: true });
    h.view.centerAt(700, 280, { scale: 0.7, instant: true });
    close(h.view.state().scale, 0.7);
    assert.equal(h.calls.scrolls.length, 0);
    h.view.reset();
    h.view.reveal(['step-a'], { instant: true });
    assert.equal(h.view.state().mode, 'semantic');
    assert.ok(h.view.state().scale > 1);
    assert.equal(h.calls.scrolls.length, 0);
    h.Archify.focus.active = () => 'step-a';
    h.svg.clientWidth = 620;
    h.observers[0].callback(); h.flush();
    assert.equal(h.view.state().mode, 'semantic');
    assert.equal(h.calls.scrolls.length, 0);
  },
  native() {
    function transcript(source, mobile) {
      const h = camera({ source, canvas: false, mobile });
      const result = [comparable(h.view.state())];
      const wheel = h.dispatch(h.container, 'wheel', { deltaY: 100 });
      assert.equal(wheel.defaultPrevented, false);
      assert.equal(h.observers.length, 0);
      h.drag(60, 10); result.push(comparable(h.view.state()));
      h.view.zoomOut(); result.push(comparable(h.view.state()));
      h.view.zoomIn(); h.drag(-80, -20); result.push(comparable(h.view.state()));
      for (let i = 0; i < 20; i++) h.view.zoomIn();
      close(h.view.state().scale, 3);
      result.push(comparable(h.view.state()));
      h.view.reset(); h.view.reveal(['step-a'], { instant: true });
      result.push(comparable(h.view.state()), h.calls.scrolls.map(value => ({ ...value })));
      return result;
    }
    for (const mobile of [false, true]) {
      assert.deepEqual(transcript(input.adapted, mobile), transcript(input.native, mobile));
    }
  },
};

assert.ok(cases[scenario], `Unknown camera test: ${scenario}`);
cases[scenario]();
process.stdout.write(JSON.stringify({ scenario, passed: true }));
