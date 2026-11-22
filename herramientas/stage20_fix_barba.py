#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE20 — Relleno de grietas en Male FacialHair3 (Full Beard).
Fecha: 2026-11-22. Orden: Stiven («barrido completo... arregla uno por uno»).

La barba completa traia grietas internas casi transparentes (alfa ~40-70)
que dejaban ver la piel: se veian como una curva clara pintada dentro de
la barba («barba muy extrana con mechones»). La grieta principal es una
curva de 510 px en x403-507, y891-934; hay otra horizontal en y827-832 y
varios agujeros pequenos. Cada grieta se rellena con la mediana del color
de la barba opaca en un radio de 15 px y alfa 255. Fuera de las grietas
no cambia ningun pixel (verificado por assert).

NO se toca la grieta superior (514 px, x304-456, y737-798): es el hueco
entre el bigote y la barba, por donde debe verse la piel. Tampoco se toca
el borde exterior (franja antialias) ni el agujero de la boca.
El borde superior en punta es la textura dibujada de la barba, no un error.

Originales en versiones/2026-11-22_stage20-antes-fragmentos/Male/FacialHair3.png
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'version-linux'))
import motor

# Grietas identificadas por (tam, x0, x1, y0, y1), componentes de
# (alfa<100) dentro de la silueta rellena de la barba.
GRIETAS = [(510, 403, 507, 891, 934), (94, 374, 400, 900, 921),
           (78, 357, 389, 827, 832), (56, 325, 350, 827, 830),
           (75, 530, 545, 963, 980), (37, 520, 529, 977, 987),
           (18, 321, 321, 874, 891), (18, 317, 319, 921, 936),
           (16, 559, 563, 748, 756), (14, 323, 323, 831, 844),
           (10, 506, 508, 937, 940), (8, 320, 320, 937, 944),
           (8, 340, 340, 980, 987), (8, 672, 675, 881, 884)]


def main():
    ruta = os.path.join(BASE, 'version-linux', 'assets', 'Male', 'FacialHair3.png')
    orig = np.asarray(Image.open(ruta).convert('RGBA')).astype(np.uint8)
    a = motor.capa('Male', 'FacialHair3')
    al = a[..., 3].astype(float)
    relleno = ndimage.binary_fill_holes(al > 30)
    interior = relleno & (al < 100)
    lab, n = ndimage.label(interior)
    comps = {}
    for i in range(1, n + 1):
        m = lab == i
        s = int(m.sum())
        if s >= 8:
            ys, xs = np.where(m)
            comps[(s, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))] = m
    nuevo = orig.copy().astype(float)
    total = 0
    for t in GRIETAS:
        if t not in comps:
            print(f'  AVISO: grieta no encontrada (ya rellenada?): {t}')
            continue
        m = comps[t]
        dil = ndimage.binary_dilation(m, iterations=15)
        vecinos = dil & (al > 200) & ~m
        color = np.median(orig[vecinos][:, :3], axis=0)
        nuevo[m, :3] = color
        nuevo[m, 3] = 255
        total += int(m.sum())
        print(f'  grieta {t}: rellenada con {color.round(0)}')
    fuera = np.ones(al.shape, bool)
    for t in GRIETAS:
        if t in comps:
            fuera &= ~comps[t]
    assert (nuevo[fuera].astype(np.uint8) == orig[fuera]).all(), 'cambio fuera de la zona'
    Image.fromarray(nuevo.astype(np.uint8)).save(ruta)
    print(f'FH3: {total} px rellenados')


if __name__ == '__main__':
    main()
