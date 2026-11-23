// grabar_video_randomize.js — Graba un vídeo de ~1 minuto del creador web
// (Playwright con playwright-core del MCP instalado en ~/workspace/playwright-mcp).
// Abre http://127.0.0.1:8765/, espera a que carguen las 67 capas y sigue esta
// línea de tiempo (60 s desde la navegación):
//   0-8s   mujer por defecto (apertura del programa)
//   8-13s  randomize mujer x5 (1 clic/s)
//   13-18s pausa | 18s clic #btnM (a hombre) | 20-25s randomize hombre x5
//   25-30s pausa | 30s clic #btnF (a mujer)   | 32-37s randomize mujer x5
//   37-42s pausa | 42s clic #btnM (a hombre)  | 44-49s randomize hombre x5
//   49-52s pausa | 52s clic #btnF (a mujer)   | 54-59s randomize mujer x5
//   59-60s cuadro final.
// Salida: diagnostico_usuario/video_randomize/video_randomize_1min.webm
// (1280x800). Registra el código de cada resultado en consola.
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

const OUT = '/home/hatch/workspace/anime-portrait-studio/diagnostico_usuario/video_randomize';
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
  const log = (msg) => console.log(`[t=${((Date.now() - t0) / 1000).toFixed(1)}s] ${msg}`);

  await page.goto('http://127.0.0.1:8765/', { waitUntil: 'load' });
  await page.waitForFunction(
    () => document.getElementById('estado').textContent === '' && Object.keys(imgs).length === 67,
    { timeout: 30000 }
  );
  log('creador cargado (67 capas): ' + (await page.textContent('#codigo')));
  await page.screenshot({ path: path.join(OUT, 'frame_apertura.png') });

  const codigo = async () => (await page.textContent('#codigo')).trim();
  const azar = async (n, quien) => {
    for (let i = 0; i < n; i++) {
      await page.click('#btnAzar');
      await sleep(1000);
    }
    log(`randomize ${quien} x${n}: ` + (await codigo()));
  };
  // Espera hasta el segundo absoluto t (desde t0) y luego ejecuta.
  const hasta = async (t, fn) => {
    const queda = t * 1000 - (Date.now() - t0);
    if (queda > 0) await sleep(queda);
    if (fn) await fn();
  };

  await hasta(8);
  await azar(5, 'mujer');            // 8-13s
  await hasta(18);
  await page.click('#btnM'); log('cambio a hombre: ' + (await codigo()));
  await hasta(20);
  await azar(5, 'hombre');           // 20-25s
  await hasta(30);
  await page.click('#btnF'); log('cambio a mujer: ' + (await codigo()));
  await hasta(32);
  await azar(5, 'mujer');            // 32-37s
  await hasta(42);
  await page.click('#btnM'); log('cambio a hombre: ' + (await codigo()));
  await hasta(44);
  await azar(5, 'hombre');           // 44-49s
  await hasta(52);
  await page.click('#btnF'); log('cambio a mujer: ' + (await codigo()));
  await hasta(54);
  await azar(5, 'mujer');            // 54-59s
  await hasta(60);
  log('fin: ' + (await codigo()));

  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();
  const tmpPath = await video.path();
  const finalPath = path.join(OUT, 'video_randomize_1min.webm');
  fs.renameSync(tmpPath, finalPath);
  console.log('VIDEO:', finalPath, fs.statSync(finalPath).size, 'bytes');
})().catch((e) => { console.error('FALLO:', e.message); process.exit(1); });
