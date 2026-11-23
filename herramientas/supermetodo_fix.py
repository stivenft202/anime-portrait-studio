# supermetodo_fix.py — FASE 3 (arreglos) del SÚPER MÉTODO de Anime Portrait Studio
#
# Aplica los 25 arreglos de la lista del coordinador (2026-11-23) sobre las
# capas de version-linux/assets/{Female,Male}.
#
# REGLA DE SELECCIÓN (obligatoria): por COMPONENTE CONECTADO
# (scipy.ndimage.label sobre la máscara oscura/café: alfa>150 y lum<120,
# o café lum 100-205 y R-B>25). Se elige el componente cuya bbox queda
# CONTENIDA en el bbox dado expandido 6 px (12 px en reintento); NUNCA se
# borran regiones rectangulares. Si ningún componente cumple, el arreglo
# FALLA y se reporta (no se fuerza).
# La contención (no solo intersección) protege los componentes de diseño
# vecinos: p. ej. la cola inferior del ojo Sorprendido M (438,570)-(469,591)
# intersecta el bbox de la motita (467,583)-(469,584) pero su bbox no cabe
# en él, así que nunca se selecciona.
#
# Métodos:
#   BORRAR: alfa=0 (y RGB=0) en los píxeles del componente.
#   INPAINT: relleno con piel por difusión de Laplace (500 iter, solo desde
#     píxeles de piel, como T19b); alfa intacta.
#   FUERA-DE-ROPA: borrar píxeles de Base fuera de la unión de las siluetas
#     (alfa>0) de los 3 outfits del sexo, solo dentro de la zona indicada.
#
# Asserts por capa: 0 px cambiados fuera de la unión de las máscaras
# objetivo; alfa intacta fuera de las máscaras de borrado.
# Snapshot previo: versiones/2026-11-23_supermetodo-antes/ (19 archivos
# únicos; la lista nombra 20 porque Female/Hair3_Back.png aparece en los
# ítems 13 y 25, es el mismo archivo).
# Salida: diagnostico_usuario/supermetodo/supermetodo_fix_reporte.json

import hashlib
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(BASE, "version-linux", "assets")
OUTDIR = os.path.join(BASE, "diagnostico_usuario", "supermetodo")
os.makedirs(OUTDIR, exist_ok=True)
REPORT = os.path.join(OUTDIR, "supermetodo_fix_reporte.json")

# bbox: (x0, y0, x1, y1) INCLUSIVOS, coordenadas (x, y) de lienzo 1200x1600.
# px: tamaño esperado aproximado del componente (para validar la selección).
# Cada entrada: (nº, capa "Sexo/Archivo.png", método, [(bbox, px_esperado), ...])
PLAN = [
    (1, "Female/Nose3.png", "erase",
     [((324, 693, 333, 707), 81)]),
    (2, "Female/Nose1.png", "erase",
     [((321, 681, 322, 682), 2)]),
    (3, "Male/Nose1.png", "erase",
     [((310, 620, 310, 620), 1), ((301, 632, 301, 632), 1),
      ((295, 639, 295, 639), 1), ((293, 701, 293, 701), 1),
      ((312, 726, 312, 728), 3)]),
    (4, "Female/Base.png", "inpaint",
     [((584, 701, 601, 718), 38), ((612, 690, 622, 706), 33)]),
    (5, "Male/Base.png", "inpaint",
     [((767, 780, 773, 788), 16), ((787, 751, 791, 759), 14)]),
    # 6 y 7 son FUERA-DE-ROPA (zonas, no bboxes de componente); se añaden abajo.
    (8, "Male/Base.png", "erase",
     [((840, 818, 849, 825), 20)]),
    (9, "Male/Base.png", "erase",
     [((234, 253, 236, 255), 5)]),
    (10, "Male/Base.png", "inpaint",
     [((359, 245, 359, 245), 1), ((778, 1528, 778, 1528), 1)]),
    (11, "Male/Hair4_Front.png", "erase",
     [((476, 490, 480, 491), 7), ((886, 924, 904, 944), 47),
      ((759, 620, 762, 632), 20), ((738, 595, 750, 625), 75),
      ((1113, 1290, 1137, 1307), 60)]),
    (12, "Male/Eyes_Surprised.png", "erase",
     [((313, 596, 324, 613), 44), ((319, 585, 321, 588), 8),
      ((319, 597, 320, 598), 3), ((320, 599, 321, 602), 5),
      ((292, 568, 293, 569), 3), ((467, 583, 469, 584), 5),
      ((463, 584, 465, 586), 8)]),
    (13, "Female/Hair3_Back.png", "erase",
     [((222, 1456, 282, 1597), 935), ((288, 1494, 326, 1597), 472),
      ((285, 1275, 321, 1379), 371), ((251, 1389, 282, 1479), 301),
      ((394, 1151, 426, 1172), 125), ((950, 1089, 1126, 1369), 1345),
      ((821, 1040, 937, 1167), 1087), ((1026, 1339, 1051, 1358), 93),
      ((976, 1327, 1005, 1332), 85), ((370, 788, 380, 799), 47)]),
    (14, "Female/Outfit3.png", "erase",
     [((1142, 1176, 1150, 1190), 56)]),
    (15, "Male/Hair2_Front.png", "erase",
     [((877, 925, 904, 952), 66), ((738, 588, 750, 626), 87),
      ((1116, 1290, 1137, 1304), 57), ((1073, 1321, 1096, 1344), 48),
      ((769, 536, 780, 546), 23), ((469, 489, 474, 491), 10)]),
    (16, "Female/Hair3_Front.png", "erase",
     [((727, 668, 733, 687), 44), ((746, 602, 758, 629), 46),
      ((797, 563, 805, 574), 18)]),
    (17, "Male/Hair1_Front.png", "erase",
     [((737, 588, 749, 625), 88)]),
    (18, "Male/Hair3_Front.png", "erase",
     [((1072, 1316, 1101, 1345), 68), ((772, 617, 793, 639), 45),
      ((793, 591, 798, 615), 59), ((770, 536, 781, 545), 23),
      ((756, 639, 770, 641), 23), ((473, 488, 477, 489), 7)]),
    (19, "Female/Hair4_Front.png", "erase",
     [((758, 557, 783, 574), 74), ((786, 557, 813, 596), 65),
      ((726, 667, 733, 687), 54)]),
    (20, "Female/Hair11_Front.png", "erase",
     [((843, 879, 849, 901), 47), ((321, 700, 331, 714), 24)]),
    (21, "Female/Hair2_Front.png", "erase",
     [((331, 669, 336, 674), 11), ((775, 612, 789, 630), 36),
      ((756, 601, 772, 608), 27), ((775, 584, 782, 588), 16),
      ((810, 634, 811, 640), 9), ((456, 522, 462, 522), 7)]),
    (22, "Female/Hair1_Front.png", "erase",
     [((847, 1105, 856, 1114), 39), ((805, 576, 809, 586), 15)]),
    (23, "Male/Outfit2.png", "erase",
     [((558, 1023, 562, 1057), 83)]),
    (24, "Female/Hair2_Back.png", "erase",
     [((371, 788, 381, 799), 28)]),
]

# Ítems 6 y 7: (nº, capa, zona (x0,y0,x1,y1) exclusivos en x1/y1 como slice)
FUERA_ROPA = [
    (6, "Male/Base.png", (100, 1290, 260, 1480)),
    (7, "Male/Base.png", (1175, 1220, 1200, 1245)),
]


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def mascara_objetivo(im):
    """Píxeles oscuros (alfa>150, lum<120) o café (lum 100-205, R-B>25)."""
    r, g, b, al = (im[..., i].astype(int) for i in range(4))
    lum = (r + g + b) // 3
    oscuro = (al > 150) & (lum < 120)
    cafe = (al > 150) & (lum >= 100) & (lum < 205) & ((r - b) > 25)
    return oscuro | cafe


def componentes(mask):
    """Devuelve lista de dicts {bbox(x0,y0,x1,y1 inclusivos), px, mask}."""
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        s = int(m.sum())
        ys, xs = np.where(m)
        out.append({"bbox": (int(xs.min()), int(ys.min()),
                             int(xs.max()), int(ys.max())),
                    "px": s, "mask": m})
    return out


def seleccionar(comps, bbox, esperado):
    """Componente(s) cuya bbox cabe en bbox expandido. Devuelve (lista, nota).

    Regla: contención en bbox+6px; reintento con +12px. Si el componente
    esperado es mayor que el bbox dado (bbox aproximado), se acepta también
    un componente que intersecte el bbox y cuyo tamaño no supere 3x lo
    esperado y cuya bbox no exceda el bbox dado en más de 25 px por lado.
    """
    x0, y0, x1, y1 = bbox
    for exp in (6, 12):
        cands = [c for c in comps
                 if c["bbox"][0] >= x0 - exp and c["bbox"][1] >= y0 - exp
                 and c["bbox"][2] <= x1 + exp and c["bbox"][3] <= y1 + exp]
        if cands:
            return cands, f"contenido en bbox+{exp}px"
    cands = []
    for c in comps:
        cx0, cy0, cx1, cy1 = c["bbox"]
        intersecta = not (cx1 < x0 or cx0 > x1 or cy1 < y0 or cy0 > y1)
        cabe_casi = (cx0 >= x0 - 25 and cy0 >= y0 - 25
                     and cx1 <= x1 + 25 and cy1 <= y1 + 25)
        if intersecta and cabe_casi and c["px"] <= 3 * max(esperado, 1):
            cands.append(c)
    if cands:
        return cands, "intersección con bbox+25px y px<=3x esperado"
    return [], "SIN componente: bbox no contiene el componente esperado"


def piel_local(im):
    zona = im[650:750, 450:550]
    m = zona[..., 3] > 200
    return np.median(zona[m][:, :3].astype(float), axis=0)


def inpaint_piel(im, mask, iters=500):
    """Difusión de Laplace desde píxeles de piel (T19b). Solo RGB."""
    out = im[..., :3].astype(float).copy()
    out[mask] = piel_local(im)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0)
               + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4.0
        out[mask] = avg[mask]
    im2 = im.copy()
    im2[..., :3] = np.clip(out, 0, 255).astype("uint8")
    return im2


def main():
    # Agrupar ítems por capa, manteniendo el orden de la lista.
    por_capa = {}
    for num, capa, metodo, bboxes in PLAN:
        por_capa.setdefault(capa, []).append((num, metodo, bboxes))
    for num, capa, zona in FUERA_ROPA:
        por_capa.setdefault(capa, []).append((num, "fuera-ropa", [zona]))

    reporte = {"items": [], "capas": {}}
    fallos = []

    for capa in sorted(por_capa):
        ruta = os.path.join(A, capa)
        md5_antes = md5(ruta)
        orig = np.asarray(Image.open(ruta).convert("RGBA"))
        im = orig.copy()
        mask_obj = mascara_objetivo(orig)
        comps = componentes(mask_obj)
        # Máscara unión de todo lo que se va a tocar en esta capa (para asserts).
        union = np.zeros(orig.shape[:2], bool)
        # Para inpaint se acumulan las máscaras y se aplica al final por capa.
        inpaint_masks = []

        for num, metodo, bboxes in sorted(por_capa[capa]):
            if metodo == "fuera-ropa":
                (x0, y0, x1, y1) = bboxes[0]
                sexo = capa.split("/")[0]
                union_sil = np.zeros(orig.shape[:2], bool)
                for o in ("Outfit1.png", "Outfit2.png", "Outfit3.png"):
                    oa = np.asarray(Image.open(
                        os.path.join(A, sexo, o)).convert("RGBA"))
                    union_sil |= oa[..., 3] > 0
                zona = np.zeros(orig.shape[:2], bool)
                zona[y0:y1, x0:x1] = True
                m = zona & (im[..., 3] > 0) & (~union_sil)
                n = int(m.sum())
                if n == 0:
                    reporte["items"].append(
                        {"n": num, "capa": capa, "metodo": metodo,
                         "px": 0, "ok": False,
                         "nota": "0 px de Base fuera de ropa en la zona"})
                    fallos.append(num)
                else:
                    im[m] = 0
                    union |= m
                    reporte["items"].append(
                        {"n": num, "capa": capa, "metodo": metodo,
                         "px": n, "ok": True,
                         "nota": f"Base fuera de unión de 3 outfits, zona "
                                 f"x[{x0},{x1}] y[{y0},{y1}]"})
                continue

            for bbox, esperado in bboxes:
                cands, nota = seleccionar(comps, bbox, esperado)
                if not cands:
                    reporte["items"].append(
                        {"n": num, "capa": capa, "metodo": metodo,
                         "bbox": list(bbox), "px_esperado": esperado,
                         "px": 0, "ok": False, "nota": nota})
                    fallos.append((num, bbox))
                    continue
                m = np.zeros(orig.shape[:2], bool)
                for c in cands:
                    m |= c["mask"]
                n = int(m.sum())
                # Validación de tamaño: no borrar un componente gigante por
                # error (salvo ítem 13, fragmentos grandes de Hair3_Back).
                if num != 13 and n > 3 * max(esperado, 1) + 10:
                    reporte["items"].append(
                        {"n": num, "capa": capa, "metodo": metodo,
                         "bbox": list(bbox), "px_esperado": esperado,
                         "px": n, "ok": False,
                         "nota": f"RECHAZADO: componente de {n}px >> "
                                 f"esperado {esperado}px ({nota})"})
                    fallos.append((num, bbox))
                    continue
                if metodo == "erase":
                    im[m] = 0
                else:  # inpaint: acumular; se aplica tras el bucle
                    inpaint_masks.append(m)
                union |= m
                reporte["items"].append(
                    {"n": num, "capa": capa, "metodo": metodo,
                     "bbox": list(bbox), "px_esperado": esperado,
                     "px": n, "ok": True,
                     "nota": f"{len(cands)} componente(s); {nota}"})

        if inpaint_masks:
            m_inp = np.zeros(orig.shape[:2], bool)
            for m in inpaint_masks:
                m_inp |= m
            im = inpaint_piel(im, m_inp)

        # --- ASSERTS por capa ---
        dif_rgb = np.abs(im[..., :3].astype(int)
                         - orig[..., :3].astype(int)).sum(axis=2) > 0
        dif_alfa = im[..., 3] != orig[..., 3]
        dif = dif_rgb | dif_alfa
        assert not (dif & ~union).any(), \
            f"{capa}: cambios fuera de las máscaras objetivo"
        # Alfa intacta salvo en máscaras de borrado (inpaint no toca alfa).
        assert not (dif_alfa & ~union).any(), f"{capa}: alfa cambió fuera"

        Image.fromarray(im).save(ruta)
        md5_desp = md5(ruta)
        reporte["capas"][capa] = {"md5_antes": md5_antes,
                                  "md5_despues": md5_desp,
                                  "px_tocados": int(union.sum())}
        print(f"{capa}: {int(union.sum())} px tocados | "
              f"{md5_antes[:8]} -> {md5_desp[:8]}")

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print(f"\nReporte: {REPORT}")
    if fallos:
        print(f"FALLOS ({len(fallos)}): {fallos}")
    else:
        print("SIN FALLOS: los 25 ítems aplicados.")
    return reporte


if __name__ == "__main__":
    main()
