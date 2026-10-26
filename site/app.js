import { t, localized, translatePage } from './i18n.js';

const $ = (id) => document.getElementById(id);
const shelf = $('shelf'), reader = $('reader'), stage = $('stage'), bookEl = $('book');

// Book model: each sketchnote (4:3) fills the whole open book.
// Leaf -1 = front board: front = cover, back = left half of sketchnote 0.
// Leaf j: front = right half of sketchnote j, back = left half of sketchnote j+1.
// Leaf N-1 = back board: its back is the back cover.
// page: -1 = closed showing the front, 0..N-1 = open at that sketchnote, N = closed showing the back.
const OPEN = 8;       // degrees each half lifts towards the viewer
const FAN = 0.7;      // extra degrees per stacked leaf; the block's edge shows without fanning
const FAN_Z = 1.5;    // depth between stacked leaves
const STACK = 6;      // leaves visible on each side (the boards always show underneath)
const STRIPS = 12;    // strips per leaf so it can bend
const BEND = 70;      // maximum bend while turning (degrees between spine and edge)
const PRELOAD = 3;

let notebooks = [];
let current = null;
let page = -1;
let leaves = [];      // index j+1 -> leaf j
let anim = null;      // turn animation in progress
let booted = false;   // a notebook opened from the first URL appears without flying off the shelf
let pw = 0;           // half-page width in px

const label = (n) => t('sketchnotes', n);
const rad = (d) => (d * Math.PI) / 180;

function hashFor(nb, p) {
  if (p < 0) return `#/${nb.slug}`;
  if (p >= nb.pages.length) return `#/${nb.slug}/end`;
  return `#/${nb.slug}/${p + 1}`;
}

/* ---------- Shelf: closed notebooks ---------- */
let shelfCols = 0;
function renderShelf() {
  $('shelf-count').textContent = t('notebooks', notebooks.length);
  const grid = $('grid');
  const cs = getComputedStyle(grid);
  const bw = parseFloat(cs.getPropertyValue('--book-slot')), gap = parseFloat(cs.columnGap) || 0;
  const cols = Math.max(1, Math.floor((grid.clientWidth - parseFloat(cs.paddingLeft) * 2 + gap) / (bw + gap)));
  if (cols === shelfCols) return;
  shelfCols = cols;
  const cards = notebooks.map(card);
  // one shelf per row of notebooks
  const rows = [];
  for (let i = 0; i < cards.length; i += cols) {
    const row = document.createElement('div');
    row.className = 'shelf-row';
    const books = document.createElement('div');
    books.className = 'shelf-books';
    books.append(...cards.slice(i, i + cols));
    const plank = document.createElement('div');
    plank.className = 'plank';
    plank.innerHTML = '<div class="plank-top"></div><div class="plank-front"></div>';
    row.append(books, plank);
    rows.push(row);
  }
  grid.replaceChildren(...rows);
}

function card(nb) {
  const a = document.createElement('a');
  a.className = nb === current ? 'card away' : 'card';
  a.href = hashFor(nb, -1);
  a.dataset.slug = nb.slug;
  const d = Math.min(26, 8 + nb.pages.length * 1.1);
  a.innerHTML = `
    <div class="nb" style="--d:${d}px; --cover:url('${nb.cover}')">
      <div class="wall-shadow"></div>
      <div class="ground"></div>
      <div class="box">
        <div class="b-back"></div>
        <div class="b-back-edge"></div>
        <div class="b-edge-r"></div>
        <div class="b-edge-t"></div>
        <div class="b-inside" style="background-image:url('${nb.thumb}')"></div>
        <div class="b-hinge">
          <div class="b-cover"></div>
          <div class="b-cover-edge"></div>
          <div class="b-cover-top"></div>
          <div class="b-cover-in" style="background-image:url('${nb.thumb}')"></div>
        </div>
      </div>
    </div>
    <div class="tag"><h3></h3><p>${label(nb.pages.length)}</p></div>`;
  a.querySelector('h3').textContent = nb.title;
  return a;
}

/* ---------- Book ---------- */
function layout() {
  if (!current) return;
  const w = stage.clientWidth * 0.72, h = stage.clientHeight * 0.8;
  const W = Math.min(w, h / 0.75, 1500);
  pw = W / 2;
  for (const el of [bookEl, stage]) {
    el.style.setProperty('--pw', `${pw}px`);
    el.style.setProperty('--ph', `${W * 0.75}px`);
    el.style.setProperty('--sw', `${pw / STRIPS}px`);
  }
  placeBook(page);
}

function makeLeaf(j, n) {
  const leaf = document.createElement('div');
  leaf.className = 'leaf flat';
  if (j === -1) leaf.classList.add('cover-leaf');
  if (j === n - 1) leaf.classList.add('back-leaf');
  leaf.strips = [];
  // boards: rigid card slightly larger than the leaves
  leaf.rigid = j === -1 || j === n - 1;
  if (leaf.rigid) leaf.insertAdjacentHTML('beforeend', '<div class="board"><div class="b-out"></div><div class="b-in"></div><div class="b-side"></div></div>');
  let parent = leaf;
  for (let i = 0; i < STRIPS; i++) {
    const s = document.createElement('div');
    s.className = i === STRIPS - 1 ? 'strip last' : 'strip';
    s.style.setProperty('--i', i);
    s.innerHTML = '<div class="face front"></div><div class="face back"></div>';
    parent.appendChild(s);
    leaf.strips.push(s);
    parent = s;
  }
  return leaf;
}

function buildBook(nb) {
  const n = nb.pages.length;
  // page block: fore-edge and head visible when closed
  bookEl.innerHTML = '<div class="block"><div class="fore"></div><div class="head"></div></div>';
  bookEl.style.setProperty('--t', `${thickness(n)}px`);
  leaves = [];
  for (let j = -1; j < n; j++) {
    const leaf = makeLeaf(j, n);
    bookEl.appendChild(leaf);
    leaves.push(leaf);
  }
  leafAt(-1).style.setProperty('--front', `url('${nb.cover}')`);
  if (nb.back) leafAt(n - 1).style.setProperty('--back', `url('${nb.back}')`);
  else leafAt(n - 1).querySelector('.b-out').append(backCover(nb));
}

// "Tarugo 2022" → 2022 · "TRGCON26" → 2026
function yearOf(title) {
  const full = title.match(/\b(19|20)\d{2}\b/);
  if (full) return full[0];
  const short = title.match(/(\d{2})$/);
  return short ? `20${short[1]}` : '';
}

// back cover from info.json, laid out like the 3D one: title, date · venue · count, talks, URL
function backCover(nb) {
  const info = nb.info || {};
  const el = document.createElement('div');
  el.className = 'back-text';
  const add = (parent, tag, cls, text) => {
    const child = document.createElement(tag);
    child.className = cls;
    if (text != null) child.textContent = text;
    parent.append(child);
    return child;
  };
  const index = notebooks.indexOf(nb) + 1;
  add(el, 'p', 'bt-brand', `Drawing Talks / ${String(index).padStart(2, '0')}`);
  add(el, 'h2', 'bt-title', nb.title).style.setProperty('--len', nb.title.length);
  add(el, 'p', 'bt-meta', [localized(info.date) || yearOf(nb.title), localized(info.venue), label(nb.pages.length)].filter(Boolean).join('  ·  '));
  const list = add(el, 'ol', 'bt-talks');
  list.style.setProperty('--rows', Math.max(nb.pages.length, 6));
  nb.pages.forEach((_, i) => {
    const talk = info.talks?.[i];
    const title = localized(talk?.title);
    add(list, 'li', '', title ? (talk.speaker ? `${title} — ${talk.speaker}` : title) : t('sketchnote', i + 1));
  });
  const foot = add(el, 'p', 'bt-foot');
  add(foot, 'span', '', localized(info.url).replace(/^https?:\/\//, '').replace(/\/$/, ''));
  add(foot, 'span', '', 'Sketchnotes · @oyabun');
  return el;
}

const leafAt = (j) => leaves[j + 1];

function loadImages(p) {
  const n = current.pages.length;
  const c = Math.max(0, Math.min(n - 1, p));
  for (let i = c - PRELOAD; i <= c + PRELOAD; i++) {
    if (i < 0 || i >= n) continue;
    const front = leafAt(i);
    if (front.dataset.loaded) continue;
    front.dataset.loaded = '1';
    const url = `url('${current.pages[i].src}')`;
    front.style.setProperty('--front', url);
    leafAt(i - 1).style.setProperty('--back', url);
  }
}

const thickness = (n) => Math.min(24, 6 + n);

// Resting pose of leaf j when the view is at p.
// Closed: all flat and packed into a block. Open: two stacks in a V.
function rest(j, p) {
  const n = current.pages.length;
  const right = j >= p;
  const k = right ? j - p : p - 1 - j;
  const board = j === -1 || j === n - 1;
  if (p < 0 || p >= n) return { a: right ? 0 : -180, z: (-k * thickness(n)) / n, hidden: false };
  const kk = board ? Math.min(k, STACK + 1) : Math.min(k, STACK);
  return { a: right ? -OPEN + kk * FAN : -180 + OPEN - kk * FAN, z: -kk * FAN_Z, hidden: !board && k > STACK };
}

const rootTransform = (a, z) => `translateZ(${z}px) rotateY(${a}deg)`;

function flatten(leaf) {
  if (!leaf.curled) return;
  leaf.curled = false;
  leaf.classList.add('flat');
  leaf.strips.forEach((s) => {
    s.style.transform = '';
    s.style.setProperty('--shade', 0);
  });
}

// Puts every leaf (except `skip`) at rest for view p.
function placeLeaves(p, skip) {
  const n = current.pages.length;
  for (let j = -1; j < n; j++) {
    if (j === skip) continue;
    const leaf = leafAt(j);
    const { a, z, hidden } = rest(j, p);
    leaf.style.transform = rootTransform(a, z);
    leaf.style.visibility = hidden ? 'hidden' : '';
    flatten(leaf);
  }
}

// Closed book: the cover is centred by shifting the book half a page.
function placeBook(p) {
  const n = current.pages.length;
  const shift = p < 0 ? -pw / 2 : p >= n ? pw / 2 : 0;
  // closed, it turns slightly so the fore-edge shows
  const turn = p < 0 ? -16 : p >= n ? 16 : 0;
  bookEl.style.transform = `rotateX(12deg) rotateY(${turn}deg) translateX(${shift}px)`;
  bookEl.classList.toggle('closed-front', p < 0);
  bookEl.classList.toggle('closed-back', p >= n);
}

// Leaf j turning in direction dir (1 = forward) with progress t in [0, 1].
function curl(j, dir, t) {
  const leaf = leafAt(j);
  const from = rest(j, page).a;
  // stops 1° short of the target stack so it always stays in front
  const to = rest(j, page + dir).a + dir;
  const a = from + (to - from) * t;
  let bend = leaf.rigid ? 0 : BEND * Math.sin(Math.PI * t);
  // the edge cannot pass through the target stack
  bend = Math.max(0, Math.min(bend, dir > 0 ? a - to : to - a));
  const step = (dir > 0 ? -bend : bend) / (STRIPS - 1);
  leaf.style.visibility = '';
  leaf.style.transform = rootTransform(a, 0);
  if (leaf.rigid) return;
  leaf.curled = true;
  leaf.classList.remove('flat');
  const rest0 = Math.abs(Math.cos(rad(OPEN)));
  leaf.strips.forEach((s, i) => {
    s.style.transform = i ? `rotateY(${step}deg)` : '';
    const ai = a + step * i;
    s.style.setProperty('--shade', Math.max(0, 0.45 * (rest0 - Math.abs(Math.cos(rad(ai))))).toFixed(3));
  });
}

function updateUI() {
  const n = current.pages.length;
  $('r-pos').textContent = page < 0 ? t('cover') : page >= n ? t('backCoverLabel') : `${page + 1} / ${n}`;
  $('btn-prev').disabled = page <= -1;
  $('btn-next').disabled = page >= n;
  const h = hashFor(current, page);
  if (location.hash !== h) history.replaceState(null, '', h);
  document.title = `${current.title} · Drawing Talks`;
}

function render() {
  placeLeaves(page);
  placeBook(page);
  loadImages(page);
  updateUI();
}

const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

// Animates the leaf turn from t0 to t1; reaching 1 changes the page.
function animateFlip(dir, t0, t1, done) {
  finishAnim();
  const j = dir > 0 ? page : page - 1;
  const target = page + dir;
  const ms = 250 + 650 * Math.abs(t1 - t0);
  const start = performance.now();
  const leaf = leafAt(j);
  leaf.classList.add('instant');
  anim = { finish: null };
  const end = () => {
    cancelAnimationFrame(anim.raf);
    anim = null;
    leaf.classList.remove('instant');
    if (t1 === 1) page = target;
    render();
    done && done();
  };
  anim.finish = end;
  const tick = (now) => {
    const x = Math.min(1, (now - start) / ms);
    curl(j, dir, t0 + (t1 - t0) * ease(x));
    if (x < 1) anim.raf = requestAnimationFrame(tick);
    else end();
  };
  anim.raf = requestAnimationFrame(tick);
}

function finishAnim() { if (anim) anim.finish(); }

function flip(dir) {
  if (!current) return;
  finishAnim();
  const n = current.pages.length;
  const target = page + dir;
  if (target < -1 || target > n) return;
  loadImages(target);
  placeLeaves(target, dir > 0 ? page : page - 1);
  placeBook(target);
  animateFlip(dir, 0, 1);
}

function jump(p) {
  finishAnim();
  page = p;
  render();
}

/* ---------- Taking a notebook off the shelf and putting it back ---------- */
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
let flight = null;    // { finish } while the book flies between the shelf and the reader
let leaving = false;  // closing on its way back to the shelf: input is ignored
const busy = () => !current || leaving || flight;

const cardFor = (nb) => $('grid').querySelector(`.card[data-slug="${CSS.escape(nb.slug)}"]`);
const center = (r) => ({ x: r.left + r.width / 2, y: r.top + r.height / 2 });
function onScreen(el) {
  const r = el.getBoundingClientRect();
  return r.bottom > 0 && r.top < innerHeight && r.width > 0;
}

// Moves the whole stage so the closed book in the reader sits exactly over its shelf copy,
// then animates to (inward) or from (outward) its place in the reader.
function fly(card, inward, done) {
  const from = card.querySelector('.b-back').getBoundingClientRect();
  const to = leafAt(-1).querySelector('.b-out').getBoundingClientRect();
  const sr = stage.getBoundingClientRect();
  const a = center(from), b = center(to);
  const s = from.height / to.height;
  stage.style.transformOrigin = `${b.x - sr.left}px ${b.y - sr.top}px`;
  const shelfPose = { transform: `translate(${a.x - b.x}px, ${a.y - b.y}px) scale(${s})` };
  const readerPose = { transform: 'none' };
  const timing = { duration: inward ? 760 : 680, easing: 'cubic-bezier(.3,.6,.15,1)', fill: 'both' };
  const fade = (el, delay = 0) => el.animate(
    inward ? [{ opacity: 0 }, { opacity: 1 }] : [{ opacity: 1 }, { opacity: 0 }],
    { ...timing, delay, duration: timing.duration - delay });
  const anims = [
    stage.animate(inward ? [shelfPose, readerPose] : [readerPose, shelfPose], timing),
    fade(reader.querySelector('.reader-bg')),
    fade(reader.querySelector('.reader-head'), inward ? 250 : 0),
    fade(reader.querySelector('.toolbar'), inward ? 250 : 0),
    fade(stage.querySelector('.floor-shadow'), inward ? 300 : 0),
  ];
  const finish = () => {
    if (!flight) return;
    flight = null;
    anims.forEach((x) => x.cancel());
    stage.style.transformOrigin = '';
    done && done();
  };
  flight = { finish };
  anims[0].finished.then(finish, () => {});
}

function openNotebook(nb, p, animate = false) {
  finishAnim();
  if (flight) flight.finish();
  current = nb;
  document.documentElement.classList.add('reading');
  reader.hidden = false;
  $('r-title').textContent = nb.title;
  $('r-count').textContent = label(nb.pages.length);
  buildBook(nb);
  page = p;
  layout();
  bookEl.classList.add('instant');
  leaves.forEach((l) => l.classList.add('instant'));
  render();
  const card = cardFor(nb);
  card?.classList.add('away');
  if (animate && p === -1 && card && onScreen(card) && !reducedMotion.matches) fly(card, true);
  requestAnimationFrame(() => requestAnimationFrame(() => {
    bookEl.classList.remove('instant');
    leaves.forEach((l) => l.classList.remove('instant'));
  }));
}

// Closes the book (if it is open), flies it back to its gap on the shelf and drops the reader.
function closeNotebook() {
  if (!current || leaving) return;
  finishAnim();
  if (flight) flight.finish();
  const nb = current;
  const card = cardFor(nb);
  const done = () => {
    leaving = false;
    current = null;
    cardFor(nb)?.classList.remove('away');
    bookEl.replaceChildren();
    reader.hidden = true;
    document.documentElement.classList.remove('reading');
    document.title = 'Drawing Talks';
  };
  if (!card || reducedMotion.matches) return done();
  leaving = true;
  card.scrollIntoView({ block: 'nearest' });
  const wasOpen = page !== -1;
  if (wasOpen) { page = -1; render(); }
  history.replaceState(null, '', '#/');
  setTimeout(() => fly(card, false, done), wasOpen ? 820 : 0);
}

/* ---------- Arrastre y clic ---------- */
let drag = null;
stage.addEventListener('pointerdown', (e) => {
  if (busy() || e.button) return;
  finishAnim();
  const n = current.pages.length;
  const r = bookEl.getBoundingClientRect();
  let dir;
  if (page < 0) dir = 1;
  else if (page >= n) dir = -1;
  else dir = e.clientX > r.left + r.width / 2 ? 1 : -1;
  drag = { x: e.clientX, dir, t: 0, t0: performance.now(), moving: false };
  stage.setPointerCapture(e.pointerId);
});
stage.addEventListener('pointermove', (e) => {
  if (!drag) return;
  const dx = e.clientX - drag.x;
  if (!drag.moving) {
    if (Math.abs(dx) < 8) return;
    drag.moving = true;
    stage.classList.add('dragging');
    const j = drag.dir > 0 ? page : page - 1;
    leafAt(j).classList.add('instant');
    loadImages(page + drag.dir);
    placeLeaves(page + drag.dir, j);
    placeBook(page + drag.dir);
  }
  drag.t = Math.max(0, Math.min(1, (drag.dir > 0 ? -dx : dx) / (pw * 1.4)));
  curl(drag.dir > 0 ? page : page - 1, drag.dir, drag.t);
});
const endDrag = (e) => {
  if (!drag) return;
  const d = drag;
  drag = null;
  stage.classList.remove('dragging');
  if (!d.moving) {
    if (e.type === 'pointerup') {
      const r = bookEl.getBoundingClientRect();
      if (e.clientX >= r.left - 40 && e.clientX <= r.right + 40) flip(d.dir);
    }
    return;
  }
  const fast = performance.now() - d.t0 < 300 && d.t > 0.05;
  const commit = d.t > 0.3 || fast;
  if (!commit) { placeBook(page); }
  animateFlip(d.dir, d.t, commit ? 1 : 0);
};
stage.addEventListener('pointerup', endDrag);
stage.addEventListener('pointercancel', endDrag);

/* ---------- Rutas ---------- */
function route() {
  const [slug, n] = decodeURIComponent(location.hash.replace(/^#\/?/, '')).split('/');
  const nb = notebooks.find((x) => x.slug === slug);
  if (!nb) { if (current) closeNotebook(); return; }
  if (leaving) return;
  const total = nb.pages.length;
  const p = n === 'end' || n === 'fin' ? total : n ? Math.max(0, Math.min(total - 1, (parseInt(n, 10) || 1) - 1)) : -1;
  if (current !== nb) openNotebook(nb, p, booted);
  else if (p !== page) jump(p);
}

$('btn-back').onclick = () => { location.hash = ''; };
$('btn-prev').onclick = () => { if (!busy()) flip(-1); };
$('btn-next').onclick = () => { if (!busy()) flip(1); };
$('btn-full').onclick = () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen?.();
};
addEventListener('keydown', (e) => {
  if (busy()) return;
  if (e.key === 'ArrowRight') flip(1);
  else if (e.key === 'ArrowLeft') flip(-1);
  else if (e.key === 'Home') jump(0);
  else if (e.key === 'End') jump(current.pages.length - 1);
  else if (e.key === 'Escape' && !document.fullscreenElement) location.hash = '';
});
addEventListener('hashchange', route);
addEventListener('resize', () => { layout(); renderShelf(); });

translatePage();
fetch('notebooks.json', { cache: 'no-cache' }).then((r) => r.json()).then((data) => {
  notebooks = data;
  renderShelf();
  route();
  booted = true;
});
