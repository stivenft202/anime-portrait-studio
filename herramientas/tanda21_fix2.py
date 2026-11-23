"""Tanda 21 — fix parte 2 (quiebros del mechón principal H8/H9).
El mechón principal de Hair8_Front y Hair9_Front (plantilla compartida)
tiene un quiebro en ángulo recto: baja en diagonal (x775,y1240 -> x755,y1280),
hace una banda HORIZONTAL (x644-755, y1290-1305) y sigue bajando hacia la
derecha (x660,y1310 -> x696,y1360). Es un gancho antinatural.

Fix: borrar la banda horizontal (y1288-1308, x640-760) y redibujar una
diagonal suave de (755,1280) a (660,1310) con el color del mechón
(mediana [45,42,45]), ancho ~7 px, bordes suavizados por distancia.
Snapshot previo en versiones/2026-11-23_tanda21-antes/.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.expanduser('~/workspace/anime-portrait-studio')
AS = os.path.join(ROOT, 'version-linux/assets/Female')

def load(name):
    return np.array(Image.open(os.path.join(AS, name)).convert('RGBA')).astype(np.int32)

def save(a, name):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(AS, name))

# Segmento de la diagonal suave: de (755,1280) a (660,1310)
P0 = np.array([755.0, 1280.0])
P1 = np.array([660.0, 1310.0])
COLOR = np.array([45, 42, 45], dtype=np.int32)

for nombre in ['Hair8_Front.png', 'Hair9_Front.png']:
    a = load(nombre)
    # 1. Borrar la banda horizontal (y1288-1308, x640-760).
    m = np.zeros((1600, 1200), dtype=bool)
    m[1288:1309, 640:761] = True
    m &= a[..., 3] > 0
    n_borrado = int(m.sum())
    a[..., 3] = np.where(m, 0, a[..., 3])
    # 2. Redibujar la diagonal suave.
    #    Distancia de cada píxel de la zona al segmento P0-P1.
    ys, xs = np.mgrid[1275:1316, 640:765]
    pts = np.stack([xs, ys], axis=-1).astype(float)
    v = P1 - P0
    L2 = (v * v).sum()
    t = np.clip(((pts - P0) * v).sum(axis=-1) / L2, 0, 1)
    proj = P0 + t[..., None] * v
    dist = np.linalg.norm(pts - proj, axis=-1)
    # ancho 7 px (radio 3.5), borde suave 1 px
    alfa = np.clip(4.5 - dist, 0, 1)  # 1.0 si dist<=3.5, cae a 0 en 4.5
    # solo donde la diagonal pasa (dist < 4.5)
    zona = np.zeros((1600, 1200), dtype=bool)
    zona[1275:1316, 640:765] = True
    al = np.zeros((1600, 1200), dtype=float)
    al[1275:1316, 640:765] = alfa
    # componer: donde alfa>0, mezclar color del mechón sobre lo existente
    for c in range(3):
        a[..., c] = np.where(al > 0,
                             (COLOR[c] * al + a[..., c] * (1 - al)).astype(np.int32),
                             a[..., c])
    a[..., 3] = np.where(al > 0,
                         np.maximum(a[..., 3], (al * 255).astype(np.int32)),
                         a[..., 3])
    n_dib = int((alfa > 0).sum())
    save(a, nombre)
    print(f'{nombre}: banda borrada {n_borrado} px, diagonal dibujada {n_dib} px')

print('OK parte 2 (quiebros)')
