# causa_raiz_puntos_cafe.py — Investigación de causa raíz: puntos/lunares
# CAFÉ en la boca. Renderiza TODAS las bocas × narices (24 combos, Base +
# nariz + boca, piel Light) y caza cada punto café en la zona de la boca.
# Para cada punto, rastrea QUÉ CAPA lo aporta (Base / Nariz / Boca)
# muestreando las capas en esos píxeles exactos.
# Definición "café": más oscuro que la piel y marrón (R>G>B, R-B>25).
import sys, os
sys.path.insert(0, '/home/hatch/workspace/anime-portrait-studio/version-linux')
import numpy as np
from PIL import Image
from scipy import ndimage
import motor

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
OUT = os.path.join(BASE, 'diagnostico_usuario/lunares_boca_nariz/causa_raiz')
os.makedirs(OUT, exist_ok=True)

ZONA = (250, 680, 550, 900)  # x0,y0,x1,y1 zona boca

def es_cafe(arr):
    """Máscara de píxeles café/oscuros: luminancia < 180 y R-B>25 y R>=G>=B."""
    r, g, b = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)
    lum = (r + g + b) // 3
    return (lum < 180) & ((r - b) > 25) & (r >= g) & (g >= b)

def clusters(mask, min_px=3):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) >= min_px:
            out.append((len(xs), int(xs.mean()), int(ys.mean()),
                        (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))))
    out.sort(reverse=True)
    return out

def capa_en(sexo, archivo, xs, ys):
    """¿Qué aporta esta capa en los píxeles (xs,ys)? Devuelve (n_opacos,
    color medio RGB, alfa media)."""
    im = np.array(Image.open(os.path.join(A, sexo, archivo)).convert('RGBA'))
    sel = im[ys, xs]
    op = sel[:, 3] > 150
    if op.sum() == 0:
        return 0, None, 0.0
    return int(op.sum()), sel[op][:, :3].mean(axis=0).astype(int), float(sel[op][:, 3].mean())

BOCAS_F = ['Mouth_Neutral.png', 'Mouth_Happy.png', 'Mouth_Sad.png', 'Mouth_Angry.png', 'Mouth_Surprised.png']
BOCAS_M = ['Mouth_Neutral.png', 'Mouth_Happy.png', 'Mouth_Surprised.png']
NARICES = ['Nose1.png', 'Nose2.png', 'Nose3.png']

print('combo | clusters café en zona boca (sin contar la boca misma) | origen por capa')
hallazgos = []
for sexo, bocas in (('Female', BOCAS_F), ('Male', BOCAS_M)):
    for ni, nariz in enumerate(NARICES):
        for bi, boca in enumerate(bocas):
            rec = dict(sexo=sexo, pelo=0, ropa=0, ojos=0, nariz=ni, boca=bi,
                       color_pelo=0, piel=0, color_ropa=0, color_ojos=0, vello=0)
            arr = np.clip(motor.render(rec), 0, 255).astype('uint8')
            x0, y0, x1, y1 = ZONA
            sub = arr[y0:y1, x0:x1]
            m = es_cafe(sub)
            cls = clusters(m)
            # la boca es el cluster mayor (o los 2 mayores si la boca se parte);
            # los demás clusters son los puntos sospechosos
            sospechosos = cls[1:] if cls else []
            # si el mayor es muy pequeño (<40px) no es una boca normal: revisar
            codigo = motor.codigo(rec)
            for (t, cx, cy, (bx0, by0, bx1, by1)) in sospechosos:
                gx, gy = cx + x0, cy + y0
                # píxeles del cluster en coordenadas globales
                lab, _ = ndimage.label(m)
                ys, xs = np.where(lab == lab[cy, cx])
                xs_g, ys_g = xs + x0, ys + y0
                origen = {}
                for capa in ('Base.png', nariz, boca):
                    n, col, al = capa_en(sexo, capa, xs_g, ys_g)
                    if n > 0:
                        origen[capa] = (n, tuple(col) if col is not None else None)
                hallazgos.append((codigo, t, (gx, gy), (bx0 + x0, by0 + y0, bx1 + x0, by1 + y0), origen))
                print(f'{codigo}: {t}px @({gx},{gy}) [{bx0+x0},{by0+y0}-{bx1+x0},{by1+y0}] origen={origen}')
            if not sospechosos:
                print(f'{codigo}: sin puntos (solo la boca: {cls[0][0] if cls else 0}px)')
print()
print(f'TOTAL puntos café sospechosos: {len(hallazgos)}')
import json
with open(os.path.join(OUT, 'hallazgos.json'), 'w') as f:
    json.dump([{'combo': c, 'px': t, 'centro': p, 'bbox': b,
                'origen': {k: [v[0], list(v[1])] for k, v in o.items()}}
               for c, t, p, b, o in hallazgos], f, indent=1)
print('guardado en', OUT)
