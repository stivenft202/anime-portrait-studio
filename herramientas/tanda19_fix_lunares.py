# tanda19_fix_lunares.py — Tanda 19: lunares en boca y nariz.
# Diagnóstico (verificado en el vídeo frame a frame y en las capas a 4x):
#  NARIZ — la "coma" oscura de Nose2 (mujer y hombre) se lee como un lunar en
#    la punta de la nariz; Nose1 hombre tiene motitas sueltas alrededor de la
#    fosa; Nose1 mujer una motita en la piel junto a la nariz.
#  BOCA — la sombra de la comisura + borde inferior del labio en la capa Base
#    (ambos sexos) forman una mancha negra en la esquina de la boca, en TODOS
#    los combos; además ticks sueltos en Mouth_Happy (mujer/hombre) y un trazo
#    suelto bajo Mouth_Neutral (hombre).
# Método stage20: snapshot antes, operaciones por componente (no a mano),
# asserts de 0 px fuera de los objetivos, re-verificación por escaneo.
#  - Borrar (alfa=0): componentes oscuras aisladas y las comas de Nose2.
#  - Aclarar (mezcla 60% hacia piel local): sombra de comisura + borde labio
#    en Base (se conserva la forma como sombra suave, no se borra el dibujo).
#  - NO se toca: la línea de la nariz, los trazos finos de fosa nasal
#    (Nose1 22px, Nose3 81px), la línea de la boca ni la cuña de la comisura
#    propia de cada boca, la línea de la barbilla.
import os, shutil
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
SNAP = os.path.join(BASE, 'versiones/2026-11-23_tanda19-antes-lunares')
os.makedirs(SNAP, exist_ok=True)

# (sexo, archivo, [(cx, cy) de cada componente a borrar])
BORRAR = [
    ('Female', 'Nose1.png', [(362, 713), (324, 704), (318, 684)]),
    ('Female', 'Nose2.png', [(329, 700), (323, 706), (322, 705), (321, 703)]),
    ('Female', 'Nose3.png', [(323, 706), (322, 705), (321, 703)]),
    ('Male', 'Nose1.png', [(293, 639), (302, 702), (300, 631), (312, 728), (312, 710), (312, 724), (306, 624)]),
    ('Male', 'Nose2.png', [(279, 688)]),
    ('Female', 'Mouth_Happy.png', [(452, 776), (450, 774)]),
    ('Male', 'Mouth_Happy.png', [(410, 768), (366, 763)]),
    ('Male', 'Mouth_Neutral.png', [(339, 804)]),
]
# (sexo, archivo, [(cx, cy) de cada componente a aclarar])
ACLARAR = [
    ('Female', 'Base.png', [(364, 772), (381, 808)]),
    ('Male', 'Base.png', [(332, 779), (315, 753)]),
]
MEZCLA = 0.60  # 60% hacia piel local

def componentes_oscuros(im):
    a = im[..., 3]
    gris = im[..., :3].astype(int).min(axis=2)
    oscuro = (a > 150) & (gris < 100)
    lab, n = ndimage.label(oscuro)
    comps = {}
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        comps[(int(xs.mean()), int(ys.mean()))] = (lab == i)
    return comps

def piel_local(im):
    # mediana de piel de la mejilla (x450-550, y650-750), píxeles opacos
    zona = im[650:750, 450:550]
    mask = zona[..., 3] > 200
    px = zona[mask][:, :3].astype(float)
    return np.median(px, axis=0)

total_borrados = 0
for sexo, f, objetivos in BORRAR:
    p = os.path.join(A, sexo, f)
    shutil.copy2(p, os.path.join(SNAP, f"{sexo}_{f}"))
    orig = np.array(Image.open(p).convert('RGBA'))
    im = orig.copy()
    comps = componentes_oscuros(im)
    cambiados = np.zeros(im.shape[:2], bool)
    for (cx, cy) in objetivos:
        assert (cx, cy) in comps, f"{sexo}/{f}: componente ({cx},{cy}) no hallada"
        m = comps[(cx, cy)]
        total_borrados += int(m.sum())
        im[m, 3] = 0
        cambiados |= m
    dif_rgb = np.abs(im[..., :3].astype(int) - orig[..., :3].astype(int)).sum(axis=2)
    assert (dif_rgb == 0).all(), f"{sexo}/{f}: cambió RGB fuera de lo previsto"
    # assert: solo alfa de los objetivos cambió (los componentes incluyen
    # píxeles semitransparentes de borde, alfa 150-255, así que la caída
    # de alfa es -(alfa original), no solo -255)
    dif_a = im[..., 3].astype(int) - orig[..., 3].astype(int)
    assert (dif_a <= 0).all(), f"{sexo}/{f}: alfa aumentó en algún px"
    assert (dif_a != 0).sum() == int(cambiados.sum()), f"{sexo}/{f}: alfa cambió fuera de objetivos"
    Image.fromarray(im).save(p)
    print(f"BORRADO {sexo}/{f}: {int(cambiados.sum())} px en {len(objetivos)} componentes")

total_aclarados = 0
for sexo, f, objetivos in ACLARAR:
    p = os.path.join(A, sexo, f)
    if not os.path.exists(os.path.join(SNAP, f"{sexo}_{f}")):
        shutil.copy2(p, os.path.join(SNAP, f"{sexo}_{f}"))
    orig = np.array(Image.open(p).convert('RGBA'))
    im = orig.copy()
    piel = piel_local(orig)
    comps = componentes_oscuros(im)
    cambiados = np.zeros(im.shape[:2], bool)
    for (cx, cy) in objetivos:
        assert (cx, cy) in comps, f"{sexo}/{f}: componente ({cx},{cy}) no hallada"
        m = comps[(cx, cy)]
        total_aclarados += int(m.sum())
        im[m, :3] = np.clip(0.4 * im[m, :3].astype(float) + MEZCLA * piel, 0, 255).astype('uint8')
        cambiados |= m
    dif_a = im[..., 3].astype(int) - orig[..., 3].astype(int)
    assert (dif_a == 0).all(), f"{sexo}/{f}: cambió alfa al aclarar"
    dif_rgb = np.abs(im[..., :3].astype(int) - orig[..., :3].astype(int)).sum(axis=2)
    assert ((dif_rgb != 0) == cambiados).all(), f"{sexo}/{f}: RGB cambió fuera de objetivos"
    Image.fromarray(im).save(p)
    print(f"ACLARADO {sexo}/{f}: {int(cambiados.sum())} px en {len(objetivos)} componentes (piel local {piel.astype(int)})")

print(f"TOTAL borrados: {total_borrados} px | TOTAL aclarados: {total_aclarados} px")
print("Snapshot en", SNAP)
