"""Tanda 21 — fix parte 1d (limpieza fina).
1. Hair8_Front #3 fantasma: restos semi-transparentes (alfa 1-100) del
   zigzag en la región y1180-1350, x330-470. Borrar alfa=0 los píxeles
   oscuros y finos que quedan en el trazado del zigzag (dilatar 2 px la
   zona borrada en 1c y borrar lo que quede ahí con alfa>0).
2. Outfit3 franja lima (C2c): píxeles claros de Outfit3 ADYACENTES AL PELO
   (no al transparente) en x1100-1140, y1020-1130. Recolorar al color del
   cuerpo local [56,74,102].
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

# ---------------- 1. Hair8 #3 fantasma ----------------
h8 = load('Hair8_Front.png')
# La zona del zigzag: reconstruir la máscara borrada en 1c (flood-fill)
# y dilatarla 2 px; borrar cualquier píxel con alfa>0 dentro (restos).
op = h8[..., 3] > 100
y0, y1, x0, x1 = 1180, 1350, 330, 470
sub = op[y0:y1, x0:x1]
lab, n = ndimage.label(sub)
# La semilla es la misma que en 1c: cerca de (400,1250).
sy, sx = 1250 - y0, 400 - x0
best = None
for dy in range(-15, 16):
    for dx in range(-15, 16):
        yy, xx = sy + dy, sx + dx
        if 0 <= yy < sub.shape[0] and 0 <= xx < sub.shape[1] and sub[yy, xx]:
            d = dy * dy + dx * dx
            if best is None or d < best[0]:
                best = (d, yy, xx)
# En 1c ya se borró el componente; ahora no debe quedar nada cerca de la
# semilla. En su lugar: borrar restos de baja alfa en la región del zigzag.
# Reconstruir el trazado: píxeles con alfa>0 (cualquier alfa) en la región
# que formen una línea fina oscura. Usar la zona y1180-1350, x330-470 y
# borrar píxeles con alfa>0 que estén a <=2 px de un píxel que ANTES era
# parte del zigzag. Como ya se borró, aproximar: borrar píxeles oscuros
# (lum<120) con alfa 1-100 en la región, que son restos de borde.
r, g, b = h8[..., 0], h8[..., 1], h8[..., 2]
lum = (r + g + b) / 3
zona = np.zeros((1600, 1200), dtype=bool)
zona[y0:y1, x0:x1] = True
restos = zona & (h8[..., 3] > 0) & (h8[..., 3] <= 100) & (lum < 120)
n = int(restos.sum())
h8[..., 3] = np.where(restos, 0, h8[..., 3])
print(f'Hair8 #3 fantasma: restos borrados {n} px')
save(h8, 'Hair8_Front.png')

# ---------------- 2. Outfit3 franja lima (adyacente al pelo) ----------------
o3 = load('Outfit3.png')
h9 = load('Hair9_Front.png')
lum3 = o3[..., :3].mean(axis=2)
op3 = o3[..., 3] > 200
# adyacente al pelo: dilatar la máscara de Hair9_Front 2 px y cruzar con Outfit3
pelo = h9[..., 3] > 100
ady_pelo = ndimage.binary_dilation(pelo, iterations=2) & op3
claro = lum3 > 140
zona2 = np.zeros((1600, 1200), dtype=bool)
zona2[1020:1130, 1100:1140] = True
m2 = ady_pelo & claro & zona2
n2 = int(m2.sum())
color_ref = np.array([56, 74, 102], dtype=np.int32)
o3[..., :3] = np.where(m2[..., None], color_ref, o3[..., :3])
print(f'Outfit3 franja lima (ady. pelo): {n2} px recolorados')
save(o3, 'Outfit3.png')
print('OK parte 1d')
