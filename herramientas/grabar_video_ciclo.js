// grabar_video_ciclo.js — Graba un vídeo de 40 s del creador web para un ciclo
// de revisión (Playwright con playwright-core del MCP).
// Uso: node herramientas/grabar_video_ciclo.js <N>   (N = número de ciclo)
// Línea de tiempo (40 s desde la navegación, cada combo ~3 s):
//   0-3s   mujer por defecto (apertura)
//   3-18s  randomize mujer x5 (1 clic cada 3 s)
//   18s    cambio a hombre | 19-34s randomize hombre x5 (1 clic cada 3 s)
//   34s    cambio a mujer  | 35-40s randomize mujer x2 (1 clic cada 3 s)
// Total: 13 combos (1 default + 5 F + 5 M + 2 F).
// Salida: diagnostico_usuario/ciclos/ciclo<N>/video_ciclo<N>.webm (1280x800)
// y combos_ciclo<N>.json con {t, codigo} de cada combo mostrado.
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

const N = process.argv[2] || '1';
const OUT = `/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/ciclos/ciclo${N}`;
fs.mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: OUT, size: { width: 1280, height: 800 } },
  });
  const page = await context.newPage();
  const t0 = Date.now();
  const combos = [];
  const log = (msg) => console.log(`[t=${((Date.now() - t0) / 1000).toFixed(1)}s] ${msg}`);
  const codigo = async () => (await page.textContent('#codigo')).trim();
  const registrar = async (etiqueta) => {
    const c = await codigo();
    combos.push({ t: +((Date.now() - t0) / 1000).toFixed(1), etiqueta, codigo: c });
    log(`${etiqueta}: ${c}`);
  };
  // Espera hasta el segundo absoluto t (desde t0) y luego ejecuta.
  const hasta = async (t, fn) => {
    const queda = t * 1000 - (Date.now() - t0);
    if (queda > 0) await sleep(queda);
    if (fn) await fn();
  };

  await page.goto('http://127.0.0.1:8765/', { waitUntil: 'load' });
  await page.waitForFunction(
    () => document.getElementById('estado').textContent === '' && Object.keys(imgs).length === 67,
    { timeout: 30000 }
  );
  await registrar('apertura mujer default');

  await hasta(3);  await page.click('#btnAzar'); await registrar('F azar 1');
  await hasta(6);  await page.click('#btnAzar'); await registrar('F azar 2');
  await hasta(9);  await page.click('#btnAzar'); await registrar('F azar 3');
  await hasta(12); await page.click('#btnAzar'); await registrar('F azar 4');
  await hasta(15); await page.click('#btnAzar'); await registrar('F azar 5');
  await hasta(18); await page.click('#btnM'); log('cambio a hombre');
  await hasta(19); await page.click('#btnAzar'); await registrar('M azar 1');
  await hasta(22); await page.click('#btnAzar'); await registrar('M azar 2');
  await hasta(25); await page.click('#btnAzar'); await registrar('M azar 3');
  await hasta(28); await page.click('#btnAzar'); await registrar('M azar 4');
  await hasta(31); await page.click('#btnAzar'); await registrar('M azar 5');
  await hasta(34); await page.click('#btnF'); log('cambio a mujer');
  await hasta(35); await page.click('#btnAzar'); await registrar('F azar 6');
  await hasta(38); await page.click('#btnAzar'); await registrar('F azar 7');
  await hasta(40);
  log('fin: ' + (await codigo()));

  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();
  const tmpPath = await video.path();
  const finalPath = path.join(OUT, `video_ciclo${N}.webm`);
  fs.renameSync(tmpPath, finalPath);
  fs.writeFileSync(path.join(OUT, `combos_ciclo${N}.json`), JSON.stringify(combos, null, 2));
  console.log('VIDEO:', finalPath, fs.statSync(finalPath).size, 'bytes');
  console.log('COMBOS:', combos.length);
})().catch((e) => { console.error('FALLO:', e.message); process.exit(1); });
