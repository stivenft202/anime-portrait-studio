#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TANDA 0 — Corrección de los 3 defectos reales del barrido de capas.
Fecha: 2026-11-22. Orden: Stiven («Empieza con la tanda 0 (capas)»).

Defectos (ver diagnostico_usuario/barrido_tanda0/reporte.json y revision/):
1. Male/Hair2_Front: cuadrado marrón de 80 px (x301-311, y512-524) + mota
   de 25 px (x317-324, y534-539) junto al ojo lejano. Se ven en la canónica
   como parche marrón sobre la piel. Se borran (alfa=0), como stage20.
2. Female/Hair6_Front: mota oscura suelta de 33 px (x610-614, y869-876)
   en la mejilla/mandíbula, separada del pelo. Se borra (alfa=0).
3. Male/FacialHair3: rendija blanca fina en diagonal (91 px en y689 +
   45 px en x696-703, y715-733) en la parte superior derecha de la barba,
   visible como rasguño, + 5 microagujeros de 9-21 px. Se rellenan con la
   mediana del color de la barba opaca vecina (radio 15), como stage20.

NO se toca: el hueco de 514 px entre bigote y barba (x304-456, y737-798),
que es intencional (por ahí debe verse la piel; documentado en
stage20_fix_barba.py); el agujero de la boca; los mechones legítimos
(pecho, trenza, oreja) ni ningún otro píxel. Cada arreglo verifica con
assert que fuera de sus componentes exactos no cambia nada.

Snapshot previo: versiones/2026-11-22_tanda0-antes-fixes/
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'version-linux'))
import motor

# Componentes a borrar (tam, x0, x1, y0, y1), mismo detector que stage20.
BORRAR = {
    ('Male', 'Hair2_Front'): [(80, 301, 311, 512, 524),
                              (25, 317, 324, 534, 539)],
    ('Female', 'Hair6_Front'): [(33, 610, 614, 869, 876)],
}

# Grietas a rellenar en FacialHair3 (tam, x0, x1, y0, y1).
GRIETAS_FH3 = [(91, 614, 704, 689, 689), (45, 696, 703, 715, 733),
               (9, 558, 560, 729, 733), (9, 304, 306, 735, 741),
               (9, 299, 302, 746, 748), (21, 289, 296, 749, 753),
               (9, 444, 446, 1004, 1009)]


def componentes_frente(sexo, nombre):
    a = motor.capa(sexo, nombre)
    base = motor.capa(sexo, 'Base')[..., 3] > 0
    mask = a[..., 3] > 30
    lab, n = ndimage.label(mask)
    main = set(np.unique(lab[:250, :])) - {0}
    mainmask = np.isin(lab, list(main))
    cara = base.copy(); cara[:450, :] = False; cara[1150:, :] = False
    stray = cara & mask & ~mainmask
    lab2, n2 = ndimage.label(stray)
    comps = {}
    for i in range(1, n2 + 1):
        m = lab2 == i
        s = int(m.sum())
        if s >= 15:
            ys, xs = np.where(m)
            comps[(s, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))] = m
    return comps


def borrar_fragmentos():
    total = 0
    for (sexo, nombre), lista in sorted(BORRAR.items()):
        ruta = os.path.join(BASE, 'version-linux', 'assets', sexo, nombre + '.png')
        orig = np.asarray(Image.open(ruta).convert('RGBA')).astype(np.uint8)
        comps = componentes_frente(sexo, nombre)
        nuevo = orig.copy()
        for t in lista:
            assert t in comps, f'componente no encontrado en {sexo} {nombre}: {t}'
            m = comps[t]
            nuevo[m, 3] = 0
            nuevo[m, :3] = 0
            total += int(m.sum())
            print(f'  {sexo} {nombre} {t}: borrado')
        fuera = np.ones(nuevo.shape[:2], bool)
        for t in lista:
            fuera &= ~comps[t]
        assert (nuevo[fuera] == orig[fuera]).all(), f'cambio fuera de la zona en {nombre}'
        Image.fromarray(nuevo).save(ruta)
        print(f'{sexo} {nombre}: {sum(t[0] for t in lista)} px borrados')
    return total


def rellenar_barba():
    ruta = os.path.join(BASE, 'version-linux', 'assets', 'Male', 'FacialHair3.png')
    orig = np.asarray(Image.open(ruta).convert('RGBA')).astype(np.uint8)
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
    nuevo = orig.copy().astype(float)
    total = 0
    for t in GRIETAS_FH3:
        assert t in comps, f'grieta no encontrada en FacialHair3: {t}'
        m = comps[t]
        dil = ndimage.binary_dilation(m, iterations=15)
        vecinos = dil & (al > 200) & ~m
        color = np.median(orig[vecinos][:, :3], axis=0)
        nuevo[m, :3] = color
        nuevo[m, 3] = 255
        total += int(m.sum())
        print(f'  FH3 {t}: rellenada con {color.round(0)}')
    fuera = np.ones(al.shape, bool)
    for t in GRIETAS_FH3:
        fuera &= ~comps[t]
    assert (nuevo[fuera].astype(np.uint8) == orig[fuera]).all(), 'cambio fuera de la zona en FH3'
    Image.fromarray(nuevo.astype(np.uint8)).save(ruta)
    print(f'Male FacialHair3: {total} px rellenados')
    return total


if __name__ == '__main__':
    b = borrar_fragmentos()
    g = rellenar_barba()
    print(f'TANDA 0: {b} px borrados + {g} px rellenados = {b + g} px corregidos, 3 defectos')
