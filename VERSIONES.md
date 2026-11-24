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
- SUBIDO 2026-11-22 ~18:35 por orden de Stiven («subelo ya», regla nueva: siempre
  GitHub + Drive/Unity): GitHub commit `94b6efc0` (151 archivos, verificado
  151/151 hashes, motor.py y PortraitCreator.cs confirmados en raw.githubuser
  content.com); Drive/Unity 86 archivos por ID y verificados por md5 86/86
  (60 variantes EyesColor, 18 capas de pelo de ella, 7 de él incl. FacialHair3,
  PortraitCreator.cs), sin tocar ningún .meta. Unity/Drive = stage20.
- Barrido visual en el navegador: el navegador en la nube NO puede abrir
  http://127.0.0.1:8765/ (rechaza direcciones locales, loopback). Se hizo con
  Playwright Python en el Chromium local (`herramientas/barrido_navegador.py`,
  2026-11-22 ~18:32): 11/11 checks con el código correcto, revisados visualmente
  en `diagnostico_usuario/barrido_navegador/` — #31 sin franja dorada ni trazos
  azules, H6/H11 Silver limpios, H12→H4 con clic real (pelo presente, no calvo),
  #17 con ojos Brown uniformes y barba incipiente, Angry Violet/Red con iris de
  un solo color (disco verificado numéricamente: navegador = motor ±2,5 RGB),
  Randomize x3 válido, Full Beard sin la curva clara. SIN defectos nuevos. La
  boca Sorprendido sigue siendo el óvalo rojo por decisión de Stiven.

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

## 2026-11-22 — Tanda 0 del barrido completo (capas)
- Barrido con Playwright MCP (stdio, JSON-RPC): 144 renders en el navegador
  (67 capas aisladas + 67 canónicas + 10 auxiliares de disco), 1200×1600.
- Detectores: fragmentos en cara, azules en pelo crudo, grietas en FH3,
  disco ámbar del iris, trazos sueltos. 14 sospechosos → revisados con zoom.
- **3 defectos reales corregidos (331 px):**
  1. Male/Hair2_Front: cuadrado marrón 80 px (x301-311, y512-524) + mota
     25 px (x317-324, y534-539) junto al ojo lejano — borrados.
  2. Female/Hair6_Front: mota oscura 33 px (x610-614, y869-876) en la
     mejilla — borrada.
  3. Male/FacialHair3: rendija blanca en diagonal 91+45 px (x614-704,
     y689-733) + 5 microagujeros de 9-21 px — rellenados con mediana local.
- Confirmado limpio: azules en pelo crudo 0 px; fragmentos stage20 0
  reaparecidos; grietas stage20 en FH3 0 reaparecidas; disco ámbar limpio
  (racimo mayor 11 px, borde); 113 falsas alarmas §11 etiquetadas; 11
  sospechosos descartados (pelo legítimo / textura de barba).
- NO se tocó el hueco de 514 px entre bigote y barba (x304-456, y737-798):
  es intencional (documentado en stage20_fix_barba.py).
- Scripts: herramientas/tanda0_fix.py (con asserts, 0 px fuera de zona),
  herramientas/tanda0_verificar.py. Snapshot previo en
  versiones/2026-11-22_tanda0-antes-fixes/. Verificación visual post-fix
  (3 zooms + 2 planchas canónicas) OK.
- Reporte: diagnostico_usuario/barrido_tanda0/ (reporte.json, renders,
  planchas, revision/, verificacion/).
- PENDIENTE: subir a GitHub + Drive/Unity cuando Stiven lo ordene.

## 2026-11-22 — Tanda 1 del barrido completo (mujeres, pelo 1)
- 225 renders en el navegador MCP (F, Hair1 Long Straight; ropa 0-2 ×
  ojos 0-4 × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600, ~1 s
  por combo (203 s en total).
- Detectores: lunares/trazos en cara, azules en pelo, disco del iris,
  trazos sueltos, integridad (ojos/bocas presentes).
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" se explican por 3 causas sistemáticas, no errores:
  - D2 azules: bug del detector (la capucha azul O3 se contaba como pelo);
    corregida la máscara por ropa y re-medido: 0 px en los 225. El detector
    ya quedó corregido en detectar_tanda1.py para las tandas siguientes.
  - D3 disco: el frente del pelo tapa 53 px de la esquina interior del
    iris y parte el racimo al medirlo; el disco ámbar está intacto y el
    iris se ve uniforme (verificado con zoom E1/E2/E4).
  - D4 trazos: 26 componentes, todos arte del dibujo (líneas de la oreja,
    sombra de mandíbula ya anotada, esquina de la boca, pliegues de ropa).
- Confirmado limpio: lunares reales 0; azules en pelo 0 px; disco intacto
  en los 5 ojos; ojos y bocas presentes y completos en los 225; ningún
  render en blanco. 225 falsas alarmas §11 (1 por combo).
- Nota de método: en las tandas siguientes el D3 debe comparar contra el
  valor esperado con el pelo puesto (no contra el crudo) y el D4 debe
  excluir la oreja y limitarse a y<900.
- Reporte: diagnostico_usuario/barrido_tanda1/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 2 del barrido completo (mujeres, pelo 2)
- 225 renders en el navegador MCP (F, Hair2 Pixie Cut; ropa 0-2 × ojos 0-4
  × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600, ~1 s por combo
  (200 s en total).
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 8 componentes
  distintos, todos arte del dibujo (sombra de la esquina de la boca,
  borde inferior de la boca M1, líneas de la mandíbula/mentón, borde de
  la capucha O3), verificados con zoom. D1, D2, D3 y D5 no marcaron nada.
- Confirmado limpio: lunares reales 0 (450 falsas alarmas §11); azules en
  pelo 0 px; disco ámbar intacto (racimo cálido 62 px, igual al crudo 61 px:
  el Pixie Cut es corto y NO tapa la esquina del iris; iris uniforme
  verificado a ojo en E1 y E5); ojos y bocas presentes en los 225.
- Nota de método: la calibración D3 por ojo con el pelo puesto funcionó
  (desviación 0,0); el D4 con oreja excluida y y<900 deja solo 8
  componentes sistemáticos de arte, descartables por bbox.
- Reporte: diagnostico_usuario/barrido_tanda2/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 3 del barrido completo (mujeres, pelo 3)
- 225 renders en el navegador MCP (F, Hair3 Bob Cut; ropa 0-2 × ojos 0-4
  × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 8 componentes
  distintos, todos arte del dibujo (sombra de la esquina de la boca,
  líneas de la mandíbula/mentón, mota de sombra de la mandíbula ya anotada,
  y uno NUEVO respecto a la tanda 2: línea y sombra de la mandíbula junto
  a la oreja, x688-722, y727-777, 201 px — el Bob Cut deja ver esa unión;
  verificado con zoom: es la línea de la mandíbula y su sombra, arte
  legítimo). D1, D2, D3 y D5 no marcaron nada.
- Confirmado limpio: lunares reales 0 (450 falsas alarmas §11); azules en
  pelo 0 px; disco ámbar intacto (racimo cálido por ojo con este pelo: 36
  px, E3 39, desviación 0,0; el Bob Cut tapa parte de la esquina interior
  del iris, como el pelo 1; iris uniforme verificado a ojo en E1 y E5);
  ojos y bocas presentes en los 225.
- Reporte: diagnostico_usuario/barrido_tanda3/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 4 del barrido completo (mujeres, pelo 4)
- 225 renders en el navegador MCP (F, Hair4 Long Wavy; ropa 0-2 × ojos 0-4
  × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600, ~1 s por combo
  (163 s en total). Nota: servidor.py estaba caído al empezar la tanda y
  se relanzó con nohup (responde 200).
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 6 componentes
  distintos, todos arte ya conocido de las tandas 1-3, NINGUNO nuevo
  (mota de sombra de la mandíbula, línea y sombra junto a la oreja, sombra
  de la esquina de la boca, líneas de la mandíbula/mentón, borde inferior
  de la boca M1). D1, D2, D3 y D5 no marcaron nada.
- Confirmado limpio: lunares reales 0 (450 falsas alarmas §11); azules en
  pelo 0 px; disco ámbar intacto (racimo cálido por ojo con este pelo:
  mediana 55 px, mín. 51, máx. 55; el Long Wavy tapa parte de la esquina
  interior del iris, como los pelos 1 y 3; iris uniforme verificado a ojo
  en E1 y E5); ojos y bocas presentes en los 225.
- Reporte: diagnostico_usuario/barrido_tanda4/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 5 del barrido completo (mujeres, pelo 5)
- 225 renders en el navegador MCP (F, Hair5, pelo largo con mechones
  laterales que caen por delante de los hombros; ropa 0-2 × ojos 0-4
  × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600, ~1 s por combo
  (163 s en total).
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 5 componentes
  distintos, todos arte del dibujo. Uno NUEVO como componente aparte:
  línea vertical mandíbula-cuello (x721-737, y733-768, 53 px) — es arte
  de la capa Base (el borde delantero de la mandíbula que baja al cuello);
  verificado: la línea está en la Base sola, NO en Hair5_Front, y en la
  tanda 4 el mismo punto estaba tapado por el pelo 4. Descartable por bbox
  en tandas siguientes. Los 3 componentes conocidos que no salen (línea de
  la mandíbula/mentón, mota de sombra, borde inferior de la mandíbula)
  siguen ahí, pero los mechones del pelo 5 los parten por debajo del
  umbral de 50 px (verificado numéricamente).
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11, 1 por
  combo: borde inferior del ojo; la de la mandíbula ya no sale porque el
  pelo 5 tapa esa zona); azules en pelo 0 px; disco ámbar intacto (racimo
  cálido por ojo con este pelo: E1 29, E2 29, E3 39, E4 29, E5 33, desv.
  máx. 2,0; el pelo 5 tapa parte de la esquina interior del iris; iris
  uniforme verificado a ojo en E1 y E5); ojos y bocas presentes en los 225.
- Reporte: diagnostico_usuario/barrido_tanda5/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 6 del barrido completo (mujeres, pelo 6)
- 225 renders en el navegador MCP (F, Hair6 coleta alta, pelo largo
  recogido arriba con mechones sueltos enmarcando la cara; ropa 0-2
  × ojos 0-4 × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600,
  ~1 s por combo (167 s en total). Servidor.py respondía 200 al empezar;
  no hizo falta relanzarlo.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 6 componentes
  distintos, todos arte del dibujo (mota de sombra de la mandíbula, línea
  vertical mandíbula-cuello, línea y sombra junto a la oreja, sombra de la
  esquina de la boca, borde derecho de la mandíbula/cuello — contorno del
  cuello, verificado con zoom —, borde de cuello de la capucha O3). D1, D2,
  D3 y D5 no marcaron nada.
- VERIFICACIÓN DEL ARREGLO DE LA TANDA 0: la mancha oscura de 33 px
  borrada de Female/Hair6_Front (x610-614, y869-876) **sigue borrada**:
  0 px opacos en esa zona de la capa (alfa máx. 30, media 2,2), 0
  componentes D1/D4 cerca en los 225 renders, y el recorte con zoom 4x
  de la zona en el render se ve limpio (piel, sombra de la mandíbula y un
  mechón de la coleta, sin mancha). Verificado también por mí a ojo.
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11, 1 por
  combo: borde inferior del ojo); azules en pelo 0 px; disco ámbar
  intacto (racimo cálido por ojo con este pelo: E1 37, E2 37, E3 39, E4 37,
  E5 37, desviación 0,0; la coleta tapa parte de la esquina interior del
  iris; iris uniforme verificado a ojo en E1); ojos y bocas presentes en
  los 225.
- Reporte: diagnostico_usuario/barrido_tanda6/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 7 del barrido completo (mujeres, pelo 7)
- 225 renders en el navegador MCP (F, Hair7 Long Braid, trenza larga;
  ropa 0-2 × ojos 0-4 × nariz 0-2 × boca 0-4; colores por defecto),
  1200×1600, ~1 s por combo (165 s en total). Servidor.py respondía 200
  al empezar; no hizo falta relanzarlo.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 5 componentes
  distintos, todos arte ya conocido, NINGUNO nuevo (mota de sombra de la
  mandíbula, línea y sombra junto a la oreja, sombra de la esquina de la
  boca, borde inferior de la mandíbula, borde de cuello de la capucha O3).
  La línea vertical mandíbula-cuello y el borde derecho de la mandíbula
  no aparecen como componentes aparte porque la trenza tapa esas zonas.
  D1, D2, D3 y D5 no marcaron nada.
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11, 1 por
  combo: borde inferior del ojo); azules en pelo 0 px; disco ámbar
  intacto (racimo cálido por ojo con este pelo: E1 27, E2 14, E3 39, E4 20,
  E5 33, desviación 0,0; E2 es el valor más bajo hasta ahora porque la
  trenza tapa más de su esquina interior; iris uniforme verificado a ojo
  en E1 y E5); ojos y bocas presentes en los 225.
- Reporte: diagnostico_usuario/barrido_tanda7/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 8 del barrido completo (mujeres, pelo 8)
- 225 renders en el navegador MCP (F, Hair8 moño alto, pelo recogido
  arriba con mechones sueltos enmarcando la cara; ropa 0-2 × ojos 0-4
  × nariz 0-2 × boca 0-4; colores por defecto), 1200×1600, ~1 s por combo
  (166 s en total). Servidor.py respondía 200 al empezar; no hizo falta
  relanzarlo.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- CONTROLES AMPLIADOS (orden de Stiven 2026-11-22 ~21:47: revisar
  también cualquier otro tipo de error, no solo los que él indicó):
  D6 calvas/pelo movido y D7 manchas/trazos raros en TODO el retrato,
  y revisión visual de LAS 9 planchas completas (antes solo 2).
- Los 225 "sospechosos" eran solo D4 (trazos sueltos): 4 componentes por
  combo (900 en total), todos arte ya conocido. D1, D2, D3, D5, D6 y D7
  no marcaron nada.
- D6: 0 px en los 225. Nota de método: la primera pasada comparó contra
  el canónico O1 para todas las ropas y marcó 1.706.070 px en 210 renders
  (FALSO POSITIVO: la ropa tapa el pelo trasero de forma distinta en cada
  ropa, y los bordes semitransparentes del pelo frontal dejan traslucir
  los ojos). Corregido a canónico POR ROPA + máscara del pelo sin los
  bboxes de ojos/nariz/boca (parche_d6_tanda8.py) y recalculado: 0 px.
  El log detectar.log aún contiene la salida de la primera pasada; el
  resultado válido es reporte.json tras el parche. D6 debe usar siempre
  el canónico de la misma ropa.
- D7: 0 px en los 225 combos.
- REVISIÓN RETROACTIVA: D6 y D7 pasados sobre los 1.575 renders de las
  tandas 1-7 (sin re-renderizar, sin modificarlos): 0 sospechosos D6 y
  0 sospechosos D7 en las 7 tandas. No hay calvas, pelo movido, manchas
  ni trazos raros escondidos en las tandas 1-7. Resultado en
  barrido_tanda8/retro_tandas1-7.json.
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11); azules
  en pelo 0 px; disco ámbar intacto (racimo cálido por ojo con este pelo:
  E1 32, E2 32, E3 39, E4 32, E5 33, desv. máx. 1,0; iris uniforme
  verificado a ojo en E1 y E5); ojos y bocas presentes en los 225.
- Reporte: diagnostico_usuario/barrido_tanda8/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 9 del barrido completo (mujeres, pelo 9)
- 225 renders en el navegador MCP (F, Hair9 Hime Cut, flequillo recto,
  mechones laterales largos hasta la mandíbula y pelo largo por detrás;
  ropa 0-2 × ojos 0-4 × nariz 0-2 × boca 0-4; colores por defecto),
  1200×1600, ~1 s por combo (164 s en total). Servidor.py respondía 200
  al empezar; no hizo falta relanzarlo.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7, las 9 planchas revisadas visualmente.
  Los 225 "sospechosos" eran solo D4 (trazos sueltos): 3 componentes
  distintos (525 px en total), todos arte ya conocido, NINGUNO nuevo
  (línea vertical mandíbula-cuello, sombra de la esquina de la boca,
  borde de cuello de la capucha O3). D1, D2, D3, D5, D6 y D7 no
  marcaron nada.
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11); azules
  en pelo 0 px; disco ámbar intacto (racimo cálido por ojo con este pelo:
  E1 36, E2 36, E3 39, E4 36, E5 36, desviación 0,0; el Hime Cut tapa
  parte de la esquina interior del iris, como los pelos 1 y 3; iris
  uniforme verificado a ojo en E1 y E5); ojos y bocas presentes en los
  225; calvas/pelo movido (D6) 0 px; manchas/trazos raros en todo el
  retrato (D7) 0 px.
- Nota de método: al adaptar los scripts de la tanda 8 con sed, el
  codigo() usaba 'F H8' (con espacio) y el sed solo reemplazó 'F_H8',
  así que la primera pasada del reporte salió con códigos "F H8". Se
  detectó, se corrigieron los dos scripts y se re-corrió la detección
  completa; los números son idénticos y el reporte final tiene 225
  códigos H9 y 0 códigos H8 (verificado). En las tandas siguientes,
  verificar el string del código tras el sed antes de correr.
- Reporte: diagnostico_usuario/barrido_tanda9/ (reporte.json, renders,
  planchas, revision/). Nada del proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 10 del barrido completo (mujeres, pelo 10)
- 225 renders en el navegador MCP (F, Hair10 Messy Bun, moño alto
  despeinado; ropa 0-2 × ojos 0-4 × nariz 0-2 × boca 0-4; colores por
  defecto), 1200×1600, ~1 s por combo. Servidor.py estaba caído al
  empezar y se relanzó con nohup (responde 200).
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7, las 9 planchas revisadas visualmente.
  Los 225 "sospechosos" eran solo D4 (trazos sueltos): 7 componentes
  distintos, todos arte ya conocido, NINGUNO nuevo (sombra esquina de
  la boca, mota de sombra de la mandíbula, línea/sombra junto a la
  oreja, borde derecho mandíbula/cuello, borde cuello capucha O3).
  D1, D2, D3, D5, D6 y D7 no marcaron nada.
- Confirmado limpio: lunares reales 0 (450 falsas alarmas §11, 2 por
  combo); azules en pelo 0 px; disco ámbar intacto (racimo cálido por
  ojo con este pelo: E1 27, E2 10, E3 39, E4 20, E5 36, desviación 0,0;
  E2 es el valor más bajo hasta ahora porque el moño despeinado tapa
  más de su esquina interior; iris uniforme); ojos y bocas presentes en
  los 225; calvas/pelo movido (D6) 0 px; manchas/trazos raros en todo el
  retrato (D7) 0 px.
- Lección de la tanda 9 aplicada: tras el sed se corrigieron a mano los
  restos 'Hair9_Front/Back' y 'tanda': 9; reporte final con 225 códigos
  H10 y 0 códigos H9 (verificado).
- Reporte: diagnostico_usuario/barrido_tanda10/ (reporte.json, renders,
  planchas; revision/ vacía: no hubo sospechosos nuevos). Nada del
  proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 11 del barrido completo (mujeres, pelo 11)
- 225 renders en el navegador MCP (F, Hair11 Side Ponytail, coleta
  lateral; ropa 0-2 × ojos 0-4 × nariz 0-2 × boca 0-4; colores por
  defecto), 1200×1600, ~1 s por combo.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7, las 9 planchas revisadas visualmente.
  Los 225 "sospechosos" eran solo D4 (trazos sueltos): 8 componentes
  distintos, todos arte ya conocido, NINGUNO nuevo (sombra esquina de
  la boca, mota de sombra de la mandíbula, línea/sombra junto a la
  oreja, línea vertical mandíbula-cuello, borde cuello capucha O3,
  borde derecho mandíbula/cuello). El borde derecho reaparece como
  componente aparte porque Hair11_Front no cubre esa zona (0/217 px
  con alfa>30), mientras Hair10_Front sí la cubría (84/217 px) — es
  arte de la Base, no defecto. D1, D2, D3, D5, D6 y D7 no marcaron nada.
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11, 1 por
  combo); azules en pelo 0 px; disco ámbar intacto (desviación máx.
  0,0 px respecto a la mediana calibrada por ojo con este pelo);
  ojos y bocas presentes en los 225 (ojos mín. 99,7 % de la mediana,
  boca 100 %); calvas/pelo movido (D6) 0 px; manchas/trazos raros en
  todo el retrato (D7) 0 px.
- Reporte: diagnostico_usuario/barrido_tanda11/ (reporte.json, renders,
  planchas; revision/ vacía: no hubo sospechosos nuevos). Nada del
  proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 12 del barrido completo (mujeres, pelo 12)
- 225 renders en el navegador MCP (F, Hair12 Long Curly, pelo largo
  rizado; ropa 0-2 × ojos 0-4 × nariz 0-2 × boca 0-4; colores por
  defecto), 1200×1600, ~1 s por combo. Servidor.py respondía 200 al
  empezar; no hizo falta relanzarlo.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7, las 9 planchas revisadas visualmente.
  Los 225 "sospechosos" eran solo D4 (trazos sueltos): 2 componentes
  idénticos en los 225 renders, ambos arte conocido de la mandíbula
  (mota de sombra x580-601 y701-720, 51 px; línea y sombra junto a la
  oreja x688-719 y727-777, 188 px), verificados con zoom en el render
  canónico. D1, D2, D3, D5, D6 y D7 no marcaron nada.
- Confirmado limpio: lunares reales 0 (225 falsas alarmas §11, 1 por
  combo); azules en pelo 0 px; disco ámbar intacto (desviación 0 px en
  los 5 ojos, calibrado con este pelo); ojos y bocas presentes en los
  225 (no vacío 1,22–1,23 M px); calvas/pelo movido (D6) 0 px;
  manchas/trazos raros en todo el retrato (D7) 0 px.
- Con esta tanda quedan COMPLETAS las 12 tandas de mujer (pelos 1-12),
  todas limpias salvo los 3 arreglos de la tanda 0 (pendientes de subir).
- Reporte: diagnostico_usuario/barrido_tanda12/ (reporte.json, renders,
  planchas, revision/zoom_mandibula_F_H12_O1_E1_N1_M1.png). Nada del
  proyecto modificado en esta tanda.

## 2026-11-22 — Tanda 13 del barrido completo (hombres, pelo 1)
- 540 renders en el navegador MCP (M, Hair1 «Style 1»; ropa 0-2 × ojos
  0-4 × nariz 0-2 × boca 0-2 × vello 0-3 None/Mustache/Stubble/Full
  Beard; colores por defecto), 1200×1600, ~1 s por combo. Vello
  verificado que cambia de verdad (bigote 2.174 px, barba incipiente
  7.195 px, barba completa 69.473 px) y sexo Male confirmado visualmente.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7 adaptados a hombres (D1/D4 excluyen la zona
  del vello; D6/D7 con canónico por ropa+vello; la textura de la barba
  es arte). Las 22 planchas revisadas visualmente.
  Los 540 "sospechosos" eran solo arte: D4 4 componentes repetidos y
  D1 2 falsas alarmas §11, revisados con zoom. D2, D3, D5, D6 y D7 no
  marcaron nada.
- Arte de hombre identificado (guardado en reporte.json →
  resumen.arte_bboxes_hombre, para las tandas 14-16): borde derecho
  mandíbula/cuello (829,829,853,899, 540 renders), línea y sombra junto
  a la oreja (678,721,702,768, 405; FH3 la tapa), línea del mentón
  (347,818,365,859, 405; FH3 la tapa), borde inferior mandíbula/cuello
  con la ropa (481,892,506,899, 180; solo FH0/FH1, O1/O3), contorno/
  sombra inferior de la mandíbula D1 (364,860,373,891 y 502,869,551,891,
  180 cada uno). Los componentes de arte de mujer (sombra esquina de la
  boca, mota de sombra de la mandíbula, línea vertical mandíbula-cuello,
  borde cuello-capucha O3) NO aparecen en hombres.
- VERIFICACIÓN DEL ARREGLO DEL STAGE20: la barba completa FH3 (Facial-
  Hair3) NO tiene grietas ni huecos: 0 px claros dentro del núcleo de
  la barba (77.947 px) en 3 renders de muestra, 100 % de solape oscuro;
  la línea fina curva es arte (también en la referencia corregida del
  stage20, barba_FH3.png). Verificado también por mí a ojo en el zoom.
- Confirmado limpio: lunares reales 0 (360 falsas alarmas §11, mandí-
  bula); azules en pelo 0 px; disco ámbar sin desviaciones >25 px de la
  mediana por ojo; ojos y bocas presentes en los 540 (mínimos ≈
  medianas); calvas/pelo movido (D6) 0 px; manchas/trazos raros en todo
  el retrato (D7) 0 px.
- Reporte: diagnostico_usuario/barrido_tanda13/ (reporte.json, renders,
  planchas, revision/ 7 zooms). Nada del proyecto modificado en esta
  tanda.

## 2026-11-23 — Tanda 14 del barrido completo (hombres, pelo 2)
- 540 renders en el navegador MCP (M, Hair2 «Style 2»; ropa 0-2 × ojos
  0-4 × nariz 0-2 × boca 0-2 × vello 0-3 None/Mustache/Stubble/Full
  Beard; colores por defecto), 1200×1600, ~1 s por combo. Vello
  verificado visualmente antes de seguir (FH0 sin vello, FH1 bigote,
  FH2 barba corta, FH3 barba completa) y sexo Male confirmado.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7 adaptados a hombres. Las 22 planchas
  revisadas visualmente. Los 540 "sospechosos" eran solo arte: D4
  1.305 px en 5 grupos (línea del mentón, borde derecho mandíbula/
  cuello, borde inferior mandíbula-cuello), todos arte conocido,
  revisados con zoom. D1, D2, D3, D5, D6 y D7 no marcaron nada.
- Diferencias con la tanda 13: la línea junto a la oreja NO aparece
  con Hair2 (el pelo tapa esa zona); el borde derecho de la mandíbula
  empieza en y=816 (antes 829) y SE PARTE en dos componentes solo en
  la ropa O3 ((828,816,835,849) + (836,850,854,899)) por el cruce del
  cuello de la chaqueta — verificado con zoom, es la misma línea de
  contorno, no un defecto. Bboxes nuevos añadidos en
  reporte.json → resumen.arte_bboxes_hombre.
- VERIFICACIÓN DEL ARREGLO DEL STAGE20: la barba completa FH3 NO tiene
  grietas ni huecos: 0 px claros dentro del núcleo de la barba
  (71.710 px) en 3 renders de muestra; la línea fina curva es arte.
  Verificado también por mí a ojo en el zoom.
- Confirmado limpio: lunares reales 0 (360 falsas alarmas §11); azules
  en pelo 0 px; disco ámbar sin desviaciones >25 px de la mediana por
  ojo; ojos y bocas presentes en los 540; calvas/pelo movido (D6) 0 px;
  manchas/trazos raros en todo el retrato (D7) 0 px.
- Nota de método: al adaptar los scripts con sed hubo que corregir dos
  cosas antes de correr: `FacialHair1` se había convertido en
  `FacialHair2` en VELLO_N, y el sed `tanda.: 13` corrompió la línea
  `{'tanda': 13, ...}`. Verificado después: sintaxis OK, sin restos de
  H1/Hair1/tanda13.
- Reporte: diagnostico_usuario/barrido_tanda14/ (reporte.json, renders,
  planchas, revision/ 6 zooms). Nada del proyecto modificado en esta
  tanda.

## 2026-11-23 — Tanda 15 del barrido completo (hombres, pelo 3)
- 540 renders en el navegador MCP (M, Hair3 «Style 3»; ropa 0-2 × ojos
  0-4 × nariz 0-2 × boca 0-2 × vello 0-3 None/Mustache/Stubble/Full
  Beard; colores por defecto), 1200×1600, ~1 s por combo. Vello
  verificado a ojo en los 4 valores y sexo Male confirmado.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7 adaptados a hombres. Las 22 planchas
  revisadas visualmente. Los 540 "sospechosos" eran solo D4 (trazos
  sueltos): 1.530 componentes en 4 grupos, todos arte de la Base
  verificado con zoom. D1, D2, D3, D5, D6 y D7 no marcaron nada.
- Novedades de arte con Hair3: el pelo 3 tapa el tramo superior del
  borde derecho de la mandíbula (y 816-849), así que ese borde ya no
  aparece ni como pieza única ni partido en O3 — solo queda el tramo
  inferior (835,850,853,899) en los 540; y la línea junto a la oreja
  (678,721,702,768) REAPARECE con Hair3 (en tanda 14 con Hair2 no
  aparecía; en tanda 13 con Hair1 sí).
- VERIFICACIÓN DEL ARREGLO DEL STAGE20: la barba completa FH3 NO tiene
  grietas ni huecos: las 14 grietas del stage20 NO reaparecieron (zoom
  + D7 0 px en los 135 renders FH3). Verificado también por mí a ojo en
  el zoom.
- Confirmado limpio: lunares reales 0 (360 falsas alarmas §11 en 2
  bboxes de mandíbula); azules en pelo 0 px; disco ámbar sin desvia-
  ciones >25 px de la mediana con este pelo en ningún ojo; ojos y bocas
  presentes en los 540; calvas/pelo movido (D6) 0 px; manchas/trazos
  raros en todo el retrato (D7) 0 px.
- Incidencia: la primera pasada de detectar_tanda15.py fue interrumpida
  por un reinicio del runtime (~8,5 min, sin reporte.json porque el
  script solo escribe al final — nada parcial que rescatar); se relanzó
  desde cero y terminó bien.
- Reporte: diagnostico_usuario/barrido_tanda15/ (reporte.json, renders,
  planchas, revision/ 5 zooms). Nada del proyecto modificado en esta
  tanda.

## 2026-11-23 — Tanda 16 del barrido completo (hombres, pelo 4)
- 540 renders en el navegador MCP (M, Hair4 «Style 4», pelo corto
  rizado; ropa 0-2 × ojos 0-4 × nariz 0-2 × boca 0-2 × vello 0-3
  None/Mustache/Stubble/Full Beard; colores por defecto), 1200×1600,
  ~1 s por combo. Servidor.py estaba caído al empezar y se relanzó
  (responde 200). Vello verificado a ojo y sexo Male confirmado.
- **0 defectos reales. Errores arreglados en esta tanda: 0.**
- Controles ampliados D1-D7 adaptados a hombres. Las 22 planchas
  revisadas visualmente. Los 540 "sospechosos" eran solo arte: D4
  1.305 trazos en 5 grupos, todos arte de la Base verificado con zoom.
  D1, D2, D3, D5, D6 y D7 no marcaron nada.
- Novedad de arte con Hair4: el borde derecho de la mandíbula es
  pieza única (828,824,853,899) en O1/O2 y partido en O3; el pelo tapa
  un poco más arriba que con Hair2 (y0 824 vs 816) y mucho menos que
  con Hair3 (que tapaba hasta y850). La línea junto a la oreja NO
  aparece con Hair4 en ningún render (el pelo la tapa por completo,
  igual que con Hair2).
- VERIFICACIÓN DEL ARREGLO DEL STAGE20: la barba completa FH3 NO tiene
  grietas ni huecos: las 14 grietas del stage20 NO reaparecieron (135
  renders FH3, zoom verificado). Verificado también por mí a ojo en el
  zoom.
- Confirmado limpio: lunares reales 0 (360 falsas alarmas §11); azules
  en pelo 0 px; disco ámbar sin desviaciones >25 px de la mediana con
  este pelo en ningún ojo; ojos y bocas presentes en los 540; calvas/
  pelo movido (D6) 0 px; manchas/trazos raros en todo el retrato (D7)
  0 px.
- Con esta tanda quedan COMPLETAS las 4 tandas de hombre (pelos 1-4),
  todas limpias, y las 12 de mujer también. Solo falta la tanda 17
  (colores).
- Reporte: diagnostico_usuario/barrido_tanda16/ (reporte.json, renders,
  planchas, revision/ 3 zooms). Nada del proyecto modificado en esta
  tanda.

## 2026-11-23 — Tanda 17 del barrido completo (COLORES, última)
- 555 renders en el navegador MCP (1200×1600, ~537 s): A) pelo mujer
  12 pelos × 24 colores = 288; B) ojos mujer 5 × 7 colores = 35; C) ropa
  mujer 3 × 24 colores = 72; D) pelo hombre 4 × 24 colores = 96; E) piel
  mujer 4 tonos × 12 pelos = 48; F) piel hombre 4 tonos × 4 pelos = 16.
  Las 28 planchas revisadas visualmente + zooms de veredicto.
- **1 DEFECTO REAL ENCONTRADO Y ARREGLADO (T17-01): la solapa/cuello de
  Outfit1 mujer estaba dibujada en la capa Base, no en Outfit1.** No
  seguía el tinte de ropa y sí el de piel: con Royal Blue el jersey era
  azul vivo y la solapa seguía salvia/gris; con piel Deep la solapa se
  oscurecía a marrón. Evidencia: píxel (520,1100) = (122,118,108) con
  OC00 White y con OC16 Coral (crudo Base exacto); con SK3 Deep =
  (76,54,36) = crudo × tinte Deep. Tamaño: solapa estricta 5.757–13.095
  px según el pelo; banda aprox. x430–650, y950–1200. Afectaba a 395
  renders (todas las mujeres con O1); visible con claridad en 59 y sutil
  con los valores por defecto — por eso las tandas 1–16 no lo vieron.
  Además, la pieza derecha de esa solapa (973 px) asomaba por Outfit2
  («Green Jacket»), que no la cubre del todo: mismo defecto en O2.
- **Corrección (método stage20, script herramientas/tanda17_fix.py):**
  snapshot ANTES en versiones/2026-11-23_tanda17-antes-fixes/ (md5
  verificado). Solapa (14.174 px) copiada tal cual de Base a Outfit1
  (White/Light son tinte neutro [1,1,1]); hueco en Base rellenado con
  piel inpaintada (difusión de Laplace enmascarada, solo desde piel);
  hueco de Outfit2 (973 px) rellenado con el verde del cuello de la
  chaqueta vecina. Asserts: 0 px cambiados fuera de la solapa (Base y
  Outfit1) y fuera del hueco (Outfit2); solapa copiada idéntica.
  Archivos: Base, Outfit1 y Outfit2 de Female (md5 nuevos en
  reporte.json → resumen.correccion).
- **Verificación post-arreglo (herramientas/tanda17_verificar.py +
  navegador):** O1 por defecto BYTE-IDÉNTICO al pre-fix (maxdiff 0);
  O1 Royal Blue: solapa (520,1100) = (37,50,92) exacto, 11.258 px
  difieren todos dentro de la solapa; O1 Deep: solapa (122,118,108)
  exacto (ya no sigue la piel); O2 Royal Blue: hueco azul (19,27,42),
  sin franja salvia; O3 sin cambios salvo 40 px de borde
  semitransparente. Re-render en el navegador (V1/V2/V3): mismos valores
  exactos, V3 default byte-idéntico. Zooms en
  diagnostico_usuario/barrido_tanda17/revision/zoom_fix_*.png. 0 px de
  piel nueva en el pecho.
- Confirmado limpio (160 renders): tinte de pelo cubre frente+espalda en
  los 24 colores y 12 pelos; iris uniforme en los 7 colores de ojos, sin
  disco ámbar; O2 y O3 cubren completos (salvo el hueco ya arreglado);
  piel uniforme, nariz sigue el tinte; 0 lunares reales. No-defectos
  clasificados: reflejos claros del pelo, hebras del arte, patilla de
  hombre (arte), 113 flags D3 de hombre = artefacto de calibración
  (calibrar D3-EC0 por sexo+ojos la próxima vez).
- **Errores arreglados en esta tanda: 2 (T17-01 y T17-02).** BARRIDO COMPLETO
  TERMINADO (tandas 0–17). Total general: 5 errores arreglados
  (tanda 0: 3, tanda 17: 2; tandas 1–16: 0).
- **T17-02 (hallado 2026-11-23 ~03:00 por Dani en revisión visual propia
  del fix T17-01, con zoom):** Female Outfit1 y Outfit2 tenían agujeros
  interiores (alfa 0) dentro de la silueta de la prenda por los que se veía
  la piel de Base: motas beige sobre el jersey (O1: 817 px, 46 comp.,
  mayores 277 y 213 px, en la línea de pliegue izquierda; O2: 302 px,
  68 comp., mayor 46 px, motas sobre la camisa blanca). Evidencia: píxel
  (389,1391) en O1 Royal Blue = (190,172,158) = Base exacto con Outfit1
  alfa 0. El barrido no lo detectó porque el defecto está horneado en la
  capa (también en el canónico de D7). **Fix (herramientas/
  tanda17b_fix_huecos.py, snapshot versiones/2026-11-23_tanda17b-antes-
  huecos/):** 1.119 px rellenados con la prenda vecina (Laplace, 500 it.),
  alfa 255; asserts 0 px fuera de las máscaras. **Verificado en motor
  (5 renders) y navegador (3 renders, verificacion_postfix_t17b/):**
  0 px de piel en la zona del parche (antes 151), 0 px de piel en los
  817 px de agujero, colores en agujeros azul Royal; navegador vs motor
  en agujeros maxdiff 10 (V1) y 9 (V3). Nuevos md5: Outfit1
  3024315b62e20d061b3ead506f5b4bad, Outfit2
  3bd789cad4e1b32aceffa5f22ff5f7b2. Los agujeros de pelo/ojos/barba son
  diseño (hebras, construcción del ojo, textura de barba) y NO se tocaron;
  Outfit3 y hombre (motas de 1 px) son ruido y NO se tocaron.
- **SUBIDO 2026-11-23 ~08:00 por orden de Stiven («Sí, súbelo a GitHub y
  Drive»):** GitHub commit
  `eb0eb6e40ada6fd998986d543c422bb1945f4889` (159 archivos, 0 diferencias
  blob verificado; Outfit1 y Base confirmados por raw.githubusercontent.com)
  y Drive/Unity 6/6 verificados por md5 re-descargado (script
  herramientas/sweep_subir_drive.py). **GitHub = Drive/Unity = barrido
  completo (Linux + stage20 + 5 fixes).** OJO: el staging inicial de 97
  archivos NO incluía unity/ (62 archivos: 60 EyesColor + README +
  PortraitCreator.cs) y el doc del conector no lo listaba; se añadió
  antes de subir — sin eso el commit habría BORRADO unity/ del repo.
  PortraitCreator.cs local = blob del repo (65fe7f34...), sin cambios.
  Que Stiven deje sincronizar Drive y reabra Unity.
- Reporte: diagnostico_usuario/barrido_tanda17/ (reporte.json con las
  dos correcciones registradas, renders, planchas, revision/ 17+6 zooms,
  verificacion_postfix/ 3 renders de navegador T17-01,
  verificacion_postfix_t17b/ 3 renders de navegador T17-02).
- **Tanda 18 (colores hombre, cierra el hueco de la tanda 17) TERMINADA
  2026-11-23 ~08:29: 75 renders en el navegador MCP (72: outfits O1/O2/O3
  de hombre × 24 colores de ropa, piel Light; + 3 controles White con
  piel Deep). 0 ERRORES REALES.** D-EXACT ropa 0 px y D-EXACT-CRUCE 0 px
  (toda la prenda cambia con el color); D-PIEL-CRUCE 0 px, maxdif 0.0
  (la prenda es idéntica entre piel Light y Deep: nada de la ropa está
  en Base); T17-02 0 px de agujeros con piel. 9 sospechosos, todos
  no-defectos: patilla (arte conocido, mismo bbox que tanda 16), pelo
  semi-transparente sobre outfit/piel (composición, alfa 201–245),
  borde semi-transparente de la capucha O2 (artefacto de máscara),
  D-LAPEL O2 540 px = líneas finas del contorno de la mandíbula y sombra
  del cuello (arte de Base, no pieza de ropa; verificado por Dani con el
  mapa), tela beige de O3 (color propio del outfit, no piel). 4 planchas
  revisadas por Dani (O2 en 24 colores tiñe uniforme; controles Deep:
  piel oscura, ropa idéntica). Reporte:
  diagnostico_usuario/barrido_tanda18/ (reporte.json, renders, planchas,
  revision/). **Nada que subir: 0 archivos cambiados.**
- **Tanda 19 (lunares en boca y nariz) TERMINADA 2026-11-23 ~09:15: hallado
  por Stiven viendo el vídeo de 1 min (randomize): lunares en boca y nariz
  en hombres y mujeres. Diagnóstico: (1) NARIZ: Nose2 (mujer y hombre) tiene
  una "coma" oscura gruesa en la punta (F 103 px, M 112 px) que se lee como
  lunar; Nose1 hombre tiene 7 motitas sueltas alrededor de la fosa (32 px);
  Nose1 mujer una motita en la piel junto a la nariz (5 px). (2) BOCA: la
  sombra de la comisura + borde inferior del labio en la capa Base (ambos
  sexos) forman una mancha negra en la esquina de la boca en TODOS los
  combos; además ticks sueltos en Mouth_Happy (F 12 px, M 13 px) y un trazo
  suelto bajo Mouth_Neutral hombre (15 px). Los 6 combos registrados del
  vídeo tenían lunar en nariz Y en boca: 00 F H1 N1 M1, 05 F H2 N2 M2
  (la coma de Nose2, la más visible), 10 M H3 N1 M3, 15 F H11 N2 M5,
  20 M H2 N1 M3, 25 F H7 N1 M4. Fix (herramientas/tanda19_fix_lunares.py,
  snapshot versiones/2026-11-23_tanda19-antes-lunares/): 300 px borrados
  (comas + motitas + ticks) y 304 px aclarados (Base comisura/borde,
  mezcla 60% hacia piel local, se conserva la forma como sombra suave).
  10 capas: F/M Base, F Nose1/2/3, M Nose1/2, F Mouth_Happy, M Mouth_Happy,
  M Mouth_Neutral. Verificado (herramientas/tanda19_verificar.py):
  re-escaneo 0 objetivos restantes; 6/6 combos re-renderizados, diferencias
  SOLO en las zonas objetivo (los 71+121 px "fuera de zona" de los combos
  de hombre son la esquina de Base hombre, que está más a la izquierda;
  zonas de verificación dibujadas para la cara de mujer); zooms 4x
  antes/después revisados por Dani (nariz limpia, esquina suave, boca
  Sorprendido intacta por orden de Stiven). NO se tocó: línea de la nariz,
  fosa nasal fina (Nose1 22 px, Nose3 81 px), línea de la boca, cuña de la
  comisura propia de cada boca, línea de la barbilla. PENDIENTE: subir a
  GitHub + Drive cuando Stiven lo ordene (10 archivos). Reporte:
  diagnostico_usuario/lunares_boca_nariz/ (escaneo, composites por
  boca/nariz, combos_video/ y combos_video_postfix/ con zooms 4x,
  antes_despues_nariz_05.png y antes_despues_boca_05.png).**
- **Tanda 19b (CAUSA RAÍZ de los puntos café en bocas) TERMINADA 2026-11-23
  ~09:40: orden de Stiven («encuéntrame como sea la causa raíz... si no,
  seguirá apareciendo en nuevos combos»). Causa raíz probada: la capa Base
  trae una "BOCA FANTASMA" — restos de la boca original que quedó en la
  cara al separar en capas: una línea de boca rota en segmentos, manchas
  de sombra del labio y (hombre) un bloque gris manchado en la esquina de
  la boca, justo donde va la boca real. Cada render superpone la boca real
  sobre esa fantasma y los pedacitos rotos se leen como puntos/lunares
  café. Está en Base → aparece en TODOS los combos de ese sexo, con
  cualquier boca y nariz → por eso seguían apareciendo en combos nuevos.
  La Tanda 19 no la vio porque solo buscaba píxeles casi negros (gris<100);
  la fantasma es marrón medio (gris 100-205). Prueba: render de las 24
  bocas×narices (271 clusters café, los mismos en todos los combos, todos
  con origen en Base) + zoom de Base sola mostrando la línea fantasma y el
  bloque gris. Fix (herramientas/tanda19b_fix_fantasma.py + _v2.py, snapshot
  versiones/2026-11-23_tanda19b-antes-fantasma/): v1 inpaint con piel
  (F 433 px + mezcla 342 px; M 680 px + mezcla 214 px); v2 (núcleos oscuros
  que la máscara café no incluía + relleno que salió marrón por vecinos
  marrones) inpaint de todos los píxeles oscuros + mezcla 80% hacia piel
  de mejilla (F 330 px, M 1007 px). Solo cambian las 2 capas Base
  (F md5 f5ba606a35fe5bfcf8a60c40d3086412, M md5 2368d4e27918ecf748149de8a750407b).
  Lección: el assert «todos los objetivos cambian» era demasiado estricto
  (un píxel objetivo puede quedar igual tras el inpaint); el correcto es
  «nada cambia fuera de los objetivos». Lección 2: los píxeles RGB (0,0,0)
  con alfa 0 son transparentes y NO se ven en el render (la sonda inicial
  los contó como líneas negras). Verificado
  (herramientas/tanda19b_verificar.py): Base sola compuesta = piel limpia,
  fantasma desaparecida; 6/6 combos del vídeo re-renderizados con recetas
  completas, diferencias SOLO en las zonas objetivo (0 px fuera); las capas
  Mouth son líneas finas limpias (la punta de la boca Neutral es la comisura
  del labio, diseño). Quedan solo sombras suaves (medianas ~214-226, casi
  piel), sombreado normal, no lunares. **SUBIDO 2026-11-23 ~09:57 por orden
  de Stiven («Sí, súbelo a GitHub y Drive»): GitHub commit
  198603ccc722ab2ec9d89879fd6c057b4b755f3a (168 archivos, verificado 168/168
  blobs + Base F/M por raw.githubusercontent.com) y Drive/Unity 10/10
  verificado por md5 (las 2 Base + Nose1/2/3 F, Nose1/2 M, Mouth_Happy F/M,
  Mouth_Neutral M). GitHub = Drive/Unity = T19 + T19b.** Reporte:
  diagnostico_usuario/lunares_boca_nariz/causa_raiz/ (sonda 24 combos,
  zooms Base sola antes/después, combos post-19b).**
- **Ciclo 1 de 7 (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces grabar
  vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,16 s, 13 combos
  (5 mujer + 5 hombre + 2 mujer + default). Revisión: 13/13 frames vistos
  por Dani + renders motor de los 13 combos + escaneos a nivel de capa
  (café y oscuro en Base/narices/bocas, agujeros interiores en prendas,
  blue-cast en pelo) + comparación motor vs vídeo (dif media 8-14 = compresión
  VP9 + alineación; clusters dif>60 máx 1510 px, todos en bordes de pelo o
  del lienzo; ojo del combo 00 verificado a 4x, iris verde igual). Resultado:
  0 ERRORES. Solo arte conocido (lavados de nariz, líneas de boca, óvalo
  Sorprendido, sombras suaves de comisura, lavado marrón de nariz hombre,
  motas de 1 px en prendas). Blue-cast 0 px. Nada que arreglar, nada que
  subir. Reporte: diagnostico_usuario/ciclos/ciclo1/reporte.json.**
- **Ciclo 2 de 7 (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces grabar
  vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,16 s, 13 combos
  (5 mujer + 5 hombre + 2 mujer + default). Revisión: 14/14 retratos vistos
  por Dani (13 frames + default, que solo se ve en vídeo t≈3,5) + renders
  motor de los 13 combos + escaneos a nivel de capa (café y oscuro en
  Base/narices/bocas, agujeros interiores en prendas, blue-cast en pelo) +
  comparación motor vs vídeo con la geometría real del lienzo (552x736 en
  (16,16): dif media 3,3-5,3; dif>60 total 6-170 px dispersos, 0 clusters
  ≥100 px). Frame_00 y frame_01 muestran ambos el combo #1 (la extracción
  t+1,5 cae en el límite del hold). Resultado: 0 ERRORES. Solo arte conocido
  (lavados de nariz y puente nasal, lavado marrón de nariz hombre, línea de
  mandíbula, ceja, comisura, óvalo Sorprendido, sombra suave del cuello +
  ribete teñido con el color de la prenda, motas de 1 px en prendas).
  Blue-cast 0 px. Nada que arreglar, nada que subir. Nota: la comparación
  sin alinear (600x800 en (0,0), como en ciclo 1) infla la dif con clusters
  falsos de ~12k px en bordes de pelo; no usarla. Reporte:
  diagnostico_usuario/ciclos/ciclo2/reporte.json.**
- **Ciclo 3 de 7 (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces grabar
  vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,4 s, 13 combos
  (5 mujer + 5 hombre + 2 mujer + default). Revisión: 13/13 frames vistos
  por Dani + default verificado aparte (t=3,5, dif 2,5) + renders motor de
  los 13 combos + escaneos a nivel de capa (café y oscuro en Base/narices/
  bocas, agujeros interiores en prendas, blue-cast en pelo) + comparación
  motor vs vídeo con la geometría real del lienzo (552x736 en (16,16):
  dif media 2,5-3,5; dif>60 total 2-173 px dispersos, mayor cluster 8 px;
  13/13 frames con mejor match = su propio combo). La extracción a mitad
  real del hold corrigió el problema del ciclo 2: frame_00 ya muestra el
  default (no duplica el combo #1). Escaneos idénticos al ciclo 2 (capas
  sin cambios desde T19b); Base F/M limpias, sin rastro de boca fantasma.
  Resultado: 0 ERRORES. Solo arte conocido (lavados de nariz y puente
  nasal, lavado marrón de nariz hombre, línea de mandíbula, ceja, comisura,
  óvalo Sorprendido en 05 y 09, sombra suave del cuello + ribete teñido con
  el color de la prenda, motas de 1 px en prendas). Sospechosos revisados a
  4x y no arreglados (diseño): líneas rojizas de costura del hoodie en
  03/05/12 = arte horneado de Outfit3 F (capa sola idéntica al render);
  parche naranja del cuello en 12 = ribete teñido con OC16; banda marrón
  del pecho en 04 = sombra de la abertura de la camisa de Outfit2. Blue-cast
  0 px. Nada que arreglar, nada que subir. Reporte:
  diagnostico_usuario/ciclos/ciclo3/reporte.json.**
- **Ciclo 4 de 7 (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces grabar
  vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,28 s, 13 combos
  (5 mujer + 5 hombre + 2 mujer + default). Revisión: 13/13 frames vistos
  por Dani + renders motor de los 13 combos + escaneos a nivel de capa
  (café y oscuro en Base/narices/bocas, agujeros interiores en prendas,
  blue-cast en pelo) + comparación motor vs vídeo con la geometría real del
  lienzo (552x736 en (16,16): dif media 2,3-3,6; dif>60 total 1-75 px
  dispersos, mayor cluster coherente 5 px; 13/13 frames con mejor match =
  su propio combo). Escaneos idénticos al ciclo 3 (capas sin cambios desde
  T19b); Base F/M limpias, sin rastro de boca fantasma. Blue-cast 0 px en
  los 10 pelos usados. Resultado: 0 ERRORES. Solo arte conocido (lavados de
  nariz y puente nasal, lavado marrón de nariz hombre, línea de mandíbula,
  ceja, comisura, óvalo Sorprendido en 02/08/09/10, sombra suave del cuello
  + ribete teñido con el color de la prenda, motas de 1 px en prendas).
  Sospechosos revisados a 3x motor vs vídeo y no arreglados (diseño):
  parche naranja del cuello en 03 = ribete teñido con OC16, parche rosa
  del cuello en 12 = ribete teñido con OC17, línea fina vertical en el
  cuello/camisa de 12 = costura de la camisa de Outfit2, motitas de 1 px
  en el cuello en 04, punta de hebra bajo la barbilla en 01 = extremo de
  hebra de Hair7, líneas de costura del hoodie en 03/05. Nada que arreglar,
  nada que subir. Reporte:
  diagnostico_usuario/ciclos/ciclo4/reporte.json.**
- **Ciclo 5 de 7 (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces grabar
  vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,48 s, 13 combos
  (5 mujer + 5 hombre + 2 mujer + default). Revisión: 13/13 frames vistos
  por Dani + renders motor de los 13 combos + escaneos a nivel de capa
  (café y oscuro en Base/narices/bocas, agujeros interiores en prendas,
  blue-cast en pelo) + comparación motor vs vídeo con la geometría real del
  lienzo (552x736 en (16,16): dif media 2,5-3,5; dif>60 total 1-103 px
  dispersos, mayor cluster coherente 7 px; 13/13 frames con mejor match =
  su propio combo). Escaneos idénticos al ciclo 4 (capas sin cambios desde
  T19b); Base F/M limpias, sin rastro de boca fantasma (md5 f5ba606a /
  2368d4e2). Blue-cast 0 px en los 9 pelos usados. Resultado: 0 ERRORES.
  Solo arte conocido (lavados de nariz y puente nasal, lavado marrón de
  nariz hombre, línea de mandíbula, ceja, comisura, óvalo Sorprendido en
  02/04/06/08/09/11, sombra suave del cuello + ribete teñido con el color
  de la prenda, motas de 1 px en prendas). Sospechosos revisados a 4x motor
  vs vídeo y no arreglados (diseño): parche lila/rosa del cuello en 05
  (OC22) y 12 (OC20) y parche pálido en 11 (OC3) = ribete teñido con OC;
  cluster horizontal de 7 px en (168-174, 382) en 07/09/10 = borde
  barba completa/piel, anti-aliasing + VP9, idéntico en motor a 4x;
  líneas de costura del hoodie en 01/02/03/05/09/10/11/12. Pelo rizado
  F H12 (04) y ojos E4 (11) vistos por primera vez en un ciclo, limpios.
  Nada que arreglar, nada que subir. Reporte:
  diagnostico_usuario/ciclos/ciclo5/reporte.json.**
- **Ciclo 6 de 7 (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces grabar
  vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,36 s, 13 combos
  (5 mujer + 5 hombre + 2 mujer + default). Revisión: 13/13 frames vistos
  por Dani + renders motor de los 13 combos + escaneos a nivel de capa
  (café y oscuro en Base/narices/bocas, agujeros interiores en prendas,
  blue-cast en pelo) + comparación motor vs vídeo con la geometría real del
  lienzo (552x736 en (16,16): dif media 2,5-3,5; dif>60 total 1-87 px
  dispersos, mayor cluster coherente 6 px; 13/13 frames con mejor match =
  su propio combo). Escaneos idénticos al ciclo 5 (capas sin cambios desde
  T19b); Base F/M limpias, sin rastro de boca fantasma (md5 f5ba606a /
  2368d4e2). Blue-cast 0 px en los 9 pelos usados. Resultado: 0 ERRORES.
  Solo arte conocido (lavados de nariz y puente nasal, lavado marrón de
  nariz hombre, línea de mandíbula, ceja, comisura, óvalo Sorprendido en
  01/10/12, sombra suave del cuello + ribete teñido con el color de la
  prenda, motas de 1 px en prendas). Sospechosos revisados a 4x motor
  vs vídeo y no arreglados (diseño): parche rosa del cuello en 04
  (OC17) y parche pálido verdoso en 11 (OC12) y parche amarillento en 12
  (OC15) = ribete teñido con OC; cluster de 6 px en (168-173, 382) en 08
  = borde barba completa/piel, anti-aliasing + VP9, idéntico en motor a
  4x; cluster de 3 px en (152-153, 345-346) en 07 y 10 = borde del
  bigote, idéntico en motor a 4x; cluster de 4 px en (242-245, 734) en
  11 = nudo de la trenza en el borde inferior, idéntico en motor a 4x;
  líneas de costura del hoodie en 02/04/06/08/11. Pelo F H7 Long Braid
  (11) y F H8 Double Buns (12) vistos por primera vez en un ciclo,
  limpios. Nada que arreglar, nada que subir. Reporte:
  diagnostico_usuario/ciclos/ciclo6/reporte.json.**
- **Ciclo 7 de 7 — ÚLTIMO (orden de Stiven 2026-11-23 ~10:07: repetir 7 veces
  grabar vídeo 40 s + revisar + arreglar + actualizar): vídeo de 41,32 s,
  13 combos (5 mujer + 5 hombre + 2 mujer + default). Revisión: 13/13 frames
  vistos por Dani + renders motor de los 13 combos + escaneos a nivel de capa
  (café y oscuro en Base/narices/bocas, agujeros interiores en prendas,
  blue-cast en pelo) + comparación motor vs vídeo con la geometría real del
  lienzo (552x736 en (16,16): dif media 2,4-3,7; dif>60 total 0-80 px
  dispersos, mayor cluster coherente 2 px; 13/13 frames con mejor match =
  su propio combo). Escaneos idénticos al ciclo 6 (capas sin cambios desde
  T19b); Base F/M limpias, sin rastro de boca fantasma (md5 f5ba606a /
  2368d4e2). Blue-cast 0 px en los 10 pelos usados. Resultado: 0 ERRORES.
  Solo arte conocido (lavados de nariz y puente nasal, lavado marrón de nariz
  hombre, línea de mandíbula, ceja, comisura, óvalo Sorprendido en 07/10/11/12,
  sombra suave del cuello + ribete teñido con el color de la prenda, motas de
  1 px en prendas). Sospechosos revisados a 4x motor vs vídeo y no arreglados
  (diseño): mancha rosada suave bajo el ojo en 11 y 12 = sombreado suave de
  la mejilla, idéntica en motor y vídeo; punto oscuro en la oreja en 06/08/10
  = ojo lejano entre hebras de pelo / detalle de la oreja de Base M, idéntico
  en motor a 4x; parche lavanda del cuello en 04 (OC21) y parche verdoso en
  05 (OC3) y parche amarillento en 12 (OC15) = ribete teñido con OC; líneas
  de costura del hoodie en 01/03/05. **CICLO DE REVISIÓN POR VÍDEO COMPLETO:
  7/7 ciclos, 0 errores en los 7. Nada que arreglar, nada que subir.**
  Reporte: diagnostico_usuario/ciclos/ciclo7/reporte.json.**

## 2026-11-23 — Boca Sorprendido nueva (variante R, de la referencia de Stiven)
- Stiven reabrió la boca Sorprendido 2026-11-23 10:56: el «circulito» del vídeo
  del ciclo 7 era la boca misma (29x37 px, óvalo rojo). Muestras A/B (vectores)
  rechazadas por parecerse entre sí; referencias de internet; 4 caras
  generadas (mujer círculo, mujer D con dientes, hombre grito, hombre
  dientecito + lengua). Stiven eligió la boca del hombre 2 (dientecito +
  lengua) y confirmó que cambiarla es solo cambiar la capa.
- Variante C (dibujada a mano) RECHAZADA por Stiven 11:26 («muy fea muy mal
  dibujada») y ordenó calcar con Playwright. Variante T (calco de la boca 3/4
  pegado tal cual) RECHAZADA 11:36: se veía como si comiera, con cachetes
  grandes — la boca 3/4 es ancha y el rostro del programa es de perfil.
  Orden: varios métodos con y sin Playwright hasta que quede lo más fiel
  posible, sin entregar nada hasta cumplirlo; adaptar 3/4 a 2D de perfil.
- Variante B (calco de perfil generado, 33x42, diente + lengua): cumplía los
  4 criterios y se presentó a Stiven 11:44, pero antes de que respondiera
  mandó una referencia MUCHO MEJOR (REF_BOCA_ANIME_2.png, chico de perfil
  puro mirando a la izquierda, boca en D con interior oscuro + lengua rosa,
  sin diente) y ordenó usar esa.
- **Variante R (APLICADA): calco de la boca de REF_BOCA_ANIME_2.png**
  (bbox x321-406, y616-716; mismo método que B: solo píxeles oscuros
  lum<110, dilatar 1, componente de mayor solape, rellenar agujeros).
  Boca calcada 84x79 px, escalada a 45x42 px (más ancha que B porque la
  referencia es un jadeo bien abierto). Capas Female_R_layer.png
  (md5 95c8230615335c880c202750e678caa7) y Male_R_layer.png
  (md5 377331947a8178aa56148732189feee7). Verificada en el navegador
  (copia de prueba, renders F H1 O1 E1 N1 M5 / M H1 O1 E1 N1 M3 + zooms 4x):
  se lee como jadeo sorprendido en perfil, cachete plano, sin «comer».
  Presentada a Stiven 11:48; **aprobada 11:52 («aplicala en hombre y mujer»)**.
- Aplicación: snapshot de las bocas viejas en
  `versiones/2026-11-23_boca-sorprendido-R-antes/` (óvalo original:
  F 250255f58fbc405784936f70659fac30, M 304c56db4cf2b9d86b351948e00e85c9).
  Capas R copiadas a `version-linux/assets/{Female,Male}/Mouth_Surprised.png`
  (md5 verificados iguales a las capas R). Verificación en motor con el
  programa real: píxeles de la boca dif media 0.12 (F) / 0.15 (M) contra el
  render del navegador (idéntico).
- **SUBIDA A GITHUB (sin Unity/Drive, por orden de Stiven):** push del árbol
  completo (179 archivos, 179/179 blobs verificados + 2 bocas por
  raw.githubusercontent.com md5) commit
  `a5f709a78a51f506ad466936c5495847ae9696ae`
  (https://github.com/stivenft202/anime-portrait-studio/commit/a5f709a78a51f506ad466936c5495847ae9696ae)
  + release `v2026-11-23-boca-sorprendido-R` con el archivo nuevo
  `boca-sorprendido-R_2026-11-23.zip` (las 2 capas nuevas + NOTA.txt, 10.378
  bytes) — cada nueva versión es un nuevo archivo en GitHub:
  https://github.com/stivenft202/anime-portrait-studio/releases/tag/v2026-11-23-boca-sorprendido-R
  **Actualización 2026-11-23 ~12:54: por orden de Stiven («Sí, sube la
  boca R a Drive/Unity también»), las 2 bocas R subidas a Drive/Unity
  (Female 1MgMpFdnSnV0-V11M-PXgbAPPvwtn23l9, Male
  1kuye8Paw8bLB5Sla516XiHNKVJVdw6Q1), 2/2 verificadas por md5
  (95c82306... / 37733194...). Desde ahora GitHub = Drive/Unity = boca R.**

## 2026-11-23 — SÚPER MÉTODO: escaneo píxel por píxel de las 67 capas (orden de Stiven)
- Stiven mandó 4 capturas de Unity con círculos rojos (13:07): puntito en
  la nariz (2 mujeres), marcas en el cuello, trazos sueltos en pelo y
  ropa, marquitas en los ojos, puntito en la mejilla. Orden: blindarse con
  un súper método potente que detecte hasta el error más mínimo con zoom,
  arreglar todo y grabar vídeo al final. Eligió el método completo en las
  67 capas.
- Combos identificados de sus capturas: C1 `F H7 O3 E1 N3 M1 | HC10 ST2
  OC17 EC3`, C2 `M H4 O2 E1 N2 M1 | HC12 ST2 OC19 EC2 FH0`, C3 `M H2 O1 E5
  N2 M1 | HC1 ST4 OC7 EC3 FH2`, C4 `F H3 O3 E1 N3 M1 | HC22 ST1 OC4 EC5`.
- **El puntito de la nariz era EL MISMO en las dos mujeres: la coma marrón
  de Female Nose3 (81 px, x324-333 y693-707), NO las motitas de 1 px de
  Nose1.** Lección: no borrar a ciegas; la posición en la captura manda.
- Método: escaneo A NIVEL DE CAPA (los renders no ven defectos horneados),
  cuadrícula de celdas 100×100 con zoom 4x + detectores D-STRAY
  (componentes desprendidos oscuros y café medio), D-PROTRUDE
  (protuberancias finas fuera de la silueta), D-SPECK (motitas 1-3 px),
  D-HOLE (agujeros interiores en prendas) + revisión visual de las
  planchas con el propio ojo.
- **Arreglos: 8.966 px en 23 capas** (snapshot previo en
  `versiones/2026-11-23_supermetodo-antes/`, scripts
  `herramientas/supermetodo_*.py`): coma de Nose3 F (89 px), motitas
  Nose1 F (2 px) y M (7 px), rasguño curvo en la mejilla de Base F (176
  px, inpaint), motitas en cuello de Base M (32 px), rayita diagonal fuera
  de la cara en Base M (20 px), fragmento flotante en Base M (5 px),
  trazos sueltos en Hair4 M (219 px), motitas en Eyes_Surprised M (65 px),
  9 fragmentos largos tipo cuchilla en Hair3_Back F (5.233 px),
  trazo suelto en Outfit3 F (48 px), trazos sueltos en Hair2 M (291 px),
  Hair3 F (110 px), Hair1 M (88 px), Hair3 M (237 px), Hair4 F (196 px),
  Hair11 F (73 px), Hair2 F (107 px), Hair1 F (60 px), hilo vertical en
  Outfit2 M (86 px), fragmento en Hair2_Back F (28 px) + **defringe:
  halo blanco/beige en el borde exterior de las 6 ropas (1.559 px,
  artefacto de recorte, clase nueva)** + 234 px de Base M que se
  transparentaba por el borde semitransparente de Outfit2 (umbral
  correcto: silueta OPACA alfa>200, no alfa>0).
- Verificación: las 4 capturas re-renderizadas post-fix, cada marca de
  Stiven eliminada (zooms 4x revisados por el coordinador y por Dani:
  coma de nariz fuera, queda solo sombra suave; mejilla limpia). Detectores
  re-corridos: los componentes arreglados dan 0 candidatos. Control sin
  tinte de ojos: 0 px fuera de objetivo (los 826 px de C3 con tinte son
  redondeo del `_ojos_tinte` del motor, no daño al arte; en Unity el tinte
  usa variantes horneadas, no afecta).
- Dudosos NO arreglados (para el ojo de Stiven): rastro claro muy tenue
  donde estaba el rasguño de la mejilla (invisible a tamaño normal);
  cola inferior del ojo en C3 (conectada, diseño, se lee como gotita);
  ribete del cuello que se tiñe con la ropa (pendiente de decisión).
- Vídeo final: `diagnostico_usuario/videos/video_supermetodo_2026-11-23.webm`
  (41,68 s, 14 combos, todos Sorprendido). PENDIENTE subir a GitHub/Drive
  cuando Stiven lo ordene (23 archivos cambiados).

## 2026-11-23 — RIBETE DEL CUELLO (error que el súper método NO vio; orden implícita de Stiven)
- Stiven (2026-11-23 ~14:55), viendo el vídeo del súper método: del
  segundo 9 al 21 todos los psj salen con un trazo sobrante en el cuello
  (banda del color de la ropa: rosa con Rose, amarilla con Yellow).
  Pregunta: de qué sirvió el súper método si siguen estos errores.
- Respuesta honesta: el súper método sí sirvió para su clase (trazos
  desprendidos, motitas, agujeros: 8.966 px, las 4 capturas limpias),
  pero era CIEGO a esta clase: la banda es parte CONECTADA de la capa de
  ropa (el ribete/cuello interior, y en O2 la camisa blanca), no un trazo
  suelto, así que ningún detector la marcó. Dani ya la había visto en los
  7 ciclos («parche del cuello») y la dejó como dudosa pendiente de la
  decisión de Stiven; Stiven decidió: es error.
- Causa medida: el ribete sube por detrás del cuello hasta y~874 (mujer)
  / y~821 (hombre O2) y, como la ropa (30) va por encima de la Base (20),
  pinta sobre la piel del cuello. Es pálido en crudo, así que con el tinte
  se vuelve chillón (amarillo/rosa); con Blanco apenas se nota, por eso se
  escondió en los renders por defecto.
- Fix fase 1 (`herramientas/ribete_cuello_fix.py`, snapshot
  `versiones/2026-11-23_ribete-cuello-antes/`): borrados 29.384 px de las
  6 ropas donde la Base es opaca y y<960 (el cuello por encima de los
  hombros). Verificado: amarillo en el cuello 6.159 px → 0 px.
- Fix fase 2 (`herramientas/ribete_cuello_fix_fase2.py`, snapshot
  `versiones/2026-11-23_ribete-cuello-fase2-antes/`): quedaba una franja
  brillante en la base del cuello (y960-1010, el ribete bajo); recoloreados
  6.367 px en F O2 + 3.049 px en F O3 al color del cuerpo (el ribete deja
  de contrastar; las líneas oscuras de pliegues se conservan). Verificado:
  amarillo en cuello+base 9.270 px → 65 px (0 sobre el cuello).
- Verificación: renders Amarillo/Rosa/Blanco + hombre O2 revisados por
  Dani a ojo (cuello limpio, el cuello de la prenda queda en la base del
  cuello como debe ser). Vídeo nuevo grabado:
  `diagnostico_usuario/videos/video_ribete_2026-11-23.webm` (41,68 s,
  14 combos, todos Sorprendido; 2 fotogramas revisados por Dani).
  PENDIENTE subir a GitHub/Drive cuando Stiven lo ordene (las 6 ropas ya
  estaban en los 23 archivos del súper método; total sigue siendo 23
  capas + scripts nuevos).

## 2026-11-23 — TANDA 20 (2 capturas nuevas de Stiven, revisión POR CAPA)
- Stiven (2026-11-23 ~15:50) envió 2 capturas más con errores y ordenó:
  revisarlos por capa, sin barrer los combos. Hallazgos medidos en capa:
- **Base F, punta de la nariz (la marca de la captura 1):** la capa
  Nose3 está LIMPIA (0 px oscuros/marrones); la mancha es de la BASE:
  202 px oscuros + 941 px marrones en la punta + motita negra. Fix
  (`herramientas/tanda20_fix.py`, snapshot
  `versiones/2026-11-23_tanda20-antes/`): mancha aclarada 65% hacia la
  piel (queda sombra suave) y motita borrada por inpaint. 457 px.
- **Base M, frente (la marca de la captura 2):** dos triángulos marrones
  (sombra de pelo geométrica que asoma como mancha). Chico 115 px en
  x464-478 y400-422 (visible con H2/H3; el combo de Stiven es H3).
  Grande 950 px en x400-431 y311-383 (visible con H1). Fix: inpaint
  con piel. 1.367 px.
- **Pelo H4 F y H3 M (bordes):** halo claro en el borde (defringe, misma
  clase que en las ropas). Fix: recoloreado al color del pelo vecino.
  H4_Front 268 px, H4_Back 831 px; H3 M 0 px (no tenía halo). Las hebras
  sueltas del pelo ondulado son DISEÑO y no se tocan.
- **Ojo Gris moteado (la marca del ojo en la captura 2):** NO es la capa
  Eyes_Angry (el arte verde está limpio) sino el TINTE: con Gris el iris
  conservaba la textura de luminancia y se veía sucio (parches verdes,
  morados, disco lavanda). Fix en `motor.py` `_ojos_tinte`: si el destino
  es casi sin saturación (solo Gris), el iris se aplana al color destino
  (luminancia comprimida 65% hacia él). Verificado: iris Gris uniforme,
  Azul intacto (control). Re-bakeadas las 10 variantes Gray de
  `unity/EyesColor/` (`herramientas/tanda20_rebakear_gris.py`; sat 10,
  lum_std 17-25). Los otros 50 variantes no cambian.
- Verificación: los 2 combos re-renderizados y revisados por Dani a ojo
  (nariz limpia con sombra suave, frente limpia, iris Gris uniforme).
- **SUBIDO 2026-11-23 ~16:26 (Stiven: «Sí, súbelo a GitHub y Drive»):**
  GitHub commit `ea0d2adc78a51bc5c270b82c912e6b5f254d3bd6` (192 archivos,
  192/192 blobs verificados) + release
  `v2026-11-23-supermetodo-ribete-tanda20` (id 456011728, descripción
  completa con los 3 bloques de cambios) + ZIP
  `supermetodo-ribete-tanda20_2026-11-23.zip` (34,5 MB, 42 archivos,
  asset id 784582982). Drive/Unity: 34/34 archivos subidos por ID y
  verificados por md5 (24 capas + 10 variantes Gray). **GitHub =
  Drive/Unity = súper método + ribete + Tanda 20.**

## 2026-11-23 — TANDA 21 (4 capturas nuevas de Stiven, revisión POR CAPA, zooms 7x)
- Stiven (2026-11-23 ~16:32) envió 4 capturas (todas mujer + O3 Blue
  Hoodie) y ordenó: buen método (combo de métodos + Playwright + lupas
  + zooms casi al 700%), por capas, no por combos. Ejecutado por
  coordinador con 2 analistas; verificado por Dani a ojo en los 4
  renders finales + md5.
- **Female/Outfit3 (9.703 px + 276 + 124 + 456 + 51):** láminas
  triangulares oscuras en el borde izquierdo del pecho (3 grandes + 2
  pequeñas + 8 motitas) — conectadas pero anómalas (O1/O2 y O3 de hombre
  son lisos en esa zona); recortadas a envolvente suave. Hilo fino
  vertical colgando (C2, 276 px), gancho/púa sobre el hombro (C1,
  124 px), franja pálida del ribete recoloreado en el cuello (C3/C4,
  456 px: recolorear no funcionaba, se borró), franja lima brillante
  de 1 px junto al pelo (C2, 51 px, defringe).
- **Female/Hair8_Front (6.512 + 102 + 1.226 borrados + 964 dibujados +
  94):** 3 líneas desprendidas en cuello/pecho + restos
  semi-transparentes; piquito + motita en el cuello; QUIEBRO en ángulo
  recto del mechón principal (banda horizontal con 2 esquinas de 90°):
  borrada la banda y redibujada diagonal suave.
- **Female/Hair9_Front (3.440 + 1.230 borrados + 964 dibujados):** 2
  líneas desprendidas en el pecho + motita; mismo quiebro que H8 (misma
  posición, plantilla compartida), mismo arreglo.
- **Female/Hair2_Front (36 px):** muesca en el borde del pelo sobre el
  ojo (C3) + motitas en la frente; rellenado con color de pelo.
- **Female/Hair2_Back (3.243 px):** 6 hilos desprendidos latentes en
  cuello/pecho (invisibles en el render actual, tapados por Base/O3).
- Total: ~26.500 px corregidos + 1.928 px dibujados (2 diagonales).
  5 capas. Snapshot `versiones/2026-11-23_tanda21-antes/`.
- Diseño NO tocado: parche pálido del cuello interior de la camisa
  (O3); mechones principales de H8/H9; hebra larga de Hair2_Front
  sobre el hombro derecho (C4, 4.189 px, conectada — Stiven la marcó;
  si insiste, se borra el tramo); penacho del hombro y solapa de O3.
- Residual menor: mechón punteado de Hair9_Front (x300-310, y691-880,
  hebra rota en 3 trozos; no se pudo unir).
- Verificación: 4 capturas re-renderizadas post-fix en motor y en
  navegador real (Playwright); diff pre/post solo en pecho/cuello/
  hombro/frente, 0 px en la cara. **SUBIDO 2026-11-23 ~17:24 (Stiven:
  «Sí, súbelo a GitHub y Drive»):** GitHub commit
  `0aa61168fd19d13dee4871b54c2752743ed714a1` (200 archivos, 200/200
  blobs verificados; Outfit3 también verificado por
  raw.githubusercontent.com) + release `v2026-11-23-tanda21`
  (id 456066615, descripción completa) + ZIP
  `tanda21_2026-11-23.zip` (8,4 MB, 5 capas + NOTA.txt, asset id
  784760761). Drive/Unity: 5/5 subidas por ID y verificadas por
  re-descarga md5. **GitHub = Drive/Unity = Tanda 21.**

## 2026-11-23 — TANDA 22 (5 capturas nuevas de Stiven, revisión POR CAPA, zooms 10x)
- Stiven (2026-11-23 ~18:45) envió 5 capturas y ordenó el mismo método
  que la Tanda 21 pero con zooms casi al 1000%. Ejecutado por
  coordinador con 2 analistas; verificado por Dani a ojo en los 5
  renders finales + md5.
- **Eyes ×5 (795 px):** fragmento pálido DESPRENDIDO de 159 px en la
  punta de la nariz, idéntico en las 5 capas de ojos — NO era Nose1 ni
  Base (ablación: sin la capa de ojos → 0 px pálidos). Borrado en las 5.
- **Hair10_Front (28.621 px):** HALO (clase nueva): franja
  semitransparente clara en todo el borde del pelo, 53.513 px — defringe
  31.085 px. Huecos en la línea del pelo que dejaban ver piel (425 px:
  eran pelo semitransparente pálido, no transparentes — máscara
  alfa<200 + Laplace + oscurecido de borde 279 px). Motitas claras en
  el moño (698 px oscurecidas + 180 de fragmentos).
- **Hair9_Front (11.435 px):** HALO 31.422 px — defringe 11.987 px.
  Hebra punteada vertical (resto de T21, ~200 px) borrada; fragmento
  curvo desprendido (150 px); 30 componentes desprendidos (489 px).
- **Hair7_Front (804 px):** gota en el cuello (hebra que se hincha a
  10-13 px × 56 px, 668 px) + punto desprendido (38 px) + guión en
  hueco de trenza y micros (98 px).
- **Hair2_Front (1.656 px):** fragmentos junto a la oreja (231 px) y
  en la línea del pelo (173 px) + motitas (84 px) + defringe (1.203 px).
- **Hair2_Back (6.849 px):** halo 11.853 px — defringe 7.026 px.
- **Outfit3 (4.469 px visibles):** guión desprendido en el pecho
  (75 px) + pico triangular (1.056 px); hilo colgando en el hombro
  (1.333 px); aleta triangular conectada en el pecho izquierdo (612 px,
  T21 la clasificó diseño — Stiven la volvió a marcar → defecto);
  solapa fina conectada en el hombro derecho (689 px, mismo caso);
  remanente del ribete en el cuello (466 px: guiones naranja-rojo +
  borde punteado).
- **Outfit2 (172 px):** arco flotante en el cuello (57 px, también en
  O3) + curva clara (115 px).
- **Nose1 (3 px):** 3 px oscuros desprendidos bajo la punta.
  **Eyes_Sad (41 px):** guión sobre la ceja interior.
- Total: 54.845 px visibles corregidos. 13 capas. Snapshot
  `versiones/2026-11-23_tanda22-antes/`. motor.py NO tocado (iris
  idénticos pre/post).
- Diseño NO tocado: rim-light fino en el contorno de H9 (brillo
  dibujado); hebra larga de Hair2_Front en el hombro (T21); hebras
  largas de H7/H10/H9; guión rojizo de Outfit2 (parece costura);
  mancha café del cuello interior de O3/O2.
- PENDIENTE subir a GitHub/Drive cuando Stiven lo ordene (13 capas +
  scripts).
- Script nuevo `herramientas/grabar_video.js` (reutilizable): graba el
  creador con Playwright; opciones --duracion, --segundos, --boca
  (sorprendido|aleatorio), --sexos, --salida, --url. Reemplaza a
  grabar_video_ciclo.js / grabar_video_randomize.js para las próximas
  grabaciones. Vídeo de 40 s con esta versión (randomize hombre y mujer,
  siempre Sorprendido) grabado con él.

## 2026-11-23 — Rayita suelta en Female Hair1_Front (vista por Stiven en el vídeo Sorprendido)
- Stiven vio el vídeo de 40 s (versión R) y reportó 12:12: «perfecto, solo
  vi un error en el primer psj mostrado en el video, la chica tiene una
  pequeña rayita en la boca sorprendida, arreglalo y fijate si aparece en
  mas combos».
- Causa: NO era la boca R. Es un trazo fino horizontal DESPRENDIDO de la
  capa Female Hair1_Front (19 px, x380-392, y787-789), que flota sobre la
  piel justo a la izquierda de la boca y se lee como una rayita pegada a
  ella. Confirmado por medición por capa (Base, Nose1, Hair1_Back y la
  boca R limpias en esa zona) y por el mapa de alfa (la rayita está
  separada de la masa del pelo por píxeles transparentes, sin puente).
- Alcance: SOLO Female Hair1_Front la tiene (escaneo de las 12 frentes de
  pelo de mujer + 4 de hombre en la zona de la boca: ningún otro). Aparece
  en TODOS los combos de mujer con H1 (Long Straight), con cualquier
  boca/nariz/ropa: 225 combos de piezas. En el vídeo salía en 2 combos
  (apertura F H1 O1 E1 N1 M5 y azar 3 F H1 O3 E3 N2 M5).
- Fix (`herramientas/rayita_fix_H1.py`, snapshot previo en
  `versiones/2026-11-23_rayita-H1-antes/`): borrados los 19 px (alfa=0).
  Hair1_Front F md5 69644a81... → 94140fdb...
- Verificación: render en motor pre-fix (snapshot) vs post-fix del primer
  combo: cambian EXACTAMENTE 19 px, todos dentro de la rayita, nada más.
  Render en el navegador (copia de prueba) del primer combo: boca limpia,
  sin rayita. **SUBIDO 2026-11-23 ~12:48 por orden de Stiven («Sí, súbelo a
  GitHub y Drive»): GitHub commit 211c3547 (180 archivos, verificado
  180/180, Hair1_Front por raw md5 94140fdb...) + release
  v2026-11-23-rayita-H1 (id 455781891) con rayita-H1_2026-11-23.zip (asset
  id 783950284, 2.029.843 bytes) y descripción completa de los cambios;
  Drive/Unity 1/1 verificado por md5. GitHub = Drive/Unity = rayita.**

## 2026-11-23 — Cuadritos de color en Unity (orden de Stiven)
- Stiven 20:16: en Unity NO le salen los cuadritos de colores que ve en
  mis vídeos; en Unity el color solo se elige con las flechas < >. Y sí
  descargó y esperó el último sync de Drive. Tenía razón en lo que veía:
  los cuadritos solo existían en el creador web (versión Linux,
  `index.html`, `COLOR_FILAS`), nunca en Unity. En Unity
  `PortraitCreator.cs` construía cada fila solo con < y > (así dice su
  propio comentario). El sync de Drive funcionaba bien: tenía las últimas
  capas (Tanda 22); ningún sync iba a traer los cuadritos porque no
  existían en el código de Unity.
- Fix (`PortraitCreator.cs`, snapshot previo en
  `versiones/2026-11-23_cuadritos-antes/`, md5 antes 046dc538... = blob
  GitHub 65fe7f34...): las 4 categorías de color (EYE COLOR, HAIR COLOR,
  SKIN TONE, OUTFIT COLOR) ahora tienen una fila de cuadritos clicables
  justo debajo de su fila, con los colores de la paleta
  (`PortraitPalette`, `NamedColor.name` + `.color`). Un clic elige el
  color directo (`SelectColor`, nuevo método público: fija el índice,
  `ApplyCurrent()` + `RefreshUI()`). El cuadrito seleccionado lleva un
  borde blanco (`Outline`, toggled en `RefreshUI()`); los demás sin
  borde. Los botones < > siguen funcionando igual.
- Layout: las filas pasaron de 0.044 a 0.038 de alto (pitch 0.052 →
  0.044) y cada fila de cuadritos mide 0.026, para que las 4 filas
  nuevas quepan sobre los botones de acción. Verificado por simulación:
  filas 0.868 → 0.306, botones de acción 0.294 → 0.060, texto del combo
  0.008–0.055 (sin solapes). Ancho por cuadrito: 24 colores ≈ 20 px,
  7 colores ≈ 74 px, 4 colores ≈ 131 px (panel de 576 px a 1920×1080).
  Los cuadritos no tienen transición de color del botón
  (`Selectable.Transition.None`), así que siempre muestran el color
  exacto de la paleta. Si la paleta es null no se construyen cuadritos
  (seguro). Llaves/paréntesis/corchetes balanceados (85/85, 316/316,
  51/51). NO se pudo compilar en Unity aquí (no hay Unity ni csc/mcs
  en Linux): Stiven lo prueba en su PC y dice si se ve bien.
- SUBIDO 2026-11-23 ~20:20 por orden de Stiven («Sí, pon los cuadritos
  en Unity»): Drive/Unity `PortraitCreator.cs` (id
  1WJmiDhcw5Jvjp_aFIs9z7jjAjeNV_mTR) reemplazado y verificado por
  re-descarga md5 5bca0e9e... GitHub: `PortraitCreator.cs` actualizado
  por PUT (commit 254e792f, blob fce8a6c2..., verificado por raw md5
  5bca0e9e...) y `VERSIONES.md` (commit 4e9109d8) + release
  v2026-11-23-cuadritos-unity (id 456194356) con descripción completa y
  asset cuadritos-unity_2026-11-23.zip (id 785223076, 8.072 bytes).
  GitHub = Drive/Unity = cuadritos. NOTA: la
  Tanda 22 sigue PENDIENTE de subir (Stiven no ha respondido al widget);
  este cambio NO incluye sus 13 capas.

## 2026-11-23 — Candados por rasgo + Reset to Default (EN CURSO, no subido)
- Orden de Stiven 21:22: agregar selectores individuales (candado) a
  los rasgos para que Randomize no toque los fijos, solo los demás; y
  21:23 otro botón general "restaurar a predeterminado" para dejar todo
  sin selectores. 21:24: elegir yo el mejor texto, redacción y estética.
- WEB (`version-linux/index.html`, verificado en navegador con
  `herramientas/probar_candados.js`): cada fila tiene un botón candado
  (🔒 fijado / 🔓 libre) a la derecha; el rasgo fijado se ve en dorado y
  su candado con fondo dorado. Randomize salta los fijos (verificado:
  HAIR y OUTFIT fijos no cambiaron en 3 Randomize, los demás sí).
  Botón "Reset to Default" bajo Randomize: vuelve a la mujer por
  defecto (F H1 O1 E1 N1 M1, colores 1) y quita TODOS los candados
  (verificado: código F H1... y 0 candados activos). Los candados NO
  forman parte de la receta (no se guardan en el JSON). De paso se
  arregló un bug: el handler genérico de botones reasignaba el onclick
  de los cuadritos de color y al hacerles clic se rompía (FILAS.find
  daba undefined); ahora solo los botones < > llevan ese handler y el
  clic en un cuadrito SÍ cambia el color (verificado: Chestnut).
- UNITY (`PortraitCreator.cs`): botón PIN por fila (la fuente legacy de
  Unity no tiene el emoji 🔒, así que dice PIN y se pone dorado al
  fijar; el valor también se pone dorado). `Randomize()` salta los
  fijos; `ToggleLock(categoría)`; `ResetToDefault()` (vuelve a Female
  por defecto y quita todos los candados). Acciones ahora 6 (se agregó
  Reset to Default, botones un poco más bajos: 0.034, pitch 0.039;
  último botón termina en 0.065, sin solape con el combo). Llaves/
  paréntesis/corchetes balanceados (90/90, 351/351, 74/74). NO
  compilado en Unity aquí: Stiven lo prueba en su PC.
- PENDIENTE subir junto con la edad (misma versión nueva) cuando
  Stiven apruebe la muestra de edad. NO se sube nada todavía.

## 2026-11-24 — Edad como selector (Joven / Anciano) + pelos grises v11.1 [RAMA edad-ancianos, no main]
- Orden de Stiven 2026-11-23 21:21: edad como selector, sin tocar la
  geometría de la cara, arrugas para ancianos; y 2026-11-24 09:41: NO
  adultos (solo Joven/Anciano) y pelo anciano TOTALMENTE gris. Rama
  `edad-ancianos` creada desde main `de3d8e7f`; esta versión vive SOLO
  en esa rama. Incluye la Tanda 22 (13 capas) y los candados + Reset
  (arriba), porque los grises v11 se derivaron de las capas Tanda 22.
- Selector AGE (primera fila, con candado; valor en inglés Young /
  Elderly). Anciano = Base anciana v9 (marcas tono piel, nunca grises
  ni negras) + pelos grises v11.1 de los 16 peinados; tinte de pelo
  anulado con Anciano (el Silver no grisaba). Receta `edad` 0/1 y
  código `AG1` (Joven) / `AG2` (Anciano) al final. Randomize incluye
  la edad salvo candado; Reset vuelve a Joven y quita los candados.
- Método gris dinámico v11.1 (`herramientas/pelo_gris_dinamico.py`,
  10 pasos A–J): curva de remapeo de luminancia + streamlines largos
  (método v8) + limpieza de retazos como paso del proceso (componentes,
  despeje de ceja, oreja, repisa bajo la oreja, sien, polvo, barrido
  final tras cada corte). Se aplica a los 16 peinados (12 mujer + 4
  hombre, Front y Back): 26 capas reales + 6 Back vacíos (F H5–H10).
  0 componentes problemáticos y 0 motas finales en las 26.
- Causa raíz de los retazos (verificada): el gris REVELA, no crea —
  el arte joven tiene filamentos de 1–4 px invisibles en negro
  (contraste ~0–5 niveles) que en gris se vuelven hilos brillantes
  (~90–120). 13/16 retazos de la mujer existen idénticos en el joven
  negro. Los cortes v9/v10 sí crearon retazos (motes y halos) por
  tocar solo alfa>200.
- 3 revisiones con vídeo en Playwright (60 combos: 48 ancianos + 12
  jóvenes; ciclo 1 halló ranuras verticales en el flequillo de F H8/
  H9/H10 por un bug del despeje de ceja — 24.043 px quitados — y se
  arregló EN EL MÉTODO, v11.1, re-aplicado a los 16; ciclos 2 y 3 sin
  retazos nuevos). Vídeo final: `diagnostico_usuario/edad/
  videos_revision/ciclo3_video.webm` (41,76 s, 20 combos).
- UNITY (`PortraitCreator.cs` CatAge=0, CatCount=11 + `PortraitRecipe.
  cs`, `PortraitData.cs`, `PortraitView.cs`; mapa en `unity/
  EDAD_TEXTURAS.md`). NO compilado en Unity aquí: Stiven lo prueba
  en su PC.
- Conocido: con Anciano el vello facial sigue oscuro (no hay capas
  grises de barba); la web y el motor difieren hasta ~50 niveles en
  hebras semitransparentes del pelo anciano (`teñida()`, artefacto
  preexistente, a ojo iguales); las líneas de los hombros de la
  chaqueta del hombre no tienen pelo debajo (0 px) — pendiente de
  confirmación de Stiven.

## 2026-11-24 — Barba gris anciana v11.1 [RAMA edad-ancianos, no subido aún]
- Orden de Stiven 2026-11-24 ~15:19 («Sí, la barba gris también»):
  con Anciano la barba quedaba oscura. Generadas las 3 capas
  `FacialHair<N>_Elderly` con el método gris v11.1 adaptado
  (`herramientas/vello_gris.py`, informe `informe_vello_v11.1.json`):
  el Stubble SON puntos por diseño, así que solo se borraron los 6
  puntos fuera de la silueta; el Mustache conserva su punta izquierda
  (402 px) y se borraron 17 motas; la Full Beard conserva su masa
  aunque salga de la silueta (cuelga bajo la mandíbula por diseño).
  FH1: 19→2 componentes, 0 motas; FH2: 104→55 componentes, 0 polvo
  aislado; FH3: 39→16 componentes. Integrado en web (precargar +
  componer, verificado en navegador: AGE Elderly, FACIAL HAIR Full
  Beard, 0 errores) y motor (mismo criterio que el pelo: capa
  _Elderly + tinte en (1,1,1)); Unity: `PortraitData.
  facialHairsElderly` + `PortraitView.SetFacialHair` / `SetHairColor`
  (blanco con Anciano, fallback a la joven). Los renders jóvenes son
  idénticos a antes (diff máx. 0.0 en 3 combos). PENDIENTE: veredicto
  de Stiven sobre la muestra y subir el commit a la rama.

## 2026-11-24 — Correcciones a la barba gris (marcas de Stiven) [RAMA edad-ancianos, no subido aún]
- Stiven marcó 2 cosas en la muestra de la barba gris (~15:31):
  (1) la barba se pasó un poquito de crecida; (2) un pedacito de
  cuello se sale en el cuello de la camisa (O3).
- (1) Causa: la barba JOVEN sale 35-71 px por delante de la barbilla
  (en negro no se nota contra el fondo oscuro; el gris lo revela).
  Arreglo DINÁMICO en el método (`herramientas/vello_gris.py`,
  paso `borde_frente_barba` al final del proceso): recorta el borde
  frontal de FH3_Elderly siguiendo la curva de la barbilla con 12 px
  de margen + bigote hasta el borde de la cara + transición suave
  (y921-960) hasta el borde natural de la punta. 4.264 px sólidos
  recortados; FH3 nuevo md5 `3f85941fea8b`. Lecciones: recortar hasta
  la línea del CUELLO borraba toda la punta (17.161 px); la barbilla
  suavizada mezcla el cuello en y925 y dejaba una muesca — el ancla
  de la transición es jaw[920]; el recorte va DESPUÉS de la limpieza
  (antes, B/D borraban las hebras del borde nuevo). La barba joven
  NO se toca (queda igual que siempre).
- (1b) Stiven marcó después la PUNTA de abajo (~15:51): el recorte
  del frente dejó al descubierto que la barba cuelga 88 px por
  debajo del mentón (hasta y1011) delante del cuello. Arreglo con SU
  método: referencia del mismo personaje SIN barba (FH0) — el mentón
  termina en y923 (el borde de la Base salta de x405 a x500 ahí) y la
  línea de la mandíbula sube a la oreja. Paso
  `borde_inferior_barba` (al final del proceso): recorta la barba por
  debajo de esa línea (curva por (405,923), (550,878), (700,832)).
  52.047 px sólidos recortados; la barba termina en y923, sigue la
  mandíbula, sin faldón ni escalón. Lección: el primer intento (v6)
  dejó un escalón plano en y899 porque el bucle empezaba en y900 —
  el corte debe empezar por encima de la línea (y800). Verificado en
  O1/O2/O3 ancianos con FH3; el joven no cambia.
- (2) Causa: cuña de piel de 162 px en (860-876, 938-959) que se
  asoma por encima del borde del cuello de la camisa O3 (defecto del
  arte joven, idéntico en joven y anciano). Arreglo:
  `herramientas/arreglar_cuello_o3.py` extiende el cuello de la
  camisa O3 sobre la cuña (color copiado de la chaqueta + ribete
  oscuro por el borde nuevo). Solo O3 en la copia de la rama; la
  Base no se toca. Verificado: el render joven O3 solo cambia 211 px
  en la cuña; O1/O2 ancianos con FH3 se ven limpios.
