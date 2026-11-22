# stage20 — quitar los trazos azulados del pelo femenino.
#
# Hallazgo (2026-11-22, capturas de Stiven #31 y otras): las capas de pelo
# de mujer tienen brillos dibujados en azul pálido (B-R > 30, p. ej. H11_Front
# 8.422 px, H6_Front 6.170, H5_Front 6.051, H12_Front 4.158, H9_Front 3.414,
# H1_Back 5.311, H3_Back 3.893). Como el tinte de pelo es multiplicativo,
# esos píxeles NO toman el color elegido: con tintes fríos (Silver, Platinum)
# se ven AZULES y con tintes cálidos (Honey) se ven DORADOS. Son los "trazos
# azules en la parte de atrás del cabello" que reportó Stiven. Las capas de
# hombre están limpias (0-34 px).
#
# Arreglo: teñir esos píxeles con el color base oscuro de la propia capa (la
# mediana de sus píxeles opacos), para que se fundan con el pelo y el trazo
# desaparezca. NO basta con desaturarlos a gris: un gris claro con tinte
# Honey sigue viéndose dorado (se probó: el antes/después con Honey salía
# idéntico, la franja dorada seguía ahí). Fundirlos con la base es lo que
# quita el trazo con cualquier tinte.
# No se borra ningún píxel ni se toca nada fuera de los píxeles azulados:
# se verifica con assert que el diff fuera de la máscara es 0.
#
# Precedente: igual que el fix de fragmentos de stage20 (operación por píxel
# con guion, snapshot antes/después, verificación visual y barrido).
# Snapshot previo: versiones/2026-11-22_stage20-antes-azules/
import os
import numpy as np
from PIL import Image

BASE = os.path.join(os.path.dirname(__file__), '..', 'version-linux', 'assets')

def arreglar(sexo, nombre):
    ruta = os.path.join(BASE, sexo, nombre + '.png')
    a = np.asarray(Image.open(ruta).convert('RGBA')).astype(float)
    orig = a.copy()
    al = a[..., 3]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mascara = (al > 80) & (b - r > 30)
    n = int(mascara.sum())
    if n == 0:
        return 0
    # Color base oscuro de la capa: mediana de sus píxeles opacos. Los
    # brillos azulados se funden con el pelo y el trazo desaparece.
    opacos = a[..., :3][al > 80]
    base = np.median(opacos, axis=0)
    a[..., 0][mascara] = base[0]
    a[..., 1][mascara] = base[1]
    a[..., 2][mascara] = base[2]
    # Verificación: fuera de la máscara no cambia nada.
    fuera = ~mascara
    assert np.array_equal(a[..., :3][fuera], orig[..., :3][fuera]), nombre
    assert np.array_equal(a[..., 3], orig[..., 3]), nombre
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(ruta)
    return n

if __name__ == '__main__':
    total = 0
    for sexo in ('Female', 'Male'):
        for f in sorted(os.listdir(os.path.join(BASE, sexo))):
            if f.startswith('Hair') and f.endswith('.png'):
                n = arreglar(sexo, f[:-4])
                if n:
                    print(f'{sexo}/{f}: {n} px neutralizados')
                    total += n
    print('TOTAL:', total, 'px')
