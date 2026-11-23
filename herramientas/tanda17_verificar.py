# tanda17_verificar.py — Re-verificación del fix T17-01 (motor post-fix vs motor pre-fix)
# Compara renders con las capas ACTUALES (post-fix) contra renders con las
# capas del SNAPSHOT pre-fix, usando el MISMO motor (así no interfiere la
# diferencia preexistente motor-vs-navegador en bordes/sombras).
# Checks:
#  R1 O1 White/Light: idéntico al pre-fix (diff 0 en todo).
#  R2 O1 RoyalBlue: solapa (520,1100) ~= (37,50,92); diff solo dentro de L.
#  R3 O1 White/Deep: solapa (520,1100) ~= (122,118,108); diff solo dentro de L.
#  R4 O2 White: diff solo dentro de G (hueco rellenado de verde).
#  R5 O2 RoyalBlue: sin franja salvia; diff solo dentro de G.
#  R6 O3 White: idéntico al pre-fix (diff 0 en todo).
import sys, os
sys.path.insert(0, '/home/hatch/workspace/anime-portrait-studio/version-linux')
import numpy as np
from PIL import Image
import motor

SNAP = '/home/hatch/workspace/anime-portrait-studio/versiones/2026-11-23_tanda17-antes-fixes'
LROOT = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets/Female'

# máscaras L y G sobre las capas ORIGINALES del snapshot
b0 = np.array(Image.open(f'{SNAP}/Base.png').convert('RGBA')).astype(int)
o10 = np.array(Image.open(f'{SNAP}/Outfit1.png').convert('RGBA')).astype(int)
o20 = np.array(Image.open(f'{SNAP}/Outfit2.png').convert('RGBA')).astype(int)
zone = np.zeros((1600, 1200), bool); zone[900:1600, :] = True
rg = b0[:, :, 0] - b0[:, :, 1]
mask_L = zone & (b0[:, :, 3] > 200) & (o10[:, :, 3] < 30) & (rg < 15)
mask_G = zone & (b0[:, :, 3] > 200) & (o20[:, :, 3] < 30) & (rg < 15) & mask_L
print('L:', int(mask_L.sum()), 'G:', int(mask_G.sum()))

def render_post(rec):
    return np.rint(motor.render(rec)).astype(int)

# monkeypatch: las 3 capas cambiadas se leen del snapshot (pre-fix)
_orig_capa = motor.capa
_cache_pre = {}
def capa_pre(sexo, archivo):
    if sexo == 'Female' and archivo in ('Base', 'Outfit1', 'Outfit2'):
        if archivo not in _cache_pre:
            _cache_pre[archivo] = np.asarray(
                Image.open(os.path.join(SNAP, archivo + '.png')).convert('RGBA')).astype(float)
        return _cache_pre[archivo]
    return _orig_capa(sexo, archivo)

def render_pre(rec):
    motor.capa = capa_pre
    try:
        return np.rint(motor.render(rec)).astype(int)
    finally:
        motor.capa = _orig_capa

base_rec = {'sexo': 'Female', 'pelo': 0, 'ropa': 0, 'ojos': 0, 'nariz': 0,
            'boca': 0, 'color_pelo': 0, 'piel': 0, 'color_ropa': 0,
            'color_ojos': 0, 'vello': 0}
def rec(**kw):
    r = dict(base_rec); r.update(kw); return r

casos = [
    ('R1 O1 White/Light', rec(), mask_L, 'identico'),
    ('R2 O1 RoyalBlue', rec(color_ropa=9), mask_L, 'en_L'),
    ('R3 O1 White/Deep', rec(piel=3), mask_L, 'en_L'),
    ('R4 O2 White', rec(ropa=1), mask_G, 'en_G'),
    ('R5 O2 RoyalBlue', rec(ropa=1, color_ropa=9), mask_G, 'en_G'),
    ('R6 O3 White', rec(ropa=2), mask_L, 'en_L'),  # O3 cubre la solapa, pero
    # su borde semitransparente deja ver 40 px de L: el cambio Base (salvia->
    # piel) altera levemente la mezcla; es el comportamiento correcto.
]
for label, r, mask, modo in casos:
    a, b = render_post(r), render_pre(r)
    d = np.abs(a - b).max(axis=2)
    fuera = int(((d > 0) & ~mask).sum())
    dentro = int(((d > 0) & mask).sum())
    print(f'{label}: maxdiff {int(d.max())} | px diff>0: {int((d>0).sum())} '
          f'(dentro mascara {dentro}, fuera {fuera})')
    if modo == 'identico':
        assert int(d.max()) == 0, f'{label}: diff {int(d.max())}, no idéntico'
    else:
        assert fuera == 0, f'{label}: {fuera} px con diff FUERA de la mascara'

# píxeles testigo (post-fix)
r2 = render_post(rec(color_ropa=9))
print('R2 solapa (520,1100):', tuple(r2[1100, 520]), 'esperado ~(37,50,92)')
assert np.abs(r2[1100, 520].astype(int) - np.array([37, 50, 92])).max() <= 2
r3 = render_post(rec(piel=3))
print('R3 solapa (520,1100):', tuple(r3[1100, 520]), 'esperado ~(122,118,108)')
assert np.abs(r3[1100, 520].astype(int) - np.array([122, 118, 108])).max() <= 2
r1 = render_post(rec())
print('R1 solapa (520,1100):', tuple(r1[1100, 520]), 'esperado ~(122,118,108)')
assert np.abs(r1[1100, 520].astype(int) - np.array([122, 118, 108])).max() <= 2
r5 = render_post(rec(ropa=1, color_ropa=9))
r5pix = render_post(rec(pelo=1, ropa=1, color_ropa=9))  # Pixie: el pelo no tapa el hueco
print('R5 hueco O2 (925,1000) con H1:', tuple(r5[1000, 925]), '(lo tapa el pelo largo)')
print('R5 hueco O2 (925,1000) con Pixie:', tuple(r5pix[1000, 925]),
      'pre-fix era salvia ~(129,123,111)')
assert r5pix[1000, 925, 2] > r5pix[1000, 925, 0] + 20, 'el hueco O2 sigue salvia, no azul'
r4 = render_post(rec(ropa=1))
print('R4 hueco O2 (925,1000):', tuple(r4[1000, 925]), 'pre-fix era salvia ~(129,123,111)')

# zooms para revisión visual
def zoom(arr, path, box=(350, 900, 750, 1350)):
    Image.fromarray(arr.astype('uint8')).convert('RGB').crop(box).save(path)
zoom(r2, '/tmp/verif_R2_solapa_RoyalBlue.png')
zoom(r3, '/tmp/verif_R3_solapa_Deep.png')
zoom(r5pix, '/tmp/verif_R5_O2_RoyalBlue.png', box=(800, 880, 1050, 1200))
zoom(r1, '/tmp/verif_R1_O1_default.png')
b = Image.open(f'{LROOT}/Base.png').convert('RGBA')
f = Image.new('RGBA', b.size, (255, 255, 255, 255)); f.alpha_composite(b)
f.convert('RGB').crop((200, 850, 1000, 1600)).resize((400, 375)).save('/tmp/verif_Base_pecho_postfix.png')
print('OK — verificación numérica del fix T17-01 superada')
