# boca_perfil_calco_B.py — Método B: calcar la boca de las caras de PERFIL
# generadas (ya están de perfil, sin adaptar). Misma segmentación que el
# calco 3/4: píxeles "de boca" (oscuros o rojizos o diente blanco),
# dilatar, componente con mayor solape con la bbox esperada, rellenar.
# Traza las dos (hombre y mujer) y las escala a alto 42 px para comparar;
# la mejor se usa para ambos sexos (mismo diseño, como la boca actual).
# Salida: diagnostico_usuario/boca_sorprendido/perfil/
#   calco_B_<sexo>_tamano_real.png, calco_B_<sexo>_mascara.png,
#   Female_B_layer.png / Male_B_layer.png (con la mejor de las dos).
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

BASE = '/home/hatch/workspace/anime-portrait-studio'
OUT = f'{BASE}/diagnostico_usuario/boca_sorprendido/perfil'
REFS = {
    'hombre': (f'{OUT}/media-generation-perfil-hombre-sorprendido-0-1a4fb3a9-2564-44c2-95f8-5a7f5773620b.webp',
               (347, 1011, 517, 1163)),   # bbox grounding x0,y0,x1,y1 en px
    'mujer': (f'{OUT}/media-generation-perfil-mujer-sorprendido-0-dacfc274-196e-4281-85e6-7abfb570cc89.webp',
              (432, 824, 536, 960)),
}
CENTRO = {'Female': (406.5, 783.5), 'Male': (357.5, 773.5)}
ALTO_OBJ = 42


def calcar(nombre, ruta, bbox):
    ref = np.array(Image.open(ruta).convert('RGB')).astype(int)
    ex0, ey0, ex1, ey1 = bbox
    # Recorte ajustado (margen 12): en perfil la boca está pegada a la línea
    # del labio y a la sombra de la barbilla; un margen grande mete esas
    # zonas en la máscara.
    m = 12
    x0, y0 = max(0, ex0 - m), max(0, ey0 - m)
    x1, y1 = min(ref.shape[1], ex1 + m), min(ref.shape[0], ey1 + m)
    crop = ref[y0:y1, x0:x1]
    lum = crop.sum(axis=2) // 3
    # SOLO píxeles oscuros (contorno negro + interior rojo oscuro). La lengua
    # rosa y el diente blanco quedan como agujeros y los rellena
    # binary_fill_holes. La regla "rojizo" se quita: en perfil conectaba la
    # boca con la sombra rosada del labio/barbilla y la máscara se derramaba.
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
    print(f'{nombre}: componentes {n}, elegida {mejor} (solape {mejor_area} px)')
    mascara = ndi.binary_fill_holes(lab == mejor)
    ys, xs = np.where(mascara)
    by0, by1, bx0, bx1 = ys.min(), ys.max(), xs.min(), xs.max()
    print(f'   bbox calcada: x {bx0}-{bx1}, y {by0}-{by1} '
          f'({bx1 - bx0 + 1}x{by1 - by0 + 1} px)')
    ctrl = crop.astype('uint8').copy()
    ctrl[mascara] = (255, 0, 0)
    Image.fromarray(ctrl).resize(
        (crop.shape[1] * 3, crop.shape[0] * 3), Image.NEAREST).save(
        f'{OUT}/calco_B_{nombre}_mascara.png')
    boca_rgb = crop[by0:by1 + 1, bx0:bx1 + 1].astype('uint8')
    boca_alfa = (mascara[by0:by1 + 1, bx0:bx1 + 1] * 255).astype('uint8')
    boca = Image.fromarray(boca_rgb).convert('RGBA')
    boca.putalpha(Image.fromarray(boca_alfa))
    boca.save(f'{OUT}/calco_B_{nombre}_tamano_real.png')
    # escalar a alto 42 manteniendo proporción
    w, h = boca.size
    nh = ALTO_OBJ
    nw = max(1, round(w * nh / h))
    boca_p = boca.resize((nw, nh), Image.LANCZOS)
    print(f'   escalada a alto {nh}: {nw}x{nh} px')
    return boca_p


def capa_para(sexo, boca_p):
    cx, cy = CENTRO[sexo]
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(boca_p, (int(cx - boca_p.width / 2), int(cy - boca_p.height / 2)),
                boca_p)
    return nueva


if __name__ == '__main__':
    resultados = {}
    for nombre, (ruta, bbox) in REFS.items():
        resultados[nombre] = calcar(nombre, ruta, bbox)
    # La boca de la mujer de perfil tiene las proporciones de perfil
    # (29x42, más alta que ancha); la del hombre sale más ancha. El diseño
    # es el mismo (diente + lengua + interior oscuro) y la boca actual es
    # el mismo diseño para ambos sexos: se usa el calco de la mujer para
    # ambos. El calco del hombre queda guardado para comparar.
    resultados['hombre'].save(f'{OUT}/calco_B_hombre_escalado_42.png')
    for sexo in ('Female', 'Male'):
        capa_para(sexo, resultados['mujer']).save(f'{OUT}/{sexo}_B_layer.png')
    print('capas B guardadas (calco de la mujer de perfil, para ambos sexos)')
