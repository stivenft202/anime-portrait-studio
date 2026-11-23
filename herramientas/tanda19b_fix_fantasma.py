# tanda19b_fix_fantasma.py — Tanda 19b, CAUSA RAÍZ de los puntos café en bocas.
#
# CAUSA RAÍZ (probada): la capa Base trae una "BOCA FANTASMA": restos de la
# boca original que quedó en la cara cuando se separó en capas — una línea
# de boca rota en segmentos, manchas de sombra del labio y (hombre) un
# bloque gris manchado en la esquina de la boca, justo donde va la boca
# real. Cada render superpone la boca real (capa Mouth) sobre esa fantasma.
# Los segmentos rotos y las manchas se leen como puntos/lunares café.
# Está en Base → aparece en TODOS los combos de ese sexo, con cualquier
# boca y nariz → por eso "siguen apareciendo en combos nuevos".
# La Tanda 19 no la vio porque solo buscaba píxeles casi negros (gris<100);
# la fantasma es MARRÓN MEDIO (gris 100-205), en muchos componentes.
#
# FIX DE RAÍZ: terminar de quitar la boca fantasma de Base (ambos sexos):
#  - INPAINT con piel (difusión de Laplace, como T17-01): la línea fantasma,
#    la esquina, las manchas del labio inferior y el bloque gris del hombre.
#    La boca real la dibuja siempre la capa Mouth, así que no se pierde nada.
#  - MEZCLA 85% hacia piel (sombra muy tenue, se conserva el modelado):
#    surco del filtrum y sombra de la barbilla.
#  - NO se toca: el contorno de la nariz, el perfil de la cara, la línea
#    de la mandíbula/barbilla, ni ninguna capa Mouth/Nose.
import os, shutil
import numpy as np
from PIL import Image

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
SNAP = os.path.join(BASE, 'versiones/2026-11-23_tanda19b-antes-fantasma')
os.makedirs(SNAP, exist_ok=True)

def es_cafe(im):
    r, g, b, al = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    lum = (r.astype(int) + g.astype(int) + b.astype(int)) // 3
    return (al > 80) & (lum < 205) & ((r.astype(int) - b.astype(int)) > 25)

def piel_local(im):
    zona = im[650:750, 450:550]
    mask = zona[..., 3] > 200
    return np.median(zona[mask][:, :3].astype(float), axis=0)

def inpaint_piel(im, mask, iters=500):
    """Rellena los píxeles de mask con piel por difusión de Laplace desde
    los píxeles vecinos no enmascarados (solo RGB; alfa intacta)."""
    out = im[..., :3].astype(float).copy()
    m = mask.copy()
    # inicializar con el color de piel local para acelerar
    piel = piel_local(im)
    out[m] = piel
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) +
               np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4.0
        out[m] = avg[m]
    im2 = im.copy()
    im2[..., :3] = np.clip(out, 0, 255).astype('uint8')
    return im2

def rect_mask(shape, rects):
    m = np.zeros(shape[:2], bool)
    for (x0, y0, x1, y1) in rects:
        m[y0:y1, x0:x1] = True
    return m

# (sexo, rects a INPAINT, rects a MEZCLAR 85%)
PLAN = {
    'Female': (
        # línea fantasma + esquina + manchas labio inferior + extremo derecho
        [(360, 763, 436, 819)],
        # filtrum y barbilla: sombra tenue
        [(350, 720, 368, 752), (390, 814, 408, 830)],
    ),
    'Male': (
        # bloque gris + esquina + parche 350px + marca vertical
        [(300, 740, 345, 790), (339, 775, 354, 801), (313, 739, 318, 769)],
        # barbilla: sombra tenue
        [(356, 810, 385, 820)],
    ),
}
MEZCLA = 0.85

for sexo, (rects_inp, rects_mez) in PLAN.items():
    p = os.path.join(A, sexo, 'Base.png')
    shutil.copy2(p, os.path.join(SNAP, f"{sexo}_Base.png"))
    orig = np.array(Image.open(p).convert('RGBA'))
    im = orig.copy()
    cafe = es_cafe(im)
    # --- INPAINT ---
    mask_inp = cafe & rect_mask(im.shape, rects_inp)
    n_inp = int(mask_inp.sum())
    if n_inp:
        im = inpaint_piel(im, mask_inp)
    # --- MEZCLA 85% ---
    mask_mez = cafe & rect_mask(im.shape, rects_mez)
    n_mez = int(mask_mez.sum())
    piel = piel_local(orig)
    if n_mez:
        im[mask_mez, :3] = np.clip(0.15 * im[mask_mez, :3].astype(float) + MEZCLA * piel, 0, 255).astype('uint8')
    # --- ASSERTS: ningún cambio fuera de los objetivos; alfa intacta ---
    # (OJO: un píxel objetivo puede quedar con el mismo valor tras el
    # inpaint/mezcla, así que NO se exige que todos los objetivos cambien,
    # solo que nada fuera de ellos cambie.)
    assert (im[..., 3] == orig[..., 3]).all(), f"{sexo}: cambió alfa"
    dif = np.abs(im[..., :3].astype(int) - orig[..., :3].astype(int)).sum(axis=2) > 0
    assert not (dif & ~(mask_inp | mask_mez)).any(), f"{sexo}: RGB cambió fuera de objetivos"
    Image.fromarray(im).save(p)
    print(f"{sexo}/Base.png: inpaint {n_inp} px + mezcla {n_mez} px (piel {piel.astype(int)})")
print('Snapshot en', SNAP)
