# Drawing Talks

Los cuadernos de sketchnotes de [@oyabun](https://github.com/oyabun) en una estantería 3D: cada cuaderno es un libro que se saca de la balda, se abre y se hojea. Cada lámina ocupa un pliego completo.

- `site/index.html`: estantería 3D (three.js)
- `site/classic.html`: vista clásica en CSS 3D

## Enlaces

| URL | Qué abre |
| --- | --- |
| `#/tarugo-2024` | el cuaderno, cerrado |
| `#/tarugo-2024/0` | la portadilla |
| `#/tarugo-2024/3` | la lámina 3 |
| `#/tarugo-2024/fin` | la última lámina |

## Estructura

```
notebooks/<Cuaderno>/       originales (fuera del repo, salvo info.json)
  cover.png                 portada; sin ella se usa la primera lámina
  back.png                  contraportada; sin ella se genera con info.json
  *.png / *.jpg             láminas, ordenadas por el número del nombre
  info.json                 datos de la contraportada y de la pared
  assets/
    wallpaper.png           pared mientras el cuaderno está seleccionado
    poster-*.png            pósters satinados pegados a la pared
site/                       la web publicada (img/ y notebooks.json los genera el build)
tools/                      build, vigilante y servidor local
```

### info.json

`node tools/make-info.js` lo crea para los cuadernos que no lo tienen; el que ya existe no se toca.

```json
{
  "evento": "Tarugo",
  "edicion": "2024",
  "fecha": "2024",
  "lugar": "La Nave (Madrid)",
  "url": "",
  "wallpaper": "wallpaper.png",
  "autor": "@oyabun",
  "laminas": 7,
  "charlas": [
    { "lamina": 1, "archivo": "…png", "titulo": "…", "ponente": "…", "url": "" }
  ],
  "posters": {
    "poster-movie.png": { "x": -3, "y": 2.8, "alto": 2.4, "giro": -3 }
  }
}
```

- `wallpaper`: se busca en la carpeta y en `assets/`; `""` deja el papel envejecido.
- `posters` es opcional. Sin él, los pósters se colocan solos alrededor de la balda. Las unidades son de la pared: la balda está en `y = 0.47` y un libro mide 1.09 × 1.56.
- Wallpapers de 3000–4000 px de ancho; el build los reduce a 3840 px como máximo.

## Desarrollo

```bash
cd tools
npm install
npm run build     # genera site/img y site/notebooks.json (incremental)
npm run watch     # regenera al cambiar algo en notebooks/
npm run serve     # http://localhost:8080
```

El renderer 3D (`site/3d/bookshelfRenderer.js`) se genera con `site/3d/patch_renderer.py` a partir del original de ThreeUI; los cambios están en [`site/3d/PATCHES.md`](site/3d/PATCHES.md).

## Créditos

- Renderer Bookshelf de [ThreeUI](https://github.com/MengTo/threeui), MIT (`site/3d/THREEUI-LICENSE`)
- [three.js](https://threejs.org) r165, MIT (`site/vendor/three-LICENSE`)
- Texturas Paper006 y Wood049 de [ambientCG](https://ambientcg.com), CC0
- Láminas y portadas: oyabun
