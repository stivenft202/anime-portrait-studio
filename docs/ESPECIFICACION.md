# Anime Half Portrait Studio — Especificación de la Fase 0

Kit de Unity de retratos anime de medio cuerpo por capas (Estilo 1: anime TV
moderno, cel shading, contornos limpios, ojos grandes). Esta fase fija la
plantilla sobre la que nacen TODAS las capas del kit: si una capa no respeta
esta especificación, no entra al paquete.

## Lienzo único

- **1200 × 1600 px exactos** para todo: plantilla, retrato de referencia y
  cada capa suelta. Ninguna capa se genera ni se recorta a otro tamaño.
- Vista **tres cuartos**: cabeza girada levemente hacia la izquierda del
  espectador, mirada hacia la izquierda (pose de conversación).
- Encuadre de medio cuerpo: de la coronilla a media cintura (el corte va en
  el borde inferior del lienzo, y = 1600).

## Guía de proporciones (sobre el lienzo 1200×1600)

| Referencia | Valor |
|---|---|
| El cabello puede subir hasta | y ≈ 60 |
| Coronilla | y ≈ 180 |
| Centro de la cara | x ≈ 580 |
| **Cruz de anclaje (centro de ojos)** | **(580, 470)** |
| Línea de ojos | y ≈ 470 |
| Nariz | y ≈ 560 |
| Boca | y ≈ 620 |
| Mentón | y ≈ 700 |
| Cuello | y ≈ 700–790 |
| Hombros | y ≈ 810 |
| Corte inferior (media cintura) | y = 1600 |

La cruz de anclaje (580, 470) es el punto de registro común: al apilar las
capas, todas comparten este punto y el mismo lienzo, así ninguna pieza queda
descuadrada. La plantilla visual está en `plantilla_maestra.png`.

## Orden de capas (de atrás hacia adelante)

1. **Fondo** (transparente en el retrato final; en el kit lo pone el usuario)
2. **Cabello trasero** (la masa de pelo que va detrás del cuerpo)
3. **Base** (cuerpo y piel: cabeza, cuello y torso sin ropa)
4. **Ropa** (torso)
5. **Expresión** — en este kit ojos + cejas + boca van juntos en **una sola
   capa** por expresión (no son tres capas separadas)
6. **Cabello delantero** (flequillo y mechones frontales)
7. **Accesorios** (lentes, aretes, diademas, etc.)

Los colores (cabello, ojos, piel, ropa) se aplican por **tinte** dentro de
Unity desde una paleta; no se genera una imagen por color.

## Tablero de referencias terminadas (control obligatorio)

En `~/workspace/retratos-anime/referencias/` vive el tablero de retratos
TERMINADOS (ilustraciones completas, no capas) en Estilo 1, tres cuartos y
mirada a un lado: `referencia_madre.png` (la chica de pelo negro, la
referencia madre aprobada por Esteban), `referencia_hombre_1.png`,
`referencia_hombre_2.png`, `referencia_mujer_1.png` y
`referencia_mujer_2.png`. Es el estándar de proporciones del kit: pupilas
desplazadas a un lado (pose de conversación, nunca mirando a la cámara),
espacio de piel visible entre el ojo lejano y la oreja, y boca bajo la
línea de la nariz, desplazada hacia el lado hacia el que mira el rostro.

**Regla (fijada por Esteban el 20 nov 2026):** «Toda capa y todo compuesto
se compara contra el tablero de referencias terminadas (carpeta
referencias/) antes de aprobarse; ninguna proporción se da por buena sin
ese contraste».

## Regla del fondo magenta y extracción de capas

- Cada capa suelta se genera sobre **fondo magenta puro #FF00FF**, plano y
  uniforme, sin sombras ni degradados.
- La extracción a PNG con transparencia se hace con el script
  `~/workspace/retratos-anime/extraer_capa.py`:

  ```
  python3 extraer_capa.py entrada.png salida.png
  ```

  El script calcula el alfa por distancia de color al magenta (con rampa
  suave en los bordes) y aplica **defringe**: deshace la mezcla con el fondo
  en los píxeles semitransparentes para eliminar el halo magenta. La salida
  conserva el tamaño original (1200×1600) — nunca se recorta al contenido,
  porque el registro entre capas depende del lienzo completo.

## Archivos de la Fase 0

| Archivo | Qué es |
|---|---|
| `fase0/plantilla_maestra.png` | Plantilla guía 1200×1600: silueta esquemática en tres cuartos, líneas guía con rótulos en inglés, línea del centro de la cara (x=580) y cruz de anclaje en (580, 470). |
| `fase0/retrato_referencia.png` | Retrato completo de referencia (mujer joven, Estilo 1, tres cuartos mirando a la izquierda, ropa casual, fondo sólido claro), normalizado a 1200×1600 sin deformar. Es la referencia de estilo y proporciones que aprueba Esteban antes de producir las capas. |
| `fase0/ESPECIFICACION.md` | Este documento. |
| `../extraer_capa.py` | Script reutilizable de extracción de capas desde fondo magenta (vive en la raíz del proyecto porque lo usan todas las fases). |

## Método v2 — set del hombre desde cero (fijado por Esteban el 20 nov 2026)

El set del hombre de la v1 fue BORRADO por orden de Esteban tras errores de
proporción repetidos; el detonante final fue que la cara no tenía nariz (la
capa de expresión la excluía y la base no la llevaba). La v2 se rehace con
este método, sin atajos:

### Flujo obligatorio

1. **Tablero ampliado:** al tablero de retratos terminados se suman
   referencias de internet de retratos anime masculinos de novela visual en
   tres cuartos casi de perfil, guardadas en `referencias/internet/`
   (guía interna de proporciones).
2. **Primero el DIBUJO MAESTRO TERMINADO:** un retrato completo del hombre
   (casi de perfil mirando a la izquierda, mirada a un lado, nariz parcial
   visible), validado con cuadrícula medida y con la checklist de abajo.
   **Sin el visto bueno de Esteban al maestro no se extrae ninguna capa.**
3. **REGLA UNIVERSAL DE VARIANTES:** cualquier cabello, expresión, ropa o
   cambio, por sutil que sea, se genera primero como DIBUJO TERMINADO del
   personaje maestro con esa variante puesta (misma pose, misma
   composición, proporciones del maestro), y recién ahí se calca/extrae la
   capa de ese dibujo. Si una variante no existe como dibujo terminado, no
   existe como capa. **Prohibido generar piezas sueltas flotantes o
   improvisar la capa directa.**
4. **Extracción, nunca invención:** cada capa nace por diferencia/mascarado
   de su dibujo terminado contra el dibujo base terminado, sobre el lienzo
   1200×1600. La BASE lleva la nariz parcial como rasgo estructural mínimo
   (con las orejas), para que ningún compuesto pueda quedar sin nariz; las
   expresiones llevan ojos + cejas + boca.

### Los tres candados

1. **Superposición para calcar:** el dibujo maestro terminado se superpone
   con baja opacidad sobre cada candidato y cada compuesto; las
   proporciones deben CALCAR las del maestro, no aproximarse «a ojo».
2. **Cuadrícula de tercios bloqueada + medición en píxeles antes de
   dibujar:** tercios fijos en x=400 y x=800, y=533 e y=1067, con rejilla
   de 100 px. Antes de generar/extraer cada pieza se miden y anotan en
   píxeles las bandas de cada rasgo según la cuadrícula del maestro; la
   pieza solo se acepta si sus rasgos caen dentro de las bandas medidas.
3. **Checklist obligatoria** antes de dar por buena cualquier cara y antes
   de pasar a capas: (a) nariz parcial visible en el casi perfil; (b) ojo
   lejano separado de la oreja con hueco de piel; (c) mirada a un lado,
   nunca a la cámara; (d) boca en posición de tres cuartos; (e) cejas
   visibles, sin pelo encima de los ojos. Y el maestro necesita el visto
   bueno de Esteban antes de extraer las capas definitivas.

### Posiciones medidas del maestro v2 (ley para todas sus capas)

Maestro: `fase1/pruebas/hombre_v2_maestro.png`; versión con cuadrícula y
textos: `fase1/pruebas/hombre_v2_maestro_cuadricula.png` (lienzo
1200×1600; mediciones visuales sobre rejilla de 50 px + segmentación):

| Rasgo | Posición medida |
|---|---|
| Coronilla | y ≈ 130 |
| Nacimiento del pelo (frente) | y ≈ 300 |
| Flequillo: borde sobre la zona de cejas (x 330–660) | no baja de y ≈ 430 |
| Flequillo: mechón lateral máximo (x 255–300) | y ≈ 575, sin cubrir el ojo lejano |
| Línea de cejas (cercana) | y 435–465, x 340–620 |
| Banda de ojos (cercano) | y 495–595, x 335–620 |
| Iris cercano | x 385–460, y 515–590 (pupila desplazada a la izquierda) |
| Ojo lejano (parcial, en el contorno) | x 225–265, y 545–610 |
| Hueco ojo–oreja | ojo termina en x ≈ 620 → oreja empieza en x ≈ 695 (≈75 px de piel) |
| **Punta de la nariz** | **(255, 665)** |
| Base de la nariz | y ≈ 695 |
| Boca | línea y 760–780, x 310–435, centro (372, 770) |
| Mentón | (405, 912), y ≈ 910 |
| Oreja | x 695–855, y 495–700 |
| Escote: punto más alto de la prenda (collar lateral) | y ≈ 905 (x ≈ 1010) |
| Escote en V (centro del pecho) | y ≈ 1245 (x ≈ 440) |

Checklist del maestro v2: (a) nariz parcial visible ✓ (punta en (255,665)
con línea de puente y fosa sombreada); (b) hueco ojo–oreja de ≈75 px ✓;
(c) mirada a un lado en ambos ojos ✓; (d) boca pequeña desplazada a la
izquierda bajo la nariz ✓; (e) ceja cercana completa y visible, flequillo
detenido en y≈430 sobre su zona ✓.
