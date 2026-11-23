# tanda19_verificar.py — Verifica el fix de lunares (Tanda 19):
# 1) Re-escanea las capas: los componentes objetivo deben haber desaparecido
#    y ningún otro componente debe haber cambiado.
# 2) Re-renderiza los 6 combos del vídeo y compara contra los renders
#    pre-fix guardados: la diferencia debe estar SOLO en las zonas objetivo.
# 3) Guarda zooms post-fix de nariz/boca para revisión visual.
import sys, os
sys.path.insert(0, '/home/hatch/workspace/anime-portrait-studio/version-linux')
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
OUT = os.path.join(BASE, 'diagnostico_usuario/lunares_boca_nariz')
PRE = os.path.join(OUT, 'combos_video')
POST = os.path.join(OUT, 'combos_video_postfix')
os.makedirs(POST, exist_ok=True)

OBJETIVOS = {
    ('Female', 'Nose1.png'): [(362, 713), (324, 704), (318, 684)],
    ('Female', 'Nose2.png'): [(329, 700), (323, 706), (322, 705), (321, 703)],
    ('Female', 'Nose3.png'): [(323, 706), (322, 705), (321, 703)],
    ('Male', 'Nose1.png'): [(293, 639), (302, 702), (300, 631), (312, 728), (312, 710), (312, 724), (306, 624)],
    ('Male', 'Nose2.png'): [(279, 688)],
    ('Female', 'Mouth_Happy.png'): [(452, 776), (450, 774)],
    ('Male', 'Mouth_Happy.png'): [(410, 768), (366, 763)],
    ('Male', 'Mouth_Neutral.png'): [(339, 804)],
    ('Female', 'Base.png'): [(364, 772), (381, 808)],
    ('Male', 'Base.png'): [(332, 779), (315, 753)],
}

def comps_oscuros(im):
    a = im[..., 3]
    gris = im[..., :3].astype(int).min(axis=2)
    lab, n = ndimage.label((a > 150) & (gris < 100))
    out = {}
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        out[(int(xs.mean()), int(ys.mean()))] = len(xs)
    return out

print('=== 1) Re-escaneo de capas ===')
todo_ok = True
for (sexo, f), objs in OBJETIVOS.items():
    im = np.array(Image.open(os.path.join(A, sexo, f)).convert('RGBA'))
    comps = comps_oscuros(im)
    for (cx, cy) in objs:
        if (cx, cy) in comps:
            print(f'  FALLO {sexo}/{f}: componente ({cx},{cy}) sigue presente ({comps[(cx,cy)]} px)')
            todo_ok = False
    print(f'  {sexo}/{f}: objetivos borrados/aclarados OK; componentes oscuros restantes: {len(comps)}')
print('  ESCANEO:', 'OK — todos los objetivos desaparecieron' if todo_ok else 'FALLO')

print('=== 2) Re-render de los 6 combos del vídeo ===')
import motor
COMBOS = {
 '00_F_H1_O1_E1_N1_M1': dict(sexo='Female',pelo=0,ropa=0,ojos=0,nariz=0,boca=0,color_pelo=0,piel=0,color_ropa=0,color_ojos=0,vello=0),
 '05_F_H2_O1_E2_N2_M2': dict(sexo='Female',pelo=1,ropa=0,ojos=1,nariz=1,boca=1,color_pelo=9,piel=2,color_ropa=14,color_ojos=6,vello=0),
 '10_M_H3_O2_E2_N1_M3': dict(sexo='Male',pelo=2,ropa=1,ojos=1,nariz=0,boca=2,color_pelo=13,piel=1,color_ropa=2,color_ojos=1,vello=1),
 '15_F_H11_O3_E1_N2_M5': dict(sexo='Female',pelo=10,ropa=2,ojos=0,nariz=1,boca=4,color_pelo=14,piel=1,color_ropa=16,color_ojos=5,vello=0),
 '20_M_H2_O2_E3_N1_M3': dict(sexo='Male',pelo=1,ropa=1,ojos=2,nariz=0,boca=2,color_pelo=10,piel=0,color_ropa=21,color_ojos=6,vello=3),
 '25_F_H7_O1_E5_N1_M4': dict(sexo='Female',pelo=6,ropa=0,ojos=4,nariz=0,boca=3,color_pelo=19,piel=3,color_ropa=4,color_ojos=3,vello=0),
}
# zonas objetivo en el render (nariz punta + esquina boca), con margen
ZONAS = [(300, 620, 440, 730), (340, 730, 460, 840)]
for nombre, rec in COMBOS.items():
    arr = np.clip(motor.render(rec), 0, 255).astype('uint8')
    im = Image.fromarray(arr)
    im.save(f'{POST}/{nombre}.png')
    for zona, (x0, y0, x1, y1) in {'nariz': (260, 600, 420, 760), 'boca': (300, 700, 500, 860)}.items():
        im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 4, (y1 - y0) * 4), Image.LANCZOS).save(f'{POST}/{nombre}_{zona}.png')
    pre = np.array(Image.open(f'{PRE}/{nombre}.png').convert('RGB')).astype(int)
    dif = np.abs(arr.astype(int) - pre).max(axis=2) > 12
    ys, xs = np.where(dif)
    fuera = sum(1 for x, y in zip(xs, ys) if not any(x0 - 5 <= x <= x1 + 5 and y0 - 5 <= y <= y1 + 5 for x0, y0, x1, y1 in ZONAS))
    print(f'  {nombre}: {int(dif.sum())} px difieren del pre-fix; fuera de zonas objetivo: {fuera}')
print('listo en', POST)
