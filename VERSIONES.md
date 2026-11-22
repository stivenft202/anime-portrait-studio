# VERSIONES

## 2026-11-22 — Stage20: barrido completo y arreglo de los errores reportados por Stiven
- Orden de Stiven 17:21: barrido completo de los 4.860 combos y arreglar uno por uno
  los errores de sus 11 capturas de Unity (lunares en boca, ojos de otro color, barba
  extraña con mechones, mujer sin ojos, falta de pelo, cicatriz en la mejilla, calva,
  pelo movido a la izquierda).
- Barrido: `probar_todo.py` corrido 2 veces (16:52 y 17:23), resultado idéntico:
  2.173 combos marcados, todos en las zonas de falsa alarma conocidas (§11). El
  barrido NO detecta estos errores (solo escanea la mejilla/mandíbula y excluye la boca).
- Diagnóstico: las 11 recetas reproducidas en Linux salen mayormente BIEN (la calva,
  el pelo movido y la mujer sin ojos NO se reproducen en Linux) → lo de Unity es
  estado local de su PC (los .asset en Drive son de las 14:42, no de las 17:15;
  sync o menús sin regenerar). Las 60 EyesColor verificadas una por una: correctas.
  El código de Unity (PortraitView/SetupAssistant) auditado: sin errores.
- Errores REALES en las texturas, arreglados (snapshot previo en
  `versiones/2026-11-22_stage20-antes-fragmentos/`):
  1. Fragmentos de cara horneados en los frentes de pelo: 57 componentes borrados
     (18.671 px) en 12 capas — trozos de ojo/ceja, línea de la boca, zigzag de la
     mejilla (= la «cicatriz») y trazo del mentón. Script `herramientas/stage20_fix_fragmentos.py`.
     Verificado: detector re-corrido, solo queda pelo legítimo (pecho, trenza, oreja).
  2. Barba completa (FacialHair3): 14 grietas casi transparentes rellenadas (950 px)
     con el color local de la barba — la curva clara que se veía dentro de la barba.
     Script `herramientas/stage20_fix_barba.py`. No se tocó el hueco bigote/barba.
  3. Disco ámbar del iris (fix D del §12): `_ojos_tinte` en `motor.py` ahora tiñe
     también el disco cálido inferior del iris y su borde grisáceo (rim), cada uno
     con su propia escala. Además la caché del iris era por nombre y chocaba entre
     él y ella (mismo nombre de archivo, arte distinto): ahora es por (sexo, nombre).
  4. Variantes EyesColor re-horneadas (60) con la lógica corregida, en
     `unity/EyesColor/` (Female/Male). Verificado: parte verde byte-idéntica a la
     variante vieja (0 px difieren >5); disco ahora en el color pedido
     (Angry Gray: vieja [119,113,98] ámbar → nueva [127,132,138] gris).
- 18:03 — Stiven mandó 7 capturas más con la ÚLTIMA versión y confirmó que le
  salió «Portrait Kit is ready». La hipótesis de datos viejos queda DESCARTADA:
  los errores están en stage19 mismo. Y el barrido numérico no los ve (solo
  busca manchas en la mejilla). Nuevos hallazgos y arreglos (snapshot previo en
  `versiones/2026-11-22_stage20-antes-azules/`):
  5. Trazos azules/dorados en el pelo de ella: brillos dibujados en azul pálido
     (B-R>30) en las capas de pelo femenino — 63.789 px en 23 capas (H11_Front
     11.060, H6_Front 8.493, H1_Back 8.427, H5_Front 7.897, H3_Back 6.998,
     H12_Front 5.102, H9_Front 3.679...). No toman el tinte: con tintes fríos
     se ven azules y con Honey dorados, como un trazo pegado al borde del pelo.
     Arreglo: esos píxeles se tiñen con el color base oscuro de su propia capa
     (mediana de sus píxeles opacos) para que se fundan con el pelo.
     Script `herramientas/stage20_fix_azules.py`. OJO: primero se probó
     desaturarlos a gris y NO funcionó (un gris claro con Honey sigue dorado:
     el antes/después con Honey salía idéntico). Verificado: 0 px azulados
     restantes; renders H9 Honey (franja dorada DESAPARECIDA), H6/H11 Silver
     (sin trazos azules) revisados visualmente.
  6. Código de receta «H12» en hombre: al cambiar de Female a Male, el Creador
     conservaba los índices (SetCharacter no los limitaba) → el código mostraba
     «M H12» y el panel «Style 4». El render estaba bien (PortraitView ya
     limitaba). Arreglo en `PortraitCreator.cs`: `ClampRecipeToData()` llamado
     en SetCharacter, Start y LoadRecipe. El .cs local coincide por md5 con el
     de Drive (fb0b9207...), el fix se sube por id sin tocar el .meta.
  7. Creador web (`index.html`, versión Linux): mismo bug al cambiar de sexo
     (R.pelo sin limitar → el pelo desaparecía) y `ojosTeñidos` sin el fix del
     disco. Arreglados: `limitar()` en `dibujar()` y disco+rim en `ojosTeñidos`
     (igual que `motor.py`). Sintaxis JS verificada con node.
- Playwright: no se usó el Playwright standalone para este trabajo (sus
  binarios se perdieron en el reinicio de la VM y la reinstalación está
  bloqueada con 403). El barrido VISUAL se hace con el navegador del runtime
  sobre el creador local (http://127.0.0.1:8765/), que es la misma clase de
  automatización (clics + capturas) y sí funciona.
- Decisión de Stiven 2026-11-22 ~18:21: boca Sorprendido RECHAZADA — la boca queda
  como está (el óvalo rojo de 29×37 px). La propuesta v2 NO se aplica. Muestra en
  `diagnostico_usuario/muestra_boca/` (M13 y F19S, actual vs propuesta) queda archivada.
- Verificación: 11 recetas re-renderizadas (`diagnostico_usuario/verificacion_stage20/`),
  revisadas visualmente — pelo completo, ojos visibles y de un solo color, sin
  cicatriz, barba sin curva clara. Re-barrido `probar_todo.py` (log
  `probar_todo_2026-11-22_stage20.log`): 2.307 marcados (antes 2.173, +134).
  Comparación Female antes/después (frentes del snapshot vs corregidos): AHORA 763,
  ANTES 629, +134 nuevas, 0 quitadas, casi todas en la zona (x~90, y~210) del
  detector: al quitar los fragmentos de pelo quedó a la vista el borde inferior
  del ojo y la mandíbula, que el detector marca como falsa alarma (§11). NO es
  regresión del arte: ninguna receta dejó de estar marcada y las 134 nuevas son
  H2/H10 (los frentes con fragmentos quitados).
- Regla nueva de Stiven 2026-11-22 ~18:21: «de ahora en adelante sube todo tambien
  siempre a drive para unity» — cada update va a GitHub Y a Drive/Unity siempre
  (reemplaza la regla anterior de «solo por orden expresa»).
- Barrido visual en el navegador: el navegador en la nube NO puede abrir
  http://127.0.0.1:8765/ (rechaza direcciones locales, loopback). La verificación
  visual por esa vía falló; pendiente investigar Playwright MCP (orden de Stiven).

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

## 2026-11-22 — Primera versión en GitHub
- Repo https://github.com/stivenft202/anime-portrait-studio, commit ee7ae9ab.
- Contenido: stage19 Linux completo (86 archivos, 75 MB).
- Verificado: 86/86 hashes de blob iguales a los locales; motor.py en GitHub lleva el fix de ojos.
