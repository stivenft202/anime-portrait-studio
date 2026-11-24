// Prueba de EDAD (Joven/Anciano) en el creador web.
// Uso: servir version-linux en http://127.0.0.1:8766/ y correr:
//   node herramientas/probar_edad.js
// (Modelo: herramientas/probar_candados.js; puerto 8766 para no chocar
// con el servidor normal del 8765.)
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');
const fs = require('fs');

const OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/edad/trabajo_rama/verificacion_edad';
const shot = (page, name) => page.locator('#lienzo').screenshot({ path: `${OUT}/${name}.png` });

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errores = [];
  page.on('pageerror', e => errores.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errores.push('CONSOLE: ' + m.text()); });
  await page.goto('http://127.0.0.1:8766/', { waitUntil: 'load' });
  await page.waitForFunction(() => document.getElementById('estado').textContent === '', null, { timeout: 30000 });
  const codigo = () => page.evaluate(() => document.getElementById('codigo').textContent);
  const valor = (clave) => page.evaluate((c) => document.getElementById('v_' + c).textContent, clave);
  const filas = () => page.evaluate(() => Array.from(document.querySelectorAll('#filas .fila .etq')).map(e => e.textContent));

  console.log('0) filas:', JSON.stringify(await filas()));
  console.log('1) inicio:', await codigo(), '| AGE =', await valor('edad'));

  // 2) Cambiar a Anciano con el botón > de la fila AGE (clic real en la UI).
  await page.click('button[data-k="edad"][data-d="1"]');
  console.log('2) tras AGE > :', await codigo(), '| AGE =', await valor('edad'));
  await shot(page, 'web_F_anciano_H1');

  // 3) Con Anciano, cambiar HAIR COLOR no debe tocar el pelo (tinte anulado).
  const antes = await page.locator('#lienzo').screenshot();
  await page.evaluate(() => {
    // Hijos de #filas con AGE primera: 0 AGE, 1 HAIR, 2 OUTFIT, 3 EYES,
    // 4 EYE COLOR, 5 swatches ojos, 6 NOSE, 7 MOUTH, 8 FACIAL HAIR,
    // 9 HAIR COLOR, 10 swatches pelo, ... -> Silver es el 5º cuadrito.
    const sw = document.querySelectorAll('#filas > div')[10].querySelectorAll('button')[4];
    sw.click();
  });
  console.log('3) tras cuadrito Silver con Anciano, HAIR COLOR:', await valor('color_pelo'));
  await shot(page, 'web_F_anciano_H1_silver');

  // 4) Fijar AGE con el candado y Randomize 5 veces: la edad no cambia.
  await page.click('button[data-candado="edad"]');
  for (let i = 0; i < 5; i++) await page.click('#btnAzar');
  console.log('4) tras 5x Randomize con AGE fijado: AGE =', await valor('edad'), '| codigo:', await codigo());

  // 5) Reset: vuelve a Joven y quita todos los candados.
  await page.click('#btnReset');
  console.log('5) tras Reset:', await codigo(), '| AGE =', await valor('edad'));
  const candados = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button[data-candado]')).filter(b => b.textContent === '🔒').length);
  console.log('   candados activos tras Reset:', candados);
  await shot(page, 'web_F_joven_H1');

  // 6) Todos los pelos ancianos cargan: mujer H1..H12 y hombre H1..H4.
  //    Se cambia a Anciano y se cicla el pelo; el canvas nunca debe quedar
  //    en blanco y no debe haber errores de página.
  await page.click('button[data-k="edad"][data-d="1"]');
  for (let h = 0; h < 12; h++) {
    const px = await page.evaluate(() => {
      const c = document.getElementById('lienzo'), x = c.getContext('2d');
      const d = x.getImageData(0, 0, 1200, 1600).data;
      let n = 0; for (let i = 3; i < d.length; i += 401 * 4) if (d[i] > 0) n++;
      return n;
    });
    console.log(`   F anciana H${h + 1}: muestras opacas=${px}`);
    if (h < 11) await page.click('button[data-k="pelo"][data-d="1"]');
  }
  await page.click('#btnM');
  console.log('   cambio a Male:', await codigo());
  for (let h = 0; h < 4; h++) {
    console.log(`   M anciano H${h + 1}: AGE =`, await valor('edad'));
    if (h < 3) await page.click('button[data-k="pelo"][data-d="1"]');
  }
  await shot(page, 'web_M_anciano_H4');

  console.log('errores de pagina/consola:', errores.length ? errores : 'ninguno');
  await browser.close();
})().catch(e => { console.error('FALLO:', e.message); process.exit(1); });
