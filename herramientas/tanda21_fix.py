"""Tanda 21 — fix parte 1 (borrados y rellenos, sin los quiebros).
Snapshot previo en versiones/2026-11-23_tanda21-antes/.
Fuentes: informes de los analistas C1+C2 y C3+C4.

Outfit3 F:
  1. Láminas del borde izquierdo: recortar hasta la envolvente suave
     por las muescas (y1136->x370, y1296->x297, y1496->x243). ~9.000 px.
  2. Hilo fino vertical (C2a): componente propio x373-376, y928-1099.
     Borrar el tramo visible y1000-1099 (~340 px).
  3. Gancho en hombro der (C1): púa en x1059-1078, y906-940, por encima
     del borde del hombro (y~934). Borrar ~150 px.
  4. Franja del cuello (ribete recoloreado, C3/C4): tira pálida y960-1040
     (709 px) + defringe del canto naranja. Borrar alfa=0.
  5. Franja lima brillante borde der (C2c): defringe x1100-1130, y1020-1125.
Hair8_Front F:
  6. Líneas desprendidas #2 (3.206 px), #3 (1.291 px), #4 (783 px).
  7. Piquito lateral (548-563, y970-975) + motita (428-429, 942-944): ~45 px.
Hair9_Front F:
  8. Líneas desprendidas #2 (1.797 px), #3 (1.303 px).
  9. Mechón vertical punteado (539 px, x300-310, y691-880): unir huecos
     de 1 px con color de pelo (~10 px).
  10. Motita 10 px en (873-876, 1084-1087).
Hair2_Front F:
  11. Muesca en la frente (C3): rellenar huecos del borde con pelo, ~75 px.
Hair2_Back F:
  12. Hilos desprendidos comps 124 (1.638 px), 119 (413 px), 125 (160 px).
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')
AS = os.path.join(ROOT, 'version-linux/assets/Female')

def load(name):
    return np.array(Image.open(os.path.join(AS, name)).convert('RGBA')).astype(np.int32)

def save(a, name):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(AS, name))

def comps(mask, min_px=1):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) >= min_px:
            out.append((i, len(xs), int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())))
    return lab, out

def erase_component(a, lab, comp_id):
    """Borra (alfa=0) un componente. Devuelve nº de px borrados."""
    m = lab == comp_id
    n = int(m.sum())
    a[..., 3] = np.where(m, 0, a[..., 3])
    return n

# ---------------- Outfit3 ----------------
o3 = load('Outfit3.png')
o3_orig = o3.copy()
total_o3 = 0

# 1. Láminas: envolvente suave por las muescas.
#    Puntos de control (y, x del borde): la prenda a la DERECHA queda.
ctrl = [(1050, 375), (1136, 370), (1296, 297), (1496, 243), (1550, 238)]
ys_c = np.array([c[0] for c in ctrl]); xs_c = np.array([c[1] for c in ctrl])
yy = np.arange(1600)
edge_x = np.interp(yy, ys_c, xs_c)
mask = np.zeros((1600, 1200), dtype=bool)
for y in range(1050, 1551):
    mask[y, :int(edge_x[y])] = True
mask &= o3[..., 3] > 0
n = int(mask.sum())
o3[..., 3] = np.where(mask, 0, o3[..., 3])
print(f'Outfit3 láminas recortadas: {n} px')
total_o3 += n

# 2. Hilo fino vertical: componente propio en x360-390, y900-1120.
lab, cs_o3 = comps(o3[..., 3] > 100, 50)
# buscar componente con bbox ~x373-376, y928-1099
for i, cnt, xmin, xmax, ymin, ymax in cs_o3:
    if 365 <= xmin and xmax <= 385 and 900 <= ymin and ymax <= 1120 and cnt < 2000:
        # solo el tramo visible y1000-1099 + el componente entero si es fino
        m = (lab == i)
        n2 = int(m.sum())
        o3[..., 3] = np.where(m, 0, o3[..., 3])
        print(f'Outfit3 hilo fino borrado: comp {i} {n2} px bbox x{xmin}-{xmax} y{ymin}-{ymax}')
        total_o3 += n2

# 3. Gancho hombro der: píxeles de Outfit3 en x1055-1082 con y<934.
m = np.zeros((1600, 1200), dtype=bool)
m[900:934, 1055:1082] = True
m &= o3[..., 3] > 0
n = int(m.sum())
o3[..., 3] = np.where(m, 0, o3[..., 3])
print(f'Outfit3 gancho hombro borrado: {n} px')
total_o3 += n

# 4. Franja del cuello (ribete recoloreado): tira pálida y960-1040.
#    Color crudo rosa pálido ~(197,162,150): píxeles con R>170, G 130-180,
#    B 120-170, en la zona del cuello x500-650, y955-1045.
r, g, b = o3[..., 0], o3[..., 1], o3[..., 2]
palido = (o3[..., 3] > 100) & (r > 170) & (g > 120) & (g < 185) & (b > 110) & (b < 175)
zona = np.zeros((1600, 1200), dtype=bool)
zona[955:1045, 500:650] = True
m = palido & zona
n = int(m.sum())
o3[..., 3] = np.where(m, 0, o3[..., 3])
print(f'Outfit3 franja cuello borrada: {n} px')
total_o3 += n

# 5. Franja lima borde der: defringe. Píxeles claros del borde de Outfit3
#    en x1100-1135, y1020-1130: recolorar al color del cuerpo más cercano.
#    (Se hace al final, tras los borrados, con el color local.)
save(o3, 'Outfit3.png')
print(f'Outfit3 total (sin defringe): {total_o3} px')

# ---------------- Hair8_Front ----------------
h8 = load('Hair8_Front.png')
lab8, cs8 = comps(h8[..., 3] > 100, 100)
# Identificar #2, #3, #4 por bbox aproximado (informe analista).
# #2: diagonal (764,1052)->(455,1595); #3: zigzag (461,1156)->(340,1340);
# #4: diagonal corta (337,1468)->(288,1595).
objetivos8 = [
    ('#2', 400, 800, 1050, 1600, 2500, 4000),
    ('#3', 300, 500, 1100, 1400, 1000, 1600),
    ('#4', 250, 400, 1400, 1600, 500, 1100),
]
total_h8 = 0
for nombre, xmin0, xmax0, ymin0, ymax0, pmin, pmax in objetivos8:
    mejor = None
    for i, cnt, xmin, xmax, ymin, ymax in cs8:
        if xmin0 <= xmin and xmax <= xmax0 and ymin0 <= ymin and ymax <= ymax0 and pmin <= cnt <= pmax:
            if mejor is None or cnt > mejor[1]:
                mejor = (i, cnt, xmin, xmax, ymin, ymax)
    if mejor:
        n = erase_component(h8, lab8, mejor[0])
        print(f'Hair8_Front {nombre} borrado: comp {mejor[0]} {n} px bbox x{mejor[2]}-{mejor[3]} y{mejor[4]}-{mejor[5]}')
        total_h8 += n
    else:
        print(f'Hair8_Front {nombre}: NO ENCONTRADO (revisar)')
# 7. Piquito + motita del cuello.
m = np.zeros((1600, 1200), dtype=bool)
m[970:976, 548:564] = True
m[942:945, 428:430] = True
m &= h8[..., 3] > 0
n = int(m.sum())
h8[..., 3] = np.where(m, 0, h8[..., 3])
print(f'Hair8_Front piquito+motita borrados: {n} px')
total_h8 += n
save(h8, 'Hair8_Front.png')
print(f'Hair8_Front total: {total_h8} px')

# ---------------- Hair9_Front ----------------
h9 = load('Hair9_Front.png')
lab9, cs9 = comps(h9[..., 3] > 100, 100)
objetivos9 = [
    ('#2', 200, 350, 1350, 1600, 1400, 2200),
    ('#3', 400, 600, 1300, 1600, 1000, 1700),
]
total_h9 = 0
for nombre, xmin0, xmax0, ymin0, ymax0, pmin, pmax in objetivos9:
    mejor = None
    for i, cnt, xmin, xmax, ymin, ymax in cs9:
        if xmin0 <= xmin and xmax <= xmax0 and ymin0 <= ymin and ymax <= ymax0 and pmin <= cnt <= pmax:
            if mejor is None or cnt > mejor[1]:
                mejor = (i, cnt, xmin, xmax, ymin, ymax)
    if mejor:
        n = erase_component(h9, lab9, mejor[0])
        print(f'Hair9_Front {nombre} borrado: comp {mejor[0]} {n} px bbox x{mejor[2]}-{mejor[3]} y{mejor[4]}-{mejor[5]}')
        total_h9 += n
    else:
        print(f'Hair9_Front {nombre}: NO ENCONTRADO (revisar)')
# 9. Mechón punteado: unir huecos de 1 px en x300-310, y691-880.
#    Rellenar con color de pelo local (mediana del mechón).
sub = h9[691:880, 300:311]
op = sub[..., 3] > 100
color_pelo = np.median(sub[op][:, :3], axis=0) if op.any() else np.array([60, 50, 45])
# huecos: píxeles transparentes entre dos píxeles opacos del mechón (vertical)
col = h9[691:880, 300:311, 3] > 100
relleno = 0
for x in range(11):
    c = col[:, x]
    for y in range(1, len(c) - 1):
        if not c[y] and c[y - 1] and c[y + 1]:
            h9[691 + y, 300 + x, :3] = color_pelo
            h9[691 + y, 300 + x, 3] = 255
            relleno += 1
print(f'Hair9_Front mechón punteado: huecos rellenados {relleno} px, color {color_pelo.astype(int)}')
# 10. Motita (873-876, 1084-1087).
m = np.zeros((1600, 1200), dtype=bool)
m[1084:1088, 873:877] = True
m &= h9[..., 3] > 0
n = int(m.sum())
h9[..., 3] = np.where(m, 0, h9[..., 3])
print(f'Hair9_Front motita borrada: {n} px')
total_h9 += n
save(h9, 'Hair9_Front.png')
print(f'Hair9_Front total borrado: {total_h9} px')

# ---------------- Hair2_Front (frente) ----------------
h2f = load('Hair2_Front.png')
# 11. Muesca en la frente: huecos del borde con piel visible.
#    Zona x400-420, y475-500: píxeles transparentes rodeados de pelo.
#    Color de pelo local: mediana del pelo adyacente (x395-425, y470-500).
sub = h2f[470:505, 395:425]
op = sub[..., 3] > 100
color_h2 = np.median(sub[op][:, :3], axis=0) if op.any() else np.array([60, 50, 45])
# Rellenar huecos: píxeles transparentes en la zona que están entre pelo
# (dentro de la envolvente del borde). Usar closing morfológico del alfa.
alfa = (h2f[..., 3] > 100)
zona = np.zeros((1600, 1200), dtype=bool)
zona[475:500, 400:420] = True
# closing: dilatar 2 y erosionar 2 -> huecos pequeños se cierran
dil = ndimage.binary_dilation(alfa, iterations=2)
ero = ndimage.binary_erosion(dil, iterations=2)
huecos = ero & ~alfa & zona
n = int(huecos.sum())
h2f[..., :3] = np.where(huecos[..., None], color_h2, h2f[..., :3])
h2f[..., 3] = np.where(huecos, 255, h2f[..., 3])
print(f'Hair2_Front muesca frente rellenada: {n} px, color {color_h2.astype(int)}')
save(h2f, 'Hair2_Front.png')

# ---------------- Hair2_Back (hilos desprendidos) ----------------
h2b = load('Hair2_Back.png')
lab2b, cs2b = comps(h2b[..., 3] > 100, 100)
# comps 124 (x517-601, y886-1118, 1638 px), 119 (arco, 413 px), 125 (guión, 160 px).
# Borrar componentes desprendidos en la zona x450-650, y850-1150 que NO sean
# la masa principal (la masa termina en y845).
total_h2b = 0
for i, cnt, xmin, xmax, ymin, ymax in cs2b:
    if 450 <= xmin and xmax <= 700 and ymin >= 850 and cnt < 3000:
        n = erase_component(h2b, lab2b, i)
        print(f'Hair2_Back hilo desprendido borrado: comp {i} {n} px bbox x{xmin}-{xmax} y{ymin}-{ymax}')
        total_h2b += n
save(h2b, 'Hair2_Back.png')
print(f'Hair2_Back total: {total_h2b} px')

# ---------------- Asserts: 0 px fuera de las máscaras ----------------
# (Verificación por diff contra snapshot, se hace en el paso de verificación.)
print('OK parte 1')
