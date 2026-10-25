// Creates notebooks/<notebook>/info.json (back cover details) when it is missing.
// Fills in what the files tell; URL, exact date and venue are left empty.
// wallpaper: mural behind the shelf; pattern: tiles across the wall ("" = aged paper).
const fs = require('fs');
const path = require('path');
const SRC = path.resolve(__dirname, '../notebooks');
const { order, isCover, isBack, isWallpaper, isPattern } = require('./order.js');

const plain = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
function talkName(file, title) {
  const brand = plain(title.split(/[\s,]+/)[0]);
  const parts = file
    .replace(/\.[a-z0-9]+$/i, '')
    .replace(/^\d+\s*-\s*/, '')
    .replace(/[._]+/g, ' ')
    .split(/\s+-\s+/)
    .map((p) => p.replace(/^\d+\s+(?=[A-ZÁÉÍÓÚ])/, '').trim())
    .filter((p, i, all) => !(all.length > 1 && i === 0 && (plain(p).includes(brand) || /^[A-Z]{2,}\d*$/.test(p))))
    .filter((p) => /[a-záéíóúñ]{3,}/i.test(p) && !/^(sketch|paper|img|scan)\b/i.test(p));
  return parts.join(' · ');
}
function yearOf(title) {
  const full = title.match(/\b(19|20)\d{2}\b/);
  if (full) return full[0];
  const short = title.match(/(\d{2})$/);
  return short ? `20${short[1]}` : '';
}

for (const dir of fs.readdirSync(SRC).sort()) {
  const full = path.join(SRC, dir);
  if (!fs.statSync(full).isDirectory()) continue;
  const out = path.join(full, 'info.json');
  if (fs.existsSync(out)) { console.log('exists:', dir); continue; }
  const files = fs.readdirSync(full)
    .filter((f) => /\.(png|jpe?g)$/i.test(f) && !/_auto_x2/.test(f) && !isCover(f) && !isBack(f) && !isWallpaper(f) && !isPattern(f))
    .sort((a, b) => order(a) - order(b) || a.localeCompare(b));
  const talks = files.map((file, i) => {
    let title = talkName(file, dir);
    let speaker = '';
    const m = title.match(/^(.*?)\s*\(([^)]+)\)\s*$/);
    if (m) { title = m[1]; speaker = m[2]; }
    return { sketchnote: i + 1, file, title, speaker, url: '' };
  });
  const info = {
    event: dir.replace(/\s+\d{4}$/, ''),
    edition: yearOf(dir),
    date: yearOf(dir),
    venue: '',
    url: '',
    hashtag: '',
    description: '',
    wallpaper: fs.readdirSync(full).find(isWallpaper) || '',
    pattern: fs.readdirSync(full).find(isPattern) || '',
    author: '@oyabun',
    sketchnotes: files.length,
    talks,
  };
  fs.writeFileSync(out, JSON.stringify(info, null, 2) + '\n');
  console.log('created:', dir, files.length);
}
