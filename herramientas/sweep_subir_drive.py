# sweep — subir a Drive/Unity los 6 archivos arreglados del barrido (tandas 0 y 17).
#
# Uso: python3 herramientas/sweep_subir_drive.py
# Reemplaza cada archivo POR ID con `drive files update --upload`
# (sin tocar ningún .meta). Verificación: descarga cada archivo subido
# y compara md5 con el local. El CLI responde con el JSON del archivo,
# NO con la palabra "success": la verificación por md5 es la que manda.
#
# Archivos (orden de Stiven 2026-11-23 ~07:54, «Sí, súbelo a GitHub y Drive»):
#   Tanda 0:  Female/Hair6_Front.png, Male/Hair2_Front.png, Male/FacialHair3.png
#   Tanda 17: Female/Base.png, Female/Outfit1.png, Female/Outfit2.png
#             (Outfit1/2 incluyen T17-01 + T17-02)
# IDs localizados listando Textures/Female y Textures/Male por CLI
# (el /tmp/drive_difieren.json del stage20 se perdió en un reinicio de VM).
import hashlib, json, os, subprocess, sys

CLI = '/opt/hatch/bin/hatch_gws_cli'
BASE = '/home/hatch/workspace/anime-portrait-studio'

ARCHIVOS = [
    {'sexo': 'Female', 'name': 'Hair6_Front.png',
     'path': 'version-linux/assets/Female/Hair6_Front.png',
     'id': '1VfVcZxNVbBpXQTONefX_57d9iLq6_L2Q',
     'md5': '2153d1d65f5aaae6c67bd1b1b0efb204'},
    {'sexo': 'Male', 'name': 'Hair2_Front.png',
     'path': 'version-linux/assets/Male/Hair2_Front.png',
     'id': '1QYHLXMnuJLiU0hH2qqKEVjLENbCh8Wf7',
     'md5': 'c518da879413be1820d2e8d21e4f6c9e'},
    {'sexo': 'Male', 'name': 'FacialHair3.png',
     'path': 'version-linux/assets/Male/FacialHair3.png',
     'id': '1WWbSlT6EY094yTYZOvoFyfd0y3nK6WLf',
     'md5': '9e240bf28ba363ae55e6b90525129588'},
    {'sexo': 'Female', 'name': 'Base.png',
     'path': 'version-linux/assets/Female/Base.png',
     'id': '1KR4gg1cJWMMfER8TdsuGWKEOCJAIQvIb',
     'md5': '318969ab26ff31bf1047925a4ba84690'},
    {'sexo': 'Female', 'name': 'Outfit1.png',
     'path': 'version-linux/assets/Female/Outfit1.png',
     'id': '1ZW5NxWUcUCAfRcY16zajNpyvSa7c-J-8',
     'md5': '3024315b62e20d061b3ead506f5b4bad'},
    {'sexo': 'Female', 'name': 'Outfit2.png',
     'path': 'version-linux/assets/Female/Outfit2.png',
     'id': '1dTjwFnMzpnH6k_Hf5B_b-JTNizA4z5C-',
     'md5': '3bd789cad4e1b32aceffa5f22ff5f7b2'},
]

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def cli(args):
    return subprocess.run([CLI] + args, capture_output=True, text=True, timeout=300)

def main():
    print(f'archivos a subir: {len(ARCHIVOS)}', flush=True)
    # 1. Comprobar md5 locales antes de subir.
    for f in ARCHIVOS:
        lm = md5(os.path.join(BASE, f['path']))
        assert lm == f['md5'], f"md5 local inesperado en {f['name']}: {lm}"
    print('md5 locales OK', flush=True)
    subidos, fallos = [], []
    for i, f in enumerate(ARCHIVOS, 1):
        r = cli(['drive', 'files', 'update', '--params',
                 json.dumps({'fileId': f['id']}), '--upload',
                 os.path.join(BASE, f['path'])])
        ok = False
        try:
            ok = json.loads(r.stdout).get('id') == f['id']
        except Exception:
            ok = False
        print(f"[{i}/{len(ARCHIVOS)}] {f['sexo']}/{f['name']}: {'OK' if ok else 'FALLO'}", flush=True)
        if not ok:
            print('   stdout:', r.stdout[:300], 'stderr:', r.stderr[:300], flush=True)
            fallos.append(f)
        else:
            subidos.append(f)
    print(f'subidos: {len(subidos)}, fallos: {len(fallos)}', flush=True)
    # 2. Verificación por md5 descargando de Drive.
    print('verificando por md5...', flush=True)
    mal = []
    for i, f in enumerate(subidos, 1):
        tmp = '/tmp/drive_verif_sweep.bin'
        r = cli(['drive', 'files', 'get', '--params',
                 json.dumps({'fileId': f['id'], 'alt': 'media'}), '-o', tmp])
        try:
            dm = md5(tmp)
        except Exception:
            dm = 'ERROR DESCARGA'
        ok = dm == f['md5']
        print(f"[{i}/{len(subidos)}] {f['sexo']}/{f['name']}: md5 Drive={dm} {'OK' if ok else 'MAL'}", flush=True)
        if not ok:
            mal.append(f)
    print(f"verificación: {len(subidos) - len(mal)}/{len(subidos)} OK", flush=True)
    if fallos or mal:
        print('FALLOS:', [f['name'] for f in fallos + mal], flush=True)
        sys.exit(1)
    print('OK — Drive/Unity = barrido completo (6 archivos)', flush=True)

if __name__ == '__main__':
    main()
