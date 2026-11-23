# supermetodo_fix_correccion.py — Corrección de los ítems 3, 5, 8, 9, 10 y 23.
#
# Hallazgos de la inspección (sobre el snapshot, ANTES del fix):
#  - Ítem 3 (Male/Nose1): la máscara oscura+café conecta la nariz entera
#    en un solo componente (2546 px) y tragó el componente dudoso de 10 px
#    (296,633)-(300,637) que está PROHIBIDO tocar. Con máscara SOLO oscura
#    (alfa>150, lum<120) las 4 motitas de 1 px y el trazo de 3 px son
#    componentes aislados exactos, y los componentes de 19 px y 10 px
#    quedan intactos. Se usa máscara oscura + tamaño <= 3 px.
#  - Ítem 5 (Male/Base): las motitas del cuello son trazos oscuros (16 px
#    y 14 px exactos con máscara oscura) embebidos en sombra café que los
#    conecta a la red gigante de sombreado. Con máscara oscura son
#    componentes exactos. Se usa máscara oscura + inpaint.
#  - Ítem 8 (Male/Base): con máscara oscura son 19+1 = 20 px exactos.
#  - Ítem 9 (Male/Base): el fragmento son 5 px con alfa>0 en la ventana
#    3x3 (1 oscuro + 4 grises tenues lum 137-182, R-B<25); el resto de la
#    ventana es transparente. Se borran los 5 px con alfa>0 del bbox.
#  - Ítem 10 (Male/Base): 1 px café cada uno; máscara oscura+café.
#  - Ítem 23 (Male/Outfit2): el hilo es negro (0,0,0) con alfa 85 (65 px),
#    120 (7 px) y 255 (10 px): 82 px en total. La máscara alfa>150 solo
#    veía 10 px. Se usa máscara (alfa>50, lum<120).
#  - Ítems 6 y 7: NO APLICABLES. Verificado en snapshot: 0 px de Base
#    fuera de la silueta de Outfit1, Outfit2 u Outfit3 (ni con alfa>0 ni
#    con alfa>80, ni por outfit individual ni por unión) en ambas zonas.
#    La Base queda siempre DENTRO del borde de la ropa (p. ej. ítem 6,
#    y=1290: Base xmin=216, Outfit2 xmin=213). No se fuerza nada.
#
# Actualiza diagnostico_usuario/supermetodo/supermetodo_fix_reporte.json
# (reescribe los ítems corregidos y añade 6/7 como no-aplicados).

import hashlib
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(BASE, "version-linux", "assets")
REPORT = os.path.join(BASE, "diagnostico_usuario", "supermetodo",
                      "supermetodo_fix_reporte.json")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def mascaras(im):
    r, g, b, al = (im[..., i].astype(int) for i in range(4))
    lum = (r + g + b) // 3
    dark = (al > 150) & (lum < 120)
    brown = (al > 150) & (lum >= 100) & (lum < 205) & ((r - b) > 25)
    return {"dark": dark, "union": dark | brown,
            "negro50": (al > 50) & (lum < 120)}


def componentes(mask):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        ys, xs = np.where(m)
        out.append({"bbox": (int(xs.min()), int(ys.min()),
                             int(xs.max()), int(ys.max())),
                    "px": int(m.sum()), "mask": m})
    return out


def seleccionar(comps, bbox, exp=2, px_max=None):
    x0, y0, x1, y1 = bbox
    cands = [c for c in comps
             if c["bbox"][0] >= x0 - exp and c["bbox"][1] >= y0 - exp
             and c["bbox"][2] <= x1 + exp and c["bbox"][3] <= y1 + exp
             and (px_max is None or c["px"] <= px_max)]
    return cands


def piel_local(im):
    zona = im[650:750, 450:550]
    m = zona[..., 3] > 200
    return np.median(zona[m][:, :3].astype(float), axis=0)


def inpaint_piel(im, mask, iters=500):
    out = im[..., :3].astype(float).copy()
    out[mask] = piel_local(im)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0)
               + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4.0
        out[mask] = avg[mask]
    im2 = im.copy()
    im2[..., :3] = np.clip(out, 0, 255).astype("uint8")
    return im2


# (nº, capa, máscara, [(bbox, px_esperado, px_max)], método)
PLAN = [
    (3, "Male/Nose1.png", "dark",
     [((310, 620, 310, 620), 1, 3), ((301, 632, 301, 632), 1, 3),
      ((295, 639, 295, 639), 1, 3), ((293, 701, 293, 701), 1, 3),
      ((312, 726, 312, 728), 3, 3)], "erase"),
    (5, "Male/Base.png", "dark",
     [((767, 780, 773, 788), 16, None), ((787, 751, 791, 759), 14, None)],
     "inpaint"),
    (8, "Male/Base.png", "dark",
     [((840, 818, 849, 825), 20, None)], "erase"),
    (10, "Male/Base.png", "union",
     [((359, 245, 359, 245), 1, 3), ((778, 1528, 778, 1528), 1, 3)],
     "inpaint"),
    (23, "Male/Outfit2.png", "negro50",
     [((558, 1023, 562, 1057), 83, None)], "erase"),
]


def main():
    reporte = json.load(open(REPORT, encoding="utf-8"))
    # Quitar los registros previos de los ítems que se corrigen (3,5,8,10,23)
    # y los de 6/7; se reescriben abajo. Se conservan los demás.
    reporte["items"] = [it for it in reporte["items"]
                        if it["n"] not in (3, 5, 6, 7, 8, 10, 23)]
    fallos = []

    por_capa = {}
    for num, capa, mask, bboxes, metodo in PLAN:
        por_capa.setdefault(capa, []).append((num, mask, bboxes, metodo))

    for capa in sorted(por_capa):
        ruta = os.path.join(A, capa)
        md5_antes = reporte["capas"][capa]["md5_antes"]
        assert md5(ruta) == md5_antes, f"{capa}: no está en estado snapshot"
        orig = np.asarray(Image.open(ruta).convert("RGBA"))
        im = orig.copy()
        msk = mascaras(orig)
        union = np.zeros(orig.shape[:2], bool)
        inpaint_masks = []

        for num, maskname, bboxes, metodo in sorted(por_capa[capa]):
            comps = componentes(msk[maskname])
            for bbox, esperado, px_max in bboxes:
                cands = seleccionar(comps, bbox, exp=2, px_max=px_max)
                if not cands:
                    reporte["items"].append(
                        {"n": num, "capa": capa, "metodo": metodo,
                         "bbox": list(bbox), "px_esperado": esperado,
                         "px": 0, "ok": False,
                         "nota": "CORRECCIÓN: sin componente con la "
                                 "máscara corregida"})
                    fallos.append((num, bbox))
                    continue
                m = np.zeros(orig.shape[:2], bool)
                for c in cands:
                    m |= c["mask"]
                n = int(m.sum())
                if metodo == "erase":
                    im[m] = 0
                else:
                    inpaint_masks.append(m)
                union |= m
                reporte["items"].append(
                    {"n": num, "capa": capa, "metodo": metodo,
                     "bbox": list(bbox), "px_esperado": esperado,
                     "px": n, "ok": True,
                     "nota": f"CORRECCIÓN máscara {maskname}: "
                             f"{len(cands)} componente(s)"})

        # Ítem 9: borrar los 5 px con alfa>0 dentro del bbox 3x3.
        if capa == "Male/Base.png":
            x0, y0, x1, y1 = 234, 253, 236, 255
            m9 = np.zeros(orig.shape[:2], bool)
            m9[y0:y1 + 1, x0:x1 + 1] = orig[y0:y1 + 1, x0:x1 + 1, 3] > 0
            n9 = int(m9.sum())
            assert n9 == 5, f"ítem 9: {n9} px con alfa>0, se esperaban 5"
            im[m9] = 0
            union |= m9
            reporte["items"].append(
                {"n": 9, "capa": capa, "metodo": "erase",
                 "bbox": [234, 253, 236, 255], "px_esperado": 5, "px": n9,
                 "ok": True,
                 "nota": "CORRECCIÓN: 5 px con alfa>0 en ventana 3x3 "
                         "(1 oscuro + 4 grises tenues)"})

        if inpaint_masks:
            m_inp = np.zeros(orig.shape[:2], bool)
            for m in inpaint_masks:
                m_inp |= m
            im = inpaint_piel(im, m_inp)

        dif = (np.abs(im[..., :3].astype(int) - orig[..., :3].astype(int))
               .sum(axis=2) > 0) | (im[..., 3] != orig[..., 3])
        assert not (dif & ~union).any(), \
            f"{capa}: cambios fuera de las máscaras objetivo"
        Image.fromarray(im).save(ruta)
        md5_desp = md5(ruta)
        reporte["capas"][capa]["md5_despues"] = md5_desp
        reporte["capas"][capa]["px_tocados"] = int(union.sum())
        print(f"{capa}: corrección {int(union.sum())} px | "
              f"{md5_antes[:8]} -> {md5_desp[:8]}")

    # Ítems 6 y 7: no aplicables (verificado: 0 px fuera de ropa).
    for num, zona in ((6, "x[100,260] y[1290,1480]"),
                      (7, "x[1175,1200] y[1220,1245]")):
        reporte["items"].append(
            {"n": num, "capa": "Male/Base.png", "metodo": "fuera-ropa",
             "px": 0, "ok": False,
             "nota": f"NO APLICADO: 0 px de Base fuera de la silueta de "
                     f"Outfit1, Outfit2 u Outfit3 (alfa>0 y alfa>80, por "
                     f"outfit y unión) en zona {zona}; la Base queda "
                     f"siempre dentro del borde de la ropa. Defecto no "
                     f"presente a nivel de capa con el método indicado; "
                     f"no se fuerza."})

    reporte["items"].sort(key=lambda it: it["n"])
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print("FALLOS corrección:", fallos if fallos else "ninguno")
    print("Reporte actualizado:", REPORT)


if __name__ == "__main__":
    main()
