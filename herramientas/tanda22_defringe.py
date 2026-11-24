#!/usr/bin/env python3
"""TANDA 22 — Fase 1: defringe de las capas de pelo.

Halo = píxeles semitransparentes (alfa 20-200) a <=2 px de la silueta
opaca (alfa>200) y claros (lum>120). Se recolorean al color del píxel
opaco más cercano, conservando el alfa (mismo método que el defringe
de ropas del súper método y de pelo de la Tanda 20).

Capas: Hair10_Front (halo 53.513 px), Hair9_Front (31.422 px),
Hair2_Front (7.569 px), Hair2_Back (11.853 px).
Solo se toca el halo; el resto de la capa queda byte-idéntico.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.expanduser("~/workspace/anime-portrait-studio/version-linux/assets/Female")

CAPAS = ["Hair10_Front", "Hair9_Front", "Hair2_Front", "Hair2_Back"]


def defringe(nombre):
    ruta = os.path.join(BASE, nombre + ".png")
    a = np.array(Image.open(ruta).convert("RGBA")).astype(np.int32)
    orig = a.copy()
    alpha = a[..., 3]
    lum = a[..., :3].max(axis=2)
    opaco = alpha > 200
    dil = ndimage.binary_dilation(opaco, iterations=2)
    halo = dil & (~opaco) & (alpha >= 20) & (alpha <= 200) & (lum > 120)
    n = int(halo.sum())
    if n:
        # color del opaco más cercano (distancia euclídea)
        _, idx = ndimage.distance_transform_edt(~opaco, return_indices=True)
        ys, xs = np.where(halo)
        ny, nx = idx[0][ys, xs], idx[1][ys, xs]
        a[ys, xs, 0] = orig[ny, nx, 0]
        a[ys, xs, 1] = orig[ny, nx, 1]
        a[ys, xs, 2] = orig[ny, nx, 2]
        # alfa se conserva
    # assert: solo cambian píxeles del halo en RGB; alfa intacto
    dif_rgb = (a[..., :3] != orig[..., :3]).any(axis=2)
    dif_alfa = a[..., 3] != orig[..., 3]
    assert not dif_alfa.any(), f"{nombre}: cambió el alfa"
    assert set(map(tuple, np.argwhere(dif_rgb))) <= set(map(tuple, np.argwhere(halo))), \
        f"{nombre}: cambios fuera del halo"
    Image.fromarray(a.astype(np.uint8)).save(ruta)
    print(f"{nombre}: halo recoloreado {n} px")
    return n


def main():
    total = 0
    for c in CAPAS:
        total += defringe(c)
    print(f"TOTAL defringe: {total} px")


if __name__ == "__main__":
    main()
