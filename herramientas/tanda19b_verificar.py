# tanda19b_verificar.py — Verifica el fix de causa raíz (boca fantasma):
# 1) re-sonda la zona boca de Base: la fantasma debe haber desaparecido
#    (sin componentes café en la línea/esquina/labio inferior).
# 2) re-renderiza los 6 combos del vídeo con motor y los compara con los
#    renders pre-19b (diagnostico_usuario/lunares_boca_nariz/combos_video_postfix/):
#    las diferencias deben estar SOLO en las zonas objetivo de Base.
# 3) construye zooms antes/después de la zona boca (combo 00 y 10) y de la
#    Base sola, para revisión visual.
import os, sys
sys.path.insert(0, '/home/hatch/workspace/anime-portrait-studio/version-linux')
import numpy as np
from PIL import Image
from scipy import ndimage
import motor

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
OUT = os.path.join(BASE, 'diagnostico_usuario/lunares_boca_nariz/causa_raiz')
os.makedirs(OUT, exist_ok=True)
PRE = os.path.join(BASE, 'diagnostico_usuario/lunares_boca_nariz/combos_video_postfix')

def es_cafe(im):
    r, g, b, al = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    lum = (r.astype(int) + g.astype(int) + b.astype(int)) // 3
    return (al > 80) & (lum < 205) & ((r.astype(int) - b.astype(int)) > 25)

print('== 1) Sonda café en zona boca de Base (post-19b) ==')
for sexo, zona in (('Female', (350, 720, 450, 830)), ('Male', (280, 680, 420, 850))):
    im = np.array(Image.open(os.path.join(A, sexo, 'Base.png')).convert('RGBA'))
    x0, y0, x1, y1 = zona
    m = es_cafe(im)[y0:y1, x0:x1]
    lab, n = ndimage.label(m)
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) >= 3:
            comps.append((len(xs), int(xs.mean()) + x0, int(ys.mean()) + y0))
    comps.sort(reverse=True)
    print(f'  {sexo}: {len(comps)} componentes café >=3px en zona boca')
    for t, cx, cy in comps[:12]:
        print(f'    {t}px @({cx},{cy})')

print()
print('== 2) Re-render 6 combos del vídeo (post-19b) y diff vs pre-19b ==')
COMBOS = [  # recetas COMPLETAS del vídeo (0-based), igual que en la T19
    dict(sexo='Female', pelo=0, ropa=0, ojos=0, nariz=0, boca=0,
         color_pelo=0, piel=0, color_ropa=0, color_ojos=0, vello=0,
         suf='00_F_H1_O1_E1_N1_M1'),
    dict(sexo='Female', pelo=1, ropa=0, ojos=1, nariz=1, boca=1,
         color_pelo=9, piel=2, color_ropa=14, color_ojos=6, vello=0,
         suf='05_F_H2_O1_E2_N2_M2'),
    dict(sexo='Male', pelo=2, ropa=1, ojos=1, nariz=0, boca=2,
         color_pelo=13, piel=1, color_ropa=2, color_ojos=1, vello=1,
         suf='10_M_H3_O2_E2_N1_M3'),
    dict(sexo='Female', pelo=10, ropa=2, ojos=0, nariz=1, boca=4,
         color_pelo=14, piel=1, color_ropa=16, color_ojos=5, vello=0,
         suf='15_F_H11_O3_E1_N2_M5'),
    dict(sexo='Male', pelo=1, ropa=1, ojos=2, nariz=0, boca=2,
         color_pelo=10, piel=0, color_ropa=21, color_ojos=6, vello=3,
         suf='20_M_H2_O2_E3_N1_M3'),
    dict(sexo='Female', pelo=6, ropa=0, ojos=4, nariz=0, boca=3,
         color_pelo=19, piel=3, color_ropa=4, color_ojos=3, vello=0,
         suf='25_F_H7_O1_E5_N1_M4'),
]
# zonas objetivo de Base por sexo (rects del fix 19b)
ZONAS = {
    'Female': [(360, 763, 436, 819), (350, 720, 368, 752), (390, 814, 408, 830)],
    'Male': [(300, 740, 345, 790), (339, 775, 354, 801), (313, 739, 318, 769), (356, 810, 385, 820)],
}
for rec in COMBOS:
    suf = rec.pop('suf')
    sexo = rec['sexo']
    arr = np.clip(motor.render(rec), 0, 255).astype('uint8')
    Image.fromarray(arr).save(os.path.join(OUT, f'{suf}_post19b.png'))
    pre = np.array(Image.open(os.path.join(PRE, f'{suf}.png')).convert('RGB'))
    dif = np.abs(arr.astype(int) - pre.astype(int)).sum(axis=2) > 0
    # píxeles fuera de las zonas objetivo
    zmask = np.zeros(dif.shape, bool)
    for (x0, y0, x1, y1) in ZONAS[sexo]:
        zmask[y0:y1, x0:x1] = True
    fuera = dif & ~zmask
    print(f'  {suf}: dif total {int(dif.sum())} px, fuera de zonas objetivo: {int(fuera.sum())} px')
    if fuera.sum():
        ys, xs = np.where(fuera)
        print(f'    bbox fuera: x {xs.min()}-{xs.max()} y {ys.min()}-{ys.max()}')

print()
print('== 3) Zooms antes/después zona boca ==')
def zoom(render_path, zona, out_path, scale=4):
    im = Image.open(render_path).convert('RGB').crop(zona)
    im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    im.save(out_path)
for suf, sexo in (('00_F_H1_O1_E1_N1_M1', 'Female'), ('10_M_H3_O2_E2_N1_M3', 'Male')):
    zona = (300, 700, 500, 860) if sexo == 'Female' else (260, 660, 420, 860)
    zoom(os.path.join(PRE, f'{suf}.png'), zona, os.path.join(OUT, f'{suf}_boca_ANTES.png'))
    zoom(os.path.join(OUT, f'{suf}_post19b.png'), zona, os.path.join(OUT, f'{suf}_boca_DESPUES.png'))
    # Base sola post-19b
    b = Image.open(os.path.join(A, sexo, 'Base.png')).convert('RGBA')
    z = b.crop(zona).resize(((zona[2] - zona[0]) * 4, (zona[3] - zona[1]) * 4), Image.LANCZOS)
    z.save(os.path.join(OUT, f'BASE_boca_{sexo}_DESPUES.png'))
print('  zooms en', OUT)
print('Verificación lista.')
