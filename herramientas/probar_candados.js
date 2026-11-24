// Prueba de candados + Reset to Default en el creador web.
// Uso: node herramientas/probar_candados.js
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('http://127.0.0.1:8765/', { waitUntil: 'load' });
  await page.waitForFunction(() => document.getElementById('estado').textContent === '', null, { timeout: 30000 });
  const codigo = () => page.evaluate(() => document.getElementById('codigo').textContent);
  const valor = (clave) => page.evaluate((c) => document.getElementById('v_' + c).textContent, clave);

  console.log('1) inicio:', await codigo());

  // 2) Clic en un cuadrito de color (prueba del fix del bug de onclick):
  //    el 3er cuadrito de HAIR COLOR (Chestnut) debe cambiar el pelo a Chestnut.
  await page.evaluate(() => {
    // Hijos de #filas: 0 HAIR, 1 OUTFIT, 2 EYES, 3 EYE COLOR, 4 swatches ojos,
    // 5 NOSE, 6 MOUTH, 7 FACIAL HAIR, 8 HAIR COLOR, 9 swatches pelo, ...
    const sw = document.querySelectorAll('#filas > div')[9].querySelectorAll('button')[2];
    sw.click();
  });
  console.log('2) tras cuadrito Chestnut, HAIR COLOR:', await valor('color_pelo'));

  // 3) Fijar HAIR y OUTFIT con el candado, luego Randomize 3 veces.
  await page.evaluate(() => {
    document.querySelector('button[data-candado="pelo"]').click();
    document.querySelector('button[data-candado="ropa"]').click();
  });
  const peloAntes = await valor('pelo');
  const ropaAntes = await valor('ropa');
  console.log('3) fijados HAIR=', peloAntes, ' OUTFIT=', ropaAntes);
  for (let i = 0; i < 3; i++) await page.click('#btnAzar');
  const peloDespues = await valor('pelo');
  const ropaDespues = await valor('ropa');
  console.log('   tras 3x Randomize: HAIR=', peloDespues, ' OUTFIT=', ropaDespues,
    '| HAIR igual:', peloAntes === peloDespues, '| OUTFIT igual:', ropaAntes === ropaDespues);
  console.log('   codigo ahora:', await codigo());

  // 4) Reset to Default: debe volver a F H1 O1 E1 N1 M1 y quitar los candados.
  await page.click('#btnReset');
  console.log('4) tras Reset:', await codigo());
  const candados = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button[data-candado]')).filter(b => b.textContent === '🔒').length);
  console.log('   candados activos tras Reset:', candados);
  console.log('   estado:', await page.evaluate(() => document.getElementById('estado').textContent));

  // 5) Captura del panel con un candado puesto (para ver la estética).
  await page.evaluate(() => document.querySelector('button[data-candado="ojos"]').click());
  await page.screenshot({ path: '/tmp/candados_panel.png' });
  console.log('5) captura en /tmp/candados_panel.png');
  await browser.close();
})().catch(e => { console.error('FALLO:', e.message); process.exit(1); });
