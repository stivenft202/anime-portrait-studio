#!/usr/bin/env python3
"""
limpiar_capas.py — Puerta de calidad OBLIGATORIA para toda capa de pelo nueva
(Anime Half Portrait Studio). Se corre sobre el set crudo recien extraido y
luego la auditoria de compuesto debe dar ~0 antes de entregar.

Uso:
  python3 limpiar_capas.py <carpeta_capas> <femenino|masculino> <carpeta_salida>

Enfermedades que cura (nacen en la extraccion, SIEMPRE):
  1. Masa de pelo semitransparente: la base calva (piel, lum ~210-245) brilla
     a traves del frente/trasero y se ve como trazos claros entre mechones.
     -> Solidificacion: dentro de la zona de pelo del dibujo fuente, el alfa
        sube a >=235 con el RGB del propio dibujo donde la capa era fina.
  2. Islas claras (lineas de separacion palidas horneadas en la capa).
     -> Recolor por propagacion desde el pelo vecino de la misma capa.
  3. Huecos del frente sobre la base (la coronilla/flequillo dejan ver piel).
     -> La solidificacion los cubre: trabaja sobre alfa, no solo huecos = 0.

Auditoria (lo que ve el usuario, no proxies de capa):
  Para cada pelo x {Natural, Natural Black, Wine Red, Chestnut}:
  compuesto donde el dibujo es pelo (lum<160) y el compuesto supera al dibujo
  en >50 de luminosidad = trazo fantasma. Debe quedar en ~0.
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

BG = {"femenino": np.array([204.0, 223.0, 233.0]), "masculino": np.array([202.0, 222.0, 229.0])}
CRUDOS = {
    "femenino": ("/home/hatch/workspace/retratos-anime/fase1/crudos/mujer_v2",
                 "/home/hatch/workspace/retratos-anime/fase1/pruebas/mujer_v2_maestro.png"),
    "masculino": ("/home/hatch/workspace/retratos-anime/fase1/crudos/hombre_v2",
                  "/home/hatch/workspace/retratos-anime/fase1/crudos/hombre_v2/maestro_a_norm.png"),
}

def dibujo_de(crudo_dir, maestro, h):
    if h == 1:
        return maestro
    return os.path.join(crudo_dir, f"dibujo_pelo{h}_ali.png")

def prop_fill(work, fleck, known):
    todo = fleck.copy()
    for _ in range(80):
        if not todo.any():
            break
        ker = np.ones((3, 3))
        cntm = ndimage.convolve(known.astype(float), ker, mode="constant")
        fillable = todo & (cntm > 0)
        if not fillable.any():
            break
        for ch in range(3):
            s = ndimage.convolve(np.where(known, work[..., ch], 0.0), ker, mode="constant")
            work[..., ch] = np.where(fillable, s / np.maximum(cntm, 1), work[..., ch])
        known |= fillable
        todo &= ~fillable
    return todo

def solidificar(capa, dib, bg):
    """Sube el alfa de la masa de pelo a >=235 dentro de la zona de pelo del
    dibujo, estampando el RGB del dibujo donde la capa era fina."""
    dib_hair = (np.abs(dib - bg).max(axis=2) > 25) & (dib.mean(axis=2) < 175)
    presente = capa[..., 3] > 40
    region = dib_hair & ndimage.binary_dilation(presente, iterations=16)
    region = ndimage.binary_closing(region, iterations=2)
    fina = region & (capa[..., 3] < 235)
    if not fina.sum():
        return capa, 0
    # alfa objetivo con borde suave de 2 px
    objetivo = ndimage.gaussian_filter(fina.astype(float), sigma=0.9)
    objetivo = np.clip(objetivo * 1.8, 0, 1) * 235
    sel = fina & (objetivo > capa[..., 3])
    capa = capa.copy()
    capa[..., 3] = np.where(sel, objetivo, capa[..., 3])
    capa[..., :3] = np.where(sel[..., None], dib, capa[..., :3])
    return capa, int(sel.sum())

def recolor_islas(capa, dib, bg):
    """Recolorea pixeles claros (lum>92) dentro de la silueta de pelo del
    dibujo desde el pelo vecino de la misma capa."""
    sil = ndimage.binary_dilation(np.abs(dib - bg).max(axis=2) > 25, iterations=2)
    lum = capa[..., :3].mean(axis=2)
    fleck = sil & (capa[..., 3] > 8) & (lum > 92)
    if not fleck.sum():
        return capa, 0
    work = capa.copy()
    known = (capa[..., 3] > 8) & (lum <= 92)
    rest = prop_fill(work, fleck, known)
    if rest.any():
        med = np.median(capa[..., :3][known], axis=0) if known.any() else np.array([50., 40., 35.])
        for ch in range(3):
            work[..., ch] = np.where(rest, med[ch], work[..., ch])
    return work, int(fleck.sum())

def sellar_fantasmas(carpeta_base, carpeta_salida, dibs, bg):
    """Paso 3: sello guiado por el compuesto. Renderiza el retrato (con la
    Base/Outfit1/Expression de carpeta_base y los pelos de carpeta_salida) y
    estampa en el FRENTE el RGB del dibujo en todo grupo fantasma >=40 px
    (donde el dibujo es pelo y el compuesto brilla >50 por encima). Itera
    hasta 0. El frente es la unica capa que puede tapar a la base."""
    def load(n, st=None):
        p = os.path.join(st, n) if st else os.path.join(carpeta_base, n)
        if st and not os.path.exists(p):
            p = os.path.join(carpeta_base, n)
        return np.asarray(Image.open(p).convert("RGBA")).astype(float)
    for h, dib in dibs.items():
        dib_hair = (np.abs(dib - bg).max(axis=2) > 25) & (dib.mean(axis=2) < 160)
        dib_hair[1350:] = False
        front = load(f"Hair{h}_Front.png", carpeta_salida)
        back = load(f"Hair{h}_Back.png", carpeta_salida)
        base = load("Base.png"); outfit = load("Outfit1.png"); expr = load("Expression_Neutral.png")
        for _ in range(3):
            c = np.zeros((1600, 1200, 4)); c[..., :3] = (40, 44, 52); c[..., 3] = 255
            for lay in (back, base, outfit, expr, front):
                a = lay[..., 3:4] / 255.0
                c[..., :3] = lay[..., :3] * a + c[..., :3] * (1 - a)
            ghost = dib_hair & (c[..., :3].mean(axis=2) > dib.mean(axis=2) + 50)
            lab, cnt = ndimage.label(ghost)
            if not cnt:
                break
            sizes = ndimage.sum(np.ones_like(lab), lab, range(1, cnt + 1))
            keep = np.isin(lab, [i + 1 for i in range(cnt) if sizes[i] >= 40])
            if not keep.sum():
                break
            soft = ndimage.gaussian_filter(keep.astype(float), sigma=0.8)
            a_new = np.clip(soft * 1.8, 0, 1) * 245
            sel = a_new > front[..., 3]
            front[..., 3] = np.where(sel, a_new, front[..., 3])
            front[..., :3] = np.where(sel[..., None], dib, front[..., :3])
        Image.fromarray(front.clip(0, 255).astype(np.uint8), "RGBA").save(
            os.path.join(carpeta_salida, f"Hair{h}_Front.png"))
        print(f"Hair{h}_Front: fantasmas sellados")

def main():
    carpeta, genero, salida = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(salida, exist_ok=True)
    bg = BG[genero]
    crudo_dir, maestro = CRUDOS[genero]
    for h in (1, 2, 3, 4):
        dib = np.asarray(Image.open(dibujo_de(crudo_dir, maestro, h)).convert("RGB")).astype(float)
        for parte in ("Back", "Front"):
            ruta = os.path.join(carpeta, f"Hair{h}_{parte}.png")
            capa = np.asarray(Image.open(ruta).convert("RGBA")).astype(float)
            capa, n_sol = solidificar(capa, dib, bg)
            capa, n_rec = recolor_islas(capa, dib, bg)
            Image.fromarray(capa.clip(0, 255).astype(np.uint8), "RGBA").save(
                os.path.join(salida, f"Hair{h}_{parte}.png"))
            print(f"Hair{h}_{parte}: solidificados {n_sol} px, islas recoloreadas {n_rec} px")
    dibs = {}
    for h in (1, 2, 3, 4):
        dibs[h] = np.asarray(Image.open(dibujo_de(crudo_dir, maestro, h)).convert("RGB")).astype(float)
    sellar_fantasmas(carpeta, salida, dibs, bg)

if __name__ == "__main__":
    main()

# =====================================================================
# EXTENSION stage11 (21 nov): la puerta cubre TODAS las capas, no solo pelo.
# Enfermedades adicionales cazadas (visibles sobre todo con piel Deep,
# porque la expresion nunca se tine y la base si):
#  4. Expresiones: manchas palidas grises fuera de los rasgos (gotas junto
#     al ojo lejano) y agujeros dentro del iris -> limpieza por lista
#     blanca: se borra todo componente fuera de la zona de rasgos y toda
#     mancha palida no encerrada por trazo oscuro (la esclerotica y los
#     dientes SI estan encerrados); los agujeros encerrados se rellenan.
#  5. Bases: fantasmas de los rasgos del dibujo calvo (anillos del iris,
#     brillos de labio) -> difuminado de las cajas de ojos con pluma ANCHA
#     (sigma 14; una pluma fina deja una banda visible); fleco frio del
#     borde y rim mas claro que la piel -> recolor desde la piel opaca.
#  6. Ropas: la misma enfermedad de alfa que el pelo (el buso dejaba ver
#     el pelo trasero como trazos marrones) -> solidificar dentro de la
#     silueta de prenda del dibujo (prenda = no-fondo y no-piel, y>800).
#  7. Puntitos blancos en el pelo de la mujer: componentes claros chicos
#     (<=40 px, lum>170) DENTRO de la silueta -> recolor por propagacion.
#     SOLO componentes chicos: el brillo dibujado de ella son componentes
#     grandes y se respeta. PROHIBIDO defringe amplio en su pelo: su
#     textura de mechones es semitransparente a proposito y se aplana.
# =====================================================================

# =====================================================================
# EXTENSION stage12 (21 nov): ROPAS y FRENTES — lecciones de la ronda del buso
# - Las ROPAS jamas se "solidifican" estampando RGB del dibujo con una mascara
#   ingenua (no-fondo & no-piel): incluye pelo y sombra del cuello y RECOLOREA
#   miles de px (stage11 dano las 6 ropas; hubo que restaurarlas del ZIP v12).
#   Lo unico permitido en ropas: (a) recolorear trazos palido-calidos PEQUENOS
#   rodeados de prenda (mayoria local no palida), (b) rellenar huecos interiores
#   (silueta rellena, alfa<90) con el color PROPIO propagado, (c) recolorear
#   piel-en-prenda rodeada de prenda. PROHIBIDO borrar por "fuera de la silueta
#   del personaje del dibujo": en el hombre eso perforo la camiseta interior
#   de Outfit1 (7.235 px) porque el maestro lleva la camisa distinta.
# - Los "trazos" sobre el buso NO eran (solo) la ropa: los FRENTES de pelo 2/3
#   traen horneado el CONTORNO BEIGE de la prenda del dibujo (line art de la
#   chaqueta del dibujo pelo2) y un BORDE CLARO (rim (174,166,151)) que sigue
#   el contorno inferior del pelo. Al teñir el pelo (Wine) se vuelven lineas
#   rojas que calcan los pliegues de CUALQUIER prenda. Diagnostico correcto:
#   aislar capas (sin frente / sin trasero / sin ropa) antes de tocar nada.
# - Borrado seguro del rim: alfa>40 & lum>115 & R-B>12 & y>850 & NO pelo-segun-
#   el-dibujo (erosion 1-2). SIN proteccion por "vecindario oscuro": el rim
#   abraza la masa de pelo y esa proteccion lo salvaba. Para pelos LARGOS
#   (1 y 4) NO aplicar pasadas de pixeles calidos: sus mechones legitimos
#   sobre la ropa son calidos y se destruyen (verificado: 12-18 mil px).
# - Revisar la matriz COMPLETA (96 combos por personaje) en hojas de contacto
#   Y hojas de TORSO aparte: la hoja de caras no muestra el pecho.
# =====================================================================
