# Barrido VISUAL del creador web en el navegador local (Chromium headless).
#
# El navegador en la nube no puede abrir http://127.0.0.1:8765/ (loopback
# rechazado), así que el barrido se hace aquí con Playwright Python contra
# el Chromium ya instalado en /var/tmp/ms-playwright (PLAYWRIGHT_BROWSERS_PATH).
# Requiere servidor.py corriendo (http://127.0.0.1:8765/).
#
# 8 checks del barrido original: 6 recetas fijadas por evaluate + dibujar(),
# cambio de sexo con CLIC REAL en #btnM (prueba de limitar()), y Randomize x3
# con clics reales en #btnAzar. Por cada check: código de #codigo + captura
# de página + lienzo a resolución completa (toDataURL) en
# diagnostico_usuario/barrido_navegador/.
import base64, json, os, sys
from playwright.sync_api import sync_playwright

BASE = '/home/hatch/workspace/anime-portrait-studio'
OUT = os.path.join(BASE, 'diagnostico_usuario/barrido_navegador')
os.makedirs(OUT, exist_ok=True)

# receta: (nombre, dict de campos R)
CHECKS = [
    ('01_31_H9_Honey', dict(sexo='Female', pelo=8, ropa=2, ojos=3, nariz=0, boca=1,
                            color_pelo=14, piel=0, color_ropa=0, color_ojos=4, vello=0)),
    ('02_F_H6_Silver', dict(sexo='Female', pelo=5, ropa=0, ojos=0, nariz=0, boca=0,
                            color_pelo=4, piel=0, color_ropa=0, color_ojos=0, vello=0)),
    ('03_F_H11_Silver', dict(sexo='Female', pelo=10, ropa=0, ojos=0, nariz=0, boca=0,
                             color_pelo=4, piel=0, color_ropa=0, color_ojos=0, vello=0)),
    ('04_M_H12_a_Style4', dict(sexo='Male', pelo=11, ropa=0, ojos=0, nariz=1, boca=4,
                               color_pelo=1, piel=1, color_ropa=13, color_ojos=4, vello=0)),
    ('05_17_M_Stubble', dict(sexo='Male', pelo=0, ropa=2, ojos=0, nariz=0, boca=2,
                             color_pelo=4, piel=0, color_ropa=15, color_ojos=1, vello=2)),
    ('06_F_Angry_Violet', dict(sexo='Female', pelo=0, ropa=0, ojos=3, nariz=0, boca=0,
                               color_pelo=0, piel=0, color_ropa=0, color_ojos=4, vello=0)),
    ('07_F_Angry_Red', dict(sexo='Female', pelo=0, ropa=0, ojos=3, nariz=0, boca=0,
                            color_pelo=0, piel=0, color_ropa=0, color_ojos=6, vello=0)),
]

def set_receta(page, rec):
    js = '; '.join(f"R.{k}={json.dumps(v)}" for k, v in rec.items()) + '; dibujar();'
    page.evaluate(js)
    page.wait_for_timeout(400)

def guardar(page, nombre):
    codigo = page.inner_text('#codigo')
    page.screenshot(path=os.path.join(OUT, nombre + '_pagina.png'))
    data = page.evaluate("document.getElementById('lienzo').toDataURL('image/png')")
    with open(os.path.join(OUT, nombre + '_lienzo.png'), 'wb') as f:
        f.write(base64.b64decode(data.split(',', 1)[1]))
    print(f'{nombre}: {codigo}', flush=True)
    return codigo

def main():
    reporte = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1280, 'height': 900})
        pg.goto('http://127.0.0.1:8765/', wait_until='load')
        pg.wait_for_function("Object.keys(imgs).length===67 && document.getElementById('estado').textContent===''", timeout=60000)
        pg.wait_for_timeout(500)
        print('creador cargado: 67 imagenes', flush=True)
        for nombre, rec in CHECKS:
            set_receta(pg, rec)
            reporte[nombre] = guardar(pg, nombre)
        # 8) Cambio de sexo con CLIC REAL: Female H12 -> Male (debe decir H4, pelo presente).
        set_receta(pg, dict(sexo='Female', pelo=11, ropa=0, ojos=0, nariz=0, boca=0,
                            color_pelo=0, piel=0, color_ropa=0, color_ojos=0, vello=0))
        pg.click('#btnM')
        pg.wait_for_timeout(400)
        reporte['08_sexo_F_H12_a_M'] = guardar(pg, '08_sexo_F_H12_a_M')
        # 9) Randomize x3 con clics reales.
        for i in (1, 2, 3):
            pg.click('#btnAzar')
            pg.wait_for_timeout(400)
            reporte[f'09_azar_{i}'] = guardar(pg, f'09_azar_{i}')
        b.close()
    json.dump(reporte, open(os.path.join(OUT, 'reporte.json'), 'w'), indent=1, ensure_ascii=False)
    print('REPORTE OK', len(reporte), 'checks', flush=True)

if __name__ == '__main__':
    main()
