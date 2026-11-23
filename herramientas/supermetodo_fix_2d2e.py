#!/usr/bin/env python3
"""SÚPER MÉTODO — corrección 2d/2e: la piel de Base se transparenta por el
borde semitransparente de la ropa.

Causa real (medida): en y=1350, Base M es opaca (alfa 255) desde x=198,
mientras el borde OPACO de Outfit2 empieza en x=199; el píxel x=198 de la
ropa es negro con alfa 85, así que la piel se ve a través y forma la
"línea clara". El fix agent midió 0 px porque mi brief pedía la silueta
con alfa>0 (el fringe alfa 85 cuenta como "dentro"); el umbral visual
correcto es la silueta OPACA (alfa>200).

Fix: borrar (alfa=0) los píxeles de Base M que estén fuera de la silueta
opaca de Outfit2, solo dentro de las zonas 2d/2e y a <=3 px del borde
opaco. Snapshot: Base M ya está en versiones/2026-11-23_supermetodo-antes/
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.expanduser("~/workspace/anime-portrait-studio")
ASSETS = os.path.join(BASE, "version-linux/assets")

base_p = os.path.join(ASSETS, "Male/Base.png")
out_p = os.path.join(ASSETS, "Male/Outfit2.png")
b = np.array(Image.open(base_p).convert("RGBA")).astype(int)
o = np.array(Image.open(out_p).convert("RGBA")).astype(int)
orig = b.copy()

opaco = o[..., 3] > 200
# distancia a la silueta opaca (0 = dentro)
dist = ndimage.distance_transform_edt(~opaco)
zonas = [
    (slice(1290, 1481), slice(100, 261)),   # 2d
    (slice(1220, 1246), slice(1175, 1201)),  # 2e
]
mask = np.zeros((1600, 1200), dtype=bool)
for ys, xs in zonas:
    zona = np.zeros((1600, 1200), dtype=bool)
    zona[ys, xs] = True
    mask |= zona & (~opaco) & (dist <= 3) & (b[..., 3] > 0)
print("px de Base a borrar:", int(mask.sum()))
b[mask] = [0, 0, 0, 0]
dif = np.any(b != orig, axis=2)
assert int(dif.sum()) == int(mask.sum()), "cambios fuera de la máscara"
assert np.array_equal(b[..., :3][~mask], orig[..., :3][~mask])
Image.fromarray(b.astype("uint8"), "RGBA").save(base_p)
print("OK: Male/Base.png actualizado")
