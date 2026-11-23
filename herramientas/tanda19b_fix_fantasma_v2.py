# tanda19b_fix_fantasma_v2.py — Segunda pasada del fix de causa raíz.
#
# Lo que quedó tras la v1 (verificado a ojo en BASE_boca_*_DESPUES.png):
#  1) Núcleos OSCUROS de la línea fantasma (casi negros, R-B<25): la
#     máscara "café" (R-B>25) no los incluía, así que quedaron como
#     puntitos oscuros en los extremos de la línea (F: 23px, 16px, 13px...).
#  2) El parche de 350px del hombre (y el bloque gris) se rellenó con
#     marrón: la difusión de Laplace promedia los vecinos, y los vecinos
#     son la mancha marrón de la nariz (2099px). El relleno salió marrón.
# FIX v2: máscara = TODOS los píxeles oscuros (lum<205), no solo los
# cafés; tras el inpaint, mezcla del 80% hacia piel de mejilla para que
# el relleno sea piel limpia aunque los vecinos sean marrones.
import os, shutil
import numpy as np
from PIL import Image

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
SNAP = os.path.join(BASE, 'versiones/2026-11-23_tanda19b-antes-fantasma')

def es_oscuro(im):
    r, g, b, al = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    lum = (r.astype(int) + g.astype(int) + b.astype(int)) // 3
    return (al > 80) & (lum < 205)

def piel_local(im):
    zona = im[650:750, 450:550]
    mask = zona[..., 3] > 200
    return np.median(zona[mask][:, :3].astype(float), axis=0)

def inpaint_piel(im, mask, iters=500):
    out = im[..., :3].astype(float).copy()
    piel = piel_local(im)
    out[mask] = piel
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) +
               np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4.0
        out[mask] = avg[mask]
    im2 = im.copy()
    im2[..., :3] = np.clip(out, 0, 255).astype('uint8')
    return im2

def rect_mask(shape, rects):
    m = np.zeros(shape[:2], bool)
    for (x0, y0, x1, y1) in rects:
        m[y0:y1, x0:x1] = True
    return m

PLAN = {
    'Female': [(360, 763, 436, 819)],
    'Male': [(300, 740, 345, 790), (339, 775, 354, 801), (313, 739, 318, 769)],
}
MEZCLA_PIEL = 0.80

for sexo, rects in PLAN.items():
    p = os.path.join(A, sexo, 'Base.png')
    # snapshot de la v1 (estado actual antes de la v2)
    shutil.copy2(p, os.path.join(SNAP, f"{sexo}_Base_v1.png"))
    orig = np.array(Image.open(p).convert('RGBA'))
    im = orig.copy()
    mask = es_oscuro(im) & rect_mask(im.shape, rects)
    n = int(mask.sum())
    piel = piel_local(orig)
    if n:
        im = inpaint_piel(im, mask)
        # forzar piel limpia: 80% hacia piel de mejilla
        im[mask, :3] = np.clip(0.20 * im[mask, :3].astype(float) + MEZCLA_PIEL * piel, 0, 255).astype('uint8')
    assert (im[..., 3] == orig[..., 3]).all(), f"{sexo}: cambió alfa"
    dif = np.abs(im[..., :3].astype(int) - orig[..., :3].astype(int)).sum(axis=2) > 0
    assert not (dif & ~mask).any(), f"{sexo}: RGB cambió fuera de objetivos"
    Image.fromarray(im).save(p)
    print(f"{sexo}/Base.png v2: inpaint+piel {n} px (piel {piel.astype(int)})")
print('Snapshot v1 en', SNAP)
