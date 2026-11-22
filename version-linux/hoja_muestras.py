#!/usr/bin/env python3
"""Hojas de muestra para Esteban: vello facial + ropas de él, pelos nuevos + ropas de ella."""
import os, sys
sys.path.insert(0, os.path.expanduser('~/workspace/retratos-anime/version-linux'))
import motor
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SAL = os.path.expanduser('~/workspace/your_files')
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
PW = 460  # ancho de panel (recorte cuadrado superior 1200x1200)


def panel(receta):
    comp = motor.render(receta)
    img = Image.fromarray(comp.astype('uint8')).crop((0, 0, 1200, 1200))
    return img.resize((PW, PW), Image.LANCZOS)


def hoja(nombre, items):
    n = len(items)
    H = PW + 52
    img = Image.new('RGB', (PW * n + 12 * (n + 1), H + 12), (24, 26, 32))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(F, 25)
    for i, (rec, etiq) in enumerate(items):
        x = 12 + i * (PW + 12)
        img.paste(panel(rec), (x, 12))
        tw = d.textlength(etiq, font=f)
        d.text((x + (PW - tw) / 2, PW + 22), etiq, font=f, fill=(255, 214, 90))
    ruta = os.path.join(SAL, nombre)
    img.save(ruta)
    print('OK', ruta, img.size)


base_m = dict(sexo='Male', pelo=0, ropa=0, ojos=0, nariz=0, boca=0,
              color_pelo=2, piel=1, color_ropa=0, vello=0)
hoja('Muestra_El_Vello_y_Ropas.png', [
    (dict(base_m, vello=1, ropa=0, color_pelo=2), 'Bigote + Camisa azul'),
    (dict(base_m, vello=2, ropa=1, color_pelo=1), 'Barba incipiente + Hoodie'),
    (dict(base_m, vello=3, ropa=2, color_pelo=2), 'Barba completa + Chaqueta'),
])
base_f = dict(sexo='Female', pelo=0, ropa=0, ojos=0, nariz=0, boca=0,
              color_pelo=0, piel=1, color_ropa=0)
hoja('Muestra_Ella_Pelos_y_Ropas.png', [
    (dict(base_f, pelo=6, ropa=1, color_pelo=5), 'Trenza larga + Chaqueta verde'),
    (dict(base_f, pelo=7, ropa=2, color_pelo=3), 'Dos moños + Hoodie azul'),
    (dict(base_f, pelo=9, ropa=0, color_pelo=2), 'Moño desordenado + Suéter'),
])
