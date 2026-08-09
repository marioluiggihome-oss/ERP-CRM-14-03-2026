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

# ─── DE DONDE SALE CADA NUMERO ──────────────────────────────────────────────
#
# «¿De donde salen esos 2.845?» tiene que poder contestarse. Un numero sin
# origen no se puede discutir con nadie: ni con el cliente, ni con el
# arquitecto, ni con el montador que dice que ahi no cabe.
#
# `heredada` es la que viene de otro proyecto o de una version anterior, y es la
# mas peligrosa de todas justamente porque parece tan buena como las demas.
ORIGENES = {
    "obra": "Medida en obra",
    "plano_arquitecto": "Plano del arquitecto",
    "plano_cliente": "Plano del cliente",
    "manual": "Introducida a mano",
    "heredada": "Heredada de otro proyecto",
}

# Cuales se consideran comprobadas sobre el terreno. Las demas llevan aviso de
# NO VERIFICADA, que no es lo mismo que estar mal: es que nadie ha ido a
# mirarlo.
ORIGENES_VERIFICADOS = ("obra",)

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


def puntos_de(medida):
    """Las tomas sueltas de una misma cota, cuando la pared no es recta.

    Una pared no mide «3.150». Mide 3.150 arriba, 3.143 en medio y 3.138 abajo,
    y para un mueble a medida esa diferencia de 12 mm es la que decide si el
    frente cierra o no. Guardar solo un numero es tirar el dato que importa.

    `medida["puntos"]`: [{etiqueta, valor}] — se admite tambien una lista de
    numeros sueltos, que es como se teclea deprisa en obra.
    """
    fuera = []
    for i, p in enumerate(((medida or {}).get("puntos") or [])):
        if isinstance(p, dict):
            v = _num(p.get("valor"))
            etq = _txt(p.get("etiqueta")) or f"Punto {i + 1}"
        else:
            v = _num(p)
            etq = f"Punto {i + 1}"
        if v is None:
            continue
        fuera.append({"etiqueta": etq, "valor": v})
    return fuera


def irregularidad(medida):
    """Cuanto baila esa cota entre sus puntos, y por donde.

    Devuelve None si no hay al menos dos puntos: con uno solo no hay nada que
    comparar, y sacar un 0 diria que la pared esta recta cuando lo que pasa es
    que se ha medido una vez.

    NO se elige un valor «bueno» entre los puntos. La mas pequenia se ofrece
    aparte porque es la que manda para que el mueble ENTRE, pero quien decide
    es quien firma: puede haber un rodapie, un alicatado o una decision de
    recortar en obra que aqui no se sabe.
    """
    ptos = puntos_de(medida)
    if len(ptos) < 2:
        return None
    valores = [p["valor"] for p in ptos]
    menor = min(ptos, key=lambda p: p["valor"])
    mayor = max(ptos, key=lambda p: p["valor"])
    return {
        "puntos": ptos,
        "minimo": menor["valor"], "dondeMinimo": menor["etiqueta"],
        "maximo": mayor["valor"], "dondeMaximo": mayor["etiqueta"],
        "recorrido": round(mayor["valor"] - menor["valor"], 3),
        # El que manda para que el mueble entre. Se ofrece, no se aplica.
        "elMasEstrecho": menor["valor"],
        "media": round(sum(valores) / len(valores), 3),
    }


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
    org = _txt(m.get("origen"))
    irreg = irregularidad(m)

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
        # DE DONDE SALE. Un origen que no esta en la lista se deja tal cual en
        # vez de caer a «manual»: inventarle procedencia a un dato es
        # exactamente lo contrario de lo que sirve esto.
        "origen": org,
        "origenEtiqueta": ORIGENES.get(org, org),
        # NO VERIFICADA no quiere decir mal: quiere decir que nadie ha ido a
        # mirarlo. Sin origen tampoco se da por verificada — no consta que
        # alguien lo comprobara.
        "verificada": org in ORIGENES_VERIFICADOS,
        # La pared que no es recta, cuando se han tomado varios puntos.
        "irregularidad": irreg,
        "pendiente": pendiente,
        "notas": _txt(m.get("notas")),
        # QUIÉN Y CUÁNDO viajan siempre, aunque la pantalla no los pinte.
        # La pantalla devuelve esta misma lista al guardar, así que lo que no
        # salga de aquí se pierde en el viaje de vuelta: añadir una medida
        # borraría quién tomó las demás, y sin eso una medida no se puede
        # preguntar a nadie.
        "tomadaPor": _txt(m.get("tomadaPor")),
        "tomadaAt": _txt(m.get("tomadaAt")),
        "confirmadaPor": _txt(m.get("confirmadaPor")),
        "confirmadaAt": _txt(m.get("confirmadaAt")),
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


def impacto_en_modulos(medida, modulos):
    """A QUE MUEBLES afecta esta diferencia de medida.

    «La pared da 53 mm menos» no le dice nada a nadie hasta que se sabe a que
    muebles toca. Es la diferencia entre enterarse ahora y enterarse durante el
    montaje.

    `medida`: la de siempre, con `pared` para saber de cual se habla.
    `modulos`: [{id, pared, ancho}] — los de esa pared, en las MISMAS unidades
               que la medida. Aqui no se convierte nada, y por eso tampoco se
               puede equivocar convirtiendo.

    LO QUE NO HACE: elegir a cual se le quitan los milimetros. Recortar el
    ultimo, meter un relleno o repartirlo entre todos son decisiones distintas,
    con precios distintos, y las toma quien firma el proyecto.
    """
    m = medida or {}
    pared = _txt(m.get("pared"))
    # La diferencia que importa es contra la medida con la que se va a
    # fabricar; si aun no hay confirmada, contra la de obra.
    nueva = _num(m.get("confirmada"))
    if nueva is None:
        nueva = _num(m.get("tomada"))
    vieja = _num(m.get("introducida"))

    if nueva is None or vieja is None:
        return {"pared": pared, "diferencia": None, "modulos": [], "suma": None,
                "resumen": "Faltan las dos medidas para poder decir a qué afecta.",
                "sinComprobar": True}

    dif = round(nueva - vieja, 3)
    if not pared:
        # Sin saber de que pared se habla no se puede tocar nada. Decir «no
        # afecta a nada» seria mentir en la direccion peligrosa.
        return {"pared": "", "diferencia": dif, "modulos": [], "suma": None,
                "resumen": ("Esta medida no dice de qué pared es: no se puede saber a "
                            "qué muebles afecta."),
                "sinComprobar": True}

    de_esa_pared = [x for x in (modulos or []) if _txt(x.get("pared")) == pared]
    sin_pared = [x for x in (modulos or []) if not _txt(x.get("pared"))]

    anchos = [_num(x.get("ancho")) for x in de_esa_pared]
    suma = round(sum(a for a in anchos if a is not None), 3) if de_esa_pared else None
    sin_ancho = [_nombre(x) for x, a in zip(de_esa_pared, anchos) if a is None]
    nombres_sin_pared = [_nombre(x) for x in sin_pared]

    return {
        "pared": pared,
        "diferencia": dif,
        "modulos": [_nombre(x) for x in de_esa_pared],
        "suma": suma,
        "sinAncho": sin_ancho,
        # Modulos que no dicen en que pared estan: no se puede afirmar que NO
        # les afecta, asi que se nombran.
        "sinPared": nombres_sin_pared,
        "sinComprobar": bool(sin_ancho or sin_pared) or not de_esa_pared,
        "resumen": _resumen_impacto(pared, dif, de_esa_pared, suma, sin_ancho,
                                    nombres_sin_pared),
    }


def _nombre(modulo):
    return _txt((modulo or {}).get("id")) or "sin nombre"


def _resumen_impacto(pared, dif, de_esa_pared, suma, sin_ancho, sin_pared):
    if dif == 0:
        return f"La {pared} mide lo previsto: no afecta a ningún mueble."
    if not de_esa_pared:
        return (f"La {pared} cambia {dif:+g}, pero no hay ningún mueble asignado a "
                "esa pared: no se puede decir a qué afecta.")
    quienes = ", ".join(_nombre(x) for x in de_esa_pared)
    verbo = "faltan" if dif < 0 else "sobran"
    texto = (f"La {pared} cambia {dif:+g}: {verbo} {abs(dif):g} en un frente de "
             f"{len(de_esa_pared)} mueble(s) — {quienes}. El programa NO elige a cuál "
             "se le quitan: recortar uno, meter un relleno o repartirlo son "
             "decisiones distintas.")
    if suma is not None:
        texto += f" Suman {suma:g}."
    if sin_ancho:
        texto += f" Sin ancho: {', '.join(sin_ancho)}."
    if sin_pared:
        texto += f" Y hay muebles sin pared asignada ({', '.join(sin_pared)}): mírales."
    return texto


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
