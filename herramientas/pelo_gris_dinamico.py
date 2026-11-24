"""Pelo anciano v11 — MÉTODO DINÁMICO GRIS (Fase 2 del trabajo de EDAD).

Convierte CUALQUIER peinado a gris anciano limpiamente, con prevención de
retazos incorporada. Parte SIEMPRE de la capa ORIGINAL joven (no de v8/v9/
v10, que acumulan cortes) y reaplica el gris v8 + la limpieza.

Método (en orden, por capa):
  A. Gris v8: remapeo de luminancia (pelo_canas_v8.CURVA, v8.3) + streamlines
     v8.3 largas y pocas, con los resguardos v11: las streamlines se siembran
     y caminan SOLO donde la distancia al borde de la masa es >=6 px (antes:
     erosión de 4 px) y el peso gaussiano solo se aplica donde la distancia
     al borde es >=2 px (antes: sobre todo alfa>0) — así ninguna streamline
     acentúa un filamento del borde ni el halo.
  B. Componentes tras el gris (alfa>200, 4-conexidad): la masa y los mechones
     de diseño (lista DISEÑO por peinado, abajo) se quedan; las motas (n<40)
     y los hilos finos (ancho mediano <=6 px, largo >30 px) que NO están en
     la lista se borran. El borrado opera sobre alfa>0 COMPLETO (sólido +
     halo, por Voronoi al sólido más cercano) — la lección v9/v10: borrar
     solo alfa>200 deja motas y halos punteados.
  C. Dedos (filamentos conectados, ancho local <=4 px durante >30 px):
     detector por distancia al núcleo del mismo componente; se borra el dedo
     si su componente NO está en la lista DISEÑO (los dedos de un mechón de
     diseño se quedan). La red de seguridad es el bucle de render (paso H).
  D. Despeje de la ceja (solo Front): el flequillo se recorta por encima de
     la curva superior de CADA ceja (Eyes_Neutral, solo columnas con ceja
     real — sin extrapolar más allá de sus extremos, que es lo que en v9
     cortó la hebra de la sien F); corte = top_ceja - 14 px, caída suave
     de 8 px. REGLA v11.1 (Fase 4, ciclo 1): el recorte con rampa se aplica
     a TODO intervalo que NAZCA por encima de la línea de corte (es
     flequillo/masa, aunque el cierre lo haya partido en dos por una
     rendija del arte); el borrado ENTERO solo se aplica a intervalos que
     nacen EN o BAJO la línea y tocan la banda (hebra suelta colgando
     sobre la ceja). La v11 borraba entero cualquier intervalo separado
     que tocara la banda, y cuando el primer intervalo era una astilla
     de 1-2 px y el segundo era la masa entera, borraba LA MASA y dejaba
     una RANURA vertical de piel en el flequillo (F H8, H9 y H10 en el
     vídeo del ciclo 1; H10: 12.043 px). La rampa deja la ceja igual de
     despejada: todo lo que queda bajo la línea se pone a 0.
  E. Oreja (solo Front): ningún componente desconectado dentro de la zona
     de la oreja (caja derivada del contorno oscuro de la Base) + limpieza
     del polvo antialiased dentro de la caja.
  F. Repisa bajo la oreja (solo Front): si el borde inferior de la masa
     forma una repisa horizontal bajo la oreja seguida de un escalón hacia
     la patilla, se talla el frente en diagonal suave (como v10).
  G. Sien: si el despeje de la ceja creó un muro vertical recto en la zona
     de la sien, se redondea tallando una curva suave (como v10).
  H. Polvo y cierre: tras cada borrado, diff de corte obligatorio (ninguna
     mota n>=2 ni halo >20 px restantes en la ventana). El polvo aislado
     (alfa 20-200 a >3 px del sólido, en racimos <100 px) se borra; los
     racimos grandes (>=100 px) son el borde suave / sombra del pelo y se
     conservan y se listan. Métrica de cierre: polvo = 0 en cada zona
     tratada.
  I. Bucle de render (render_v11.py / verificar_v11.py, fuera de este
     script): el render gris vs el control joven marca los retazos
     revelados (contraste gris >60 donde el joven tiene <15); todo retazo
     que quede se vuelve al método (pasos B/C) y se re-renderiza.

Regla de Stiven (2026-11-24 ~11:53): todo arreglo que nazca de un retazo y
sea del método queda EN EL MÉTODO y se aplica a los 16 peinados, nunca como
parche de una sola capa. La lista DISEÑO es dato del método (se construye
con el inventario + la inspección visual del render joven) y es lo único
por peinado; las reglas son las mismas para los 16.

Entrada: version-linux/assets/{Female,Male}/Hair{N}_{Front,Back}.png
Salida: {Sexo}_Hair{N}_{Front,Back}_canas_v11_1.png (+ informe JSON).
No toca version-linux/assets/ ni las v9/v10/v11. No sube nada.
Uso: python3 pelo_gris_dinamico.py

v11.1 (2026-11-24, Fase 4 ciclo 1): corrección del paso D (ver arriba).
Re-aplicado a los 16 peinados; las capas que no cambian conservan su md5 v11.
"""
import os, sys, json, hashlib, zlib
import numpy as np
from PIL import Image
from scipy import ndimage

VERSION = 'v11_3'  # sufijo de salida: *_canas_v11_3.png, informe_v11_3.json

EDAD = os.path.dirname(os.path.abspath(__file__))
PROYECTO = os.path.dirname(os.path.dirname(EDAD))
ASSETS = os.path.join(PROYECTO, 'version-linux', 'assets')
ESTR8 = np.ones((3, 3), dtype=bool)

# ------------------------------------------------------------------ gris v8
CURVA_IN = np.array([0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 110, 140, 255], dtype=float)
CURVA_OUT = np.array([55, 62, 72, 85, 98, 108, 120, 150, 168, 171, 184, 196, 208, 220, 255], dtype=float)

def remapear(rgb):
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    g = np.interp(lum, CURVA_IN, CURVA_OUT)
    return np.stack([g - 1.0, g, g + 2.0], axis=-1)

DIST_MIN = 45.0

def campo_flujo(lum, mascara):
    gx = ndimage.gaussian_filter(lum, 3, order=(0, 1))
    gy = ndimage.gaussian_filter(lum, 3, order=(1, 0))
    jxx = ndimage.gaussian_filter(gx * gx, 12)
    jxy = ndimage.gaussian_filter(gx * gy, 12)
    jyy = ndimage.gaussian_filter(gy * gy, 12)
    ang_grad = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    ang_hebra = ang_grad + np.pi / 2
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
    ys, xs = np.where(mascara)
    y_top = np.percentile(ys, 2)
    cx = float(np.median(xs[ys < y_top + 80])) if (ys < y_top + 80).sum() > 50 else float(np.median(xs))
    cy = float(y_top)
    yy, xx = np.mgrid[0:lum.shape[0], 0:lum.shape[1]]
    rx, ry = xx - cx, yy - cy
    r = np.hypot(rx, ry) + 1e-6
    dx = 0.55 * rx / r
    dy = 0.55 * ry / r + 0.45
    ang_geo = np.arctan2(dy, dx)
    w = np.clip(coh / 0.3, 0, 1)
    s = np.sin(2 * ang_hebra) * w + np.sin(2 * ang_geo) * (1 - w)
    c = np.cos(2 * ang_hebra) * w + np.cos(2 * ang_geo) * (1 - w)
    s = ndimage.gaussian_filter(s, 25)
    c = ndimage.gaussian_filter(c, 25)
    return 0.5 * np.arctan2(s, c)

def trazar_streamline(x0, y0, ang, dentro, largo_max, paso=4.0):
    h, w = ang.shape
    pts_f = [(x0, y0)]
    x, y = x0, y0
    L = 0.0
    while L < largo_max / 2:
        ix, iy = int(round(x)), int(round(y))
        if not (0 <= ix < w and 0 <= iy < h):
            break
        th = ang[iy, ix]
        x += np.cos(th) * paso
        y += np.sin(th) * paso
        ix, iy = int(round(x)), int(round(y))
        if not (0 <= ix < w and 0 <= iy < h) or not dentro[iy, ix]:
            break
        pts_f.append((x, y))
        L += paso
    pts_b = []
    x, y = x0, y0
    L = 0.0
    while L < largo_max / 2:
        ix, iy = int(round(x)), int(round(y))
        if not (0 <= ix < w and 0 <= iy < h):
            break
        th = ang[iy, ix]
        x -= np.cos(th) * paso
        y -= np.sin(th) * paso
        ix, iy = int(round(x)), int(round(y))
        if not (0 <= ix < w and 0 <= iy < h) or not dentro[iy, ix]:
            break
        pts_b.append((x, y))
        L += paso
    pts = pts_b[::-1] + pts_f
    if len(pts) < 12:
        return None
    return np.array(pts, dtype=float)

def peso_streamlines(lineas, shape, mascara_peso):
    h, w = shape
    W = np.zeros((h, w), dtype=float)
    for pts, sigma in lineas:
        seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
        total = seg.sum()
        if total < 10:
            continue
        n = max(8, int(total))
        t = np.linspace(0, 1, n)
        s = np.concatenate([[0], np.cumsum(seg)])
        cx = np.interp(t * total, s, pts[:, 0])
        cy = np.interp(t * total, s, pts[:, 1])
        r = int(np.ceil(3 * sigma + 3))
        xlo, xhi = max(0, int(cx.min()) - r), min(w, int(cx.max()) + r + 1)
        ylo, yhi = max(0, int(cy.min()) - r), min(h, int(cy.max()) + r + 1)
        if xhi <= xlo or yhi <= ylo:
            continue
        gx, gy = np.meshgrid(np.arange(xlo, xhi), np.arange(ylo, yhi))
        d2 = np.full(gx.shape, 1e9)
        for k in range(0, len(cx), 8):
            dblk = (gx[None, :, :] - cx[k:k + 8, None, None]) ** 2 + \
                   (gy[None, :, :] - cy[k:k + 8, None, None]) ** 2
            d2 = np.minimum(d2, dblk.min(axis=0))
        g = np.exp(-d2 / (2 * sigma * sigma))
        vx, vy = pts[-1, 0] - pts[0, 0], pts[-1, 1] - pts[0, 1]
        vn = np.hypot(vx, vy) + 1e-6
        ux, uy = vx / vn, vy / vn
        s_pos = (gx - pts[0, 0]) * ux + (gy - pts[0, 1]) * uy
        s_pos = np.clip(s_pos / total, 0, 1)
        tp = np.clip(1.0 - (np.abs(s_pos - 0.5) * 2 - 0.6) / 0.4, 0.0, 1.0)
        W[ylo:yhi, xlo:xhi] = np.maximum(W[ylo:yhi, xlo:xhi], g * tp)
    return W * mascara_peso

def gris_v8(a, sexo, parte):
    """Remapeo v8.3 + streamlines v8.3 con resguardos v11 (semilla y camino
    a >=6 px del borde de la masa; peso solo a >=2 px del borde)."""
    orig = a[..., :3]
    alfa = a[..., 3]
    lum = 0.299 * orig[..., 0] + 0.587 * orig[..., 1] + 0.114 * orig[..., 2]
    opaco = alfa > 200
    pelo = (alfa > 0).astype(float)
    gris = remapear(orig)
    dist = ndimage.distance_transform_edt(opaco)
    # v11: dentro = >=6 px del borde (antes erosión de 4 px)
    dentro = dist >= 6.0
    oscuro = (lum < 40).astype(float)
    frac_oscuro = ndimage.uniform_filter(oscuro, size=31)
    plano = dentro & (frac_oscuro < 0.08)
    ang = campo_flujo(np.where(opaco, lum, 165.0), opaco)
    ys, xs = np.where(plano)
    n_px = int(opaco.sum())
    n_hebras = int(38 * n_px / 100000)
    n_brillos = int(22 * n_px / 100000)
    semilla = int(zlib.crc32(f'{sexo}_{parte}'.encode()) % 100000)
    rng = np.random.default_rng(semilla)

    def recoger(n, sem):
        r = np.random.default_rng(sem)
        celdas, celda = {}, DIST_MIN
        out = []
        intentos = 0
        while len(out) < n and intentos < n * 300 and len(xs):
            intentos += 1
            i = r.integers(0, len(xs))
            x0, y0 = float(xs[i]), float(ys[i])
            cx, cy = int(x0 // celda), int(y0 // celda)
            ok = True
            for gx in (cx - 1, cx, cx + 1):
                for gy in (cy - 1, cy, cy + 1):
                    for (px, py) in celdas.get((gx, gy), ()):
                        if (px - x0) ** 2 + (py - y0) ** 2 < DIST_MIN ** 2:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                continue
            celdas.setdefault((cx, cy), []).append((x0, y0))
            out.append((x0, y0))
        return out

    lineas_h, lineas_b = [], []
    for (x0, y0) in recoger(n_hebras, semilla):
        largo = float(rng.uniform(120, 300))
        sigma = float(rng.uniform(0.8, 1.1))
        pts = trazar_streamline(x0, y0, ang, dentro, largo)
        if pts is not None:
            lineas_h.append((pts, sigma))
    for (x0, y0) in recoger(n_brillos, semilla + 7):
        largo = float(rng.uniform(60, 150))
        sigma = float(rng.uniform(0.7, 1.0))
        pts = trazar_streamline(x0, y0, ang, dentro, largo)
        if pts is not None:
            lineas_b.append((pts, sigma))
    # v11: el peso solo se aplica a >=2 px del borde (antes: todo alfa>0)
    mascara_peso = (dist >= 2.0).astype(float)
    W_h = peso_streamlines(lineas_h, (1600, 1200), mascara_peso)
    W_b = peso_streamlines(lineas_b, (1600, 1200), mascara_peso)
    out = gris.copy()
    out = out * (1 - 0.78 * W_h[..., None]) + 72.0 * (0.78 * W_h[..., None])
    out = out * (1 - 0.85 * W_b[..., None]) + 212.0 * (0.85 * W_b[..., None])
    a[..., :3] = np.where((alfa > 0)[..., None], out, orig)
    a[..., 3] = alfa
    return dict(hebras=len(lineas_h), brillos=len(lineas_b))

# ------------------------------------------------------------------ borrado
def borrar_mascara(a, mascara):
    """Borra alfa=0 en `mascara` (píxeles sólidos a borrar) + su halo:
    un píxel con alfa>0 se borra si está más cerca de la máscara que de
    cualquier pelo que se queda. Opera sobre alfa>0 COMPLETO."""
    solido = a[..., 3] > 200
    queda = solido & ~mascara
    d_queda = ndimage.distance_transform_edt(~queda)
    d_borra = ndimage.distance_transform_edt(~mascara)
    halo = (a[..., 3] > 0) & (d_borra < d_queda)
    n_sol = int((mascara & (a[..., 3] > 0)).sum())
    n_halo = int((halo & ~mascara).sum())
    a[mascara, 3] = 0
    a[halo, 3] = 0
    return n_sol, n_halo

def componentes(solido):
    lab, n = ndimage.label(solido)
    sizes = np.bincount(lab.ravel())
    slices = ndimage.find_objects(lab)
    dt = ndimage.distance_transform_edt(solido)
    out = []
    for i in range(1, n + 1):
        s = slices[i - 1]
        sub = lab[s] == i
        d = dt[s][sub]
        out.append(dict(id=int(i), n=int(sizes[i]),
                        x0=int(s[1].start), x1=int(s[1].stop) - 1,
                        y0=int(s[0].start), y1=int(s[0].stop) - 1,
                        ancho_med=float(2 * np.median(d)),
                        ancho_max=float(2 * d.max()),
                        largo=int(max(s[1].stop - s[1].start, s[0].stop - s[0].start))))
    out.sort(key=lambda c: -c['n'])
    return out, lab

def polvo_lejos(a):
    """Polvo lejos de la masa: píxeles alfa 20-200 a >3 px del sólido.
    Incluye la rampa del corte de la ceja (v9/v10 tienen el mismo racimo
    de ~260 px: es el borde suavizado del corte, no un retazo)."""
    solido = a[..., 3] > 200
    cerca = ndimage.binary_dilation(solido, iterations=3)
    polvo = (a[..., 3] >= 20) & (a[..., 3] <= 200) & ~cerca
    lab, n = ndimage.label(polvo)
    sizes = np.bincount(lab.ravel())[1:] if n else []
    return int(polvo.sum()), int(n), [int(s) for s in sorted(sizes, reverse=True)[:5]]

def polvo_aislado_mascara(a):
    """Máscara del polvo aislado: alfa 20-200 a >10 px del sólido."""
    sol = a[..., 3] > 200
    lejos = ~ndimage.binary_dilation(sol, iterations=10)
    return (a[..., 3] >= 20) & (a[..., 3] <= 200) & lejos

def polvo_aislado(a):
    """Polvo AISLADO (la métrica de verificación): racimos de alfa 20-200
    a >10 px del sólido con n>=20 px. La rampa del corte de la ceja está
    a <=9 px del sólido y no cuenta; un racimo aislado sí sería un retazo.
    Devuelve (n_px, n_clusters, top)."""
    masc = polvo_aislado_mascara(a)
    lab, n = ndimage.label(masc)
    sizes = np.bincount(lab.ravel())[1:] if n else []
    grandes = [int(s) for s in sizes if s >= 20]
    return int(masc.sum()), len(grandes), sorted(grandes, reverse=True)[:5]

def limpiar_puntas(a, informe):
    """Puntas de gradiente: un píxel con alfa>200 sin ningún vecino sólido
    en cruz (arriba/abajo/izquierda/derecha) es un artefacto de la
    conectividad-4: toca pelo solo en diagonal y `componentes()` lo cuenta
    como un componente de 1 px, pero visualmente es parte del borde suave
    (su alfa es 201-210 y sus vecinos 150-200). Se baja su alfa al máximo
    de sus vecinos en cruz (deja de ser sólido y se funde con el borde).
    Un pelo real siempre tiene un vecino en cruz (una hebra de 1 px de
    ancho tiene vecino a lo largo de la hebra)."""
    sol = a[..., 3] > 200
    cruz = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=int)
    suma = ndimage.convolve(sol.astype(int), cruz, mode='constant')
    puntas = sol & (suma == 1)
    n = int(puntas.sum())
    if n:
        # máximo de los vecinos en cruz SIN el centro (el centro es el
        # propio píxel, 201-210, y lo dejaría igual)
        cruz_sin_centro = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=int)
        maxvec = ndimage.maximum_filter(a[..., 3], footprint=cruz_sin_centro)
        a[puntas, 3] = maxvec[puntas]
        informe['puntas_limpiadas'] = n
    return n

def barrer_motas(a, informe, etiqueta):
    """Diff de corte con efecto: borra (con halo) todos los componentes
    alfa>200 con n<40 que queden tras un paso de forma (un corte puede
    cercenar un fragmento de la masa). Devuelve el nº borrado."""
    solido = a[..., 3] > 200
    comps, lab = componentes(solido)
    n_borrados = 0
    for c in comps[1:]:
        if c['n'] < 40:
            m = lab == c['id']
            ns, nh = borrar_mascara(a, m)
            n_borrados += 1
            informe.setdefault('motas_barridas', []).append(
                dict(paso=etiqueta, n=c['n'], x0=c['x0'], x1=c['x1'],
                     y0=c['y0'], y1=c['y1'], solido_borrado=ns, halo_borrado=nh))
    return n_borrados

def barrer_fragmentos(a, clave, informe, etiqueta):
    """Barrido de fragmentos tras un corte: un corte (ceja, sien, repisa,
    dedos, polvo) puede CERCENAR un trozo de la masa y dejarlo como un
    componente fino desconectado (un hilo que en el original era parte de
    la masa). Se borran (con halo) las motas (n<40) y los hilos finos
    (ancho mediano <=6, largo >30) que NO sean parte de un mechón de
    diseño (criterio suelto: más de la mitad de su caja dentro de un
    mechón listado). Se repite hasta que un pase no borre nada (borrar un
    fragmento puede aislar otro píxel). Devuelve el nº borrado."""
    total = 0
    for _pase in range(3):
        solido = a[..., 3] > 200
        comps, lab = componentes(solido)
        n_borrados = 0
        for c in comps[1:]:
            es_hilo = c['ancho_med'] <= 6.0 and c['largo'] > 30
            if c['n'] < 40 or es_hilo:
                if es_diseno_suelto(clave, c, lab):
                    informe.setdefault('fragmentos_conservados', []).append(
                        dict(paso=etiqueta, n=c['n'], x0=c['x0'], x1=c['x1'],
                             y0=c['y0'], y1=c['y1']))
                    continue
                m = lab == c['id']
                ns, nh = borrar_mascara(a, m)
                n_borrados += 1
                informe.setdefault('fragmentos_barridos', []).append(
                    dict(paso=etiqueta, tipo='mota' if c['n'] < 40 else 'hilo',
                         n=c['n'], ancho_med=round(c['ancho_med'], 1), largo=c['largo'],
                         x0=c['x0'], x1=c['x1'], y0=c['y0'], y1=c['y1'],
                         solido_borrado=ns, halo_borrado=nh))
        total += n_borrados
        if n_borrados == 0:
            break
    return total

def motas_y_halo(a, ventana=None):
    """Diff de corte obligatorio: motas (componentes alfa>200 con n>=2) y
    polvo (alfa 20-200 a >3 px del sólido) restantes en la ventana (o en
    toda la capa). Un corte no está terminado mientras queden. Las motas
    se etiquetan en TODA la capa y solo cuentan las que están ENTERAS
    dentro de la ventana (un componente cortado por el borde de la ventana
    no es una mota: es parte de la masa)."""
    sol = a[..., 3] > 200
    cerca = ndimage.binary_dilation(sol, iterations=3)
    polvo_full = (a[..., 3] >= 20) & (a[..., 3] <= 200) & ~cerca
    lab, n = ndimage.label(sol)
    sizes = np.bincount(lab.ravel())[1:] if n else []
    slices = ndimage.find_objects(lab)
    if ventana is None:
        sub_polvo = polvo_full
        motas = [int(s) for s in sizes if 2 <= s < 40]
    else:
        x0, y0, x1, y1 = ventana
        sub_polvo = polvo_full[y0:y1 + 1, x0:x1 + 1]
        motas = []
        for i in range(1, n + 1):
            if 2 <= sizes[i - 1] < 40:
                s = slices[i - 1]
                if s[1].start >= x0 and s[1].stop - 1 <= x1 and \
                        s[0].start >= y0 and s[0].stop - 1 <= y1:
                    motas.append(int(sizes[i - 1]))
    return motas, int(sub_polvo.sum())

# ------------------------------------------------------------------ DISEÑO
# Mechones de diseño por peinado: (n, x0, x1, y0, y1) del componente en la
# capa ORIGINAL. Se construyó con el inventario (inventario_v11.json) +
# la inspección visual del render joven: son colas, trenzas, moños,
# mechones largos, ondas, rizos o mechones decorativos — partes de la
# silueta del peinado. Todo hilo fino que NO está aquí se borra (paso B).
# Clave: (sexo, nº, parte). Un componente en la lista se conserva entero,
# incluidos sus dedos (paso C).
DISENO = {
    ('Female', 1, 'Back'): [(5210, 544, 655, 1307, 1597),   # #79 mechón inf. centro (Fase 1: diseño)
                            (1313, 691, 768, 719, 780)],   # mechón der. tras la oreja
    ('Female', 4, 'Front'): [(184, 456, 473, 1543, 1592)],  # punta de onda inf. centro
    ('Female', 4, 'Back'): [(2828, 682, 768, 718, 958),    # mechón ondulado der.
                            (1751, 288, 465, 1247, 1597)], # mechón ondulado izq.
    ('Female', 5, 'Front'): [(822, 345, 449, 1280, 1458),   # hebra cola izq.
                            (346, 391, 452, 826, 919),      # hebra cola izq. (cuello)
                            (101, 764, 780, 987, 1023)],   # hebra cola der.
    ('Female', 6, 'Front'): [(1636, 456, 689, 1138, 1594),  # coleta alta: hebras
                            (882, 290, 386, 1386, 1594),
                            (758, 255, 302, 1416, 1594),
                            (604, 548, 644, 1451, 1594),
                            (449, 219, 258, 1458, 1594)],
    ('Female', 7, 'Front'): [(1088, 371, 558, 1060, 1271),  # trenza: hebras
                            (989, 278, 445, 1139, 1397),
                            (202, 422, 523, 901, 921),      # hebra horizontal sup. trenza
                            (116, 767, 840, 118, 139),      # mechón coronilla
                            (1560, 332, 359, 726, 879)],   # tira izq. de la trenza
    ('Female', 10, 'Front'): [(2144, 456, 779, 1041, 1594),  # moño despeinado: hebras sueltas
                            (1023, 553, 701, 1366, 1584),
                            (850, 374, 485, 1134, 1294),
                            (720, 255, 314, 1384, 1594),
                            (590, 305, 415, 1157, 1316),
                            (585, 541, 597, 1086, 1128)],
    ('Female', 11, 'Front'): [(5322, 258, 597, 1083, 1594),  # coleta lateral
                            (2139, 311, 587, 1033, 1297),
                            (648, 245, 300, 1334, 1513),   # hebra suelta izq.
                            (296, 218, 243, 1517, 1594),   # hebra suelta izq. inf.
                            (5543, 350, 548, 785, 1090)],  # mechón delantero grande
    ('Female', 12, 'Front'): [(198, 434, 452, 1537, 1594),   # puntas de rizo inf.
                            (139, 689, 694, 1554, 1594),
                            (12849, 2, 12, 2, 1594)],      # banda del borde izq. del lienzo
    ('Male', 2, 'Front'): [(791, 206, 233, 387, 433),       # mechón lateral decorativo
                            (501, 221, 251, 239, 268)],     # mechón sup. izq.
    ('Male', 3, 'Front'): [(930, 201, 233, 387, 433)],      # mechón lateral decorativo
    ('Male', 4, 'Front'): [(517, 219, 252, 238, 270),       # mechón sup. izq.
                            (967, 194, 233, 387, 433)],     # mechón lateral decorativo
    ('Male', 4, 'Back'): [(605, 475, 507, 249, 281)],       # mechón trasero
}

def es_diseno(clave, comp):
    """¿Es este componente un mechón de diseño? Coincidencia EXACTA con la
    lista (para el paso B, sobre los componentes del original)."""
    for (n, x0, x1, y0, y1) in DISENO.get(clave, []):
        if comp['n'] == n and comp['x0'] == x0 and comp['x1'] == x1 \
                and comp['y0'] == y0 and comp['y1'] == y1:
            return True
    return False

_DISENO_MASCARA = {}

def mascara_diseno(clave):
    """Máscara de los mechones de diseño (del ORIGINAL) dilatada 10 px.
    Un fragmento partido de un mechón por un corte queda a <=10 px de su
    mechón (el corte solo quita un puente fino); un hilo suelto en un hueco
    está a >25 px. Se usa en los barridos tras los cortes."""
    if clave in _DISENO_MASCARA:
        return _DISENO_MASCARA[clave]
    sexo, h, parte = clave
    ruta = os.path.join(ASSETS, sexo, f'Hair{h}_{parte}.png')
    o = np.asarray(Image.open(ruta).convert('RGBA'))
    sol = o[..., 3] > 200
    comps, lab = componentes(sol)
    masc = np.zeros(sol.shape, dtype=bool)
    for c in comps:
        if es_diseno(clave, c):
            masc |= lab == c['id']
    masc = ndimage.binary_dilation(masc, iterations=10)
    _DISENO_MASCARA[clave] = masc
    return masc

def es_diseno_suelto(clave, comp, lab):
    """¿Es este componente (posiblemente un fragmento de un mechón de
    diseño partido por un corte) parte de un mechón de diseño? Sí si
    alguno de sus píxeles toca la máscara de diseño dilatada 10 px.
    El criterio por caja era demasiado laxo: un hilo suelto dentro de la
    caja grande de un mechón se conservaba por error."""
    return bool((mascara_diseno(clave) & (lab == comp['id'])).any())

# ------------------------------------------------------------------ paso B
def paso_componentes(a, clave, informe):
    """Motas (n<40) e hilos finos (ancho mediano <=6, largo >30) que no
    están en DISEÑO: borrar con halo. Devuelve el nº borrado."""
    solido = a[..., 3] > 200
    comps, lab = componentes(solido)
    informe['componentes_antes'] = len(comps)
    informe['masa_n'] = comps[0]['n'] if comps else 0
    borrados, conservados = [], []
    for c in comps[1:]:
        if c['n'] < 40:
            borrados.append(('mota', c))
        elif c['ancho_med'] <= 6.0 and c['largo'] > 30:
            if es_diseno(clave, c):
                conservados.append(('diseno', c))
            else:
                borrados.append(('hilo', c))
        else:
            conservados.append(('mechon', c))
    for tipo, c in borrados:
        m = lab == c['id']
        ns, nh = borrar_mascara(a, m)
        informe.setdefault('borrados', []).append(
            dict(tipo=tipo, n=c['n'], ancho_med=round(c['ancho_med'], 1),
                 largo=c['largo'], x0=c['x0'], x1=c['x1'], y0=c['y0'], y1=c['y1'],
                 solido_borrado=ns, halo_borrado=nh))
    informe['conservados'] = [dict(tipo=t, n=c['n'], ancho_med=round(c['ancho_med'], 1),
                                   largo=c['largo'], x0=c['x0'], x1=c['x1'],
                                   y0=c['y0'], y1=c['y1'])
                              for t, c in conservados]
    return len(borrados)

# ------------------------------------------------------------------ paso C
def dedos_D(a):
    """Dedos por distancia al núcleo del mismo componente (dedos_v11.py):
    componente conexa de {D>3} con píxeles a D>30 del núcleo. Devuelve
    lista de (máscara, comp_id, largo, punta)."""
    solido = a[..., 3] > 200
    dt = ndimage.distance_transform_edt(solido)
    nucleo = dt > 2.0
    lab, ncomp = ndimage.label(solido)
    sizes = np.bincount(lab.ravel())
    slices = ndimage.find_objects(lab)
    out = []
    for c in range(1, ncomp + 1):
        if sizes[c] < 500:
            continue
        s = slices[c - 1]
        y0, y1 = max(0, s[0].start - 2), min(solido.shape[0], s[0].stop + 2)
        x0, x1 = max(0, s[1].start - 2), min(solido.shape[1], s[1].stop + 2)
        comp = (lab[y0:y1, x0:x1] == c)
        sub_nuc = nucleo[y0:y1, x0:x1] & comp
        if not sub_nuc.any():
            continue
        D = ndimage.distance_transform_edt(~sub_nuc)
        D = np.where(comp, D, 0)
        lejos = comp & (D > 3)
        labf, nf = ndimage.label(lejos, structure=ESTR8)
        if nf == 0:
            continue
        fsizes = np.bincount(labf.ravel())
        for i in range(1, nf + 1):
            if fsizes[i] < 5:
                continue
            m = labf == i
            dmax = float(D[m].max())
            if dmax <= 30:
                continue
            ys, xs = np.where(m)
            ip = int(np.argmax(D[m]))
            masc = np.zeros(solido.shape, dtype=bool)
            masc[y0:y1, x0:x1][m] = True
            out.append(dict(mascara=masc, comp=int(c), comp_n=int(sizes[c]),
                            n=int(fsizes[i]), largo=round(dmax, 1),
                            x0=int(xs.min() + x0), x1=int(xs.max() + x0),
                            y0=int(ys.min() + y0), y1=int(ys.max() + y0),
                            punta=[int(xs[ip] + x0), int(ys[ip] + y0)]))
    out.sort(key=lambda d: -d['largo'])
    return out

def paso_dedos(a, clave, informe):
    """Borra los dedos de componentes que NO están en DISEÑO (los dedos de
    un mechón de diseño se quedan). El bucle de render (paso I) es la red
    de seguridad para los dedos marginales que este detector no ve."""
    solido = a[..., 3] > 200
    comps, lab = componentes(solido)
    por_id = {c['id']: c for c in comps}
    n_borrados = 0
    for d in dedos_D(a):
        c = por_id.get(d['comp'])
        if c is None:
            continue
        if es_diseno(clave, c):
            informe.setdefault('dedos_conservados', []).append(
                dict(comp_n=c['n'], largo=d['largo'], punta=d['punta']))
            continue
        ns, nh = borrar_mascara(a, d['mascara'])
        n_borrados += 1
        informe.setdefault('dedos_borrados', []).append(
            dict(comp_n=c['n'], n=d['n'], largo=d['largo'],
                 x0=d['x0'], x1=d['x1'], y0=d['y0'], y1=d['y1'],
                 punta=d['punta'], solido_borrado=ns, halo_borrado=nh))
    return n_borrados

# ------------------------------------------------------------------ cejas
def curvas_ceja(sexo):
    """Curvas (top, bot) por columna de CADA ceja de Eyes_Neutral, solo
    sobre columnas con ceja real (sin extrapolar más allá de sus extremos).
    Devuelve lista de (x0, top[], bot[])."""
    ruta = os.path.join(ASSETS, sexo, 'Eyes_Neutral.png')
    e = np.asarray(Image.open(ruta).convert('RGBA')).astype(int)
    lum = e[..., :3].mean(axis=2)
    oscuro = (e[..., 3] > 200) & (lum < 120)
    lab, n = ndimage.label(oscuro)
    sizes = np.bincount(lab.ravel())
    slices = ndimage.find_objects(lab)
    # Una ceja es un componente oscuro HORIZONTAL (ancho > 2x alto), con
    # n>=100 y por encima de y=510. El ojo lejano es vertical (alto > ancho)
    # y la ceja lejana se funde con él: no se usa (el bucle de render la cubre).
    cejas = []
    for i in range(1, n + 1):
        if sizes[i] < 100:
            continue
        s = slices[i - 1]
        if s[0].start > 510:
            continue
        ancho = s[1].stop - s[1].start
        alto = s[0].stop - s[0].start
        if ancho < 2 * alto:
            continue
        cejas.append((i, s))
    out = []
    for i, s in cejas[:2]:
        x0, x1, y0, y1 = s[1].start, s[1].stop, s[0].start, s[0].stop
        top = np.full(x1 - x0, np.nan)
        bot = np.full(x1 - x0, np.nan)
        for j, x in enumerate(range(x0, x1)):
            col = np.where(oscuro[y0:y1, x])[0]
            if len(col):
                top[j] = col.min() + y0
                bot[j] = col.max() + y0
        xs = np.arange(len(top))
        ok = ~np.isnan(top)
        if ok.sum() < 10:
            continue
        # interpolar SOLO dentro del rango con datos; fuera, no hay ceja
        top_i = np.interp(xs, xs[ok], top[ok])
        bot_i = np.interp(xs, xs[ok], bot[ok])
        top_i = ndimage.median_filter(top_i, size=9, mode='nearest')
        bot_i = ndimage.median_filter(bot_i, size=9, mode='nearest')
        out.append((x0, top_i, bot_i, bool(ok[0]), bool(ok[-1])))
    out.sort(key=lambda t: t[0])
    return out

def intervalos_cerrados(col):
    cerrado = ndimage.binary_closing(col, structure=np.ones(7, dtype=bool))
    out = []
    s = None
    for i, v in enumerate(cerrado):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((s, i - 1))
            s = None
    if s is not None:
        out.append((s, len(col) - 1))
    return out

def paso_ceja(a, sexo, informe):
    """Despeje de la ceja (solo Front). Recorte del flequillo por encima de
    la curva de cada ceja (corte = top - 14 px, con rampa de 8 px).
    REGLA v11.1: la rampa se aplica a TODO intervalo que NAZCA por encima
    de la línea de corte (es flequillo/masa, aunque el cierre lo haya
    partido en dos por una rendija del arte: en v11 el primer intervalo
    era a veces una astilla de 1-2 px y el segundo la masa entera, y el
    borrado entero de ese segundo intervalo dejaba una ranura vertical
    de piel en el flequillo — F H8, H9, H10 en el vídeo del ciclo 1).
    El borrado ENTERO solo se aplica a intervalos que nacen EN o BAJO la
    línea y tocan la banda (hebra suelta colgando sobre la ceja, el caso
    v9). La ceja queda igual de despejada: la rampa pone a 0 todo lo que
    queda bajo la línea. El muro vertical que queda en el extremo de la
    ceja lo redondea el paso G (sien); aquí NO se suaviza la máscara."""
    if informe.get('parte') != 'Front':
        return 0
    alpha = a[..., 3]
    n_total = 0
    for (x0, top, bot, _, _) in curvas_ceja(sexo):
        for j, x in enumerate(range(x0, x0 + len(top))):
            corte = top[j] - 14.0
            yb = bot[j] + 30.0
            col = alpha[:700, x] > 200
            ivs = intervalos_cerrados(col)
            if not ivs:
                continue
            for (a1, b1) in ivs:
                if a1 < corte - 6:
                    # Nace por encima de la línea: es flequillo/masa.
                    # Rampa (nunca borrado entero); si no llega a la
                    # línea no se toca.
                    if b1 > corte - 6:
                        ys = np.arange(max(0, int(corte) - 10), min(700, b1 + 1))
                        factor = np.clip((corte + 2 - ys) / 8.0, 0, 1)
                        antes = a[ys, x, 3].copy()
                        a[ys, x, 3] = antes * factor
                        n_total += int(((antes > 0) & (a[ys, x, 3] == 0)).sum())
                elif a1 <= yb and b1 >= corte - 6:
                    # Nace en/bajo la línea y toca la banda: hebra suelta
                    # sobre la ceja -> se borra entera (caso v9).
                    a[a1:b1 + 1, x, 3] = 0
                    n_total += (b1 - a1 + 1)
    informe['ceja_px_borrados'] = n_total
    return n_total

# ------------------------------------------------------------------ oreja
def caja_oreja(sexo):
    """Caja de la oreja derivada del componente oscuro de la oreja en la
    Base (original): el componente compacto (50<=ancho<=150, 100<=alto<=250)
    en x700-900, y450-750, más 40 px de margen. El contorno largo de la
    cabeza/cuello NO es la oreja y no se usa."""
    b = np.asarray(Image.open(os.path.join(EDAD, f'{sexo}_Base_original.png')).convert('RGBA')).astype(int)
    lum = b[..., :3].mean(axis=2)
    oscuro = (b[..., 3] > 200) & (lum < 120)
    lab, n = ndimage.label(oscuro)
    sizes = np.bincount(lab.ravel())
    slices = ndimage.find_objects(lab)
    mejor = None
    for i in range(1, n + 1):
        if sizes[i] < 100:
            continue
        s = slices[i - 1]
        x0, x1, y0, y1 = s[1].start, s[1].stop - 1, s[0].start, s[0].stop - 1
        if x0 < 700 or x1 > 900 or y0 < 450 or y1 > 750:
            continue
        ancho, alto = x1 - x0 + 1, y1 - y0 + 1
        if 50 <= ancho <= 150 and 100 <= alto <= 250:
            if mejor is None or sizes[i] > sizes[mejor]:
                mejor = i
    if mejor is None:
        return (680, 470, 880, 740)
    s = slices[mejor - 1]
    return (max(0, s[1].start - 40), max(0, s[0].start - 40),
            min(1199, s[1].stop - 1 + 40), min(1599, s[0].stop - 1 + 40))

def paso_oreja(a, sexo, informe):
    """Zona de la oreja sin fragmentos flotantes (solo Front): borra los
    componentes desconectados (n>=40) ENTEROS dentro de la caja de la oreja
    (un mechón que la cruza no se toca) + el polvo dentro de la caja que no
    esté a <=1 px de pelo que se queda."""
    if informe.get('parte') != 'Front':
        return 0
    x0, y0, x1, y1 = caja_oreja(sexo)
    informe['caja_oreja'] = [x0, y0, x1, y1]
    solido = a[..., 3] > 200
    comps, lab = componentes(solido)
    if not comps:
        return 0
    masa_id = comps[0]['id']
    n_borrados = 0
    for c in comps[1:]:
        if c['n'] < 40:
            continue
        # ¿entero dentro de la caja (con 15 px de margen)?
        if c['x0'] >= x0 - 15 and c['x1'] <= x1 + 15 and c['y0'] >= y0 - 15 and c['y1'] <= y1 + 15:
            m = lab == c['id']
            ns, nh = borrar_mascara(a, m)
            n_borrados += 1
            informe.setdefault('oreja_borrados', []).append(
                dict(n=c['n'], x0=c['x0'], x1=c['x1'], y0=c['y0'], y1=c['y1'],
                     solido_borrado=ns, halo_borrado=nh))
    # polvo dentro de la caja: solo queda el pelo que se queda (+1 px)
    solido2 = a[..., 3] > 200
    cerca = ndimage.binary_dilation(solido2, iterations=1)
    polvo = (a[..., 3] > 0) & ~cerca
    dentro = np.zeros(a.shape[:2], dtype=bool)
    dentro[y0:y1, x0:x1] = True
    polvo &= dentro
    if polvo.sum():
        a[polvo, 3] = 0
        informe['oreja_polvo_borrado'] = int(polvo.sum())
    return n_borrados

# ------------------------------------------------------------------ repisa
def paso_repisa(a, sexo, informe):
    """Repisa bajo la oreja (solo Front): si el borde inferior de la masa
    forma una repisa horizontal seguida de un escalón hacia la patilla, se
    talla el frente en diagonal suave (como v10)."""
    if informe.get('parte') != 'Front':
        return 0
    x0, y0, x1, y1 = caja_oreja(sexo)
    solido = a[..., 3] > 200
    # borde inferior de la masa por columna en la zona bajo la oreja
    y_sup, y_inf = y1 - 30, y1 + 130
    xs = np.arange(x0 - 40, x1 + 60)
    fondo = []
    for x in xs:
        col = np.where(solido[y_sup:y_inf, x])[0]
        fondo.append(int(col.max()) + y_sup if len(col) else -1)
    fondo = np.array(fondo, dtype=float)
    # buscar una repisa: tramo >40 px con fondo plano (±3) seguido de una
    # caída >25 px hacia la derecha en <15 px
    repisa = None
    for i in range(len(xs) - 60):
        tramo = fondo[i:i + 40]
        if (tramo < 0).any():
            continue
        # la repisa es plana a ±12 px (v10 la midió y718-729: 11 px de rango)
        if tramo.max() - tramo.min() <= 12:
            despues = fondo[i + 40:i + 55]
            # el escalón: primer x tras la repisa donde el fondo cae >25 px
            xr = None
            for j in range(i + 40, min(i + 55, len(xs))):
                if fondo[j] >= 0 and fondo[j] - tramo.mean() > 25:
                    xr = int(xs[j])
                    break
            if xr is not None:
                # y_rep = el punto más bajo de la repisa (para que el tallado
                # cubra su borde inferior, como v10: y688-732)
                repisa = (int(xs[i]), xr, float(tramo.max()))
                break
    if repisa is None:
        informe['repisa'] = 'no detectada'
        return 0
    xl, xr, y_rep = repisa
    informe['repisa'] = dict(x0=xl, x1=xr, y_fondo=round(y_rep, 1))
    # tallar: borrar la parte delantera de la repisa con frente diagonal
    # X(y) = xr -> xr-11 entre y_rep-45 e y_rep+5 (como v10: 765->754).
    # La máscara cubre TODA la región (no solo el sólido): si se recorta
    # solo sobre el sólido, los píxeles suaves de la repisa quedan aislados
    # en la zona tallada como un racimo de polvo.
    m = np.zeros(a.shape[:2], dtype=bool)
    for y in range(max(0, int(y_rep) - 45), int(y_rep) + 6):
        xc = xr - 11.0 * (y - (y_rep - 45)) / 50.0
        m[y, max(0, xl - 10):int(round(xc))] = True
    if not m.any():
        return 0
    # pluma suave en el borde del tallado; el desenfoque nunca llega a 1.0
    # exacto, así que lo que queda con alfa<1 se pone a 0 (borrado efectivo)
    mf = ndimage.gaussian_filter(m.astype(float), 1.5)
    antes = a[..., 3].copy()
    a[..., 3] = antes * (1 - mf)
    a[..., 3][a[..., 3] < 1] = 0
    ns = int(((antes > 0) & (a[..., 3] == 0)).sum())
    informe['repisa_px_borrados'] = ns
    return ns

# ------------------------------------------------------------------ sien
def ventana_sien(sexo):
    """Ventana de la sien: el muro recto que deja el despeje de la ceja
    está en el EXTREMO CERCANO de la ceja (donde termina el corte): la
    ventana es estrecha y está centrada en ese extremo, para que el borde
    izquierdo de la masa sea el muro y no el borde de la ventana.
    Devuelve (xw0, xw1, y0, y1)."""
    cejas = curvas_ceja(sexo)
    if not cejas:
        return None
    x0, top, bot, _, _ = cejas[0]
    x_fin = x0 + len(top) - 1
    return (x_fin - 15, x_fin + 80, int(top.min()) - 60, int(bot.max()) + 40)

def borde_izq_masa(masa, x0, x1, y0, y1):
    """Borde izquierdo de la MASA por fila en la ventana."""
    out = np.full(y1 - y0, -1)
    for j, y in enumerate(range(y0, y1)):
        xs = np.where(masa[y, x0:x1])[0]
        if len(xs):
            out[j] = xs.min() + x0
    return out

def masa_principal(a):
    solido = a[..., 3] > 200
    comps, lab = componentes(solido)
    if not comps:
        return solido
    return lab == comps[0]['id']

def paso_sien(a, sexo, informe, borde_antes):
    """Redondea un muro vertical recto creado por el despeje de la ceja:
    si el borde izquierdo de la masa es constante (±1 px) durante >25 px
    de y en la zona de la sien y ANTES no lo era, se talla una curva suave
    (como v10)."""
    if informe.get('parte') != 'Front':
        return 0
    ven = ventana_sien(sexo)
    if ven is None:
        return 0
    xw0, xw1, y0, y1 = ven
    masa = masa_principal(a)
    despues = borde_izq_masa(masa, xw0, xw1, y0, y1)
    n_tallado = 0
    i = 0
    while i < len(despues) - 25:
        if despues[i] < 0:
            i += 1
            continue
        j = i
        while j + 1 < len(despues) and despues[j + 1] >= 0 \
                and abs(despues[j + 1] - despues[i]) <= 1:
            j += 1
        largo = j - i + 1
        if largo > 25:
            # ¿era recto antes? si antes también era recto, es diseño
            ant = borde_antes[i:j + 1]
            era_recto = len(ant[ant >= 0]) > 20 and \
                (ant[ant >= 0].max() - ant[ant >= 0].min() <= 1)
            if not era_recto:
                x_muro = int(despues[i])
                # tallar curva: el borde se abre a la derecha en el medio
                m = np.zeros(a.shape[:2], dtype=bool)
                ys = np.arange(y0 + i, y0 + j + 1)
                amp = 9.0
                curva = x_muro + amp * np.sin(np.pi * (ys - (y0 + i)) / max(1, largo))
                for y, xc in zip(ys, curva):
                    m[y, max(0, x_muro - 2):int(round(xc))] = True
                mf = ndimage.gaussian_filter(m.astype(float), 1.5)
                antes = a[..., 3].copy()
                a[..., 3] = antes * (1 - mf)
                a[..., 3][a[..., 3] < 1] = 0
                n_tallado += int(((antes > 0) & (a[..., 3] == 0)).sum())
                informe.setdefault('sien_tallado', []).append(
                    dict(x_muro=x_muro, y0=int(y0 + i), y1=int(y0 + j),
                         px=int(((antes > 0) & (a[..., 3] == 0)).sum())))
                masa = masa_principal(a)
                despues = borde_izq_masa(masa, xw0, xw1, y0, y1)
        i = max(j + 1, i + 1)
    return n_tallado

# ------------------------------------------------------------------ polvo
def paso_polvo(a, informe):
    """Polvo aislado: racimos de alfa 20-200 a >3 px del sólido con n<100
    se borran; los racimos grandes (>=100 px) son el borde suave / sombra
    del pelo y se conservan y se listan. PERO: un racimo AISLADO (>10 px
    del sólido) con alfa mediano >=40 es visible en gris (un hilo o una
    mancha) y se borra; y en la ventana de la ceja se borra TODO el polvo
    aislado (ningún pelo sobre la ceja, aunque sea tenue).
    v11.2 (2026-11-24): el umbral era 80; el velo de H9 (2 racimos tenues
    alfa 44 y 63, invisibles en fondo oscuro, visibles en fondo claro)
    quedaba conservado. Con 40 se borran. En el informe v11.1 SOLO H9
    Front tenía tenues, así que el cambio no afecta a las demás capas."""
    solido = a[..., 3] > 200
    cerca = ndimage.binary_dilation(solido, iterations=3)
    polvo = (a[..., 3] >= 20) & (a[..., 3] <= 200) & ~cerca
    lab, n = ndimage.label(polvo)
    sizes = np.bincount(lab.ravel())
    slices = ndimage.find_objects(lab)
    borrados, conservados = 0, []
    for i in range(1, n + 1):
        if sizes[i] < 100:
            m = lab == i
            a[m, 3] = 0
            borrados += int(sizes[i])
        else:
            s = slices[i - 1]
            conservados.append(dict(n=int(sizes[i]), x0=int(s[1].start),
                                    x1=int(s[1].stop) - 1, y0=int(s[0].start),
                                    y1=int(s[0].stop) - 1))
    informe['polvo_borrado_px'] = borrados
    informe['polvo_conservado'] = conservados
    # --- polvo aislado visible: borrarlo (con 2 px de margen) ---
    # Se etiqueta la máscara aislada tras un CIERRE de 3 px: dos trozos del
    # mismo hilo separados por 1-2 px se fusionan y se borran juntos (si no,
    # se borra la mitad opaca del hilo y queda la mitad tenue).
    masc_ais = polvo_aislado_mascara(a)
    masc_cerr = ndimage.binary_dilation(masc_ais, iterations=3)
    lab2, n2 = ndimage.label(masc_cerr)
    sizes2 = np.bincount(lab2.ravel())
    slices2 = ndimage.find_objects(lab2)
    # ventana de la ceja (solo Front) para el borrado total
    ven_ceja = None
    if informe.get('parte') == 'Front':
        cejas = curvas_ceja(informe['sexo'])
        if cejas:
            x0, top, bot, _, _ = cejas[0]
            ven_ceja = (x0 - 10, int(top.min()) - 20,
                        x0 + len(top) + 10, int(bot.max()) + 40)
    borrados_ais, tenues = [], []
    for i in range(1, n2 + 1):
        # píxeles aislados ORIGINALES dentro de este racimo cerrado
        orig = masc_ais & (lab2 == i)
        n_orig = int(orig.sum())
        if n_orig < 20:
            continue
        s = slices2[i - 1]
        alfa_med = float(np.median(a[orig, 3]))
        en_ceja = ven_ceja is not None and \
            s[1].start >= ven_ceja[0] and s[1].stop - 1 <= ven_ceja[2] and \
            s[0].start >= ven_ceja[1] and s[0].stop - 1 <= ven_ceja[3]
        if en_ceja or alfa_med >= 40:
            m = ndimage.binary_dilation(lab2 == i, iterations=2)
            a[m, 3] = 0
            borrados_ais.append(dict(n=n_orig, alfa_med=round(alfa_med),
                                     x0=int(s[1].start), x1=int(s[1].stop) - 1,
                                     y0=int(s[0].start), y1=int(s[0].stop) - 1,
                                     en_ceja=bool(en_ceja)))
        else:
            tenues.append(dict(n=n_orig, alfa_med=round(alfa_med),
                               x0=int(s[1].start), x1=int(s[1].stop) - 1,
                               y0=int(s[0].start), y1=int(s[0].stop) - 1))
    informe['polvo_aislado_borrado'] = borrados_ais
    informe['polvo_tenue_conservado'] = tenues
    return borrados

# ------------------------------------------------------------------ paso K (v11.3)
def barbilla_y(sexo):
    """Y de la barbilla (mentón) medida en la Base joven: la fila donde el
    ancho de la piel cae de golpe (la cara termina, empieza el cuello).
    La Base anciana v9 tiene la misma geometría, así que vale la joven."""
    ruta = os.path.join(ASSETS, sexo, 'Base.png')
    b = np.asarray(Image.open(ruta).convert('RGBA')).astype(float)
    anchos, xs_min = [], []
    for y in range(600, 1001, 5):
        xs = np.where(b[y, :, 3] > 200)[0]
        if len(xs):
            anchos.append(int(xs.max() - xs.min() + 1))
            xs_min.append(int(xs.min()))
        else:
            anchos.append(0)
            xs_min.append(0)
    # la mayor caída de ancho entre dos muestras consecutivas (y850-980)
    mejor_y, mejor_caida = 920, 0
    for i in range(1, len(anchos)):
        y = 600 + i * 5
        if 850 <= y <= 980:
            caida = anchos[i - 1] - anchos[i]
            if caida > mejor_caida:
                mejor_caida, mejor_y = caida, y
    return mejor_y

def banda_cuello(sexo, y_chin):
    """Banda x del cuello/pecho a la altura de la barbilla, de la Base:
    el rango x de la piel en y_chin, ensanchado 150 px a cada lado.
    Debajo de la barbilla, las hebras finas DENTRO de esta banda caen sobre
    cuello/pecho (son trazos sueltos); fuera de ella está la masa del pelo
    largo (borde de diseño, no se toca)."""
    ruta = os.path.join(ASSETS, sexo, 'Base.png')
    b = np.asarray(Image.open(ruta).convert('RGBA')).astype(float)
    xs = np.where(b[y_chin, :, 3] > 200)[0]
    if len(xs) == 0:
        return (400, 1000)
    x0 = max(0, int(xs.min()) - 150)
    x1 = min(1200, int(xs.max()) + 150)
    return (x0, x1)

def paso_dedos_sueltos(a, clave, informe):
    """v11.3 (2026-11-24): dedos finos sueltos que el gris revela y los
    pasos B/C/H no cazan porque están CONECTADOS a la masa (no son
    componentes sueltos ni polvo aislado).
    - K1 protuberancias del borde suave: el borde exterior (alfa>0) del pelo
      sigue su tendencia local (mediana 31 filas); una protuberancia
      semitransparente que sale >3 px de la tendencia es un trazo sobrante
      (G3: el borde del mechón corto sale 7 px en y959-967). Solo se recorta
      lo SEMI (alfa 20-200), nunca lo sólido: el diseño no se toca.
    - K2 dedos sólidos bajo la barbilla: hebras finas (apertura r=2 las
      borra) que se alejan >10 px de la masa y caen dentro de la banda del
      cuello/pecho (G4: hebra punteada sobre el cuello; G5: líneas sobre el
      hombro). Fuera de la banda está el borde del pelo largo (diseño).
      Se borra el dedo y el semi a 2 px alrededor (la parte punteada tenue).
    Solo Front (el Back es la masa trasera, otra geometría)."""
    if informe.get('parte') != 'Front':
        return 0
    H, W = a.shape[:2]
    alfa = a[..., 3]
    borrados_k1, borrados_k2 = [], []
    # --- K1: protuberancias del borde suave (semi) ---
    left = np.full(H, float(W))
    right = np.full(H, -1.0)
    for y in range(H):
        xs = np.where(alfa[y] > 0)[0]
        if len(xs):
            left[y] = xs.min()
            right[y] = xs.max()
    left_med = ndimage.median_filter(left, size=31, mode='nearest')
    right_med = ndimage.median_filter(right, size=31, mode='nearest')
    for lado in ('izq', 'der'):
        if lado == 'izq':
            bump = (left < left_med - 3) & (left < W)
        else:
            bump = (right > right_med + 3) & (right >= 0)
        ys = np.where(bump)[0]
        # grupos de filas contiguas (una protuberancia)
        grupos = []
        if len(ys):
            s = ys[0]
            p = ys[0]
            for y in ys[1:]:
                if y == p + 1:
                    p = y
                else:
                    grupos.append((s, p))
                    s = y
                    p = y
            grupos.append((s, p))
        for (y0, y1) in grupos:
            if y1 - y0 + 1 > 15:
                continue  # protuberancia ancha: forma del peinado, no trazo
            n_antes = 0
            for y in range(y0, y1 + 1):
                if lado == 'izq':
                    lim = int(left_med[y])
                    m = (np.arange(W) < lim) & (alfa[y] >= 20) & (alfa[y] <= 200)
                else:
                    lim = int(right_med[y])
                    m = (np.arange(W) > lim) & (alfa[y] >= 20) & (alfa[y] <= 200)
                n_antes += int(m.sum())
                a[y, m, 3] = 0
            if n_antes:
                borrados_k1.append(dict(lado=lado, y0=int(y0), y1=int(y1),
                                        px=int(n_antes)))
    # --- K2: dedos sólidos finos bajo la barbilla, en la banda del cuello ---
    y_chin = barbilla_y(informe['sexo'])
    xb0, xb1 = banda_cuello(informe['sexo'], y_chin)
    informe['k_barbilla_y'] = int(y_chin)
    informe['k_banda_cuello'] = [int(xb0), int(xb1)]
    sol = alfa > 200
    ero = ndimage.binary_erosion(sol, iterations=2)
    abierto = ndimage.binary_dilation(ero, iterations=2)
    removido = sol & ~abierto
    dist_ab = ndimage.distance_transform_edt(~abierto)
    lab, n = ndimage.label(removido)
    sizes = np.bincount(lab.ravel())
    for i in range(1, n + 1):
        if sizes[i] < 15:
            continue
        ys, xs = np.where(lab == i)
        if ys.min() <= y_chin:
            continue  # por encima de la barbilla: flequillo/mechones de diseño
        if dist_ab[lab == i].max() <= 10:
            continue  # pegado a la masa: borde, no dedo
        xc = float(xs.mean())
        if not (xb0 <= xc <= xb1):
            continue  # fuera de la banda del cuello: borde del pelo largo
        m = lab == i
        n_sol = int(m.sum())
        # semi a 2 px alrededor (la parte punteada tenue del mismo dedo)
        dil = ndimage.binary_dilation(m, iterations=2)
        m_semi = dil & (alfa >= 20) & (alfa <= 200)
        n_semi = int(m_semi.sum())
        # --- SALVAGUARDA DE PUENTE: un "dedo" fino puede ser el puente que
        # une un trozo GRUESO de pelo a la masa; borrarlo soltaría ese trozo
        # y se perdería pelo de diseño. Pero si el trozo desprendido es un
        # HILO fino (ancho_med<=6, largo>30, el mismo criterio del barrido
        # final), entonces puente+trozo son UNA hebra suelta: se borra el
        # puente y el barrido final se lleva el hilo. Solo se conserva el
        # puente si suelta un trozo GRUESO (ancho_med>6, masa de diseño).
        alfa_guarda = a[..., 3].copy()
        a[m, 3] = 0
        a[m_semi, 3] = 0
        sol2 = a[..., 3] > 200
        comps2, _ = componentes(sol2)
        grueso = [c for c in comps2[1:] if c['ancho_med'] > 6.0]
        if grueso:
            a[..., 3] = alfa_guarda  # restaura: era puente a masa gruesa
            informe.setdefault('k2_puentes_conservados', []).append(
                dict(n_sol=n_sol, x0=int(xs.min()), x1=int(xs.max()),
                     y0=int(ys.min()), y1=int(ys.max()),
                     desprendido=[dict(n=c['n'], ancho_med=round(c['ancho_med'], 1),
                                       x0=c['x0'], x1=c['x1'],
                                       y0=c['y0'], y1=c['y1'])
                                  for c in grueso]))
            continue
        borrados_k2.append(dict(n_sol=n_sol, n_semi=n_semi,
                                x0=int(xs.min()), x1=int(xs.max()),
                                y0=int(ys.min()), y1=int(ys.max()),
                                dist_max=round(float(dist_ab[lab == i].max()))))
    informe['k1_protuberancias'] = borrados_k1
    informe['k2_dedos'] = borrados_k2
    print(f'    K dedos sueltos: K1 {len(borrados_k1)} protuberancias '
          f'({sum(b["px"] for b in borrados_k1)}px semi), K2 {len(borrados_k2)} '
          f'dedos, barbilla y={y_chin}, banda x{xb0}-{xb1}', flush=True)
    return len(borrados_k1) + len(borrados_k2)

# ------------------------------------------------------------------ proceso
def procesar_capa(sexo, h, parte, informe_global):
    clave = (sexo, h, parte)
    nombre = f'{sexo}_Hair{h}_{parte}'
    ruta = os.path.join(ASSETS, sexo, f'Hair{h}_{parte}.png')
    a = np.asarray(Image.open(ruta).convert('RGBA')).astype(float)
    informe = dict(capa=nombre, sexo=sexo, pelo=h, parte=parte)
    if int((a[..., 3] > 0).sum()) == 0:
        informe['vacia'] = True
        print(f'{nombre}: VACIA (se salta)', flush=True)
        return informe
    informe['vacia'] = False
    alfa_orig = a[..., 3].copy()
    informe['alfa_pos_orig'] = int((alfa_orig > 0).sum())
    informe['alfa_solido_orig'] = int((alfa_orig > 200).sum())

    # A. gris v8 con resguardos v11
    g = gris_v8(a, sexo, f'Hair{h}_{parte}')
    informe['gris'] = g
    print(f'{nombre}: gris v8 ({g["hebras"]} hebras + {g["brillos"]} brillos)', flush=True)

    def diff(nombre_paso, ventana=None):
        # El diff de corte exige: 0 motas (n>=2) y 0 racimos de polvo AISLADO
        # (>=20 px a >10 px del sólido) en la ventana. El polvo a 3 px (la
        # rampa/pluma del corte, 100-300 px) es el borde suavizado del corte
        # y se reporta pero no es un fallo: v9/v10 lo tienen igual.
        motas, polvo3 = motas_y_halo(a, ventana)
        masc_ais = polvo_aislado_mascara(a)
        if ventana is None:
            sub = masc_ais
        else:
            x0, y0, x1, y1 = ventana
            sub = masc_ais[y0:y1 + 1, x0:x1 + 1]
        lab, n = ndimage.label(sub)
        sizes = np.bincount(lab.ravel())[1:] if n else []
        aislados = [int(s) for s in sizes if s >= 20]
        ok = (len(motas) == 0 and len(aislados) == 0)
        print(f'    diff {nombre_paso}: motas={motas} polvo_borde={polvo3}px '
              f'polvo_aislado={aislados} ({"OK" if ok else "REVISAR"})', flush=True)
        informe.setdefault('diffs', []).append(
            dict(paso=nombre_paso, motas=motas, polvo_borde_px=polvo3,
                 polvo_aislado=aislados, ok=bool(ok)))
        return ok

    # B. componentes
    n_b = paso_componentes(a, clave, informe)
    print(f'    B componentes: {n_b} borrados, '
          f'{len(informe.get("conservados", []))} conservados', flush=True)
    diff('B-componentes')

    # C. dedos
    n_d = paso_dedos(a, clave, informe)
    print(f'    C dedos: {n_d} borrados', flush=True)
    n_frag = barrer_fragmentos(a, clave, informe, 'C-dedos')
    print(f'    C fragmentos barridos: {n_frag}', flush=True)
    diff('C-dedos')

    # borde de la sien ANTES del despeje de la ceja (para el paso G)
    borde_antes = None
    ven = ventana_sien(sexo) if parte == 'Front' else None
    if ven is not None:
        xw0, xw1, y0, y1 = ven
        borde_antes = borde_izq_masa(masa_principal(a), xw0, xw1, y0, y1)

    # D. ceja
    if parte == 'Front':
        paso_ceja(a, sexo, informe)
        barrer_fragmentos(a, clave, informe, 'D-ceja')
        cejas = curvas_ceja(sexo)
        for (x0, top, bot, _, _) in cejas:
            diff('D-ceja', (x0 - 10, int(top.min()) - 20, x0 + len(top) + 10,
                            int(bot.max()) + 40))

    # E. oreja
    if parte == 'Front':
        paso_oreja(a, sexo, informe)
        barrer_fragmentos(a, clave, informe, 'E-oreja')
        if 'caja_oreja' in informe:
            x0, y0, x1, y1 = informe['caja_oreja']
            diff('E-oreja', (x0, y0, x1, y1))

    # F. repisa
    if parte == 'Front':
        paso_repisa(a, sexo, informe)
        barrer_fragmentos(a, clave, informe, 'F-repisa')
        if isinstance(informe.get('repisa'), dict):
            r = informe['repisa']
            diff('F-repisa', (max(0, r['x0'] - 20), int(r['y_fondo']) - 60,
                              r['x1'] + 20, int(r['y_fondo']) + 10))

    # G. sien
    if parte == 'Front' and borde_antes is not None:
        paso_sien(a, sexo, informe, borde_antes)
        barrer_fragmentos(a, clave, informe, 'G-sien')
        if informe.get('sien_tallado'):
            for t in informe['sien_tallado']:
                diff('G-sien', (t['x_muro'] - 20, t['y0'] - 10,
                                t['x_muro'] + 30, t['y1'] + 10))

    # H. polvo
    paso_polvo(a, informe)

    # K. dedos sueltos (v11.3): trazos finos conectados a la masa que el
    # gris revela (G3/G4/G5 de H9). Después del polvo y antes del barrido
    # final, para que el barrido limpie los restos del corte.
    paso_dedos_sueltos(a, clave, informe)
    diff('K-dedos')

    # I. barrido final de fragmentos: los cortes C-H pueden haber cercenado
    # trozos de la masa que quedan como hilos finos desconectados.
    n_frag = barrer_fragmentos(a, clave, informe, 'I-final')
    print(f'    I fragmentos barridos: {n_frag}', flush=True)
    diff('I-final')

    # J. redondeo + puntas de gradiente. El archivo es uint8 y astype()
    # TRUNCA: un vecino a 200.6 es sólido en memoria (>200) pero 200 en el
    # archivo, y deja un píxel suelto de 1 px en el archivo aunque la
    # verificación en memoria diga que no hay motas. Se redondea primero
    # (rint) para que la verificación vea exactamente lo que se guarda, y
    # luego se limpian las puntas (píxeles sólidos sin vecino en cruz).
    a = np.rint(np.clip(a, 0, 255))
    n_puntas = limpiar_puntas(a, informe)
    if n_puntas:
        print(f'    J puntas limpiadas: {n_puntas}', flush=True)

    # verificación final de la capa
    solido = a[..., 3] > 200
    comps, _ = componentes(solido)
    informe['componentes_final'] = len(comps)
    informe['masa_final_n'] = comps[0]['n'] if comps else 0
    pl, ncl, top = polvo_lejos(a)
    informe['polvo_final_px'] = pl
    informe['polvo_final_clusters'] = ncl
    informe['polvo_final_top'] = top
    pa_px, pa_n, pa_top = polvo_aislado(a)
    informe['polvo_aislado_px'] = pa_px
    informe['polvo_aislado_clusters'] = pa_n
    informe['polvo_aislado_top'] = pa_top
    motas, polvo = motas_y_halo(a)
    informe['motas_final'] = motas
    informe['polvo_final_diff'] = polvo
    # el alfa solo baja respecto al original salvo la sien F (restauración:
    # en v11 no hay restauración, así que el alfa solo baja)
    informe['alfa_sube_px'] = int((a[..., 3] > alfa_orig).sum())
    # RGB: el gris cambia el RGB (remap + streamlines); el alfa es lo que
    # se verifica contra el original en los pasos de limpieza
    out = os.path.join(EDAD, f'{nombre}_canas_{VERSION}.png')
    Image.fromarray(np.clip(a, 0, 255).astype('uint8')).save(out)
    md5 = hashlib.md5(open(out, 'rb').read()).hexdigest()
    informe['md5'] = md5
    informe['archivo'] = os.path.basename(out)
    print(f'{nombre}: v11 guardado md5={md5[:12]} | comps {informe["componentes_antes"]}'
          f'->{len(comps)} | polvo lejos {pl}px/{ncl}cl | motas {motas}', flush=True)
    return informe

def main():
    informe_global = {}
    for sexo, nh in [('Female', 12), ('Male', 4)]:
        for h in range(1, nh + 1):
            for parte in ['Front', 'Back']:
                inf = procesar_capa(sexo, h, parte, informe_global)
                informe_global[f'{sexo}_Hair{h}_{parte}'] = inf
    with open(os.path.join(EDAD, f'informe_{VERSION}.json'), 'w') as f:
        json.dump(informe_global, f, indent=1)
    print(f'informe guardado en informe_{VERSION}.json')
    # resumen
    n_ok = n_vacias = 0
    for k, v in informe_global.items():
        if v.get('vacia'):
            n_vacias += 1
        elif not v.get('motas_final') and v.get('polvo_aislado_clusters', 99) == 0:
            n_ok += 1
    print(f'capas: {len(informe_global)} | vacías: {n_vacias} | '
          f'con diff final OK: {n_ok}')
    print('listo')

if __name__ == '__main__':
    main()
