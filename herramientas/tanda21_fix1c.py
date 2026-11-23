"""Tanda 21 — fix parte 1c (remanentes).
1. Hair8_Front #3 (zigzag): línea fina en zigzag conectada a la masa por
   arriba. Se captura por flood-fill desde una semilla en el zigzag
   (y~1250), restringido a la región y1180-1350, x330-470, para no subir
   a la masa principal. Se borra alfa=0.
2. Outfit3 franja lima (C2c): píxeles OPACOS claros del borde en
   x1100-1135, y1020-1130 (crudo lum>150) recoloreados al color del
   cuerpo local (mediana de Outfit3 opaco vecino).
Snapshot previo en versiones/2026-11-23_tanda21-antes/.
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

# ---------------- 1. Hair8_Front #3 zigzag ----------------
h8 = load('Hair8_Front.png')
op = h8[..., 3] > 100
# Región de trabajo
y0, y1, x0, x1 = 1180, 1350, 330, 470
sub = op[y0:y1, x0:x1]
lab, n = ndimage.label(sub)
# Semilla: un píxel del zigzag. Buscar el píxel opaco más cercano a (400,1250).
# (400,1250) en coords de sub: y=70, x=70.
sy, sx = 1250 - y0, 400 - x0
# buscar el opaco más cercano a la semilla
best = None
for dy in range(-15, 16):
    for dx in range(-15, 16):
        yy, xx = sy + dy, sx + dx
        if 0 <= yy < sub.shape[0] and 0 <= xx < sub.shape[1] and sub[yy, xx]:
            d = dy * dy + dx * dx
            if best is None or d < best[0]:
                best = (d, yy, xx)
if best is None:
    print('Hair8 #3: semilla no encontrada')
else:
    _, yy, xx = best
    comp_id = lab[yy, xx]
    m = np.zeros((1600, 1200), dtype=bool)
    m[y0:y1, x0:x1] = (lab == comp_id)
    npx = int(m.sum())
    print(f'Hair8 #3 zigzag: comp {comp_id} {npx} px, bbox en región')
    h8[..., 3] = np.where(m, 0, h8[..., 3])
    save(h8, 'Hair8_Front.png')

# ---------------- 2. Outfit3 franja lima ----------------
o3 = load('Outfit3.png')
lum = o3[..., :3].mean(axis=2)
# píxeles opacos claros del borde: adyacentes a transparente o a pelo
op3 = o3[..., 3] > 200
# borde = opaco y con algún vecino transparente (dentro de 1 px)
vec_transp = ndimage.binary_dilation(~op3, iterations=1) & op3
claro = (lum > 150)
zona = np.zeros((1600, 1200), dtype=bool)
zona[1020:1130, 1100:1135] = True
m2 = vec_transp & claro & zona
n2 = int(m2.sum())
# color de referencia: mediana de Outfit3 opaco en x1090-1100, y1020-1130
ref = o3[1020:1130, 1085:1100]
op_r = ref[..., 3] > 200
color_ref = np.median(ref[op_r][:, :3], axis=0) if op_r.any() else np.array([100, 130, 140])
o3[..., :3] = np.where(m2[..., None], color_ref, o3[..., :3])
print(f'Outfit3 franja lima: {n2} px recolorados a {color_ref.astype(int)}')
save(o3, 'Outfit3.png')
print('OK parte 1c')
