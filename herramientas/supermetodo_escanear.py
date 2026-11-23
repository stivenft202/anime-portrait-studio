# supermetodo_escanear.py — FASE 2 (detectores) del SÚPER MÉTODO de Anime Portrait Studio
#
# Escaneo de defectos sutiles A NIVEL DE CAPA (píxel por píxel) sobre las 67 capas
# de version-linux/assets/{Female,Male} (lienzo 1200x1600).
# Solo lectura sobre assets/: no modifica ningún archivo de capas.
#
# Detectores:
#   D-STRAY    trazos/motitas desprendidos (oscuros o café medio, 1-100 px,
#              que NO tocan la masa principal dilatada 3 px)
#   D-PROTRUDE protuberancias finas (1-3 px de ancho) que sobresalen de la
#              silueta suavizada (cierre+apertura con disco ~5 px)
#   D-SPECK    motitas 1-3 px (subconjunto de D-STRAY, reportado aparte)
#   D-HOLE     agujeros interiores (binary_fill_holes sobre alfa>200) en las
#              6 capas de ropa
#
# CALIBRACIÓN v3 (tras inspección visual de muestras de la v1/v2):
#   La v1 dio 7.095 sospechosos: ruido de textura dominaba. Muestras vistas:
#   - Pelo *_Back: la capa está construida con hebras sueltas (hasta 24.350 px
#     desprendidas de la "masa principal"); un trazo desprendido ahí es diseño.
#     Solo flota de verdad si su vecino oscuro más cercano está lejos.
#   - Motitas 1-3 px: en pelo/ropa con textura hay cientos (sombreado, AA,
#     líneas punteadas con puntos cada 10-20 px). Una motita solo es
#     sospechosa sobre fondo liso y opaco Y aislada (vecino oscuro >25 px):
#     con ese filtro quedan 3 en total, y una es el extremo de una línea
#     punteada (vista con zoom).
#   - Protuberancias: la apertura con disco 5 borra rasgos finos enteros
#     (toda la boca, pestañas) y las puntas de hebra; la "profundidad" mide
#     el largo de la hebra, no cuánto sobresale. Solo Base/Outfit dan
#     candidatos (trazo fino <=6 px, sin tocar el borde del lienzo); los
#     cordones de capucha y las puntas de solapa se excluyen por ancho.
#   Por eso cada sospechoso lleva métricas y un flag `candidato`:
#     candidato=true  -> merece revisión con zoom (Fase 3)
#     candidato=false -> diseño/textura probable (se conserva en el JSON con
#                        su nota, pero no entra en el top-20)
#   Los conteos brutos se conservan en `resumen` por capa para auditar.
#
# Exclusiones de diseño conocido se marcan con excluido=true + nota.
# Los píxeles RGB (0,0,0) con alfa 0 son transparentes: todos los detectores
# exigen alfa>150 (oscuros/café) o alfa>80 (silueta).
#
# Salida:
#   diagnostico_usuario/supermetodo/reporte_detectores.json
#   diagnostico_usuario/supermetodo/reporte_detectores.md

import hashlib
import json
import os
from collections import Counter

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = os.path.expanduser("~/workspace/anime-portrait-studio")
ASSETS = os.path.join(BASE, "version-linux/assets")
OUTDIR = os.path.join(BASE, "diagnostico_usuario/supermetodo")
OUT_JSON = os.path.join(OUTDIR, "reporte_detectores.json")
OUT_MD = os.path.join(OUTDIR, "reporte_detectores.md")

# Zona cara/cuello (heurística sobre lienzo 1200x1600; incluye cuello hasta y1150).
# Solo para priorizar.
FACE_ZONE = (250, 450, 950, 1150)  # x0, y0, x1, y1


# Veredictos de la inspección visual con zoom (Fase 2, muestras revisadas).
# Clave: (capa, detector, bbox) -> veredicto. Se añade a la nota del sospechoso.
VEREDICTOS_ZOOM = {
    ("Female/Outfit1.png", "D-PROTRUDE", (839, 900, 857, 958)):
        "ZOOM: punta de la solapa del cuello (diseño, vista amplia del cuello)",
    ("Male/Outfit3.png", "D-PROTRUDE", (835, 850, 855, 894)):
        "ZOOM: punta de la solapa del cuello (diseño, igual que Outfit1 F)",
    ("Male/Outfit1.png", "D-PROTRUDE", (568, 1088, 573, 1134)):
        "ZOOM: tirilla/hilo fino colgando del borde de la chaqueta (ambiguo)",
    ("Male/Outfit3.png", "D-PROTRUDE", (569, 1089, 574, 1134)):
        "ZOOM: tirilla colgando del borde, mismo sitio que Outfit1 M (ambiguo)",
    ("Female/Hair1_Back.png", "D-STRAY", (415, 784, 433, 787)):
        "ZOOM: trazo horizontal flotando solo, pero OCULTO tras la Base "
        "(Base alfa 255 en toda la zona; invisible en render)",
    ("Female/Hair4_Back.png", "D-STRAY", (414, 784, 433, 787)):
        "ZOOM: mismo trazo horizontal que Hair1_Back (base compartida), "
        "oculto tras la Base (invisible en render)",
    ("Female/Hair2_Back.png", "D-STRAY", (372, 520, 385, 529)):
        "ZOOM: mota oscura en hueco entre hebras (probable diseño)",
    ("Female/Hair3_Back.png", "D-STRAY", (394, 1152, 426, 1172)):
        "ZOOM: fragmento diagonal de hebra suelta (probable diseño)",
    ("Female/Hair3_Front.png", "D-STRAY", (746, 602, 758, 629)):
        "ZOOM: hebra curva suelta flotando junto a la cara (ambiguo)",
    ("Male/Hair2_Front.png", "D-STRAY", (877, 925, 904, 952)):
        "ZOOM: fragmento diagonal de hebra flotando solo, vecino a 77px "
        "(ambiguo; el más aislado del escaneo)",
    ("Male/Hair2_Front.png", "D-STRAY", (1073, 1321, 1096, 1344)):
        "ZOOM: hebra suelta marrón sobre el pecho, paralela a otra "
        "(probable diseño)",
    ("Female/Hair1_Front.png", "D-STRAY", (847, 1105, 856, 1114)):
        "ZOOM: manchita oscura en hueco entre hebras (ambiguo)",
    ("Female/Base.png", "D-SPECK", (725, 1029, 725, 1029)):
        "ZOOM: 1px en el extremo inferior de una línea punteada (diseño)",
    ("Male/Base.png", "D-SPECK", (778, 1528, 778, 1528)):
        "ZOOM: 1px aislado sobre piel lisa (vecino a 57px); 1px, invisible "
        "a tamaño de render",
    ("Male/Base.png", "D-SPECK", (359, 245, 359, 245)):
        "ZOOM: 1px aislado sobre piel lisa junto a la sien (vecino a 27px); "
        "1px, invisible a tamaño de render",
    ("Female/Eyes_Neutral.png", "D-STRAY", (316, 684, 321, 699)):
        "ZOOM: cola de la línea de pestaña, idéntica en los 5 Eyes (diseño)",
    ("Male/Base.png", "D-PROTRUDE", (234, 253, 236, 255)):
        "ZOOM: fragmento diminuto de 5px flotando a ~100px de la cabeza "
        "(vecino a 58px); posible mota real, 5px",
    ("Female/Outfit3.png", "D-PROTRUDE", (745, 872, 754, 889)):
        "ZOOM: cordón de la capucha (diseño)",
    ("Female/Outfit2.png", "D-PROTRUDE", (458, 912, 468, 915)):
        "ZOOM: guión de línea punteada de costura (diseño)",
    ("Female/Hair2_Back.png", "D-STRAY", (747, 1537, 772, 1594)):
        "ZOOM: hebra larga suelta del pelo trasero (diseño)",
}

OUTFITS = {"Outfit1.png", "Outfit2.png", "Outfit3.png"}


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def disk(radius):
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return (x * x + y * y) <= radius * radius


def components(mask):
    """Componentes conectados (8-conectividad): lista {px, bbox} por px desc."""
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return []
    sizes = ndimage.sum_labels(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    slices = ndimage.find_objects(lab)
    out = []
    for i, sl in enumerate(slices):
        if sl is None:
            continue
        out.append({
            "px": int(sizes[i]),
            "bbox": [int(sl[1].start), int(sl[0].start),
                     int(sl[1].stop) - 1, int(sl[0].stop) - 1],
        })
    out.sort(key=lambda c: -c["px"])
    return out


def component_mask(mask, bbox):
    """Máscara booleana del componente mayor dentro de bbox (recorte de mask)."""
    x0, y0, x1, y1 = bbox
    sub = mask[y0:y1 + 1, x0:x1 + 1]
    lab, n = ndimage.label(sub, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return sub
    sizes = ndimage.sum_labels(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    return lab == (int(np.argmax(sizes)) + 1)


def bbox_center(bbox):
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def in_face_zone(bbox):
    cx, cy = bbox_center(bbox)
    x0, y0, x1, y1 = FACE_ZONE
    return x0 <= cx <= x1 and y0 <= cy <= y1


def exclusion_note(sexo, name, detector, bbox):
    """Nota de exclusión (diseño conocido) o None. Se marca, no se elimina."""
    cx, cy = bbox_center(bbox)
    base = name.replace(".png", "")
    if sexo == "Female" and base == "Base" and abs(cx - 366) <= 20 and abs(cy - 714) <= 20:
        return "EXCLUIDO: tick del philtrum (diseño, Base F ~(366,714))"
    if sexo == "Male" and base == "Base" and detector == "D-STRAY" and cy < 900 and (cx < 330 or cx > 870):
        return "EXCLUIDO: posible patilla lateral (diseño, Base M)"
    if base == "FacialHair3" and detector in ("D-STRAY", "D-SPECK"):
        return "EXCLUIDO: textura de barba (diseño, FacialHair3)"
    if base.startswith("Eyes_") and detector in ("D-STRAY", "D-SPECK"):
        return "EXCLUIDO: construcción del ojo (diseño, huecos/trazos del ojo)"
    if base.startswith("Nose") and detector == "D-PROTRUDE":
        return "EXCLUIDO: trazos finos de fosa nasal (diseño, Nose*)"
    if base.startswith("Mouth_") and detector in ("D-STRAY", "D-SPECK"):
        return "POSIBLE DISENO: cuña de comisura de labio (revisar con zoom)"
    if base == "Outfit3" and detector == "D-PROTRUDE":
        return "POSIBLE DISENO: líneas de costura del hoodie (revisar con zoom)"
    if base.startswith("Outfit") and detector == "D-PROTRUDE" and 500 <= cy <= 800:
        return "POSIBLE DISENO: ribete del cuello (se tiñe con la prenda)"
    if "Hair" in base and detector in ("D-STRAY", "D-SPECK"):
        return "REVISAR: hebra suelta de pelo — diseño o trazo desprendido (ver zoom)"
    return None


def scan_layer(path, sexo, name):
    img = np.array(Image.open(path).convert("RGBA"))
    a = img[:, :, 3].astype(np.int32)
    r = img[:, :, 0].astype(np.int32)
    g = img[:, :, 1].astype(np.int32)
    b = img[:, :, 2].astype(np.int32)
    lum = (r + g + b) // 3

    suspects = []
    resumen = Counter()

    def add(detector, px, bbox, candidato, nota_extra=None, extra=None):
        nota = exclusion_note(sexo, name, detector, bbox)
        ver = VEREDICTOS_ZOOM.get((f"{sexo}/{name}", detector, tuple(bbox)))
        if ver:
            nota = (nota + " | " + ver) if nota else ver
        if nota_extra:
            nota = (nota + " | " + nota_extra) if nota else nota_extra
        d = {
            "detector": detector,
            "px": int(px),
            "bbox": [int(v) for v in bbox],
            "cara_cuello": bool(in_face_zone(bbox)),
            "candidato": bool(candidato),
            "excluido": bool(nota and nota.startswith("EXCLUIDO")),
            "nota": nota or "",
        }
        if extra:
            d.update(extra)
        suspects.append(d)

    # --- Masa principal: componente mayor de alfa>80, dilatada 3 px
    sil = a > 80
    lab, n = ndimage.label(sil, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return {"capa": f"{sexo}/{name}", "md5": md5(path),
                "sospechosos": [], "resumen": {},
                "error": "capa sin píxeles alfa>80"}
    sizes = ndimage.sum_labels(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    main = (lab == (int(np.argmax(sizes)) + 1))
    main_dil = ndimage.binary_dilation(main, structure=np.ones((3, 3), dtype=bool),
                                       iterations=3)
    dist_masa = ndimage.distance_transform_edt(~main_dil)

    # --- Máscara combinada oscuro|café (alfa>150 siempre; evita duplicados
    #     de píxeles que cumplen ambas condiciones)
    dark = (a > 150) & (lum < 120)
    brown = (a > 150) & (lum >= 100) & (lum <= 205) & ((r - b) > 25)
    mark = dark | brown

    # Componentes desprendidos grandes (>100 px): hebras de diseño en pelo
    # Back; se cuentan para auditar el efecto del tope de 100 px de D-STRAY.
    detached_big = 0
    for comp in components(mark & ~main_dil):
        if comp["px"] > 100:
            detached_big += 1
    resumen["desprendidos_mayores_100px"] = detached_big

    # Oclusión: en pelo *_Back, la Base (orden 20) tapa el pelo (orden 10).
    # Un trazo donde la Base es opaca es invisible en render.
    base_alpha = None
    if "Hair" in name and name.endswith("_Back.png"):
        try:
            base_alpha = np.array(
                Image.open(os.path.join(ASSETS, sexo, "Base.png"))
                .convert("RGBA"))[:, :, 3].astype(np.int32)
        except OSError:
            base_alpha = None

    # --- D-STRAY: 1-100 px, no tocan la masa dilatada.
    # Candidato si flota solo (vecino oscuro >15 px) o si es grande (>=15 px)
    # en zona de cara/cuello. El resto: hebra/textura cercana (diseño probable).
    for comp in components(mark & ~main_dil):
        if not (1 <= comp["px"] <= 100):
            continue
        bbox = comp["bbox"]
        x0, y0, x1, y1 = bbox
        cm = component_mask(mark, bbox)
        tipo = "oscuro" if dark[y0:y1 + 1, x0:x1 + 1][cm].sum() >= cm.sum() / 2 else "café"
        # distancia al vecino oscuro más cercano (fuera del propio componente)
        X0, Y0 = max(0, x0 - 40), max(0, y0 - 40)
        X1, Y1 = min(1200, x1 + 41), min(1600, y1 + 41)
        zone = mark[Y0:Y1, X0:X1].copy()
        zone[y0 - Y0:y1 - Y0 + 1, x0 - X0:x1 - X0 + 1] &= ~cm
        dzone = ndimage.distance_transform_edt(~zone)
        sub = dzone[y0 - Y0:y1 - Y0 + 1, x0 - X0:x1 - X0 + 1][cm]
        dist_vecino = float(sub.min()) if sub.size else 999.0
        dm = float(dist_masa[y0:y1 + 1, x0:x1 + 1][cm].min())
        cara = in_face_zone(bbox)
        cand = (dist_vecino > 15) or (cara and comp["px"] >= 15)
        if base_alpha is not None:
            cover = float((base_alpha[y0:y1 + 1, x0:x1 + 1][cm] > 150).mean())
            if cover >= 0.95:
                cand = False
                nota_oculto = "oculto tras la Base (invisible en render)"
                # se añade en add() vía nota_extra
                add("D-STRAY", comp["px"], bbox, cand,
                    f"tipo={tipo} | {nota_oculto}",
                    {"dist_vecino_px": round(dist_vecino, 1),
                     "dist_masa_px": round(dm, 1),
                     "oculto_tras_base": True})
                resumen["D-STRAY_bruto"] += 1
                continue
        resumen["D-STRAY_bruto"] += 1
        resumen["D-STRAY_candidatos"] += 1 if cand else 0
        add("D-STRAY", comp["px"], bbox, cand, f"tipo={tipo}",
            {"dist_vecino_px": round(dist_vecino, 1),
             "dist_masa_px": round(dm, 1)})

    # --- D-SPECK: 1-3 px. Candidato solo si está AISLADO de verdad:
    # ventana 21x21 con >80% opaca (alfa>150) y <3% de píxeles oscuros/café,
    # Y vecino oscuro/café más cercano a >25 px. Sin el requisito de
    # aislamiento, las líneas punteadas y el punteado de sombreado (puntos
    # cada 10-20 px) inundan el detector: con aislamiento quedan 3 en total,
    # y la inspección visual mostró que incluso uno de ellos es el extremo
    # de una línea punteada.
    opaq = a > 150
    for comp in components(mark):
        if not (1 <= comp["px"] <= 3):
            continue
        bbox = comp["bbox"]
        cx, cy = int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2)
        w_mark = mark[max(0, cy - 10):cy + 11, max(0, cx - 10):cx + 11]
        w_opaq = opaq[max(0, cy - 10):cy + 11, max(0, cx - 10):cx + 11]
        frac_osc = float(w_mark.mean())
        frac_opaq = float(w_opaq.mean())
        if not ((frac_opaq > 0.8) and (frac_osc < 0.03)):
            resumen["D-SPECK_bruto"] += 1
            continue
        x0, y0, x1, y1 = bbox
        cm = component_mask(mark, bbox)
        X0, Y0 = max(0, x0 - 40), max(0, y0 - 40)
        X1, Y1 = min(1200, x1 + 41), min(1600, y1 + 41)
        zone = mark[Y0:Y1, X0:X1].copy()
        zone[y0 - Y0:y1 - Y0 + 1, x0 - X0:x1 - X0 + 1] &= ~cm
        dzone = ndimage.distance_transform_edt(~zone)
        sub = dzone[y0 - Y0:y1 - Y0 + 1, x0 - X0:x1 - X0 + 1][cm]
        dist_vecino = float(sub.min()) if sub.size else 999.0
        cand = dist_vecino > 25
        resumen["D-SPECK_bruto"] += 1
        resumen["D-SPECK_candidatos"] += 1 if cand else 0
        if cand:
            tipo = "oscuro" if dark[y0:y1 + 1, x0:x1 + 1][cm].sum() >= cm.sum() / 2 else "café"
            add("D-SPECK", comp["px"], bbox, True, f"tipo={tipo}",
                {"ventana_opaca": round(frac_opaq, 2),
                 "ventana_oscura": round(frac_osc, 3),
                 "dist_vecino_px": round(dist_vecino, 1)})

    # --- D-PROTRUDE: silueta menos silueta suavizada (cierre+apertura disco 5).
    # CALIBRACIÓN v3: la apertura con disco 5 borra por completo los rasgos
    # finos (boca, ojos, nariz) y las puntas de hebra, así que en pelo/ojos/
    # boca/nariz/barba TODA protrusión es diseño o artefacto del detector.
    # Solo Base y Outfit (siluetas grandes y lisas) dan candidatos, y solo si
    # el trazo es fino (ancho_max <= 6 px, la clase buscada es 1-3 px) y no
    # toca el borde del lienzo (el pelo/ropa se corta ahí por diseño).
    # La "profundidad" (distancia a la silueta suavizada) NO discrimina: en
    # una hebra larga mide el largo de la hebra, no cuánto sobresale; se
    # conserva solo como métrica de auditoría. Se añade dist_vecino para
    # detectar guiones de líneas punteadas de costura.
    foot = disk(5)
    smoothed = ndimage.binary_closing(sil, structure=foot)
    smoothed = ndimage.binary_opening(smoothed, structure=foot)
    prot = sil & ~smoothed
    dist = ndimage.distance_transform_edt(sil)
    depth_edt = ndimage.distance_transform_edt(~smoothed)
    base_outfit = name.startswith("Base") or name.startswith("Outfit")
    labp, np_ = ndimage.label(prot, structure=np.ones((3, 3), dtype=int))
    if np_:
        psizes = ndimage.sum_labels(np.ones_like(labp), labp,
                                    index=np.arange(1, np_ + 1))
        pmaxw = ndimage.maximum(dist, labp, index=np.arange(1, np_ + 1))
        pdepth = ndimage.maximum(depth_edt, labp, index=np.arange(1, np_ + 1))
        pslices = ndimage.find_objects(labp)
        for i, sl in enumerate(pslices):
            if sl is None:
                continue
            px = int(psizes[i])
            if not (5 <= px <= 200):
                continue
            bbox = [int(sl[1].start), int(sl[0].start),
                    int(sl[1].stop) - 1, int(sl[0].stop) - 1]
            ancho = round(float(2 * pmaxw[i]), 1)
            prof = round(float(pdepth[i]), 1)
            toca_borde = (bbox[0] <= 20 or bbox[1] <= 20 or
                          bbox[2] >= 1179 or bbox[3] >= 1579)
            x0, y0, x1, y1 = bbox
            cm = component_mask(prot, bbox)
            X0, Y0 = max(0, x0 - 40), max(0, y0 - 40)
            X1, Y1 = min(1200, x1 + 41), min(1600, y1 + 41)
            zone = sil[Y0:Y1, X0:X1].copy()
            zone[y0 - Y0:y1 - Y0 + 1, x0 - X0:x1 - X0 + 1] &= ~cm
            dzone = ndimage.distance_transform_edt(~zone)
            sub = dzone[y0 - Y0:y1 - Y0 + 1, x0 - X0:x1 - X0 + 1][cm]
            dist_vecino = float(sub.min()) if sub.size else 999.0
            cand = base_outfit and (ancho <= 6) and not toca_borde
            resumen["D-PROTRUDE_bruto"] += 1
            resumen["D-PROTRUDE_candidatos"] += 1 if cand else 0
            nota = None
            if not base_outfit:
                if "Hair" in name:
                    nota = "punta de hebra (diseño; la apertura borra hebras)"
                elif name.startswith("Eyes"):
                    nota = "pestaña / trazo del ojo (diseño)"
                else:
                    nota = ("rasgo fino (la apertura borra el rasgo; "
                            "artefacto del detector, no defecto)")
            elif toca_borde:
                nota = "toca borde del lienzo (corte de capa, no defecto)"
            elif ancho > 6:
                nota = f"trazo grueso ({ancho}px: cordón/solapa/pliegue, diseño)"
            add("D-PROTRUDE", px, bbox, cand, nota,
                {"ancho_max_px": ancho, "profundidad_px": prof,
                 "toca_borde": bool(toca_borde),
                 "dist_vecino_px": round(dist_vecino, 1)})

    # --- D-HOLE: agujeros interiores solo en las 6 capas de ropa
    hole_total = 0
    hole_n = 0
    hole_max = 0
    if name in OUTFITS:
        filled = ndimage.binary_fill_holes(a > 200)
        holes = filled & ~(a > 200)
        for comp in components(holes):
            hole_total += comp["px"]
            hole_n += 1
            hole_max = max(hole_max, comp["px"])
            # Candidato: agujero de >=3 px (1-2 px es ruido de AA, como ya se
            # vio en T17-02 para Outfit3 y los de hombre)
            add("D-HOLE", comp["px"], comp["bbox"], comp["px"] >= 3)
        resumen["D-HOLE_bruto"] = hole_n
        resumen["D-HOLE_candidatos"] = sum(
            1 for s in suspects if s["detector"] == "D-HOLE" and s["candidato"])

    return {
        "capa": f"{sexo}/{name}",
        "md5": md5(path),
        "sospechosos": suspects,
        "resumen": dict(resumen),
        "agujeros_px_total": hole_total,
        "agujeros_n_componentes": hole_n,
        "agujero_max_px": hole_max,
    }


def main():
    layers = []
    for sexo in ("Female", "Male"):
        d = os.path.join(ASSETS, sexo)
        for name in sorted(os.listdir(d)):
            if name.lower().endswith(".png"):
                layers.append((sexo, name))
    print(f"Capas a escanear: {len(layers)}")
    assert len(layers) == 67, f"se esperaban 67 capas, hay {len(layers)}"

    results = []
    for sexo, name in layers:
        res = scan_layer(os.path.join(ASSETS, sexo, name), sexo, name)
        results.append(res)
        r = res["resumen"]
        print(f"{sexo}/{name}: STRAY {r.get('D-STRAY_candidatos',0)}/{r.get('D-STRAY_bruto',0)} "
              f"PROT {r.get('D-PROTRUDE_candidatos',0)}/{r.get('D-PROTRUDE_bruto',0)} "
              f"SPECK {r.get('D-SPECK_candidatos',0)}/{r.get('D-SPECK_bruto',0)} "
              f"HOLE {r.get('D-HOLE_candidatos',0)}/{r.get('D-HOLE_bruto',0)}"
              + (f" | agujeros={res['agujeros_px_total']}px max={res['agujero_max_px']}px" if name in OUTFITS else ""))

    by_detector_bruto = Counter()
    by_detector_cand = Counter()
    excluidos = 0
    for res in results:
        for s in res["sospechosos"]:
            by_detector_bruto[s["detector"]] += 1
            if s["candidato"]:
                by_detector_cand[s["detector"]] += 1
        excluidos += sum(1 for s in res["sospechosos"] if s["excluido"])
    total_bruto = sum(by_detector_bruto.values())
    total_cand = sum(by_detector_cand.values())

    for res in results:
        for det in ("D-STRAY", "D-PROTRUDE", "D-SPECK", "D-HOLE"):
            n = sum(1 for s in res["sospechosos"] if s["detector"] == det)
            assert n < 1000, f"BUG detector {det} en {res['capa']}: {n} sospechosos"

    report = {
        "metodo": "supermetodo FASE 2 — detectores a nivel de capa (v3 calibrada)",
        "capas_escaneadas": len(results),
        "total_sospechosos_bruto": total_bruto,
        "total_candidatos": total_cand,
        "por_detector_bruto": dict(by_detector_bruto),
        "por_detector_candidatos": dict(by_detector_cand),
        "excluidos_diseno": excluidos,
        "capas": results,
    }
    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Top 20: candidatos no excluidos, prioridad cara/cuello, luego mayor px
    all_s = [(res["capa"], s) for res in results for s in res["sospechosos"]]
    def flota(s):
        # STRAY: flota si su vecino oscuro está lejos; SPECK/PROTRUDE/HOLE
        # son candidatos ya filtrados por aislamiento o por silueta lisa.
        if s["detector"] == "D-STRAY":
            return s.get("dist_vecino_px", 0) > 15
        return True

    ranked = sorted(
        [t for t in all_s if t[1]["candidato"] and not t[1]["excluido"]],
        key=lambda t: (flota(t[1]), t[1]["cara_cuello"], t[1]["px"]),
        reverse=True)
    top20 = ranked[:20]

    lines = []
    lines.append("# Reporte FASE 2 — Detectores a nivel de capa (SÚPER MÉTODO, v3 calibrada)")
    lines.append("")
    lines.append(f"Capas escaneadas: **{len(results)}** (Female 41 + Male 26). "
                 "Solo lectura sobre `version-linux/assets/`; ningún archivo de "
                 "capa fue modificado.")
    lines.append("")
    lines.append("## Calibración (por qué la v1 daba 7.095 y la v3 no)")
    lines.append("")
    lines.append("- La v1 (detectores literales) dio 7.095 sospechosos: la mayoría "
                 "era textura de la propia capa. Se inspeccionaron zooms de muestras "
                 "y se calibró cada detector con una métrica de aislamiento; los "
                 "conteos brutos se conservan por capa para auditar.")
    lines.append("- **Pelo `*_Back`**: la capa está construida con hebras sueltas "
                 "(p. ej. Hair2_Back F tiene 27 componentes desprendidos >100 px, "
                 "el mayor de 24.350 px); un trazo desprendido ahí es diseño salvo "
                 "que flote solo (vecino oscuro a >15 px).")
    lines.append("- **D-SPECK**: candidato solo sobre fondo liso y opaco (ventana "
                 "21×21 con >80% opaca y <3% oscura) Y con el vecino oscuro a "
                 ">25 px; sin el aislamiento, las líneas punteadas y el punteado "
                 "de sombreado (puntos cada 10-20 px) inundan el detector.")
    lines.append("- **D-PROTRUDE**: candidato solo en Base y Outfit (siluetas "
                 "grandes y lisas), trazo fino (ancho <=6 px) y sin tocar el "
                 "borde del lienzo. En pelo/ojos/boca/nariz/barba la apertura "
                 "con disco 5 borra el rasgo entero, así que toda protrusión "
                 "ahí es diseño o artefacto del detector.")
    lines.append("- **D-HOLE**: candidato solo si el agujero es >=3 px (1-2 px es "
                 "ruido de AA, como ya se documentó en T17-02).")
    lines.append("")
    lines.append("## Totales por detector (candidatos / brutos)")
    lines.append("")
    for det in ("D-STRAY", "D-PROTRUDE", "D-SPECK", "D-HOLE"):
        lines.append(f"- **{det}**: {by_detector_cand.get(det, 0)} candidatos "
                     f"/ {by_detector_bruto.get(det, 0)} brutos")
    lines.append(f"- **Total**: {total_cand} candidatos / {total_bruto} brutos "
                 f"({excluidos} marcados EXCLUIDO = diseño conocido)")
    lines.append("")
    lines.append("## Totales por capa (candidatos / brutos; solo capas con candidatos)")
    lines.append("")
    for res in sorted(results, key=lambda r: -sum(
            1 for s in r["sospechosos"] if s["candidato"])):
        nc = sum(1 for s in res["sospechosos"] if s["candidato"])
        if nc == 0:
            continue
        c = Counter(s["detector"] for s in res["sospechosos"] if s["candidato"])
        b = Counter(s["detector"] for s in res["sospechosos"])
        lines.append(f"- {res['capa']}: " +
                     ", ".join(f"{k}={c[k]}/{b[k]}" for k in sorted(c)))
    lines.append("")
    lines.append("## D-HOLE en ropa (agujeros interiores, alfa>200)")
    lines.append("")
    for res in results:
        if res["capa"].split("/")[1] in OUTFITS:
            lines.append(f"- {res['capa']}: {res['agujeros_px_total']} px en "
                         f"{res['agujeros_n_componentes']} componentes, "
                         f"mayor {res['agujero_max_px']} px")
    lines.append("")
    lines.append("## Top 20 candidatos más relevantes "
                 "(no excluidos; prioridad: flota solo, luego cara/cuello, luego mayor px; "
                 "con veredicto visual donde se inspeccionó con zoom)")
    lines.append("")
    for i, (capa, s) in enumerate(top20, 1):
        det = s["detector"]
        met = ""
        if det == "D-STRAY":
            met = (f"vecino a {s.get('dist_vecino_px')} px, "
                   f"masa a {s.get('dist_masa_px')} px")
        elif det == "D-PROTRUDE":
            met = f"ancho ~{s.get('ancho_max_px')} px"
        elif det == "D-SPECK":
            met = (f"ventana {s.get('ventana_opaca', 0) * 100:.0f}% opaca, "
                   f"{s.get('ventana_oscura', 0) * 100:.1f}% oscura, "
                   f"vecino a {s.get('dist_vecino_px')} px")
        lines.append(f"{i}. **{capa}** — {det}, {s['px']} px, bbox {s['bbox']}, "
                     f"cara/cuello={s['cara_cuello']}. {met}. "
                     f"{s['nota'] or 'Sin nota de diseño: candidato a defecto.'}")
    lines.append("")
    lines.append("## Notas de método")
    lines.append("")
    lines.append("- D-STRAY: componentes oscuros (alfa>150, lum<120) o café "
                 "(lum 100-205, R-B>25, alfa>150) de 1-100 px que no tocan la "
                 "masa principal (componente mayor de alfa>80, dilatada 3 px). "
                 "Máscara combinada (sin duplicar píxeles que cumplen ambas).")
    lines.append("- D-SPECK: subconjunto 1-3 px de lo anterior, en cualquier zona; "
                 "candidato solo sobre fondo liso y opaco y aislado (vecino >25 px).")
    lines.append("- D-PROTRUDE: silueta (alfa>80) menos silueta suavizada "
                 "(cierre+apertura con disco de radio 5 px); componentes 5-200 px; "
                 "candidatos solo en Base/Outfit con ancho <=6 px. La profundidad "
                 "se conserva como métrica pero no discrimina (mide el largo de "
                 "la hebra en pelo).")
    lines.append("- D-HOLE: `binary_fill_holes` sobre alfa>200, solo en las 6 "
                 "capas de ropa.")
    lines.append("- Zona cara/cuello usada para priorizar: x 250-950, y 450-1150.")
    lines.append("- Female Hair1_Front: md5 verificado "
                 f"{md5(os.path.join(ASSETS, 'Female', 'Hair1_Front.png'))} "
                 "(versión con la rayita ya arreglada; el detector no la re-detecta).")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nTOTAL candidatos: {total_cand} / brutos: {total_bruto} | "
          f"por detector (cand): {dict(by_detector_cand)} | excluidos: {excluidos}")
    print(f"JSON: {OUT_JSON}\nMD: {OUT_MD}")


if __name__ == "__main__":
    main()
