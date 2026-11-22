# VERSIONES

## 2026-11-22 — Fix tinte de ojos en guardar_png (motor.py)
- Snapshot previo: `versiones/2026-11-22_antes-fix-ojos-guardar_png/motor.py` (md5 f07367b7205fb598099a10b7a303e4bd).
- Cambio (1 línea, en `guardar_png`): la capa de ojos ahora pasa por `_ojos_tinte(..., receta.get('color_ojos', 0))`,
  igual que en `render()` y en el JS del Creador. Antes el PNG exportado salía siempre con el iris verde original.
- Verificado: Blue [58,104,166], Brown [106,68,40], Red [159,42,38], Original Green sin cambio [30,42,26],
  Violet en ella con recorte cara 1200×1200 correcto. Ojos azules confirmados visualmente en el render.
- No se tocó `render()`, ni index.html, ni texturas, ni nada de Unity/Drive.

## 2026-11-22 — Réplica stage19 a Unity/Drive (orden expresa de Stiven)
- Comparación md5 local stage19 vs Drive stage18 (67 capas base): 30 iguales, 37 difieren.
  Difieren — Female (22): Base, Hair1-12_Front, Hair1-4_Back, Hair11-12_Back, Outfit1-3.
  Difieren — Male (15): Base, FacialHair1-3, Hair1-4_Front, Hair1-4_Back, Outfit1-3.
  Iguales (no se tocan): todos los Eyes, Mouth y Nose, Hair5-10_Back de ella, y las 60 EyesColor.
  Nota: el prompt maestro dice "41 capas corregidas"; por md5 difieren 37 archivos
  (algunas capas recibieron varias correcciones; las EyesColor no cambian porque los Eyes no cambian).
- Snapshot previo stage18 completo (67 PNG + comparación JSON):
  `versiones/2026-11-22_stage18-antes-stage19/`.
- Subida: reemplazo por id con `drive files update`, sin tocar ningún .meta.

- Verificación 2026-11-22 ~17:10: descargados de Drive los 37 archivos subidos y
  comparados por md5 con stage19 local: **37/37 OK, 0 mal**. Unity/Drive = stage19.
  Nota: el script de subida los marcó "FALLO" a los 37 porque buscaba la palabra
  "success" en la salida y el CLI de Drive responde con el JSON del archivo, no con
  "success". La verificación por md5 es la que manda.
- No se tocó ningún .meta. Las 60 EyesColor no cambiaron (los Eyes no cambian en stage19).
- Pendiente de Stiven: abrir Unity, esperar la sincronización de Drive y correr
  Tools > Portrait Kit > Create Data and Demo Scene y Create Creator Scene,
  y confirmar el diálogo "Portrait Kit is ready".
