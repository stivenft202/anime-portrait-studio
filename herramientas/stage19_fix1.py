# -*- coding: utf-8 -*-
# FIX stage19-A: (1) oreja — quitar de los frentes el sombreado de oreja
# mal clasificado como pelo (árbitro: el dibujo fuente muestra piel ahí);
# (2) mota — quitar el velo de píxeles semitransparentes que no son pelo
# y están lejos de la masa opaca (las manchas óxido sobre la ropa clara).
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

LINUX = '/home/hatch/workspace/retratos-anime/version-linux/assets'
PAQUETE = '/home/hatch/workspace/retratos-anime/paquete/PortraitKit/Textures'
CRUDOS_M = '/home/hatch/workspace/retratos-anime/fase1/crudos/hombre_v2'
CRUDOS_F = '/home/hatch/workspace/retratos-anime/fase1/crudos/mujer_v2'
MAESTRO_F = '/home/hatch/workspace/retratos-anime/fase1/pruebas/mujer_v2_maestro.png'

def cargar(ruta):
    return np.array(Image.open(ruta).convert('RGBA'), copy=True)

def guardar(arr, sexo, nombre):
    img = Image.fromarray(arr.astype('uint8'), 'RGBA')
    img.save(os.path.join(LINUX, sexo, nombre + '.png'))
    img.save(os.path.join(PAQUETE, sexo, nombre + '.png'))

def es_piel_fuente(rgb):
    r, g, b = rgb[..., 0].astype(float), rgb[..., 1].astype(float), rgb[..., 2].astype(float)
    lum = (r + g + b) / 3.0
    return (lum > 105) & ((r - b) >= 0) & ((r - b) <= 75)

def elipse(cx, cy, rx, ry):
    yy, xx = np.mgrid[0:1600, 0:1200]
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0

def fix_oreja(sexo, nombre, fuente_rgb, cx, cy, rx, ry):
    ruta = os.path.join(LINUX, sexo, nombre + '.png')
    a = cargar(ruta)
    zona = elipse(cx, cy, rx, ry)
    piel = es_piel_fuente(fuente_rgb)
    quitar = zona & piel & (a[..., 3] > 0)
    n = int(quitar.sum())
    if n:
        a[..., 3][quitar] = 0
        guardar(a, sexo, nombre)
    return n

def fix_mota(sexo, nombre):
    ruta = os.path.join(LINUX, sexo, nombre + '.png')
    a = cargar(ruta)
    al = a[..., 3].astype(float)
    r, g, b = a[..., 0].astype(float), a[..., 1].astype(float), a[..., 2].astype(float)
    lum = (r + g + b) / 3.0
    es_pelo = (lum < 115) & (b >= r - 32)
    dist = ndimage.distance_transform_edt(al < 235)
    quitar = (al > 0) & (al < 235) & ~es_pelo & (dist >= 3)
    n = int(quitar.sum())
    if n:
        a[..., 3][quitar] = 0
        guardar(a, sexo, nombre)
    return n

print('--- oreja él (con árbitro) ---')
fuentes_m = {1: 'maestro_a_norm.png', 2: 'dibujo_pelo2_ali.png',
             3: 'dibujo_pelo3_ali.png', 4: 'dibujo_pelo4_ali.png'}
for i, f in fuentes_m.items():
    src = np.asarray(Image.open(os.path.join(CRUDOS_M, f)).convert('RGB'))
    n = fix_oreja('Male', f'Hair{i}_Front', src, 762, 606, 62, 88)
    print(f'  Hair{i}_Front: {n} px quitados')

print('--- oreja ella 1-4 (con árbitro) ---')
src = np.asarray(Image.open(MAESTRO_F).convert('RGB'))
print('  Hair1_Front:', fix_oreja('Female', 'Hair1_Front', src, 792, 592, 58, 84))
for i in (2, 3, 4):
    src = np.asarray(Image.open(os.path.join(CRUDOS_F, f'dibujo_pelo{i}_ali.png')).convert('RGB'))
    print(f'  Hair{i}_Front:', fix_oreja('Female', f'Hair{i}_Front', src, 792, 592, 58, 84))

print('--- oreja ella 5-12 (solo núcleo del cuenco) ---')
for i in range(5, 13):
    ruta = os.path.join(LINUX, 'Female', f'Hair{i}_Front.png')
    a = cargar(ruta)
    zona = elipse(792, 592, 44, 64)
    quitar = zona & (a[..., 3] > 0)
    n = int(quitar.sum())
    if n:
        a[..., 3][quitar] = 0
        guardar(a, 'Female', f'Hair{i}_Front')
    print(f'  Hair{i}_Front: {n} px quitados')

print('--- mota: pelos y vello, ambos sexos ---')
for sexo in ('Female', 'Male'):
    carpeta = os.path.join(LINUX, sexo)
    for f in sorted(os.listdir(carpeta)):
        nombre = f[:-4]
        if nombre.startswith('Hair') or nombre.startswith('FacialHair'):
            n = fix_mota(sexo, nombre)
            if n:
                print(f'  {sexo}/{nombre}: {n} px de mota quitados')
print('FIX A terminado')
