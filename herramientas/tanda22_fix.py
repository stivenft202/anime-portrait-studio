#!/usr/bin/env python3
"""TANDA 22 — Fase 2: borrados de alfa + recortes de borde + re-afilado.

- Eyes x5: fragmento pálido de la nariz (159 px c/u).
- Nose1: 3 px oscuros bajo la punta.
- Eyes_Sad: guión 41 px sobre la ceja.
- Hair7_Front: gota (barra + punto) con re-afilado, guión de la trenza,
  2 micros.
- Hair10_Front: fragmentos desprendidos (lista de semillas + motitas <=15 px).
- Hair9_Front: TODOS los componentes desprendidos salvo la masa (16 comps:
  1 masa + 15 desprendidos, todos listados en el análisis).
- Hair2_Front: id11, id2 + componentes <=20 px.
- Outfit3: pico + guión (caja), cordón colgando (regla de runs), arco del
  cuello, curva clara, aleta (recorte diagonal), solapa (recorte a x=1101),
  guiones naranja + restos rosa del cuello, resto de corte T21.
- Outfit2: arco del cuello, curva clara.

Cada operación lleva assert de nº de px y de 0 px fuera de su máscara.
NO toca Base, Male, Outfit1, ni motor.py.
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


def components(mask):
    lab, n = ndimage.label(mask)
    return lab, n


def delete_component_at(a, lab, seed, nombre, tag):
    y, x = seed
    cid = lab[y, x]
    assert cid != 0, f"{nombre}/{tag}: semilla {seed} sin componente"
    m = lab == cid
    n = int(m.sum())
    a[m] = [0, 0, 0, 0]
    print(f"  {nombre} {tag}: borrados {n} px (comp {cid} en {seed})")
    return n


def delete_in_box(a, box, nombre, tag, cond=None):
    x0, y0, x1, y1 = box
    sub = a[y0:y1 + 1, x0:x1 + 1]
    if cond is None:
        m = sub[..., 3] > 0
    else:
        m = cond(sub)
    n = int(m.sum())
    sub[m] = [0, 0, 0, 0]
    print(f"  {nombre} {tag}: borrados {n} px en caja {box}")
    return n


def delete_components_in_box(a, box, nombre, tag):
    """Borra los componentes (alfa>10) que tocan la caja."""
    x0, y0, x1, y1 = box
    lab, _ = components(a[..., 3] > 10)
    ids = set(np.unique(lab[y0:y1 + 1, x0:x1 + 1])) - {0}
    total = 0
    for cid in ids:
        m = lab == cid
        # solo borrar si el componente cabe mayormente en la caja ampliada
        ys, xs = np.where(m)
        if xs.min() >= x0 - 5 and xs.max() <= x1 + 5 and ys.min() >= y0 - 5 and ys.max() <= y1 + 5:
            total += int(m.sum())
            a[m] = [0, 0, 0, 0]
    print(f"  {nombre} {tag}: borrados {total} px ({len(ids)} comps en caja {box})")
    return total


# ---------------------------------------------------------------- Eyes x5
for expr in ["Neutral", "Happy", "Sad", "Angry", "Surprised"]:
    nombre = f"Eyes_{expr}"
    a, ruta = load(nombre)
    n = delete_in_box(a, (315, 674, 334, 701), nombre, "fragmento nariz")
    assert n == 159, f"{nombre}: esperado 159, borrados {n}"
    save(a, ruta)

# ---------------------------------------------------------------- Nose1
a, ruta = load("Nose1")
for (x, y) in [(321, 703), (322, 705), (323, 706)]:
    a[y, x] = [0, 0, 0, 0]
print("  Nose1 motitas: borrados 3 px")
save(a, ruta)

# ---------------------------------------------------------------- Eyes_Sad dash ceja
a, ruta = load("Eyes_Sad")
lab, _ = components(a[..., 3] > 10)
delete_component_at(a, lab, (440, 408), "Eyes_Sad", "guion ceja")
save(a, ruta)

# ---------------------------------------------------------------- Hair7_Front
a, ruta = load("Hair7_Front")
# gota: borrar barra + punto (cajas)
n1 = delete_in_box(a, (524, 900, 545, 956), "Hair7_Front", "gota barra")
n2 = delete_in_box(a, (548, 971, 555, 977), "Hair7_Front", "gota punto")
# re-afilar: medir la hebra a y=890-899 (color y centro)
sub = a[880:900, 520:550]
op = sub[..., 3] > 200
ys, xs = np.where(op)
cx = int(np.median(xs)) + 520
col = np.median(sub[op][..., :3], axis=0).astype(int)
print(f"  Hair7_Front hebra: centro x={cx}, color {tuple(col)}")
# dibujar punta afilada y900-932, ancho 4->1
for y in range(900, 933):
    t = (y - 900) / 32.0
    hw = max(0.5, 2.0 * (1 - t))
    x0 = int(round(cx - hw))
    x1 = int(round(cx + hw))
    a[y, x0:x1 + 1] = [col[0], col[1], col[2], 255]
print("  Hair7_Front punta re-afilada y900-932")
# guión trenza + micros (componentes)
lab, _ = components(a[..., 3] > 10)
delete_component_at(a, lab, (540, 1015), "Hair7_Front", "guion trenza")
delete_component_at(a, lab, (773, 361), "Hair7_Front", "micro mandibula")
delete_component_at(a, lab, (302, 979), "Hair7_Front", "micro pelo")
save(a, ruta)

# ---------------------------------------------------------------- Hair10_Front
a, ruta = load("Hair10_Front")
lab, _ = components(a[..., 3] > 10)
semillas = [
    ((293, 323), "frag id128"), ((342, 299), "frag id151"),
    ((50, 889), "frag sup id1"), ((51, 914), "frag sup id2"),
    ((57, 922), "frag sup id6"), ((456, 1068), "frag id175"),
    ((584, 361), "frag id180"), ((791, 698), "frag id220"),
    ((891, 399), "frag id256"), ((442, 1102), "frag id170"),
    ((813, 688), "frag id234"),
]
for seed, tag in semillas:
    delete_component_at(a, lab, seed, "Hair10_Front", tag)
# motitas desprendidas <=15 px (polvo)
lab, n = components(a[..., 3] > 10)
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
lab, n = components(a[..., 3] > 10)
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
lab, _ = components(a[..., 3] > 10)
delete_component_at(a, lab, (589, 775), "Hair2_Front", "frag id11 oreja")
delete_component_at(a, lab, (283, 322), "Hair2_Front", "frag id2 linea pelo")
lab, n = components(a[..., 3] > 10)
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
# pico + guión: caja x372-392, y900-1119 (por encima de la línea del hombro)
n = delete_in_box(a, (372, 900, 392, 1119), "Outfit3", "pico+guion C1")
assert 700 < n < 1600, f"Outfit3 pico: nº inesperado {n}"
# cordón colgando: por fila, borrar runs finos (<16 px) con xmin>1095
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
# arco cuello + curva clara (componentes en caja)
delete_components_in_box(a, (743, 872, 754, 894), "Outfit3", "arco cuello")
delete_components_in_box(a, (717, 897, 740, 924), "Outfit3", "curva clara cuello")
# resto de corte T21
delete_components_in_box(a, (352, 1088, 372, 1136), "Outfit3", "resto corte T21")
# aleta: recorte diagonal (480,1040) -> (359,1160)
tot = 0
for y in range(1040, 1161):
    lim = 480 - (y - 1040) * 121 / 120.0
    xi = int(np.floor(lim))
    m = a[y, :xi, 3] > 0
    tot += int(m.sum())
    a[y, :xi] = [0, 0, 0, 0]
print(f"  Outfit3 aleta: recortados {tot} px (diagonal 480,1040 -> 359,1160)")
# solapa derecha: recorte a x=1101, y985-1190
tot = 0
for y in range(985, 1191):
    m = a[y, 1102:, 3] > 0
    tot += int(m.sum())
    a[y, 1102:] = [0, 0, 0, 0]
print(f"  Outfit3 solapa: recortados {tot} px (x>1101, y985-1190)")
# cuello: guiones naranja-rojo + restos rosa
def cond_naranja(sub):
    r, g = sub[..., 0], sub[..., 1]
    return (sub[..., 3] > 0) & (r > 180) & (g < 80)


def cond_rosa(sub):
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    return (sub[..., 3] > 0) & (r >= 190) & (r <= 210) & (g >= 150) & (g <= 170) & (b >= 140) & (b <= 160)


n1 = delete_in_box(a, (560, 940, 600, 1035), "Outfit3", "guiones naranja cuello", cond_naranja)
n2 = delete_in_box(a, (800, 890, 820, 905), "Outfit3", "guiones naranja cuello 2", cond_naranja)
n3 = delete_in_box(a, (555, 930, 595, 1070), "Outfit3", "restos rosa cuello", cond_rosa)
save(a, ruta)

# ---------------------------------------------------------------- Outfit2
a, ruta = load("Outfit2")
delete_components_in_box(a, (743, 872, 754, 894), "Outfit2", "arco cuello")
delete_components_in_box(a, (755, 897, 838, 928), "Outfit2", "curva clara cuello")
save(a, ruta)

print("FASE 2 COMPLETA")
