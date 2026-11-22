#!/usr/bin/env python3
"""Extrae una capa desde una EDICION de la base (misma escena con un agregado).

La edicion se genero pidiendo dibujar SOLO el agregado (rasgos faciales o
pelo) sobre la base calva. La capa se recupera por diferencia contra la base
+ reglas de color + limpieza de componentes (calibrado con diagnostico:
en expresiones el ruido es la oreja y los bordes de mandibula repintados;
en pelo, sombras de cuello/camisa y el borde del brazo).

Uso:
  python3 extraer_dif.py expr EDIT BASE_NORM SALIDA
  python3 extraer_dif.py pelo EDIT BASE_NORM BASE_RGBA SAL_TRASERO SAL_DELANTERO
"""
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def cargar_rgb(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


def guardar(edit, alpha_f, ruta):
    rgba = np.dstack([edit, alpha_f])
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").save(ruta)
    ys, xs = np.where(alpha_f > 25)
    bb = (f"x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}"
          if len(xs) else "VACIO")
    print(f"{ruta}: visible={(alpha_f > 25).mean() * 100:.2f}% bbox {bb}")


def rect(mask_shape, x0, y0, x1, y1):
    r = np.zeros(mask_shape, bool)
    r[y0:y1, x0:x1] = True
    return r


def modo_expr(edit_p, base_p, salida):
    edit = cargar_rgb(edit_p)
    base = cargar_rgb(base_p)
    diff = np.abs(edit - base).max(axis=2)
    mx = edit.max(axis=2)
    mn = edit.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    mask = diff > 38
    # Rasgos: oscuros (pestanas/cejas), saturados (iris/boca) o blancos (esclera)
    feat = (mx < 135) | (sat > 0.20) | ((mx > 248) & (diff > 60))
    mask &= feat
    # Nunca magenta: la saturacion del magenta (=1) cuela por la regla de
    # saturados los pixeles de fondo que la edicion movio junto a la cara.
    r_, g_, b_ = edit[..., 0], edit[..., 1], edit[..., 2]
    mask &= ~((np.minimum(r_, b_) - g_) > 50)
    # Region permitida: rectangulo de ojos/cejas + rectangulo de boca,
    # menos el rectangulo de la nariz (la capa es SOLO ojos+cejas+boca).
    r1 = rect(mask.shape, 325, 315, 715, 570)      # ojos + cejas
    r2 = rect(mask.shape, 430, 595, 580, 690)      # boca
    nariz = rect(mask.shape, 410, 512, 475, 582)
    permitida = (r1 | r2) & ~nariz
    mask &= permitida
    # Componentes: tamano minimo y centroide dentro de la region permitida.
    lab, n = ndimage.label(mask)
    out = np.zeros_like(mask)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() < 25:
            continue
        ys, xs = np.where(comp)
        if permitida[int(ys.mean()), int(xs.mean())]:
            out |= comp
    out &= permitida
    alpha = ndimage.gaussian_filter(out.astype(np.float32) * 255, 0.7)
    guardar(edit, alpha, salida)


def modo_pelo(edit_p, base_p, base_rgba_p, sal_t, sal_d):
    edit = cargar_rgb(edit_p)
    base = cargar_rgb(base_p)
    diff = np.abs(edit - base).max(axis=2)
    mx = edit.max(axis=2)
    mn = edit.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = edit[..., 0], edit[..., 1], edit[..., 2]
    haircolor = (r > b + 12) & (r >= g - 5) & (sat > 0.16) & (mx < 218) & (mx > 38)
    mask = (diff > 30) & haircolor
    # Fuera la zona de rasgos SOLO sobre la piel (lado delantero): si la
    # edicion dibujo cara o flequillo sobre los ojos, no entra. El pelo
    # detras del cuello (sobre fondo, lado trasero) NO se recorta: hacerlo
    # dejaba un corte recto visible a la altura del cuello.
    base_alpha_pre = np.asarray(
        Image.open(base_rgba_p).convert("RGBA"))[..., 3] > 25
    mask &= ~(rect(mask.shape, 390, 400, 790, 760) & base_alpha_pre)
    # Componentes: el pelo es la masa dominante (>=2500 px); se aceptan
    # mechas sueltas >=300 px solo en la zona alta (y<780). El resto es
    # ruido de repintado (cuello, camisa, brazo).
    lab, n = ndimage.label(mask)
    out = np.zeros_like(mask)
    for i in range(1, n + 1):
        comp = lab == i
        sz = comp.sum()
        if sz >= 2500:
            out |= comp
        elif sz >= 300:
            ys, xs = np.where(comp)
            if ys.mean() < 780:
                out |= comp
    mask = out
    # Defringe: erosionar 2 px quita el anillo de pixeles mezclados con el
    # fondo magenta en el borde exterior del pelo.
    mask = ndimage.binary_erosion(mask, iterations=2)
    base_alpha = np.asarray(Image.open(base_rgba_p).convert("RGBA"))[..., 3] > 25
    del_mask = mask & base_alpha
    tra_core = mask & ~base_alpha
    # Underlap del trasero: dilatar 2 px para que no asome piel en el borde.
    # El RGB del anillo se toma del pixel de pelo LIMPIO (color de pelo con
    # margen, sin mezcla magenta) mas cercano, y solo si esta a <=10 px;
    # si no, el anillo se descarta (evita manchas magenta junto a la cara).
    tra_img = Image.fromarray((tra_core * 255).astype(np.uint8)).filter(
        ImageFilter.MaxFilter(5))
    tra_dil = (np.asarray(tra_img) > 0) & ~del_mask
    limpio = tra_core & (sat > 0.25) & (mx < 200)
    dist, indices = ndimage.distance_transform_edt(
        ~limpio, return_indices=True)
    anillo = tra_dil & ~tra_core & (dist <= 10)
    tra_mask = tra_core | anillo
    edit_ext = edit.copy()
    edit_ext[anillo] = edit[tuple(indices)][anillo]
    # Alfa endurecido: corta el velo semitransparente que deja motas.
    def alfa_de(m):
        a = ndimage.gaussian_filter(m.astype(np.float32) * 255, 0.6)
        return np.clip((a - 20) * 1.15, 0, 255)
    guardar(edit_ext, alfa_de(tra_mask), sal_t)
    guardar(edit, alfa_de(del_mask), sal_d)


def modo_ropa(edit_p, base_p, salida):
    """La prenda se edito SOBRE el torso de la base: la capa es todo lo que
    cambio por debajo del cuello (y>=690), en componentes grandes."""
    edit = cargar_rgb(edit_p)
    base = cargar_rgb(base_p)
    diff = np.abs(edit - base).max(axis=2)
    mask = diff > 30
    zona = np.zeros(mask.shape, bool)
    zona[690:, :] = True
    mask &= zona
    # La edicion puede repintar el fondo con un magenta de otro tono: esos
    # pixeles difieren de la base pero NO son prenda. Fuera todo lo que
    # siga pareciendo magenta en la edicion.
    r, g, b = edit[..., 0], edit[..., 1], edit[..., 2]
    mask &= ~((np.minimum(r, b) - g) > 50)
    lab, n = ndimage.label(mask)
    comps = []
    for i in range(1, n + 1):
        sz = (lab == i).sum()
        if sz >= 1500:
            comps.append((sz, i))
    comps.sort(reverse=True)
    out = np.zeros_like(mask)
    for _, i in comps[:4]:
        out |= lab == i
    a = ndimage.gaussian_filter(out.astype(np.float32) * 255, 0.6)
    alpha = np.clip((a - 20) * 1.15, 0, 255)
    guardar(edit, alpha, salida)


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "expr":
        modo_expr(sys.argv[2], sys.argv[3], sys.argv[4])
    elif modo == "pelo":
        modo_pelo(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif modo == "ropa":
        modo_ropa(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
        sys.exit(1)
