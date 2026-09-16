// Scoped to the Archify delivery process: keep its nested CLI/Git children hidden
// on Windows without modifying the pinned upstream files.
if (process.platform === 'win32') {
  const childProcess = require('node:child_process');
  for (const name of ['spawn', 'spawnSync']) {
    const original = childProcess[name];
    childProcess[name] = function (command, args, options) {
      if (!Array.isArray(args)) { options = args; args = []; }
      return original.call(this, command, args, { ...options, windowsHide: true });
    };
  }
  require('node:module').syncBuiltinESMExports();
}
