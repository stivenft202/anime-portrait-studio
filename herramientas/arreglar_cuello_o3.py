#!/usr/bin/env python3
"""Arreglo del cuello (marca de Stiven 2026-11-24): un pedacito de cuello
se sale en el cuello de la camisa (Outfit3, hombre).

La cuña de piel está en la ventana x860-882, y938-968: la piel del cuello
llega hasta x~872 mientras el borde del cuello de la camisa (V) está en
x~878, y la punta de la cuña se asoma por encima del borde. El arreglo
extiende el cuello de la camisa (Outfit3) sobre la punta de la cuña:
se pinta con el color de la chaqueta copiado 8 px a la derecha (misma
textura/sombra) y se prolonga el ribete oscuro por el borde nuevo.

Solo se toca Outfit3 (hombre) en la copia de la rama; la Base no se
toca (recortarla afectaría a los 3 outfits). Se aplica en el archivo de
la rama (trabajo_rama/version-linux/assets/Male/Outfit3.png).
"""
import numpy as np
from PIL import Image

TRAB = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/edad/trabajo_rama/version-linux/assets'
REND = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/edad/muestra/vello_gris_FH3_barba.png'

rend = np.asarray(Image.open(REND).convert('RGB')).astype(int)
out = np.asarray(Image.open(f'{TRAB}/Male/Outfit3.png').convert('RGBA')).astype(float)

def es_piel(px):
    r, g, b = px
    return r > 225 and 190 < g < 230 and 170 < b < 210

# Cuña: piel en el render, ventana x860-882, y938-968
masc = np.zeros((1600, 1200), bool)
for y in range(938, 969):
    for x in range(860, 883):
        if es_piel(rend[y, x]):
            masc[y, x] = True
print('cuña de piel:', int(masc.sum()), 'px')
ys, xs = np.where(masc)
print('  caja x', xs.min(), '-', xs.max(), 'y', ys.min(), '-', ys.max())

# Pintar la chaqueta sobre la cuña: copiar el color 8 px a la derecha
# (misma textura/sombra de la chaqueta) y alfa 255.
for y, x in zip(ys, xs):
    out[y, x, :3] = out[y, x + 8, :3]
    out[y, x, 3] = 255

# Ribete oscuro por el borde nuevo de la cuña (borde superior-izquierdo):
# oscurecer 2 px por fuera de la cuña pintada, donde había piel.
from scipy import ndimage
borde = ndimage.binary_dilation(masc, iterations=2) & ~masc
ys2, xs2 = np.where(borde)
for y, x in zip(ys2, xs2):
    if es_piel(rend[y, x]):
        out[y, x, :3] = np.array([45, 34, 28])  # ribete oscuro del cuello
        out[y, x, 3] = 255
print('ribete:', len(ys2), 'px')

Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save(f'{TRAB}/Male/Outfit3.png')
import hashlib
print('Outfit3 rama nuevo md5:', hashlib.md5(open(f'{TRAB}/Male/Outfit3.png', 'rb').read()).hexdigest()[:12])
