#!/usr/bin/env python3
"""SÚPER MÉTODO — planchas de revisión con zoom 4x de la capa sola.

Para cada ítem a decidir: recorte de la capa (margen 30 px) compuesto sobre
damero claro + borde rojo del bbox objetivo + etiqueta. Salida en
diagnostico_usuario/supermetodo/revision/.
"""
import json
import os
from PIL import Image, ImageDraw

BASE = os.path.expanduser("~/workspace/anime-portrait-studio")
ASSETS = os.path.join(BASE, "version-linux/assets")
OUT = os.path.join(BASE, "diagnostico_usuario/supermetodo/revision")
os.makedirs(OUT, exist_ok=True)

# (etiqueta, capa_relativa, bbox [x0,y0,x1,y1])
ITEMS = [
    # FASE 1 — dudosos de Stiven
    ("1b_bucle_H7F", "Female/Hair7_Front.png", [1027, 580, 1055, 760]),
    ("1c_hebra_cuello_H7F", "Female/Hair7_Front.png", [612, 850, 653, 935]),
    ("1c_trazo_forro_O3F", "Female/Outfit3.png", [696, 928, 714, 979]),
    ("1d_puntas_trenza_H7F", "Female/Hair7_Front.png", [905, 880, 1010, 1080]),
    ("3b_cola_ojo_M", "Male/Eyes_Surprised.png", [438, 570, 469, 591]),
    ("4c_borde_bob_H3B", "Female/Hair3_Back.png", [1027, 472, 1060, 579]),
    ("4d_punta_H3B", "Female/Hair3_Back.png", [1021, 803, 1075, 903]),
    # FASE 2 — top detectores sin veredicto o ambiguos
    ("D_H2F_M_66px", "Male/Hair2_Front.png", [877, 925, 904, 952]),
    ("D_H3F_F_44px", "Female/Hair3_Front.png", [727, 668, 733, 687]),
    ("D_H3F_F_46px", "Female/Hair3_Front.png", [746, 602, 758, 629]),
    ("D_H4F_M_47px", "Male/Hair4_Front.png", [886, 924, 904, 944]),
    ("D_O2M_83px", "Male/Outfit2.png", [558, 1023, 562, 1057]),
    ("D_BaseM_51px", "Male/Base.png", [274, 547, 281, 559]),
    ("D_BaseM_20px", "Male/Base.png", [840, 818, 849, 825]),
    ("D_tirilla_O1M", "Male/Outfit1.png", [568, 1088, 574, 1134]),
    ("D_tirilla_O3M", "Male/Outfit3.png", [569, 1089, 574, 1134]),
    ("D_speck_BaseM_778_1528", "Male/Base.png", [770, 1520, 786, 1536]),
    ("D_speck_BaseM_359_245", "Male/Base.png", [351, 237, 367, 253]),
    ("D_H11F_F_47px", "Female/Hair11_Front.png", [843, 879, 849, 901]),
    ("D_H2F_F_11px", "Female/Hair2_Front.png", [331, 669, 336, 674]),
    ("D_H2F_M_10px", "Male/Hair2_Front.png", [469, 489, 474, 491]),
    ("D_BaseF_16px", "Female/Base.png", [338, 573, 343, 576]),
    ("D_BaseF_10px", "Female/Base.png", [342, 586, 345, 588]),
    ("D_O2M_20px", "Male/Outfit2.png", [507, 1090, 516, 1093]),
    ("D_O2M_10px", "Male/Outfit2.png", [830, 820, 834, 824]),
    ("D_O3F_23px", "Female/Outfit3.png", [337, 1139, 344, 1144]),
]


def damero(w, h, cell=16):
    img = Image.new("RGB", (w, h), (235, 235, 235))
    d = ImageDraw.Draw(img)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if (x // cell + y // cell) % 2 == 0:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(200, 200, 200))
    return img


for etiqueta, rel, bbox in ITEMS:
    x0, y0, x1, y1 = bbox
    m = 30
    cx0, cy0 = max(0, x0 - m), max(0, y0 - m)
    cx1, cy1 = min(1200, x1 + m), min(1600, y1 + m)
    capa = Image.open(os.path.join(ASSETS, rel)).convert("RGBA")
    rec = capa.crop((cx0, cy0, cx1, cy1))
    fondo = damero(rec.width, rec.height)
    fondo.paste(rec, (0, 0), rec)
    z = 4
    zoom = fondo.resize((fondo.width * z, fondo.height * z), Image.NEAREST)
    d = ImageDraw.Draw(zoom)
    # bbox objetivo en rojo (grueso para verse a 4x)
    rx0, ry0 = (x0 - cx0) * z, (y0 - cy0) * z
    rx1, ry1 = (x1 - cx0) * z, (y1 - cy0) * z
    d.rectangle([rx0, ry0, rx1, ry1], outline=(255, 0, 0), width=3)
    # rejilla cada 10 px de lienzo
    for gx in range(0, fondo.width, 10):
        d.line([(gx * z, 0), (gx * z, zoom.height)], fill=(180, 180, 255), width=1)
    for gy in range(0, fondo.height, 10):
        d.line([(0, gy * z), (zoom.width, gy * z)], fill=(180, 180, 255), width=1)
    zoom.save(os.path.join(OUT, f"rev_{etiqueta}.png"))
    print(f"{etiqueta}: {rel} bbox={bbox} crop=({cx0},{cy0})-({cx1},{cy1}) -> {zoom.width}x{zoom.height}")

print("OK:", len(ITEMS), "planchas en", OUT)
