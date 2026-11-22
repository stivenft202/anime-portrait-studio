# ESTÁNDAR DE PRODUCCIÓN DE PIEZAS — Anime Half Portrait Studio (Fase 5)

Documento normativo. Toda pieza nueva (cabello, ojos, nariz, boca, ropa, accesorio)
se produce EXACTAMENTE con este procedimiento. Sin excepciones y sin parches
manuales: una pieza que no pasa la puerta se regenera, no se remienda.

## Por qué existe este estándar

Los defectos de las fases 1–3 (trazos, mechones fantasma, bordes de color)
nacieron siempre en el mismo sitio: la EXTRACCIÓN de capas desde un dibujo
plano, seguida de parches manuales. Cada parche improvisado creó el defecto
siguiente. La solución no es parchear mejor: es que la pieza nazca de un modo
en que el error sea imposible o detectable al 100 % antes de entregarse.

## Las 6 reglas

### Regla 1 — Ninguna pieza nace de un dibujo libre
Cada pieza nueva se genera como un DELTA sobre el retrato ya aprobado:
se parte del compuesto exacto de las capas aprobadas y se genera el dibujo
completo permitiendo que cambie SOLO la región de la pieza nueva (máscara
fija por tipo de pieza, definida una sola vez en este documento).
Todo lo demás queda píxel a píxel idéntico a lo aprobado.

### Regla 2 — Extracción por diferencia exacta, nunca por familias de color
La capa nueva se obtiene restando del dibujo el render exacto de las capas
conocidas dentro de la máscara. Está prohibido separar por familias de color,
por cajas o por componentes sueltos: esos métodos son los que hornearon
contornos de ropa dentro de los frentes de pelo y bordes claros (rim) que
luego se tiñen de colores imposibles.

### Regla 3 — Puerta automática con notas numéricas (PASS / FAIL)
Toda pieza pasa por `producir_pieza.py` (la puerta, evolución de
`limpiar_capas.py`). Controles con umbral duro, sin juicio visual parcial:
1. Fuera de la máscara, el dibujo difiere del compuesto aprobado en 0 px.
2. Prueba ácida: recomponer el retrato con la pieza nueva reproduce el
   dibujo con diferencia < 0,5 %.
3. Grupos fantasma en el compuesto (contenido que el dibujo no tiene): 0.
4. Borde claro (rim) sobre prenda o piel: 0 px.
5. Alfa sólido dentro de la silueta de la pieza (sin vetas semitransparentes
   que dejen brillar la capa de abajo), salvo el borde antialias de 1 px.
6. Cero contenido fuera de la zona de la pieza.
Si cualquier control falla → FAIL → la pieza se regenera (Regla 5).
Está prohibido «arreglar» una pieza reprobada con ediciones locales.

### Regla 4 — Matriz de verificación automática
Con la pieza aceptada, el pipeline renderiza la matriz COMPLETA de
combinaciones contra el contenido existente (todos los pelos × expresiones
× ropas, con los tintes exactos de PortraitPalette.cs, incluidos el natural
y el más oscuro) y genera las hojas de contacto de cara Y de torso.
Yumi revisa las hojas antes de entregar; la entrega incluye las cifras de
la puerta (PASS con sus seis notas).

### Regla 5 — Producción por tandas cerradas
Se trabaja por tandas de un solo tipo (p. ej. 4 cabellos). Se entregan solo
las piezas con PASS; las reprobadas se regeneran dentro de la misma tanda.
Nada de entregas parciales «casi buenas» ni correcciones captura por captura.

### Regla 6 — Este documento manda
Cualquier mejora al método se escribe primero aquí y en la puerta, y se
aplica a todo lo nuevo desde ese momento. Si una regla no funciona, se
cambia la regla — no se improvisa una excepción.

## Zonas y máscaras por tipo de pieza (lienzo 1200×1600)

- Cabello: trasero y delantero; zona = silueta del cabello del dibujo delta;
  el frente nunca contiene píxeles bajo la línea de la mandíbula que no sean
  pelo según el dibujo (control 4 lo garantiza).
- Ojos (ojos + cejas): caja x260–640, y430–700.
- Nariz: caja x215–400, y600–760. La nariz sale de la base y pasa a ser capa
  propia intercambiable (2–3 variantes bastan).
- Boca: caja x300–460, y700–860.
- Ropa: zona y>780; silueta de prenda del dibujo delta.
- Accesorios: zona libre sobre el compuesto; orden de capa 60 (ya cableado).

## Cambio de arquitectura que acompaña (código, Fase 5)

La capa única «Expression» se divide en tres categorías independientes:
Eyes, Nose y Mouth. PortraitData/View/Creator se actualizan una sola vez
para soportarlas; las 4 expresiones actuales se migran separando sus rasgos
con la misma puerta (quedan como ojos/bocas iniciales y la nariz actual
como nariz 1). Esto multiplica las combinaciones sin tocar el resto del kit.
