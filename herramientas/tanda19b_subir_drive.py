# tanda19b_subir_drive.py — subir a Drive/Unity los 10 archivos de
# Tanda 19 (lunares boca/nariz) + Tanda 19b (causa raíz: boca fantasma en Base).
# Las 2 Base ya incluyen los cambios de T19 y de 19b.
# Reemplaza cada archivo POR ID con `drive files update --upload`
# (sin tocar ningún .meta). Verificación: descarga cada archivo subido
# y compara md5 con el local. IDs localizados por nombre en
# Textures/Female y Textures/Male (2026-11-23).
import hashlib, json, os, subprocess, sys

CLI = '/opt/hatch/bin/hatch_gws_cli'
BASE = '/home/hatch/workspace/anime-portrait-studio'

ARCHIVOS = [
    {'sexo': 'Female', 'name': 'Base.png',
     'path': 'version-linux/assets/Female/Base.png',
     'id': '1KR4gg1cJWMMfER8TdsuGWKEOCJAIQvIb',
     'md5': 'f5ba606a35fe5bfcf8a60c40d3086412'},
    {'sexo': 'Male', 'name': 'Base.png',
     'path': 'version-linux/assets/Male/Base.png',
     'id': '1jEs5dab8xQUr3TChHescM8iurFqCenPX',
     'md5': '2368d4e27918ecf748149de8a750407b'},
    {'sexo': 'Female', 'name': 'Nose1.png',
     'path': 'version-linux/assets/Female/Nose1.png',
     'id': '1eNukI8DmjlL3eio_95p7cbYyuwJvJu9v',
     'md5': '50e985f5c3b193b518defa0b98f4f5c5'},
    {'sexo': 'Female', 'name': 'Nose2.png',
     'path': 'version-linux/assets/Female/Nose2.png',
     'id': '1-Ep4dK97xGJXVWRt3a9GtZFuRLmonS7R',
     'md5': '6e2162e1095a02074d1aafba4e9d7ec8'},
    {'sexo': 'Female', 'name': 'Nose3.png',
     'path': 'version-linux/assets/Female/Nose3.png',
     'id': '1qgOxDqVhDG-pqcuZsJjuwTfbIgkvtbns',
     'md5': '891a045a28bce5d8cd823289bab2214b'},
    {'sexo': 'Male', 'name': 'Nose1.png',
     'path': 'version-linux/assets/Male/Nose1.png',
     'id': '18COWZB_vgU69LcFcKN37Gfh0PfkH6cDu',
     'md5': '7d63cb47f5663e0d97a7396460de0eb8'},
    {'sexo': 'Male', 'name': 'Nose2.png',
     'path': 'version-linux/assets/Male/Nose2.png',
     'id': '1hhRxF27-R9pItizh6xitdJkfgq9xuQG_',
     'md5': '7819688bbb3bcc7f02d2e6648d9b3709'},
    {'sexo': 'Female', 'name': 'Mouth_Happy.png',
     'path': 'version-linux/assets/Female/Mouth_Happy.png',
     'id': '1wHIKsjTx8fFUqT4K_Xz2iM01CBliMVe0',
     'md5': '60787d75e18d1e43509b6fd44a6bd04a'},
    {'sexo': 'Male', 'name': 'Mouth_Happy.png',
     'path': 'version-linux/assets/Male/Mouth_Happy.png',
     'id': '192Boa3_mbawvaecgRoHKDGrweDfuWUY-',
     'md5': '95f1cfcbf010104e3a20f222f4812758'},
    {'sexo': 'Male', 'name': 'Mouth_Neutral.png',
     'path': 'version-linux/assets/Male/Mouth_Neutral.png',
     'id': '1br3SdZ-QZ3GlMt-HpY4ykbmvf16rtnD8',
     'md5': 'a9b417a071bdc07ea26b3bb330e2ab5a'},
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
    for f in ARCHIVOS:
        lm = md5(os.path.join(BASE, f['path']))
        assert lm == f['md5'], f"md5 local inesperado en {f['sexo']}/{f['name']}: {lm}"
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
    print('verificando por md5...', flush=True)
    mal = []
    for i, f in enumerate(subidos, 1):
        tmp = '/tmp/drive_verif_t19b.bin'
        cli(['drive', 'files', 'get', '--params',
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
        print('FALLOS:', [f['sexo'] + '/' + f['name'] for f in fallos + mal], flush=True)
        sys.exit(1)
    print('OK — Drive/Unity = T19 + T19b (10 archivos)', flush=True)

if __name__ == '__main__':
    main()
