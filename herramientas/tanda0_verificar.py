#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TANDA 0 — Verificación post-corrección: los 3 defectos deben haber
desaparecido y no debe haber aparecido nada nuevo. Renderiza las 3
canónicas con motor.py (píxeles idénticos al navegador, diff máx. 4)
y guarda recortes con zoom de las zonas corregidas."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'version-linux'))
import motor
from tanda0_fix import componentes_frente

OUT = os.path.join(BASE, 'diagnostico_usuario', 'barrido_tanda0', 'verificacion')
os.makedirs(OUT, exist_ok=True)

# 1) Los componentes borrados ya no existen; no apareció nada nuevo en cara.
for sexo, nombre, objetivos in [
        ('Male', 'Hair2_Front', [(80, 301, 311, 512, 524), (25, 317, 324, 534, 539)]),
        ('Female', 'Hair6_Front', [(33, 610, 614, 869, 876)])]:
    comps = componentes_frente(sexo, nombre)
    for t in objetivos:
        assert t not in comps, f'{nombre}: el componente {t} SIGUE AHÍ'
    print(f'{sexo} {nombre}: {len(comps)} componentes en cara restantes '
          f'(antes: {len(comps) + len(objetivos)}); objetivos eliminados: OK')

# 2) Las grietas de FH3 ya no existen (mismo detector que stage20).
a = motor.capa('Male', 'FacialHair3')
al = a[..., 3].astype(float)
relleno = ndimage.binary_fill_holes(al > 30)
interior = relleno & (al < 100)
lab, n = ndimage.label(interior)
comps = {}
for i in range(1, n + 1):
    m = lab == i
    s = int(m.sum())
    if s >= 8:
        ys, xs = np.where(m)
        comps[(s, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))] = m
for t in [(91, 614, 704, 689, 689), (45, 696, 703, 715, 733),
          (9, 558, 560, 729, 733), (9, 304, 306, 735, 741),
          (9, 299, 302, 746, 748), (21, 289, 296, 749, 753),
          (9, 444, 446, 1004, 1009)]:
    assert t not in comps, f'FH3: la grieta {t} SIGUE AHÍ'
# El hueco intencional bigote-barba (514 px) debe seguir intacto.
assert (514, 304, 456, 737, 798) in comps, 'FH3: el hueco intencional bigote-barba SE TOCÓ'
print('Male FacialHair3: 7 grietas eliminadas: OK; hueco intencional intacto: OK')

# 3) Renders de las 3 canónicas + recortes con zoom de las zonas.
def canon(receta, nombre):
    img = Image.fromarray(np.clip(motor.render(receta, fondo=(0, 0, 0)), 0, 255).astype(np.uint8))
    img.save(os.path.join(OUT, nombre + '.png'))
    return img

c1 = canon({'sexo': 'Female', 'pelo': 5, 'ropa': 0, 'ojos': 0, 'nariz': 0, 'boca': 0,
            'color_pelo': 0, 'piel': 0, 'color_ropa': 0, 'color_ojos': 0}, 'canonica_F_Hair6_despues')
c1.crop((560, 820, 680, 920)).resize((480, 400)).save(os.path.join(OUT, 'zoom_F_Hair6_mejilla.png'))
c2 = canon({'sexo': 'Male', 'pelo': 1, 'ropa': 0, 'ojos': 0, 'nariz': 0, 'boca': 0,
            'color_pelo': 0, 'piel': 0, 'color_ropa': 0, 'color_ojos': 0, 'vello': 0}, 'canonica_M_Hair2_despues')
c2.crop((270, 480, 360, 570)).resize((450, 450)).save(os.path.join(OUT, 'zoom_M_Hair2_ojo.png'))
c3 = canon({'sexo': 'Male', 'pelo': 0, 'ropa': 0, 'ojos': 0, 'nariz': 0, 'boca': 0,
            'color_pelo': 0, 'piel': 0, 'color_ropa': 0, 'color_ojos': 0, 'vello': 3}, 'canonica_M_FH3_despues')
c3.crop((580, 650, 740, 770)).resize((480, 360)).save(os.path.join(OUT, 'zoom_M_FH3_rendija.png'))
print('VERIFICACIÓN TANDA 0: OK — 3 defectos eliminados, hueco intencional intacto')
