# Anime Portrait Studio — Linux version

Layered 2D anime half-body portrait creator (Remainder Studios).
Runs locally in the browser: pick a character, hairstyle, outfit, eyes,
nose, mouth, facial hair and colors, and export a 1200×1600 PNG.

This repository holds the **Linux program** (the creator + the render
engine). The Unity package lives in Google Drive and is only updated on
request.

## Run it

```bash
cd version-linux
python3 servidor.py
```

Then open http://127.0.0.1:8765/ in the browser.

Requirements: Python 3, Pillow, numpy, scipy
(`pip install pillow numpy scipy` if missing).

## Contents

- `version-linux/` — the creator (`servidor.py`, `index.html`, `motor.py`),
  the full tester (`probar_todo.py`), the sample sheet (`hoja_muestras.py`)
  and the art layers in `assets/Female` (41 PNG) and `assets/Male` (26 PNG).
- `herramientas/` — production tools: layer extraction, the piece gate
  (`probar_todo.py`/`producir_pieza.py`), audits and the stage19 fixes.
- `docs/` — production standard and product specification.
- `VERSIONES.md` — changelog (Spanish).

## Catalog (stage19)

- Female: 12 hairstyles, 3 outfits, 5 eyes, 3 noses, 5 mouths
  = 2,700 piece combinations.
- Male: 4 hairstyles, 3 outfits, 5 eyes, 3 noses, 3 mouths,
  facial hair (None / Mustache / Stubble / Full Beard) = 2,160.
- Palettes: hair 24, skin 4, outfit 24, eye color 7.
- Single canvas 1200×1600 for every layer. Multiplicative tints; the nose
  follows the skin tint; eyes and mouth are never tinted (eye color comes
  from baked variants in Unity / HSV iris recolor in Linux).

## Version

Current: **stage19** (22 November 2026) + eye-tint fix in
`motor.guardar_png()` (the PNG export now applies the eye color, same as
the on-screen render). See `VERSIONES.md`.
