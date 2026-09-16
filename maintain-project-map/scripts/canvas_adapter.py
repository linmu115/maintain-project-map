"""Version-checked downstream extensions to the native Archify camera.

Only the generated reading copy changes. There is still one Archify.view state,
so focus, route navigation and camera controls operate on the same viewport.
"""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _replace(source, before, after, count=1):
    actual = source.count(before)
    if actual != count:
        raise ValueError(f"Archify canvas adaptation anchor mismatch ({actual} != {count}): {before[:75]}")
    return source.replace(before, after)


def adapt_canvas(page: str) -> str:
    start = page.index("    Archify.view = (function () {")
    end = page.index("    /* ============================================================\n       Semantic Radar", start)
    camera = page[start:end]
    camera = _replace(camera, "      var viewBox = svg.viewBox && svg.viewBox.baseVal;", """      var canvasMode = document.documentElement.getAttribute('data-map-canvas') === 'true';
      var minimumZoom = canvasMode ? 0.05 : 1;
      var maximumZoom = canvasMode ? 8 : 3;
      var viewBox = svg.viewBox && svg.viewBox.baseVal;
      var canvasContent = null;
      if (canvasMode) {
        svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        // Native bounds may omit explicit edge waypoints and their labels.
        // Measure once before camera setup; never refit from a transformed box.
        if (viewBox && typeof svg.getBBox === 'function') {
          var content = svg.getBBox();
          if ([content.x, content.y, content.width, content.height].every(Number.isFinite) && content.width > 0 && content.height > 0) {
            var pad = 12;
            var left = Math.min(viewBox.x, content.x - pad);
            var top = Math.min(viewBox.y, content.y - pad);
            var right = Math.max(viewBox.x + viewBox.width, content.x + content.width + pad);
            var bottom = Math.max(viewBox.y + viewBox.height, content.y + content.height + pad);
            svg.setAttribute('data-map-original-viewbox', svg.getAttribute('viewBox'));
            svg.setAttribute('viewBox', [left, top, right - left, bottom - top].join(' '));
          }
        }
        canvasContent = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        canvasContent.setAttribute('data-map-content', 'true');
        Array.prototype.slice.call(svg.childNodes).forEach(function (child) {
          if (child.nodeType === 1 && ['defs', 'title', 'desc'].indexOf(child.localName) < 0) canvasContent.appendChild(child);
        });
        svg.appendChild(canvasContent);
      }""")
    camera = _replace(camera, "        svg.style.transform = 'translate(' + state.x + 'px,' + state.y + 'px) scale(' + state.scale + ')';", """        if (canvasMode) {
          // SVG is a stationary window. Move only its internal content plane.
          var metrics = contentMetrics();
          var tx = state.x / metrics.scale + (state.scale - 1) * (metrics.offsetX / metrics.scale - viewBox.x);
          var ty = state.y / metrics.scale + (state.scale - 1) * (metrics.offsetY / metrics.scale - viewBox.y);
          canvasContent.setAttribute('transform', 'matrix(' + [state.scale, 0, 0, state.scale, tx, ty].join(' ') + ')');
          svg.style.removeProperty('transform');
        } else {
          svg.style.transform = 'translate(' + state.x + 'px,' + state.y + 'px) scale(' + state.scale + ')';
        }""")
    camera = _replace(camera, "      function sampleRenderedState() {", """      function sampleRenderedState() {
        if (canvasMode) return { scale: state.scale, x: state.x, y: state.y, mode: state.mode };""")
    camera = _replace(camera, "x: contentOffsetX + minX * contentScale,", "x: contentOffsetX + (minX - (canvasMode ? viewBox.x : 0)) * contentScale,")
    camera = _replace(camera, "y: contentOffsetY + minY * contentScale,", "y: contentOffsetY + (minY - (canvasMode ? viewBox.y : 0)) * contentScale,")
    camera = _replace(camera, "      function clipToViewport(camera) {", """      function clipToViewport(camera) {
        // The embedded stage owns clipping. A second clip on the transformed
        // SVG can discard geometry before the user pans it into the stage.
        if (canvasMode) { svg.style.removeProperty('clip-path'); return; }""")
    camera = _replace(camera, "      function clamp() {", """      function clamp() {
        // Canvas panning is free at every scale; Reset returns to the fitted SVG.
        if (canvasMode) return;""")
    camera = _replace(camera, "        outBtn.disabled = state.scale <= 1;", "        outBtn.disabled = state.scale <= minimumZoom;")
    camera = _replace(camera, "        inBtn.disabled = state.scale >= 3;", "        inBtn.disabled = state.scale >= maximumZoom;")
    camera = _replace(camera, "container.classList.toggle('is-pannable', state.scale > 1);", "container.classList.toggle('is-pannable', canvasMode || state.scale > 1);")
    camera = _replace(camera, "        next = Math.max(1, Math.min(3, Math.round(next * 4) / 4));", """        next = canvasMode ? Math.max(minimumZoom, Math.min(maximumZoom, next))
          : Math.max(1, Math.min(3, Math.round(next * 4) / 4));""")
    camera = _replace(camera, "        var centerY = (svg.clientHeight || 1) / 2;", """        var centerY = (svg.clientHeight || 1) / 2;
        if (canvasMode && Number.isFinite(options.clientX) && Number.isFinite(options.clientY)) {
          var rect = svg.getBoundingClientRect();
          centerX = options.clientX - rect.left;
          centerY = options.clientY - rect.top;
        }""")
    camera = _replace(camera, "        if (state.scale <= 1 || event.button !== 0", "        if ((!canvasMode && state.scale <= 1) || event.button !== 0")
    camera = _replace(camera, "window.innerWidth <= 720 && container.hasAttribute('data-wide-diagram')", "!canvasMode && window.innerWidth <= 720 && container.hasAttribute('data-wide-diagram')", count=3)
    camera = _replace(camera, "        if (window.innerWidth > 720) return frameDesktop(ids, options);", "        if (canvasMode || window.innerWidth > 720) return frameDesktop(ids, options);")
    camera = _replace(camera, "Math.max(1, Math.min(3, Number(options.minimumScale) || 1))", "Math.max(minimumZoom, Math.min(maximumZoom, Number(options.minimumScale) || minimumZoom))")
    camera = _replace(camera, "Math.max(minimumScale, Math.min(3, Number.isFinite(requestedScale)", "Math.max(minimumScale, Math.min(maximumZoom, Number.isFinite(requestedScale)")
    camera = _replace(camera, "        container.setAttribute('data-camera-indicator', semantic ? 'true' : 'false');", """        container.setAttribute('data-camera-indicator', semantic ? 'true' : 'false');
        if (canvasMode) {
          if (resetDetailLabel) { resetDetailLabel.textContent = '适应全图'; resetDetailLabel.hidden = false; }
          resetBtn.toggleAttribute('data-detail-visible', true);
          resetBtn.title = '适应全图（0）：滚轮缩放，空白处按住左键拖动';
          resetBtn.setAttribute('aria-label', '适应全图');
        }""")
    camera = _replace(camera, "      container.addEventListener('pointerup', onPointerEnd);", """      if (canvasMode) {
        container.addEventListener('wheel', function (event) {
          if (event.target.closest('.diagram-nav, .focus-chip, .node-finder, .diagram-guide, .overview-map, .route-probe, .semantic-lens')) return;
          event.preventDefault();
          event.stopPropagation();
          var units = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? (svg.clientHeight || 500) : 1;
          var delta = Math.max(-600, Math.min(600, event.deltaY * units));
          if (!delta) return;
          zoom(state.scale * Math.exp(-delta * 0.0018), { clientX: event.clientX, clientY: event.clientY });
        }, { passive: false });
        var canvasResizeFrame = 0;
        function resizeCanvas() {
          if (canvasResizeFrame) return;
          canvasResizeFrame = requestAnimationFrame(function () {
            canvasResizeFrame = 0;
            var nav = container.querySelector('.diagram-nav');
            var reserve = nav ? Math.ceil(nav.getBoundingClientRect().height) + 12 : 0;
            var value = reserve + 'px';
            if (container.style.getPropertyValue('--map-canvas-nav-height') !== value) {
              container.style.setProperty('--map-canvas-nav-height', value);
            }
            if (state.mode === 'overview') reset({ automatic: true });
            else if (state.mode === 'semantic') syncSemantic();
            else apply();
          });
        }
        if (typeof ResizeObserver === 'function') {
          var canvasObserver = new ResizeObserver(resizeCanvas);
          [container, svg, container.querySelector('.diagram-nav')].filter(Boolean).forEach(function (element) { canvasObserver.observe(element); });
        }
        window.addEventListener('load', resizeCanvas, { once: true });
        window.addEventListener('resize', resizeCanvas, { passive: true });
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(resizeCanvas).catch(function () {});
        resizeCanvas();
      }
      container.addEventListener('pointerup', onPointerEnd);""")
    page = page[:start] + camera + page[end:]
    # Full-graph exports must not retain the interactive content transform.
    page = _replace(page, "        clone.style.removeProperty('clip-path');", """        clone.style.removeProperty('clip-path');
        var contentPlane = clone.querySelector('[data-map-content]');
        if (contentPlane) contentPlane.removeAttribute('transform');""")
    page = _replace(page, "          var rootMatrix = root.getCTM ? root.getCTM() : null;", """          var geometryRoot = root.querySelector('[data-map-content]') || root;
          var rootMatrix = geometryRoot.getCTM ? geometryRoot.getCTM() : null;""")
    # Native document/mobile layout budgets do not own this dedicated viewport.
    page = _replace(page, "          shell && diagram && svg && ratio >= WIDE_RATIO &&", "          html.getAttribute('data-map-canvas') !== 'true' && shell && diagram && svg && ratio >= WIDE_RATIO &&")
    page = _replace(page, "          container && svg && nav &&", "          html.getAttribute('data-map-canvas') !== 'true' && container && svg && nav &&")
    page = _replace(page, "var mobileWide = window.innerWidth <= 720 && container.hasAttribute('data-wide-diagram');", "var mobileWide = document.documentElement.getAttribute('data-map-canvas') !== 'true' && window.innerWidth <= 720 && container.hasAttribute('data-wide-diagram');")
    bootstrap = """<script id="project-map-canvas-mode">
if (new URLSearchParams(window.location.search).get('canvas') === '1') {
  document.documentElement.setAttribute('data-map-canvas', 'true');
}
</script>"""
    css = (ASSETS / "canvas.css").read_text(encoding="utf-8")
    guide = (ASSETS / "diagram-guide.js").read_text(encoding="utf-8")
    page = page.replace("</body>", '<script id="project-map-guide-disclosure">\n' + guide + '\n</script>\n</body>', 1)
    return page.replace("</head>", bootstrap + '\n<style id="project-map-canvas-style">\n' + css + "\n</style>\n</head>", 1)
