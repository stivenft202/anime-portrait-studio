#!/usr/bin/env python3
"""TANDA 22 — Fase 3b: corrección del inpaint de huecos de Hair10_Front.

La fase 3 solo rellenó los píxeles alfa<50 (197 px). Los huecos son en
realidad regiones SEMITRANSPARENTES PÁLIDAS (RGB ~135-145 frente a pelo
vecino ~52-57): la piel se ve a través de ellos y quedan como rayas
crema. La máscara correcta es alfa<200 dentro de cada caja del hueco;
se recolorean con Laplace desde el pelo opaco vecino y se ponen alfa 255.
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
    known = ~mask
    filled = np.zeros((a.shape[0], a.shape[1], 3), dtype=float)
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


a, ruta = load("Hair10_Front")
huecos = [(317, 332, 333, 354), (338, 332, 354, 362), (351, 340, 359, 354),
          (516, 339, 523, 353), (563, 326, 579, 344), (587, 329, 594, 341)]
mask = np.zeros(a.shape[:2], dtype=bool)
for (x0, y0, x1, y1) in huecos:
    sub_al = a[y0:y1 + 1, x0:x1 + 1, 3]
    mask[y0:y1 + 1, x0:x1 + 1] |= (sub_al < 200)
n = int(mask.sum())
print(f"  Hair10_Front huecos (alfa<200) a rellenar: {n} px")
fill = laplace_inpaint(a, mask)
a[mask] = np.concatenate([fill[mask], np.full((n, 1), 255.0)], axis=1)
save(a, ruta)
print("FASE 3b COMPLETA")
