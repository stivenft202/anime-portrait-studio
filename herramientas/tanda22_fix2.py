#!/usr/bin/env python3
"""TANDA 22 — Fase 2b: continuación del fix (Hair7 sin re-afilado — la
gota colgaba de una hebra diagonal, no era la punta de una hebra; tras
borrarla no se dibuja nada).

Eyes x5, Nose1 y Eyes_Sad ya están aplicados por tanda22_fix.py.
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


def delete_in_box(a, box, nombre, tag, cond=None):
    x0, y0, x1, y1 = box
    sub = a[y0:y1 + 1, x0:x1 + 1]
    m = (sub[..., 3] > 0) if cond is None else cond(sub)
    n = int(m.sum())
    sub[m] = [0, 0, 0, 0]
    print(f"  {nombre} {tag}: borrados {n} px en caja {box}")
    return n


def delete_components_in_box(a, box, nombre, tag, pad=3):
    """Borra los componentes (alfa>10) cuya bbox cae dentro de la caja
    ampliada por `pad`."""
    x0, y0, x1, y1 = box
    lab, _ = ndimage.label(a[..., 3] > 10)
    ids = set(np.unique(lab[y0:y1 + 1, x0:x1 + 1])) - {0}
    total = 0
    for cid in ids:
        ys, xs = np.where(lab == cid)
        if (xs.min() >= x0 - pad and xs.max() <= x1 + pad
                and ys.min() >= y0 - pad and ys.max() <= y1 + pad):
            m = lab == cid
            total += int(m.sum())
            a[m] = [0, 0, 0, 0]
    print(f"  {nombre} {tag}: borrados {total} px ({len(ids)} comps en caja {box})")
    return total


# ---------------------------------------------------------------- Hair7_Front
a, ruta = load("Hair7_Front")
n1 = delete_in_box(a, (524, 900, 545, 956), "Hair7_Front", "gota barra")
n2 = delete_in_box(a, (548, 971, 555, 977), "Hair7_Front", "gota punto")
# guión trenza + micros (por caja)
delete_components_in_box(a, (1013, 533, 1017, 547), "Hair7_Front", "guion trenza")
delete_components_in_box(a, (360, 769, 362, 778), "Hair7_Front", "micro mandibula")
delete_components_in_box(a, (977, 298, 981, 307), "Hair7_Front", "micro pelo")
save(a, ruta)

# ---------------------------------------------------------------- Hair10_Front
a, ruta = load("Hair10_Front")
cajas = [
    ((315, 275, 332, 312), "frag id128"),
    ((292, 327, 306, 357), "frag id151"),
    ((871, 47, 907, 54), "frag sup id1"),
    ((909, 48, 919, 54), "frag sup id2"),
    ((917, 54, 928, 60), "frag sup id6"),
    ((1049, 451, 1087, 461), "frag id175"),
    ((355, 578, 368, 590), "frag id180"),
    ((695, 776, 701, 807), "frag id220"),
    ((393, 883, 405, 900), "frag id256"),
    ((1100, 439, 1105, 445), "frag id170"),
    ((685, 810, 692, 817), "frag id234"),
]
for box, tag in cajas:
    delete_components_in_box(a, box, "Hair10_Front", tag)
lab, n = ndimage.label(a[..., 3] > 10)
sizes = ndimage.sum_labels(np.ones_like(lab), lab, range(1, n + 1))
peq = [i + 1 for i, s in enumerate(sizes) if 0 < s <= 15]
tot = 0
for cid in peq:
    m = lab == cid
    tot += int(m.sum())
    a[m] = [0, 0, 0, 0]
print(f"  Hair10_Front motitas <=15px: borrados {tot} px en {len(peq)} comps")
save(a, ruta)

# ---------------------------------------------------------------- Hair9_Front
a, ruta = load("Hair9_Front")
lab, n = ndimage.label(a[..., 3] > 10)
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
      f"borrados {tot} px en {n-1} comps")
save(a, ruta)

# ---------------------------------------------------------------- Hair2_Front
a, ruta = load("Hair2_Front")
delete_components_in_box(a, (746, 558, 804, 620), "Hair2_Front", "frag id11 oreja")
delete_components_in_box(a, (313, 276, 331, 291), "Hair2_Front", "frag id2 linea pelo")
lab, n = ndimage.label(a[..., 3] > 10)
sizes = ndimage.sum_labels(np.ones_like(lab), lab, range(1, n + 1))
peq = [i + 1 for i, s in enumerate(sizes) if 0 < s <= 20]
tot = 0
for cid in peq:
    m = lab == cid
    tot += int(m.sum())
    a[m] = [0, 0, 0, 0]
print(f"  Hair2_Front motitas <=20px: borrados {tot} px en {len(peq)} comps")
save(a, ruta)

# ---------------------------------------------------------------- Outfit3
a, ruta = load("Outfit3")
n = delete_in_box(a, (372, 900, 392, 1119), "Outfit3", "pico+guion C1")
assert 700 < n < 1600, f"Outfit3 pico: nº inesperado {n}"
tot = 0
for y in range(1010, 1196):
    row = a[y, :, 3] > 0
    d = np.diff(np.concatenate(([0], row.view(np.int8), [0])))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    for s, e in zip(starts, ends):
        if e - s < 16 and s > 1095:
            a[y, s:e] = [0, 0, 0, 0]
            tot += int(e - s)
print(f"  Outfit3 cordon: borrados {tot} px")
delete_components_in_box(a, (743, 872, 754, 894), "Outfit3", "arco cuello")
delete_components_in_box(a, (717, 897, 740, 924), "Outfit3", "curva clara cuello")
delete_components_in_box(a, (352, 1088, 372, 1136), "Outfit3", "resto corte T21")
tot = 0
for y in range(1040, 1161):
    lim = 480 - (y - 1040) * 121 / 120.0
    xi = int(np.floor(lim))
    m = a[y, :xi, 3] > 0
    tot += int(m.sum())
    a[y, :xi] = [0, 0, 0, 0]
print(f"  Outfit3 aleta: recortados {tot} px (diagonal 480,1040 -> 359,1160)")
tot = 0
for y in range(985, 1191):
    m = a[y, 1102:, 3] > 0
    tot += int(m.sum())
    a[y, 1102:] = [0, 0, 0, 0]
print(f"  Outfit3 solapa: recortados {tot} px (x>1101, y985-1190)")


def cond_naranja(sub):
    return (sub[..., 3] > 0) & (sub[..., 0] > 180) & (sub[..., 1] < 80)


def cond_rosa(sub):
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    return ((sub[..., 3] > 0) & (r >= 190) & (r <= 210)
            & (g >= 150) & (g <= 170) & (b >= 140) & (b <= 160))


delete_in_box(a, (560, 940, 600, 1035), "Outfit3", "guiones naranja cuello", cond_naranja)
delete_in_box(a, (800, 890, 820, 905), "Outfit3", "guiones naranja cuello 2", cond_naranja)
delete_in_box(a, (555, 930, 595, 1070), "Outfit3", "restos rosa cuello", cond_rosa)
save(a, ruta)

# ---------------------------------------------------------------- Outfit2
a, ruta = load("Outfit2")
delete_components_in_box(a, (743, 872, 754, 894), "Outfit2", "arco cuello")
delete_components_in_box(a, (755, 897, 838, 928), "Outfit2", "curva clara cuello")
save(a, ruta)

print("FASE 2b COMPLETA")
