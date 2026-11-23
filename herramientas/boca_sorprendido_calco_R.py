# boca_sorprendido_calco_R.py — Calcar la boca de la referencia de PERFIL
# que consiguió Stiven (REF_BOCA_ANIME_2.png, chico de perfil mirando a
# la izquierda, boca sorprendida abierta, interior oscuro + lengua rosa).
# Mismo método que el calco B (que funcionó): solo píxeles oscuros
# (lum<110), dilatar 1, componente con mayor solape con la bbox esperada,
# rellenar agujeros, escalar a alto 42 px.
# Salida: diagnostico_usuario/boca_sorprendido/perfil/ (variante R).
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

BASE = '/home/hatch/workspace/anime-portrait-studio'
OUT = f'{BASE}/diagnostico_usuario/boca_sorprendido/perfil'
REF = '/home/hatch/workspace/user/media_library/image/REF_BOCA_ANIME_2.png'
# bbox de la boca según visual grounding (1230x1278): x321-406, y616-716
BBOX = (321, 616, 406, 716)
CENTRO = {'Female': (406.5, 783.5), 'Male': (357.5, 773.5)}
ALTO_OBJ = 42


def calcar():
    ref = np.array(Image.open(REF).convert('RGB')).astype(int)
    ex0, ey0, ex1, ey1 = BBOX
    m = 12
    x0, y0 = max(0, ex0 - m), max(0, ey0 - m)
    x1, y1 = min(ref.shape[1], ex1 + m), min(ref.shape[0], ey1 + m)
    crop = ref[y0:y1, x0:x1]
    lum = crop.sum(axis=2) // 3
    masc0 = lum < 110
    masc0 = ndi.binary_dilation(masc0, iterations=1)
    lab, n = ndi.label(masc0)
    ex0c, ey0c = ex0 - x0, ey0 - y0
    ex1c, ey1c = ex1 - x0, ey1 - y0
    mejor, mejor_area = None, -1
    for c in range(1, n + 1):
        comp = lab == c
        ys, xs = np.where(comp)
        solape = ((xs >= ex0c) & (xs <= ex1c) & (ys >= ey0c) & (ys <= ey1c)).sum()
        if solape > mejor_area:
            mejor, mejor_area = c, solape
    print(f'componentes: {n}, elegida {mejor} (solape {mejor_area} px)')
    mascara = ndi.binary_fill_holes(lab == mejor)
    ys, xs = np.where(mascara)
    by0, by1, bx0, bx1 = ys.min(), ys.max(), xs.min(), xs.max()
    print(f'bbox calcada: x {bx0}-{bx1}, y {by0}-{by1} '
          f'({bx1 - bx0 + 1}x{by1 - by0 + 1} px)')
    ctrl = crop.astype('uint8').copy()
    ctrl[mascara] = (255, 0, 0)
    Image.fromarray(ctrl).resize(
        (crop.shape[1] * 3, crop.shape[0] * 3), Image.NEAREST).save(
        f'{OUT}/calco_R_mascara.png')
    boca_rgb = crop[by0:by1 + 1, bx0:bx1 + 1].astype('uint8')
    boca_alfa = (mascara[by0:by1 + 1, bx0:bx1 + 1] * 255).astype('uint8')
    boca = Image.fromarray(boca_rgb).convert('RGBA')
    boca.putalpha(Image.fromarray(boca_alfa))
    boca.save(f'{OUT}/calco_R_tamano_real.png')
    w, h = boca.size
    nh = ALTO_OBJ
    nw = max(1, round(w * nh / h))
    boca_p = boca.resize((nw, nh), Image.LANCZOS)
    print(f'escalada a alto {nh}: {nw}x{nh} px')
    return boca_p


def capa_para(sexo, boca_p):
    cx, cy = CENTRO[sexo]
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(boca_p, (int(cx - boca_p.width / 2), int(cy - boca_p.height / 2)),
                boca_p)
    return nueva


if __name__ == '__main__':
    boca_p = calcar()
    for sexo in ('Female', 'Male'):
        capa_para(sexo, boca_p).save(f'{OUT}/{sexo}_R_layer.png')
    print('capas R guardadas')
