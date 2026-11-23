"""Fix ribete del cuello (2026-11-23, visto por Stiven en el vídeo del súper método).

Causa: el ribete/cuello de las 6 capas Outfit sube demasiado por detrás
del cuello (hasta y~874 en mujer, y~821 en hombre O2) y, como la capa de
ropa (30) va POR ENCIMA de la Base (20), pinta una banda del color de la
ropa SOBRE la piel del cuello. Con Blanco se ve pálido (casi no se nota);
con Amarillo/Rosa/etc. es una banda de color chillona en el cuello.

Fix: borrar los píxeles de ropa donde la Base es opaca y y<960 (la zona
del cuello por encima de los hombros). Debajo queda piel (la máscara exige
Base opaca), así que no se abre ningún agujero al fondo. El cuello de la
prenda queda a la altura de la base del cuello (y~960), como debe ser.

Método stage20: snapshot antes, operación programática, asserts de 0 px
fuera de la máscara.
"""
import os
import shutil
import numpy as np
from PIL import Image

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')
SNAP = os.path.join(ROOT, 'versiones/2026-11-23_ribete-cuello-antes')
os.makedirs(SNAP, exist_ok=True)

Y_CORTE = 960  # base del cuello (los hombros empiezan a ensancharse ahí)

for sexo in ['Female', 'Male']:
    base = np.array(Image.open(
        os.path.join(ROOT, 'version-linux/assets', sexo, 'Base.png')
    ).convert('RGBA')).astype(int)
    bop = base[..., 3] > 200
    ys = np.arange(1600)[:, None]
    for o in [1, 2, 3]:
        p = os.path.join(ROOT, 'version-linux/assets', sexo, f'Outfit{o}.png')
        a = np.array(Image.open(p).convert('RGBA'))
        shutil.copy2(p, os.path.join(SNAP, f'{sexo}_Outfit{o}.png'))
        alpha = a[..., 3].astype(int)
        mask = (alpha > 200) & bop & (ys < Y_CORTE)
        n = int(mask.sum())
        # borrar: alfa=0 solo en la máscara
        a2 = a.copy()
        a2[mask, 3] = 0
        Image.fromarray(a2).save(p)
        # asserts: nada cambió fuera de la máscara
        antes = a.astype(int)
        despues = np.array(Image.open(p).convert('RGBA')).astype(int)
        dif = np.any(antes != despues, axis=2)
        fuera = dif & ~mask
        assert fuera.sum() == 0, f'{sexo} Outfit{o}: {fuera.sum()} px fuera!'
        print(f'{sexo} Outfit{o}: borrados {n} px, 0 fuera de máscara')
print('OK — snapshot en', SNAP)
