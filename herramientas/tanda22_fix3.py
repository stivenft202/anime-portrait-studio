#!/usr/bin/env python3
"""TANDA 22 — Fase 2c: rehacer los borrados de pelo con umbral alfa>200
(igual que los analistas). La fase 2b usó alfa>10 y el polvo de
antialiasing se coló como cientos de micro-componentes; además los
fragmentos grandes quedaban fusionados a la masa por el halo y el
filtro de caja los rechazaba.

Pasos: restaurar las 3 capas desde el snapshot, re-aplicar el defringe
(idempotente: solo recolorea halo claro) y rehacer los borrados.
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.expanduser("~/workspace/anime-portrait-studio/version-linux/assets/Female")
SNAP = os.path.expanduser("~/workspace/anime-portrait-studio/versiones/2026-11-23_tanda22-antes")


def restore(nombre):
    src = os.path.join(SNAP, f"Female_{nombre}.png")
    dst = os.path.join(BASE, nombre + ".png")
    a = np.array(Image.open(src).convert("RGBA"))
    Image.fromarray(a).save(dst)
    print(f"  {nombre}: restaurada del snapshot")


def load(nombre):
    ruta = os.path.join(BASE, nombre + ".png")
    return np.array(Image.open(ruta).convert("RGBA")).astype(np.int32), ruta


def save(a, ruta):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(ruta)


def defringe(nombre):
    a, ruta = load(nombre)
    orig = a.copy()
    alpha = a[..., 3]
    lum = a[..., :3].max(axis=2)
    opaco = alpha > 200
    dil = ndimage.binary_dilation(opaco, iterations=2)
    halo = dil & (~opaco) & (alpha >= 20) & (alpha <= 200) & (lum > 120)
    n = int(halo.sum())
    if n:
        _, idx = ndimage.distance_transform_edt(~opaco, return_indices=True)
        ys, xs = np.where(halo)
        ny, nx = idx[0][ys, xs], idx[1][ys, xs]
        a[ys, xs, 0] = orig[ny, nx, 0]
        a[ys, xs, 1] = orig[ny, nx, 1]
        a[ys, xs, 2] = orig[ny, nx, 2]
    assert not (a[..., 3] != orig[..., 3]).any()
    save(a, ruta)
    print(f"  {nombre}: defringe {n} px")


def delete_components_in_box(a, box, nombre, tag, pad=3, thr=200):
    x0, y0, x1, y1 = box
    lab, _ = ndimage.label(a[..., 3] > thr)
    ids = set(np.unique(lab[y0:y1 + 1, x0:x1 + 1])) - {0}
    total = 0
    for cid in ids:
        ys, xs = np.where(lab == cid)
        if (xs.min() >= x0 - pad and xs.max() <= x1 + pad
                and ys.min() >= y0 - pad and ys.max() <= y1 + pad):
            m = lab == cid
            total += int(m.sum())
            a[m] = [0, 0, 0, 0]
    print(f"  {nombre} {tag}: borrados {total} px")
    return total


for nombre in ["Hair9_Front", "Hair10_Front", "Hair2_Front"]:
    restore(nombre)
    defringe(nombre)

# ---------------------------------------------------------------- Hair10_Front
a, ruta = load("Hair10_Front")
cajas = [
    ((315, 275, 332, 312), "frag id128 (esperado 105)"),
    ((292, 327, 306, 357), "frag id151 (esperado 103)"),
    ((871, 47, 907, 54), "frag sup id1 (esperado 113)"),
    ((909, 48, 919, 54), "frag sup id2 (esperado 28)"),
    ((917, 54, 928, 60), "frag sup id6 (esperado 39)"),
    ((1049, 451, 1087, 461), "frag id175 (esperado 160)"),
    ((355, 578, 368, 590), "frag id180 (esperado 75)"),
    ((695, 776, 701, 807), "frag id220 (esperado 75)"),
    ((393, 883, 405, 900), "frag id256 (esperado 37)"),
    ((1100, 439, 1105, 445), "frag id170 (esperado 15)"),
    ((685, 810, 692, 817), "frag id234 (esperado 15)"),
]
for box, tag in cajas:
    delete_components_in_box(a, box, "Hair10_Front", tag)
lab, n = ndimage.label(a[..., 3] > 200)
sizes = ndimage.sum_labels(np.ones_like(lab), lab, range(1, n + 1))
peq = [i + 1 for i, s in enumerate(sizes) if 0 < s <= 15]
tot = 0
for cid in peq:
    m = lab == cid
    tot += int(m.sum())
    a[m] = [0, 0, 0, 0]
print(f"  Hair10_Front motitas <=15px (alfa>200): borrados {tot} px en {len(peq)} comps")
save(a, ruta)

# ---------------------------------------------------------------- Hair9_Front
a, ruta = load("Hair9_Front")
lab, n = ndimage.label(a[..., 3] > 200)
sizes = ndimage.sum_labels(np.ones_like(lab), lab, range(1, n + 1))
mayor = int(np.argmax(sizes)) + 1
tot = 0
for cid in range(1, n + 1):
    if cid == mayor:
        continue
    m = lab == cid
    tot += int(m.sum())
    a[m] = [0, 0, 0, 0]
print(f"  Hair9_Front desprendidos (salvo masa {int(sizes[mayor-1])} px): "
      f"borrados {tot} px en {n-1} comps (esperado ~467 px en 15 comps)")
save(a, ruta)

# ---------------------------------------------------------------- Hair2_Front
a, ruta = load("Hair2_Front")
delete_components_in_box(a, (746, 558, 804, 620), "Hair2_Front", "frag id11 (esperado 220)")
delete_components_in_box(a, (313, 276, 331, 291), "Hair2_Front", "frag id2 (esperado 173)")
lab, n = ndimage.label(a[..., 3] > 200)
sizes = ndimage.sum_labels(np.ones_like(lab), lab, range(1, n + 1))
peq = [i + 1 for i, s in enumerate(sizes) if 0 < s <= 20]
tot = 0
for cid in peq:
    m = lab == cid
    tot += int(m.sum())
    a[m] = [0, 0, 0, 0]
print(f"  Hair2_Front motitas <=20px (alfa>200): borrados {tot} px en {len(peq)} comps")
save(a, ruta)

print("FASE 2c COMPLETA")
