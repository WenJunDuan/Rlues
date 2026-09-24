'use strict';
// Init-only bridge: reuse the CC lock, and the same Python field merge as CX.
const fs = require('fs');
const path = require('path');
const {spawnSync} = require('child_process');
const [modulePath, index, python, script] = process.argv.slice(2);
const writer = require(modulePath);
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
if (!writer.acquire(index)) {
  process.stderr.write('shared index lock unavailable; initialization did not commit\n');
  process.exitCode = 2;
} else {
  try {
    request.latest = fs.existsSync(index) ? fs.readFileSync(index, 'utf8') : null;
    const merged = spawnSync(python, [script, '_merge_locked'], {
      input: JSON.stringify(request), encoding: 'utf8', timeout: 5000,
    });
    if (merged.error || merged.status !== 0) {
      process.stderr.write(merged.stderr || 'locked field merge failed; current index preserved\n');
      process.exitCode = 2;
    } else {
      writer.writeAtomic(index, JSON.parse(merged.stdout).content);
      const cache = path.join(path.dirname(index), '.runtime', 'platform-capabilities.json');
      fs.mkdirSync(path.dirname(cache), {recursive: true});
      writer.writeAtomic(cache, JSON.stringify(request.capabilities, null, 2) + '\n');
    }
  } finally {
    writer.release(index);
  }
}
