# Anime Half Portrait Studio — versión independiente (sin Unity)

La misma herramienta del kit de Unity, pero como programa suelto:
no necesita Unity, ni internet, ni instalar nada más que Python 3.

## Cómo se abre

En Linux:

    python3 servidor.py

En Windows (si tienes Python): doble clic a `servidor.py` o
`python servidor.py` desde la carpeta.

Se abre solo en el navegador, en http://localhost:8765
Para cerrarlo: Ctrl+C en la ventana de comandos.

## Qué hace

- Los dos personajes (Female / Male) con las flechas < > de siempre:
  pelo, ropa, ojos, nariz, boca y los tres colores.
- Botón **Randomize** con el código de combo (#n y código, igual que en Unity).
- **Export PNG** (retrato completo 1200×1600 con transparencia) y
  **Export Face PNG** (cuadrado 1200×1200), que se descargan al computador.
- **Save Recipe / Load Recipe**: guarda y carga el look como archivo JSON.

## Las reglas son las mismas del kit

Orden de capas y tintes idénticos a Unity: la nariz sigue el tinte de
piel; ojos y boca nunca se tiñen. Las texturas son las mismas PNG del
paquete (`assets/Female`, `assets/Male`): cualquier corrección de arte
vale para las dos versiones a la vez.

## Archivos

- `servidor.py` — el programa (servidor local mínimo, solo librería estándar).
- `index.html` — la interfaz del creador.
- `motor.py` — el motor de composición en Python (lo usa la prueba).
- `probar_todo.py` — renderiza TODOS los combos (1.440) y busca manchas
  fuera de las zonas de rasgos. Es el candado de calidad de esta versión.
- `assets/` — las capas PNG de ambos personajes.
