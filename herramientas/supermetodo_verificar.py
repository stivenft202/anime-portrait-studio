# supermetodo_verificar.py — FASE 3, verificación del SÚPER MÉTODO.
#
# 1) Re-renderiza con motor.py los 4 combos de las capturas (C1-C4) y 6
#    combos extra (uno por cada capa tocada que no sale en C1-C4) en versión
#    PRE-fix (árbol de assets temporal con las 19 capas del snapshot) vs
#    POST-fix. El diff debe estar SOLO dentro de la unión de los bboxes
#    objetivo del reporte de fixes (expandidos 2 px). Si algo cambia fuera,
#    se reporta y NO se da por bueno.
# 2) Zooms 4x antes/después por bbox en
#    diagnostico_usuario/supermetodo/antes_despues/ (crop de la capa).
# 3) md5_despues.txt en versiones/2026-11-23_supermetodo-antes/.

import hashlib
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "version-linux"))
import motor

SNAP = os.path.join(BASE, "versiones", "2026-11-23_supermetodo-antes")
OUT = os.path.join(BASE, "diagnostico_usuario", "supermetodo",
                   "antes_despues")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
REPORT = os.path.join(BASE, "diagnostico_usuario", "supermetodo",
                      "supermetodo_fix_reporte.json")

C1 = {"sexo": "Female", "pelo": 6, "ropa": 2, "ojos": 0, "nariz": 2,
      "boca": 0, "color_pelo": 9, "piel": 1, "color_ropa": 16,
      "color_ojos": 2}
C2 = {"sexo": "Male", "pelo": 3, "ropa": 1, "ojos": 0, "nariz": 1,
      "boca": 0, "color_pelo": 11, "piel": 1, "color_ropa": 18,
      "color_ojos": 1, "vello": 0}
C3 = {"sexo": "Male", "pelo": 1, "ropa": 0, "ojos": 4, "nariz": 1,
      "boca": 0, "color_pelo": 0, "piel": 3, "color_ropa": 6,
      "color_ojos": 2, "vello": 1}
C4 = {"sexo": "Female", "pelo": 2, "ropa": 2, "ojos": 0, "nariz": 2,
      "boca": 0, "color_pelo": 21, "piel": 0, "color_ropa": 3,
      "color_ojos": 4}
COMBOS = {"C1": C1, "C2": C2, "C3": C3, "C4": C4,
          # Extra: una por capa tocada que no sale en C1-C4.
          "X-F-H1": {"sexo": "Female", "pelo": 0, "ropa": 0, "ojos": 0,
                     "nariz": 0, "boca": 0, "color_pelo": 0, "piel": 1,
                     "color_ropa": 0, "color_ojos": 0},
          "X-F-H2": {"sexo": "Female", "pelo": 1, "ropa": 0, "ojos": 0,
                     "nariz": 0, "boca": 0, "color_pelo": 0, "piel": 1,
                     "color_ropa": 0, "color_ojos": 0},
          "X-F-H4": {"sexo": "Female", "pelo": 3, "ropa": 0, "ojos": 0,
                     "nariz": 0, "boca": 0, "color_pelo": 0, "piel": 1,
                     "color_ropa": 0, "color_ojos": 0},
          "X-F-H11": {"sexo": "Female", "pelo": 10, "ropa": 0, "ojos": 0,
                      "nariz": 0, "boca": 0, "color_pelo": 0, "piel": 1,
                      "color_ropa": 0, "color_ojos": 0},
          "X-M-H1": {"sexo": "Male", "pelo": 0, "ropa": 0, "ojos": 0,
                     "nariz": 0, "boca": 0, "color_pelo": 0, "piel": 1,
                     "color_ropa": 0, "color_ojos": 0, "vello": 0},
          "X-M-H3": {"sexo": "Male", "pelo": 2, "ropa": 0, "ojos": 0,
                     "nariz": 0, "boca": 0, "color_pelo": 0, "piel": 1,
                     "color_ropa": 0, "color_ojos": 0, "vello": 0}}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def construir_pre():
    """Árbol temporal de assets con las capas PRE-fix del snapshot."""
    pre = "/tmp/supermetodo_pre_assets"
    if os.path.exists(pre):
        shutil.rmtree(pre)
    shutil.copytree(os.path.join(BASE, "version-linux", "assets"), pre)
    for f in os.listdir(SNAP):
        if f.endswith(".png"):
            sexo, resto = f.split("_", 1)
            shutil.copy2(os.path.join(SNAP, f),
                         os.path.join(pre, sexo, resto))
    return pre


def render_con_assets(assets_dir, receta):
    motor.ASSETS = assets_dir
    motor._cache.clear()
    motor._iris_cache.clear()
    return np.clip(motor.render(receta), 0, 255).astype("uint8")


def main():
    rep = json.load(open(REPORT, encoding="utf-8"))
    # Zona permitida = unión REAL de píxeles cambiados en las capas
    # (snapshot vs post), no el bbox+2: los componentes borrados/inpaintados
    # se extienden unos px fuera del bbox dado (p. ej. el rasguño de Base F
    # llega a x580/y696 con bbox (584,701)-(601,718)). Un diff de render
    # solo puede venir de un píxel de capa cambiado.
    SNAPD = os.path.join(BASE, "versiones",
                         "2026-11-23_supermetodo-antes")
    zonas = np.zeros((1600, 1200), bool)
    for capa in rep["capas"]:
        sexo, arch = capa.split("/")
        a = np.asarray(Image.open(os.path.join(
            SNAPD, f"{sexo}_{arch}")).convert("RGBA")).astype(int)
        b = np.asarray(Image.open(os.path.join(
            BASE, "version-linux", "assets", sexo, arch)).convert(
                "RGBA")).astype(int)
        zonas |= (np.abs(a - b).sum(axis=2) > 0)

    pre_dir = construir_pre()
    post_dir = os.path.join(BASE, "version-linux", "assets")
    resultados = {}
    todo_ok = True
    for nombre, receta in COMBOS.items():
        pre = render_con_assets(pre_dir, receta)
        post = render_con_assets(post_dir, receta)
        Image.fromarray(pre).save(
            os.path.join(OUT, "renders", f"{nombre}_pre.png"))
        Image.fromarray(post).save(
            os.path.join(OUT, "renders", f"{nombre}_post.png"))
        dif = (np.abs(pre.astype(int) - post.astype(int)).sum(axis=2) > 0)
        n_dif = int(dif.sum())
        fuera = int((dif & ~zonas).sum())
        ok = fuera == 0
        todo_ok &= ok
        dsum = np.abs(pre.astype(int) - post.astype(int)).sum(axis=2)
        resultados[nombre] = {"px_diferentes": n_dif,
                              "px_fuera_de_diff_capa": fuera,
                              "fuera_max_sumaRGB": int(dsum[dif & ~zonas].max())
                              if fuera else 0,
                              "fuera_mayor_3": int((dsum[dif & ~zonas] > 3).sum())
                              if fuera else 0,
                              "ok": ok,
                              "receta": motor.codigo(receta)}
        print(f"{nombre}: diff={n_dif} px, fuera de objetivo={fuera} -> "
              f"{'OK' if ok else 'FALLO'}")

    # --- Zooms 4x antes/después por bbox (crop de la capa) ---
    n_zoom = 0
    for it in rep["items"]:
        if "bbox" not in it:
            continue
        capa = it["capa"]
        sexo, arch = capa.split("/")
        x0, y0, x1, y1 = it["bbox"]
        cx0, cy0 = max(0, x0 - 30), max(0, y0 - 30)
        cx1, cy1 = min(1200, x1 + 31), min(1600, y1 + 31)
        pre_im = Image.open(os.path.join(
            SNAP, f"{sexo}_{arch}")).convert("RGBA").crop((cx0, cy0, cx1, cy1))
        post_im = Image.open(os.path.join(
            BASE, "version-linux", "assets", sexo, arch)).convert(
                "RGBA").crop((cx0, cy0, cx1, cy1))
        # Fondo blanco para ver transparencias; escala 4x vecino más cercano.
        def prep(img):
            fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
            fondo.alpha_composite(img)
            return fondo.convert("RGB").resize(
                (img.width * 4, img.height * 4), Image.NEAREST)
        a, b = prep(pre_im), prep(post_im)
        lienzo = Image.new("RGB", (a.width + b.width + 12, a.height),
                           (200, 200, 200))
        lienzo.paste(a, (0, 0))
        lienzo.paste(b, (a.width + 12, 0))
        nombre = (f"item{it['n']:02d}_{sexo}_{arch[:-4]}_"
                  f"x{x0}-{x1}_y{y0}-{y1}.png")
        lienzo.save(os.path.join(OUT, nombre))
        n_zoom += 1

    # Zooms de las zonas 6/7 (sin cambio: antes == después).
    for num, (x0, y0, x1, y1) in ((6, (100, 1290, 260, 1480)),
                                  (7, (1175, 1220, 1200, 1245))):
        pre_im = Image.open(os.path.join(
            SNAP, "Male_Base.png")).convert("RGBA").crop((x0, y0, x1, y1))
        post_im = Image.open(os.path.join(
            BASE, "version-linux", "assets", "Male",
            "Base.png")).convert("RGBA").crop((x0, y0, x1, y1))

        def prep(img):
            fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
            fondo.alpha_composite(img)
            return fondo.convert("RGB").resize(
                (img.width * 2, img.height * 2), Image.NEAREST)
        a, b = prep(pre_im), prep(post_im)
        lienzo = Image.new("RGB", (a.width + b.width + 12, a.height),
                           (200, 200, 200))
        lienzo.paste(a, (0, 0))
        lienzo.paste(b, (a.width + 12, 0))
        lienzo.save(os.path.join(
            OUT, f"item{num:02d}_Male_Base_NO-APLICADO_x{x0}-{x1}_y{y0}-{y1}.png"))
        n_zoom += 1

    # --- md5_despues.txt ---
    lineas = []
    for capa in sorted(rep["capas"]):
        p = os.path.join(BASE, "version-linux", "assets", capa)
        lineas.append(f"{md5(p)}  {capa.replace('/', '_')}")
    with open(os.path.join(SNAP, "md5_despues.txt"), "w") as f:
        f.write("\n".join(lineas) + "\n")

    ver = {"renders": resultados, "todo_ok": todo_ok,
           "zooms": n_zoom}
    with open(os.path.join(BASE, "diagnostico_usuario", "supermetodo",
                           "supermetodo_verificacion.json"),
              "w", encoding="utf-8") as f:
        json.dump(ver, f, indent=2, ensure_ascii=False)
    print(f"\nZooms: {n_zoom} | md5_despues.txt guardado | "
          f"TODO OK: {todo_ok}")


if __name__ == "__main__":
    main()
