# boca_sorprendido_calco.py — Calcar la boca Sorprendido de la referencia
# generada (cara hombre 2: boca pequeña con dientecito y lengua).
# En vez de dibujarla a mano con vectores (la C quedó fea), se EXTRAEN
# los píxeles reales de la boca de la imagen generada:
#   contorno oscuro -> dilatar para cerrar huecos -> rellenar agujeros
#   -> quedarse solo con la componente de la boca -> recortar -> escalar.
# Muestra AISLADA, fuera del programa. NO toca version-linux/assets.
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

REF = ('/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/'
       'boca_sorprendido/muestras/media-generation-cara-sorprendida-hombre-2-dien-'
       '0-8889faa0-d838-4ed8-8f6d-3f3f302d7d13.webp')
A = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets'
OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/boca_sorprendido/muestras'
os.makedirs(OUT, exist_ok=True)

CENTRO = {'Female': (406.5, 783.5), 'Male': (357.5, 773.5)}
ZONA_CARA = {'Female': (340, 730, 470, 830), 'Male': (290, 720, 420, 820)}
FONDO = (40, 44, 52)
# bbox de la boca en la referencia (visual grounding, 1600x1600):
# x 902-1083, y 997-1134. Recorte con margen:
CROP = (880, 970, 1110, 1160)
# tamaño objetivo en el retrato (la actual es 29x37; proporción de la
# referencia 181x137 -> ancho 46, alto ~35)
ANCHO_OBJ = 46


def calcar():
    ref = np.array(Image.open(REF).convert('RGB')).astype(int)
    x0, y0, x1, y1 = CROP
    crop = ref[y0:y1, x0:x1]
    Image.fromarray(crop.astype('uint8')).resize(
        (crop.shape[1] * 3, crop.shape[0] * 3), Image.LANCZOS).save(
        f'{OUT}/calco_recorte_boca.png')
    lum = crop.sum(axis=2) // 3
    r, g, b = crop[..., 0], crop[..., 1], crop[..., 2]
    # píxeles "de boca": oscuros (contorno + interior) o rojizos (interior
    # rojo + lengua rosa) o diente blanco (muy claro y sin saturación).
    # La piel (beige claro, R-B~50) no entra en ninguna regla.
    masc0 = ((lum < 120)
             | ((r - b > 60) & (lum < 230))
             | ((lum > 225) & ((crop.max(axis=2) - crop.min(axis=2)) < 15)))
    masc0 = ndi.binary_dilation(masc0, iterations=2)
    # quedarse con la componente que más se solapa con la bbox esperada
    # de la boca (x 902-1083, y 997-1134 en la imagen original)
    lab, n = ndi.label(masc0)
    ex0, ey0, ex1, ey1 = 902 - x0, 997 - y0, 1083 - x0, 1134 - y0
    mejor, mejor_area = None, -1
    for c in range(1, n + 1):
        comp = lab == c
        ys, xs = np.where(comp)
        solape = ((xs >= ex0) & (xs <= ex1) & (ys >= ey0) & (ys <= ey1)).sum()
        if solape > mejor_area:
            mejor, mejor_area = c, solape
    print(f'componentes "de boca": {n}, elegida la {mejor} '
          f'(solape con bbox esperada: {mejor_area} px)')
    mascara = ndi.binary_fill_holes(lab == mejor)
    # recortar al bbox de la máscara
    ys, xs = np.where(mascara)
    by0, by1, bx0, bx1 = ys.min(), ys.max(), xs.min(), xs.max()
    print(f'bbox de la boca calcada en el recorte: x {bx0}-{bx1}, y {by0}-{by1} '
          f'({bx1 - bx0 + 1}x{by1 - by0 + 1} px)')
    # imagen de control: la máscara en rojo sobre el recorte
    ctrl = crop.astype('uint8').copy()
    ctrl[mascara] = (255, 0, 0)
    Image.fromarray(ctrl).resize(
        (crop.shape[1] * 3, crop.shape[0] * 3), Image.NEAREST).save(
        f'{OUT}/calco_mascara_control.png')
    boca_rgb = crop[by0:by1 + 1, bx0:bx1 + 1].astype('uint8')
    boca_alfa = (mascara[by0:by1 + 1, bx0:bx1 + 1] * 255).astype('uint8')
    boca = Image.fromarray(boca_rgb).convert('RGBA')
    boca.putalpha(Image.fromarray(boca_alfa))
    boca.save(f'{OUT}/calco_boca_tamano_real.png')
    # escalar al tamaño objetivo manteniendo proporción
    w, h = boca.size
    nw = ANCHO_OBJ
    nh = max(1, round(h * nw / w))
    boca_p = boca.resize((nw, nh), Image.LANCZOS)
    print(f'boca calcada escalada: {nw}x{nh} px')
    return boca_p


def capa_para(sexo, boca_p):
    cx, cy = CENTRO[sexo]
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(boca_p, (int(cx - boca_p.width / 2), int(cy - boca_p.height / 2)),
                boca_p)
    return nueva


def render_cara(sexo, boca_layer):
    base = Image.open(f'{A}/{sexo}/Base.png').convert('RGBA')
    nariz = Image.open(f'{A}/{sexo}/Nose1.png').convert('RGBA')
    comp = Image.alpha_composite(base, nariz)
    comp = Image.alpha_composite(comp, boca_layer)
    fondo = Image.new('RGBA', (1200, 1600), FONDO + (255,))
    fondo.alpha_composite(comp)
    x0, y0, x1, y1 = ZONA_CARA[sexo]
    z = fondo.convert('RGB').crop((x0, y0, x1, y1))
    return z.resize((z.width * 4, z.height * 4), Image.LANCZOS)


def boca_sola(boca_layer, sexo):
    cx, cy = CENTRO[sexo]
    z = boca_layer.crop((int(cx - 40), int(cy - 45), int(cx + 40), int(cy + 45)))
    fondo = Image.new('RGBA', z.size, FONDO + (255,))
    fondo.alpha_composite(z)
    return fondo.convert('RGB').resize((320, 360), Image.LANCZOS)


def imagen_final(sexo, etiqueta, boca_layer):
    cara = render_cara(sexo, boca_layer)
    sola = boca_sola(boca_layer, sexo)
    W, H = 520 + 320 + 40, 400
    img = Image.new('RGB', (W, H + 40), FONDO)
    img.paste(sola, (20, 40))
    img.paste(cara, (360, 40))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    except Exception:
        f = ImageFont.load_default()
    d.text((20, 8), etiqueta, fill=(255, 255, 255), font=f)
    ruta = f'{OUT}/{sexo}_T.png'
    img.save(ruta)
    print('guardada:', ruta)


if __name__ == '__main__':
    boca_p = calcar()
    for sexo, nom in (('Female', 'MUJER'), ('Male', 'HOMBRE')):
        capa = capa_para(sexo, boca_p)
        capa.save(f'{OUT}/{sexo}_T_layer.png')
        imagen_final(sexo, f'{nom} — T: calcada de la referencia (diente y lengua)',
                     capa)
    print('listo')
