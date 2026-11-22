# Motor de composición de Anime Half Portrait Studio (versión independiente).
# Replica exactamente las reglas del PortraitView de Unity:
# orden de capas 10/20/30/35/40/45/50, tintes multiplicativos,
# la nariz sigue el tinte de piel; ojos y boca nunca se tiñen.
import os
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, 'assets')

PELOS = {
    'Female': [('Long Straight', 'Hair1'), ('Pixie Cut', 'Hair2'), ('Bob Cut', 'Hair3'), ('Long Wavy', 'Hair4'), ('Twin Tails', 'Hair5'), ('High Ponytail', 'Hair6'), ('Long Braid', 'Hair7'), ('Double Buns', 'Hair8'), ('Hime Cut', 'Hair9'), ('Messy Bun', 'Hair10'), ('Side Ponytail', 'Hair11'), ('Long Curly', 'Hair12')],
    'Male': [('Style 1', 'Hair1'), ('Style 2', 'Hair2'), ('Style 3', 'Hair3'), ('Style 4', 'Hair4')],
}
ROPAS = {
    'Female': [('Sweater and Jacket', 'Outfit1'), ('Green Jacket', 'Outfit2'), ('Blue Hoodie', 'Outfit3')],
    'Male': [('Outfit 1', 'Outfit1'), ('Outfit 2', 'Outfit2'), ('Outfit 3', 'Outfit3')],
}
OJOS = [('Neutral', 'Eyes_Neutral'), ('Happy', 'Eyes_Happy'), ('Sad', 'Eyes_Sad'),
        ('Angry', 'Eyes_Angry'), ('Surprised', 'Eyes_Surprised')]
NARICES = [('Nose 1', 'Nose1'), ('Nose 2', 'Nose2'), ('Nose 3', 'Nose3')]
BOCAS = {
    'Female': [('Neutral', 'Mouth_Neutral'), ('Happy', 'Mouth_Happy'), ('Sad', 'Mouth_Sad'),
               ('Angry', 'Mouth_Angry'), ('Surprised', 'Mouth_Surprised')],
    'Male': [('Neutral', 'Mouth_Neutral'), ('Happy', 'Mouth_Happy'), ('Surprised', 'Mouth_Surprised')],
}
VELLO = [('None', None), ('Mustache', 'FacialHair1'), ('Stubble', 'FacialHair2'), ('Full Beard', 'FacialHair3')]
COLORES_PELO = [('Natural Black', (0.16, 0.15, 0.18)), ('Dark Brown', (0.36, 0.24, 0.17)),
                ('Chestnut', (0.55, 0.32, 0.18)), ('Ash Blonde', (0.85, 0.75, 0.55)),
                ('Silver', (0.82, 0.84, 0.88)), ('Wine Red', (0.55, 0.16, 0.20)),
                ('Jet Black', (0.08, 0.08, 0.10)), ('Chocolate', (0.42, 0.26, 0.16)),
                ('Auburn', (0.60, 0.28, 0.16)), ('Copper', (0.78, 0.42, 0.20)),
                ('Burgundy', (0.42, 0.12, 0.18)), ('Crimson', (0.72, 0.18, 0.18)),
                ('Rose Pink', (0.85, 0.45, 0.50)), ('Golden Blonde', (0.92, 0.78, 0.42)),
                ('Honey', (0.80, 0.60, 0.32)), ('Platinum', (0.95, 0.93, 0.88)),
                ('Ash Gray', (0.55, 0.56, 0.60)), ('Navy Blue', (0.16, 0.24, 0.48)),
                ('Steel Blue', (0.35, 0.48, 0.68)), ('Teal', (0.14, 0.42, 0.42)),
                ('Forest Green', (0.20, 0.38, 0.22)), ('Mint', (0.55, 0.80, 0.62)),
                ('Plum', (0.42, 0.22, 0.48)), ('Lavender', (0.62, 0.52, 0.78))]
TONOS_PIEL = [('Light', (1, 1, 1)), ('Warm', (0.96, 0.85, 0.74)),
              ('Tan', (0.85, 0.66, 0.50)), ('Deep', (0.62, 0.45, 0.33))]
COLORES_ROPA = [('White', (1, 1, 1)), ('Sand', (0.92, 0.84, 0.70)), ('Olive', (0.62, 0.66, 0.48)),
                ('Sky', (0.62, 0.76, 0.92)), ('Rose', (0.94, 0.70, 0.72)), ('Charcoal', (0.35, 0.35, 0.38)),
                ('Black', (0.15, 0.15, 0.16)), ('Gray', (0.60, 0.60, 0.62)), ('Navy', (0.20, 0.28, 0.52)),
                ('Royal Blue', (0.30, 0.42, 0.85)), ('Denim', (0.42, 0.55, 0.72)), ('Mint', (0.62, 0.85, 0.70)),
                ('Forest', (0.30, 0.48, 0.32)), ('Lime', (0.72, 0.85, 0.45)), ('Yellow', (0.95, 0.85, 0.40)),
                ('Orange', (0.92, 0.58, 0.30)), ('Coral', (0.92, 0.55, 0.48)), ('Red', (0.78, 0.25, 0.25)),
                ('Burgundy', (0.50, 0.20, 0.26)), ('Pink', (0.95, 0.65, 0.78)), ('Lavender', (0.72, 0.65, 0.88)),
                ('Purple', (0.52, 0.38, 0.72)), ('Brown', (0.48, 0.36, 0.26)), ('Camel', (0.78, 0.62, 0.42))]
# Color de ojos: None = el verde original del arte; si no, color promedio
# destino del iris (el motor escala solo los píxeles del iris, ver _ojos_tinte).
COLORES_OJOS = [('Original Green', None), ('Brown', (110, 68, 40)), ('Blue', (58, 105, 185)),
                ('Amber', (185, 128, 48)), ('Violet', (128, 92, 185)), ('Gray', (128, 132, 138)),
                ('Red', (175, 42, 38))]

_cache = {}

def capa(sexo, archivo):
    clave = (sexo, archivo)
    if clave not in _cache:
        _cache[clave] = np.asarray(Image.open(os.path.join(ASSETS, sexo, archivo + '.png')).convert('RGBA')).astype(float)
    return _cache[clave]

def _tinte(a, t):
    o = a.copy()
    o[..., :3] *= np.array(t, float)
    return o

_iris_cache = {}

def _tono(a):
    r, g, b = a[..., 0] / 255.0, a[..., 1] / 255.0, a[..., 2] / 255.0
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    d = mx - mn
    h = np.zeros_like(mx)
    m_r = (mx == r) & (d > 0); m_g = (mx == g) & (d > 0); m_b = (mx == b) & (d > 0)
    h[m_r] = (60 * ((g - b)[m_r] / d[m_r]) + 360) % 360
    h[m_g] = 60 * ((b - r)[m_g] / d[m_g]) + 120
    h[m_b] = 60 * ((r - g)[m_b] / d[m_b]) + 240
    return h, mx * 255.0, d * 255.0

def _ojos_tinte(a, nombre, idx):
    """Recolorea SOLO el iris (verde del arte, tono 85-205) hacia el
    color destino, conservando sombreado, pupila, esclerótica y brillos."""
    destino = COLORES_OJOS[idx][1]
    if destino is None:
        return a
    if nombre not in _iris_cache:
        h, mx, d = _tono(a)
        masc = (a[..., 3] > 100) & (h >= 85) & (h <= 205) & (d > 12) & (mx < 200)
        prom = a[..., :3][masc].mean(axis=0) if masc.any() else np.array([70.0, 100.0, 90.0])
        _iris_cache[nombre] = (masc, prom)
    masc, prom = _iris_cache[nombre]
    o = a.copy()
    escala = np.array(destino, float) / np.maximum(prom, 1.0)
    o[..., :3] = np.where(masc[..., None], np.clip(o[..., :3] * escala, 0, 255), o[..., :3])
    return o

def _sobre(fondo, a):
    al = a[..., 3:4] / 255.0
    return a[..., :3] * al + fondo * (1 - al)

def render(receta, fondo=(40, 44, 52)):
    """receta: dict con sexo y los índices (pelo, ropa, ojos, nariz, boca,
    color_pelo, piel, color_ropa). Devuelve un arreglo RGB 1200x1600."""
    sexo = receta['sexo']
    pelo = PELOS[sexo][receta['pelo']][1]
    h, w = capa(sexo, 'Base').shape[:2]
    comp = np.tile(np.array(fondo, float), (h, w, 1))
    comp = _sobre(comp, _tinte(capa(sexo, pelo + '_Back'), COLORES_PELO[receta['color_pelo']][1]))
    piel = TONOS_PIEL[receta['piel']][1]
    comp = _sobre(comp, _tinte(capa(sexo, 'Base'), piel))
    comp = _sobre(comp, _tinte(capa(sexo, ROPAS[sexo][receta['ropa']][1]), COLORES_ROPA[receta['color_ropa']][1]))
    comp = _sobre(comp, _tinte(capa(sexo, NARICES[receta['nariz']][1]), piel))  # la nariz sigue la piel
    ojos_arch = OJOS[receta['ojos']][1]
    comp = _sobre(comp, _ojos_tinte(capa(sexo, ojos_arch), ojos_arch, receta.get('color_ojos', 0)))
    comp = _sobre(comp, capa(sexo, BOCAS[sexo][receta['boca']][1]))
    if sexo == 'Male' and receta.get('vello', 0) > 0:
        comp = _sobre(comp, _tinte(capa(sexo, VELLO[receta['vello']][1]), COLORES_PELO[receta['color_pelo']][1]))
    comp = _sobre(comp, _tinte(capa(sexo, pelo + '_Front'), COLORES_PELO[receta['color_pelo']][1]))
    return comp

def codigo(receta):
    s = 'F' if receta['sexo'] == 'Female' else 'M'
    base = (f"{s} H{receta['pelo']+1} O{receta['ropa']+1} E{receta['ojos']+1} "
            f"N{receta['nariz']+1} M{receta['boca']+1} | HC{receta['color_pelo']+1} "
            f"ST{receta['piel']+1} OC{receta['color_ropa']+1} EC{receta.get('color_ojos', 0)+1}")
    if receta['sexo'] == 'Male':
        base += f" FH{receta.get('vello', 0)}"
    return base

def guardar_png(receta, ruta, cara=False):
    comp = render(receta, fondo=(0, 0, 0))
    # Para exportar con transparencia real se recompone sobre alfa:
    sexo = receta['sexo']
    pelo = PELOS[sexo][receta['pelo']][1]
    piel = TONOS_PIEL[receta['piel']][1]
    capas = [
        _tinte(capa(sexo, pelo + '_Back'), COLORES_PELO[receta['color_pelo']][1]),
        _tinte(capa(sexo, 'Base'), piel),
        _tinte(capa(sexo, ROPAS[sexo][receta['ropa']][1]), COLORES_ROPA[receta['color_ropa']][1]),
        _tinte(capa(sexo, NARICES[receta['nariz']][1]), piel),
        _ojos_tinte(capa(sexo, OJOS[receta['ojos']][1]), OJOS[receta['ojos']][1], receta.get('color_ojos', 0)),
        capa(sexo, BOCAS[sexo][receta['boca']][1]),
        _tinte(capa(sexo, VELLO[receta['vello']][1]), COLORES_PELO[receta['color_pelo']][1]) if sexo == 'Male' and receta.get('vello', 0) > 0 else np.zeros((1600, 1200, 4)),
        _tinte(capa(sexo, pelo + '_Front'), COLORES_PELO[receta['color_pelo']][1]),
    ]
    h, w = capas[0].shape[:2]
    salida = np.zeros((h, w, 4))
    for a in capas:
        al = a[..., 3:4] / 255.0
        salida[..., :3] = a[..., :3] * al + salida[..., :3] * (1 - al)
        salida[..., 3:4] = a[..., 3:4] + salida[..., 3:4] * (1 - al)
    img = Image.fromarray(salida.astype(np.uint8))
    if cara:
        img = img.crop((0, 0, 1200, 1200))
    img.save(ruta)
    return ruta
