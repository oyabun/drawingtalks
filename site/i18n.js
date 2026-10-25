// UI copy in English and Spanish. The language comes from ?lang=, then the saved choice,
// then the browser; the toggle saves the choice and reloads, because the book textures
// (title page, back cover) are drawn once with the current language.
const STRINGS = {
  en: {
    shelfLabel: 'Drawing Talks notebook shelf',
    loading: 'Setting up the shelf…',
    notebooks: (n) => `${n} ${n === 1 ? 'notebook' : 'notebooks'}`,
    notebookList: 'Notebooks',
    notebook: (n, title) => `Notebook ${n}: ${title}`,
    sketchnotes: (n) => `${n} ${n === 1 ? 'sketchnote' : 'sketchnotes'}`,
    sketchnote: (n) => `Sketchnote ${n}`,
    titlePage: 'Title page',
    previousNotebook: 'Previous notebook',
    nextNotebook: 'Next notebook',
    open: 'Open',
    openTitle: (title) => `Open ${title}`,
    close: 'Close',
    shelf: 'Shelf',
    backToShelf: 'Back to the shelf',
    turnOver: 'Turn over',
    showCover: 'Show cover',
    recenter: 'Recenter',
    closed: 'Closed',
    clickToOpen: 'Click the book to open it',
    hintOpen: 'Drag the pages · Drag the cover to close · Drag the background to look around',
    hintClosed: 'Drag the cover or click to open · Drag the background to look around',
    previousSketchnote: 'Previous sketchnote',
    nextSketchnote: 'Next sketchnote',
    previousSketchnoteTitle: (label) => `Previous sketchnote: ${label}`,
    nextSketchnoteTitle: (label) => `Next sketchnote: ${label}`,
    selected: (n, total, title, note) => `Notebook ${n} of ${total}: ${title}. ${note}`,
    opening: (title) => `Opening ${title}. Drag the cover, click the book or use Open to read it.`,
    opened: (title) => `${title} is open at its title page. Drag a page or use the arrows to read.`,
    closedBook: (title) => `${title} closed. Drag the cover, click the book or use Open to read it.`,
    backCover: (title) => `Back cover of ${title}.`,
    frontCover: (title) => `Front cover of ${title}.`,
    returning: (title) => `Putting ${title} back on the shelf.`,
    returned: (title) => `${title} is back on the shelf.`,
    viewReset: (title) => `View reset for ${title}.`,
    loadFailed: 'The 3D shelf could not be set up.',
    noWebgl: 'WebGL is not available in this browser.',
    contextLost: 'The 3D view stopped after losing its graphics context. Reload the page to restore it.',
    classicView: 'Classic view',
    cover: 'Cover',
    backCoverLabel: 'Back cover',
    backToNotebooks: 'Back to the notebooks',
    fullscreen: 'Full screen',
    threeDView: '3D view',
    language: 'Español',
    languageLabel: 'Cambiar a español',
  },
  es: {
    shelfLabel: 'Estantería de cuadernos Drawing Talks',
    loading: 'Preparando la estantería…',
    notebooks: (n) => `${n} ${n === 1 ? 'cuaderno' : 'cuadernos'}`,
    notebookList: 'Cuadernos',
    notebook: (n, title) => `Cuaderno ${n}: ${title}`,
    sketchnotes: (n) => `${n} ${n === 1 ? 'lámina' : 'láminas'}`,
    sketchnote: (n) => `Lámina ${n}`,
    titlePage: 'Portadilla',
    previousNotebook: 'Cuaderno anterior',
    nextNotebook: 'Cuaderno siguiente',
    open: 'Abrir',
    openTitle: (title) => `Abrir ${title}`,
    close: 'Cerrar',
    shelf: 'Estantería',
    backToShelf: 'Volver a la estantería',
    turnOver: 'Dar la vuelta',
    showCover: 'Ver portada',
    recenter: 'Recentrar',
    closed: 'Cerrado',
    clickToOpen: 'Haz clic en el libro para abrirlo',
    hintOpen: 'Arrastra las páginas · Arrastra la tapa para cerrar · Arrastra el fondo para girar',
    hintClosed: 'Arrastra la tapa o haz clic para abrir · Arrastra el fondo para girar',
    previousSketchnote: 'Lámina anterior',
    nextSketchnote: 'Lámina siguiente',
    previousSketchnoteTitle: (label) => `Lámina anterior: ${label}`,
    nextSketchnoteTitle: (label) => `Lámina siguiente: ${label}`,
    selected: (n, total, title, note) => `Cuaderno ${n} de ${total}: ${title}. ${note}`,
    opening: (title) => `Abriendo ${title}. Arrastra la tapa, haz clic en el libro o usa Abrir para leerlo.`,
    opened: (title) => `${title} abierto por la portadilla. Arrastra una página o usa las flechas para leer.`,
    closedBook: (title) => `${title} cerrado. Arrastra la tapa, haz clic en el libro o usa Abrir para leerlo.`,
    backCover: (title) => `Contraportada de ${title}.`,
    frontCover: (title) => `Portada de ${title}.`,
    returning: (title) => `Devolviendo ${title} a la estantería.`,
    returned: (title) => `${title} vuelve a estar en la estantería.`,
    viewReset: (title) => `Vista recentrada para ${title}.`,
    loadFailed: 'No se pudo preparar la estantería 3D.',
    noWebgl: 'Este navegador no tiene WebGL.',
    contextLost: 'La vista 3D se ha detenido al perder el contexto gráfico. Recarga la página para recuperarla.',
    classicView: 'Vista clásica',
    cover: 'Portada',
    backCoverLabel: 'Contraportada',
    backToNotebooks: 'Volver a los cuadernos',
    fullscreen: 'Pantalla completa',
    threeDView: 'Vista 3D',
    language: 'English',
    languageLabel: 'Switch to English',
  },
};

function readLang() {
  const param = new URLSearchParams(location.search).get('lang');
  if (param in STRINGS) return param;
  try {
    const saved = localStorage.getItem('lang');
    if (saved in STRINGS) return saved;
  } catch {}
  return (navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
}

export const lang = readLang();
document.documentElement.lang = lang;

export function t(key, ...args) {
  const value = STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
  return typeof value === 'function' ? value(...args) : value;
}

// a field in info.json can be a plain string or { "en": "…", "es": "…" }
export function localized(value) {
  if (value && typeof value === 'object') return value[lang] ?? value.en ?? value.es ?? '';
  return value ?? '';
}

export function switchLang() {
  const next = lang === 'es' ? 'en' : 'es';
  try { localStorage.setItem('lang', next); } catch {}
  const url = new URL(location.href);
  url.searchParams.delete('lang');
  location.replace(url);
}

// static copy in the HTML: data-i18n (text), data-i18n-aria (aria-label), data-i18n-title (title)
export function translatePage(root = document) {
  root.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll('[data-i18n-aria]').forEach((el) => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
  root.querySelectorAll('[data-i18n-title]').forEach((el) => { el.setAttribute('title', t(el.dataset.i18nTitle)); });
  root.querySelectorAll('[data-lang-toggle]').forEach((el) => {
    el.textContent = t('language');
    el.setAttribute('aria-label', t('languageLabel'));
    el.addEventListener('click', switchLang);
  });
}
