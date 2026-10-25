// Watches notebooks/ and reruns build.js (incremental) when anything changes.
// Polls every second: works on mounted folders too, where fs.watch doesn't always fire.
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const SRC = path.resolve(__dirname, '../notebooks');
const BUILD = path.join(__dirname, 'build.js');

function signature() {
  const parts = [];
  for (const dir of fs.readdirSync(SRC)) {
    const full = path.join(SRC, dir);
    if (!fs.statSync(full).isDirectory()) continue;
    for (const f of fs.readdirSync(full)) {
      if (f.startsWith('.')) continue;
      const st = fs.statSync(path.join(full, f));
      parts.push(`${dir}/${f}:${st.size}:${st.mtimeMs}`);
      // one level down: assets/
      if (st.isDirectory()) {
        for (const g of fs.readdirSync(path.join(full, f))) {
          if (g.startsWith('.')) continue;
          const sub = fs.statSync(path.join(full, f, g));
          parts.push(`${dir}/${f}/${g}:${sub.size}:${sub.mtimeMs}`);
        }
      }
    }
  }
  return parts.sort().join('|');
}

let last = signature();
let running = false;
let pending = false;
let changedAt = 0;

function build() {
  running = true;
  const started = Date.now();
  const child = spawn(process.execPath, [BUILD], { stdio: ['ignore', 'ignore', 'pipe'] });
  child.stderr.on('data', (d) => process.stderr.write(d));
  child.on('exit', (code) => {
    running = false;
    console.log(`${new Date().toLocaleTimeString()} build ${code === 0 ? 'ok' : `failed (${code})`} in ${Date.now() - started} ms`);
    if (pending) { pending = false; build(); }
  });
}

setInterval(() => {
  let now;
  try { now = signature(); } catch { return; } // file still being copied
  if (now !== last) { last = now; changedAt = Date.now(); return; }
  // wait 1 s without changes (large copies) before building
  if (changedAt && Date.now() - changedAt > 1000) {
    changedAt = 0;
    if (running) pending = true;
    else build();
  }
}, 1000);

console.log('watching', SRC);
