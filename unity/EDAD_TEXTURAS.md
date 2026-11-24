# Edad (Joven / Anciano) — texturas Unity

> Rama `edad-ancianos`. Cómo cablear las capas ancianas en el proyecto Unity.
> Regla: con Anciano se usan la Base anciana v9 y los pelos grises v11
> (gris TOTAL horneado en la capa); el tinte de pelo NO se aplica al pelo
> anciano (va en blanco). El vello facial no tiene versión anciana.

## Código (en `unity/Runtime/`, NO compilado aquí)

- `PortraitRecipe.ageIndex`: 0 = Joven, 1 = Anciano. El código del combo
  lleva el marcador al final: `AG1` Joven, `AG2` Anciano
  (p. ej. `F H1 O1 E1 N1 M1 | HC1 ST1 OC1 EC1 AG2`).
- `PortraitData.baseElderlySprite`: Base anciana del personaje.
- `PortraitData.hairs[i].backElderlySprite` / `frontElderlySprite`: pelo
  gris v11 del peinado i. Si falta, el render usa la capa joven.
- `PortraitView.Apply` / `SetHair` / `SetAge` eligen las capas ancianas
  cuando `ageIndex == 1`; `SetHairColor` deja el pelo en blanco en ese
  caso (el vello facial sigue con el tinte de pelo).
- `PortraitCreator`: fila AGE (primera, con PIN como las demás).
  Randomize incluye la edad salvo PIN; Reset to Default vuelve a Joven
  y quita todos los PIN.

## Mapeo de archivos (web `version-linux/assets/` -> Unity)

La Base anciana y cada pelo gris existen en el repo en
`version-linux/assets/<Sexo>/` con estos nombres:

| Uso en Unity | Archivo en el repo |
|---|---|
| `Female.baseElderlySprite` | `Female/Base_Elderly.png` (Base anciana v9, md5 `e12512ee…`) |
| `Male.baseElderlySprite` | `Male/Base_Elderly.png` (Base anciana v9, md5 `37483805…`) |
| `Female.hairs[N].backElderlySprite` | `Female/Hair<N>_Back_Elderly.png` (N = 1–12) |
| `Female.hairs[N].frontElderlySprite` | `Female/Hair<N>_Front_Elderly.png` (N = 1–12) |
| `Male.hairs[N].backElderlySprite` | `Male/Hair<N>_Back_Elderly.png` (N = 1–4) |
| `Male.hairs[N].frontElderlySprite` | `Male/Hair<N>_Front_Elderly.png` (N = 1–4) |

Nombres de peinado (mismo orden que el creador web): mujer 1 Long Straight,
2 Pixie Cut, 3 Bob Cut, 4 Long Wavy, 5 Twin Tails, 6 High Ponytail,
7 Long Braid, 8 Double Buns, 9 Hime Cut, 10 Messy Bun, 11 Side Ponytail,
12 Long Curly; hombre 1–4 Style 1–4.

## Casos especiales

- `Female Hair5–Hair10 Back` ancianos son PNG transparentes 1200x1600:
  el Back joven original ya es totalmente transparente (0 px con alfa > 0),
  así que el gris v11 no generó capa. En Unity se puede dejar el slot
  vacío (el fallback usa el Back joven, también transparente).
- Vello facial (solo hombre): sin versión anciana; con Anciano sigue su
  capa normal con el tinte de pelo. Si Stiven quiere la barba gris, hace
  falta generar `FacialHair<N>_Elderly` con el mismo método gris.
- Método de generación de los pelos grises (reproducible):
  `herramientas/pelo_gris_dinamico.py` (copia del método v11).
