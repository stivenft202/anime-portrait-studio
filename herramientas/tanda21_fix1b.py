"""Tanda 21 — fix parte 1b (remanentes de la parte 1).
Snapshot previo en versiones/2026-11-23_tanda21-antes/.

1. Outfit3 hilo fino: el tramo que cuelga en el aire (x371-378, y928-1052),
   por encima del borde de la prenda. Borrar alfa=0.
2. Outfit3 franja cuello: resto pálido (criterio amplio R>150), ~100 px.
3. Outfit3 franja lima borde der (C2c): defringe x1100-1135, y1020-1130.
4. Hair9_Front mechón punteado: closing morfológico (dilatar 1 + erosionar 1)
   en la zona x295-315, y690-885 para unir los huecos de 1 px.
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

# ---------------- Outfit3 ----------------
o3 = load('Outfit3.png')
# 1. Hilo fino que cuelga en el aire.
m = np.zeros((1600, 1200), dtype=bool)
m[928:1052, 371:379] = True
m &= o3[..., 3] > 0
n = int(m.sum())
o3[..., 3] = np.where(m, 0, o3[..., 3])
print(f'Outfit3 hilo colgante borrado: {n} px')
# 2. Franja cuello resto pálido (criterio amplio).
r, g, b = o3[..., 0], o3[..., 1], o3[..., 2]
pal = (o3[..., 3] > 100) & (r > 150) & (g > 110) & (g < 190) & (b > 100) & (b < 180)
zona = np.zeros((1600, 1200), dtype=bool)
zona[955:1045, 500:650] = True
m2 = pal & zona
n2 = int(m2.sum())
o3[..., 3] = np.where(m2, 0, o3[..., 3])
print(f'Outfit3 franja cuello resto borrado: {n2} px')
# 3. Defringe franja lima: píxeles claros del borde (crudo lum>150) en
#    x1100-1135, y1020-1130. Recolorar al color del cuerpo más cercano
#    (mediana de los píxeles opacos vecinos en la misma fila).
lum = o3[..., :3].mean(axis=2)
borde = (o3[..., 3] > 50) & (o3[..., 3] < 255) & (lum > 150)
zona3 = np.zeros((1600, 1200), dtype=bool)
zona3[1020:1130, 1100:1135] = True
m3 = borde & zona3
# color de referencia: mediana de Outfit3 opaco en x1090-1100, y1020-1130
ref = o3[1020:1130, 1090:1100]
op = ref[..., 3] > 200
color_ref = np.median(ref[op][:, :3], axis=0) if op.any() else np.array([100, 130, 140])
n3 = int(m3.sum())
o3[..., :3] = np.where(m3[..., None], color_ref, o3[..., :3])
print(f'Outfit3 defringe lima: {n3} px recolorados a {color_ref.astype(int)}')
save(o3, 'Outfit3.png')

# ---------------- Hair9_Front mechón punteado ----------------
h9 = load('Hair9_Front.png')
alfa = h9[..., 3] > 100
zona9 = np.zeros((1600, 1200), dtype=bool)
zona9[690:885, 295:315] = True
# closing solo en la zona: dilatar 1, erosionar 1 (une huecos de 1 px)
sub = alfa[690:885, 295:315]
cerrado = ndimage.binary_erosion(ndimage.binary_dilation(sub, iterations=1), iterations=1)
nuevos = cerrado & ~sub
# rellenar los nuevos píxeles con el color de pelo local
ref9 = h9[690:885, 295:315]
op9 = ref9[..., 3] > 100
color9 = np.median(ref9[op9][:, :3], axis=0) if op9.any() else np.array([80, 60, 50])
h9[..., :3] = np.where(np.pad(nuevos, ((690, 1600 - 885), (295, 1200 - 315)))[..., None],
                       color9, h9[..., :3])
h9[..., 3] = np.where(np.pad(nuevos, ((690, 1600 - 885), (295, 1200 - 315))), 255, h9[..., 3])
print(f'Hair9_Front mechón: huecos unidos {int(nuevos.sum())} px, color {color9.astype(int)}')
save(h9, 'Hair9_Front.png')
print('OK parte 1b')
