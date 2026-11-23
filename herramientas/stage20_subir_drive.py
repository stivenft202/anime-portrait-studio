# stage20 — subir a Drive/Unity los archivos que difieren de stage19.
#
# Uso: python3 herramientas/stage20_subir_drive.py
# Lee /tmp/drive_difieren.json (comparación md5 local vs Drive, generada antes)
# más PortraitCreator.cs, y reemplaza cada archivo POR ID con
# `drive files update --upload` (sin tocar ningún .meta).
# Verificación: descarga cada archivo subido y compara md5 con el local.
# El CLI responde con el JSON del archivo, NO con la palabra "success":
# la verificación por md5 es la que manda.
import json, hashlib, os, subprocess, sys

CLI = '/opt/hatch/bin/hatch_gws_cli'
BASE = '/home/hatch/workspace/anime-portrait-studio'

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def cli(args):
    r = subprocess.run([CLI] + args, capture_output=True, text=True, timeout=300)
    return r

def main():
    dif = json.load(open('/tmp/drive_difieren.json'))
    # PortraitCreator.cs (Runtime) se suma aquí.
    dif.append({'sexo': 'Runtime', 'name': 'PortraitCreator.cs',
                'path': os.path.join(BASE, 'diagnostico_usuario/unity/PortraitCreator.cs'),
                'id': '1WJmiDhcw5Jvjp_aFIs9z7jjAjeNV_mTR'})
    print(f'archivos a subir: {len(dif)}', flush=True)
    subidos, fallos = [], []
    for i, f in enumerate(dif, 1):
        path = f['path'] if os.path.isabs(f['path']) else os.path.join(BASE, f['path'])
        r = cli(['drive', 'files', 'update', '--params',
                 json.dumps({'fileId': f['id']}), '--upload', path])
        ok = False
        try:
            j = json.loads(r.stdout)
            ok = j.get('id') == f['id']
        except Exception:
            ok = False
        print(f"[{i}/{len(dif)}] {f['sexo']}/{f['name']}: {'OK' if ok else 'FALLO'}", flush=True)
        if not ok:
            print('   stdout:', r.stdout[:300], 'stderr:', r.stderr[:300], flush=True)
            fallos.append(f)
        else:
            subidos.append(f)
    print(f'subidos: {len(subidos)}, fallos: {len(fallos)}', flush=True)
    # Verificación por md5 descargando de Drive.
    print('verificando por md5...', flush=True)
    mal = []
    for i, f in enumerate(subidos, 1):
        path = f['path'] if os.path.isabs(f['path']) else os.path.join(BASE, f['path'])
        tmp = '/tmp/drive_verif.bin'
        r = cli(['drive', 'files', 'get', '--params',
                 json.dumps({'fileId': f['id'], 'alt': 'media'}), '-o', tmp])
        try:
            dm = md5(tmp)
            lm = md5(path)
            ok = dm == lm
        except Exception as e:
            ok = False
            print('   error md5:', e, flush=True)
        if not ok:
            mal.append(f)
            print(f"[{i}/{len(subidos)}] VERIF MAL {f['sexo']}/{f['name']}", flush=True)
    print(f"verificación: {len(subidos) - len(mal)}/{len(subidos)} OK", flush=True)
    if mal:
        print('MAL:', [f['sexo'] + '/' + f['name'] for f in mal], flush=True)
    if fallos:
        print('FALLOS DE SUBIDA:', [f['sexo'] + '/' + f['name'] for f in fallos], flush=True)
    json.dump({'subidos': len(subidos), 'fallos': [f['name'] for f in fallos],
               'verif_mal': [f['name'] for f in mal]},
              open('/tmp/drive_subida_stage20.json', 'w'))

if __name__ == '__main__':
    main()
