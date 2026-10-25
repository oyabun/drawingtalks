#!/usr/bin/env python3
"""Adapt ThreeUI's exact bookshelfRenderer.js to the Drawing Talks notebooks.

Every replacement is asserted against the original source so the patch fails
loudly if the upstream file changes.
"""
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
s = open(SRC).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, f"expected {count} match(es), found {n}: {old[:90]!r}"
    s = s.replace(old, new)


def rep_between(start, end, new):
    """Replace from `start` (inclusive) up to `end` (exclusive)."""
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + new + s[b:]


# --- header -----------------------------------------------------------------
rep(
    "/* This file is generated from the exact committed Bookshelf project. Do not edit by hand. */",
    "/* Drawing Talks: adapted from ThreeUI's exact Bookshelf renderer (see 3d/PATCHES.md).\n"
    "   Books, covers and pages come from notebooks.json instead of the authored seven volumes. */\n"
    "/* This file is generated from the exact committed Bookshelf project. Do not edit by hand. */",
)

# --- data: books from the caller, covers from their images ---------------------
rep_between(
    "    const BOOKS = [\n",
    "    const COVER_ATLAS_DATA",
    "    // Drawing Talks: cada cuaderno de notebooks.json (ver 3d/main.js).\n"
    "    const BOOKS = callbacks.books;\n\n",
)
s = re.sub(r'    const COVER_ATLAS_DATA = "[^"]*";\n', "", s, count=1)
rep_between(
    "    // Seven 2:3 cover artworks arranged left to right in one embedded atlas.\n",
    "    const woodTextureImage = new Image();",
    "",
)
rep(
    """      if (coverAtlasReady) {
        const [sourceX, sourceY, sourceWidth, sourceHeight] = COVER_CROPS[BOOKS.indexOf(book)];
        ctx.drawImage(
          coverAtlasImage,
          sourceX,
          sourceY,
          sourceWidth,
          sourceHeight,
          0,
          0,
          canvasTexture.width,
          canvasTexture.height
        );
""",
    """      if (book.coverImage) {
        drawImageCover(ctx, book.coverImage, canvasTexture.width, canvasTexture.height);
""",
)
rep(
    """    function makeFoilTexture(book) {
      const foilCanvas = document.createElement("canvas");""",
    """    // recorte tipo object-fit: cover
    function drawImageCover(ctx, image, width, height) {
      const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight);
      const drawWidth = image.naturalWidth * scale;
      const drawHeight = image.naturalHeight * scale;
      ctx.drawImage(image, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
    }

    function makeFoilTexture(book) {
      // la portada ya es una ilustración: sin texto estampado encima
      if (book.coverImage) {
        const blank = document.createElement("canvas");
        blank.width = blank.height = 4;
        return configureCanvasTexture(new THREE.CanvasTexture(blank));
      }
      const foilCanvas = document.createElement("canvas");""",
)
rep(
    """      const random = seededRandom(hashSeed(`${book.id}-back-cloth`) + book.seed);

      ctx.fillStyle = book.color;
      ctx.fillRect(0, 0, backCanvas.width, backCanvas.height);
""",
    """      const random = seededRandom(hashSeed(`${book.id}-back-cloth`) + book.seed);

      ctx.fillStyle = book.color;
      ctx.fillRect(0, 0, backCanvas.width, backCanvas.height);
      if (book.backImage) {
        drawImageCover(ctx, book.backImage, backCanvas.width, backCanvas.height);
        return configureCanvasTexture(new THREE.CanvasTexture(backCanvas));
      }
""",
)
rep(
    """      ctx.clearRect(0, 0, foilCanvas.width, foilCanvas.height);
      ctx.fillStyle = "#ffffff";
      ctx.strokeStyle = "#ffffff";
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";

      ctx.font = '500 16px Inter, "Helvetica Neue", Arial, sans-serif';""",
    """      ctx.clearRect(0, 0, foilCanvas.width, foilCanvas.height);
      if (book.backImage) return configureCanvasTexture(new THREE.CanvasTexture(foilCanvas));
      ctx.fillStyle = "#ffffff";
      ctx.strokeStyle = "#ffffff";
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";

      ctx.font = '500 16px Inter, "Helvetica Neue", Arial, sans-serif';""",
)
rep("ctx.fillText(`WORKING VOLUMES  /  ${book.roman}`, 68, 82);", "ctx.fillText(`DRAWING TALKS  /  ${book.roman}`, 68, 82);")
rep('ctx.fillText("AN IMAGINED EDITION", 700, 1080);', 'ctx.fillText("SKETCHNOTES · @OYABUN", 700, 1080);')

# --- pages: one lámina across each spread, loaded when the book opens --------------
rep(
    "      const interiorPageTextures = makeInteriorPageTextures(book);\n",
    "      const interiorPageTextures = [];\n",
)
rep(
    """      const interiorPageMaterials = interiorPageTextures.map((texture) => {
        const material = createFadeMaterial(shared.pageSheet);
        material.map = texture;
        material.bumpMap = paperFaceTexture;
        material.bumpScale = 0.0012;
        material.roughness = 0.96;
        material.side = THREE.FrontSide;
        material.needsUpdate = true;
        return material;
      });
""",
    """      // Cada lámina (4:3) ocupa un pliego: mitad izquierda y mitad derecha.
      // Hasta abrir el libro llevan papel en blanco (ver loadPlates).
      const makePlateMaterial = () => {
        const material = createFadeMaterial(shared.pageSheet);
        material.map = paperFaceTexture;
        material.bumpMap = paperFaceTexture;
        material.bumpScale = 0.0012;
        material.roughness = 0.96;
        material.side = THREE.FrontSide;
        material.needsUpdate = true;
        return material;
      };
      const plates = book.pages.map((page) => ({
        src: page.hd || page.src,
        left: makePlateMaterial(),
        right: makePlateMaterial(),
        textures: null
      }));
      // primera página: solo el nombre del cuaderno
      const titlePageMaterial = makePlateMaterial();
      titlePageMaterial.map = makeTitlePageTexture(book);
      const interiorPageMaterials = [titlePageMaterial, ...plates.flatMap((plate) => [plate.left, plate.right])];
      // pliegos: portadilla + uno por lámina
      const leafCount = plates.length + 1;
""",
)
rep(
    """      const pagePivots = [];
      const pageSurfaces = [];
      for (let pageIndex = 0; pageIndex < 6; pageIndex += 1) {
        const leafOrder = 5 - pageIndex;
        const frontPageMaterial = leafOrder < 4
          ? interiorPageMaterials[leafOrder * 2]
          : blankPageMaterial;
        const backPageMaterial = leafOrder < 4
          ? interiorPageMaterials[leafOrder * 2 + 1]
          : blankPageMaterial;""",
    """      // Hoja 0: cara = portadilla. Hoja j: dorso = mitad izquierda de la lámina j,
      // cara de la hoja j+1 = mitad derecha; así cada lámina cruza el pliego entre dos hojas iguales.
      const pagePivots = [];
      const pageSurfaces = [];
      const pivotCount = leafCount + 1;
      const leafStep = Math.min(0.0015, 0.008 / pivotCount);
      for (let pageIndex = 0; pageIndex < pivotCount; pageIndex += 1) {
        const leafOrder = pivotCount - 1 - pageIndex;
        const frontPageMaterial = leafOrder === 0
          ? titlePageMaterial
          : leafOrder < leafCount
            ? plates[leafOrder - 1].right
            : blankPageMaterial;
        const backPageMaterial = leafOrder < leafCount - 1
          ? plates[leafOrder].left
          : blankPageMaterial;""",
)
rep(
    """          pageDepth * 0.5 + 0.0015 + pageIndex * 0.0015
        );
        pagePivot.userData.restZ = pagePivot.position.z;
        pagePivot.userData.turnedZ = depth * 0.5 + board + 0.004 + leafOrder * 0.0015;""",
    """          pageDepth * 0.5 + 0.0015 + pageIndex * leafStep
        );
        pagePivot.userData.restZ = pagePivot.position.z;
        pagePivot.userData.turnedZ = depth * 0.5 + board + 0.004 + leafOrder * leafStep;""",
)
rep(
    """      return {
        data: book,
        root,
        motion,
        frontPivot,""",
    """      return {
        data: book,
        plates,
        leafCount,
        root,
        motion,
        frontPivot,""",
)


# Láminas: se cargan al abrir el libro y se liberan al devolverlo a la estantería.
rep(
    """    function configureResponsiveTargets() {""",
    """    const plateLoader = new THREE.ImageLoader();

    function loadPlates(rig) {
      rig.plates.forEach((plate) => {
        if (plate.textures || plate.loading) return;
        plate.loading = true;
        plateLoader.load(plate.src, (image) => {
          plate.loading = false;
          if (destroyed || rig !== activeBook) return;
          const makeHalf = (offsetX) => {
            const texture = new THREE.Texture(image);
            texture.colorSpace = THREE.SRGBColorSpace;
            texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
            texture.repeat.set(0.5, 1);
            texture.offset.set(offsetX, 0);
            texture.needsUpdate = true;
            return texture;
          };
          plate.textures = [makeHalf(0), makeHalf(0.5)];
          plate.left.map = plate.textures[0];
          plate.right.map = plate.textures[1];
          plate.left.needsUpdate = plate.right.needsUpdate = true;
          requestFrame();
        }, undefined, () => { plate.loading = false; });
      });
    }

    function unloadPlates(rig) {
      rig.plates.forEach((plate) => {
        if (!plate.textures) return;
        plate.textures.forEach((texture) => texture.dispose());
        plate.textures = null;
        plate.left.map = plate.right.map = rig.paperFaceTexture;
        plate.left.needsUpdate = plate.right.needsUpdate = true;
      });
    }

    const spreadCount = () => (activeBook || bookRigs[selectedIndex])?.leafCount || 1;

    function configureResponsiveTargets() {""",
)

# --- variable number of spreads ----------------------------------------------------
rep(
    "    const PAGINATED_LEAF_COUNT = 4;\n    const SPREAD_COUNT = PAGINATED_LEAF_COUNT + 1;\n",
    "",
)
rep("currentSpread === SPREAD_COUNT - 1;", "currentSpread === spreadCount() - 1;")
rep(
    """      pageCounter.textContent = readingOpen
        ? `${pad(currentSpread + 1)} / ${pad(SPREAD_COUNT)}`""",
    """      pageCounter.textContent = readingOpen
        ? (currentSpread === 0 ? book.title : `${currentSpread} / ${spreadCount() - 1}`)""",
)
rep("liveRegion.textContent = `Page ${currentSpread + 1} of ${SPREAD_COUNT}: ${labels[currentSpread]}.`;",
    "liveRegion.textContent = `${labels[currentSpread]}.`;")
rep(
    """        currentSpread + direction,
        0,
        SPREAD_COUNT - 1
      );""",
    """        currentSpread + direction,
        0,
        spreadCount() - 1
      );""",
)
rep(
    """            ? currentSpread < SPREAD_COUNT - 1
            : currentSpread > 0;""",
    """            ? currentSpread < spreadCount() - 1
            : currentSpread > 0;""",
)

# stacked leaves fan relative to the open spread, so long notebooks keep a tidy block
rep(
    """      rig.pagePivots.forEach((pagePivot, pageIndex) => {
        const leafOrder = rig.pagePivots.length - 1 - pageIndex;""",
    """      const paginatedLeafCount = rig.leafCount - 1;
      const unturnedAt = (leaf, spread) => -0.038 + Math.min(Math.max(leaf - spread, 0), 4) * 0.008;
      const turnedAt = (leaf, spread) => -Math.PI + 0.085 + Math.max(0, 4 - Math.max(spread - 1 - leaf, 0)) * 0.014;
      // abierto, el libro se desplaza media tapa para centrar el pliego
      rig.motion.position.x = damp(rig.motion.position.x, rig.base.width * 0.5 * amount, speed, delta);

      rig.pagePivots.forEach((pagePivot, pageIndex) => {
        const leafOrder = rig.pagePivots.length - 1 - pageIndex;""",
)
rep(
    """        if (leafOrder < PAGINATED_LEAF_COUNT) {
          const isTurned = leafOrder < currentSpread;
          const unturnedTarget = -0.038 + leafOrder * 0.008;
          const turnedTarget = -Math.PI + 0.085 + leafOrder * 0.014;""",
    """        if (leafOrder < paginatedLeafCount) {
          const isTurned = leafOrder < currentSpread;
          const unturnedTarget = unturnedAt(leafOrder, isTurned ? leafOrder : currentSpread);
          const turnedTarget = turnedAt(leafOrder, isTurned ? currentSpread : leafOrder + 1);""",
)
rep(
    "          pageTarget = -0.006 + (leafOrder - PAGINATED_LEAF_COUNT) * 0.003;",
    "          pageTarget = -0.006 + (leafOrder - paginatedLeafCount) * 0.003;",
)

# the open spread (two pages wide) has to fit the view
rep(
    """    function getInspectScale() {
      if (!activeBook || viewWidth < 820) return 0.82;
      const distance = Math.abs(inspectCameraPosition.z - inspectPosition.z);
      const worldHeight = 2 * distance * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
      const pixelsPerWorld = viewHeight / Math.max(worldHeight, 0.001);
      const estimatedBookWidth = activeBook.base.width * pixelsPerWorld * 1.16;
      const scaleForSafeWidth = (detailSafeWidth * 0.72) / Math.max(estimatedBookWidth, 1);
      return clamp(scaleForSafeWidth, 0.9, 1.32);
    }""",
    """    function getInspectScale() {
      if (!activeBook) return 0.82;
      const distance = Math.abs(inspectCameraPosition.z - inspectPosition.z);
      const worldHeight = 2 * distance * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
      const pixelsPerWorld = viewHeight / Math.max(worldHeight, 0.001);
      const spreadWidth = activeBook.base.width * 2.12 * pixelsPerWorld;
      const spreadHeight = activeBook.base.height * 1.08 * pixelsPerWorld;
      const scale = Math.min((detailSafeWidth * 0.94) / spreadWidth, (viewHeight * 0.78) / spreadHeight);
      return clamp(scale, 0.45, 1.32);
    }""",
)
# without the side panel the book is inspected in the middle of the view
rep(
    """      inspectPosition.set(narrow ? 0 : -2.25, narrow ? 2.3 : 1.56, narrow ? 0.15 : 0);
      inspectCameraPosition.set(narrow ? 0 : -0.52, narrow ? 2.46 : 1.78, narrow ? 5.7 : 5.25);""",
    """      inspectPosition.set(0, narrow ? 2.3 : 1.56, narrow ? 0.15 : 0);
      inspectCameraPosition.set(0, narrow ? 2.46 : 1.78, narrow ? 5.7 : 5.25);""",
)

rep(
    """      activeBook = bookRigs[selectedIndex];
      activeBook.contactShadow.visible = false;""",
    """      activeBook = bookRigs[selectedIndex];
      loadPlates(activeBook);
      activeBook.contactShadow.visible = false;""",
)
rep(
    """      shelfStage.attach(activeBook.root);
      snapRigToShelfSlot(activeBook, selectedIndex);""",
    """      shelfStage.attach(activeBook.root);
      unloadPlates(activeBook);
      snapRigToShelfSlot(activeBook, selectedIndex);""",
)

# --- Spanish UI copy -------------------------------------------------------------
rep(
    """    function getSpreadLabels(book) {
      return [
        "Title page",
        `${book.chapters[0]} · Plate`,
        `${book.chapters[1]} · Notes`,
        `${book.chapters[2]} · System`,
        "Colophon"
      ];
    }""",
    """    function getSpreadLabels(book) {
      return ["Portadilla", ...book.pages.map((_, index) => `Lámina ${index + 1}`)];
    }""",
)
rep('pageLabel.textContent = readingOpen ? labels[currentSpread] : "Closed";',
    'pageLabel.textContent = readingOpen ? labels[currentSpread] : "Cerrado";')
rep(': "Click book to open";', ': "Haz clic en el libro para abrirlo";')
rep('toggleBookButton.textContent = readingOpen ? "Close book" : "Open book";',
    'toggleBookButton.textContent = readingOpen ? "Cerrar" : "Abrir";')
rep(
    """        ? "Drag pages · Drag cover to close · Background to orbit"
        : "Drag cover or click once to open · Background to orbit";""",
    """        ? "Arrastra las páginas · Arrastra la tapa para cerrar · Arrastra el fondo para girar"
        : "Arrastra la tapa o haz clic para abrir · Arrastra el fondo para girar";""",
)
rep("? \"Previous sample page\"\n          : `Previous sample page: ${labels[currentSpread - 1]}`",
    "? \"Lámina anterior\"\n          : `Lámina anterior: ${labels[currentSpread - 1]}`")
rep("? \"Next sample page\"\n          : `Next sample page: ${labels[currentSpread + 1]}`",
    "? \"Lámina siguiente\"\n          : `Lámina siguiente: ${labels[currentSpread + 1]}`")
rep("counter.textContent = `${pad(selectedIndex + 1)} / ${pad(BOOKS.length)}`;",
    "counter.textContent = `${selectedIndex + 1} / ${BOOKS.length}`;")
rep('inspectButton.setAttribute("aria-label", `Open ${book.title}`);',
    'inspectButton.setAttribute("aria-label", `Abrir ${book.title}`);')
rep("pointerLabelIndex.textContent = `Volume ${pad(index + 1)}`;",
    "pointerLabelIndex.textContent = book.note;")
rep('button.setAttribute("aria-label", `Select volume ${index + 1}: ${book.title}`);',
    'button.setAttribute("aria-label", `Cuaderno ${index + 1}: ${book.title}`);')
rep("detailEyebrow.textContent = `Volume ${book.roman} · ${book.discipline}`;",
    "detailEyebrow.textContent = book.discipline;")

# --- hooks for URL routing -------------------------------------------------------------
rep(
    """      if (announce && activeBook && readingOpen) {
        liveRegion.textContent""",
    """      callbacks.onSpreadChange?.({ index: selectedIndex, open: readingOpen, spread: currentSpread });

      if (announce && activeBook && readingOpen) {
        liveRegion.textContent""",
)
rep(
    """      controls.update();
      updatePageControls(false);
      experience.classList.remove("is-opening");
      closeButton.focus({ preventScroll: true });
    }""",
    """      controls.update();
      if (pendingSpread !== null) {
        const spread = pendingSpread;
        pendingSpread = null;
        setReadingOpen(true, false);
        currentSpread = clamp(spread, 0, spreadCount() - 1);
      }
      updatePageControls(false);
      experience.classList.remove("is-opening");
      closeButton.focus({ preventScroll: true });
    }""",
)
rep(
    "    let openingViewOffsetX = 0;\n",
    "    let openingViewOffsetX = 0;\n    let pendingSpread = null;\n",
)
rep(
    """    dispose: disposeExperience,
  };""",
    """    // Drawing Talks: abrir un cuaderno (y una lámina) desde la URL
    openBook: (index, spread = null) => {
      if (!renderer) return;
      if (mode === "hero") {
        selectMarker(index, canvas);
        pendingSpread = spread;
        openDetail(canvas);
      } else if (mode === "detail" && activeBook === bookRigs[index]) {
        if (spread === null) setReadingOpen(false, false);
        else {
          if (!readingOpen) setReadingOpen(true, false);
          currentSpread = clamp(spread, 0, spreadCount() - 1);
          updatePageControls(false);
          requestFrame();
        }
      }
    },
    select: (index) => { if (mode === "hero" && renderer) selectMarker(index, canvas); },
    get mode() { return mode; },
    dispose: disposeExperience,
  };""",
)

# --- init: no cover atlas to decode --------------------------------------------------
rep(
    """      try {
        await coverAtlasImage.decode();
        coverAtlasReady = true;
      } catch (error) {
        coverAtlasReady = false;
      }
""",
    "",
)
rep('showFallback("The interactive Bookshelf collection could not be prepared.");',
    'showFallback("No se pudo preparar la estantería 3D.");')


# --- portadilla: solo el nombre ---------------------------------------------------
rep(
    "    function makeEndpaperTexture(book) {",
    """    function makeTitlePageTexture(book) {
      const canvas = document.createElement("canvas");
      canvas.width = 1024;
      canvas.height = 1536;
      const ctx = canvas.getContext("2d");
      const random = seededRandom(hashSeed(`${book.id}-title-page`) + book.seed);
      drawPaperSurface(ctx, canvas.width, canvas.height, random);
      ctx.fillStyle = "#2b2520";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const size = book.title.length > 18 ? 78 : 96;
      ctx.font = `400 ${size}px "Iowan Old Style", Baskerville, Georgia, serif`;
      const lines = [];
      book.title.split(/\\s+/).forEach((word) => {
        const last = lines[lines.length - 1];
        if (last && ctx.measureText(`${last} ${word}`).width < canvas.width * 0.72) lines[lines.length - 1] = `${last} ${word}`;
        else lines.push(word);
      });
      const lineHeight = size * 1.18;
      const top = canvas.height * 0.42 - ((lines.length - 1) * lineHeight) / 2;
      lines.forEach((line, index) => ctx.fillText(line, canvas.width / 2, top + index * lineHeight));
      const texture = configureCanvasTexture(new THREE.CanvasTexture(canvas), { anisotropy: 16 });
      texture.name = `${book.id}-title-page`;
      return texture;
    }

    function makeEndpaperTexture(book) {""",
)

# --- barniz UV selectivo: brilla solo la ilustración de la portada ---------------------
rep(
    """      canvasTexture.width = 768;
      canvasTexture.height = 1152;""",
    """      canvasTexture.width = 1024;
      canvasTexture.height = 1536;""",
)
rep(
    """      if (book.coverImage) {
        drawImageCover(ctx, book.coverImage, canvasTexture.width, canvasTexture.height);
""",
    """      if (book.coverImage) {
        drawImageCover(ctx, book.coverImage, canvasTexture.width, canvasTexture.height);
        book.spotUv = makeSpotUvMask(book.coverImage);
""",
)
rep(
    """    function makeFoilTexture(book) {
      // la portada""",
    """    // máscara del barniz: lo que se separa del color de fondo de la portada
    function makeSpotUvMask(image) {
      const width = 512;
      const height = 768;
      const source = document.createElement("canvas");
      source.width = width;
      source.height = height;
      const ctx = source.getContext("2d", { willReadFrequently: true });
      drawImageCover(ctx, image, width, height);
      const pixels = ctx.getImageData(0, 0, width, height);
      const data = pixels.data;
      let red = 0;
      let green = 0;
      let blue = 0;
      let samples = 0;
      const sample = (x, y) => {
        const index = (y * width + x) * 4;
        red += data[index];
        green += data[index + 1];
        blue += data[index + 2];
        samples += 1;
      };
      for (let x = 0; x < width; x += 4) { sample(x, 3); sample(x, height - 4); }
      for (let y = 0; y < height; y += 4) { sample(3, y); sample(width - 4, y); }
      red /= samples;
      green /= samples;
      blue /= samples;
      for (let index = 0; index < data.length; index += 4) {
        const distance = Math.hypot(data[index] - red, data[index + 1] - green, data[index + 2] - blue) / 441;
        const value = Math.round(clamp((distance - 0.14) / 0.16, 0, 1) * 255);
        data[index] = data[index + 1] = data[index + 2] = value;
        data[index + 3] = 255;
      }
      ctx.putImageData(pixels, 0, 0);
      const mask = document.createElement("canvas");
      mask.width = width;
      mask.height = height;
      const maskContext = mask.getContext("2d");
      maskContext.filter = "blur(1.2px)";
      maskContext.drawImage(source, 0, 0);
      const texture = configureCanvasTexture(new THREE.CanvasTexture(mask), { color: false, anisotropy: 8 });
      texture.name = "spot-uv-mask";
      return texture;
    }

    function makeFoilTexture(book) {
      // la portada""",
)
rep(
    """        roughness: 0.92,
        metalness: 0.035,
        clearcoat: 0.06,
        clearcoatRoughness: 0.72,""",
    """        roughness: 0.92,
        metalness: 0.035,
        clearcoat: book.spotUv ? 1 : 0.06,
        clearcoatMap: book.spotUv || null,
        clearcoatRoughness: book.spotUv ? 0.06 : 0.72,""",
)

# --- habitación: papel pintado envejecido, balda de roble con escuadras -------------------
rep_between(
    "    function addRoom() {",
    "    function addLights() {",
    """    const WALL_Z = -0.62;

    // UVs a escala real (tile = unidades de mundo por repetición) para la veta de la madera
    function applyBoxUVs(geometry, tile) {
      const position = geometry.getAttribute("position");
      const normal = geometry.getAttribute("normal");
      const uv = new Float32Array(position.count * 2);
      for (let index = 0; index < position.count; index += 1) {
        const ax = Math.abs(normal.getX(index));
        const ay = Math.abs(normal.getY(index));
        const az = Math.abs(normal.getZ(index));
        const x = position.getX(index);
        const y = position.getY(index);
        const z = position.getZ(index);
        let u;
        let v;
        if (ax >= ay && ax >= az) { u = z; v = y; }
        else if (ay >= az) { u = x; v = z; }
        else { u = x; v = y; }
        uv[index * 2] = u / tile;
        uv[index * 2 + 1] = v / tile;
      }
      geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
      return geometry;
    }

    // Paper006 (ambientCG, CC0) envejecido: manchas de té, cercos, puntitos y juntas de papel pintado
    function makeAgedWallpaper(image) {
      const size = 2048;
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = size;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(image, 0, 0, size, size);
      const random = seededRandom(hashSeed("drawing-talks-wallpaper"));
      // cada marca se dibuja en las 9 posiciones vecinas para que la textura siga siendo continua
      const tiled = (draw) => {
        for (let ox = -1; ox <= 1; ox += 1) {
          for (let oy = -1; oy <= 1; oy += 1) {
            ctx.save();
            ctx.translate(ox * size, oy * size);
            draw();
            ctx.restore();
          }
        }
      };
      const blot = (x, y, radius, stops) => tiled(() => {
        const gradient = ctx.createRadialGradient(x, y, radius * 0.08, x, y, radius);
        stops.forEach(([at, color]) => gradient.addColorStop(at, color));
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalCompositeOperation = "multiply";
      for (let stain = 0; stain < 28; stain += 1) {
        const alpha = 0.05 + random() * 0.12;
        blot(random() * size, random() * size, 90 + random() * 380, [
          [0, `rgba(150,104,56,${alpha})`],
          [0.7, `rgba(166,121,72,${alpha * 0.55})`],
          [1, "rgba(166,121,72,0)"]
        ]);
      }
      for (let ring = 0; ring < 3; ring += 1) {
        blot(random() * size, random() * size, 50 + random() * 150, [
          [0, "rgba(120,80,40,0)"],
          [0.8, "rgba(120,80,40,0)"],
          [0.9, "rgba(120,80,40,0.07)"],
          [1, "rgba(120,80,40,0)"]
        ]);
      }
      for (let spot = 0; spot < 900; spot += 1) {
        const x = random() * size;
        const y = random() * size;
        const radius = 0.6 + Math.pow(random(), 3) * 6;
        const alpha = 0.07 + random() * 0.22;
        tiled(() => {
          ctx.fillStyle = `rgba(122,78,38,${alpha})`;
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fill();
        });
      }
      ctx.globalCompositeOperation = "source-over";
      [0, size / 2, size].forEach((x) => {
        const seam = ctx.createLinearGradient(x - 7, 0, x + 7, 0);
        seam.addColorStop(0, "rgba(90,60,30,0)");
        seam.addColorStop(0.48, "rgba(90,60,30,0.13)");
        seam.addColorStop(0.6, "rgba(255,246,226,0.16)");
        seam.addColorStop(1, "rgba(90,60,30,0)");
        ctx.fillStyle = seam;
        ctx.fillRect(x - 7, 0, 14, size);
      });
      return canvas;
    }

    function loadRoomTextures(wallMaterial, oak) {
      const assets = callbacks.assets;
      if (!assets) return;
      const loader = new THREE.TextureLoader();
      const anisotropy = Math.min(16, renderer.capabilities.getMaxAnisotropy());
      const wallTile = 6;
      const load = (url, color) => new Promise((resolve) => {
        if (!url) {
          resolve(null);
          return;
        }
        loader.load(url, (texture) => {
          texture.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace;
          texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
          texture.anisotropy = anisotropy;
          resolve(texture);
        }, undefined, () => resolve(null));
      });

      Promise.all([
        load(assets.woodColor, true),
        load(assets.woodNormal),
        load(assets.woodRoughness)
      ]).then(([map, normalMap, roughnessMap]) => {
        if (destroyed) return;
        if (map) oak.map = map;
        if (normalMap) {
          oak.normalMap = normalMap;
          oak.normalScale = new THREE.Vector2(0.7, 0.7);
        }
        if (roughnessMap) {
          oak.roughnessMap = roughnessMap;
          oak.roughness = 0.95;
        }
        oak.needsUpdate = true;
        requestFrame();
      });

      new THREE.ImageLoader().load(assets.paperColor, (image) => {
        if (destroyed) return;
        const texture = configureCanvasTexture(new THREE.CanvasTexture(makeAgedWallpaper(image)));
        texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(34 / wallTile, 20 / wallTile);
        wallMaterial.map = texture;
        wallMaterial.needsUpdate = true;
        requestFrame();
      });
      load(assets.paperRoughness).then((texture) => {
        if (!texture || destroyed) return;
        texture.repeat.set(34 / wallTile, 20 / wallTile);
        wallMaterial.roughnessMap = texture;
        wallMaterial.roughness = 1;
        wallMaterial.needsUpdate = true;
        requestFrame();
      });
    }

    function addRoom() {
      // suelo fuera de cuadro: la balda cuelga de la pared empapelada
      const floor = createMesh(shared.plane, new THREE.MeshStandardMaterial({
        color: 0xd8c8aa,
        roughness: 0.92,
        metalness: 0
      }), "paper-floor", false, true);
      floor.scale.set(30, 20, 1);
      floor.rotation.x = -Math.PI * 0.5;
      floor.position.y = -7;
      scene.add(floor);

      const back = createMesh(shared.plane, new THREE.MeshStandardMaterial({
        color: 0xe9dfcb,
        roughness: 0.96,
        metalness: 0
      }), "aged-wallpaper", false, true);
      back.scale.set(34, 20, 1);
      back.position.set(0, 4, WALL_Z);
      scene.add(back);

      const oak = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        roughness: 0.62,
        metalness: 0,
        clearcoat: 0.3,
        clearcoatRoughness: 0.4,
        sheen: 0.1,
        sheenRoughness: 0.6
      });
      const shelfDepth = 1.16;
      const shelf = createMesh(
        applyBoxUVs(new RoundedBoxGeometry(17, 0.2, shelfDepth, 4, 0.03), 1.7),
        oak,
        "oak-shelf"
      );
      shelf.position.set(0, shelfBoardTop - 0.1, WALL_Z + shelfDepth * 0.5);
      shelfStage.add(shelf);

      // escuadras de hierro atornilladas a la pared
      const iron = new THREE.MeshStandardMaterial({ color: 0x24201d, roughness: 0.42, metalness: 0.75 });
      [-3.1, 3.1].forEach((x, index) => {
        const bracket = new THREE.Group();
        bracket.name = `shelf-bracket-${index}`;
        const plate = createMesh(new RoundedBoxGeometry(0.07, 0.78, 0.03, 2, 0.008), iron, "bracket-plate");
        plate.position.set(0, -0.39, 0.015);
        const arm = createMesh(new RoundedBoxGeometry(0.07, 0.03, 0.96, 2, 0.008), iron, "bracket-arm");
        arm.position.set(0, -0.015, 0.48);
        const braceLength = Math.hypot(0.68, 0.7);
        const brace = createMesh(new RoundedBoxGeometry(0.05, braceLength, 0.025, 2, 0.006), iron, "bracket-brace");
        brace.position.set(0, -0.35, 0.34);
        brace.rotation.x = Math.atan2(0.68, 0.7);
        bracket.add(plate, arm, brace);
        bracket.position.set(x, shelfBoardTop - 0.2, WALL_Z);
        shelfStage.add(bracket);
      });

      const shadowStrip = createMesh(shared.plane, new THREE.MeshBasicMaterial({
        color: 0x2f1d13,
        alphaMap: makeContactShadowTexture(),
        transparent: true,
        opacity: 0.22,
        depthWrite: false
      }), "shelf-contact-shadow", false, false);
      shadowStrip.scale.set(16, 0.85, 1);
      shadowStrip.rotation.x = -Math.PI * 0.5;
      shadowStrip.position.set(0, shelfBoardTop + 0.02, 0.06);
      shelfStage.add(shadowStrip);

      roomMaterials.floor = floor.material;
      roomMaterials.wall = back.material;
      roomMaterials.shelf = oak;
      roomMaterials.shelfDark = shared.walnutDark;
      roomMaterials.shadow = shadowStrip.material;
      loadRoomTextures(back.material, oak);
    }

""",
)
# la balda baja recta al inspeccionar (ya no hay fondo detrás de ella)
rep("const inspectShelfPosition = new THREE.Vector3(0, -4.2, -3);",
    "const inspectShelfPosition = new THREE.Vector3(0, -6.5, 0);")

# --- luz: foco cálido que baña la pared y sombras más suaves -------------------------------
rep("roomLights.hemisphere = new THREE.HemisphereLight(0xfff8e8, 0x5b4030, 0.56);",
    "roomLights.hemisphere = new THREE.HemisphereLight(0xfff8e8, 0x5b4030, 0.3);")
rep(
    "      const fill = new THREE.DirectionalLight(0xd8e3e7, 0.3);",
    """      // foco cálido sobre la balda: halo en el papel pintado y sombras de los libros en la pared
      const spot = new THREE.SpotLight(0xffd6a0, 26, 0, 0.58, 0.85, 1.4);
      spot.name = "wall-wash";
      spot.position.set(0.6, 5.8, 3.4);
      spot.target.position.set(0, 1.2, WALL_Z);
      spot.castShadow = true;
      spot.shadow.mapSize.set(2048, 2048);
      spot.shadow.bias = -0.0002;
      spot.shadow.normalBias = 0.02;
      spot.shadow.radius = 6;
      spot.shadow.camera.near = 1;
      spot.shadow.camera.far = 16;
      scene.add(spot, spot.target);
      roomLights.spot = spot;

      const fill = new THREE.DirectionalLight(0xd8e3e7, 0.3);""",
)
# no se puede girar hasta detrás de la pared
rep(
    "      controls.minPolarAngle = Math.PI * 0.24;",
    "      controls.minAzimuthAngle = -0.62;\n      controls.maxAzimuthAngle = 0.62;\n      controls.minPolarAngle = Math.PI * 0.24;",
)

rep("scene.environmentIntensity = 0.72;", "scene.environmentIntensity = 0.5;")

rep("controls.minPolarAngle = Math.PI * 0.24;", "controls.minPolarAngle = Math.PI * 0.34;")
rep("controls.maxPolarAngle = Math.PI * 0.76;", "controls.maxPolarAngle = Math.PI * 0.62;")

# --- calidad -----------------------------------------------------------------------
rep("texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());\n            texture.repeat.set(0.5, 1);",
    "texture.anisotropy = Math.min(16, renderer.capabilities.getMaxAnisotropy());\n            texture.repeat.set(0.5, 1);")

# --- color fiel a las láminas --------------------------------------------------------
# ACES satura y quema naranjas/rojos y aplasta blancos; Neutral (Khronos PBR Neutral) conserva el color base
rep("renderer.toneMapping = THREE.ACESFilmicToneMapping;\n      renderer.toneMappingExposure = 0.9;",
    "renderer.toneMapping = THREE.NeutralToneMapping;\n      renderer.toneMappingExposure = 0.82;")
# papel casi blanco: el tono crema teñía las láminas
rep("color: 0xeee6d7,", "color: 0xfbf8f2,")
# el brillo de tela velaba la portada
rep("        sheen: 0.26,\n        sheenRoughness: 0.78,", "        sheen: 0.06,\n        sheenRoughness: 0.78,")
rep("new THREE.RectAreaLight(0xffe8c2, 5.4, 4.8, 5.6)", "new THREE.RectAreaLight(0xffe8c2, 4.2, 4.8, 5.6)")

# la hoja está cosida: no gira en su plano (eso despegaba el canto del lomo);
# la torsión queda solo en la curvatura del papel, que vale 0 en el lomo
rep("""              pageTwistTarget = pageDrag.direction
                * dragEnvelope
                * (0.014 + pageDrag.verticalBias * 0.026);""",
    """              pageTwistTarget = 0;""")

# --- barniz UVI visible y libro que se puede girar ------------------------------------------
rep("    let detailBookHovered = false;\n",
    "    let detailBookHovered = false;\n    let flipped = false;\n    const spotUvTime = { value: 0 };\n")
rep("      readingOpen = false;\n      detailBookHovered = false;",
    "      readingOpen = false;\n      flipped = false;\n      detailBookHovered = false;", count=2)
rep("      readingOpen = open;\n      if (!readingOpen) currentSpread = 0;",
    "      readingOpen = open;\n      if (readingOpen && flipped) setFlipped(false);\n      if (!readingOpen) currentSpread = 0;")
rep("""        || currentSpread !== 0
      ) return null;""",
    """        || currentSpread !== 0
        || (flipped && !readingOpen)
      ) return null;""")
rep("""        if (!activeBookAtPointer()) return;
        event.preventDefault();
        setReadingOpen(true);
        return;""",
    """        if (!activeBookAtPointer()) return;
        event.preventDefault();
        if (flipped) setFlipped(false);
        else setReadingOpen(true);
        return;""")
rep("    function turnPage(direction) {",
    """    // dar la vuelta al libro cerrado para ver la contraportada
    function setFlipped(value) {
      if (mode !== "detail" || flipped === value || (value && readingOpen)) return;
      flipped = value;
      callbacks.onFlipChange?.(flipped);
      if (activeBook) {
        liveRegion.textContent = flipped
          ? `Contraportada de ${activeBook.data.title}.`
          : `Portada de ${activeBook.data.title}.`;
      }
      requestFrame();
    }

    function turnPage(direction) {""")
rep("      const delta = Math.min((time - lastTime) / 1000, 0.05);\n",
    "      const delta = Math.min((time - lastTime) / 1000, 0.05);\n      spotUvTime.value = time / 1000;\n")
# cerrado en detalle: el libro sigue un poco al puntero (el barniz brilla) y puede girarse
rep("      rig.motion.position.x = damp(rig.motion.position.x, rig.base.width * 0.5 * amount, speed, delta);\n",
    """      rig.motion.position.x = damp(rig.motion.position.x, rig.base.width * 0.5 * amount, speed, delta);
      const inDetail = mode === "detail";
      const followsPointer = inDetail
        && !readingOpen
        && !pageDrag.active
        && !reducedMotion
        && Math.abs(pointer.ndc.x) <= 1
        && Math.abs(pointer.ndc.y) <= 1;
      const turnSpeed = reducedMotion ? 1000 : 5.5;
      rig.motion.rotation.y = damp(
        rig.motion.rotation.y,
        (inDetail && flipped && !readingOpen ? Math.PI : 0) + (followsPointer ? pointer.ndc.x * 0.09 : 0),
        turnSpeed,
        delta
      );
      rig.motion.rotation.x = damp(rig.motion.rotation.x, followsPointer ? -pointer.ndc.y * 0.07 : 0, turnSpeed, delta);
""")
rep("""        sheen: 0.06,
        sheenRoughness: 0.78,
        transparent: true
      });""",
    """        sheen: 0.06,
        sheenRoughness: 0.78,
        transparent: true
      });
      if (book.spotUv) {
        // barniz UVI: un reflejo que recorre las zonas barnizadas al inclinar el libro
        coverArt.onBeforeCompile = (shader) => {
          shader.uniforms.spotUvTime = spotUvTime;
          shader.fragmentShader = shader.fragmentShader
            .replace("void main() {", "uniform float spotUvTime;\\nvoid main() {")
            .replace("#include <opaque_fragment>", `
#ifdef USE_CLEARCOATMAP
{
  // reflejo de una ventana de luz arriba a la izquierda: se mueve al inclinar el libro
  float varnish = texture2D( clearcoatMap, vClearcoatMapUv ).r;
  vec3 reflected = reflect( -normalize( vViewPosition ), normalize( vNormal ) );
  vec2 toLight = reflected.xy - vec2( -0.06 + sin( spotUvTime * 0.4 ) * 0.04, 0.07 );
  float across = dot( toLight, vec2( -0.7071, 0.7071 ) );
  float along = dot( toLight, vec2( 0.7071, 0.7071 ) );
  float glint = exp( -across * across / 0.0014 ) * exp( -along * along / 0.25 );
  float halo = exp( -dot( toLight, toLight ) / 0.03 );
  outgoingLight *= 1.0 - varnish * 0.1;
  outgoingLight += varnish * ( glint * 1.05 + halo * 0.18 ) * vec3( 1.0, 0.97, 0.92 );
}
#endif
#include <opaque_fragment>`);
        };
      }""")
rep("clearcoatRoughness: book.spotUv ? 0.06 : 0.72,", "clearcoatRoughness: book.spotUv ? 0.12 : 0.72,")
rep("""    select: (index) => { if (mode === "hero" && renderer) selectMarker(index, canvas); },""",
    """    select: (index) => { if (mode === "hero" && renderer) selectMarker(index, canvas); },
    flip: () => setFlipped(!flipped),
    get flipped() { return flipped; },""")
# contraportada: título, año, número de láminas e índice
rep_between("    function makeBackFoilTexture(book) {", "    function createMesh(", r"""    function makeBackFoilTexture(book) {
      const foilCanvas = document.createElement("canvas");
      foilCanvas.width = 1024;
      foilCanvas.height = 1536;
      const ctx = foilCanvas.getContext("2d");
      if (book.backImage) return configureCanvasTexture(new THREE.CanvasTexture(foilCanvas));
      ctx.scale(foilCanvas.width / 768, foilCanvas.height / 1152);
      const left = 68;
      const right = 700;
      const sans = (size) => `500 ${size}px Inter, "Helvetica Neue", Arial, sans-serif`;
      const serif = (size) => `400 ${size}px "Iowan Old Style", Baskerville, Georgia, serif`;
      const fit = (text, maxWidth) => {
        if (ctx.measureText(text).width <= maxWidth) return text;
        let cut = text;
        while (cut.length > 1 && ctx.measureText(`${cut}…`).width > maxWidth) cut = cut.slice(0, -1);
        return `${cut.trimEnd()}…`;
      };
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";

      ctx.font = sans(18);
      ctx.letterSpacing = "3px";
      ctx.fillText(`DRAWING TALKS  /  ${book.roman}`, left, 82);
      ctx.globalAlpha = 0.72;
      ctx.fillRect(left, 108, 176, 2);
      ctx.globalAlpha = 1;

      ctx.letterSpacing = "0px";
      let titleSize = 76;
      ctx.font = serif(titleSize);
      while (ctx.measureText(book.title).width > right - left && titleSize > 34) {
        titleSize -= 2;
        ctx.font = serif(titleSize);
      }
      ctx.fillText(book.title, left, 200);
      ctx.font = sans(20);
      ctx.letterSpacing = "2.6px";
      ctx.fillText(fit([book.year, book.place, book.discipline].filter(Boolean).join("  ·  ").toUpperCase(), right - left), left + 2, 246);
      ctx.globalAlpha = 0.5;
      ctx.fillRect(left, 282, right - left, 1.5);
      ctx.globalAlpha = 1;

      const talks = book.talks || [];
      const top = 345;
      const bottom = 1010;
      const lineHeight = Math.min(56, (bottom - top) / Math.max(1, talks.length));
      const fontSize = Math.max(16, Math.min(27, lineHeight * 0.6));
      talks.forEach((talk, index) => {
        const y = top + index * lineHeight;
        ctx.globalAlpha = 0.62;
        ctx.font = sans(Math.round(fontSize * 0.72));
        ctx.letterSpacing = "1.6px";
        ctx.fillText(String(index + 1).padStart(2, "0"), left, y);
        ctx.globalAlpha = 1;
        ctx.letterSpacing = "0px";
        ctx.font = serif(fontSize);
        ctx.fillText(fit(talk, right - left - 50), left + 50, y);
      });

      ctx.globalAlpha = 0.68;
      ctx.fillRect(left, 1040, right - left, 1.5);
      ctx.globalAlpha = 1;
      ctx.font = sans(15);
      ctx.letterSpacing = "2.6px";
      if (book.url) ctx.fillText(book.url.toUpperCase(), left, 1080);
      ctx.textAlign = "right";
      ctx.fillText("SKETCHNOTES · @OYABUN", right, 1080);

      return configureCanvasTexture(new THREE.CanvasTexture(foilCanvas));
    }

""")

rep("""        bumpScale: 0.016,
        roughness: 0.21,
        metalness: 0.9,
        clearcoat: 0.14,""", """        bumpScale: 0.006,
        roughness: 0.42,
        metalness: 0.3,
        clearcoat: 0.14,""")
# --- el grosor del bloque son las hojas reales: al pasar páginas, la derecha adelgaza y la izquierda crece
rep("""      const pageBlock = createMesh(pageGeometry, pageMaterial, `${book.id}-page-block`);
      pageBlock.position.x = 0.018;
      motion.add(pageBlock);""",
    """      const pageBlock = createMesh(pageGeometry, pageMaterial, `${book.id}-page-block`);
      pageBlock.position.x = 0.018;
      // hojas sin pasar (derecha, sobre la contratapa); se escala en z según las que quedan
      const rightStack = new THREE.Group();
      rightStack.name = `${book.id}-right-stack`;
      rightStack.add(pageBlock);
      motion.add(rightStack);""")
rep("        motion.add(signature);", "        rightStack.add(signature);")
rep("      motion.add(ribbon);", "      rightStack.add(ribbon);")
rep("      motion.add(foreEdge);", "      rightStack.add(foreEdge);")
rep("        motion.add(edge);\n      });", """        rightStack.add(edge);
      });

      // hojas ya pasadas (izquierda): van con la tapa delantera, sobre su cara interior
      const leftStack = new THREE.Group();
      leftStack.name = `${book.id}-left-stack`;
      const leftPageWidth = pageWidth - spineWidth * 0.42;
      [pageBlock, foreEdge].forEach((part) => {
        const copy = part.clone();
        copy.position.x += leftPageWidth * 0.5 - spineWidth * 0.65 - 0.018;
        leftStack.add(copy);
      });
      leftStack.visible = false;
      frontPivot.add(leftStack);""")
rep("""        plates,
        leafCount,
        root,""", """        plates,
        leafCount,
        pageDepth,
        board,
        rightStack,
        leftStack,
        stackTurned: 0,
        root,""")
# las hojas se apoyan en los bloques: sin abanico exagerado
rep("const unturnedAt = (leaf, spread) => -0.038 + Math.min(Math.max(leaf - spread, 0), 4) * 0.008;",
    "const unturnedAt = (leaf, spread) => -0.008 + Math.min(Math.max(leaf - spread, 0), 4) * 0.002;")
rep("const turnedAt = (leaf, spread) => -Math.PI + 0.085 + Math.max(0, 4 - Math.max(spread - 1 - leaf, 0)) * 0.014;",
    "const turnedAt = (leaf, spread) => -Math.PI + 0.06 + Math.max(0, 4 - Math.max(spread - 1 - leaf, 0)) * 0.003;")
rep("""      rig.pagePivots.forEach((pagePivot, pageIndex) => {
        const leafOrder = rig.pagePivots.length - 1 - pageIndex;
        let pageTarget = 0;""",
    """      // grosor de cada lado = hojas que tiene (una hoja = pageDepth / número de hojas)
      const sheet = rig.pageDepth / rig.pagePivots.length;
      rig.stackTurned = damp(rig.stackTurned, currentSpread * amount, speed, delta);
      const leftThickness = sheet * rig.stackTurned;
      const rightThickness = Math.max(sheet * 0.5, rig.pageDepth - leftThickness);
      rig.rightStack.scale.z = rightThickness / rig.pageDepth;
      rig.rightStack.position.z = (rightThickness - rig.pageDepth) * 0.5;
      rig.leftStack.visible = leftThickness > 0.0004;
      rig.leftStack.scale.z = Math.max(leftThickness, 0.0001) / rig.pageDepth;
      rig.leftStack.position.z = -(rig.board * 0.5 + leftThickness * 0.5 + 0.0008);
      const restOffset = rightThickness - rig.pageDepth;

      rig.pagePivots.forEach((pagePivot, pageIndex) => {
        const leafOrder = rig.pagePivots.length - 1 - pageIndex;
        const restZ = pagePivot.userData.restZ + restOffset;
        const turnedZ = pagePivot.userData.turnedZ + leftThickness;
        let pageTarget = 0;""")
a = s.index("      rig.pagePivots.forEach((pagePivot, pageIndex) => {\n        const leafOrder = rig.pagePivots.length - 1 - pageIndex;\n        const restZ")
b = s.index("    function selectMarker(", a)
body = s[a:b]
body = body.replace("const restZ = pagePivot.userData.restZ + restOffset;", "@@R@@").replace("const turnedZ = pagePivot.userData.turnedZ + leftThickness;", "@@T@@")
assert body.count("pagePivot.userData.restZ") >= 4 and body.count("pagePivot.userData.turnedZ") >= 3, (body.count("pagePivot.userData.restZ"), body.count("pagePivot.userData.turnedZ"))
body = body.replace("pagePivot.userData.restZ", "restZ").replace("pagePivot.userData.turnedZ", "turnedZ")
body = body.replace("@@R@@", "const restZ = pagePivot.userData.restZ + restOffset;").replace("@@T@@", "const turnedZ = pagePivot.userData.turnedZ + leftThickness;")
s = s[:a] + body + s[b:]

# --- pliegue: todas las hojas bajan al mismo punto del lomo (si no, entre las dos páginas asomaban otras)
rep("""        const curveTarget = amount > 0""",
    """        // caída hasta el lomo, en z local de la hoja (cos(giro) la anula a media vuelta)
        pagePivot.userData.flex.gutter = (spineZ - pagePivot.position.z) * Math.cos(pagePivot.rotation.y) * amount;
        const curveTarget = amount > 0""")
rep("""      const restOffset = rightThickness - rig.pageDepth;
""", """      const restOffset = rightThickness - rig.pageDepth;
      const spineZ = -rig.pageDepth * 0.5 + rightThickness - 0.004;
""")
rep("""      if (
        !settleImmediately
        && Math.abs(nextCurve - flex.curve) < 0.00001""",
    """      const gutter = flex.gutter || 0;
      if (
        !settleImmediately
        && Math.abs(gutter - (flex.appliedGutter || 0)) < 0.00001
        && Math.abs(nextCurve - flex.curve) < 0.00001""")
rep("""      flex.curve = nextCurve;
      flex.twist = nextTwist;""", """      flex.curve = nextCurve;
      flex.twist = nextTwist;
      flex.appliedGutter = gutter;""")
rep("""          const z = (
            nextCurve * shape * (1 + y * 0.14)
            + diagonalTwist
            + softRipple
          ) * direction;""", """          const gutterProgress = Math.min(1, mappedU / 0.16);
          const gutterShape = 1 - gutterProgress * gutterProgress * (3 - 2 * gutterProgress);
          const z = (
            nextCurve * shape * (1 + y * 0.14)
            + diagonalTwist
            + softRipple
            + gutter * gutterShape
          ) * direction;""")

# el libro abierto siempre opaco: si venía de un extremo de la estantería seguía medio fundido
rep("""      // grosor de cada lado = hojas que tiene""", """      if (rig.opacity < 1) {
        rig.opacity = reducedMotion ? 1 : Math.min(1, damp(rig.opacity, 1, 14, delta) + 0.002);
        rig.fadeMaterials.forEach((material) => {
          material.opacity = rig.opacity;
        });
        rig.contactShadow.material.opacity = rig.opacity * 0.24;
      }
      // grosor de cada lado = hojas que tiene""")

# --- abierto: la tapa izquierda baja al nivel de la contratapa y los bloques dejan libre el pliego
rep("""        rightStack,
        leftStack,
        stackTurned: 0,""", """        rightStack,
        leftStack,
        stackTurned: 0,
        frontRestZ: frontPivot.position.z,
        pageWidth,
        leafWidth: leftPageWidth,
        rightOuter: 0.018 + pageWidth * 0.5 + 0.002,
        leftOuter: pageWidth * 0.5 + 0.002 + leftPageWidth * 0.5 - spineWidth * 0.65,""")
rep("""      const restOffset = rightThickness - rig.pageDepth;
      const spineZ = -rig.pageDepth * 0.5 + rightThickness - 0.004;
""", """      const restOffset = rightThickness - rig.pageDepth;
      // el lomo se dobla: la tapa izquierda acaba a la altura de la contratapa
      const coverOpen = smoothstep(clamp(-rig.frontPivot.rotation.y / Math.PI, 0, 1));
      const coverDrop = (rig.base.depth + rig.board) * coverOpen;
      rig.frontPivot.position.z = rig.frontRestZ - coverDrop;
      // el pliego queda libre para que las hojas bajen al lomo sin que las tape el bloque
      const stackScale = 1 - (0.16 * rig.leafWidth * coverOpen) / rig.pageWidth;
      rig.rightStack.scale.x = stackScale;
      rig.rightStack.position.x = rig.rightOuter * (1 - stackScale);
      rig.leftStack.scale.x = stackScale;
      rig.leftStack.position.x = rig.leftOuter * (1 - stackScale);
      const spineZ = -rig.base.depth * 0.5 + 0.003;
""")
rep("const turnedZ = pagePivot.userData.turnedZ + leftThickness;", "const turnedZ = pagePivot.userData.turnedZ + leftThickness - coverDrop;")

# --- abierto, el lomo se aplana bajo el pliego (si no, asomaba entre las páginas)
rep("      const spineGeometry = new RoundedBoxGeometry(",
    "      const spineGroup = new THREE.Group();\n      spineGroup.name = `${book.id}-spine-group`;\n      motion.add(spineGroup);\n      const spineGeometry = new RoundedBoxGeometry(")
rep("      motion.add(spine);", "      spineGroup.add(spine);")
rep("      motion.add(spineFoil);", "      spineGroup.add(spineFoil);")
rep("      motion.add(spineLining);", "      spineGroup.add(spineLining);")
rep("        motion.add(headband);", "        spineGroup.add(headband);")
rep("""        frontRestZ: frontPivot.position.z,""", """        frontRestZ: frontPivot.position.z,
        spineGroup,""")
rep("""      const spineZ = -rig.base.depth * 0.5 + 0.003;
""", """      const spineZ = -rig.base.depth * 0.5 + 0.003;
      const spineExtent = rig.base.depth + rig.board * 1.88;
      const spineScale = 1 - 0.9 * coverOpen;
      rig.spineGroup.scale.z = spineScale;
      rig.spineGroup.position.z = -spineExtent * 0.5 * (1 - spineScale);
""")

# en el lomo cada hoja llega un pelo más abajo que la de encima: sin z-fighting entre hojas
rep("pagePivot.userData.flex.gutter = (spineZ - pagePivot.position.z) * Math.cos(pagePivot.rotation.y) * amount;",
    """const depthInStack = leafOrder < currentSpread ? currentSpread - 1 - leafOrder : leafOrder - currentSpread;
        pagePivot.userData.flex.gutter = (spineZ - depthInStack * 0.0012 - pagePivot.position.z) * Math.cos(pagePivot.rotation.y) * amount;""")

# --- centro: abierto, las hojas giran en el centro del lomo (antes quedaban a la derecha)
rep("""        frontRestZ: frontPivot.position.z,
        spineGroup,""", """        frontRestZ: frontPivot.position.z,
        spineGroup,
        hingeX: -width * 0.5 + spineWidth * 0.65,
        hingeShift: spineWidth * 0.65,""")
rep("""      rig.rightStack.position.x = rig.rightOuter * (1 - stackScale);
      rig.leftStack.scale.x = stackScale;
      rig.leftStack.position.x = rig.leftOuter * (1 - stackScale);""",
    """      rig.rightStack.position.x = rig.rightOuter * (1 - stackScale) - rig.hingeShift * coverOpen;
      rig.leftStack.scale.x = stackScale;
      rig.leftStack.position.x = rig.leftOuter * (1 - stackScale) + rig.hingeShift * coverOpen;""")
rep("""        const turnedZ = pagePivot.userData.turnedZ + leftThickness - coverDrop;""",
    """        const turnedZ = pagePivot.userData.turnedZ + leftThickness - coverDrop;
        pagePivot.position.x = rig.hingeX - rig.hingeShift * coverOpen;""")

# --- mural: wallpaper.* de la carpeta del cuaderno, sobre el papel pintado mientras está seleccionado
rep("""      back.position.set(0, 4, WALL_Z);
      scene.add(back);
""", """      back.position.set(0, 4, WALL_Z);
      scene.add(back);

      mural = createMesh(shared.plane, new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.94,
        metalness: 0,
        transparent: true,
        opacity: 0,
        depthWrite: false
      }), "notebook-wallpaper", false, true);
      mural.scale.set(MURAL_WIDTH, MURAL_HEIGHT, 1);
      mural.position.set(0, 4, WALL_Z + 0.003);
      mural.visible = false;
      scene.add(mural);
""")
rep("    function addRoom() {", r"""    // cubre toda la pared; la imagen se repite en espejo (sin costuras) cada MURAL_TILE de ancho
    const MURAL_WIDTH = 34;
    const MURAL_HEIGHT = 20;
    const MURAL_TILE = 6.5;
    let mural = null;
    const muralTextures = new Map();

    function muralTexture(book) {
      if (muralTextures.has(book.id)) return muralTextures.get(book.id);
      const image = book.wallpaperImage;
      const texture = new THREE.Texture(image);
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      const tileHeight = MURAL_TILE * image.naturalHeight / image.naturalWidth;
      texture.wrapS = texture.wrapT = THREE.MirroredRepeatWrapping;
      texture.repeat.set(MURAL_WIDTH / MURAL_TILE, MURAL_HEIGHT / tileHeight);
      // una baldosa entera centrada detrás de la balda
      texture.offset.set(0.5 - texture.repeat.x * 0.5, 0.5 - texture.repeat.y * 0.5 - (shelfBoardTop + 1.2 - 4) / tileHeight);
      texture.needsUpdate = true;
      muralTextures.set(book.id, texture);
      return texture;
    }

    function updateMural(delta) {
      if (!mural) return false;
      const book = BOOKS[selectedIndex];
      const wanted = book?.wallpaperImage ? book : null;
      const material = mural.material;
      const speed = reducedMotion ? 1000 : 5;
      if ((mural.userData.book || null) !== wanted) {
        // fundido de salida antes de cambiar de imagen
        material.opacity = damp(material.opacity, 0, speed * 1.8, delta);
        if (material.opacity < 0.02) {
          material.opacity = 0;
          mural.userData.book = wanted;
          material.map = wanted ? muralTexture(wanted) : null;
          material.needsUpdate = true;
        }
      } else if (wanted) {
        material.opacity = damp(material.opacity, 1, speed, delta);
      }
      mural.visible = material.opacity > 0.004;
      const target = wanted && mural.userData.book === wanted ? 1 : 0;
      return Math.abs(material.opacity - target) > 0.004;
    }

    function addRoom() {""")
rep("const themeIsMoving = updateTheme(delta);", "const themeIsMoving = updateTheme(delta) | updateMural(delta);")

# --- abierto, los bloques miden lo mismo que las hojas (antes asomaban por el canto)
rep("""        rightOuter: 0.018 + pageWidth * 0.5 + 0.002,""", """        rightOuter: 0.018 + pageWidth * 0.5 + 0.002,
        blockInner: 0.018 - pageWidth * 0.5,
        leftBlockShift: leftPageWidth * 0.5 - spineWidth * 0.65 - 0.018,
        pageHeight,""")
rep("""      const stackScale = 1 - (0.16 * rig.leafWidth * coverOpen) / rig.pageWidth;
      rig.rightStack.scale.x = stackScale;
      rig.rightStack.position.x = rig.rightOuter * (1 - stackScale) - rig.hingeShift * coverOpen;
      rig.leftStack.scale.x = stackScale;
      rig.leftStack.position.x = rig.leftOuter * (1 - stackScale) + rig.hingeShift * coverOpen;""",
"""      // tramo [inner, outer] del bloque -> del fin del pliego al canto de las hojas
      const blockSpan = rig.rightOuter - rig.blockInner;
      const openHinge = -rig.base.width * 0.5;
      const rightInner = lerp(rig.blockInner, openHinge + 0.16 * rig.leafWidth, coverOpen);
      const rightOuter = lerp(rig.rightOuter, openHinge + rig.leafWidth, coverOpen);
      const rightScale = (rightOuter - rightInner) / blockSpan;
      rig.rightStack.scale.x = rightScale;
      rig.rightStack.position.x = rightInner - rightScale * rig.blockInner;
      // la izquierda va en coordenadas de la tapa: las hojas ocupan [0, leafWidth] desde el lomo
      const leftScale = (0.84 * rig.leafWidth) / blockSpan;
      rig.leftStack.scale.x = leftScale;
      rig.leftStack.position.x = 0.16 * rig.leafWidth - leftScale * (rig.blockInner + rig.leftBlockShift);
      const heightScale = lerp(1, (rig.pageHeight - 0.014) / rig.pageHeight, coverOpen);
      rig.rightStack.scale.y = heightScale;
      rig.leftStack.scale.y = heightScale;""")
# tapas más finas
rep("      const board = 0.032;", "      const board = 0.018;")

# --- el eje de cada hoja queda clavado en el lomo; el cuerpo sube a su bloque según el giro
#     (antes el eje viajaba entre los dos bloques y a media vuelta la hoja se despegaba)
rep("""        pagePivot.userData.flex.gutter = (spineZ - depthInStack * 0.0012 - pagePivot.position.z) * Math.cos(pagePivot.rotation.y) * amount;""",
    """        const hingeZ = spineZ - depthInStack * 0.0012;
        const halfTurn = pagePivot.rotation.y * 0.5;
        const bodyLift = (restZ - hingeZ) * Math.cos(halfTurn) ** 2
          - (turnedZ - hingeZ) * Math.sin(halfTurn) ** 2;
        pagePivot.position.z = lerp(pagePivot.position.z, hingeZ, amount);
        pagePivot.userData.flex.gutter = bodyLift * amount;""")
rep("""            + gutter * gutterShape
          ) * direction;""", """            + gutter * (1 - gutterShape)
          ) * direction;""")

# --- pared por cuaderno: pattern.* en mosaico por toda la pared y wallpaper.* como mural centrado
rep_between("    // cubre toda la pared; la imagen se repite en espejo", "    function addRoom() {", r"""    // pattern: mosaico en espejo (sin costuras) por toda la pared, baldosas de PATTERN_TILE de ancho
    // wallpaper: una sola imagen escalada a la pared visible
    const WALL_WIDTH = 34;
    const WALL_HEIGHT = 20;
    const PATTERN_TILE = 6.5;
    const wallLayers = [];

    function layerTexture(image, tiled) {
      const texture = new THREE.Texture(image);
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      if (tiled) {
        const tileHeight = PATTERN_TILE * image.naturalHeight / image.naturalWidth;
        texture.wrapS = texture.wrapT = THREE.MirroredRepeatWrapping;
        texture.repeat.set(WALL_WIDTH / PATTERN_TILE, WALL_HEIGHT / tileHeight);
        // una baldosa entera centrada detrás de la balda
        texture.offset.set(
          0.5 - texture.repeat.x * 0.5,
          0.5 - texture.repeat.y * 0.5 - (shelfBoardTop + 1.2 - 4) / tileHeight
        );
      }
      texture.needsUpdate = true;
      return texture;
    }

    function addWallLayer(key, tiled, zOffset, renderOrder) {
      const material = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.94,
        metalness: 0,
        transparent: true,
        opacity: 0,
        depthWrite: false
      });
      const mesh = createMesh(shared.plane, material, `notebook-${key}`, false, true);
      if (tiled) {
        mesh.scale.set(WALL_WIDTH, WALL_HEIGHT, 1);
        mesh.position.set(0, 4, WALL_Z + zOffset);
      } else {
        mesh.position.set(0, 2, WALL_Z + zOffset);
      }
      mesh.visible = false;
      // orden fijo: si no, three.js las ordena por distancia y el patrón tapaba el mural
      mesh.renderOrder = renderOrder;
      scene.add(mesh);
      wallLayers.push({ key, tiled, mesh, book: null, textures: new Map() });
    }

    // el wallpaper cubre la pared que ve la cámara de la estantería (con margen para girar),
    // recortado tipo cover: sin repetir ni deformar
    function fitWallpaper(mesh, texture) {
      const distance = shelfCameraPosition.z - WALL_Z;
      const height = 2 * distance * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5)) * 1.1;
      const width = Math.max(height * camera.aspect, height) * 1.08;
      const centerY = shelfCameraPosition.y
        + (shelfCameraTarget.y - shelfCameraPosition.y) * distance / (shelfCameraPosition.z - shelfCameraTarget.z);
      mesh.scale.set(width, height, 1);
      mesh.position.y = centerY;
      const image = texture.image;
      const imageAspect = image.naturalWidth / image.naturalHeight;
      const wallAspect = width / height;
      if (imageAspect > wallAspect) {
        texture.repeat.set(wallAspect / imageAspect, 1);
      } else {
        texture.repeat.set(1, imageAspect / wallAspect);
      }
      texture.offset.set((1 - texture.repeat.x) * 0.5, (1 - texture.repeat.y) * 0.5);
    }

    function updateWallLayer(layer, delta) {
      const book = BOOKS[selectedIndex];
      const wanted = book?.[layer.key] ? book : null;
      const material = layer.mesh.material;
      const speed = reducedMotion ? 1000 : 5;
      if (layer.book !== wanted) {
        // fundido de salida antes de cambiar de imagen
        material.opacity = damp(material.opacity, 0, speed * 1.8, delta);
        if (material.opacity < 0.02) {
          material.opacity = 0;
          layer.book = wanted;
          if (wanted) {
            const image = wanted[layer.key];
            if (!layer.textures.has(wanted.id)) layer.textures.set(wanted.id, layerTexture(image, layer.tiled));
            material.map = layer.textures.get(wanted.id);
          } else {
            material.map = null;
          }
          material.needsUpdate = true;
        }
      } else if (wanted) {
        material.opacity = damp(material.opacity, 1, speed, delta);
      }
      if (!layer.tiled && material.map) fitWallpaper(layer.mesh, material.map);
      layer.mesh.visible = material.opacity > 0.004;
      const target = wanted && layer.book === wanted ? 1 : 0;
      return Math.abs(material.opacity - target) > 0.004;
    }

    function updateMural(delta) {
      return wallLayers.reduce((moving, layer) => updateWallLayer(layer, delta) || moving, false);
    }

""")
rep("""      mural = createMesh(shared.plane, new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.94,
        metalness: 0,
        transparent: true,
        opacity: 0,
        depthWrite: false
      }), "notebook-wallpaper", false, true);
      mural.scale.set(MURAL_WIDTH, MURAL_HEIGHT, 1);
      mural.position.set(0, 4, WALL_Z + 0.003);
      mural.visible = false;
      scene.add(mural);
""", """      // pattern.* queda en el JSON pero de momento no se usa
      addWallLayer("wallpaperImage", false, 0.006, -1);
""")

# sin marcapáginas
rep("      rightStack.add(ribbon);\n", "")
# --- wallpaper: sin recorte; se oscurece hacia los bordes (luz en el centro) y se funde con su
#     color medio oscurecido, que pinta el resto de la pared: al girar la cámara no hay corte
rep("""    function layerTexture(image, tiled) {
      const texture = new THREE.Texture(image);""", """    // color medio oscurecido: el tono de la pared fuera de la imagen
    function wallpaperShade(image) {
      const probe = document.createElement("canvas");
      probe.width = probe.height = 16;
      const ctx = probe.getContext("2d", { willReadFrequently: true });
      ctx.drawImage(image, 0, 0, 16, 16);
      const data = ctx.getImageData(0, 0, 16, 16).data;
      const sum = [0, 0, 0];
      for (let index = 0; index < data.length; index += 4) {
        sum[0] += data[index];
        sum[1] += data[index + 1];
        sum[2] += data[index + 2];
      }
      return sum.map((value) => Math.round((value / 256) * 0.38));
    }

    function makeWallpaperTexture(image) {
      const width = Math.min(2400, image.naturalWidth);
      const height = Math.round(width * image.naturalHeight / image.naturalWidth);
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(image, 0, 0, width, height);
      const [red, green, blue] = wallpaperShade(image);
      // viñeta: la luz cae en el centro, los bordes se apagan hacia el tono de la pared
      const radius = Math.hypot(width, height) * 0.5;
      const vignette = ctx.createRadialGradient(width * 0.5, height * 0.42, radius * 0.3, width * 0.5, height * 0.42, radius);
      vignette.addColorStop(0, `rgba(${red},${green},${blue},0)`);
      vignette.addColorStop(0.55, `rgba(${red},${green},${blue},0.28)`);
      vignette.addColorStop(1, `rgba(${red},${green},${blue},0.92)`);
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, width, height);
      // el último tramo funde del todo con el tono de la pared
      const feather = Math.round(Math.min(width, height) * 0.07);
      const edges = [
        [0, 0, feather, 0, 0, 0, feather, height],
        [width, 0, width - feather, 0, width - feather, 0, feather, height],
        [0, 0, 0, feather, 0, 0, width, feather],
        [0, height, 0, height - feather, 0, height - feather, width, feather]
      ];
      edges.forEach(([x0, y0, x1, y1, x, y, w, h]) => {
        const gradient = ctx.createLinearGradient(x0, y0, x1, y1);
        gradient.addColorStop(0, `rgb(${red},${green},${blue})`);
        gradient.addColorStop(1, `rgba(${red},${green},${blue},0)`);
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, w, h);
      });
      const texture = configureCanvasTexture(new THREE.CanvasTexture(canvas), { anisotropy: 8 });
      texture.userData.shade = new THREE.Color(`rgb(${red},${green},${blue})`);
      texture.userData.aspect = width / height;
      return texture;
    }

    function layerTexture(image, tiled) {
      if (!tiled) return makeWallpaperTexture(image);
      const texture = new THREE.Texture(image);""")
# fondo: el tono de la pared detrás de la imagen
rep("""      mesh.visible = false;
      // orden fijo: si no, three.js las ordena por distancia y el patrón tapaba el mural
      mesh.renderOrder = renderOrder;
      scene.add(mesh);
      wallLayers.push({ key, tiled, mesh, book: null, textures: new Map() });""",
"""      mesh.visible = false;
      // orden fijo: si no, three.js las ordena por distancia y el patrón tapaba el mural
      mesh.renderOrder = renderOrder;
      scene.add(mesh);
      let backdrop = null;
      if (!tiled) {
        backdrop = createMesh(shared.plane, new THREE.MeshStandardMaterial({
          color: 0x000000,
          roughness: 0.96,
          metalness: 0,
          transparent: true,
          opacity: 0,
          depthWrite: false
        }), `notebook-${key}-backdrop`, false, true);
        backdrop.scale.set(WALL_WIDTH, WALL_HEIGHT, 1);
        backdrop.position.set(0, 4, WALL_Z + zOffset * 0.5);
        backdrop.renderOrder = renderOrder - 0.5;
        backdrop.visible = false;
        scene.add(backdrop);
      }
      wallLayers.push({ key, tiled, mesh, backdrop, book: null, textures: new Map() });""")
rep("""      if (!layer.tiled && material.map) fitWallpaper(layer.mesh, material.map);
      layer.mesh.visible = material.opacity > 0.004;""", """      if (!layer.tiled && material.map) fitWallpaper(layer.mesh, material.map);
      layer.mesh.visible = material.opacity > 0.004;
      if (layer.backdrop) {
        if (material.map) layer.backdrop.material.color.copy(material.map.userData.shade);
        layer.backdrop.material.opacity = material.opacity;
        layer.backdrop.visible = layer.mesh.visible;
      }""")
# encajar sin recortar: el plano mantiene la proporción de la imagen y cubre la vista
rep("""      mesh.scale.set(width, height, 1);
      mesh.position.y = centerY;
      const image = texture.image;
      const imageAspect = image.naturalWidth / image.naturalHeight;
      const wallAspect = width / height;
      if (imageAspect > wallAspect) {
        texture.repeat.set(wallAspect / imageAspect, 1);
      } else {
        texture.repeat.set(1, imageAspect / wallAspect);
      }
      texture.offset.set((1 - texture.repeat.x) * 0.5, (1 - texture.repeat.y) * 0.5);""",
"""      // sin recortar: el plano conserva la proporción y lo sobrante (con el fundido) cae fuera de la vista
      const aspect = texture.userData.aspect;
      const planeWidth = Math.max(width, height * aspect) * 1.08;
      mesh.scale.set(planeWidth, planeWidth / aspect, 1);
      mesh.position.y = centerY;""")

# --- pósters satinados pegados a la pared, relieve del wallpaper y luz rasante
rep("""    function layerTexture(image, tiled) {
      if (!tiled) return makeWallpaperTexture(image);""", r"""    // relieve del yeso: la luminancia de la imagen sin el color de fondo (grietas y desconchones más oscuros)
    function makeWallBumpTexture(image) {
      const width = Math.min(1600, image.naturalWidth);
      const height = Math.round(width * image.naturalHeight / image.naturalWidth);
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.filter = "grayscale(1) contrast(1.6)";
      ctx.drawImage(image, 0, 0, width, height);
      // resta la versión borrosa: queda solo el detalle fino, no las manchas grandes de color
      ctx.filter = "grayscale(1) contrast(1.6) blur(10px) invert(1)";
      ctx.globalAlpha = 0.5;
      ctx.drawImage(image, 0, 0, width, height);
      return configureCanvasTexture(new THREE.CanvasTexture(canvas), { color: false, anisotropy: 8 });
    }

    // papel encolado: ondulaciones suaves y algo de grano; uno para todos los pósters
    let posterBumpTexture = null;
    function getPosterBumpTexture() {
      if (posterBumpTexture) return posterBumpTexture;
      const canvas = document.createElement("canvas");
      canvas.width = 256;
      canvas.height = 384;
      const ctx = canvas.getContext("2d");
      const random = seededRandom(hashSeed("poster-paper"));
      ctx.fillStyle = "#808080";
      ctx.fillRect(0, 0, 256, 384);
      ctx.filter = "blur(14px)";
      for (let blob = 0; blob < 26; blob += 1) {
        const shade = 100 + random() * 60;
        ctx.fillStyle = `rgb(${shade},${shade},${shade})`;
        ctx.beginPath();
        ctx.ellipse(random() * 256, random() * 384, 10 + random() * 40, 6 + random() * 22, random() * Math.PI, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.filter = "none";
      for (let grain = 0; grain < 5000; grain += 1) {
        const shade = 110 + random() * 40;
        ctx.fillStyle = `rgba(${shade},${shade},${shade},0.35)`;
        ctx.fillRect(random() * 256, random() * 384, 1, 1);
      }
      posterBumpTexture = configureCanvasTexture(new THREE.CanvasTexture(canvas), { color: false, anisotropy: 8 });
      return posterBumpTexture;
    }

    // sombra de contacto: la silueta del póster, borrosa
    function makePosterShadowTexture(image) {
      const canvas = document.createElement("canvas");
      canvas.width = 160;
      canvas.height = Math.round(160 * image.naturalHeight / image.naturalWidth);
      const ctx = canvas.getContext("2d");
      ctx.filter = "blur(3px) brightness(0)";
      ctx.drawImage(image, 6, 6, canvas.width - 12, canvas.height - 12);
      return configureCanvasTexture(new THREE.CanvasTexture(canvas), { anisotropy: 1 });
    }

    // huecos alrededor de la balda: [x, y, alto, giro en grados]; info.json "posters" puede fijarlos
    const POSTER_SLOTS = [
      [-3.1, 2.75, 2.3, -2.2],
      [3.15, 2.85, 2.2, 1.6],
      [-5.5, 1.95, 2.5, 1.2],
      [5.6, 1.75, 2.4, -1.4],
      [-1.25, 3.05, 1.5, 0.8],
      [1.35, 3.0, 1.45, -0.9],
      [-2.5, -1.25, 1.9, 1.5],
      [2.6, -1.3, 1.9, -1.1],
      [-7.7, 2.4, 2.3, -0.8],
      [7.8, 2.2, 2.3, 1]
    ];

    function buildPosters(book) {
      const group = new THREE.Group();
      group.name = `${book.id}-posters`;
      (book.posters || []).forEach((poster, index) => {
        const slot = POSTER_SLOTS[index % POSTER_SLOTS.length];
        const lap = Math.floor(index / POSTER_SLOTS.length);
        const x = poster.x ?? slot[0] + lap * 0.4;
        const y = poster.y ?? slot[1] - lap * 0.3;
        const height = poster.alto ?? slot[2];
        const turn = THREE.MathUtils.degToRad(poster.giro ?? slot[3]);
        const width = height * poster.image.naturalWidth / poster.image.naturalHeight;
        const map = new THREE.Texture(poster.image);
        map.colorSpace = THREE.SRGBColorSpace;
        map.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        map.needsUpdate = true;
        // satinado: algo de brillo y una capa de barniz que refleja la luz rasante
        const material = new THREE.MeshPhysicalMaterial({
          map,
          bumpMap: getPosterBumpTexture(),
          bumpScale: 1.4,
          roughness: 0.42,
          metalness: 0,
          clearcoat: 0.45,
          clearcoatRoughness: 0.32,
          transparent: true,
          alphaTest: 0.35,
          opacity: 0,
          depthWrite: false
        });
        const mesh = createMesh(shared.plane, material, `${book.id}-${poster.name}`, false, true);
        mesh.scale.set(width, height, 1);
        mesh.position.set(x, y, WALL_Z + 0.012 + index * 0.0006);
        mesh.rotation.z = turn;
        mesh.renderOrder = -0.8;
        const shadow = createMesh(shared.plane, new THREE.MeshBasicMaterial({
          map: makePosterShadowTexture(poster.image),
          transparent: true,
          opacity: 0,
          depthWrite: false
        }), `${book.id}-${poster.name}-shadow`, false, false);
        shadow.scale.set(width * 1.04, height * 1.04, 1);
        shadow.position.set(x + 0.025, y - 0.035, WALL_Z + 0.009 + index * 0.0006);
        shadow.rotation.z = turn;
        shadow.renderOrder = -0.85;
        shadow.userData.shadowStrength = 0.42;
        group.add(shadow, mesh);
      });
      scene.add(group);
      return group;
    }

    function disposePosters(group) {
      if (!group) return;
      group.traverse((child) => {
        if (!child.isMesh) return;
        child.material.map?.dispose();
        child.material.dispose();
      });
      scene.remove(group);
    }

    function layerTexture(image, tiled) {
      if (!tiled) return makeWallpaperTexture(image);""")
# el wallpaper lleva relieve
rep("""      const texture = configureCanvasTexture(new THREE.CanvasTexture(canvas), { anisotropy: 8 });
      texture.userData.shade = new THREE.Color(`rgb(${red},${green},${blue})`);""",
"""      const texture = configureCanvasTexture(new THREE.CanvasTexture(canvas), { anisotropy: 8 });
      texture.userData.bump = makeWallBumpTexture(image);
      texture.userData.shade = new THREE.Color(`rgb(${red},${green},${blue})`);""")
rep("""            material.map = layer.textures.get(wanted.id);""",
"""            material.map = layer.textures.get(wanted.id);
            if (!layer.tiled) {
              material.bumpMap = material.map.userData.bump;
              material.bumpScale = 2.2;
            }""")
rep("""          } else {
            material.map = null;
          }
          material.needsUpdate = true;""", """          } else {
            material.map = null;
            material.bumpMap = null;
          }
          material.needsUpdate = true;""")
rep("""      layer.mesh.visible = material.opacity > 0.004;
      if (layer.backdrop) {""", """      layer.mesh.visible = material.opacity > 0.004;
      if (!layer.tiled) updatePosters(layer, delta);
      if (layer.backdrop) {""")
rep("""    function updateWallLayer(layer, delta) {
      const book = BOOKS[selectedIndex];
      const wanted = book?.[layer.key] ? book : null;""", """    // los pósters se muestran aunque el cuaderno no tenga wallpaper
    function updatePosters(layer, delta) {
      const book = BOOKS[selectedIndex];
      const wanted = book?.posters?.length ? book : null;
      const speed = reducedMotion ? 1000 : 5;
      if (layer.posterBook !== wanted) {
        layer.posterOpacity = damp(layer.posterOpacity || 0, 0, speed * 1.8, delta);
        if (layer.posterOpacity < 0.02) {
          layer.posterOpacity = 0;
          disposePosters(layer.posters);
          layer.posters = wanted ? buildPosters(wanted) : null;
          layer.posterBook = wanted;
        }
      } else if (wanted) {
        layer.posterOpacity = damp(layer.posterOpacity || 0, 1, speed, delta);
      }
      layer.posters?.traverse((child) => {
        if (!child.isMesh) return;
        child.material.opacity = layer.posterOpacity * (child.userData.shadowStrength ?? 1);
        child.visible = layer.posterOpacity > 0.004;
      });
      return Math.abs(layer.posterOpacity - (wanted && layer.posterBook === wanted ? 1 : 0)) > 0.004;
    }

    function updateWallLayer(layer, delta) {
      const book = BOOKS[selectedIndex];
      const wanted = book?.[layer.key] ? book : null;""")
# luz rasante desde la izquierda: hace visible el relieve y mueve el brillo de los pósters
rep("""      const fill = new THREE.DirectionalLight(0xd8e3e7, 0.3);""", """      const rake = new THREE.SpotLight(0xfff1dc, 32, 0, 0.62, 1, 1.2);
      rake.name = "wall-rake";
      rake.position.set(-9.5, 3.4, WALL_Z + 1.1);
      rake.target.position.set(0, 1.8, WALL_Z);
      scene.add(rake, rake.target);
      roomLights.rake = rake;

      const fill = new THREE.DirectionalLight(0xd8e3e7, 0.3);""")

assert "COVER_CROPS" not in s and "coverAtlas" not in s and "SPREAD_COUNT" not in s and "PAGINATED_LEAF_COUNT" not in s
open(OUT, "w").write(s)
print("ok", len(s))
