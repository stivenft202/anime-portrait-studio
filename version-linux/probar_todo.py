# Prueba completa de la versión independiente: renderiza TODOS los combos
# posibles de ambos personajes con el motor y busca defectos visibles
# (manchas oscuras fuera de las zonas de rasgos = «lunares»).
# Uso: python3 probar_todo.py
import itertools, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motor

ESCALA = 0.25  # se prueba a 300x400 (la composición es idéntica, solo cambia el tamaño)

# Precargar las capas a escala reducida en la caché del motor
def precargar():
    for sexo in ['Female', 'Male']:
        carpeta = os.path.join(motor.ASSETS, sexo)
        for f in os.listdir(carpeta):
            if f.endswith('.png'):
                img = Image.open(os.path.join(carpeta, f)).convert('RGBA')
                img = img.resize((300, 400), Image.LANCZOS)
                motor._cache[(sexo, f[:-4])] = np.asarray(img).astype(float)

# Zona de búsqueda del «lunar»: piel abierta de la mejilla y la mandíbula
# (a escala 300x400), fuera de nariz, boca y pelo delantero.
def mascara_busqueda(sexo, receta):
    base = motor._cache[(sexo, 'Base')]
    pelo_f = motor._cache[(sexo, motor.PELOS[sexo][receta['pelo']][1] + '_Front')]
    z = np.zeros((400, 300), bool)
    z[150:223, 78:138] = True
    z[175:215, 65:130] = False   # boca
    z[138:198, 55:112] = False   # nariz
    z &= base[..., 3] > 0        # dentro de la silueta
    z &= pelo_f[..., 3] < 30     # no bajo el flequillo
    return z

def manchas(comp, sexo, receta):
    lum = comp.mean(axis=2)
    suave = ndimage.gaussian_filter(lum, sigma=6)
    # Un lunar es oscuro EN CONTRASTE con la piel que lo rodea (en piel Deep
    # hasta la piel sana baja de 105 de luminancia: el umbral absoluto no sirve).
    sospechoso = (lum < suave - 30) & mascara_busqueda(sexo, receta)
    lab, n = ndimage.label(sospechoso)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        s = int(m.sum())
        if s >= 8:
            ys, xs = np.where(m)
            out.append((s, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())))
    return out

def main():
    precargar()
    total = 0
    con_manchas = []
    for sexo in ['Female', 'Male']:
        nb = len(motor.BOCAS[sexo])
        nvel = 4 if sexo == 'Male' else 1
        for pelo, ropa, ojos, nariz, boca, vello in itertools.product(range(len(motor.PELOS[sexo])), range(3), range(5), range(3), range(nb), range(nvel)):
            receta = dict(sexo=sexo, pelo=pelo, ropa=ropa, ojos=ojos, nariz=nariz, boca=boca, vello=vello,
                          color_pelo=(pelo + ojos) % 6, piel=(ropa + nariz) % 4, color_ropa=(ojos + boca) % 6)
            comp = motor.render(receta)
            total += 1
            m = manchas(comp, sexo, receta)
            if m:
                con_manchas.append((motor.codigo(receta), m))
    print(f'Combos renderizados: {total}')
    print(f'Combos con manchas sospechosas: {len(con_manchas)}')
    from collections import Counter
    lugares = Counter()
    for cod, m in con_manchas:
        for c in m:
            lugares[(cod[0], c[1] // 10 * 10, c[3] // 10 * 10)] += 1
    for (sx, x, y), n in lugares.most_common(12):
        print(f'  {sx} zona x~{x} y~{y} (escala 300x400): {n} combos')
    for cod, m in con_manchas[:8]:
        print(' ', cod, m)
    return con_manchas

if __name__ == '__main__':
    main()
