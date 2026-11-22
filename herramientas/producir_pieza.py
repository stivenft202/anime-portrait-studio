#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PUERTA DE PRODUCCION DE PIEZAS — Anime Half Portrait Studio (Fase 5)

Implementa los 6 controles del ESTANDAR_PRODUCCION.md (fase5/). Ninguna
pieza nueva entra al paquete sin pasar esta puerta. Si un control falla,
la pieza se REGENERA: esta prohibido remendarla a mano.

Uso:
    python3 producir_pieza.py trabajo.json

El JSON de trabajo describe la pieza candidata y su contexto:
{
  "nombre": "Female Hair5 Front",
  "dibujo": "ruta/al/dibujo_terminado.png",        // RGB 1200x1600
  "fondo_dibujo": [204, 223, 233],                  // color de fondo del dibujo
  "capas_conocidas": [                              // pila SIN la pieza, atras->adelante
    {"ruta": ".../Hair5_Back.png", "tinte": [1,1,1]},
    {"ruta": ".../Base.png",       "tinte": [1,1,1]},
    ...
  ],
  "pieza": {"ruta": ".../Hair5_Front.png", "tinte": [1,1,1],
            "posicion": 4},                          // indice en la pila completa
  "tipo": "pelo_frente"   // pelo_frente|pelo_trasero|ojos|nariz|boca|ropa|accesorio
}

Controles (umbral duro entre parentesis):
  1. Delta: fuera de la zona de la pieza, el dibujo y el compuesto de las
     capas conocidas difieren en 0 px (|dif|>25).
  2. Acida: al recomponer CON la pieza, el compuesto reproduce el dibujo
     con < 0,5 % de pixeles distintos (|dif|>25).
  3. Fantasmas: grupos >=40 px de contenido en el compuesto donde el
     dibujo tiene fondo = 0.
  4. Borde claro (rim): pixeles de la pieza claros y calidos (lum>115,
     R-B>12) sobre zonas del dibujo que NO son su material = 0.
  5. Alfa solido: dentro de la silueta rellena de la pieza, los pixeles
     con alfa<235 (vetas que dejan brillar la capa de abajo) < 1 %.
  6. Zona: pixeles de la pieza fuera de la caja de su tipo = 0.

Salida: una linea por control (PASS/FAIL con su cifra) y el veredicto.
Codigo de salida 0 = PASS total, 1 = FAIL.
"""
import json, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

SLATE = np.array([40., 44., 52.])

# Cajas por tipo de pieza (lienzo 1200x1600), segun el estandar.
CAJAS = {
    "pelo_frente":  (0, 0, 1200, 1600),
    "pelo_trasero": (0, 0, 1200, 1600),
    "ojos":         (240, 410, 660, 720),
    "nariz":        (195, 580, 420, 780),
    "boca":         (280, 680, 480, 880),
    "ropa":         (0, 760, 1200, 1600),
    "accesorio":    (0, 0, 1200, 1600),
}


def cargar_rgba(ruta):
    return np.asarray(Image.open(ruta).convert("RGBA")).astype(float)


def cargar_rgb(ruta):
    return np.asarray(Image.open(ruta).convert("RGB")).astype(float)


def aplicar_tinte(capa, tinte):
    capa = capa.copy()
    for ch in range(3):
        capa[..., ch] *= tinte[ch]
    return capa


def componer(capas, fondo=(204., 223., 233.)):
    """Compone la pila sobre el fondo DEL DIBUJO (no sobre pizarra):
    asi el fondo del compuesto y el del dibujo coinciden y las
    diferencias medidas son solo del personaje."""
    c = np.zeros((1600, 1200, 3))
    c[..., 0], c[..., 1], c[..., 2] = fondo
    for lay in capas:
        a = lay[..., 3:4] / 255.0
        c = lay[..., :3] * a + c * (1 - a)
    return c


def mascara_material_dibujo(dib, tipo, fondo):
    """Donde el dibujo tiene el material de la pieza (aprox. de verificacion)."""
    dist_fondo = np.abs(dib - np.array(fondo)).max(axis=2)
    personaje = dist_fondo > 25
    lum = dib.mean(axis=2)
    if tipo in ("pelo_frente", "pelo_trasero"):
        piel = (dib[..., 0] - dib[..., 2] > 25) & (lum > 80)
        return personaje & (lum < 130) & ~piel
    if tipo == "ropa":
        m = personaje.copy()
        m[:760] = False
        piel = (dib[..., 0] > 170) & ((dib[..., 0] - dib[..., 2]) > 18) & (lum > 140)
        pelo = (lum < 110) & ~((dib[..., 0] - dib[..., 2] > 25) & (lum > 80))
        return m & ~piel & ~pelo
    # ojos/nariz/boca/accesorio: la caja manda; material = personaje en la caja
    x0, y0, x1, y1 = CAJAS[tipo]
    m = np.zeros((1600, 1200), bool)
    m[y0:y1, x0:x1] = personaje[y0:y1, x0:x1]
    return m


def verificar(trabajo):
    dib = cargar_rgb(trabajo["dibujo"])
    fondo = trabajo.get("fondo_dibujo", [204, 223, 233])
    tipo = trabajo["tipo"]
    conocidas = [aplicar_tinte(cargar_rgba(c["ruta"]), c.get("tinte", [1, 1, 1]))
                 for c in trabajo["capas_conocidas"]]
    pieza = aplicar_tinte(cargar_rgba(trabajo["pieza"]["ruta"]),
                          trabajo["pieza"].get("tinte", [1, 1, 1]))
    pos = trabajo["pieza"].get("posicion", len(conocidas))

    fondo_arr = tuple(float(v) for v in fondo)
    sin_pieza = componer(conocidas, fondo_arr)
    pila = conocidas[:pos] + [pieza] + conocidas[pos:]
    con_pieza = componer(pila, fondo_arr)

    dif = np.abs(dib - sin_pieza).max(axis=2)
    dif_acida = np.abs(dib - con_pieza).max(axis=2)
    material = mascara_material_dibujo(dib, tipo, fondo)
    zona_pieza = ndimage.binary_dilation(material, iterations=3) | (pieza[..., 3] > 40)

    resultados = []

    # Control 1 — Delta fuera de la zona
    fuera = ~zona_pieza
    n1 = int((fuera & (dif > 25)).sum())
    resultados.append(("1 Delta fuera de la zona", n1, n1 == 0, f"{n1} px"))

    # Control 2 — Prueba acida
    pct2 = 100.0 * float((dif_acida > 25).mean())
    resultados.append(("2 Acida (recomposicion)", pct2, pct2 < 0.5, f"{pct2:.2f} %"))

    # Control 3 — Grupos fantasma sobre el fondo del dibujo
    dist_fondo = np.abs(dib - np.array(fondo)).max(axis=2)
    fantasma = (np.abs(con_pieza - np.array(fondo)).max(axis=2) > 25) & (dist_fondo <= 25)
    lab, cnt = ndimage.label(fantasma)
    grandes = 0
    if cnt:
        tamanos = ndimage.sum_labels(fantasma, lab, index=np.arange(1, cnt + 1))
        grandes = int((tamanos >= 40).sum())
    resultados.append(("3 Grupos fantasma >=40 px", grandes, grandes == 0, f"{grandes} grupos"))

    # Control 4 — Borde claro (rim) sobre material ajeno
    lum_p = pieza[..., :3].mean(axis=2)
    rim = (pieza[..., 3] > 40) & (lum_p > 115) & ((pieza[..., 0] - pieza[..., 2]) > 12)
    ajeno = rim & ~ndimage.binary_dilation(material, iterations=1)
    n4 = int(ajeno.sum())
    resultados.append(("4 Borde claro sobre material ajeno", n4, n4 == 0, f"{n4} px"))

    # Control 5 — Alfa solido dentro de la silueta
    sil = ndimage.binary_fill_holes(ndimage.binary_closing(pieza[..., 3] >= 60, iterations=2))
    if sil.any():
        vetas = sil & (pieza[..., 3] < 235)
        pct5 = 100.0 * float(vetas.sum()) / float(sil.sum())
    else:
        pct5 = 100.0
    resultados.append(("5 Alfa solido en la silueta", pct5, pct5 < 1.0, f"{pct5:.2f} % de vetas"))

    # Control 6 — Contenido fuera de la caja del tipo
    x0, y0, x1, y1 = CAJAS[tipo]
    caja = np.zeros((1600, 1200), bool)
    caja[y0:y1, x0:x1] = True
    n6 = int(((pieza[..., 3] > 40) & ~caja).sum())
    resultados.append(("6 Contenido fuera de su caja", n6, n6 == 0, f"{n6} px"))

    print(f"== PUERTA DE PIEZA: {trabajo.get('nombre', trabajo['pieza']['ruta'])} ==")
    todo_ok = True
    for nombre, _valor, ok, detalle in resultados:
        todo_ok = todo_ok and ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {nombre}: {detalle}")
    print(f"== VEREDICTO: {'PASS' if todo_ok else 'FAIL — la pieza se regenera, no se remienda'} ==")
    return todo_ok


if __name__ == "__main__":
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        trabajo = json.load(f)
    sys.exit(0 if verificar(trabajo) else 1)
