#!/usr/bin/env python3
"""TANDA 22 — Fase 3: inpaint + oscurecido de motitas.

- Hair10_Front: inpaint de los huecos con piel (C3-1: 3 huecos ~371 px;
  C3-2: 3 huecos ~202 px) con color de pelo vecino (difusión de Laplace,
  300 iter, como T19b). Solo se rellenan huecos INTERIORES (dentro de
  la silueta rellena de la capa); nada exterior.
- Hair10_Front: oscurecido de motitas claras aisladas del moño (C3-3):
  clusters lum>170 y alfa>200 en y<420 con tamaño <=30 px -> blend 85%
  hacia la mediana local del pelo oscuro. Los trazos de brillo
  continuos (clusters grandes) NO se tocan.
- Outfit3: inpaint del agujerito (586,1034)-(590,1044), 32 px, con color
  de prenda vecino, alfa 255.
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.expanduser("~/workspace/anime-portrait-studio/version-linux/assets/Female")


def load(nombre):
    ruta = os.path.join(BASE, nombre + ".png")
    return np.array(Image.open(ruta).convert("RGBA")).astype(np.int32), ruta


def save(a, ruta):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(ruta)


def laplace_inpaint(a, mask, iters=300):
    """Rellena `mask` (bool) por difusión desde los vecinos opacos.
    Devuelve RGB de relleno (float)."""
    h, w = mask.shape
    known = ~mask
    filled = np.zeros((h, w, 3), dtype=float)
    for c in range(3):
        vals = np.where(known, a[..., c].astype(float), 0.0)
        wsum = np.where(known, 1.0, 0.0)
        cur = vals.copy()
        for _ in range(iters):
            avg = (np.roll(cur, 1, 0) + np.roll(cur, -1, 0)
                   + np.roll(cur, 1, 1) + np.roll(cur, -1, 1)) / 4.0
            wavg = (np.roll(wsum, 1, 0) + np.roll(wsum, -1, 0)
                    + np.roll(wsum, 1, 1) + np.roll(wsum, -1, 1)) / 4.0
            new = np.where(wavg > 0, avg / np.maximum(wavg, 1e-9), cur)
            cur = np.where(mask, new, vals)
            wsum = np.where(mask, np.minimum(wavg, 1.0), wsum)
        filled[..., c] = cur
    return filled


# ---------------------------------------------------------------- Hair10_Front
a, ruta = load("Hair10_Front")
sil = ndimage.binary_fill_holes(a[..., 3] > 200)
huecos = [(317, 332, 333, 354), (338, 332, 354, 362), (351, 340, 359, 354),
          (516, 339, 523, 353), (563, 326, 579, 344), (587, 329, 594, 341)]
mask = np.zeros(a.shape[:2], dtype=bool)
for (x0, y0, x1, y1) in huecos:
    sub_al = a[y0:y1 + 1, x0:x1 + 1, 3]
    sub_sil = sil[y0:y1 + 1, x0:x1 + 1]
    m = (sub_al < 50) & sub_sil
    mask[y0:y1 + 1, x0:x1 + 1] |= m
n = int(mask.sum())
print(f"  Hair10_Front huecos interiores a rellenar: {n} px")
fill = laplace_inpaint(a, mask)
a[mask] = np.concatenate([fill[mask], np.full((n, 1), 255.0)], axis=1)
print("  Hair10_Front huecos rellenados (Laplace)")
# motitas claras aisladas del moño
lum = a[..., :3].max(axis=2)
cand = (lum > 170) & (a[..., 3] > 200) & (np.arange(1600)[:, None] < 420)
lab, nc = ndimage.label(cand)
sizes = ndimage.sum_labels(np.ones_like(lab), lab, range(1, nc + 1))
tot = 0
for cid in range(1, nc + 1):
    if sizes[cid - 1] > 30:
        continue
    m = lab == cid
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    # mediana local del pelo oscuro en un anillo de 7 px
    ring = np.zeros_like(m)
    ring[max(0, y0 - 7):y1 + 8, max(0, x0 - 7):x1 + 8] = True
    ring &= ~ndimage.binary_dilation(m, iterations=7)
    sel = ring & (a[..., 3] > 200) & (a[..., :3].max(axis=2) < 120)
    if sel.sum() < 5:
        sel = ring & (a[..., 3] > 200)
    med = np.median(a[sel][..., :3], axis=0)
    a[m, :3] = (0.15 * a[m, :3] + 0.85 * med).astype(int)
    tot += int(m.sum())
print(f"  Hair10_Front motitas claras oscurecidas: {tot} px")
save(a, ruta)

# ---------------------------------------------------------------- Outfit3
a, ruta = load("Outfit3")
mask = np.zeros(a.shape[:2], dtype=bool)
sub_al = a[1034:1045, 586:591, 3]
m = sub_al < 50
mask[1034:1045, 586:591] |= m
n = int(mask.sum())
print(f"  Outfit3 agujerito a rellenar: {n} px")
fill = laplace_inpaint(a, mask)
a[mask] = np.concatenate([fill[mask], np.full((n, 1), 255.0)], axis=1)
save(a, ruta)

print("FASE 3 COMPLETA")
