# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
armario_geometry.py — GEOMETRÍA DEL ALZADO DE ARMARIO / VESTIDOR.

Hasta ahora el único motor de alzado acotado del ERP vivía en
`estudio_cocinas.py` y era exclusivo de cocina. En un proyecto de armario el
botón «Alzado + planta + medidas» se saltaba el dibujo vectorial y devolvía una
lámina hecha por una IA: una imagen bonita, sin una sola cota real. Esto es el
motor que faltaba.

Cálculo puro, sin base de datos ni matplotlib, para poder probarlo. El dibujo
va aparte (`routes/armarios_alzado.py`); aquí solo salen números.

TODO EN MILÍMETROS
------------------
El presupuestador de armarios trabaja en mm (`width: 2400`), y la cocina
trabaja en cm. Mezclarlos daría un armario 10 veces mayor sin que nada falle
—los ejes salen, las cajas salen— y el error solo se vería en fábrica. Aquí
NO se convierte nada: entra mm y sale mm, y hay una prueba que lo fija.

DE DÓNDE SALEN LAS MEDIDAS
--------------------------
De la misma aritmética que el despiece de `Armarios.jsx`, que es lo que se
corta de verdad. Si el alzado dibujara una balda de un ancho y el despiece
cortara otro, el plano estaría mintiendo sobre la pieza que va a existir. Por
eso las constantes de abajo son las del despiece, y están fijadas en
`test_calculo_armario_alzado.py`: si alguien cambia una sin cambiar la otra,
el CI se pone rojo.

LO QUE NO SE HACE
-----------------
No se inventa ni una cota. Si falta el ancho, el alto o el número de módulos,
NO se dibuja un armario "razonable": se devuelve el motivo y quien mira sabe
qué le falta. Y si el interior pedido no cabe en el alto disponible, tampoco se
aprieta en silencio para que quepa — se dice cuánto se pasa. Un armario
dibujado apretando es un armario que en fábrica no cierra.
"""

# ─── Constantes de fabricación (mm) ─────────────────────────────────────────
# Son las del despiece de `Armarios.jsx`. Ver nota de arriba: no son un criterio
# de este fichero, son lo que se corta.
GRUESO_PANEL = 18        # laterales, tapas, divisores y baldas
GRUESO_TRASERA = 8
HOLGURA_BALDA = 6        # la balda mide el hueco libre menos esta holgura
HOLGURA_CAJON = 26       # cuerpo del cajón = hueco libre − guías
ALTO_CAJON = 150         # alto del cuerpo de un cajón
RETRANQUEO_INTERIOR = 20  # baldas y divisores respecto al fondo
RETRANQUEO_CAJON = 50     # fondo del cajón respecto al fondo del armario

# Estándares de colocación del interior. Están escritos en el prompt de
# `armarios.py` («el maletero va siempre arriba», «los cajones abajo»), que
# hasta ahora era el único sitio donde vivían. Aquí dejan de ser una frase para
# una IA y pasan a ser números que se pueden comprobar.
ALTO_MALETERO = 300           # el maletero ocupa la franja de arriba
COLGAR_ALTURA_SIMPLE = 1200   # hueco libre bajo una barra única
COLGAR_ALTURA_DOBLE = 1000    # hueco libre bajo cada barra, en doble altura
ALTO_ZAPATERO = 180           # zapatero basculante, abajo
ALTO_PANTALONERO = 120        # pantalonero, zona media-baja

# Dos umbrales distintos, y la diferencia importa (CLAUDE.md: «bloquea lo que
# hace imposible fabricar bien; avisa lo que conviene mirar pero no impide
# cortar. Si todo bloqueara, se saltaría el circuito entero a la primera
# urgencia»).
#
# IMPOSIBLE: por debajo del grueso de la propia balda, las baldas se pisan unas
# con otras. Eso no es un armario estrecho, es un armario que no existe.
SEPARACION_BALDAS_IMPOSIBLE = GRUESO_PANEL
# INCÓMODA: cabe y se corta, pero no entra ropa doblada. Se dibuja y se avisa —
# bloquearlo tumbaba hasta la configuración por defecto del configurador, y un
# plano que se niega a salir acaba con alguien midiendo a mano.
SEPARACION_BALDAS_COMODA = 180


def _num(v):
    """A número, o None si no hay dato. Un texto vacío NO es 0."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _entero_positivo(v):
    n = _num(v)
    if n is None or n <= 0:
        return None
    return int(round(n))


# ─── Validación: sin medidas no se dibuja ───────────────────────────────────

def validar(config):
    """¿Hay datos suficientes para dibujar este armario?

    Devuelve {"ok": bool, "motivo": str, "config": {...}} con los valores ya
    normalizados. No rellena nada: si falta una medida, `ok` es False y el
    motivo dice CUÁL falta, para que el aviso lleve a alguna parte.
    """
    c = config or {}
    ancho = _num(c.get("width"))
    alto = _num(c.get("height"))
    fondo = _num(c.get("depth"))
    modulos = _entero_positivo(c.get("modules"))

    faltan = [n for n, v in (("ancho", ancho), ("alto", alto), ("fondo", fondo))
              if v is None or v <= 0]
    if modulos is None:
        faltan.append("número de módulos")
    if faltan:
        return {"ok": False, "motivo": "Falta " + " y ".join(faltan)
                + " del armario. Sin esas medidas el alzado no se puede acotar."}

    # Un armario más estrecho que sus propios laterales no es un armario
    # pequeño: es un dato mal metido, y dibujarlo daría módulos de ancho
    # negativo sin que reventara nada.
    interior = ancho - 2 * GRUESO_PANEL
    if interior <= 0:
        return {"ok": False, "motivo":
                f"El ancho ({int(ancho)} mm) no da ni para los dos laterales "
                f"de {GRUESO_PANEL} mm. Revisa si está en mm o en cm."}
    if alto - 2 * GRUESO_PANEL <= 0:
        return {"ok": False, "motivo":
                f"El alto ({int(alto)} mm) no da ni para las dos tapas de "
                f"{GRUESO_PANEL} mm. Revisa si está en mm o en cm."}

    # Los divisores comen ancho: con muchos módulos el hueco puede quedar en
    # nada o en negativo.
    paso = _paso_modulo(ancho, modulos)
    if paso - GRUESO_PANEL <= 0:
        return {"ok": False, "motivo":
                f"{modulos} módulos en {int(ancho)} mm dejan un hueco libre de "
                f"{int(paso - GRUESO_PANEL)} mm. No es fabricable."}

    puertas = _entero_positivo(c.get("numDoors")) or modulos
    return {"ok": True, "motivo": "", "config": {
        "ancho": ancho, "alto": alto, "fondo": fondo,
        "modulos": modulos, "puertas": puertas,
    }}


# ─── Reparto horizontal ─────────────────────────────────────────────────────

def _paso_modulo(ancho, modulos):
    """Paso bruto de un módulo, divisor incluido. Igual que el despiece."""
    return ancho / modulos


def modulos_alzado(ancho, modulos):
    """Dónde empieza y cuánto mide cada módulo en el alzado.

    `paso` es el reparto bruto (lo que el despiece llama `moduleWidth`) y
    `hueco` es lo que queda libre dentro, que es sobre lo que se cortan baldas
    y cajones. Son dos números distintos y confundirlos es lo que hace que una
    balda no entre.
    """
    paso = _paso_modulo(ancho, modulos)
    salida = []
    for i in range(modulos):
        salida.append({
            "indice": i,
            "x": i * paso,
            "paso": paso,
            "hueco": paso - GRUESO_PANEL,
        })
    return salida


def puertas_alzado(ancho, puertas):
    """Reparto de las puertas del frente.

    Las puertas NO tienen por qué coincidir con los módulos: el configurador
    lleva `numDoors` aparte precisamente porque en correderas casi nunca
    coinciden. Dibujarlas sobre los módulos sería dibujar otro armario.
    """
    if not puertas:
        return []
    an = ancho / puertas
    return [{"indice": i, "x": i * an, "ancho": an} for i in range(puertas)]


# ─── Reparto vertical del interior de un módulo ─────────────────────────────

def altura_colgar(mod):
    """Hueco libre bajo cada barra.

    Se toma el que venga en la configuración. Si no viene, se DERIVA del
    estándar (1200 simple / 1000 en doble altura) y se deja constancia de que
    se ha derivado, para que nadie lo lea como un dato que dio el cliente.
    """
    barras = _entero_positivo(mod.get("hangingRods")) or 0
    if barras <= 0:
        return 0, False
    dado = _num(mod.get("hangingHeight"))
    if dado and dado > 0:
        return dado, False
    return (COLGAR_ALTURA_DOBLE if barras > 1 else COLGAR_ALTURA_SIMPLE), True


def reparto_vertical(alto_interior, mod):
    """Coloca el interior de UN módulo, de abajo arriba.

    Devuelve {"elementos": [...], "libre": mm, "derivados": [...],
              "avisos": [...], "error": str|None}.

    Cada elemento lleva su `y` (cota inferior desde el suelo interior) y su
    `alto`. Nada se coloca "a ojo": el orden y las franjas son los estándares
    de arriba.

    SI NO CABE, NO SE APRIETA. Se devuelve `error` diciendo cuántos mm se pasa.
    Apretar el reparto para que entre daría un plano correcto en pantalla y un
    módulo que en fábrica no cierra — y el fallo aparecería en el taller, que
    es donde ya no se puede arreglar barato.
    """
    m = mod or {}
    elementos = []
    derivados = []
    avisos = []

    cajones = _entero_positivo(m.get("drawers")) or 0
    baldas = _entero_positivo(m.get("shelves")) or 0
    barras = _entero_positivo(m.get("hangingRods")) or 0
    extras = m.get("extras") or {}
    # El configurador ha llamado a esto `trunk` (IA) y `maletero` (pantalla) en
    # sitios distintos. Se aceptan los dos: si solo se mirara uno, el maletero
    # desaparecería del plano según por dónde se hubiera configurado.
    maletero = bool(m.get("maletero") or m.get("trunk")
                    or extras.get("maletero") or extras.get("trunk"))
    zapatero = bool(extras.get("shoesRack") or m.get("shoesRack"))
    pantalonero = bool(extras.get("trousersRack") or m.get("trousersRack"))

    h_colgar, derivada = altura_colgar(m)
    if derivada:
        derivados.append(
            f"altura de colgar {int(h_colgar)} mm (estándar; no venía en la configuración)")

    # Lo que ocupa cada cosa, sin repartir todavía.
    ocupado = (cajones * ALTO_CAJON
               + (ALTO_MALETERO if maletero else 0)
               + barras * h_colgar
               + (ALTO_ZAPATERO if zapatero else 0)
               + (ALTO_PANTALONERO if pantalonero else 0))

    if ocupado > alto_interior:
        return {"elementos": [], "libre": 0, "derivados": derivados, "avisos": avisos,
                "error":
                f"El interior pedido ocupa {int(ocupado)} mm y el módulo tiene "
                f"{int(alto_interior)} mm: se pasa en {int(ocupado - alto_interior)} mm. "
                f"Quita elementos o sube el alto del armario."}

    # De abajo arriba: zapatero, cajones, pantalonero, colgar, baldas, maletero.
    y = 0.0
    if zapatero:
        elementos.append({"tipo": "zapatero", "y": y, "alto": ALTO_ZAPATERO,
                          "etiqueta": "Zapatero"})
        y += ALTO_ZAPATERO
    for i in range(cajones):
        elementos.append({"tipo": "cajon", "y": y, "alto": ALTO_CAJON,
                          "etiqueta": f"Cajón {i + 1}"})
        y += ALTO_CAJON
    if pantalonero:
        elementos.append({"tipo": "pantalonero", "y": y, "alto": ALTO_PANTALONERO,
                          "etiqueta": "Pantalonero"})
        y += ALTO_PANTALONERO
    for i in range(barras):
        # La barra es una línea, no un volumen: su `y` es donde va la barra y el
        # `alto` es el hueco de colgado que queda debajo.
        elementos.append({"tipo": "barra", "y": y + h_colgar, "alto": h_colgar,
                          "etiqueta": "Barra de colgar"})
        y += h_colgar

    techo_baldas = alto_interior - (ALTO_MALETERO if maletero else 0)
    libre = techo_baldas - y

    if baldas:
        # Repartidas por igual en lo que queda.
        paso = libre / (baldas + 1)
        if paso <= SEPARACION_BALDAS_IMPOSIBLE:
            # Las baldas se pisarían entre sí: eso no se dibuja.
            return {"elementos": [], "libre": 0, "derivados": derivados, "avisos": avisos,
                    "error":
                    f"{baldas} balda(s) en {int(libre)} mm libres dejan {int(paso)} mm "
                    f"entre balda y balda, y la balda ya mide {GRUESO_PANEL} mm de "
                    f"grueso: se pisarían. Reduce las baldas o sube el alto."}
        if paso < SEPARACION_BALDAS_COMODA:
            # Cabe y se corta: se dibuja, pero que conste.
            avisos.append(
                f"{baldas} balda(s) a {int(paso)} mm entre sí (por debajo de los "
                f"{SEPARACION_BALDAS_COMODA} mm cómodos para ropa doblada).")
        for i in range(baldas):
            elementos.append({"tipo": "balda", "y": y + paso * (i + 1),
                              "alto": GRUESO_PANEL, "etiqueta": "Balda"})

    if maletero:
        elementos.append({"tipo": "maletero", "y": techo_baldas,
                          "alto": ALTO_MALETERO, "etiqueta": "Maletero"})

    return {"elementos": elementos, "libre": max(0.0, libre),
            "derivados": derivados, "avisos": avisos, "error": None}


# ─── Piezas, para que el plano y el despiece digan lo mismo ─────────────────

def medidas_piezas(ancho, alto, fondo, modulos):
    """Las medidas de corte que el alzado está representando.

    Van en el plano para que quien lo mire pueda contrastarlas con el despiece
    sin abrir otra pantalla. Son la misma aritmética, a propósito.
    """
    paso = _paso_modulo(ancho, modulos)
    hueco = paso - GRUESO_PANEL
    return {
        "lateral": (alto, fondo, GRUESO_PANEL),
        "tapa": (ancho - 2 * GRUESO_PANEL, fondo, GRUESO_PANEL),
        "trasera": (ancho - 2 * GRUESO_PANEL, alto - 2 * GRUESO_PANEL, GRUESO_TRASERA),
        "divisor": (alto - 2 * GRUESO_PANEL, fondo - RETRANQUEO_INTERIOR, GRUESO_PANEL),
        "balda": (hueco - HOLGURA_BALDA, fondo - RETRANQUEO_INTERIOR, GRUESO_PANEL),
        "cajon": (hueco - HOLGURA_CAJON, fondo - RETRANQUEO_CAJON, ALTO_CAJON),
        "divisores_uds": max(0, modulos - 1),
    }


# ─── El alzado completo ─────────────────────────────────────────────────────

def montar(config, module_configs=None):
    """Arma toda la geometría del alzado, lista para dibujar.

    Devuelve {"ok": False, "motivo": ...} si no se puede, o el conjunto de
    geometría si sí. Los problemas de UN módulo no tumban el plano entero: ese
    módulo se marca con su error y el resto se dibuja, porque un plano parcial
    con el fallo señalado sirve más que un error en blanco.
    """
    v = validar(config)
    if not v["ok"]:
        return {"ok": False, "motivo": v["motivo"]}

    c = v["config"]
    ancho, alto, fondo = c["ancho"], c["alto"], c["fondo"]
    n_mod, n_puertas = c["modulos"], c["puertas"]

    alto_interior = alto - 2 * GRUESO_PANEL
    cols = modulos_alzado(ancho, n_mod)
    mcs = list(module_configs or [])

    interiores, problemas, derivados, avisos = [], [], [], []
    for col in cols:
        mc = mcs[col["indice"]] if col["indice"] < len(mcs) else {}
        rep = reparto_vertical(alto_interior, mc)
        if rep["error"]:
            problemas.append({"modulo": col["indice"] + 1, "motivo": rep["error"]})
        for d in rep["derivados"]:
            derivados.append(f"Módulo {col['indice'] + 1}: {d}")
        for a in rep["avisos"]:
            avisos.append(f"Módulo {col['indice'] + 1}: {a}")
        interiores.append({**col, "elementos": rep["elementos"],
                           "libre": rep["libre"], "error": rep["error"]})

    # Si NINGÚN módulo se ha podido repartir, no hay plano que enseñar: eso es
    # un error, no un dibujo vacío que el usuario interpretaría como "el
    # armario está vacío".
    if problemas and len(problemas) == n_mod:
        return {"ok": False, "motivo": problemas[0]["motivo"], "problemas": problemas}

    return {
        "ok": True,
        "ancho": ancho, "alto": alto, "fondo": fondo,
        "altoInterior": alto_interior,
        "modulos": interiores,
        "puertas": puertas_alzado(ancho, n_puertas),
        "piezas": medidas_piezas(ancho, alto, fondo, n_mod),
        # Se informan, NO se esconden en un log: son las tres cosas que quien
        # mira el plano necesita saber para fiarse de él. `problemas` es lo que
        # no se ha podido dibujar, `avisos` lo que se ha dibujado pero conviene
        # mirar, y `derivados` las medidas que no dio nadie y salen del estándar.
        "problemas": problemas,
        "avisos": avisos,
        "derivados": derivados,
    }
