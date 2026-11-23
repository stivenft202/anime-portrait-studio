# boca_perfil_render_una.py — Renderiza UNA variante de boca Sorprendido en
# el navegador (Playwright MCP), en la copia de prueba (puerto 8766).
# Uso: python3 boca_perfil_render_una.py <VARIANTE>   (A050, A062, A075, B, C1, C2)
# 1) copia las capas Female_<VAR>_layer.png / Male_<VAR>_layer.png a la
#    copia de prueba (NO toca el programa real),
# 2) abre el creador en el navegador, renderiza mujer (F H1 O1 E1 N1 M5) y
#    hombre (M H1 O1 E1 N1 M3) y guarda el lienzo,
# 3) genera el recorte 4x de la zona de la boca.
import base64, json, os, shutil, subprocess, sys, time
from PIL import Image

VAR = sys.argv[1]
BASE = '/home/hatch/workspace/anime-portrait-studio'
PERFIL = f'{BASE}/diagnostico_usuario/boca_sorprendido/perfil'
COPIA = f'{BASE}/diagnostico_usuario/boca_sorprendido/prueba_navegador/version-linux-t'
MCP_DIR = '/home/hatch/workspace/playwright-mcp'
ZONA = {'F': (340, 730, 470, 830), 'M': (290, 720, 420, 820)}

# 1) capas de la variante -> copia de prueba (cp --remove-destination)
for sexo in ('Female', 'Male'):
    src = f'{PERFIL}/{sexo}_{VAR}_layer.png'
    dst = f'{COPIA}/assets/{sexo}/Mouth_Surprised.png'
    if os.path.islink(dst):
        os.remove(dst)
    shutil.copyfile(src, dst)
print(f'[{VAR}] capas copiadas a la copia de prueba', flush=True)

# 2) cliente MCP (mismo patrón que boca_sorprendido_prueba_navegador.py)
def send(proc, obj):
    proc.stdin.write(json.dumps(obj) + '\n'); proc.stdin.flush()

def read_msg(proc, timeout=180):
    import select
    end = time.time() + timeout
    while True:
        left = end - time.time()
        if left <= 0: raise TimeoutError('sin respuesta del servidor MCP')
        r, _, _ = select.select([proc.stdout.fileno()], [], [], left)
        if not r: raise TimeoutError('sin respuesta del servidor MCP')
        line = proc.stdout.readline()
        if not line: raise RuntimeError('el servidor MCP cerró stdout')
        msg = json.loads(line)
        if 'id' in msg: return msg

def call(proc, mid, name, args):
    send(proc, {'jsonrpc': '2.0', 'id': mid, 'method': 'tools/call',
                'params': {'name': name, 'arguments': args}})
    return read_msg(proc)

def eval_value(proc, mid, fn):
    r = call(proc, mid, 'browser_evaluate', {'function': fn})
    txt = ''
    for c in r.get('result', {}).get('content', []):
        if c.get('type') == 'text': txt = c.get('text', '')
    if '### Result\n' not in txt:
        raise RuntimeError('resultado sin "### Result": ' + txt[:300])
    val = txt.split('### Result\n', 1)[1]
    if '\n### Ran Playwright code' in val:
        val = val.split('\n### Ran Playwright code', 1)[0]
    val = val.strip()
    if val.startswith('"'):
        if val.endswith('"'): val = val[1:-1]
        val = val.replace('\n', '').replace('\r', '')
    return val

def eval_bool(proc, mid, fn):
    return eval_value(proc, mid, fn).strip() == 'true'

def save_png(data_url, path):
    assert data_url.startswith('data:image/png;base64,'), data_url[:60]
    raw = base64.b64decode(data_url.split(',', 1)[1])
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', 'no es PNG válido'
    with open(path, 'wb') as f: f.write(raw)
    return len(raw)

def js_combo(sexo, pelo, ropa, ojos, nariz, boca, vello, hc, st, oc, ec):
    return ("() => { R.sexo='" + sexo + "'; R.pelo=" + str(pelo) +
            "; R.ropa=" + str(ropa) + "; R.ojos=" + str(ojos) +
            "; R.nariz=" + str(nariz) + "; R.boca=" + str(boca) +
            "; R.vello=" + str(vello) + "; R.color_pelo=" + str(hc) +
            "; R.piel=" + str(st) + "; R.color_ropa=" + str(oc) +
            "; R.color_ojos=" + str(ec) + "; dibujar();"
            " return codigo() + '|' + document.getElementById('lienzo').toDataURL('image/png'); }")

COMBOS = [
    ('F', 'Female', 0, 0, 0, 0, 4, 0, 0, 0, 0, 0),
    ('M', 'Male', 0, 0, 0, 0, 2, 0, 0, 0, 0, 0),
]

env = dict(os.environ); env.pop('PLAYWRIGHT_BROWSERS_PATH', None)
proc = subprocess.Popen(
    ['node', 'node_modules/@playwright/mcp/cli.js', '--headless',
     '--no-sandbox', '--caps', 'vision', '--browser', 'chromium'],
    cwd=MCP_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
mid = [10]
try:
    send(proc, {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
                           'clientInfo': {'name': 'dani-perfil', 'version': '1.0'}}})
    r = read_msg(proc)
    print(f'[{VAR}] initialize:', r.get('result', {}).get('serverInfo'), flush=True)
    send(proc, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    mid[0] += 1
    call(proc, 2, 'browser_navigate', {'url': 'http://127.0.0.1:8766/'})
    cargado = False
    for i in range(30):
        mid[0] += 1
        if eval_bool(proc, mid[0], "() => document.getElementById('estado').textContent === '' && Object.keys(imgs).length === 67"):
            print(f'[{VAR}] capas cargadas tras {i + 1}s', flush=True); cargado = True; break
        time.sleep(1)
    if not cargado: raise RuntimeError('las 67 capas no cargaron en 30s')
    for letra, *args in COMBOS:
        mid[0] += 1
        val = eval_value(proc, mid[0], js_combo(*args))
        cod_pagina, data_url = val.split('|data:image/png', 1)
        data_url = 'data:image/png' + data_url
        ruta = os.path.join(PERFIL, f'render_{VAR}_{letra}.png')
        n = save_png(data_url, ruta)
        print(f'[{VAR}] {letra}: {cod_pagina.strip()} -> {n} bytes', flush=True)
        # 3) recorte 4x de la zona de la boca
        im = Image.open(ruta).convert('RGB')
        x0, y0, x1, y1 = ZONA[letra]
        z = im.crop((x0, y0, x1, y1))
        z = z.resize((z.width * 4, z.height * 4), Image.LANCZOS)
        z.save(os.path.join(PERFIL, f'render_{VAR}_{letra}_zoom_boca.png'))
    print(f'[{VAR}] RENDER OK', flush=True)
finally:
    proc.terminate()
    try: proc.wait(timeout=10)
    except Exception: proc.kill()
