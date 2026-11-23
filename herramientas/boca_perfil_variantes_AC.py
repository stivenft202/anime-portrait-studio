# boca_perfil_variantes_AC.py — Variantes de boca Sorprendido adaptadas a PERFIL 2D.
# Método A: aplastar la boca calcada 3/4 (conservar alto, comprimir ancho)
#   con factores 0.50 / 0.62 / 0.75 -> capas A050, A062, A075.
# Método C: redibujar en forma de perfil (óvalo vertical estrecho, con
#   diente blanco arriba y lengua rosa abajo, inclinación "baja a la
#   izquierda"), 2 tamaños: C1 30x40, C2 36x44.
# Salida: diagnostico_usuario/boca_sorprendido/perfil/
#   Female_<VAR>_layer.png / Male_<VAR>_layer.png (lienzo 1200x1600)
#   + Female_<VAR>.png / Male_<VAR>.png (muestra: boca sola + cara 4x).
# NO toca version-linux/assets.
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

A = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets'
OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/boca_sorprendido/perfil'
os.makedirs(OUT, exist_ok=True)
CENTRO = {'Female': (406.5, 783.5), 'Male': (357.5, 773.5)}
ZONA_CARA = {'Female': (340, 730, 470, 830), 'Male': (290, 720, 420, 820)}
FONDO = (40, 44, 52)
TRAZO = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/boca_sorprendido/muestras/calco_boca_tamano_real.png'


def capa_para(sexo, boca_p):
    cx, cy = CENTRO[sexo]
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(boca_p, (int(cx - boca_p.width / 2), int(cy - boca_p.height / 2)),
                boca_p)
    return nueva


def metodo_A():
    """Aplastar el calco 3/4: mismo alto (35), ancho x factor."""
    trazo = Image.open(TRAZO).convert('RGBA')
    for nombre, f in (('A050', 0.50), ('A062', 0.62), ('A075', 0.75)):
        nw = max(1, round(46 * f))
        boca = trazo.resize((nw, 35), Image.LANCZOS)
        print(f'{nombre}: boca {boca.size[0]}x{boca.size[1]} px')
        for sexo in ('Female', 'Male'):
            capa_para(sexo, boca).save(f'{OUT}/{sexo}_{nombre}_layer.png')


def dibujar_boca_perfil(w, h):
    """Óvalo vertical estrecho de boca abierta en perfil, con diente y lengua.
    Se dibuja a 4x y se gira -7° (extremo izquierdo más bajo: 'baja a la
    izquierda', como las bocas actuales)."""
    S = 4
    W, H = w * S, h * S
    dib = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dib)
    # silueta: elipse vertical, parte superior algo más estrecha (la boca
    # en perfil se estrecha arriba, donde está el diente, y se redondea abajo)
    d.ellipse([0, 0, W - 1, H - 1], fill=(80, 35, 30, 255))
    # recortar un poco las esquinas superiores para afinar la parte de arriba
    d.ellipse([0, 0, W - 1, H - 1], fill=(80, 35, 30, 255))
    # interior rojo medio
    m = 3 * S
    d.ellipse([m, m, W - 1 - m, H - 1 - m], fill=(122, 56, 47, 255))
    # interior oscuro (boca abierta), deja hueco arriba para el diente
    # y abajo para la lengua
    m2 = 6 * S
    d.ellipse([m2, m2 + 5 * S, W - 1 - m2, H - 1 - m2 - 9 * S],
              fill=(88, 38, 34, 255))
    # diente blanco arriba: caperuza curva (no rectángulo), ~55% del ancho
    tw = int(W * 0.55)
    th = int(H * 0.20)
    tx0 = (W - tw) // 2
    d.pieslice([tx0, 2 * S, tx0 + tw, 2 * S + 2 * th], 180, 360,
               fill=(240, 240, 240, 255))
    # dientecito pequeño debajo del diente principal (como en la referencia)
    d.ellipse([W // 2 - 2 * S, 2 * S + th - 1 * S,
               W // 2 + 2 * S, 2 * S + th + 3 * S],
              fill=(240, 240, 240, 255))
    # lengua rosa abajo: elipse ancha que ocupa el tercio inferior
    d.ellipse([6 * S, H - 14 * S, W - 1 - 6 * S, H - 1 - 3 * S],
              fill=(186, 126, 108, 255))
    # inclinación "baja a la izquierda": giro horario (ángulo negativo)
    dib = dib.rotate(-7, resample=Image.BICUBIC, expand=False,
                     fillcolor=(0, 0, 0, 0))
    return dib.resize((w, h), Image.LANCZOS)


def metodo_C():
    for nombre, (w, h) in (('C1', (30, 40)), ('C2', (36, 44))):
        boca = dibujar_boca_perfil(w, h)
        print(f'{nombre}: boca {w}x{h} px (dibujada, giro -7°)')
        for sexo in ('Female', 'Male'):
            capa_para(sexo, boca).save(f'{OUT}/{sexo}_{nombre}_layer.png')


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


def muestra(sexo, var, etiqueta):
    boca_layer = Image.open(f'{OUT}/{sexo}_{var}_layer.png').convert('RGBA')
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
    ruta = f'{OUT}/{sexo}_{var}.png'
    img.save(ruta)
    print('muestra:', ruta)


if __name__ == '__main__':
    metodo_A()
    metodo_C()
    for var, et in (('A050', 'A 0.50: calcada aplastada x0.50'),
                    ('A062', 'A 0.62: calcada aplastada x0.62'),
                    ('A075', 'A 0.75: calcada aplastada x0.75'),
                    ('C1', 'C1: redibujada perfil 30x40'),
                    ('C2', 'C2: redibujada perfil 36x44')):
        for sexo, nom in (('Female', 'MUJER'), ('Male', 'HOMBRE')):
            muestra(sexo, var, f'{nom} — {et}')
    print('listo')
