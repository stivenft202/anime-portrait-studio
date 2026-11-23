# rayita_fix_H1.py — Borrar la rayita suelta de Female Hair1_Front.
# La rayita (19 px, x380-392, y787-789) es un trazo fino horizontal
# desprendido de la masa del pelo, que flota sobre la piel justo a la
# izquierda de la boca: en los renders se lee como una rayita pegada a la
# boca. Stiven la vio en el primer combo del vídeo Sorprendido
# (F H1 O1 E1 N1 M5) y ordenó arreglarla y revisar si sale en más combos.
# Escaneo previo: SOLO Female Hair1_Front la tiene (ninguna otra frente de
# pelo de mujer ni de hombre tiene una rayita así en la zona de la boca).
# Aparece en TODOS los combos de mujer con H1 (Long Straight), con
# cualquier boca/nariz/ropa: 225 combos de piezas.
# Método stage20: snapshot previo en
# versiones/2026-11-23_rayita-H1-antes/; borrar solo el componente
# detectado (alfa=0); assert 0 px cambiados fuera del objetivo.
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

BASE = '/home/hatch/workspace/anime-portrait-studio'
RUTA = f'{BASE}/version-linux/assets/Female/Hair1_Front.png'
# zona de la boca (mujer, centro 406.5, 783.5)
X0, X1, Y0, Y1 = 326, 476, 738, 823

a = np.array(Image.open(RUTA).convert('RGBA')).astype(int)
orig = a.copy()
z = a[Y0:Y1, X0:X1]
alfa = z[:, :, 3] > 150
lum = z[:, :, :3].sum(axis=2) // 3
oscuro = alfa & (lum < 120)
lab, n = ndi.label(oscuro)
objetivo = None
for c in range(1, n + 1):
    ys, xs = np.where(lab == c)
    w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    if h <= 4 and w >= 8 and len(xs) <= 60:
        objetivo = (c, len(xs), xs.min() + X0, xs.max() + X0,
                    ys.min() + Y0, ys.max() + Y0)
        print(f'rayita hallada: comp {c}, {len(xs)} px, '
              f'x {xs.min() + X0}-{xs.max() + X0}, '
              f'y {ys.min() + Y0}-{ys.max() + Y0} ({w}x{h})')
assert objetivo is not None, 'no se halló la rayita'
c = objetivo[0]
masc = np.zeros(a.shape[:2], dtype=bool)
masc[Y0:Y1, X0:X1] = (lab == c)
a[masc, 3] = 0
# assert: solo cambian los píxeles objetivo
dif = (a != orig).any(axis=2)
assert dif.sum() == objetivo[1], f'cambiaron {dif.sum()} px, esperados {objetivo[1]}'
assert (dif == masc).all(), 'hay cambios fuera de la rayita'
Image.fromarray(a.astype('uint8')).save(RUTA)
print(f'borrados {objetivo[1]} px en {RUTA}')
