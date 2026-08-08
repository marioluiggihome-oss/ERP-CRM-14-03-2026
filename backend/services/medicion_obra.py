# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
medicion_obra.py — LA MEDIDA TIENE TRES NIVELES, Y NO SE MEZCLAN.

Cálculo puro, sin base de datos, para poder probarlo.

EL PROBLEMA
-----------
Hoy una medida es un número y ya está. Pero el 3.245 que se escribió el día de
la venta y el 3.238 que midió el montador en la obra NO son la misma cosa, y
guardarlos en el mismo hueco significa que el segundo pisa al primero y nadie
se entera de que había siete milímetros de diferencia. Siete milímetros en el
hueco de una columna es un mueble que no entra.

LOS TRES NIVELES
----------------
    introducida — la que se tecleó al vender. Vale para presupuestar, NO para
                  cortar.
    tomada      — la que alguien midió en la obra, con el metro en la mano.
    confirmada  — la que se ha dado por buena para fabricar. La escribe una
                  persona, a mano.

Suben, no bajan: una medida confirmada sigue teniendo su tomada y su
introducida guardadas, porque la diferencia entre ellas es justo lo que hay que
poder mirar cuando algo sale mal.

LO QUE ESTE MÓDULO NO HACE, A PROPÓSITO
---------------------------------------
**No decide cuál es la buena.** Si la introducida y la tomada no coinciden, lo
dice y obliga a revisar; no se queda con la más nueva, ni con la más pequeña,
ni hace una media. Elegir por su cuenta es exactamente como se fabrica con la
medida equivocada sin que nadie llegue a saberlo.

**No confirma solo.** `confirmar` exige el valor. Copiar la tomada en silencio
sería inventarse el acto de comprobarla, que es lo único que separa un número
de una medida buena.

**No convierte la falta de dato en un cero.** Sin medida, `None`. Un cero es un
número y se cuela en el despiece; un `None` para la fabricación hasta que
alguien vaya con el metro.
"""

SIN_MEDIR = "sin_medir"
INTRODUCIDA = "introducida"
TOMADA = "tomada"
CONFIRMADA = "confirmada"

# De menos a más fiable. El orden es el que manda en `nivel`, y por eso está
# escrito una sola vez.
NIVELES = (SIN_MEDIR, INTRODUCIDA, TOMADA, CONFIRMADA)

ETIQUETA_NIVEL = {
    SIN_MEDIR: "Sin medir",
    INTRODUCIDA: "Introducida (de la venta)",
    TOMADA: "Tomada en obra",
    CONFIRMADA: "Confirmada para fabricar",
}


def _num(v):
    """Número, o None si no consta. Cadena vacía NO es cero."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _txt(v):
    return str(v or "").strip()


def nivel(medida):
    """Hasta dónde ha llegado esta medida.

    Se mira de arriba abajo: lo que manda es el nivel MÁS ALTO que tenga valor.
    Que exista la clave no basta —una `tomada` a None es una medida que nadie
    ha ido a tomar todavía— porque si contara, el nivel subiría solo con abrir
    el formulario.
    """
    m = medida or {}
    if _num(m.get("confirmada")) is not None:
        return CONFIRMADA
    if _num(m.get("tomada")) is not None:
        return TOMADA
    if _num(m.get("introducida")) is not None:
        return INTRODUCIDA
    return SIN_MEDIR


def valor_para_fabricar(medida):
    """El número con el que se puede cortar. None mientras no esté confirmado.

    NO cae a la tomada «porque es la más nueva». Una medida tomada es una
    medida que alguien apuntó; confirmarla es el acto de darla por buena, y
    saltárselo aquí lo borraría del proceso entero.
    """
    return _num((medida or {}).get("confirmada"))


def diferencia(medida):
    """Cuánto se separan la introducida y la tomada. None si falta alguna.

    En las unidades en que estén escritas: este módulo no convierte nada, y por
    eso tampoco puede equivocarse convirtiendo.
    """
    intro = _num((medida or {}).get("introducida"))
    tomada = _num((medida or {}).get("tomada"))
    if intro is None or tomada is None:
        return None
    return round(tomada - intro, 3)


def hay_discrepancia(medida, tolerancia=0):
    """¿Se separan lo bastante como para tener que mirarlo?

    Con `tolerancia` a 0 —lo normal— CUALQUIER diferencia se señala. Una
    tolerancia por defecto distinta de cero sería el programa decidiendo qué
    diferencia da igual, y eso depende de dónde esté la medida: 3 mm en un
    hueco de columna no es lo mismo que 3 mm en un zócalo.
    """
    d = diferencia(medida)
    if d is None:
        return False
    return abs(d) > (_num(tolerancia) or 0)


def revisar_una(medida, tolerancia=0):
    """Una medida, con su nivel, su diferencia y qué le falta.

    `medida`: {clave, etiqueta, introducida, tomada, confirmada, critica,
               unidad, notas}
    """
    m = dict(medida or {})
    n = nivel(m)
    d = diferencia(m)
    discrepa = hay_discrepancia(m, tolerancia)
    critica = bool(m.get("critica"))

    # Qué hay que hacer con ella, en una frase y en imperativo: un aviso que no
    # dice qué hacer se lee, se asiente y no se hace nada.
    if n == SIN_MEDIR:
        pendiente = "Nadie ha puesto esta medida todavía."
    elif n == INTRODUCIDA:
        pendiente = "Falta tomarla en obra con el metro."
    elif n == TOMADA and discrepa:
        pendiente = (f"No coincide con la de la venta ({d:+g} {_txt(m.get('unidad')) or 'mm'}). "
                     "Hay que revisarla y confirmar cuál vale.")
    elif n == TOMADA:
        pendiente = "Falta confirmarla para poder fabricar."
    elif discrepa:
        # Confirmada Y con diferencia: NO es un problema, es lo normal cuando
        # la obra no mide lo que decía el presupuesto. Se deja escrito porque
        # explica por qué el mueble no es el que se presupuestó.
        pendiente = ""
    else:
        pendiente = ""

    return {
        "clave": _txt(m.get("clave")),
        "etiqueta": _txt(m.get("etiqueta")) or _txt(m.get("clave")),
        "unidad": _txt(m.get("unidad")) or "mm",
        "introducida": _num(m.get("introducida")),
        "tomada": _num(m.get("tomada")),
        "confirmada": _num(m.get("confirmada")),
        "nivel": n,
        "nivelEtiqueta": ETIQUETA_NIVEL[n],
        "diferencia": d,
        "discrepa": discrepa,
        "critica": critica,
        # Bloquea la fabricación solo si es CRÍTICA y no está confirmada. Una
        # medida secundaria sin confirmar avisa; parar la obra por el ancho de
        # un zócalo haría que el aviso se ignorase también cuando importa.
        "bloquea": critica and n != CONFIRMADA,
        "valorParaFabricar": valor_para_fabricar(m),
        "pendiente": pendiente,
        "notas": _txt(m.get("notas")),
    }


def revisar(medidas, tolerancia=0):
    """Todas las medidas de la obra, con el estado en el que está cada una."""
    filas = [revisar_una(m, tolerancia) for m in (medidas or [])]
    bloqueos = [f for f in filas if f["bloquea"]]
    discrepancias = [f for f in filas if f["discrepa"]]
    confirmadas = [f for f in filas if f["nivel"] == CONFIRMADA]
    sin_medir = [f for f in filas if f["nivel"] == SIN_MEDIR]

    return {
        "medidas": filas,
        "total": len(filas),
        "confirmadas": len(confirmadas),
        "sinMedir": len(sin_medir),
        "discrepancias": discrepancias,
        "bloqueos": bloqueos,
        "puedeFabricar": not bloqueos,
        "resumen": _resumen(len(filas), len(confirmadas), len(sin_medir),
                            len(discrepancias), len(bloqueos)),
    }


def _resumen(total, confirmadas, sin_medir, discrepancias, bloqueos):
    if not total:
        return "No hay ninguna medida apuntada en esta obra."
    partes = [f"{confirmadas} de {total} confirmadas"]
    if sin_medir:
        partes.append(f"{sin_medir} sin medir")
    if discrepancias:
        # Se nombran SIEMPRE, aunque estén confirmadas: explican por qué lo
        # fabricado no es lo presupuestado.
        partes.append(f"{discrepancias} con diferencia entre venta y obra")
    if bloqueos:
        partes.append(f"{bloqueos} crítica(s) sin confirmar")
    return " · ".join(partes) + "."


def tomar(medida, valor, quien="", cuando=""):
    """Apunta la medida tomada en obra. NO toca la introducida.

    La introducida se guarda tal cual estaba: la diferencia entre las dos es lo
    que se quiere poder mirar, y pisarla la borraría.
    """
    m = dict(medida or {})
    v = _num(valor)
    if v is None:
        raise ValueError("Una medida tomada sin valor no es una medida tomada.")
    m["tomada"] = v
    m["tomadaPor"] = _txt(quien)
    m["tomadaAt"] = _txt(cuando)
    return m


def confirmar(medida, valor, quien="", cuando=""):
    """Da una medida por buena para fabricar, CON su valor.

    El valor es obligatorio y va aparte. Copiar aquí la tomada «porque es la
    que hay» convertiría confirmar en un botón que no comprueba nada, y confirmar
    es justo lo único que separa un número apuntado de una medida con la que se
    corta.
    """
    m = dict(medida or {})
    v = _num(valor)
    if v is None:
        raise ValueError(
            "Confirmar es escribir la medida buena: sin valor no se confirma.")
    m["confirmada"] = v
    m["confirmadaPor"] = _txt(quien)
    m["confirmadaAt"] = _txt(cuando)
    return m


def comparar_mediciones(medidas_a, medidas_b, etiqueta_a="A", etiqueta_b="B"):
    """Dos mediciones de la misma obra, una al lado de la otra.

    Es el caso de «la midió el comercial y luego el montador»: se enseñan las
    dos y las diferencias, y NO se elige. Elegir por su cuenta —la más nueva,
    la de quien tiene más galones— es como se acaba cortando con la mala.
    """
    por_clave_a = {_txt(m.get("clave")): m for m in (medidas_a or []) if _txt(m.get("clave"))}
    por_clave_b = {_txt(m.get("clave")): m for m in (medidas_b or []) if _txt(m.get("clave"))}

    filas = []
    for clave in sorted(set(por_clave_a) | set(por_clave_b)):
        a = por_clave_a.get(clave)
        b = por_clave_b.get(clave)
        va = valor_visible(a)
        vb = valor_visible(b)
        d = None if (va is None or vb is None) else round(vb - va, 3)
        filas.append({
            "clave": clave,
            "etiqueta": _txt((a or b or {}).get("etiqueta")) or clave,
            etiqueta_a: va,
            etiqueta_b: vb,
            "diferencia": d,
            # Falta en una de las dos: no es una diferencia de 0, es que una de
            # las dos mediciones no la trae.
            "soloEnUna": va is None or vb is None,
            "coincide": d == 0 if d is not None else None,
        })

    distintas = [f for f in filas if f["diferencia"] not in (None, 0)]
    faltan = [f for f in filas if f["soloEnUna"]]
    return {
        "filas": filas,
        "distintas": distintas,
        "faltan": faltan,
        "hayQueRevisar": bool(distintas or faltan),
        "resumen": _resumen_comparacion(len(filas), len(distintas), len(faltan)),
    }


def valor_visible(medida):
    """El número más fiable que tenga esa medida, sea del nivel que sea.

    Sirve para ENSEÑAR y para comparar dos mediciones; no para cortar — para
    eso está `valor_para_fabricar`, que solo devuelve la confirmada. Son dos
    preguntas distintas y por eso son dos funciones distintas.
    """
    m = medida or {}
    for campo in ("confirmada", "tomada", "introducida"):
        v = _num(m.get(campo))
        if v is not None:
            return v
    return None


def _resumen_comparacion(total, distintas, faltan):
    if not total:
        return "No hay medidas que comparar."
    if not distintas and not faltan:
        return f"Las {total} medidas coinciden."
    partes = []
    if distintas:
        partes.append(f"{distintas} no coinciden")
    if faltan:
        partes.append(f"{faltan} solo están en una de las dos")
    return "; ".join(partes) + f" (de {total}). Hay que revisarlas: el programa no elige."
