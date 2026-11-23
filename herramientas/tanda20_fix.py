"""Tanda 20 — errores de las 2 capturas de Stiven (2026-11-23 ~15:50).
Revisión POR CAPA (orden de Stiven: no barrer combos).

Hallazgos (medidos en la capa, no en el render):
1. Base F, punta de la nariz: mancha oscura y sucia en la punta
   (202 px lum<130 en x316-328 y675-706 + 941 px marrones) y una motita
   negra. La capa Nose3 está LIMPIA (0 px oscuros/marrones): la mancha
   es de la Base. Fix: aclarar la mancha mezclando 65% hacia la piel
   local (queda una sombra suave, no se borra la nariz) y borrar la
   motita negra por inpaint.
2. Base M, frente: dos triángulos marrones (sombra de pelo geométrica
   que asoma como mancha). Chico 115 px en x464-478 y400-422 (visible
   con H2/H3 — el combo de Stiven es H3). Grande 950 px en x400-431
   y311-383 (visible con H1, 27% sin cubrir). Fix: inpaint con piel.
3. Pelo H4 (mujer) y H3 (hombre): halo claro en el borde (defringe,
   misma clase que en las ropas del súper método). Fix: recolorear los
   píxeles claros del borde al color del pelo vecino (sin borrar hebras;
   las hebras sueltas son diseño del pelo ondulado).
El ojo Gris moteado es un problema del TINTE (_ojos_tinte), no de la
capa Eyes_Angry (el arte verde está limpio); se trata aparte.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')

def cargar(sexo, f):
    p = os.path.join(ROOT, 'version-linux/assets', sexo, f)
    return p, np.array(Image.open(p).convert('RGBA')).astype(int)

def guardar(p, a):
    Image.fromarray(a.astype(np.uint8)).save(p)

def inpaint(a, mask, iters=400):
    """Difusión de Laplace desde los píxeles vecinos no enmascarados."""
    m = mask.astype(bool)
    out = a.astype(float).copy()
    # semilla: media de vecinos no-máscara (solo RGB; alfa se conserva)
    for _ in range(iters):
        for c in range(3):
            ch = out[..., c]
            prom = (np.roll(ch, 1, 0) + np.roll(ch, -1, 0)
                    + np.roll(ch, 1, 1) + np.roll(ch, -1, 1)) / 4
            ch[m] = prom[m]
            out[..., c] = ch
    return out

def assert_solo_mascara(antes, despues, mask, nombre):
    dif = np.any(antes != despues, axis=2)
    fuera = dif & ~mask
    assert fuera.sum() == 0, f'{nombre}: {fuera.sum()} px fuera de máscara!'
    print(f'{nombre}: {int(mask.sum())} px, 0 fuera de máscara')

# ---- 1. Base F: nariz ----
p, a = cargar('Female', 'Base.png')
antes = a.copy()
r, g, b, alpha = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
lum = (r + g + b) / 3
piel = np.array([247.0, 219.0, 202.0])
yy, xx = np.mgrid[0:1600, 0:1200]
zona = (xx >= 305) & (xx <= 365) & (yy >= 650) & (yy <= 745)
oscura = zona & (alpha > 150) & (lum < 160)
# motita negra: muy oscura -> inpaint; resto oscuro -> aclarar 65% hacia piel
negra = oscura & (lum < 85)
aclarar = oscura & ~negra
a2 = a.astype(float).copy()
for c in range(3):
    a2[..., c] = np.where(aclarar, a[..., c] * 0.35 + piel[c] * 0.65, a2[..., c])
a2 = inpaint(a2, negra, iters=200)
a = np.clip(a2, 0, 255).astype(int)
a[..., 3] = antes[..., 3]
guardar(p, a)
assert_solo_mascara(antes, a, oscura, 'Base F nariz')

# ---- 2. Base M: triángulos de la frente ----
p, a = cargar('Male', 'Base.png')
antes = a.copy()
r, g, b, alpha = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
lum = (r + g + b) / 3
yy, xx = np.mgrid[0:1600, 0:1200]
tri_chico = (xx >= 460) & (xx <= 482) & (yy >= 396) & (yy <= 426) & (alpha > 150) & (lum < 200) & ((r - b) > 15)
tri_grande = (xx >= 396) & (xx <= 435) & (yy >= 307) & (yy <= 387) & (alpha > 150) & (lum < 200) & ((r - b) > 15)
mask = tri_chico | tri_grande
a2 = inpaint(a.astype(float), mask, iters=400)
a = np.clip(a2, 0, 255).astype(int)
a[..., 3] = antes[..., 3]
guardar(p, a)
assert_solo_mascara(antes, a, mask, 'Base M frente')

# ---- 3. Defringe en pelos H4 F y H3 M ----
for sexo, f in [('Female', 'Hair4_Front.png'), ('Female', 'Hair4_Back.png'),
                ('Male', 'Hair3_Front.png'), ('Male', 'Hair3_Back.png')]:
    p, a = cargar(sexo, f)
    antes = a.copy()
    alpha = a[..., 3]
    lum = a[..., :3].mean(axis=2)
    op = alpha > 200
    borde = ndimage.binary_dilation(op, iterations=2) & ~op
    halo = borde & (alpha > 20) & (alpha < 200) & (lum > 165)
    # recolor: color del píxel opaco más cercano
    _, inds = ndimage.distance_transform_edt(~op, return_indices=True)
    a2 = a.copy()
    ys, xs = np.where(halo)
    a2[ys, xs, 0] = a[inds[0][ys, xs], inds[1][ys, xs], 0]
    a2[ys, xs, 1] = a[inds[0][ys, xs], inds[1][ys, xs], 1]
    a2[ys, xs, 2] = a[inds[0][ys, xs], inds[1][ys, xs], 2]
    guardar(p, a2)
    assert_solo_mascara(antes, a2, halo, f'{sexo}/{f} defringe')

print('OK')
