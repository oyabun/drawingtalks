import { createBookshelfRenderer } from './bookshelfRenderer.js';
import { t, localized, translatePage } from '../i18n.js';

const host = document.getElementById('shelf3d');
const canvas = document.getElementById('shelf3d-canvas');
const flipButton = document.getElementById('flip-book');
translatePage();

function loadImage(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

// average cover colour: spine cloth, back board and room tint
function averageColor(img) {
  const c = document.createElement('canvas');
  c.width = 12; c.height = 18;
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, c.width, c.height);
  const d = ctx.getImageData(0, 0, c.width, c.height).data;
  let r = 0, g = 0, b = 0;
  for (let i = 0; i < d.length; i += 4) { r += d[i]; g += d[i + 1]; b += d[i + 2]; }
  const n = d.length / 4;
  return [r / n, g / n, b / n];
}

// "5-Lechazoconf 24 - Un gran proyecto (Laura Lacarra).png" → "Un gran proyecto (Laura Lacarra)"
// generic names ("sketch_ 1", "Paper.Bloc.2") → "Sketchnote N"
const plain = (text) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
function talkName(file, title, index) {
  const brand = plain(title.split(/[\s,]+/)[0]);
  const parts = file
    .replace(/\.[a-z0-9]+$/i, '')
    .replace(/^\d+\s*-\s*/, '')
    .replace(/[._]+/g, ' ')
    .split(/\s+-\s+/)
    .map((part) => part.replace(/^\d+\s+(?=[A-ZÁÉÍÓÚ])/, '').trim())
    .filter((part, i, all) => !(all.length > 1 && i === 0 && (plain(part).includes(brand) || /^[A-Z]{2,}\d*$/.test(part))))
    .filter((part) => /[a-záéíóúñ]{3,}/i.test(part) && !/^(sketch|paper|img|scan)\b/i.test(part));
  return parts.length ? parts.join(' · ') : t('sketchnote', index + 1);
}

// "Tarugo 2022" → 2022 · "TRGCON26" → 2026
function yearOf(title) {
  const full = title.match(/\b(19|20)\d{2}\b/);
  if (full) return full[0];
  const short = title.match(/(\d{2})$/);
  return short ? `20${short[1]}` : '';
}

const hex = ([r, g, b]) => '#' + [r, g, b].map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('');
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const luminance = ([r, g, b]) => (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;

const WALL = [242, 232, 214];

function toBook(nb, index, cover, back, wallpaper, pattern, posters) {
  const n = nb.pages.length;
  const base = cover ? averageColor(cover) : [45, 48, 50];
  const cloth = mix(base, [30, 30, 32], 0.25);
  const light = luminance(cloth) > 0.55;
  return {
    id: nb.slug,
    title: nb.title,
    roman: String(index + 1).padStart(2, '0'),
    discipline: t('sketchnotes', n),
    note: t('sketchnotes', n),
    deck: '',
    binding: '',
    format: '',
    theme: '',
    motif: '',
    motifKey: 'compass',
    paletteLabel: '',
    color: hex(cloth),
    foil: light ? '#2a2622' : '#e9dcc0',
    // the room is the same for every book: the aged paper doesn't change with the book
    palette: {
      paper: hex(WALL),
      paperDeep: hex(mix(WALL, [0, 0, 0], 0.35)),
      paperPale: hex(mix(base, [255, 255, 255], 0.82)),
      ink: '#f4eee6',
      inkSoft: '#c9c3bb',
      wall: hex(WALL),
      shelf: '#f4ebe1',
      shelfDark: '#1c0f09',
      light: '#ffe4c0',
      fill: '#f6efe2',
    },
    // 2:3 board, a little wider than the page (pages are halves of a 4:3 sketchnote)
    width: 1.09,
    height: 1.56,
    // thickness = boards (0.026) + one leaf per sketchnote, plus title page and endpaper (~0.7 mm each)
    depth: 0.026 + (n + 2) * 0.0038,
    seed: 11 * (index + 1),
    pages: nb.pages,
    // the notebook's info.json wins; anything missing is derived from the file name
    // text fields can be a string or { "en": …, "es": … }
    year: localized(nb.info?.date) || yearOf(nb.title),
    place: localized(nb.info?.venue),
    url: localized(nb.info?.url).replace(/^https?:\/\//, '').replace(/\/$/, ''),
    talks: nb.pages.map((page, i) => {
      const talk = nb.info?.talks?.[i];
      const title = localized(talk?.title);
      if (!title) return talkName(page.name, nb.title, i);
      return talk.speaker ? `${title} — ${talk.speaker}` : title;
    }),
    coverImage: cover,
    backImage: back,
    wallpaperImage: wallpaper,
    patternImage: pattern,
    posters: posters.filter((poster) => poster.image),
  };
}

/* ---------- URL: #/slug (closed) · #/slug/0 (title page) · #/slug/3 (sketchnote 3) ---------- */
let books = [];
let api = null;
let writing = false;

function setHash(h) {
  if (location.hash === h || (h === '#/' && !location.hash)) return;
  writing = true;
  history.replaceState(null, '', h || '#/');
  writing = false;
}

function route() {
  if (!api || writing) return;
  const [, slug, n] = location.hash.split('/');
  const index = books.findIndex((b) => b.id === slug);
  if (index < 0) {
    if (api.mode === 'detail') api.close();
    return;
  }
  const total = books[index].pages.length;
  const spread = n === 'end' || n === 'fin' ? total : n ? Math.max(0, Math.min(total, parseInt(n, 10) || 0)) : null;
  api.openBook(index, spread);
}

const data = await fetch('notebooks.json', { cache: 'no-cache' }).then((r) => r.json());
const images = await Promise.all(data.map((nb) => Promise.all([
  loadImage(nb.cover),
  nb.back ? loadImage(nb.back) : null,
  nb.wallpaper ? loadImage(nb.wallpaper) : null,
  nb.pattern ? loadImage(nb.pattern) : null,
  Promise.all((nb.posters || []).map(async (poster) => ({ ...poster, image: await loadImage(poster.src) }))),
])));
books = data.map((nb, i) => toBook(nb, i, ...images[i]));
document.getElementById('shelf-count').textContent = t('notebooks', books.length);

api = createBookshelfRenderer(host, canvas, {
  books,
  t,
  assets: {
    paperColor: '3d/tex/paper-color.webp',
    paperRoughness: '3d/tex/paper-roughness.webp',
    woodColor: '3d/tex/wood-color.webp',
    woodNormal: '3d/tex/wood-normal.webp',
    woodRoughness: '3d/tex/wood-roughness.webp',
  },
  onReady: () => {
    canvas.classList.add('is-ready');
    host.dataset.state = 'ready';
    route();
  },
  onError: (message) => {
    host.dataset.state = 'unavailable';
    document.getElementById('fallback-status').textContent = message;
  },
  onSelectionChange: ({ index }) => {
    document.title = `${books[index].title} · Drawing Talks`;
  },
  onModeChange: (mode) => {
    if (mode === 'shelf') { setHash('#/'); document.title = 'Drawing Talks'; }
  },
  onFlipChange: (flipped) => {
    flipButton.textContent = t(flipped ? 'showCover' : 'turnOver');
  },
  onSpreadChange: ({ index, open, spread }) => {
    const b = books[index];
    flipButton.hidden = open;
    setHash(open ? `#/${b.id}/${spread}` : `#/${b.id}`);
  },
});

flipButton.addEventListener('click', () => api.flip());
new ResizeObserver(() => api.resize()).observe(host);
addEventListener('hashchange', route);
host.focus({ preventScroll: true });
