# boca_sorprendido_muestra_C.py — Variante C: la boca que eligió Stiven
# (cara generada hombre 2: boca pequeña con un dientecito blanco arriba
# y lengua rosa abajo). Muestra AISLADA, fuera del programa.
# NO toca version-linux/assets: vive solo en
# diagnostico_usuario/boca_sorprendido/muestras/.
# Además mide el espacio real entre la boca y la línea de la barbilla
# en la Base, para responder si cabe sin tocar el mentón.
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

A = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets'
OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/boca_sorprendido/muestras'
os.makedirs(OUT, exist_ok=True)

CENTRO = {'Female': (406.5, 783.5), 'Male': (357.5, 773.5)}
ZONA_CARA = {'Female': (340, 730, 470, 830), 'Male': (290, 720, 420, 820)}
FONDO = (40, 44, 52)
# tamaño de la boca nueva (actual: 29x37; A: 46x59; B: 44x46)
W_M, H_M = 38, 42


def medir_espacio(sexo):
    """¿Cuánto sitio hay entre la boca y la barbilla en la Base?
    Escanea la banda x=cx±15 desde justo debajo del centro de la boca
    hasta y=950 y lista los tramos de píxeles oscuros (líneas de barbilla)."""
    cx, cy = CENTRO[sexo]
    im = np.array(Image.open(f'{A}/{sexo}/Base.png').convert('RGBA'))
    banda = im[int(cy + 5):950, int(cx - 15):int(cx + 15)]
    lum = banda[..., :3].astype(int).sum(axis=2) // 3
    oscuro = (banda[..., 3] > 150) & (lum < 150)
    por_fila = oscuro.any(axis=1)
    # tramos consecutivos de filas con algún px oscuro
    tramos, ini = [], None
    for i, v in enumerate(por_fila):
        if v and ini is None:
            ini = i
        elif not v and ini is not None:
            tramos.append((ini + int(cy + 5), i - 1 + int(cy + 5)))
            ini = None
    if ini is not None:
        tramos.append((ini + int(cy + 5), len(por_fila) - 1 + int(cy + 5)))
    abajo_nueva = cy + H_M / 2
    print(f'{sexo}: centro boca y={cy:.0f} | boca nueva llega hasta y={abajo_nueva:.0f}')
    print(f'   tramos oscuros (líneas de barbilla) debajo de la boca: {tramos[:5]}')
    if tramos:
        print(f'   hueco libre entre el borde inferior de la boca nueva y la 1ª línea: '
              f'{tramos[0][0] - abajo_nueva:.0f} px')
    return tramos


def variante_C(sexo):
    """Boca pequeña con dientecito blanco arriba y lengua rosa abajo."""
    cx, cy = CENTRO[sexo]
    S = 4  # dibujar a 4x para bordes suaves
    W, H = W_M * S, H_M * S
    dib = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dib)
    # borde exterior oscuro
    d.ellipse([0, 0, W - 1, H - 1], fill=(80, 35, 30, 255))
    # interior rojo medio
    m = 3 * S
    d.ellipse([m, m, W - 1 - m, H - 1 - m], fill=(122, 56, 47, 255))
    # interior oscuro (boca abierta)
    m2 = 6 * S
    d.ellipse([m2, m2 + 2 * S, W - 1 - m2, H - 1 - m2 - 5 * S], fill=(88, 38, 34, 255))
    # dientecito blanco arriba (rectángulo redondeado, centrado)
    tw, th = 20 * S, 8 * S
    tx0, ty0 = (W - tw) // 2, 4 * S
    d.rounded_rectangle([tx0, ty0, tx0 + tw, ty0 + th], radius=3 * S,
                        fill=(240, 240, 240, 255))
    # lengua rosa abajo
    d.ellipse([7 * S, H - 15 * S, W - 1 - 7 * S, H - 1 - 4 * S],
              fill=(186, 126, 108, 255))
    dib = dib.resize((W_M, H_M), Image.LANCZOS)
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(dib, (int(cx - W_M / 2), int(cy - H_M / 2)), dib)
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
    ruta = f'{OUT}/{sexo}_C.png'
    img.save(ruta)
    print('guardada:', ruta)


if __name__ == '__main__':
    for sexo in ('Female', 'Male'):
        medir_espacio(sexo)
    for sexo, nom in (('Female', 'MUJER'), ('Male', 'HOMBRE')):
        c = variante_C(sexo)
        c.save(f'{OUT}/{sexo}_C_layer.png')
        imagen_final(sexo, f'{nom} — C: pequeña con dientecito y lengua (elegida)',
                     c)
    print('listo')
