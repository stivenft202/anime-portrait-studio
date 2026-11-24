#!/usr/bin/env python3
"""Sube a Drive/Unity las 5 capas corregidas de la Tanda 21 (por ID),
y verifica cada una re-descargándola y comparando md5.

Uso: python3 herramientas/tanda21_subir_drive.py
"""
import hashlib
import json
import os
import subprocess
import sys

CLI = "/opt/hatch/bin/hatch_gws_cli"
BASE = os.path.expanduser("~/workspace/anime-portrait-studio/version-linux/assets/Female")

# (nombre, drive_file_id, md5_esperado_post_fix)
ARCHIVOS = [
    ("Outfit3.png", "1ZsAJxO_ObvYV2MfupzBFxFK-6UCEfqgB", "0932143ed40c17ef73908d6f29f96c0e"),
    ("Hair8_Front.png", "1iwqTluPQPVBBragcuXoA9K3OlkRzVI-z", "ff52b02679a34d48ed276e0e9f4b46f2"),
    ("Hair9_Front.png", "18fHbn95LVWZji0riI-gKLxIkT6ZKyO7J", "259218e4fb0adf621e0c801ed208e59a"),
    ("Hair2_Front.png", "1MaQ-HhaKUDfbGivdXXXH4k-yMyXkYGTi", "b7db720b11f863b65827b1c2cbd85c05"),
    ("Hair2_Back.png", "1sn05Ljirt82Ho8KnvkRO4UZ1G26hKtHJ", "59d6eb28e23c9cd4a19433d186be8a55"),
]


def md5_de(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ok = 0
    for nombre, file_id, esperado in ARCHIVOS:
        ruta = os.path.join(BASE, nombre)
        local = md5_de(ruta)
        assert local == esperado, f"{nombre}: md5 local {local} != esperado {esperado}"
        print(f"[{nombre}] subiendo...", flush=True)
        r = subprocess.run(
            [CLI, "drive", "files", "update",
             "--params", json.dumps({"fileId": file_id}),
             "--upload", ruta],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ERROR al subir: {r.stderr.strip()[:300]}")
            continue
        # Verificar re-descargando
        tmp = f"/tmp/t21_drive_{nombre}"
        r2 = subprocess.run(
            [CLI, "drive", "files", "get",
             "--params", json.dumps({"fileId": file_id, "alt": "media"}),
             "-o", tmp],
            capture_output=True, text=True)
        if r2.returncode != 0:
            print(f"  ERROR al verificar: {r2.stderr.strip()[:300]}")
            continue
        remoto = md5_de(tmp)
        os.remove(tmp)
        if remoto == esperado:
            print(f"  OK verificado md5 {remoto}")
            ok += 1
        else:
            print(f"  MISMATCH: Drive tiene {remoto}, esperado {esperado}")
    print(f"\n{ok}/{len(ARCHIVOS)} verificados.")
    sys.exit(0 if ok == len(ARCHIVOS) else 1)


if __name__ == "__main__":
    main()
