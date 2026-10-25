const isCover = (f) => /^(cover|cvoer)\.(png|jpe?g)$/i.test(f);
const isBack = (f) => /^back\.(png|jpe?g)$/i.test(f);

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

const isWallpaper = (f) => /^wallpaper\.(png|jpe?g)$/i.test(f);

const isPattern = (f) => /^pattern\.(png|jpe?g)$/i.test(f);

module.exports = { order, isCover, isBack, isWallpaper, isPattern };
