// tanda21_verificar_navegador.js — Renderiza las 4 recetas de la Tanda 21
// en el navegador REAL (http://127.0.0.1:8765/) y guarda el lienzo.
// Uso: node tanda21_verificar_navegador.js
// Salida: diagnostico_usuario/tanda21/navegador/t21_{c1,c2,c3,c4}_nav.png
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

const OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/tanda21/navegador';
fs.mkdirSync(OUT, { recursive: true });

// Recetas en índices 0-BASED (motor) -> el creador usa 1-BASED en R.
// R.pelo etc. son 0-based en index.html? Verificado: R.pelo es índice 0-based
// (ARCH.pelo(i) = Hair${i+1}). R.ropa, R.ojos, R.nariz, R.boca igual.
// color_pelo/piel/color_ropa/color_ojos son índices 0-based.
// vello: 0=None, 1=Mustache, 2=Stubble, 3=Full Beard.
const RECETAS = {
  c1: { sexo: 'Female', pelo: 7, ropa: 2, ojos: 3, nariz: 1, boca: 2, vello: 0, color_pelo: 21, piel: 1, color_ropa: 22, color_ojos: 5 },
  c2: { sexo: 'Female', pelo: 8, ropa: 2, ojos: 1, nariz: 1, boca: 1, vello: 0, color_pelo: 2, piel: 3, color_ropa: 13, color_ojos: 3 },
  c3: { sexo: 'Female', pelo: 1, ropa: 2, ojos: 2, nariz: 1, boca: 1, vello: 0, color_pelo: 1, piel: 2, color_ropa: 23, color_ojos: 4 },
  c4: { sexo: 'Female', pelo: 1, ropa: 2, ojos: 3, nariz: 0, boca: 0, vello: 0, color_pelo: 2, piel: 0, color_ropa: 8, color_ojos: 0 },
};

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto('http://127.0.0.1:8765/', { waitUntil: 'load' });
  // Esperar a que carguen las 67 capas (#estado vacío)
  await page.waitForFunction(() => {
    const e = document.querySelector('#estado');
    return e && e.textContent === '';
  }, { timeout: 60000 });
  console.log('capas cargadas');
  for (const [tag, r] of Object.entries(RECETAS)) {
    await page.evaluate((rr) => {
      R.sexo = rr.sexo; R.pelo = rr.pelo; R.ropa = rr.ropa; R.ojos = rr.ojos;
      R.nariz = rr.nariz; R.boca = rr.boca; R.vello = rr.vello;
      R.color_pelo = rr.color_pelo; R.piel = rr.piel;
      R.color_ropa = rr.color_ropa; R.color_ojos = rr.color_ojos;
      dibujar();
    }, r);
    await page.waitForTimeout(1500);
    const dataUrl = await page.evaluate(() => {
      const c = document.querySelector('#lienzo');
      return c.toDataURL('image/png');
    });
    const b64 = dataUrl.split(',')[1];
    fs.writeFileSync(path.join(OUT, `t21_${tag}_nav.png`), Buffer.from(b64, 'base64'));
    const codigo = await page.evaluate(() => document.querySelector('#codigo').textContent);
    console.log(tag, '->', codigo);
  }
  await browser.close();
  console.log('OK navegador');
})().catch((e) => { console.error('ERROR', e); process.exit(1); });
