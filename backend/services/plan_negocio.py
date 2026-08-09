# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
plan_negocio.py — EL PLAN DE NEGOCIO DE UNA FÁBRICA, DE ABAJO ARRIBA.

Cálculo puro, sin base de datos, para poder probarlo. Todo en EUROS y en
MUEBLES; las horas, en horas.

DE DÓNDE PARTE
--------------
No parte de «¿cuántas cocinas podemos vender?», que es una previsión y por tanto
un deseo. Parte de la fábrica, que es un hecho:

    personas → muebles/hora → coste real por mueble → margen B2B/B2C
    → pedidos necesarios → cuándo hace falta una persona más.

LA REGLA DE LA CASA, LA MISMA QUE EN EL RESTO DEL ERP
----------------------------------------------------
NO SE INVENTA UN DATO. Lo que no se sabe vale `None`, y todo lo que dependa de
ello vale `None` también. **Nunca 0.**

Un cero aquí es mucho peor que un hueco: un hueco se ve, y un 0 parece un
resultado. Un coste por mueble de 0 € da un margen del 100 %, un punto de
equilibrio de 0 muebles y un plan de negocio precioso — y todo mentira. Con un
`None` la pantalla dice «falta dato» y el plan no se puede firmar hasta que
alguien traiga el número. Que es exactamente lo que tiene que pasar.

Y UN CERO TAMPOCO ES UNA MEDIDA
-------------------------------
Un precio de compra de 0 € no es un casco regalado: es una casilla sin rellenar.
Igual que un ancho de 0 mm no es un mueble estrechísimo. Ojo: hay ceros que SÍ
significan algo —un gasto de estructura de 0 € es «no tengo ese gasto», y un
descuento de 0 es «sin descuento»—, y esos se respetan.
"""

# Las seis referencias de partida. Columnas, fregaderos y rinconeros entran
# cuando toque; la lista es un dato, no una verdad del programa.
REFERENCIAS = ("Bajo 45", "Bajo 60", "Bajo 90", "Alto 45", "Alto 60", "Alto 90")

# Lo que se compra o se consume por mueble. Se suma para dar el coste de
# materiales; la mano de obra va aparte porque sale de la capacidad.
COSTES_DE_MATERIAL = (
    "casco", "bisagras", "guias", "patasZocalo", "otrosHerrajes",
    "componentes", "embalaje", "otrosDirectos",
)

# Lo que cuesta vender y entregar en B2C y no existe en B2B.
COSTES_B2C = ("comisionComercial", "montaje", "transporte", "postventa")


def _num(v):
    """Número, o None si no consta. Cadena vacía NO es cero."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _importe(v):
    """Un número que puede ser un IMPORTE, o None.

    Se admite el 0: un gasto de estructura de 0 € significa «no tengo ese
    gasto», y eso es un dato. Lo que no se admite es lo que no se puede leer.
    """
    return _num(v)


def _precio(v):
    """Un número que puede ser un PRECIO DE COMPRA O DE VENTA, o None.

    AQUÍ EL 0 NO VALE. Un casco a 0 € no es un casco regalado: es una casilla
    sin rellenar. Y colado en el coste da un margen del 100 % y un plan de
    negocio que parece buenísimo.
    """
    n = _num(v)
    return None if n is None or n <= 0 else n


def _positivo(v):
    """Una cantidad que tiene que ser mayor que cero para significar algo:
    personas, muebles por hora, horas al año, años de amortización."""
    n = _num(v)
    return None if n is None or n <= 0 else n


def _r(v, dec=2):
    return None if v is None else round(v, dec)


# ─── 1. Capacidad ───────────────────────────────────────────────────────────

def capacidad(datos):
    """De las personas a los muebles al año, y al coste de la mano de obra.

    `datos`: {personas, mueblesHora, horasDia, diasSemana, horasAno,
              costeHoraPersona}

    OJO CON LAS HORAS: `horasAno` son las horas productivas DEL EQUIPO, ya
    descontadas vacaciones, festivos y paradas. La capacidad da por hecho que
    las personas están las mismas horas; si una se va de vacaciones, el equipo
    no produce a ese ritmo. No es un fallo del cálculo, es lo que significa el
    dato — y por eso se dice aquí.
    """
    d = datos or {}
    personas = _positivo(d.get("personas"))
    mh = _positivo(d.get("mueblesHora"))
    horas = _positivo(d.get("horasAno"))
    coste_hora = _precio(d.get("costeHoraPersona"))

    anual = _r(mh * horas, 0) if (mh is not None and horas is not None) else None

    # Coste del equipo por hora y, de ahí, lo que lleva de mano de obra un
    # mueble: lo que cuesta la hora del equipo entre los muebles de esa hora.
    equipo_hora = _r(personas * coste_hora) if (personas is not None and coste_hora is not None) else None
    mo_mueble = _r(equipo_hora / mh) if (equipo_hora is not None and mh is not None) else None

    horas_dia = _positivo(d.get("horasDia"))
    dias = _positivo(d.get("diasSemana"))
    semanal = _r(mh * horas_dia * dias, 0) if None not in (mh, horas_dia, dias) else None

    return {
        "personas": personas,
        "mueblesHora": mh,
        "horasAno": horas,
        "capacidadAnual": anual,
        "capacidadSemanal": semanal,
        "costeEquipoHora": equipo_hora,
        "manoObraPorMueble": mo_mueble,
    }


# ─── 2. Coste por mueble ────────────────────────────────────────────────────

def coste_referencia(ref, mano_obra):
    """El coste directo de UNA referencia: materiales + mano de obra.

    Si falta cualquier partida de material, el coste es None. No se suma «lo que
    hay»: un coste a medias no es un coste bajo, es un coste desconocido, y
    presentado como número se convierte en un margen que no existe.
    """
    r = ref or {}
    partidas = {}
    falta = []
    for c in COSTES_DE_MATERIAL:
        v = _precio(r.get(c))
        partidas[c] = v
        if v is None:
            falta.append(c)

    materiales = None if falta else _r(sum(partidas.values()))
    directo = _r(materiales + mano_obra) if (materiales is not None and mano_obra is not None) else None

    return {
        "nombre": r.get("nombre") or r.get("id") or "",
        "materiales": materiales,
        "manoObra": mano_obra,
        "costeDirecto": directo,
        "faltan": falta + ([] if mano_obra is not None else ["manoObra"]),
    }


def margen(precio, coste):
    """Margen en euros y en porcentaje sobre el PRECIO DE VENTA.

    Sobre el precio, no sobre el coste: un mueble que cuesta 100 y se vende a
    150 deja un 33 % de margen, no un 50 % de recargo. Confundirlos infla el
    plan entero.
    """
    p = _precio(precio)
    c = _num(coste)
    if p is None or c is None:
        return {"euros": None, "porcentaje": None}
    return {"euros": _r(p - c), "porcentaje": _r((p - c) / p, 4)}


def coste_b2c(datos):
    """Lo que cuesta vender y entregar un mueble en B2C y no existe en B2B.

    Aquí el 0 SÍ vale: no pagar comisión es un dato. Lo que no vale es dejarlo
    en blanco y que el margen B2C salga como si fuera el B2B.
    """
    d = datos or {}
    partes = {c: _importe(d.get(c)) for c in COSTES_B2C}
    falta = [c for c, v in partes.items() if v is None]
    return {
        "partes": partes,
        "total": None if falta else _r(sum(partes.values())),
        "faltan": falta,
    }


# ─── 3. El plan entero ──────────────────────────────────────────────────────

def _media(valores):
    buenos = [v for v in valores if v is not None]
    return _r(sum(buenos) / len(buenos)) if buenos else None


def calcular(entrada):
    """El plan completo a partir de lo que se sepa.

    `entrada`: {capacidad, referencias:[...], b2c, repartoB2B, estructura,
                inversion, plazoEntregaSemanas, escenarios:[...]}

    Devuelve TODO lo que se pueda calcular y, muy importante, `faltan`: la lista
    de lo que impide cerrar el plan. Un plan de negocio no se juzga solo por lo
    que dice, sino por lo que todavía no puede decir.
    """
    e = entrada or {}
    cap = capacidad(e.get("capacidad"))
    mo = cap["manoObraPorMueble"]

    refs_in = e.get("referencias") or []
    refs = []
    for r in refs_in:
        c = coste_referencia(r, mo)
        c["margenB2B"] = margen(r.get("precioB2B"), c["costeDirecto"])
        c["margenB2C"] = margen(r.get("precioB2C"), c["costeDirecto"])
        c["precioB2B"] = _precio(r.get("precioB2B"))
        c["precioB2C"] = _precio(r.get("precioB2C"))
        refs.append(c)

    coste_medio = _media([r["costeDirecto"] for r in refs])
    margen_b2b_medio = _media([r["margenB2B"]["euros"] for r in refs])
    margen_b2c_bruto = _media([r["margenB2C"]["euros"] for r in refs])
    precio_b2b_medio = _media([r["precioB2B"] for r in refs])
    precio_b2c_medio = _media([r["precioB2C"] for r in refs])

    b2c = coste_b2c(e.get("b2c"))
    # El margen de contribución B2C: lo que queda después de pagar la venta, el
    # montaje y el transporte. Es lo comparable con el margen B2B.
    margen_b2c = (_r(margen_b2c_bruto - b2c["total"])
                  if (margen_b2c_bruto is not None and b2c["total"] is not None) else None)

    # El reparto entre canales. Es una fracción (0,7 = 70 %), y el 0 vale: «no
    # vendo nada en B2B» es una decisión, no un hueco.
    reparto = _num(e.get("repartoB2B"))
    if reparto is not None and not (0 <= reparto <= 1):
        reparto = None

    margen_medio = None
    precio_medio = None
    if reparto is not None:
        if margen_b2b_medio is not None and margen_b2c is not None:
            margen_medio = _r(reparto * margen_b2b_medio + (1 - reparto) * margen_b2c)
        if precio_b2b_medio is not None and precio_b2c_medio is not None:
            precio_medio = _r(reparto * precio_b2b_medio + (1 - reparto) * precio_b2c_medio)

    estructura = _suma_bloque(e.get("estructura"))
    inversion = _suma_bloque(e.get("inversion"))

    # Punto de equilibrio: los muebles que hay que vender al año solo para pagar
    # la estructura. Si el margen medio fuera 0 o negativo no hay punto de
    # equilibrio que valga — no es que salga un número muy grande, es que no
    # existe: por muchos muebles que se vendan no se cubre nada.
    equilibrio = None
    if estructura["total"] is not None and margen_medio is not None and margen_medio > 0:
        equilibrio = _r(estructura["total"] / margen_medio, 0)

    parte_capacidad = None
    if equilibrio is not None and cap["capacidadAnual"]:
        parte_capacidad = _r(equilibrio / cap["capacidadAnual"], 4)

    facturacion = (_r(precio_medio * cap["capacidadAnual"], 0)
                   if (precio_medio is not None and cap["capacidadAnual"] is not None) else None)
    ebitda = None
    if margen_medio is not None and cap["capacidadAnual"] is not None and estructura["total"] is not None:
        ebitda = _r(margen_medio * cap["capacidadAnual"] - estructura["total"], 0)

    # Cuándo contratar: no por año de calendario, sino porque la cartera ya no
    # cabe en la fábrica. El aviso que funciona es el PLAZO DE ENTREGA.
    semanas = _positivo(e.get("plazoEntregaSemanas"))
    cartera_disparador = (_r(semanas * cap["capacidadSemanal"], 0)
                          if (semanas is not None and cap["capacidadSemanal"] is not None) else None)

    return {
        "capacidad": cap,
        "referencias": refs,
        "costeDirectoMedio": coste_medio,
        "b2c": b2c,
        "margenB2BMedio": margen_b2b_medio,
        "margenB2CMedio": margen_b2c,
        "repartoB2B": reparto,
        "margenMedioPonderado": margen_medio,
        "precioMedio": precio_medio,
        "estructura": estructura,
        "inversion": inversion,
        "amortizacionAnual": _amortizacion(e.get("inversion")),
        "puntoEquilibrio": equilibrio,
        "parteDeLaCapacidad": parte_capacidad,
        "facturacionPlenaCapacidad": facturacion,
        "ebitdaPlenaCapacidad": ebitda,
        "carteraParaContratar": cartera_disparador,
        "escenarios": _escenarios(e, margen_medio, precio_medio, estructura["total"]),
        "faltan": _que_falta(cap, refs, b2c, reparto, estructura, e),
        "sostenible": _sostenible(parte_capacidad),
    }


def _suma_bloque(bloque):
    """Un bloque de importes (estructura, inversión) con su total.

    El total es None si falta alguna línea: una estructura a medias sumada como
    si estuviera entera da un punto de equilibrio bajísimo, que es la forma más
    cara de equivocarse en un plan.
    """
    b = bloque or {}
    partes = {k: _importe(v) for k, v in b.items()}
    falta = [k for k, v in partes.items() if v is None]
    return {
        "partes": partes,
        "total": None if (falta or not partes) else _r(sum(partes.values()), 0),
        "faltan": falta,
        "vacio": not partes,
    }


def _amortizacion(inversion):
    """La maquinaria repartida entre sus años de vida."""
    i = inversion or {}
    maquinaria = _precio(i.get("maquinaria"))
    anos = _positivo(i.get("anosAmortizacion"))
    if maquinaria is None or anos is None:
        return None
    return _r(maquinaria / anos, 0)


def _escenarios(entrada, margen_medio, precio_medio, estructura_total):
    """Qué pasaría con 2, 3 o 4 personas.

    LA PRODUCTIVIDAD DE CADA ESCENARIO ES UN DATO QUE HAY QUE MEDIR, no una
    regla de tres. Suponer que tres personas rinden un 50 % más que dos es
    justo el tipo de número inventado que hunde un plan: con dos hay reparto de
    tareas, con tres puede haber más rendimiento o puede haber estorbo.

    Y el EBITDA de los escenarios grandes descuenta la estructura de HOY: al
    contratar sube el salario y puede subir el alquiler. Va dicho en `aviso`.
    """
    e = entrada or {}
    horas = _positivo((e.get("capacidad") or {}).get("horasAno"))
    salida = []
    for esc in e.get("escenarios") or []:
        mh = _positivo(esc.get("mueblesHora"))
        anual = _r(mh * horas, 0) if (mh is not None and horas is not None) else None
        salida.append({
            "nombre": esc.get("nombre") or "",
            "personas": _positivo(esc.get("personas")),
            "mueblesHora": mh,
            "capacidadAnual": anual,
            "facturacion": _r(anual * precio_medio, 0) if (anual is not None and precio_medio is not None) else None,
            "margenBruto": _r(anual * margen_medio, 0) if (anual is not None and margen_medio is not None) else None,
            "ebitda": (_r(anual * margen_medio - estructura_total, 0)
                       if None not in (anual, margen_medio, estructura_total) else None),
            "aviso": ("El EBITDA descuenta la estructura actual: al contratar sube."
                      if (esc.get("personas") or 0) > 2 else ""),
        })
    return salida


def _que_falta(cap, refs, b2c, reparto, estructura, entrada):
    """Lo que impide cerrar el plan, ordenado por lo que más desbloquea.

    Esta lista es la mitad del valor de todo esto. Un plan que no dice lo que le
    falta se lee como si estuviera terminado.
    """
    falta = []
    if cap["manoObraPorMueble"] is None:
        falta.append({"que": "Coste por hora de una persona (coste empresa)",
                      "donde": "capacidad.costeHoraPersona",
                      "porque": "Sin él no hay mano de obra por mueble, y sin ella no hay coste."})
    sin_casco = [r["nombre"] for r in refs if "casco" in (r["faltan"] or [])]
    if sin_casco:
        falta.append({"que": f"Precio de compra del casco ({', '.join(sin_casco)})",
                      "donde": "referencias[].casco",
                      "porque": "Es el dato número uno: sin coste no hay margen y sin margen no hay plan."})
    sin_precio = [r["nombre"] for r in refs if r["precioB2B"] is None and r["precioB2C"] is None]
    if sin_precio:
        falta.append({"que": f"Precio de venta ({', '.join(sin_precio)})",
                      "donde": "referencias[].precioB2B / precioB2C",
                      "porque": "Es una decisión comercial, no un cálculo."})
    if b2c["faltan"]:
        falta.append({"que": "Costes comerciales del B2C: " + ", ".join(b2c["faltan"]),
                      "donde": "b2c",
                      "porque": "Es lo que separa el margen B2C del B2B."})
    if reparto is None:
        falta.append({"que": "Reparto de ventas entre B2B y B2C",
                      "donde": "repartoB2B",
                      "porque": "Cambia el margen medio y con él el punto de equilibrio."})
    if estructura["vacio"] or estructura["faltan"]:
        falta.append({"que": "Gastos de estructura del año",
                      "donde": "estructura",
                      "porque": "Es el listón que hay que superar; sin él no hay punto de equilibrio."})
    if _positivo((entrada or {}).get("plazoEntregaSemanas")) is None:
        falta.append({"que": "Plazo de entrega que se quiere prometer",
                      "donde": "plazoEntregaSemanas",
                      "porque": "Convierte «vamos llenos» en una señal concreta de contratar."})
    return falta


def _sostenible(parte):
    """¿Se sostiene la estructura con esta fábrica?

    None mientras no se sepa. Si hay que vender más del 100 % de lo que se puede
    fabricar, la respuesta es que NO: no es que haya que apretar, es que con
    esta estructura no sale, y hay que bajar coste o subir precio.
    """
    if parte is None:
        return None
    return parte <= 1
