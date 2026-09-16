/* History entries belong to this map, and contain the rendered reading state. */
(function (global) {
  'use strict';
  global.ProjectMapHistory = {
    create(key, capture, restore, changed) {
      const history = global.history;
      let current = null, restoring = false;
      const own = value => value?.projectMap?.key === key ? value.projectMap : null;
      function save() {
        if (!current || restoring) return;
        current.snapshot = capture();
        history.replaceState({ ...history.state, projectMap: current }, '', global.location.hash);
      }
      function commit(url) {
        const previous = current;
        if (!restoring && previous && previous.url !== url) {
          current = { key, index: previous.index + 1, url, snapshot: capture() };
          history.pushState({ projectMap: current }, '', url);
        } else {
          current = { key, index: previous?.index || 0, url, snapshot: capture() };
          history.replaceState({ ...history.state, projectMap: current }, '', url);
        }
        changed(current.index > 0);
      }
      function restoreCurrent() {
        current = own(history.state);
        restoring = true;
        try { restore(current?.snapshot || null); }
        finally { restoring = false; }
      }
      global.addEventListener('popstate', restoreCurrent);
      return {
        save, commit, restoreCurrent,
        back() { if (current?.index > 0) { save(); history.back(); } },
      };
    },
  };
})(globalThis);
