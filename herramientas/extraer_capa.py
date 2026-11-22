#!/usr/bin/env python3
"""Extrae el alfa de una capa generada sobre fondo magenta puro (#FF00FF).

Uso: python3 extraer_capa.py entrada.png salida.png

Metodo: alfa por distancia de color al magenta (el color clave se estima de
las esquinas de la imagen, que siempre son fondo; si no parecen magenta se
usa #FF00FF puro) + defringe: en los pixeles semitransparentes se
des-premultiplica la contribucion del fondo para quitar el tinte magenta
de los bordes.
"""
import sys

import numpy as np
from PIL import Image


def main() -> None:
    if len(sys.argv) != 3:
        print("uso: python3 extraer_capa.py entrada.png salida.png")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]

    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)

    # Color clave: se toman bloques de las 4 esquinas y del borde superior
    # (las esquinas inferiores pueden ser la prenda, porque el torso llega
    # hasta el borde inferior). De esos pixeles solo se usan los que son
    # claramente magenta (R y B altos, G bajo) y se toma su mediana; si hay
    # muy pocos, se usa magenta puro.
    h, w = a.shape[:2]
    blocks = [
        a[:10, :10], a[:10, -10:], a[-10:, :10], a[-10:, -10:],
        a[:10, w // 2 - 5:w // 2 + 5], a[-10:, w // 2 - 5:w // 2 + 5],
    ]
    pix = np.concatenate([b.reshape(-1, 3) for b in blocks])
    mask = (pix[:, 0] > 150) & (pix[:, 1] < 110) & (pix[:, 2] > 150)
    if int(mask.sum()) >= 20:
        key = np.median(pix[mask], axis=0)
    else:
        key = np.array([255.0, 0.0, 255.0], dtype=np.float32)

    # Alfa por distancia euclidea al color clave.
    d = np.sqrt(((a - key) ** 2).sum(axis=2))
    t0, t1 = 55.0, 170.0
    alpha = np.clip((d - t0) / (t1 - t0), 0.0, 1.0)

    # Defringe: pixel = alfa*fg + (1-alfa)*fondo  =>  fg = (pixel - (1-alfa)*fondo)/alfa
    out = a.copy()
    semi = (alpha > 0.0) & (alpha < 1.0)
    if semi.any():
        al = alpha[semi][:, None]
        fg = (a[semi] - (1.0 - al) * key[None, :]) / np.maximum(al, 1e-4)
        out[semi] = np.clip(fg, 0, 255)

    rgba = np.dstack([out, alpha * 255.0]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(dst)
    print(
        f"OK {dst}: clave={key.astype(int).tolist()} "
        f"transparente={100.0 * (alpha == 0).mean():.1f}% "
        f"opaco={100.0 * (alpha == 1).mean():.1f}%"
    )


if __name__ == "__main__":
    main()
