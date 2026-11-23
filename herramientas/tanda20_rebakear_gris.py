"""Re-bakear SOLO las variantes Gray de EyesColor (Tanda 20, 2026-11-23).

motor.py _ojos_tinte ahora aplana el iris cuando el destino es casi
sin saturación (Gris): antes el iris quedaba moteado (parches verdes,
morados y claros). Solo Gray cumple esa condición (max-min=10); los
demás colores no cambian. Se re-bakean las 10 variantes Gray
(5 ojos x 2 sexos) para que Unity coincida con el motor.
Snapshot previo en versiones/2026-11-23_tanda20-antes/EyesColor_Gray/.
"""
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')
sys.path.insert(0, os.path.join(ROOT, 'version-linux'))
import motor

OJOS = ['Neutral', 'Happy', 'Sad', 'Angry', 'Surprised']
IDX_GRIS = 5  # COLORES_OJOS: Gray (128,132,138)

os.makedirs(os.path.join(ROOT, 'versiones/2026-11-23_tanda20-antes/EyesColor_Gray'), exist_ok=True)

for sexo in ['Female', 'Male']:
    for ojo in OJOS:
        src = os.path.join(ROOT, 'version-linux/assets', sexo, f'Eyes_{ojo}.png')
        dst = os.path.join(ROOT, 'unity/EyesColor', sexo, f'EyesColor_{ojo}_Gray.png')
        # snapshot
        snap = os.path.join(ROOT, 'versiones/2026-11-23_tanda20-antes/EyesColor_Gray', f'{sexo}_EyesColor_{ojo}_Gray.png')
        Image.open(dst).save(snap)
        a = np.array(Image.open(src).convert('RGBA'))
        motor._iris_cache.clear()
        t = motor._ojos_tinte(a, f'Eyes_{ojo}', IDX_GRIS, sexo)
        Image.fromarray(t.astype(np.uint8)).save(dst)
        # verificación: el iris teñido debe ser casi gris (sat baja) y uniforme
        m = motor._iris_cache[(sexo, f'Eyes_{ojo}')]
        masc, prom, disco, prom_disco, rim = m
        iris = masc | rim
        if disco is not None:
            iris = iris | disco
        px = t[..., :3][iris].astype(int)
        sat = (px.max(axis=1) - px.min(axis=1))
        lum = px.mean(axis=1)
        print(f'{sexo} {ojo} Gray: sat_media={sat.mean():.1f} lum_std={lum.std():.1f} px={len(px)}')
print('OK')
