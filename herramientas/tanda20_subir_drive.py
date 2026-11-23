# tanda20_subir_drive.py — subir a Drive/Unity los 34 archivos del
# Súper método + Ribete + Tanda 20 (24 capas + 10 variantes Gray).
# Reemplaza cada archivo POR ID con `drive files update --upload`
# (sin tocar ningún .meta). Verificación: descarga cada archivo subido
# y compara md5 con el local. IDs localizados por nombre en
# Textures/Female y Textures/Male (2026-11-23).
import hashlib, json, os, subprocess, sys

CLI = '/opt/hatch/bin/hatch_gws_cli'
BASE = '/home/hatch/workspace/anime-portrait-studio'

ARCHIVOS = [
    # --- Capas Female (14) ---
    {'sexo': 'Female', 'name': 'Base.png',
     'path': 'version-linux/assets/Female/Base.png',
     'id': '1KR4gg1cJWMMfER8TdsuGWKEOCJAIQvIb',
     'md5': '78f8d9a0e87b4bb68ef4417f9ec0ebcb'},
    {'sexo': 'Female', 'name': 'Hair11_Front.png',
     'path': 'version-linux/assets/Female/Hair11_Front.png',
     'id': '1eQ8ha-o578P_NJpDn4AYI9rZfro5eSXJ',
     'md5': '8bc2fade7b576168a051ebf7192f7669'},
    {'sexo': 'Female', 'name': 'Hair1_Front.png',
     'path': 'version-linux/assets/Female/Hair1_Front.png',
     'id': '1PMqY1DOKVPv5H8yMMdmTAAEXH0WnR-yK',
     'md5': '2da21562a1df3a2d6888ecf45b218633'},
    {'sexo': 'Female', 'name': 'Hair2_Back.png',
     'path': 'version-linux/assets/Female/Hair2_Back.png',
     'id': '1sn05Ljirt82Ho8KnvkRO4UZ1G26hKtHJ',
     'md5': '42bc51fbca5be11509f3be1ac561ec3b'},
    {'sexo': 'Female', 'name': 'Hair2_Front.png',
     'path': 'version-linux/assets/Female/Hair2_Front.png',
     'id': '1MaQ-HhaKUDfbGivdXXXH4k-yMyXkYGTi',
     'md5': '18e57825100b75e1b36cf67fdd21ce61'},
    {'sexo': 'Female', 'name': 'Hair3_Back.png',
     'path': 'version-linux/assets/Female/Hair3_Back.png',
     'id': '1YhmhU-CyoIBUNxV3houhviOsSndozrMn',
     'md5': '2e95012a472c88b7bcdcc6e739d81dde'},
    {'sexo': 'Female', 'name': 'Hair3_Front.png',
     'path': 'version-linux/assets/Female/Hair3_Front.png',
     'id': '1_rOWvD9p5-A8Ww2_Nw9x3tiCAZ7Z_O7E',
     'md5': '0aacb21b0b2ebe6826d12f9a2676f099'},
    {'sexo': 'Female', 'name': 'Hair4_Back.png',
     'path': 'version-linux/assets/Female/Hair4_Back.png',
     'id': '1reStXkLj3W5IGOo_-RlMmCkJErJpAr1w',
     'md5': 'b47eb14a3f2807adf9d15dbf08a6a9cd'},
    {'sexo': 'Female', 'name': 'Hair4_Front.png',
     'path': 'version-linux/assets/Female/Hair4_Front.png',
     'id': '1qF3AcetEtclB72Efc40wfAD37YD-U0aE',
     'md5': 'eb749e9f2c3288a8dba82d9b380774de'},
    {'sexo': 'Female', 'name': 'Nose1.png',
     'path': 'version-linux/assets/Female/Nose1.png',
     'id': '1eNukI8DmjlL3eio_95p7cbYyuwJvJu9v',
     'md5': '724277074a6e88e8dc781912e817e864'},
    {'sexo': 'Female', 'name': 'Nose3.png',
     'path': 'version-linux/assets/Female/Nose3.png',
     'id': '1qgOxDqVhDG-pqcuZsJjuwTfbIgkvtbns',
     'md5': 'e7801bb5d5edd78da80483f3f530e926'},
    {'sexo': 'Female', 'name': 'Outfit1.png',
     'path': 'version-linux/assets/Female/Outfit1.png',
     'id': '1ZW5NxWUcUCAfRcY16zajNpyvSa7c-J-8',
     'md5': '8f0747a1338811d55f45cd60e6c371cb'},
    {'sexo': 'Female', 'name': 'Outfit2.png',
     'path': 'version-linux/assets/Female/Outfit2.png',
     'id': '1dTjwFnMzpnH6k_Hf5B_b-JTNizA4z5C-',
     'md5': 'c79f0c0fbe57d8258bd06c77b02341b4'},
    {'sexo': 'Female', 'name': 'Outfit3.png',
     'path': 'version-linux/assets/Female/Outfit3.png',
     'id': '1ZsAJxO_ObvYV2MfupzBFxFK-6UCEfqgB',
     'md5': '2d2620ad3d5c998cf7d4e6edc48e0381'},
    # --- Variantes Gray Female (5) ---
    {'sexo': 'Female', 'name': 'EyesColor_Neutral_Gray.png',
     'path': 'unity/EyesColor/Female/EyesColor_Neutral_Gray.png',
     'id': '1qTpow1HhxPWcI-3StyjZMJq5bZ61xE8_',
     'md5': '1c9a367c3f332c6de953ba7e3d5122a9'},
    {'sexo': 'Female', 'name': 'EyesColor_Happy_Gray.png',
     'path': 'unity/EyesColor/Female/EyesColor_Happy_Gray.png',
     'id': '13Mjh5_U0q2KLfBALnzkcCIYUc70CFd-I',
     'md5': 'a42ba09c3b48a2e40882990a6e2738dd'},
    {'sexo': 'Female', 'name': 'EyesColor_Sad_Gray.png',
     'path': 'unity/EyesColor/Female/EyesColor_Sad_Gray.png',
     'id': '1Jlj6bYmyMUefvB0rKvNOGKg-eP-RX9B7',
     'md5': '2d899ad45883ea783b26f89f70b971cf'},
    {'sexo': 'Female', 'name': 'EyesColor_Angry_Gray.png',
     'path': 'unity/EyesColor/Female/EyesColor_Angry_Gray.png',
     'id': '1xEo1-yZ92nlTaLTvsL47u1lpBB0WhYpZ',
     'md5': '03854a1271fdc4428e73f96bac59a9a3'},
    {'sexo': 'Female', 'name': 'EyesColor_Surprised_Gray.png',
     'path': 'unity/EyesColor/Female/EyesColor_Surprised_Gray.png',
     'id': '1a_ShyV3QcIUYzJWSLdHLMoq5NkVVXtPo',
     'md5': '44685a8ac1a654454809766871d84396'},
    # --- Capas Male (10) ---
    {'sexo': 'Male', 'name': 'Base.png',
     'path': 'version-linux/assets/Male/Base.png',
     'id': '1jEs5dab8xQUr3TChHescM8iurFqCenPX',
     'md5': '57cad4941e958ace3fe4a35954e9a2e8'},
    {'sexo': 'Male', 'name': 'Eyes_Surprised.png',
     'path': 'version-linux/assets/Male/Eyes_Surprised.png',
     'id': '18gZr1sG0NfgGRcn9ovXECIf7KUnziYh8',
     'md5': 'b0f9893edd55b8427fd3709bef087506'},
    {'sexo': 'Male', 'name': 'Hair1_Front.png',
     'path': 'version-linux/assets/Male/Hair1_Front.png',
     'id': '1-FZHI1LdusUMOE4eGMCWOQZe1N4jXvBx',
     'md5': '37b2a0246237e8d7af69112baee8c239'},
    {'sexo': 'Male', 'name': 'Hair2_Front.png',
     'path': 'version-linux/assets/Male/Hair2_Front.png',
     'id': '1QYHLXMnuJLiU0hH2qqKEVjLENbCh8Wf7',
     'md5': '7926d0274f56d0de678eae1ed90419ce'},
    {'sexo': 'Male', 'name': 'Hair3_Front.png',
     'path': 'version-linux/assets/Male/Hair3_Front.png',
     'id': '1_QXmu3cAV54HzD-eu6kpkN13aFKMb6kd',
     'md5': 'de7f75d87284ddb98aa0e566bccf73e2'},
    {'sexo': 'Male', 'name': 'Hair4_Front.png',
     'path': 'version-linux/assets/Male/Hair4_Front.png',
     'id': '1Ma3iaS6DbRGpSg5hqjRpA4sQcr3kihfJ',
     'md5': '00bd98cddde1475f54ab4ad0f1784a74'},
    {'sexo': 'Male', 'name': 'Nose1.png',
     'path': 'version-linux/assets/Male/Nose1.png',
     'id': '18COWZB_vgU69LcFcKN37Gfh0PfkH6cDu',
     'md5': 'd5e616e25f015e217db8dc97605e6363'},
    {'sexo': 'Male', 'name': 'Outfit1.png',
     'path': 'version-linux/assets/Male/Outfit1.png',
     'id': '1mZ0q4Xzuwz9M7UnAzMmcT_t5a-d9l80a',
     'md5': 'bd46d1829acc61e07b4672925ded8c88'},
    {'sexo': 'Male', 'name': 'Outfit2.png',
     'path': 'version-linux/assets/Male/Outfit2.png',
     'id': '1EJtyh0xfgNdnb9UnEHeon7GCLwdmVVO6',
     'md5': 'b13cdbbe0353e7c69cb82d07369ebc79'},
    {'sexo': 'Male', 'name': 'Outfit3.png',
     'path': 'version-linux/assets/Male/Outfit3.png',
     'id': '1uA2KpjZOFHsIsOa8kR-dv3Rsikuuo8Nq',
     'md5': '968a3e6bb30d4135a16c4f3e4f59450b'},
    # --- Variantes Gray Male (5) ---
    {'sexo': 'Male', 'name': 'EyesColor_Neutral_Gray.png',
     'path': 'unity/EyesColor/Male/EyesColor_Neutral_Gray.png',
     'id': '1xvsfapH5zilx1nPL0HARMAebcY1QKJd7',
     'md5': '44f32cc8eb217a58c4aea7c847d43c24'},
    {'sexo': 'Male', 'name': 'EyesColor_Happy_Gray.png',
     'path': 'unity/EyesColor/Male/EyesColor_Happy_Gray.png',
     'id': '171Li_yXC_dfoDDeC5pjSYFAXUMvU6TLr',
     'md5': '871a1a2d7c38610faa84f0206df70d9b'},
    {'sexo': 'Male', 'name': 'EyesColor_Sad_Gray.png',
     'path': 'unity/EyesColor/Male/EyesColor_Sad_Gray.png',
     'id': '1rfO2WmiYc3tlxSiAM4-qMo8cwc8n4bDd',
     'md5': '981e5b5a07655150cfc3cbda04e58505'},
    {'sexo': 'Male', 'name': 'EyesColor_Angry_Gray.png',
     'path': 'unity/EyesColor/Male/EyesColor_Angry_Gray.png',
     'id': '1lBBoyx4EaijrH1D5BFvUvkJg8Ote8F0l',
     'md5': 'ef6b638452995979cefddefacf498a04'},
    {'sexo': 'Male', 'name': 'EyesColor_Surprised_Gray.png',
     'path': 'unity/EyesColor/Male/EyesColor_Surprised_Gray.png',
     'id': '1MDmr8oA9M2ZBCFAtP4iZvPfX7vUIh0OJ',
     'md5': '44800a4ab6ede637cd0e83bdbb919a82'},
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
        tmp = '/tmp/drive_verif_t20.bin'
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
    print('OK — Drive/Unity = Súper método + Ribete + Tanda 20 (34 archivos)', flush=True)

if __name__ == '__main__':
    main()
