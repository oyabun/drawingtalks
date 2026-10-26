// Builds site/img/* (optimised WebP) and site/notebooks.json from notebooks/
// - cover.png (or cvoer.png) -> front cover of the closed notebook
// - back.png                -> back cover
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'notebooks');
const OUT = path.join(ROOT, 'site');

const isCover = (f) => /^(cover|cvoer)\.(png|jpe?g)$/i.test(f);
const isBack = (f) => /^back\.(png|jpe?g)$/i.test(f);
// wall while the notebook is selected: wallpaper.* = mural, pattern.* = tiles
const isWallpaper = (f) => /^wallpaper\.(png|jpe?g)$/i.test(f);
const isPattern = (f) => /^pattern\.(png|jpe?g)$/i.test(f);

const slugify = (s) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function order(name) {
  const dia = name.match(/Dia (\d+) - (?:La portada|Lamina (\d+))/i);
  if (dia) return +dia[1] * 1000 + (dia[2] ? +dia[2] + 1 : 0);
  let m;
  if ((m = name.match(/^(\d+)[-.]/))) return +m[1];
  if ((m = name.match(/^.*? - (\d+)(?: |-|\.|$)/))) return +m[1];
  if ((m = name.match(/\.(\d+)\.(?:png|jpe?g)$/i))) return +m[1];
  if ((m = name.match(/_\s*(\d+)\./))) return +m[1];
  return 9999;
}

// incremental: an image is only rebuilt when its original is newer
const stale = (src, out) => !fs.existsSync(out) || fs.statSync(out).mtimeMs < fs.statSync(src).mtimeMs;
const write = (src, out, make) => (stale(src, out) ? make(sharp(src)).toFile(out) : Promise.resolve());

// 2:3 centre crop: the closed notebook is half a sketchnote
const board = (file, out) =>
  write(file, out, (img) => img.resize({ width: 1000, height: 1500, fit: 'cover', position: 'centre' }).webp({ quality: 86 }));

(async () => {
  const notebooks = [];
  for (const dir of fs.readdirSync(SRC).sort()) {
    const full = path.join(SRC, dir);
    if (!fs.statSync(full).isDirectory()) continue;
    const all = fs.readdirSync(full).filter((f) => /\.(png|jpe?g)$/i.test(f) && !/_auto_x2/.test(f));
    // info.json: back cover and wall details (see make-info.js)
    const infoFile = path.join(full, 'info.json');
    const info = fs.existsSync(infoFile) ? JSON.parse(fs.readFileSync(infoFile, 'utf8')) : null;
    // info.json decides the wall ("" = none); without the field, wallpaper.* / pattern.* are looked up in the folder
    // assets/: wallpaper and posters (poster-*.png) for the wall; files named in info.json are looked up there too
    const assetsDir = path.join(full, 'assets');
    const assets = fs.existsSync(assetsDir) ? fs.readdirSync(assetsDir).filter((f) => /\.(png|jpe?g|webp)$/i.test(f)) : [];
    const wallImage = (field, test) => {
      if (!info || !(field in info)) {
        const inAssets = assets.find(test);
        return inAssets ? `assets/${inAssets}` : all.find(test) || null;
      }
      if (!info[field]) return null;
      for (const candidate of [info[field], `assets/${info[field]}`]) {
        if (fs.existsSync(path.join(full, candidate))) return candidate;
      }
      console.warn(`  ${dir}: ${info[field]} not found`);
      return null;
    };
    const wallFile = wallImage('wallpaper', isWallpaper);
    const patternFile = wallImage('pattern', isPattern);
    const coverFile = all.find(isCover);
    const backFile = all.find(isBack);
    const files = all
      .filter((f) => !isCover(f) && !isBack(f) && !isWallpaper(f) && !isPattern(f) && f !== wallFile && f !== patternFile)
      .sort((a, b) => order(a) - order(b) || a.localeCompare(b));
    const slug = slugify(dir);
    const dirOut = `${OUT}/img/${slug}`;
    // outputs in this folder that no longer match anything are deleted at the end
    fs.mkdirSync(dirOut, { recursive: true });
    const keep = new Set();

    const pages = [];
    for (let i = 0; i < files.length; i++) {
      const src = path.join(full, files[i]);
      const { width, height } = await sharp(src).metadata();
      const base = `img/${slug}/${String(i).padStart(2, '0')}`;
      // the order can change when sketchnotes are added: if an output name belonged to another file, it is rebuilt
      const marker = `${OUT}/${base}.src`;
      const sameSource = fs.existsSync(marker) && fs.readFileSync(marker, 'utf8') === files[i];
      if (!sameSource) for (const f of [`${base}.webp`, `${base}-hd.webp`, `${base}-thumb.webp`]) fs.rmSync(`${OUT}/${f}`, { force: true });
      fs.writeFileSync(marker, files[i]);
      keep.add(`${String(i).padStart(2, '0')}.src`);
      await write(src, `${OUT}/${base}.webp`, (img) => img.resize({ width: 1800, withoutEnlargement: true }).webp({ quality: 82 }));
      // large version for the 3D shelf (each half page = 1280 px)
      await write(src, `${OUT}/${base}-hd.webp`, (img) => img.resize({ width: 2560, withoutEnlargement: true }).webp({ quality: 85 }));
      if (i === 0) await write(src, `${OUT}/${base}-thumb.webp`, (img) => img.resize({ width: 640 }).webp({ quality: 78 }));
      keep.add(`${String(i).padStart(2, '0')}.webp`).add(`${String(i).padStart(2, '0')}-hd.webp`);
      if (i === 0) keep.add('00-thumb.webp');
      pages.push({ src: `${base}.webp`, hd: `${base}-hd.webp`, w: width, h: height, name: files[i] });
    }
    // the cover can switch from the first sketchnote to cover.png: rebuilt when its source changes
    const coverSrc = coverFile || files[0];
    const coverMarker = `${dirOut}/cover.src`;
    if (!fs.existsSync(coverMarker) || fs.readFileSync(coverMarker, 'utf8') !== coverSrc) fs.rmSync(`${dirOut}/cover.webp`, { force: true });
    fs.writeFileSync(coverMarker, coverSrc);
    await board(path.join(full, coverSrc), `${dirOut}/cover.webp`);
    keep.add('cover.webp').add('cover.src');
    if (backFile) { await board(path.join(full, backFile), `${dirOut}/back.webp`); keep.add('back.webp'); }
    const wallOut = (file, name) => {
      keep.add(`${name}.webp`);
      return write(path.join(full, file), `${dirOut}/${name}.webp`, (img) => img.resize({ width: 3840, withoutEnlargement: true }).webp({ quality: 88 }));
    };
    if (wallFile) await wallOut(wallFile, 'wallpaper');
    if (patternFile) await wallOut(patternFile, 'pattern');

    // posters: satin, pasted on the wall; info.json "posters" can pin x, y, height, rotation per file
    const posters = [];
    for (const file of assets.filter((f) => /^poster-.+\.(png|jpe?g|webp)$/i.test(f)).sort()) {
      const name = file.replace(/\.[a-z]+$/i, '');
      keep.add(`${name}.webp`);
      const src = path.join(assetsDir, file);
      await write(src, `${dirOut}/${name}.webp`, (img) => img.resize({ height: 1536, withoutEnlargement: true }).webp({ quality: 90, alphaQuality: 90 }));
      const { width, height } = await sharp(src).metadata();
      posters.push({ src: `img/${slug}/${name}.webp`, w: width, h: height, name: file, ...(info?.posters?.[file] || {}) });
    }


    notebooks.push({
      slug,
      title: dir,
      info,
      cover: `img/${slug}/cover.webp`,
      back: backFile ? `img/${slug}/back.webp` : null,
      wallpaper: wallFile ? `img/${slug}/wallpaper.webp` : null,
      pattern: patternFile ? `img/${slug}/pattern.webp` : null,
      posters,
      thumb: `img/${slug}/00-thumb.webp`,
      pages,
    });
    for (const f of fs.readdirSync(dirOut)) if (!keep.has(f)) fs.rmSync(path.join(dirOut, f));
    console.log(dir, pages.length, coverFile || '(no cover)', backFile || '', wallFile || '', patternFile || '', posters.length ? `${posters.length} posters` : '');
  }
  // notebook folders that no longer exist
  const slugs = new Set(notebooks.map((n) => n.slug));
  for (const d of fs.readdirSync(`${OUT}/img`)) if (!slugs.has(d)) fs.rmSync(`${OUT}/img/${d}`, { recursive: true });
  // shelf order: by year (info.json date, else the title), oldest first; notebooks without a year go last
  const yearOf = (nb) => {
    const date = nb.info?.date;
    const text = `${typeof date === 'object' && date ? date.en ?? date.es ?? '' : date ?? ''} ${nb.title}`;
    const full = text.match(/\b(19|20)\d{2}\b/);
    if (full) return +full[0];
    const short = nb.title.match(/(\d{2})$/);
    return short ? 2000 + +short[1] : Infinity;
  };
  notebooks.sort((a, b) => yearOf(a) - yearOf(b) || a.title.localeCompare(b.title));
  fs.writeFileSync(`${OUT}/notebooks.json`, JSON.stringify(notebooks, null, 1));
})();
