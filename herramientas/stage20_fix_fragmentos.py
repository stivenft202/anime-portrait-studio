#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE20 — Limpieza de fragmentos de cara horneados en los frentes de pelo.
Fecha: 2026-11-22. Orden: Stiven («barrido completo... arregla uno por uno»).

Cada frente de pelo se extrajo de un dibujo plano y arrastra pedazos de la
cara (trozos de ojo, ceja, linea de la boca, zigzag de la mejilla, trazo del
menton). Esos pedazos van en la capa de pelo (orden 50), POR ENCIMA de los
ojos (40) y la boca (45), asi que tapan el ojo tintado o se ven como
cicatriz/lunar. El detector (componentes en la zona de la cara no conectados
a la masa principal) los localizo; cada uno se verifico visualmente en las
hojas de diagnostico_usuario/fragmentos/ antes de borrarlo.

Regla aplicada: se borra SOLO el componente exacto (alfa=0 en sus pixeles).
No se toca ningun otro pixel: el diff fuera de los componentes borrados es 0.
Se conservan: mechones de pelo legitimos (pecho, trenza, mechones laterales),
el pelo de la zona de la oreja y los componentes diminutos invisibles.

Componentes identificados por (tamano, x0, x1, y0, y1) — mismo detector que
el barrido (alfa>30, zona de cara dentro de la Base, y 450-1150, sin tocar
la masa que toca y<250).
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'version-linux'))
import motor

# (sexo, pelo_index_0based) -> lista de componentes a borrar (tam, x0, x1, y0, y1)
BORRAR = {
    ('Female', 1): [(340, 400, 416, 847, 901), (245, 337, 371, 623, 672),
                    (137, 371, 378, 590, 616), (126, 317, 333, 675, 699),
                    (86, 358, 378, 768, 793), (43, 437, 455, 523, 534)],
    ('Female', 2): [(417, 400, 425, 849, 915), (321, 354, 386, 734, 821),
                    (141, 515, 548, 534, 544), (46, 442, 470, 520, 526),
                    (23, 350, 364, 557, 560)],
    ('Female', 3): [(388, 400, 417, 845, 904), (319, 354, 387, 735, 821),
                    (204, 504, 550, 532, 544), (120, 371, 377, 590, 615),
                    (51, 449, 488, 519, 522)],
    ('Female', 6): [(1444, 445, 553, 536, 582), (560, 465, 495, 565, 612),
                    (1293, 414, 589, 893, 1036), (189, 354, 362, 735, 781),
                    (23, 363, 373, 782, 790)],
    ('Female', 7): [(983, 446, 543, 534, 568)],
    ('Female', 9): [(2484, 439, 542, 537, 616)],
    ('Female', 10): [(73, 327, 353, 707, 731), (44, 355, 359, 734, 753),
                     (38, 316, 322, 684, 700), (30, 357, 361, 760, 778)],
    ('Female', 11): [(567, 457, 491, 539, 601), (67, 471, 489, 586, 604)],
    ('Male', 0): [(574, 297, 342, 690, 711), (373, 518, 544, 513, 545),
                  (310, 438, 465, 545, 578), (297, 410, 428, 510, 539),
                  (275, 335, 409, 769, 780), (271, 404, 467, 487, 510),
                  (24, 469, 475, 488, 492)],
    ('Male', 1): [(464, 511, 545, 508, 545), (312, 408, 429, 509, 539),
                  (311, 438, 465, 545, 578), (269, 336, 410, 769, 780),
                  (264, 405, 468, 487, 507), (198, 840, 877, 950, 981),
                  (88, 294, 318, 529, 535)],
    ('Male', 2): [(1235, 409, 546, 499, 543), (279, 335, 409, 768, 779),
                  (222, 410, 471, 486, 497), (122, 443, 466, 559, 578),
                  (63, 451, 464, 546, 555), (49, 438, 449, 554, 565),
                  (42, 405, 413, 497, 507)],
    ('Male', 3): [(463, 511, 545, 508, 545), (321, 408, 429, 508, 537),
                  (305, 438, 466, 545, 578), (277, 336, 408, 769, 780),
                  (261, 409, 474, 487, 502), (165, 309, 319, 552, 599),
                  (35, 404, 410, 501, 509)],
}


def componentes(sexo, nombre):
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
    return a, lab2, comps


def main():
    total_px = 0
    for (sexo, pelo), lista in sorted(BORRAR.items()):
        nombre = motor.PELOS[sexo][pelo][1] + '_Front'
        a, lab2, comps = componentes(sexo, nombre)
        ruta = os.path.join(BASE, 'version-linux', 'assets', sexo, nombre + '.png')
        orig = np.asarray(Image.open(ruta).convert('RGBA')).astype(np.uint8)
        nuevo = orig.copy()
        borrados = 0
        for t in lista:
            if t not in comps:
                print(f'  AVISO: componente no encontrado en {sexo} {nombre}: {t}')
                continue
            m = comps[t]
            nuevo[m, 3] = 0
            nuevo[m, :3] = 0
            borrados += 1
            total_px += int(m.sum())
        # verificacion: fuera de los componentes borrados, nada cambia
        fuera = np.ones(nuevo.shape[:2], bool)
        for t in lista:
            if t in comps:
                fuera &= ~comps[t]
        assert (nuevo[fuera] == orig[fuera]).all(), f'cambio fuera de la zona en {nombre}'
        Image.fromarray(nuevo).save(ruta)
        print(f'{sexo} {nombre}: borrados {borrados}/{len(lista)} componentes, '
              f'{sum(t[0] for t in lista if t in comps)} px')
    print(f'TOTAL: {total_px} px borrados en {len(BORRAR)} capas')


if __name__ == '__main__':
    main()
