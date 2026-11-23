#!/usr/bin/env python3
"""SÚPER MÉTODO — defringe del halo blanco en los bordes de las 6 ropas.

Hallazgo Fase 4: la "línea clara" que Stiven circuló en 2d/2e NO es piel que
sobresalga (0 px de Base fuera de la ropa) sino píxeles BLANCOS
semi-transparentes (lum>200, alfa 20-210) en el borde exterior de la ropa:
artefacto de recorte sobre fondo blanco. Se recolorean con el color del
píxel opaco más cercano de la misma capa, conservando el alfa (la silueta
y el anti-aliasing no cambian). Tras la primera pasada quedó una línea
clara tenue formada por el fringe medio (lum 120-200, también claro
contra fondos oscuros), así que el umbral se amplió a lum>120: todo el
fringe claro exterior es halo, no degradado del borde (el degradado
normal de una chaqueta oscura sería rojo oscuro, no beige claro).
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.expanduser("~/workspace/anime-portrait-studio")
SNAP = os.path.join(BASE, "versiones/2026-11-23_supermetodo-antes")
ASSETS = os.path.join(BASE, "version-linux/assets")

# 1) snapshot previo de las ropas que el fix agent no tocó (Outfit2 M y
#    Outfit3 F ya están en el snapshot con su versión pre-fix)
for rel in ["Female/Outfit1.png", "Female/Outfit2.png",
            "Male/Outfit1.png", "Male/Outfit3.png"]:
    dst = os.path.join(SNAP, rel.replace("/", "_"))
    if not os.path.exists(dst):
        import shutil
        shutil.copy(os.path.join(ASSETS, rel), dst)
        print("snapshot añadido:", rel)

resultados = {}
for sexo in ["Female", "Male"]:
    for o in [1, 2, 3]:
        rel = f"{sexo}/Outfit{o}.png"
        p = os.path.join(ASSETS, rel)
        a = np.array(Image.open(p).convert("RGBA")).astype(int)
        alpha, rgb = a[..., 3], a[..., :3]
        lum = rgb.mean(axis=2)
        opaco = alpha > 200
        cerca = ndimage.binary_dilation(opaco, iterations=2) & ~opaco
        fringe = cerca & (alpha > 20) & (alpha < 210) & (lum > 120)
        n = int(fringe.sum())
        if n == 0:
            print(f"{rel}: 0 px blancos, sin cambios")
            resultados[rel] = 0
            continue
        # color del píxel opaco más cercano (distancia euclídea)
        _, inds = ndimage.distance_transform_edt(~opaco, return_indices=True)
        ny, nx = inds[0][fringe], inds[1][fringe]
        a[fringe, :3] = rgb[ny, nx]
        # asserts: solo cambian píxeles del fringe (algunos ya tenían el color
        # del vecino opaco y no cambian: dif <= n); alfa intacta.
        b = np.array(Image.open(p).convert("RGBA")).astype(int)
        assert np.array_equal(a[..., 3], b[..., 3]), "alfa cambió"
        dif = np.any(a != b, axis=2)
        assert int((dif & ~fringe).sum()) == 0, "cambios fuera del fringe"
        assert int(dif.sum()) <= n, f"dif {int(dif.sum())} > fringe {n}"
        Image.fromarray(a.astype("uint8"), "RGBA").save(p)
        resultados[rel] = n
        print(f"{rel}: defringe {n} px blancos")

print("total defringe:", sum(resultados.values()), "px")
