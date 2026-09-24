'use strict';
// athena rollback [--home <dir>]: restore every file the last install replaced, retired or created,
// and point ~/.athena/current back where it was.
const os = require('os');
const path = require('path');
const { flags } = require('./lib/common.cjs');
const { rollback } = require('./lib/install-apply.cjs');

function main(argv, io) {
  let f;
  try { f = flags(argv, { home: 'str' }).flags; } catch (error) { io.stderr.write(`athena rollback: ${error.message}\n`); return 2; }
  const home = path.resolve(f.home || os.homedir());
  try {
    const { record, problems, backup } = rollback(home);
    io.stdout.write(`rolled back athena ${record.version}: ${record.entries.length} file(s) restored; current → ${record.previous_current || '(none)'}\n` +
      `files you changed after the install (if any) are kept in ${path.join(backup, 'after-install')}\n`);
    for (const p of problems) io.stderr.write(`problem: ${p}\n`);
    return problems.length ? 1 : 0;
  } catch (error) {
    io.stderr.write(`athena rollback: ${error.message}\n`);
    return 1;
  }
}

module.exports = { main };
