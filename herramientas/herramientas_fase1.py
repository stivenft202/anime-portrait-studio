#!/usr/bin/env python3
"""Herramientas de apoyo Fase 1 (Anime Half Portrait Studio).

Subcomandos:
  normalizar IN OUT      Escala uniforme por altura a 1600 y recorta/rellena
                         en horizontal centrado en x=580/1200 -> 1200x1600.
                         El relleno es magenta puro (lo quita la extraccion).
  medir IMG              Imprime bbox del alfa y porcentajes.
  trasladar IN OUT DX DY [ESCALA]  Desplaza la capa (y escala uniforme
                         alrededor del ancla 580,470 si ESCALA != 1).
  componer OUT CAPA1 [CAPA2 ...]   Compone las capas (de atras a adelante)
                         sobre fondo gris claro y guarda la prueba.
"""
import sys

import numpy as np
from PIL import Image

W, H = 1200, 1600
ANCHOR = (580, 470)
MAGENTA = (255, 0, 255)


def normalizar(ruta_in, ruta_out):
    img = Image.open(ruta_in).convert("RGB")
    w, h = img.size
    s = H / h
    nw = round(w * s)
    img = img.resize((nw, H), Image.LANCZOS)
    lienzo = Image.new("RGB", (W, H), MAGENTA)
    # Centro horizontal en la fraccion del centro de cara (580/1200).
    cx = nw * (580 / W)
    x0 = int(round(580 - cx))
    lienzo.paste(img, (x0, 0))
    lienzo.save(ruta_out)
    print(f"normalizar: {ruta_in} {w}x{h} -> {ruta_out} 1200x1600 (escala {s:.3f}, x0={x0})")


def medir(ruta):
    img = Image.open(ruta).convert("RGBA")
    al = np.asarray(img)[..., 3]
    ys, xs = np.where(al > 25)
    if len(xs) == 0:
        print(f"{ruta}: SIN contenido")
        return
    print(f"{ruta}: {img.size[0]}x{img.size[1]} bbox x {xs.min()}..{xs.max()} "
          f"y {ys.min()}..{ys.max()} | opaco={(al > 250).mean() * 100:.1f}% "
          f"visible={(al > 25).mean() * 100:.1f}%")


def trasladar(ruta_in, ruta_out, dx, dy, escala=1.0):
    img = Image.open(ruta_in).convert("RGBA")
    if escala != 1.0:
        nw, nh = round(W * escala), round(H * escala)
        img = img.resize((nw, nh), Image.LANCZOS)
        # Tras escalar alrededor del ancla: el ancla queda en ANCHOR*escala.
        ox = int(round(ANCHOR[0] - ANCHOR[0] * escala)) + int(dx)
        oy = int(round(ANCHOR[1] - ANCHOR[1] * escala)) + int(dy)
    else:
        ox, oy = int(dx), int(dy)
    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lienzo.alpha_composite(img, (ox, oy))
    lienzo.save(ruta_out)
    print(f"trasladar: {ruta_in} -> {ruta_out} dx={ox} dy={oy} escala={escala}")


def componer(ruta_out, capas):
    fondo = Image.new("RGBA", (W, H), (225, 228, 235, 255))
    for c in capas:
        fondo.alpha_composite(Image.open(c).convert("RGBA"), (0, 0))
    fondo.convert("RGB").save(ruta_out)
    print(f"componer: {ruta_out} <- {len(capas)} capas")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "normalizar":
        normalizar(sys.argv[2], sys.argv[3])
    elif cmd == "medir":
        medir(sys.argv[2])
    elif cmd == "trasladar":
        esc = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
        trasladar(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), esc)
    elif cmd == "componer":
        componer(sys.argv[2], sys.argv[3:])
    else:
        print(__doc__)
        sys.exit(1)
