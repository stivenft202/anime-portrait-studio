"""Barba gris anciana (vello facial) con el método v11.1 adaptado.

El método de pelo (pelo_gris_dinamico.py) no se puede aplicar tal cual al
vello facial:
  - FH2 (Stubble) SON puntos: paso_componentes borraría los 98 puntos <40 px
    que son el diseño. Solo se borran los puntos fuera de la silueta.
  - FH1 (Mustache): la punta izquierda (402 px) es diseño aunque sea un
    componente aparte; solo se borran las motas <40 px.
  - FH3 (Full Beard): la barba SALE de la silueta por diseño (cuelga bajo
    la mandíbula); solo se borran motas <40 px DESPEGADAS de la masa.
Reglas comunes: gris v8 (remapeo + streamlines), redondeo + puntas, y
verificación final (motas / polvo aislado)."""
import os, sys, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage
import pelo_gris_dinamico as m

EDAD = os.path.dirname(os.path.abspath(__file__))
ASSETS = '/home/hatch/workspace/anime-portrait-studio/version-linux/assets'
VERSION = 'v11.1'

base = np.asarray(Image.open(f'{ASSETS}/Male/Base.png').convert('RGBA'))
SILUETA = base[..., 3] > 0  # cara + cuerpo

def guardar(a, nombre):
    out = os.path.join(EDAD, f'{nombre}_Elderly.png')
    Image.fromarray(np.clip(a, 0, 255).astype('uint8')).save(out)
    md5 = hashlib.md5(open(out, 'rb').read()).hexdigest()
    return out, md5

def verificar(a, informe):
    solido = a[..., 3] > 200
    comps, _ = m.componentes(solido)
    informe['componentes_final'] = len(comps)
    informe['masa_final_n'] = comps[0]['n'] if comps else 0
    pl, ncl, top = m.polvo_lejos(a)
    informe['polvo_final_px'] = pl
    informe['polvo_final_clusters'] = ncl
    pa_px, pa_n, pa_top = m.polvo_aislado(a)
    informe['polvo_aislado_px'] = pa_px
    informe['polvo_aislado_clusters'] = pa_n
    motas, polvo = m.motas_y_halo(a)
    informe['motas_final'] = motas
    informe['polvo_final_diff'] = polvo
    return informe

def borde_inferior_barba(a, informe):
    """Recorta la parte de ABAJO de la barba completa que sobra: la barba
    joven cuelga 88 px por debajo del mentón (hasta y1011) delante del
    cuello, y con el frente recortado esa punta se ve como un faldón
    suelto (marca de Stiven 2026-11-24). La referencia es el mismo
    personaje SIN barba (FH0): el mentón termina en y923 (el borde de
    la Base salta de x405 a x500 ahí) y la línea de la mandíbula sube
    hacia la oreja. Se recorta la barba por debajo de esa línea
    (curva por (405,923), (550,878), (700,832), medida en la
    referencia), con pluma de 3 px. Solo FH3."""
    # Línea de la mandíbula (referencia sin barba): cuadrática por 3 puntos
    x0, y0 = 405.0, 923.0
    x1, y1 = 550.0, 878.0
    x2, y2 = 700.0, 832.0
    # coeficientes de la parábola y = A x^2 + B x + C
    import numpy as _np
    A_, B_, C_ = _np.polyfit([x0, x1, x2], [y0, y1, y2], 2)
    def linea(x):
        if x <= x0:
            return y0
        return A_ * x * x + B_ * x + C_
    solido_antes = int((a[800:1020, :, 3] > 200).sum())
    for y in range(800, 1020):
        for x in range(300, 760):
            ly = linea(x)
            if y > ly + 3:
                a[y, x, 3] = 0
            elif y > ly:
                f = np.clip((ly + 3 - y) / 3.0, 0.0, 1.0)
                a[y, x, 3] *= f
    solido_despues = int((a[900:1020, :, 3] > 200).sum())
    informe['borde_inferior_recortado_px'] = int(solido_antes - solido_despues)
    print(f'    borde inferior recortado: {solido_antes - solido_despues} px sólidos '
          f'(línea de la mandíbula, mentón en y923)', flush=True)

def borde_frente_barba(a, informe):
    """Recorta el borde FRONTAL (izquierdo) de la barba completa para que
    no se pase de crecida: la barba joven sale 35-71 px por delante de la
    barbilla (en negro no se nota contra el fondo; en gris sí) y el
    bigote sale 15 px por delante de la cara. Se recorta siguiendo la
    curva de la barbilla (Base) con 12 px de margen, SOLO hasta y=925:
    por debajo de la barbilla la barba cuelga delante del cuello por
    diseño y su borde inferior ya redondea solo (recortar ahí con la
    línea del cuello borraba toda la punta de la barba). Solo FH3.
    El recorte lleva una pluma de 3 px para que el borde no quede duro."""
    base = np.asarray(Image.open(f'{ASSETS}/Male/Base.png').convert('RGBA'))
    sb = base[..., 3] > 0
    # barbilla: x mínimo de la Base por fila (solo cara, y<930), suavizado
    jaw = np.zeros(1600)
    for y in range(1600):
        xs = np.where(sb[y])[0]
        jaw[y] = xs.min() if len(xs) else 1200
    jaw = ndimage.uniform_filter1d(jaw, size=9, mode='nearest')
    # Borde frontal ORIGINAL de la barba (antes de recortar), para la
    # transición suave por debajo de la barbilla.
    sol_orig = a[..., 3] > 200
    frente_orig = np.full(1600, 1200.0)
    for y in range(1600):
        xs = np.where(sol_orig[y])[0]
        if len(xs):
            frente_orig[y] = xs.min()
    # Ancla de la transición: la línea de la barbilla en y=920. NO usar
    # jaw[925]: el suavizado ahí ya mezcla el cuello (el salto
    # barbilla->cuello contamina la media y la línea da un brinco de
    # ~35 px que deja una muesca en la barbilla).
    ancla = jaw[920] - 12
    solido_antes = int((a[680:930, :, 3] > 200).sum())
    for y in range(700, 961):
        if y < 840:
            frente = jaw[y] - 2   # bigote y hueco de la boca
        elif y <= 920:
            frente = jaw[y] - 12  # cuerpo de la barba: 12 px por delante
        else:
            # Transición suave (y921-960): del ancla (y920) al borde
            # natural de la barba, para no dejar un escalón horizontal
            # donde termina el recorte.
            t = (y - 920) / 40.0
            frente = ancla * (1 - t) + frente_orig[y] * t
        xi = int(np.floor(frente))
        if xi <= 0:
            continue
        # borrar todo a la izquierda del frente
        a[y, :xi, 3] = 0
        # pluma de 3 px sobre el borde: rampa de alfa
        for x in range(xi, min(1200, xi + 3)):
            f = np.clip((x - frente) / 3.0, 0.0, 1.0)
            a[y, x, 3] *= f
    solido_despues = int((a[680:930, :, 3] > 200).sum())
    informe['borde_frente_recortado_px'] = int(solido_antes - solido_despues)
    print(f'    borde frontal recortado: {solido_antes - solido_despues} px sólidos '
          f'(barbilla-12 hasta y925, bigote al borde)', flush=True)

def procesar_fh(n, nombre):
    ruta = f'{ASSETS}/Male/FacialHair{n}.png'
    a = np.asarray(Image.open(ruta).convert('RGBA')).astype(float)
    informe = dict(capa=f'FacialHair{n}', nombre=nombre)
    alfa_orig = a[..., 3].copy()
    informe['alfa_pos_orig'] = int((alfa_orig > 0).sum())
    informe['alfa_solido_orig'] = int((alfa_orig > 200).sum())

    # A. gris v8 (remapeo + streamlines), semilla por capa
    g = m.gris_v8(a, 'Male', f'FacialHair{n}')
    informe['gris'] = g
    print(f'FacialHair{n} ({nombre}): gris v8 ({g["hebras"]} hebras + {g["brillos"]} brillos)', flush=True)

    # B. limpieza según la capa (ver docstring)
    solido = a[..., 3] > 200
    comps, lab = m.componentes(solido)
    borrados = []
    if n == 1:
        # Mustache: borrar motas <40 px (son motas de 1-2 px alrededor del bigote)
        for c in comps[1:]:
            if c['n'] < 40:
                borrados.append(c)
    elif n == 2:
        # Stubble: borrar SOLO los puntos fuera de la silueta (fondo oscuro)
        fuera = solido & ~ndimage.binary_dilation(SILUETA, iterations=2)
        lab_f, nf = ndimage.label(fuera)
        for i in range(1, nf + 1):
            c = dict(n=int((lab_f == i).sum()))
            borrados.append(('mascara', lab_f == i, c['n']))
        # borrar por máscara directamente
        for _, masc, nn in borrados:
            ns, nh = m.borrar_mascara(a, masc)
        informe['borrados'] = [dict(tipo='fuera_silueta', n=nn) for _, _, nn in borrados]
        print(f'    B stubble fuera de silueta: {len(borrados)} manchas borradas', flush=True)
        borrados = []
    else:
        # Full Beard: borrar motas <40 px DESPEGADAS de la masa (>10 px)
        masa = lab == comps[0]['id']
        cerca = ndimage.binary_dilation(masa, iterations=10)
        for c in comps[1:]:
            if c['n'] < 40 and not (cerca & (lab == c['id'])).any():
                borrados.append(c)
    for c in borrados:
        masc = lab == c['id']
        ns, nh = m.borrar_mascara(a, masc)
        informe.setdefault('borrados', []).append(
            dict(tipo='mota', n=c['n'], x0=c['x0'], x1=c['x1'], y0=c['y0'], y1=c['y1'],
                 solido_borrado=ns, halo_borrado=nh))
    print(f'    B borrados: {len(informe.get("borrados", []))}', flush=True)

    # C. barrido final de fragmentos (solo FH1 y FH3; FH2 son puntos por diseño)
    if n != 2:
        # barrer_fragmentos usa mascara_diseno (rutas de pelo): no vale aquí.
        # En su lugar: motas nuevas tras el borrado.
        solido2 = a[..., 3] > 200
        comps2, _ = m.componentes(solido2)
        informe['componentes_tras_B'] = len(comps2)

    # D. redondeo + puntas (igual que el paso J del método de pelo)
    a = np.rint(np.clip(a, 0, 255))
    n_puntas = m.limpiar_puntas(a, informe)
    if n_puntas:
        print(f'    D puntas limpiadas: {n_puntas}', flush=True)
    informe['alfa_sube_px'] = int((a[..., 3] > alfa_orig).sum())

    # E. FH3: recortar el borde frontal (barba crecida de más, marca de
    # Stiven 2026-11-24) y el borde inferior (la punta que cuelga bajo
    # el mentón, marca de Stiven 2026-11-24 ~15:51). Van AL FINAL,
    # después de la limpieza: si van antes, los pasos B/D borran las
    # hebras finas del borde nuevo y dejan una muesca horizontal en la
    # barbilla. Solo la barba completa; FH1/FH2 no lo necesitan. Los
    # recortes solo quitan píxeles, no crean motas.
    if n == 3:
        borde_frente_barba(a, informe)
        borde_inferior_barba(a, informe)

    verificar(a, informe)
    out, md5 = guardar(a, f'Male_FacialHair{n}')
    informe['md5'] = md5
    informe['archivo'] = os.path.basename(out)
    print(f'FacialHair{n}: guardado md5={md5[:12]} | comps {len(comps)}->'
          f'{informe["componentes_final"]} | motas {informe["motas_final"]} | '
          f'polvo_aislado {informe["polvo_aislado_clusters"]}cl', flush=True)
    return informe

def main():
    informe_global = {}
    for n, nombre in [(1, 'Mustache'), (2, 'Stubble'), (3, 'Full Beard')]:
        informe_global[f'Male_FacialHair{n}'] = procesar_fh(n, nombre)
    with open(os.path.join(EDAD, f'informe_vello_{VERSION}.json'), 'w') as f:
        json.dump(informe_global, f, indent=1)
    print('informe guardado en informe_vello_v11.1.json')
    print('listo')

if __name__ == '__main__':
    main()
