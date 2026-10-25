// Crea notebooks/<cuaderno>/info.json (datos de la contraportada) si no existe.
// Rellena lo que se deduce de los archivos; URL, fecha exacta y lugar quedan vacíos.
// wallpaper: mural detrás de la balda; pattern: mosaico por toda la pared ("" = papel envejecido).
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
  if (fs.existsSync(out)) { console.log('ya existe:', dir); continue; }
  const files = fs.readdirSync(full)
    .filter((f) => /\.(png|jpe?g)$/i.test(f) && !/_auto_x2/.test(f) && !isCover(f) && !isBack(f) && !isWallpaper(f) && !isPattern(f))
    .sort((a, b) => order(a) - order(b) || a.localeCompare(b));
  const charlas = files.map((archivo, i) => {
    let titulo = talkName(archivo, dir);
    let ponente = '';
    const m = titulo.match(/^(.*?)\s*\(([^)]+)\)\s*$/);
    if (m) { titulo = m[1]; ponente = m[2]; }
    return { lamina: i + 1, archivo, titulo, ponente, url: '' };
  });
  const info = {
    evento: dir.replace(/\s+\d{4}$/, ''),
    edicion: yearOf(dir),
    fecha: yearOf(dir),
    lugar: '',
    url: '',
    hashtag: '',
    descripcion: '',
    wallpaper: fs.readdirSync(full).find(isWallpaper) || '',
    pattern: fs.readdirSync(full).find(isPattern) || '',
    autor: '@oyabun',
    laminas: files.length,
    charlas,
  };
  fs.writeFileSync(out, JSON.stringify(info, null, 2) + '\n');
  console.log('creado:', dir, files.length);
}
