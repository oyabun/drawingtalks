# 3D bookshelf

`bookshelfRenderer.js` is ThreeUI's Bookshelf renderer (`src/shaders/bookshelf/bookshelfRenderer.js`,
SHA-256 `94c5141e…16a8`), changed by `patch_renderer.py`. Every edit in the script is checked
against the original source text, and the script is the full list of changes:

- books, covers and back covers come from `notebooks.json` (`main.js`); the embedded cover atlas is gone
- the inside: a title page with the notebook's name, then each lámina across one open spread
  (left half on the back of leaf j, right half on the front of leaf j+1); `-hd.webp` láminas load when a book opens
- spot-UV varnish on the cover art: a clearcoat mask built from the cover, plus a shader glint
  (a window reflection) on the varnished areas that moves as the book tilts with the pointer
- the closed book can be turned over (`flip()`, `onFlipChange`); the back cover lists title, year,
  number of láminas and the talks (`year` / `talks` come from `main.js`)
- Neutral tone mapping instead of ACES, so the láminas keep their colours; pages no longer twist
  in their own plane (that pulled the edge off the spine)
- the room: aged-paper wallpaper (Paper006), an oak shelf (Wood049) on iron brackets, a warm spotlight;
  while a notebook is selected its `assets/wallpaper.png` covers the visible wall (vignette, edge fade
  into its darkened average colour, bump from its luminance) and its `assets/poster-*.png` are pasted
  around the shelf as satin posters (clearcoat, paper bump, contact shadow); a raking spotlight shows
  the relief
- the open book: page stacks as thick as the real leaves, the left board drops to table level,
  the spine flattens and every leaf bends down to the same point of the spine
- orbit limits, Spanish labels, URL hooks (`openBook`, `onSpreadChange`)

To regenerate:

    python3 patch_renderer.py <original bookshelfRenderer.js> bookshelfRenderer.js

ThreeUI (https://github.com/MengTo/threeui) is MIT licensed; its notice is in `THREEUI-LICENSE`.
`three165/` holds ThreeUI's three.js adapters, unchanged. three.js r165 is in `../vendor/` (MIT).
The textures in `tex/` come from ambientCG and are CC0 (see `tex/CREDITS.txt`).
