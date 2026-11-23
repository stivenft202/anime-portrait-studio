# boca_sorprendido_prueba_navegador.py — Probar la boca calcada (T) DENTRO
# del programa, en el navegador (Playwright MCP), SIN tocar el programa real:
# se usa una COPIA temporal en diagnostico_usuario/boca_sorprendido/
# prueba_navegador/version-linux-t (servida en el puerto 8766) con las
# capas Mouth_Surprised reemplazadas por la calcada.
# Renderiza 2 combos (mujer y hombre, boca Sorprendido) y guarda el lienzo.
import base64, json, os, subprocess, sys, time

MCP_DIR = '/home/hatch/workspace/playwright-mcp'
OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/boca_sorprendido/prueba_navegador'
os.makedirs(OUT, exist_ok=True)

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

# índices 0-based; boca Sorprendido: mujer M5 -> 4, hombre M3 -> 2
COMBOS = [
    ('F_Sorprendido_T', 'Female', 0, 0, 0, 0, 4, 0, 0, 0, 0, 0),
    ('M_Sorprendido_T', 'Male', 0, 0, 0, 0, 2, 0, 0, 0, 0, 0),
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
                           'clientInfo': {'name': 'dani-calco-T', 'version': '1.0'}}})
    r = read_msg(proc)
    print('initialize:', r.get('result', {}).get('serverInfo'), flush=True)
    send(proc, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    mid[0] += 1
    call(proc, 2, 'browser_navigate', {'url': 'http://127.0.0.1:8766/'})
    cargado = False
    for i in range(30):
        mid[0] += 1
        if eval_bool(proc, mid[0], "() => document.getElementById('estado').textContent === '' && Object.keys(imgs).length === 67"):
            print(f'capas cargadas tras {i + 1}s', flush=True); cargado = True; break
        time.sleep(1)
    if not cargado: raise RuntimeError('las 67 capas no cargaron en 30s')
    for nombre, *args in COMBOS:
        mid[0] += 1
        val = eval_value(proc, mid[0], js_combo(*args))
        cod_pagina, data_url = val.split('|data:image/png', 1)
        data_url = 'data:image/png' + data_url
        ruta = os.path.join(OUT, nombre + '.png')
        n = save_png(data_url, ruta)
        print(f'{nombre}: {cod_pagina.strip()} -> {n} bytes', flush=True)
    print('RENDERS NAVEGADOR OK', flush=True)
finally:
    proc.terminate()
    try: proc.wait(timeout=10)
    except Exception: proc.kill()
