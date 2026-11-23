#!/usr/bin/env python3
"""FASE 4 (coordinador) — verificación independiente post-fix.

1. Re-renderiza C1-C4 PRE-fix (árbol temporal: snapshot + symlinks al resto)
   vs POST-fix (assets actuales) con motor.py y recetas CORRECTAS de
   capturas.json. El diff de render debe estar contenido en la unión de los
   px cambiados a nivel de capa (snapshot vs actual).
2. Control C3 con color_ojos=0 (sin tinte): debe dar 0 px fuera.
3. Guarda renders post-fix + zooms 4x de cada zona circulada por Stiven.
"""
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.expanduser("~/workspace/anime-portrait-studio")
sys.path.insert(0, os.path.join(BASE, "version-linux"))
import motor

SNAP = os.path.join(BASE, "versiones/2026-11-23_supermetodo-antes")
OUT = os.path.join(BASE, "diagnostico_usuario/supermetodo/capturas")
os.makedirs(OUT, exist_ok=True)

CAPS = json.load(open(os.path.join(OUT, "capturas.json")))["capturas"]

# --- árbol PRE-fix: symlinks a assets reales, salvo las 19 capas del snapshot
TMP = "/tmp/sm4_pre"
shutil.rmtree(TMP, ignore_errors=True)
for sexo in ("Female", "Male"):
    os.makedirs(os.path.join(TMP, sexo), exist_ok=True)
    for f in os.listdir(os.path.join(BASE, "version-linux/assets", sexo)):
        os.symlink(os.path.join(BASE, "version-linux/assets", sexo, f),
                   os.path.join(TMP, sexo, f))
# sobrescribir los 19 con el snapshot (rm del symlink + copia real)
for f in os.listdir(SNAP):
    if not f.endswith(".png"):
        continue
    sexo, resto = f.split("_", 1)
    dest = os.path.join(TMP, sexo, resto)
    os.remove(dest)
    shutil.copy(os.path.join(SNAP, f), dest)


def render(receta, assets_dir):
    motor.ASSETS = assets_dir
    motor._cache.clear()
    motor._iris_cache.clear()
    arr = motor.render(receta)
    return np.clip(arr, 0, 255).astype("uint8")


# --- máscara de px cambiados a nivel de capa (snapshot vs actual)
capa_diff = {}
for f in os.listdir(SNAP):
    if not f.endswith(".png"):
        continue
    sexo, resto = f.split("_", 1)
    a = np.array(Image.open(os.path.join(SNAP, f)).convert("RGBA")).astype(int)
    b = np.array(Image.open(os.path.join(BASE, "version-linux/assets", sexo, resto)).convert("RGBA")).astype(int)
    capa_diff[f"{sexo}/{resto}"] = np.any(a != b, axis=2)
    print(f"{sexo}/{resto}: {int(capa_diff[f'{sexo}/{resto}'].sum())} px cambiados en capa")


def capas_de_receta(receta):
    sexo = receta["sexo"]
    files = [f"{sexo}/Base.png",
             f"{sexo}/Hair{receta['pelo'] + 1}_Back.png",
             f"{sexo}/Outfit{receta['ropa'] + 1}.png",
             f"{sexo}/Nose{receta['nariz'] + 1}.png",
             f"{sexo}/Eyes_{['Neutral', 'Happy', 'Sad', 'Angry', 'Surprised'][receta['ojos']]}.png",
             f"{sexo}/Mouth_{['Neutral', 'Happy', 'Sad', 'Angry', 'Surprised'][receta['boca']] if sexo == 'Female' else ['Neutral', 'Happy', 'Surprised'][receta['boca']]}.png",
             f"{sexo}/Hair{receta['pelo'] + 1}_Front.png"]
    if sexo == "Male" and receta.get("vello", 0):
        files.append(f"Male/FacialHair{receta['vello']}.png")
    return files


resultados = {}
for cap in CAPS:
    receta = dict(cap["receta_0based"])
    pre = render(receta, TMP)
    post = render(receta, os.path.join(BASE, "version-linux/assets"))
    Image.fromarray(post).save(os.path.join(OUT, f"{cap['id']}_postfix.png"))
    dif = np.any(pre != post, axis=2)
    # unión de px cambiados en las capas de este combo
    union = np.zeros((1600, 1200), dtype=bool)
    for cf in capas_de_receta(receta):
        if cf in capa_diff:
            union |= capa_diff[cf]
    fuera = dif & ~union
    resultados[cap["id"]] = {
        "px_diferentes": int(dif.sum()),
        "px_fuera_de_capa": int(fuera.sum()),
        "ok": bool(fuera.sum() == 0),
    }
    print(f"{cap['id']}: dif={int(dif.sum())} fuera_de_capa={int(fuera.sum())} ok={fuera.sum() == 0}")
    # zooms 4x post-fix de cada zona circulada
    for m in cap["marcas"]:
        x0, y0, x1, y1 = m["circulo_bbox_canvas"]
        mx, my = 40, 40
        cx0, cy0 = max(0, x0 - mx), max(0, y0 - my)
        cx1, cy1 = min(1200, x1 + mx), min(1600, y1 + my)
        crop = Image.fromarray(post).crop((cx0, cy0, cx1, cy1))
        zoom = crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST)
        d = ImageDraw.Draw(zoom)
        d.rectangle([(x0 - cx0) * 4, (y0 - cy0) * 4, (x1 - cx0) * 4, (y1 - cy0) * 4],
                    outline=(255, 0, 0), width=3)
        zoom.save(os.path.join(OUT, f"{cap['id']}_zona_{m['id']}_postfix.png"))

# --- control C3 sin tinte de ojos
c3 = [c for c in CAPS if c["id"] == "captura3"][0]
rec = dict(c3["receta_0based"])
rec["color_ojos"] = 0
pre = render(rec, TMP)
post = render(rec, os.path.join(BASE, "version-linux/assets"))
dif = np.any(pre != post, axis=2)
union = np.zeros((1600, 1200), dtype=bool)
for cf in capas_de_receta(rec):
    if cf in capa_diff:
        union |= capa_diff[cf]
fuera = dif & ~union
print(f"C3 control sin tinte: dif={int(dif.sum())} fuera_de_capa={int(fuera.sum())}")
resultados["C3_control_sin_tinte"] = {"px_diferentes": int(dif.sum()),
                                      "px_fuera_de_capa": int(fuera.sum()),
                                      "ok": bool(fuera.sum() == 0)}

json.dump(resultados, open(os.path.join(BASE, "diagnostico_usuario/supermetodo/fase4_verificacion.json"), "w"), indent=1)
print("OK — fase4_verificacion.json escrito")
