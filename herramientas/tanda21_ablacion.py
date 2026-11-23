"""Ablación por capa para Tanda 21 (2026-11-23).

Reproduce render(receta) de motor.py pero permitiendo OMITIR una capa.
Uso: para atribuir una marca a su capa, se renderiza el combo completo y
el combo sin cada capa candidata; la capa cuya omisión elimina la marca
en la zona es la culpable.

Zonas marcadas (en coords del render 1200x1600):
  C1: cuello/hombro/pecho (garabato grande), líneas verdes cuello/pecho.
  C2: (a) borde pelo izq junto hombro, (b) frente cuello junto collar,
      (c) borde pelo der junto hombro; parche pálido cuello.
  C3: motita frente sobre el ojo; garabato cuello/pecho; línea vertical
      que cuelga de barbilla/cuello.
  C4: hombro/espalda (garabato); línea fina marrón sobre hombro; línea
      vertical que cuelga de barbilla/cuello.
"""
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')
sys.path.insert(0, os.path.join(ROOT, 'version-linux'))
import motor

RECETAS = {
    'c1': dict(sexo='Female', pelo=7, ropa=2, ojos=3, nariz=1, boca=2,
               color_pelo=21, piel=1, color_ropa=22, color_ojos=5, vello=0),
    'c2': dict(sexo='Female', pelo=8, ropa=2, ojos=1, nariz=1, boca=1,
               color_pelo=2, piel=3, color_ropa=13, color_ojos=3, vello=0),
    'c3': dict(sexo='Female', pelo=1, ropa=2, ojos=2, nariz=1, boca=1,
               color_pelo=1, piel=2, color_ropa=23, color_ojos=4, vello=0),
    'c4': dict(sexo='Female', pelo=1, ropa=2, ojos=3, nariz=0, boca=0,
               color_pelo=2, piel=0, color_ropa=8, color_ojos=0, vello=0),
}

def render_sin(receta, omitir=None):
    """Igual que motor.render pero omitiendo una capa ('back','base',
    'outfit','nariz','ojos','boca','front')."""
    sexo = receta['sexo']
    pelo = motor.PELOS[sexo][receta['pelo']][1]
    h, w = motor.capa(sexo, 'Base').shape[:2]
    comp = np.tile(np.array((40, 44, 52), float), (h, w, 1))
    if omitir != 'back':
        comp = motor._sobre(comp, motor._tinte(motor.capa(sexo, pelo + '_Back'),
                             motor.COLORES_PELO[receta['color_pelo']][1]))
    piel = motor.TONOS_PIEL[receta['piel']][1]
    if omitir != 'base':
        comp = motor._sobre(comp, motor._tinte(motor.capa(sexo, 'Base'), piel))
    if omitir != 'outfit':
        comp = motor._sobre(comp, motor._tinte(motor.capa(sexo, motor.ROPAS[sexo][receta['ropa']][1]),
                             motor.COLORES_ROPA[receta['color_ropa']][1]))
    if omitir != 'nariz':
        comp = motor._sobre(comp, motor._tinte(motor.capa(sexo, motor.NARICES[receta['nariz']][1]), piel))
    ojos_arch = motor.OJOS[receta['ojos']][1]
    if omitir != 'ojos':
        comp = motor._sobre(comp, motor._ojos_tinte(motor.capa(sexo, ojos_arch), ojos_arch,
                             receta.get('color_ojos', 0), sexo))
    if omitir != 'boca':
        comp = motor._sobre(comp, motor.capa(sexo, motor.BOCAS[sexo][receta['boca']][1]))
    if omitir != 'front':
        comp = motor._sobre(comp, motor._tinte(motor.capa(sexo, pelo + '_Front'),
                             motor.COLORES_PELO[receta['color_pelo']][1]))
    return np.clip(comp, 0, 255).astype('uint8')

def zona_diff(a, b, x0, x1, y0, y1, umbral=30):
    """Nº de px que cambian >umbral entre dos renders en una zona."""
    d = np.abs(a[y0:y1, x0:x1].astype(int) - b[y0:y1, x0:x1].astype(int)).sum(axis=2)
    return int((d > umbral).sum())

if __name__ == '__main__':
    out = os.path.join(ROOT, 'diagnostico_usuario/tanda21')
    os.makedirs(out, exist_ok=True)
    # Zonas de interés por captura (x0,x1,y0,y1)
    ZONAS = {
        'c1': {'pecho_izq': (180, 420, 1000, 1500),
               'cuello': (380, 700, 850, 1050),
               'hombro_der': (800, 1100, 900, 1300)},
        'c2': {'pecho_izq': (180, 420, 1050, 1550),
               'cuello_frente': (420, 650, 950, 1150),
               'hombro_der': (950, 1150, 900, 1250)},
        'c3': {'frente': (300, 550, 300, 500),
               'pecho_izq': (180, 420, 1000, 1500),
               'cuello': (380, 700, 850, 1050)},
        'c4': {'hombro_der': (850, 1150, 900, 1400),
               'pecho_izq': (180, 420, 1000, 1500),
               'cuello': (380, 700, 850, 1050)},
    }
    for tag, rec in RECETAS.items():
        full = render_sin(rec)
        Image.fromarray(full).save(f'{out}/t21_{tag}_full.png')
        print(f'== {tag} ==', flush=True)
        for omit in ['back', 'base', 'outfit', 'front']:
            v = render_sin(rec, omitir=omit)
            for zname, (x0, x1, y0, y1) in ZONAS[tag].items():
                n = zona_diff(full, v, x0, x1, y0, y1)
                print(f'  sin {omit:7s} | {zname:14s} | px que cambian: {n}', flush=True)
        print(flush=True)
    print('OK')
