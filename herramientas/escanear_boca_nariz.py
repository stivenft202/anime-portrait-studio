# escanear_boca_nariz.py — Busca lunares (motas oscuras aisladas) horneados en las
# capas de boca y nariz de ambos sexos, y renderiza cada una sobre la Base
# para revisión visual. Una mota horneada en una capa aparece en TODOS los
# combos que usan esa boca/nariz, así que el arreglo es por capa, no por combo.
# Salida: diagnostico_usuario/lunares_boca_nariz/
import os
import numpy as np
from PIL import Image
from scipy import ndimage

BASE = '/home/hatch/workspace/anime-portrait-studio'
A = os.path.join(BASE, 'version-linux/assets')
OUT = os.path.join(BASE, 'diagnostico_usuario/lunares_boca_nariz')
os.makedirs(OUT, exist_ok=True)

CAPAS = []
for sexo in ('Female', 'Male'):
    for f in sorted(os.listdir(os.path.join(A, sexo))):
        if f.startswith(('Mouth_', 'Nose')):
            CAPAS.append((sexo, f))

def gris(a):
    return a[..., :3].astype(int).min(axis=2)  # canal más oscuro

print(f"{'capa':38s} {'px_opacos':>9s} {'comps_oscuros':>13s}  componentes (tam, centroide, bbox)")
resultados = {}
for sexo, f in CAPAS:
    p = os.path.join(A, sexo, f)
    im = np.array(Image.open(p).convert('RGBA'))
    alpha = im[..., 3]
    opacos = (alpha > 150).sum()
    oscuro = (alpha > 150) & (gris(im) < 100)
    lab, n = ndimage.label(oscuro)
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        comps.append((len(xs), int(xs.mean()), int(ys.mean()),
                      (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))))
    comps.sort(reverse=True)
    resultados[(sexo, f)] = comps
    desc = ' | '.join(f"{t}px@({cx},{cy})[{x0},{y0}-{x1},{y1}]" for t, cx, cy, (x0, y0, x1, y1) in comps[:8])
    print(f"{sexo+'/'+f:38s} {opacos:9d} {n:13d}  {desc}")

# Render compuesto Base + nariz + boca (piel Light, sin pelo/ojos/ropa) y zoom de la cara
for sexo in ('Female', 'Male'):
    base = Image.open(os.path.join(A, sexo, 'Base.png')).convert('RGBA')
    narices = ['Nose1.png', 'Nose2.png', 'Nose3.png']
    bocas = (['Mouth_Neutral.png', 'Mouth_Happy.png', 'Mouth_Sad.png', 'Mouth_Angry.png', 'Mouth_Surprised.png']
             if sexo == 'Female' else ['Mouth_Neutral.png', 'Mouth_Happy.png', 'Mouth_Surprised.png'])
    for n in narices:
        for b in bocas:
            comp = base.copy()
            comp.alpha_composite(Image.open(os.path.join(A, sexo, n)).convert('RGBA'))
            comp.alpha_composite(Image.open(os.path.join(A, sexo, b)).convert('RGBA'))
            # zoom cara: nariz+boca (x250-700, y550-950) x2
            z = comp.crop((250, 550, 700, 950)).resize((900, 800), Image.LANCZOS)
            z.save(os.path.join(OUT, f"{sexo}_{n[:-4]}_{b[:-4]}.png"))
    # capa sola recortada a su bbox + margen, x3, para ver motas sueltas
    for f in narices + bocas:
        im = Image.open(os.path.join(A, sexo, f)).convert('RGBA')
        a = np.array(im)[..., 3]
        ys, xs = np.where(a > 30)
        if len(xs) == 0:
            continue
        x0, y0, x1, y1 = max(0, xs.min() - 40), max(0, ys.min() - 40), min(1200, xs.max() + 40), min(1600, ys.max() + 40)
        fondo = Image.new('RGBA', (x1 - x0, y1 - y0), (240, 240, 240, 255))
        fondo.alpha_composite(im.crop((x0, y0, x1, y1)))
        fondo = fondo.resize((fondo.width * 3, fondo.height * 3), Image.LANCZOS)
        fondo.save(os.path.join(OUT, f"CAPA_{sexo}_{f}"))
print('renders en', OUT)
