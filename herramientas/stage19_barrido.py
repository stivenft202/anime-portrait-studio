# -*- coding: utf-8 -*-
# BARRIDO TOTAL stage19: auditoría de capas a resolución completa +
# render de TODOS los combos de piezas en 2 juegos de tintes (revelador
# Deep+Wine y control Light+Natural) buscando: manchas, parches cálidos
# en el pelo e iris no visibles (ojos tapados/ausentes).
import itertools, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, '/home/hatch/workspace/retratos-anime/version-linux')
import motor

SALIDA = '/home/hatch/workspace/retratos-anime/stage19_resultado.json'

# ============ 1) AUDITORÍA DE CAPAS (resolución completa) ============
def familia(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (r + g + b) / 3.0
    return lum, r - b

def auditoria_capas():
    res = {}
    for sexo in ('Female', 'Male'):
        carpeta = os.path.join(motor.ASSETS, sexo)
        for f in sorted(os.listdir(carpeta)):
            if not f.endswith('.png'):
                continue
            nombre = f[:-4]
            a = np.asarray(Image.open(os.path.join(carpeta, f)).convert('RGBA')).astype(float)
            al = a[..., 3]
            lum, rb = familia(a)
            datos = {}
            if nombre.startswith('Hair') or nombre.startswith('FacialHair'):
                piel = (al > 25) & (lum > 80) & (rb > 22)
                datos['piel_en_pelo'] = int(piel.sum())
                if nombre.endswith('_Front') or nombre.startswith('FacialHair'):
                    # pelo opaco dentro de las cajas de los iris = ojo tapado
                    cajas = (motor.IRIS_CAJAS[sexo] if hasattr(motor, 'IRIS_CAJAS') else None)
                # halo cálido semitransparente
                halo = (al > 0) & (al <= 25) & (lum > 60) & (rb > 30)
                datos['halo_calido'] = int(halo.sum())
            if nombre.startswith('Eyes'):
                fuera = al > 40
                zona = np.zeros(al.shape, bool)
                y0, y1, x0, x1 = (430, 770, 230, 720) if sexo == 'Female' else (430, 750, 190, 660)
                zona[y0:y1, x0:x1] = True
                datos['fuera_de_zona'] = int((fuera & ~zona).sum())
            if nombre.startswith('Mouth'):
                zona = np.zeros(al.shape, bool)
                y0, y1, x0, x1 = (700, 880, 280, 490) if sexo == 'Female' else (690, 870, 250, 470)
                zona[y0:y1, x0:x1] = True
                datos['fuera_de_zona'] = int(((al > 40) & ~zona).sum())
                datos['halo_piel'] = int(((al > 40) & zona & (lum > 150) & (rb > 25)).sum())
            if nombre.startswith('Nose'):
                zona = np.zeros(al.shape, bool)
                y0, y1, x0, x1 = (600, 760, 250, 390) if sexo == 'Female' else (590, 750, 195, 350)
                zona[y0:y1, x0:x1] = True
                datos['fuera_de_zona'] = int(((al > 40) & ~zona).sum())
            if nombre.startswith('Outfit'):
                datos['piel_en_ropa'] = int(((al > 25) & (lum > 80) & (rb > 22)).sum())
                datos['pelo_en_ropa'] = int(((al > 40) & (lum < 70) & (a[..., 2] >= a[..., 0] - 5)).sum())
            if any(v > 0 for v in datos.values()):
                res[f'{sexo}/{nombre}'] = datos
    return res

# Cajas de iris a resolución completa (medidas de stage15/17)
IRIS = {  # (cerca: x0,x1,y0,y1), (lejos: ...)
    'Female': ((430, 495, 540, 625), (358, 398, 540, 625)),
    'Male':   ((398, 468, 512, 610), (310, 348, 512, 610)),
}

def auditoria_iris_capas():
    """Contenido de iris real en cada capa de ojos + pelo delantero que
    invada las cajas de iris."""
    res = {}
    for sexo in ('Female', 'Male'):
        carpeta = os.path.join(motor.ASSETS, sexo)
        for expr in ('Neutral', 'Happy', 'Sad', 'Angry', 'Surprised'):
            a = motor.capa(sexo, 'Eyes_' + expr)
            h, mx, d = motor._tono(a)
            masc = (a[..., 3] > 100) & (h >= 85) & (h <= 205) & (d > 12) & (mx < 200)
            fila = {}
            for clave, (x0, x1, y0, y1) in zip(('cerca', 'lejos'), IRIS[sexo]):
                fila[clave] = int(masc[y0:y1, x0:x1].sum())
            res[f'{sexo}/Eyes_{expr}'] = fila
        # pelo delantero sobre las cajas de iris
        for i in range(len(motor.PELOS[sexo])):
            arch = motor.PELOS[sexo][i][1] + '_Front'
            a = motor.capa(sexo, arch)
            fila = {}
            for clave, (x0, x1, y0, y1) in zip(('cerca', 'lejos'), IRIS[sexo]):
                fila[clave] = int((a[y0:y1, x0:x1, 3] > 120).sum())
            res[f'{sexo}/{arch}'] = fila
    return res

# ============ 2) RENDER MASIVO A 0.25 ============
def precargar():
    motor._cache.clear()
    for sexo in ('Female', 'Male'):
        carpeta = os.path.join(motor.ASSETS, sexo)
        for f in os.listdir(carpeta):
            if f.endswith('.png'):
                img = Image.open(os.path.join(carpeta, f)).convert('RGBA')
                img = img.resize((300, 400), Image.LANCZOS)
                motor._cache[(sexo, f[:-4])] = np.asarray(img).astype(float)

def mascara_busqueda(sexo, receta):
    base = motor._cache[(sexo, 'Base')]
    pelo_f = motor._cache[(sexo, motor.PELOS[sexo][receta['pelo']][1] + '_Front')]
    z = np.zeros((400, 300), bool)
    z[150:223, 78:138] = True
    z[175:215, 65:130] = False
    z[138:198, 55:112] = False
    z[218:252, 88:150] = True    # cuello
    z &= base[..., 3] > 0
    z &= pelo_f[..., 3] < 30
    return z

def manchas(comp, sexo, receta):
    lum = comp.mean(axis=2)
    suave = ndimage.gaussian_filter(lum, sigma=6)
    sospechoso = (lum < suave - 30) & mascara_busqueda(sexo, receta)
    lab, n = ndimage.label(sospechoso)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        s = int(m.sum())
        if s >= 8:
            ys, xs = np.where(m)
            out.append((s, int(xs.min()), int(ys.min())))
    return out

def iris_visibles(comp, sexo):
    """Cuenta píxeles de ojo (oscuros o saturados) en las cajas de iris
    a escala 0.25."""
    r, g, b = comp[..., 0], comp[..., 1], comp[..., 2]
    lum = (r + g + b) / 3.0
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    ojo = (lum < 115) | ((mx - mn) > 45)
    res = {}
    for clave, (x0, x1, y0, y1) in zip(('cerca', 'lejos'), IRIS[sexo]):
        res[clave] = int(ojo[y0 // 4:y1 // 4, x0 // 4:x1 // 4].sum())
    return res

def parche_calido(comp, sexo, receta):
    """Píxeles rojizos dentro de la zona visible del pelo delantero."""
    pelo_f = motor._cache[(sexo, motor.PELOS[sexo][receta['pelo']][1] + '_Front')]
    zona = pelo_f[..., 3] > 120
    r, b = comp[..., 0], comp[..., 2]
    lum = comp.mean(axis=2)
    m = zona & ((r - b) > 45) & (lum > 60) & (lum < 215)
    return int(m.sum())

def main():
    print('auditoría de capas...', flush=True)
    aud = auditoria_capas()
    iris = auditoria_iris_capas()
    print('render masivo...', flush=True)
    precargar()
    TINTES = [
        dict(color_pelo=5, piel=3, color_ropa=0, color_ojos=0),   # Wine + Deep
        dict(color_pelo=0, piel=0, color_ropa=5, color_ojos=0),   # Natural + Light
    ]
    combos = []
    total = 0
    for sexo in ('Female', 'Male'):
        nb = len(motor.BOCAS[sexo])
        nvel = 4 if sexo == 'Male' else 1
        for pelo, ropa, ojos, nariz, boca, vello in itertools.product(
                range(len(motor.PELOS[sexo])), range(3), range(5), range(3), range(nb), range(nvel)):
            for t, tinte in enumerate(TINTES):
                receta = dict(sexo=sexo, pelo=pelo, ropa=ropa, ojos=ojos, nariz=nariz,
                              boca=boca, vello=vello, **tinte)
                comp = motor.render(receta)
                total += 1
                flags = {}
                m = manchas(comp, sexo, receta)
                if m:
                    flags['manchas'] = m
                iv = iris_visibles(comp, sexo)
                flags['iris'] = iv
                pc = parche_calido(comp, sexo, receta)
                if pc > 25:
                    flags['parche_calido'] = pc
                if m or pc > 25:
                    combos.append({'codigo': motor.codigo(receta), 'tinte': t, **flags})
    with open(SALIDA, 'w') as f:
        json.dump({'auditoria_capas': aud, 'iris_capas': iris,
                   'total_renders': total, 'combos_marcados': combos}, f)
    print(f'TOTAL renders: {total}; combos marcados: {len(combos)}')
    print('capas con avisos:', len(aud))
    for k, v in aud.items():
        print(' ', k, v)
    print('iris por capa de ojos:')
    for k, v in iris.items():
        if 'Eyes' in k:
            print(' ', k, v)

if __name__ == '__main__':
    main()
