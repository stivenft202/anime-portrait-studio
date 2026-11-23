"""Fix ribete del cuello, fase 2 (2026-11-23).

Fase 1 (ribete_cuello_fix.py) borró la parte de la ropa que pintaba
SOBRE la piel del cuello (y<960). Quedó una franja brillante en la base
del cuello (y960-1010, detrás del cuello, x650-900): el ribete/cuello
interior, que es pálido en crudo y con el tinte se vuelve chillón
(amarillo/rosa), contrastando con el cuerpo de la prenda.

Fase 2: recolorea SOLO los píxeles pálidos de esa franja al color
mediano del cuerpo de la prenda. El cuello queda del color de la prenda
(el ribete deja de contrastar), sin agujeros (no se borra nada, solo se
recolorea) y sin tocar el frente de la camisa (x<650) ni el cuerpo.
Las líneas oscuras (pliegues) se conservan: definen el cuello.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')

# color mediano del cuerpo (pecho y1100-1300) por capa, medido 2026-11-23
CUERPO = {
    ('Female', 2): (114, 118, 87),
    ('Female', 3): (94, 120, 150),
}

for (sexo, o), (cr, cg, cb) in CUERPO.items():
    p = os.path.join(ROOT, 'version-linux/assets', sexo, f'Outfit{o}.png')
    a = np.array(Image.open(p).convert('RGBA')).astype(int)
    r, g, b, alpha = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    lum = (r + g + b) / 3
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    ys, xs = np.mgrid[0:1600, 0:1200]
    mask = (alpha > 200) & (lum > 195) & (sat < 60) \
        & (ys >= 955) & (ys < 1015) & (xs >= 650) & (xs < 900)
    n = int(mask.sum())
    a2 = a.copy()
    a2[mask, 0] = cr
    a2[mask, 1] = cg
    a2[mask, 2] = cb
    Image.fromarray(a2.astype(np.uint8)).save(p)
    antes = a
    despues = np.array(Image.open(p).convert('RGBA')).astype(int)
    dif = np.any(antes != despues, axis=2)
    fuera = dif & ~mask
    assert fuera.sum() == 0, f'{sexo} Outfit{o}: {fuera.sum()} px fuera!'
    print(f'{sexo} Outfit{o}: recoloreados {n} px, 0 fuera de máscara')
print('OK')
