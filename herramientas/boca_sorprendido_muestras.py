# boca_sorprendido_muestras.py — 4 modificaciones de la boca Sorprendido
# (2 mujer + 2 hombre) como muestras AISLADAS, fuera del programa.
# NO toca version-linux/assets: las variantes viven solo en
# diagnostico_usuario/boca_sorprendido/muestras/.
# Variante A (más grande): el óvalo original escalado 1.6x, mismo estilo.
# Variante B (forma de O): óvalo nuevo dibujado, más redondo/ancho, interior
# más oscuro (boca bien abierta) y lengua abajo.
# Cada imagen final = boca sola (izq.) + boca sobre la cara (der., zoom 4x),
# con etiqueta. Render sobre Base + Nose1, piel Light, sin tintes.
import os
from PIL import Image, ImageDraw, ImageFont

A = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets'
OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/boca_sorprendido/muestras'
os.makedirs(OUT, exist_ok=True)

# Centro del óvalo original por sexo (bbox F [392-421,765-802], M [343-372,755-792])
CENTRO = {'Female': (406.5, 783.5), 'Male': (357.5, 773.5)}
# Zona de la boca para el recorte de la cara (lienzo 1200x1600)
ZONA_CARA = {'Female': (340, 730, 470, 830), 'Male': (290, 720, 420, 820)}
FONDO = (40, 44, 52)

def variante_A(sexo):
    """Óvalo original escalado 1.6x alrededor de su centro."""
    orig = Image.open(f'{A}/{sexo}/Mouth_Surprised.png').convert('RGBA')
    cx, cy = CENTRO[sexo]
    # ventana 60x70 centrada en el óvalo (transparente salvo el óvalo)
    win = orig.crop((int(cx - 30), int(cy - 35), int(cx + 30), int(cy + 35)))
    win2 = win.resize((96, 112), Image.LANCZOS)
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(win2, (int(cx - 48), int(cy - 56)), win2)
    return nueva

def variante_B(sexo):
    """Óvalo nuevo en forma de O: 44x46, más redondo, interior oscuro, lengua."""
    cx, cy = CENTRO[sexo]
    S = 4  # dibujar a 4x para bordes suaves
    W, H = 44 * S, 46 * S
    dib = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dib)
    # borde exterior oscuro
    d.ellipse([0, 0, W - 1, H - 1], fill=(80, 35, 30, 255))
    # interior rojo medio
    m = 3 * S
    d.ellipse([m, m, W - 1 - m, H - 1 - m], fill=(122, 56, 47, 255))
    # interior oscuro (boca abierta) — centro
    m2 = 6 * S
    d.ellipse([m2, m2 + 2 * S, W - 1 - m2, H - 1 - m2 - 6 * S], fill=(88, 38, 34, 255))
    # lengua abajo
    d.ellipse([7 * S, H - 15 * S, W - 1 - 7 * S, H - 1 - 4 * S], fill=(186, 126, 108, 255))
    dib = dib.resize((44, 46), Image.LANCZOS)
    nueva = Image.new('RGBA', (1200, 1600), (0, 0, 0, 0))
    nueva.paste(dib, (int(cx - 22), int(cy - 23)), dib)
    return nueva

def render_cara(sexo, boca_layer):
    """Base + Nose1 + boca, sobre fondo oscuro, recorte zona boca a 4x."""
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
    """El óvalo solo, recortado y a 4x, sobre fondo oscuro."""
    cx, cy = CENTRO[sexo]
    z = boca_layer.crop((int(cx - 40), int(cy - 45), int(cx + 40), int(cy + 45)))
    fondo = Image.new('RGBA', z.size, FONDO + (255,))
    fondo.alpha_composite(z)
    return fondo.convert('RGB').resize((320, 360), Image.LANCZOS)

def imagen_final(sexo, variante, etiqueta, boca_layer):
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
    ruta = f'{OUT}/{sexo}_{variante}.png'
    img.save(ruta)
    print('guardada:', ruta)

if __name__ == '__main__':
    for sexo, nom in (('Female', 'MUJER'), ('Male', 'HOMBRE')):
        a = variante_A(sexo)
        b = variante_B(sexo)
        a.save(f'{OUT}/{sexo}_A_layer.png')
        b.save(f'{OUT}/{sexo}_B_layer.png')
        imagen_final(sexo, 'A', f'{nom} — A: más grande (óvalo x1.6)', a)
        imagen_final(sexo, 'B', f'{nom} — B: forma de O (más redonda y abierta)', b)
    print('listo')
