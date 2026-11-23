// grabar_video.js — Script REUTILIZABLE para grabar vídeos del creador web
// de Anime Portrait Studio (Playwright con playwright-core del MCP).
// Se usa cada vez que hay que grabar el programa en acción (revisiones por
// vídeo, nuevas expresiones, etc.).
//
// Uso:
//   node herramientas/grabar_video.js [opciones]
//
// Opciones:
//   --duracion <s>    Duración total del vídeo (defecto 40)
//   --segundos <s>    Segundos por combo antes de randomizar (defecto 3)
//   --boca <modo>     sorprendido = forzar la boca Sorprendido en TODOS los
//                     combos (mujer M5, hombre M3); aleatorio = dejar la
//                     boca que salga en el randomize (defecto: sorprendido)
//   --sexos <lista>   mujer,hombre | mujer | hombre (defecto: mujer,hombre;
//                     con los dos, cambia de sexo a la mitad del vídeo)
//   --salida <ruta>   Archivo .webm de salida (defecto:
//                     diagnostico_usuario/videos/video_<fecha-hora>.webm)
//   --url <base>      URL del creador (defecto http://127.0.0.1:8765/)
//
// Salida: el vídeo .webm (1280x800) y un .json con el mismo nombre con
// {t, etiqueta, codigo} de cada combo mostrado.
const { chromium } = require('/home/hatch/workspace/playwright-mcp/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

const BASE = '/home/hatch/workspace/anime-portrait-studio';

// --- argumentos ---
const args = {};
for (let i = 2; i < process.argv.length; i += 2) {
  const k = process.argv[i];
  const v = process.argv[i + 1];
  if (!k || !k.startsWith('--')) continue;
  args[k.slice(2)] = v === undefined ? true : v;
}
const DURACION = parseInt(args.duracion || '40', 10);
const SEGUNDOS = parseInt(args.segundos || '3', 10);
const BOCA = (args.boca || 'sorprendido').toLowerCase();
const SEXOS = (args.sexos || 'mujer,hombre').split(',').map((s) => s.trim().toLowerCase());
const URL = args.url || 'http://127.0.0.1:8765/';
const ahora = new Date();
const sello = `${ahora.getFullYear()}-${String(ahora.getMonth() + 1).padStart(2, '0')}-${String(ahora.getDate()).padStart(2, '0')}_${String(ahora.getHours()).padStart(2, '0')}-${String(ahora.getMinutes()).padStart(2, '0')}`;
const SALIDA = args.salida || path.join(BASE, 'diagnostico_usuario', 'videos', `video_${sello}.webm`);
const OUT_DIR = path.dirname(SALIDA);
fs.mkdirSync(OUT_DIR, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: OUT_DIR, size: { width: 1280, height: 800 } },
  });
  const page = await context.newPage();
  const t0 = Date.now();
  const combos = [];
  const log = (msg) => console.log(`[t=${((Date.now() - t0) / 1000).toFixed(1)}s] ${msg}`);
  const codigo = async () => (await page.textContent('#codigo')).trim();

  // Fuerza la boca Sorprendido según el sexo actual y re-renderiza.
  const forzarBoca = async () => {
    if (BOCA !== 'sorprendido') return;
    await page.evaluate(() => {
      R.boca = R.sexo === 'F' ? 4 : 2;
      dibujar();
    });
  };
  const registrar = async (etiqueta) => {
    const c = await codigo();
    combos.push({ t: +((Date.now() - t0) / 1000).toFixed(1), etiqueta, codigo: c });
    log(`${etiqueta}: ${c}`);
  };
  const hasta = async (t, fn) => {
    const queda = t * 1000 - (Date.now() - t0);
    if (queda > 0) await sleep(queda);
    if (fn) await fn();
  };

  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction(
    () => document.getElementById('estado').textContent === '' && Object.keys(imgs).length === 67,
    { timeout: 30000 }
  );
  log(`grabando ${DURACION}s, combo cada ${SEGUNDOS}s, boca=${BOCA}, sexos=${SEXOS.join('+')}`);

  // Sexo inicial: el primero de la lista (antes del combo de apertura).
  // Si hay dos sexos, se cambia al otro a la mitad del vídeo.
  let sexoActual = SEXOS[0] === 'hombre' ? 'M' : 'F';
  if (sexoActual === 'M') await page.click('#btnM');
  let cambiado = SEXOS.length < 2;

  // Combo de apertura: sexo inicial, boca forzada si toca.
  await forzarBoca();
  await registrar('apertura');

  const nSlots = Math.floor(DURACION / SEGUNDOS);
  for (let k = 1; k <= nSlots; k++) {
    const t = k * SEGUNDOS;
    if (t >= DURACION) break;
    await hasta(t, async () => {
      if (!cambiado && t >= DURACION / 2) {
        const otro = SEXOS[1] === 'hombre' ? 'M' : 'F';
        await page.click(otro === 'M' ? '#btnM' : '#btnF');
        sexoActual = otro;
        cambiado = true;
        log(`cambio a ${otro === 'M' ? 'hombre' : 'mujer'}`);
      }
      await page.click('#btnAzar');
      await forzarBoca();
    });
    await registrar(`azar ${k}`);
  }
  await hasta(DURACION);
  log('fin: ' + (await codigo()));

  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();
  const tmpPath = await video.path();
  fs.renameSync(tmpPath, SALIDA);
  const jsonPath = SALIDA.replace(/\.webm$/i, '.json');
  fs.writeFileSync(jsonPath, JSON.stringify(combos, null, 2));
  console.log('VIDEO:', SALIDA, fs.statSync(SALIDA).size, 'bytes');
  console.log('COMBOS:', combos.length, '->', jsonPath);
})().catch((e) => { console.error('FALLO:', e.message); process.exit(1); });
