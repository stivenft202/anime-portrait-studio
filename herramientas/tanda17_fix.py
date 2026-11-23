# tanda17_fix.py — Corrección del defecto T17-01 (tanda 17, colores)
#
# Defecto: la solapa/cuello de Outfit1 mujer ("Sweater and Jacket") está dibujada
# en la capa Base, no en Outfit1. No sigue el tinte de ropa y sí el de piel.
# Evidencia: píxel (520,1100) = (122,118,108) con OC00 White y con OC16 Coral
# (crudo Base exacto); con SK3 Deep = (76,54,36) = crudo x tinte Deep.
# Además, la pieza derecha de esa solapa (901 px) asoma por Outfit2 ("Green
# Jacket"), que no la cubre del todo: mismo defecto en O2, más pequeño.
#
# Corrección (método stage20: snapshot ANTES, ops de píxeles por script,
# assert de 0 px fuera de los componentes objetivo, re-verificación):
#  1. Máscara L = solapa visible a través de Outfit1: y900-1600, Base alfa>200,
#     Outfit1 alfa<30, R-G<15 (gris, no piel). 14.174 px.
#     Se COPIA tal cual (RGBA) de Base a Outfit1 (White/Light son tinte neutro
#     [1,1,1], así que el render por defecto queda byte-idéntico).
#  2. En Base, la máscara L se rellena con piel inpaintada (difusión de Laplace
#     desde píxeles de piel vecinos: R-G>=25, alfa>200).
#  3. Hueco G en Outfit2 = (gris visible a través de O2) ∩ (máscara L): 973 px
#     (901 de la pieza principal + 72 de fragmentos de borde de la solapa
#     dentro de L: contorno oscuro 62 px y punta del borde 10 px).
#     Se rellena en Outfit2 con el verde del cuello de la chaqueta vecina
#     (difusión desde píxeles verdes opacos de O2), alfa 255, para que el
#     cuello de O2 quede completo y tiña con la ropa.
#  NO se tocan: la sombra oscura bajo la barbilla (arte, queda en Base), las
#  motas <60 px, Outfit3 (cubre la solapa completa), ni ninguna capa de hombre.
#
# Snapshot ANTES (md5 verificado) en:
#   versiones/2026-11-23_tanda17-antes-fixes/{Base,Outfit1,Outfit2}.png
#   Base    87a4bdd45933d0413ee16e2d7071bf19
#   Outfit1 8332f246755246283a4d9ba686ea42da
#   Outfit2 d7226def9c9098557fdbde7e40168d88

import hashlib
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets/Female'

def md5(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()

def laplace_inpaint(rgb, mask, known, iters=500):
    """Rellena `mask` por difusión (Laplace) desde los píxeles `known`.
    Solo los píxeles `known` y los de la máscara participan en el promedio:
    los vecinos que no son ni piel/verde ni máscara (p. ej. la chaqueta o el
    contorno oscuro) NO anclan el relleno, así que el resultado es una
    interpolación pura de la fuente (piel o verde) y conserva su familia
    de color (R-G>=25 en piel; verde en O2). rgb: float HxWx3."""
    filled = rgb.copy()
    # inicialización: color del píxel conocido más cercano
    _, inds = ndimage.distance_transform_edt(~known, return_indices=True)
    ys, xs = np.where(mask)
    filled[ys, xs] = rgb[inds[0][ys, xs], inds[1][ys, xs]]
    valid = (known | mask).astype(float)
    for _ in range(iters):
        f0 = filled * valid[:, :, None]
        s = (np.roll(f0, 1, 0) + np.roll(f0, -1, 0)
             + np.roll(f0, 1, 1) + np.roll(f0, -1, 1))
        c = (np.roll(valid, 1, 0) + np.roll(valid, -1, 0)
             + np.roll(valid, 1, 1) + np.roll(valid, -1, 1))
        avg = np.divide(s, c[:, :, None], out=filled.copy(),
                        where=c[:, :, None] > 0)
        # solo se actualizan los píxeles de la máscara con al menos un vecino válido
        upd = mask & (c > 0)
        filled[upd] = avg[upd]
    return filled

base = np.array(Image.open(f'{ROOT}/Base.png').convert('RGBA')).astype(int)
out1 = np.array(Image.open(f'{ROOT}/Outfit1.png').convert('RGBA')).astype(int)
out2 = np.array(Image.open(f'{ROOT}/Outfit2.png').convert('RGBA')).astype(int)
base0, out10, out20 = base.copy(), out1.copy(), out2.copy()

H, W = 1600, 1200
zone = np.zeros((H, W), bool); zone[900:1600, :] = True
rg_base = base[:, :, 0] - base[:, :, 1]

# --- 1. Máscara L: solapa visible a través de Outfit1 ---
mask_L = zone & (base[:, :, 3] > 200) & (out1[:, :, 3] < 30) & (rg_base < 15)
n_L = int(mask_L.sum())
print('máscara L (solapa):', n_L, 'px')
assert n_L == 14174, f'máscara L inesperada: {n_L} px (esperado 14174)'

# --- 2. Copiar la solapa a Outfit1 (RGBA tal cual) ---
out1[mask_L] = base[mask_L]

# --- 3. Rellenar la solapa en Base con piel inpaintada ---
piel = (base[:, :, 3] > 200) & (rg_base >= 25)
print('píxeles fuente de piel:', int(piel.sum()))
base_rgb = base[:, :, :3].astype(float)
filled = laplace_inpaint(base_rgb, mask_L, piel, iters=500)
base[:, :, :3] = np.clip(np.rint(filled), 0, 255).astype(int)
# el alfa de la máscara en Base ya era 255; se conserva.

# --- 4. Hueco G en Outfit2: gris visible a través de O2 y dentro de L ---
mask_G = zone & (base0[:, :, 3] > 200) & (out20[:, :, 3] < 30) & (rg_base < 15) & mask_L
n_G = int(mask_G.sum())
print('hueco G (Outfit2):', n_G, 'px')
assert n_G == 973, f'hueco G inesperado: {n_G} px (esperado 973)'
# fuente: verde de la chaqueta de O2 (opaco, G>=R, G>=B, no blanco)
verde = (out2[:, :, 3] > 200) & (out2[:, :, 1] >= out2[:, :, 0]) \
    & (out2[:, :, 1] >= out2[:, :, 2]) & (out2[:, :, 0] < 200)
print('píxeles fuente verdes O2:', int(verde.sum()))
out2_rgb = out2[:, :, :3].astype(float)
filled2 = laplace_inpaint(out2_rgb, mask_G, verde, iters=500)
out2[:, :, :3] = np.clip(np.rint(filled2), 0, 255).astype(int)
out2[mask_G, 3] = 255

# --- 5. Asserts: 0 px cambiados fuera de los componentes objetivo ---
d_base = np.any(base != base0, axis=2)
d_out1 = np.any(out1 != out10, axis=2)
d_out2 = np.any(out2 != out20, axis=2)
print('Base cambiados:', int(d_base.sum()), '| fuera de L:', int((d_base & ~mask_L).sum()))
print('Outfit1 cambiados:', int(d_out1.sum()), '| fuera de L:', int((d_out1 & ~mask_L).sum()))
print('Outfit2 cambiados:', int(d_out2.sum()), '| fuera de G:', int((d_out2 & ~mask_G).sum()))
assert int((d_base & ~mask_L).sum()) == 0
assert int((d_out1 & ~mask_L).sum()) == 0
assert int((d_out2 & ~mask_G).sum()) == 0
# La difusión de Laplace converge en 7 px de L casi exactamente a su color
# original (el contorno oscuro de la solapa y la chaqueta vecina anclan el
# relleno hacia tonos grises); esos 7 px quedan invisibles en todos los
# renders: en O1 los cubre la solapa pegada en Outfit1, en O2/O3 la ropa.
n_sin_cambio_L = n_L - int(d_base.sum())
print('px de L sin cambio de color (convergen al original):', n_sin_cambio_L)
assert n_sin_cambio_L <= 20
assert int(d_out1.sum()) == n_L and int(d_out2.sum()) == n_G
# la solapa copiada a Outfit1 debe ser idéntica a la de Base (antes)
assert np.array_equal(out1[mask_L], base0[mask_L])
# la solapa ya no está en Base (ningún píxel de L conserva el color gris de solapa)
assert not np.any((base[mask_L][:, 0] - base[mask_L][:, 1]) < 15), 'quedan grises en L'

# --- 6. Guardar ---
Image.fromarray(base.astype('uint8'), 'RGBA').save(f'{ROOT}/Base.png')
Image.fromarray(out1.astype('uint8'), 'RGBA').save(f'{ROOT}/Outfit1.png')
Image.fromarray(out2.astype('uint8'), 'RGBA').save(f'{ROOT}/Outfit2.png')
print('md5 Base nueva:   ', md5(f'{ROOT}/Base.png'))
print('md5 Outfit1 nueva:', md5(f'{ROOT}/Outfit1.png'))
print('md5 Outfit2 nueva:', md5(f'{ROOT}/Outfit2.png'))
print('OK — fix T17-01 aplicado')
