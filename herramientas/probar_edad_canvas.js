// Captura el canvas a resolución completa (1200x1600) vía toDataURL,
// para comparar píxel a píxel con el motor (la captura del elemento sale
// a tamaño de pantalla y el reescalado falsea la comparación).
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');
const fs = require('fs');
const OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/edad/trabajo_rama/verificacion_edad';

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('http://127.0.0.1:8766/', { waitUntil: 'load' });
  await page.waitForFunction(() => document.getElementById('estado').textContent === '', null, { timeout: 30000 });
  const dump = (name) => page.evaluate((n) => {
    const c = document.getElementById('lienzo');
    window.__dump = c.toDataURL('image/png');
    return n;
  }, name).then(async () => {
    const url = await page.evaluate(() => window.__dump);
    fs.writeFileSync(`${OUT}/${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
    console.log(name, 'guardado');
  });

  await page.click('button[data-k="edad"][data-d="1"]');
  await dump('canvas_F_anciano_H1');
  await page.click('#btnReset');
  await dump('canvas_F_joven_H1');
  await page.click('#btnM');
  await page.click('button[data-k="edad"][data-d="1"]');
  for (let i = 0; i < 3; i++) await page.click('button[data-k="pelo"][data-d="1"]');
  console.log('M:', await page.evaluate(() => document.getElementById('codigo').textContent));
  await dump('canvas_M_anciano_H4');
  await browser.close();
})().catch(e => { console.error('FALLO:', e.message); process.exit(1); });
