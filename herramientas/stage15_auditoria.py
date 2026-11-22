# Auditoría total del PortraitKit (stage15) — censo de defectos por capa.
# No modifica nada: solo mide y reporta. Salida: lista de defectos por archivo.
import numpy as np, os, sys
from PIL import Image
from scipy import ndimage

PK = os.path.expanduser('~/workspace/retratos-anime/paquete/PortraitKit/Textures')

def cargar(sexo, nombre):
    return np.asarray(Image.open(f'{PK}/{sexo}/{nombre}.png').convert('RGBA'))

def componentes(mask, minpx=15):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        s = int(m.sum())
        if s < minpx: continue
        ys, xs = np.where(m)
        out.append((s, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())))
    return sorted(out, reverse=True)

def en_caja(comp, caja):
    s, x0, x1, y0, y1 = comp
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return caja[0] <= cx <= caja[1] and caja[2] <= cy <= caja[3]

ZONAS = {
 'Female': dict(ceja=(350, 620, 400, 520), ojo_c=(395, 600, 490, 665), ojo_l=(290, 400, 480, 720),
                nariz=(240, 420, 580, 780), boca=(300, 490, 720, 850),
                fantasma=[(380, 580, 430, 520), (395, 600, 490, 665), (330, 480, 740, 830)]),
 'Male':   dict(ceja=(350, 620, 400, 485), ojo_c=(380, 580, 470, 645), ojo_l=(255, 365, 450, 645),
                nariz=(200, 400, 580, 780), boca=(290, 480, 720, 830),
                fantasma=[(380, 580, 420, 485), (380, 580, 470, 645), (300, 470, 730, 815)]),
}

def auditar(sexo):
    Z = ZONAS[sexo]
    base = cargar(sexo, 'Base')
    dentro = base[..., 3] > 0
    print(f'===== {sexo} =====')
    # --- BASE: fantasmas de rasgos (desviación local alta dentro de las cajas de rasgos)
    rgb = base[..., :3].astype(float)
    desenf = ndimage.gaussian_filter(rgb, sigma=(8, 8, 0))
    dev = np.abs(rgb - desenf).max(axis=2)
    for i, (x0, x1, y0, y1) in enumerate(Z['fantasma']):
        zona = np.zeros_like(dentro); zona[y0:y1, x0:x1] = True
        n = int(((dev > 12) & dentro & zona).sum())
        print(f'  Base fantasma caja{i+1}: {n}px con desviación>12')
    # --- OJOS
    for nombre in ['Eyes_Neutral', 'Eyes_Happy', 'Eyes_Sad', 'Eyes_Angry', 'Eyes_Surprised']:
        a = cargar(sexo, nombre)
        al = a[..., 3]
        fuera = int(((al > 40) & ~dentro).sum())
        comps = componentes(al > 40)
        sueltos = [c for c in comps if not (en_caja(c, Z['ceja']) or en_caja(c, Z['ojo_c']) or en_caja(c, Z['ojo_l']))]
        cejas = [c for c in comps if en_caja(c, Z['ceja']) and c[0] > 200]
        # verde fuera de los dos cúmulos principales de iris
        verde = (a[..., 1] > a[..., 0] + 12) & (a[..., 1] > a[..., 2]) & (al > 60)
        vcomps = componentes(verde, 30)
        verde_fuera = sum(c[0] for c in vcomps[2:]) if len(vcomps) > 2 else 0
        print(f'  {nombre}: fuera_silueta={fuera} cejas={len(cejas)} sueltos={sueltos} verde_fuera_iris={verde_fuera}')
    # --- BOCAS
    for nombre in ['Mouth_Neutral', 'Mouth_Happy', 'Mouth_Sad', 'Mouth_Angry', 'Mouth_Surprised']:
        p = f'{PK}/{sexo}/{nombre}.png'
        if not os.path.exists(p): continue
        a = cargar(sexo, nombre)
        al = a[..., 3]
        lum = a[..., :3].mean(axis=2)
        sat = a[..., :3].max(axis=2) - a[..., :3].min(axis=2)
        fuera = int(((al > 40) & ~dentro).sum())
        halo = int(((al > 100) & (lum > 200) & (sat < 45)).sum())
        comps = componentes(al > 40)
        sueltos = [c for c in comps if not en_caja(c, Z['boca'])]
        print(f'  {nombre}: fuera_silueta={fuera} halo_piel={halo} sueltos={sueltos}')
    # --- NARICES
    for nombre in ['Nose1', 'Nose2', 'Nose3']:
        a = cargar(sexo, nombre)
        al = a[..., 3]
        fuera = int(((al > 40) & ~dentro).sum())
        comps = componentes(al > 40)
        sueltos = [c for c in comps if not en_caja(c, Z['nariz'])]
        print(f'  {nombre}: fuera_silueta={fuera} sueltos={sueltos}')
    # --- PELOS: contenido oscuro dentro de la zona interior de la cara (posible ceja horneada)
    for n in [1, 2, 3, 4]:
        for parte in ['Back', 'Front']:
            a = cargar(sexo, f'Hair{n}_{parte}')
            lum = a[..., :3].mean(axis=2)
            oscuro = (a[..., 3] > 100) & (lum < 120)
            zona = np.zeros_like(dentro)
            if sexo == 'Female': zona[430:900, 300:620] = True
            else: zona[430:900, 280:600] = True
            comps = componentes(oscuro & zona, 60)
            if comps: print(f'  Hair{n}_{parte}: masas oscuras en zona cara: {comps[:4]}')
    # --- ROPAS: contenido por encima de y=740 (zona de la cara/cuello alto)
    for n in [1, 2, 3]:
        a = cargar(sexo, f'Outfit{n}')
        arriba = int((a[:740, :, 3] > 40).sum())
        if arriba: print(f'  Outfit{n}: {arriba}px por encima de y=740')

for sexo in ['Female', 'Male']:
    auditar(sexo)
print('AUDITORÍA TERMINADA')
