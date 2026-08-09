# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
interferencias.py — LO QUE CHOCA CON LO QUE, ANTES DE FABRICAR.

Cálculo puro, sin base de datos, para poder probarlo. En CENTÍMETROS, que es en
lo que trabaja la planta (`planta_cocina`).

QUÉ RESUELVE
------------
Los choques de una cocina no se descubren en el plano: se descubren en obra,
cuando la puerta del horno da con el cajón de al lado o cuando dos personas no
pueden cruzarse porque el pasillo se quedó en 70 cm. Casi todos son
comprobables con geometría, sin ninguna IA de por medio.

LAS TRES REGLAS DE ESTE MÓDULO
------------------------------
1. **Lo que no se puede comprobar se DICE, no se aprueba.** Si no se sabe hacia
   dónde abre una puerta, la respuesta no es «no hay choque»: es «no se ha
   podido comprobar el choque de M06». Un repaso que da por bueno lo que no ha
   mirado es peor que no hacer el repaso, porque deja tranquilo.

2. **Los mínimos son de la casa, no del programa.** El paso libre entre dos
   filas o la holgura de un rincón son criterios de oficio y cambian de un
   fabricante a otro. Por eso son PARÁMETROS con un valor de partida, y cada
   aviso dice CON QUÉ NÚMERO se ha juzgado — para poder discutirlo en vez de
   creérselo.

3. **No se arregla nada solo.** Se dice qué choca, cuánto y dónde. Mover un
   módulo o meter un junquillo es una decisión de quien firma el proyecto.
"""

# ─── Criterios de la casa (parámetros, no verdades) ─────────────────────────
#
# VALORES DE PARTIDA, pendientes de confirmar con el taller. Están aquí para
# poder cambiarlos en un sitio y para que se vean; no son medidas de ningún
# mueble, son el listón a partir del cual esto avisa.
PASO_LIBRE_MIN = 90        # cm entre frentes de dos filas enfrentadas
PASO_LIBRE_COMODO = 120    # cm por debajo de los cuales se avisa, sin bloquear
HOLGURA_RINCON_MIN = 5     # cm de junquillo para que una puerta abra en rincón

# Lo que un frente necesita por delante para abrirse del todo. Un abatible
# —horno, lavavajillas— barre hacia fuera; un cajón sale recto.
BARRIDO = {"abatible": 60, "cajon": 55, "puerta": 0}

# Elementos cuyo frente abate hacia fuera y por tanto barren el paso.
ABATIBLES = ("horno", "lavavajillas", "lavadora", "secadora", "microondas")


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _medida(v):
    """Un número que puede ser una MEDIDA, o None.

    UN CERO NO ES UNA MEDIDA. Una distancia entre paredes de 0 cm no es una
    cocina estrechísima: es una medida que nadie ha puesto. Sin esto, salía
    «el paso queda en −120 cm», que no significa nada y encima parece un
    cálculo.

    Ojo: el JUNQUILLO sí puede ser 0 —quiere decir que no hay junquillo, que es
    justo el caso que hace chocar la puerta—, así que ese sigue con `_num`.
    """
    n = _num(v)
    return None if n is None or n <= 0 else n


def _txt(v):
    return str(v or "").strip()


def _aviso(clave, nivel, texto, donde=None, dato=None):
    """Un choque, con su nivel y con el número que lo justifica.

    `nivel`: 'error' no se puede fabricar así; 'aviso' hay que mirarlo;
    'sin_comprobar' falta un dato para poder decir nada.
    """
    return {"clave": clave, "nivel": nivel, "texto": texto,
            "donde": _txt(donde), "dato": dato}


# ─── 1. El paso entre dos filas enfrentadas ─────────────────────────────────

def paso_libre(distancia, fondo_a, fondo_b=0):
    """Lo que queda entre los frentes de dos filas enfrentadas.

    Devuelve None si no se sabe la distancia entre las paredes. En una cocina
    lineal esa distancia muchas veces NO está medida, y suponerla es
    exactamente lo que este ERP no hace.
    """
    d = _medida(distancia)
    if d is None:
        return None
    return round(d - (_medida(fondo_a) or 0) - (_medida(fondo_b) or 0), 1)


def revisar_paso(distancia, fondo_a, fondo_b=0, minimo=PASO_LIBRE_MIN,
                 comodo=PASO_LIBRE_COMODO, donde="entre las dos filas"):
    """¿Se puede pasar y trabajar entre las dos filas?"""
    libre = paso_libre(distancia, fondo_a, fondo_b)
    if libre is None:
        return [_aviso("paso", "sin_comprobar",
                       "No consta la distancia entre las dos paredes: no se puede "
                       "comprobar el paso. Mídela en obra.", donde)]
    if libre < minimo:
        return [_aviso("paso", "error",
                       f"El paso queda en {libre:g} cm y el mínimo de la casa es "
                       f"{minimo:g}. Con menos no se abre un cajón con alguien detrás.",
                       donde, libre)]
    if libre < comodo:
        return [_aviso("paso", "aviso",
                       f"El paso queda en {libre:g} cm. Se puede, pero por debajo de "
                       f"{comodo:g} cm dos personas no se cruzan.", donde, libre)]
    return []


def revisar_barrido(distancia, fondo_a, fondo_b, tipo_frente, donde=""):
    """Un abatible o un cajón abierto, ¿deja pasar por delante?

    Es el choque que más se ve en obra: el lavavajillas abierto corta la cocina
    entera. Se mide contra lo que queda LIBRE, no contra la distancia total.
    """
    libre = paso_libre(distancia, fondo_a, fondo_b)
    barre = BARRIDO.get(_txt(tipo_frente).lower())
    if barre is None:
        return [_aviso("barrido", "sin_comprobar",
                       f"No se sabe cómo abre «{tipo_frente}»: no se puede comprobar "
                       "si corta el paso.", donde)]
    if libre is None:
        return [_aviso("barrido", "sin_comprobar",
                       "Sin la distancia entre paredes no se puede comprobar el "
                       "barrido del frente.", donde)]
    if barre == 0:
        return []
    queda = round(libre - barre, 1)
    if queda < 0:
        return [_aviso("barrido", "error",
                       f"Abierto barre {barre:g} cm y solo hay {libre:g} cm de paso: "
                       f"choca contra el frente de enfrente.", donde, queda)]
    if queda < 40:
        # 40 cm es lo que ocupa una persona de lado. Igual que arriba: es un
        # criterio, y va escrito en el propio aviso.
        return [_aviso("barrido", "aviso",
                       f"Con el frente abierto quedan {queda:g} cm de paso: no se "
                       "pasa por detrás sin cerrarlo.", donde, queda)]
    return []


# ─── 2. El rincón ───────────────────────────────────────────────────────────

def revisar_rincon(rincon, apertura=None, holgura=HOLGURA_RINCON_MIN, donde="el rincón"):
    """La puerta del módulo del rincón, ¿puede abrir?

    `rincon`: {ancho, fondo} — lo que ocupa la pared contigua, en cm.
    `apertura`: 'D', 'I' o None si nadie lo ha decidido todavía.

    Si la mano no está decidida NO se aprueba: se dice que falta. En la
    nomenclatura de tarifa eso es el sufijo D/I, y un código que llega al taller
    con D/I lo decide el taller con un 50 % de acertar.
    """
    r = rincon or {}
    fondo = _medida(r.get("fondo"))
    if fondo is None:
        return [_aviso("rincon", "sin_comprobar",
                       "No consta el fondo del rincón: no se puede comprobar si la "
                       "puerta abre.", donde)]
    if not _txt(apertura):
        return [_aviso("rincon", "sin_comprobar",
                       "El módulo del rincón no tiene mano decidida (sigue como D/I): "
                       "sin saber hacia dónde abre no se puede comprobar el choque.",
                       donde)]

    junquillo = _num(r.get("junquillo")) or 0
    if junquillo < holgura:
        return [_aviso("rincon", "error",
                       f"La puerta abre hacia el rincón y hay {junquillo:g} cm de "
                       f"junquillo; la casa pide {holgura:g}. Al abrir da contra la "
                       "pared o contra el tirador de al lado.", donde, junquillo)]
    return []


# ─── 3. Las instalaciones tienen su zona ────────────────────────────────────
#
# Propuesta 232: un desagüe, una toma de gas o un cuadro eléctrico tienen un
# espacio alrededor que no se puede tapar. Hoy eso vive en la cabeza de quien
# monta y aparece cuando ya está el mueble puesto.

# Cuánto hay que dejar libre alrededor de cada instalación, en cm a cada lado.
# Criterios de la casa: pendientes de confirmar, y cada aviso dice el número.
ZONA_INSTALACION = {
    "desague": 20,
    "toma_agua": 15,
    "gas": 25,
    "cuadro": 30,
    "caldera": 40,
}


def revisar_instalaciones(modulos, instalaciones, zonas=None):
    """¿Hay algún módulo tapando lo que no se puede tapar?

    `modulos`: [{id, x, largo}] a lo largo de la pared, en cm.
    `instalaciones`: [{tipo, x, pared}] — el punto donde está, en cm.

    Solo se comprueban las que tienen posición. Una instalación sin `x` no se
    da por buena: se dice que no se ha podido comprobar, porque «está por ahí»
    no es una posición.
    """
    z = {**ZONA_INSTALACION, **(zonas or {})}
    avisos = []
    for ins in instalaciones or []:
        tipo = _txt(ins.get("tipo")).lower()
        x = _num(ins.get("x"))
        margen = z.get(tipo)
        if margen is None:
            avisos.append(_aviso("instalacion", "sin_comprobar",
                                 f"«{tipo or 'sin tipo'}» no tiene zona definida: no se "
                                 "puede comprobar si algo la invade.", tipo))
            continue
        if x is None:
            avisos.append(_aviso("instalacion", "sin_comprobar",
                                 f"La {tipo} no tiene posición apuntada: hay que medir "
                                 "dónde está antes de poder comprobarlo.", tipo))
            continue

        for m in modulos or []:
            # La POSICIÓN sí puede ser 0 —el primer módulo empieza en la
            # esquina—, pero un largo de 0 es un módulo que no existe.
            mx = _num(m.get("x"))
            largo = _medida(m.get("largo"))
            if mx is None or largo is None:
                continue
            # ¿El módulo pisa la zona de la instalación?
            if mx < x + margen and (mx + largo) > x - margen:
                avisos.append(_aviso(
                    "instalacion", "aviso",
                    f"{_txt(m.get('id')) or 'Un módulo'} cae sobre la {tipo}, que pide "
                    f"{margen:g} cm libres a cada lado. Comprueba que se puede "
                    "registrar.",
                    _txt(m.get("id")) or tipo, margen))
    return avisos


# ─── El repaso completo ─────────────────────────────────────────────────────

def revisar(datos):
    """Todos los choques de una cocina, en una lista.

    `datos`: {distanciaParedes, filas:[{fondo}], rincon, aperturaRincon,
              frentes:[{tipo, donde}], modulos, instalaciones}
    """
    d = datos or {}
    avisos = []

    filas = d.get("filas") or []
    fondo_a = (filas[0] or {}).get("fondo") if len(filas) > 0 else None
    fondo_b = (filas[1] or {}).get("fondo") if len(filas) > 1 else 0

    # El paso solo tiene sentido con dos filas: en una cocina de una sola pared
    # no hay nada enfrente, y comprobarlo daría un aviso que no significa nada.
    if len(filas) > 1:
        avisos += revisar_paso(d.get("distanciaParedes"), fondo_a, fondo_b)
        for fr in d.get("frentes") or []:
            avisos += revisar_barrido(d.get("distanciaParedes"), fondo_a, fondo_b,
                                      fr.get("tipo"), fr.get("donde"))

    if d.get("rincon"):
        avisos += revisar_rincon(d.get("rincon"), d.get("aperturaRincon"))

    avisos += revisar_instalaciones(d.get("modulos"), d.get("instalaciones"))

    errores = [a for a in avisos if a["nivel"] == "error"]
    sin_comprobar = [a for a in avisos if a["nivel"] == "sin_comprobar"]
    return {
        "avisos": avisos,
        "errores": errores,
        "sinComprobar": sin_comprobar,
        # Limpio SOLO si no hay errores Y no ha quedado nada sin comprobar. Lo
        # segundo es lo que impide que este repaso deje tranquilo sin haber
        # mirado.
        "limpio": not errores and not sin_comprobar,
        "resumen": _resumen(len(errores),
                            len([a for a in avisos if a["nivel"] == "aviso"]),
                            len(sin_comprobar)),
    }


def _resumen(errores, avisos, sin_comprobar):
    if not errores and not avisos and not sin_comprobar:
        return "Sin choques: todo lo comprobable está comprobado."
    partes = []
    if errores:
        partes.append(f"{errores} choque(s)")
    if avisos:
        partes.append(f"{avisos} a mirar")
    if sin_comprobar:
        # Se nombra aparte a propósito: no son «cero choques», es que faltan
        # datos para poder decirlo.
        partes.append(f"{sin_comprobar} SIN comprobar por falta de datos")
    return " · ".join(partes) + "."
