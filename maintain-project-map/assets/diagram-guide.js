/* Disclosure only: native Archify continues to own chapters and playback. */
(() => {
  if (document.documentElement.dataset.mapCanvas !== 'true') return;
  const panel = document.getElementById('guided-views');
  if (!panel || document.documentElement.dataset.embed === 'true') return;
  const disclosure = document.createElement('details');
  disclosure.className = 'map-guide';
  const summary = document.createElement('summary');
  summary.textContent = '阅读引导 · 章节与路径';
  panel.before(disclosure);
  disclosure.append(summary, panel);
  const sync = () => { disclosure.hidden = panel.hidden; };
  sync();
  if (/(?:^#|&)(?:view|beat|play)=/.test(location.hash)) disclosure.open = true;
  new MutationObserver(changes => {
    sync();
    if (changes.some(change => change.attributeName === 'data-active-view') && panel.dataset.activeView !== 'all') disclosure.open = true;
  }).observe(panel, {attributes:true, attributeFilter:['hidden','data-active-view']});
})();
