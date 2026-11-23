# tanda17b_fix_huecos.py — Corrección del defecto T17-02 (tanda 17, revisión propia)
#
# Defecto: Female Outfit1 ("Sweater and Jacket") y Outfit2 ("Green Jacket")
# tienen agujeros interiores (alfa 0) dentro de la silueta de la prenda por los
# que se ve la piel de la capa Base: motas color piel sobre el jersey.
# Evidencia: render O1 Royal Blue, píxel (389,1391) = (190,172,158) =
# Base exacto, con Outfit1 alfa 0 en ese punto; zoom
# /tmp/t17_check/zoom_parche_render.png muestra las motas beige sobre el
# jersey azul siguiendo la línea de pliegue; mapa de agujeros en
# /tmp/t17_check/mapa_huecos_O1.png y mapa_huecos_O2.png.
# Conteo (binary_fill_holes sobre alfa>200): Outfit1 817 px (46 componentes,
# mayores 277 y 213 px, bbox x309-667 y1109-1542, todos con piel debajo);
# Outfit2 302 px (68 componentes, mayor 46 px, bbox x375-839 y897-1545,
# 301 con piel debajo y 1 con fondo). Preexistente: el snapshot de T17-01
# tiene los mismos agujeros (O1pre alfa 0 en los mismos píxeles).
# El barrido no lo detectó porque el defecto está horneado en la capa: todos
# los renders lo contienen, así que también está en el canónico de D7.
# NO son diseño: los agujeros de pelo/ojos/barba (hebras, construcción del
# ojo, textura de barba) se dejan intactos; solo se tocan los agujeros
# interiores de Outfit1 y Outfit2 de mujer. Outfit3 (15 px, motas de 1 px)
# y los de hombre (máx. 1 px) son ruido y NO se tocan.
#
# Corrección (método stage20: snapshot ANTES, ops de píxeles por script,
# assert de 0 px fuera de los componentes objetivo, re-verificación):
#  1. Máscara H = agujeros interiores de cada Outfit (binary_fill_holes).
#  2. Se rellenan con la prenda vecina (difusión de Laplace desde píxeles
#     opacos de la misma capa, 500 iteraciones), alfa 255.
#
# Snapshot ANTES (md5 verificado) en:
#   versiones/2026-11-23_tanda17b-antes-huecos/{Outfit1,Outfit2}.png
#   (versiones YA con el fix T17-01)
#   Outfit1 88d7ff95f46957748f67b9150d155d96
#   Outfit2 b4630451b55ed05d0fa98b20cabf7eeb

import hashlib
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets/Female'

def md5(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()

def laplace_inpaint(rgb, mask, known, iters=500):
    """Rellena `mask` por difusión (Laplace) desde los píxeles `known`.
    Solo los píxeles `known` y los de la máscara participan en el promedio.
    rgb: float HxWx3."""
    filled = rgb.copy()
    _, inds = ndimage.distance_transform_edt(~known, return_indices=True)
    ys, xs = np.where(mask)
    filled[ys, xs] = rgb[inds[0][ys, xs], inds[1][ys, xs]]
    valid = (known | mask).astype(float)
    for _ in range(iters):
        f0 = filled * valid[:, :, None]
        s = (np.roll(f0, 1, 0) + np.roll(f0, -1, 0)
             + np.roll(f0, 1, 1) + np.roll(f0, -1, 1))
        c = (np.roll(valid, 1, 0) + np.roll(valid, -1, 0)
             + np.roll(valid, 1, 1) + np.roll(valid, -1, 1))
        avg = np.divide(s, c[:, :, None], out=filled.copy(),
                        where=c[:, :, None] > 0)
        upd = mask & (c > 0)
        filled[upd] = avg[upd]
    return filled

ESPERADO = {'Outfit1': 817, 'Outfit2': 302}

for nombre in ['Outfit1', 'Outfit2']:
    arr = np.array(Image.open(f'{ROOT}/{nombre}.png').convert('RGBA')).astype(int)
    orig = arr.copy()
    opaco = arr[:, :, 3] > 200
    mask = ndimage.binary_fill_holes(opaco) & ~opaco
    n = int(mask.sum())
    print(f'{nombre}: agujeros interiores: {n} px (esperado {ESPERADO[nombre]})')
    assert n == ESPERADO[nombre], f'máscara inesperada en {nombre}: {n} px'
    rgb = arr[:, :, :3].astype(float)
    filled = laplace_inpaint(rgb, mask, opaco, iters=500)
    arr[:, :, :3] = np.clip(np.rint(filled), 0, 255).astype(int)
    arr[mask, 3] = 255
    d = np.any(arr != orig, axis=2)
    print(f'  cambiados: {int(d.sum())} | fuera de la máscara: {int((d & ~mask).sum())} | alfa 255 en máscara: {int((arr[mask, 3] == 255).sum())}/{n}')
    assert int((d & ~mask).sum()) == 0
    assert int(d.sum()) == n
    assert int((arr[mask, 3] == 255).sum()) == n
    Image.fromarray(arr.astype('uint8'), 'RGBA').save(f'{ROOT}/{nombre}.png')
    print(f'  md5 {nombre} nueva: {md5(f"{ROOT}/{nombre}.png")}')

print('OK — fix T17-02 aplicado')
