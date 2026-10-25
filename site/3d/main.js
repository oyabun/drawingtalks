import { createBookshelfRenderer } from './bookshelfRenderer.js';

const host = document.getElementById('shelf3d');
const canvas = document.getElementById('shelf3d-canvas');
const flipButton = document.getElementById('flip-book');
const label = (n) => `${n} ${n === 1 ? 'lámina' : 'láminas'}`;

function loadImage(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

// color medio de la portada: tela del lomo, contratapa y tono de la habitación
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
// nombres genéricos ("sketch_ 1", "Paper.Bloc.2") → "Lámina N"
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
  return parts.length ? parts.join(' · ') : `Lámina ${index + 1}`;
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
    discipline: label(n),
    note: label(n),
    deck: '',
    binding: '',
    format: '',
    theme: '',
    motif: '',
    motifKey: 'compass',
    paletteLabel: '',
    color: hex(cloth),
    foil: light ? '#2a2622' : '#e9dcc0',
    // la habitación es la misma para todos: el papel pintado no cambia con el libro
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
    // tapa 2:3 algo más ancha que la página (las páginas son medias láminas 4:3)
    width: 1.09,
    height: 1.56,
    // grosor = tapas (0.026) + una hoja por lámina, más portadilla y guarda (~0.7 mm cada una)
    depth: 0.026 + (n + 2) * 0.0038,
    seed: 11 * (index + 1),
    pages: nb.pages,
    // info.json del cuaderno manda; si falta algo, se deduce del nombre de archivo
    year: nb.info?.fecha || yearOf(nb.title),
    place: nb.info?.lugar || '',
    url: (nb.info?.url || '').replace(/^https?:\/\//, '').replace(/\/$/, ''),
    talks: nb.pages.map((page, i) => {
      const talk = nb.info?.charlas?.[i];
      if (!talk?.titulo) return talkName(page.name, nb.title, i);
      return talk.ponente ? `${talk.titulo} — ${talk.ponente}` : talk.titulo;
    }),
    coverImage: cover,
    backImage: back,
    wallpaperImage: wallpaper,
    patternImage: pattern,
    posters: posters.filter((poster) => poster.image),
  };
}

/* ---------- URL: #/slug (cerrado) · #/slug/0 (portadilla) · #/slug/3 (lámina 3) ---------- */
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
  const spread = n === 'fin' ? total : n ? Math.max(0, Math.min(total, parseInt(n, 10) || 0)) : null;
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
document.getElementById('shelf-count').textContent = `${books.length} cuadernos`;

api = createBookshelfRenderer(host, canvas, {
  books,
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
    flipButton.textContent = flipped ? 'Ver portada' : 'Dar la vuelta';
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
