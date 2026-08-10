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

def mano_obra_de(ref, coste_equipo_hora, media_por_mueble):
    """Lo que cuesta MONTAR ese mueble, a partir del TIEMPO que lleva.

    POR QUÉ EL TIEMPO Y NO UN COSTE
    -------------------------------
    Un coste por mueble no se mide: se estima. El tiempo sí — con un cronómetro,
    en la propia fábrica. Y es lo único que cambia de verdad entre referencias:
    un bajo de 90 con cajones no lleva lo mismo que un alto de 45, y darles a los
    dos la misma mano de obra reparte mal el coste y luego el margen.

    Los MINUTOS son de EQUIPO, no de persona: si los dos montan el mismo mueble
    durante 20 minutos, son 20 minutos de equipo, no 40. Es la misma cuenta que
    la capacidad (3 muebles/hora del equipo), y mezclarlas duplicaría el coste.

    Si no se ha medido, se usa la media que sale de la capacidad. Es un dato
    peor —una media reparte igual lo caro y lo barato— y por eso se dice de dónde
    viene con `fuente`.
    """
    minutos = _positivo((ref or {}).get("minutosPorMueble"))
    if minutos is not None and coste_equipo_hora is not None:
        return _r(coste_equipo_hora * minutos / 60), "medido", minutos
    return media_por_mueble, "media", minutos


def coste_referencia(ref, mano_obra):
    """El coste directo de UNA referencia: materiales + mano de obra.

    DOS FORMAS DE DAR EL MATERIAL, Y LAS DOS VALEN
    ----------------------------------------------
    1. UN SOLO NÚMERO por mueble (`costeMaterialesMueble`). Es lo normal al
       empezar: se sabe lo que cuesta el mueble entero y no cómo se reparte.
    2. EL DESGLOSE en ocho partidas. Sirve para saber DÓNDE está el coste
       cuando llegue el momento de apretar al proveedor.

    Si hay número por mueble, MANDA ÉL. El desglose se queda guardado pero no se
    usa: sumar los dos sería contar el material dos veces, y mezclar en silencio
    dos fuentes que no cuadran es peor que no tener ninguna. Por eso se devuelve
    `fuente`, para que la pantalla diga cuál está usando.

    OJO: es el coste del MATERIAL, sin mano de obra. La mano de obra sale de la
    fábrica (personas, muebles/hora y coste por hora) y se suma aquí. Meterla
    también en ese número la contaría dos veces.

    Si se va por el desglose y falta una sola partida, el coste es None. No se
    suma «lo que hay»: un coste a medias no es un coste bajo, es un coste
    desconocido, y presentado como número se convierte en un margen que no
    existe.
    """
    r = ref or {}

    directo_material = _precio(r.get("costeMaterialesMueble"))
    partidas = {c: _precio(r.get(c)) for c in COSTES_DE_MATERIAL}

    if directo_material is not None:
        materiales, falta, fuente = directo_material, [], "por_mueble"
    else:
        falta = [c for c, v in partidas.items() if v is None]
        # Con el desglose entero a medias, lo que falta de verdad es EL COSTE:
        # decir «faltan ocho partidas» cuando no se ha empezado a rellenar nada
        # es ruido. Se nombra la pieza que desbloquea, que es el casco.
        materiales = None if falta else _r(sum(partidas.values()))
        fuente = "desglose"
        if len(falta) == len(COSTES_DE_MATERIAL):
            falta = ["costeMaterialesMueble"]

    coste = _r(materiales + mano_obra) if (materiales is not None and mano_obra is not None) else None

    return {
        "nombre": r.get("nombre") or r.get("id") or "",
        "materiales": materiales,
        "manoObra": mano_obra,
        "costeDirecto": coste,
        "fuente": fuente,
        "partidas": partidas,
        "faltan": falta + ([] if mano_obra is not None else ["manoObra"]),
    }


def margen(precio, coste):
    """Lo que deja un mueble, contado de las TRES maneras que se usan.

    Son tres formas de mirar lo mismo, y confundirlas es el error de cuentas más
    caro que hay en este oficio. Un mueble que cuesta 100 y se vende a 150:

      · MARGEN  33,3 %  — sobre el PRECIO DE VENTA. Es el que va a la cuenta de
        resultados y el que se compara con Howdens o Nobia.
      · RECARGO 50,0 %  — sobre el COSTE. Es lo que se le suma al coste para
        llegar al precio. SIEMPRE es mayor que el margen.
      · COEFICIENTE ×1,50 — el multiplicador. Es como se trabaja en tarifa: se
        coge el coste y se multiplica.

    Dar por bueno un «50 %» sin decir sobre qué es como se acaba vendiendo con
    un tercio menos de margen del que se creía.
    """
    p = _precio(precio)
    c = _num(coste)
    if p is None or c is None:
        return {"euros": None, "porcentaje": None, "recargo": None, "coeficiente": None}
    euros = _r(p - c)
    # El recargo y el coeficiente se dividen por el COSTE: con coste 0 o menos no
    # significan nada, y un «infinito %» en un plan no es un dato.
    sobre_coste = c > 0
    return {
        "euros": euros,
        "porcentaje": _r((p - c) / p, 4),
        "recargo": _r((p - c) / c, 4) if sobre_coste else None,
        "coeficiente": _r(p / c, 3) if sobre_coste else None,
    }


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
        mo_ref, fuente_mo, minutos = mano_obra_de(r, cap["costeEquipoHora"], mo)
        c = coste_referencia(r, mo_ref)
        c["fuenteManoObra"] = fuente_mo
        c["minutosPorMueble"] = minutos
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

    # ── El coste COMPLETO: el directo más su parte de estructura ────────────
    #
    # Se calcula DOS VECES a propósito:
    #   · a plena capacidad — el suelo teórico, el mejor caso posible.
    #   · a las ventas que se esperan de verdad — el que hay que mirar.
    # Enseñar solo el primero es como se firman tarifas que solo salen si la
    # fábrica va llena, y llena no va casi nunca el primer año.
    tasa = tasa_horaria(cap, estructura["total"])
    ventas = _positivo(e.get("ventasEsperadas"))
    h_vendidas = horas_vendidas(ventas, cap)
    tasa_real = tasa_horaria({**cap, "horasAno": h_vendidas}, estructura["total"])

    minutos_medios = 60.0 / cap["mueblesHora"] if cap.get("mueblesHora") else None
    for r in refs:
        minutos = r.get("minutosPorMueble") or minutos_medios
        r["costeCompleto"] = coste_completo(r["materiales"], minutos, tasa["total"])
        r["costeCompletoReal"] = coste_completo(r["materiales"], minutos, tasa_real["total"])
        r["margenCompletoB2B"] = margen(r["precioB2B"], r["costeCompleto"])
        r["margenCompletoB2C"] = margen(r["precioB2C"], r["costeCompleto"])
        r["margenRealB2B"] = margen(r["precioB2B"], r["costeCompletoReal"])
        r["margenRealB2C"] = margen(r["precioB2C"], r["costeCompletoReal"])
        # Un mueble que a plena capacidad gana y a las ventas reales pierde es
        # el caso que hay que ver de un vistazo: el precio no se sostiene.
        r["pierdeEnReal"] = (r["margenRealB2B"]["euros"] is not None
                             and r["margenRealB2B"]["euros"] < 0)
    coste_completo_medio = _media([r["costeCompleto"] for r in refs])
    coste_real_medio = _media([r["costeCompletoReal"] for r in refs])

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
        "avisoTiempos": _cuadran_los_tiempos(cap, refs),
        "tasaHoraria": tasa,
        "tasaHorariaReal": tasa_real,
        "ventasEsperadas": ventas,
        "horasVendidas": h_vendidas,
        "costeCompletoMedio": coste_completo_medio,
        "costeCompletoRealMedio": coste_real_medio,
        "avisoAbsorcion": _aviso_absorcion(cap, estructura["total"], tasa, tasa_real, ventas),
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


def tasa_horaria(cap, estructura_total):
    """LO QUE CUESTA UNA HORA DE FÁBRICA, CON TODO DENTRO.

    La mano de obra no es lo único que se consume al montar un mueble: mientras
    el equipo monta, la nave se paga, la luz corre, el ERP se paga y el seguro
    también. Repartir todo eso entre las horas productivas del año da el coste
    de verdad de una hora de fábrica.

    De aquí sale la diferencia entre las dos preguntas que hay que saber
    contestar, y que NO son la misma:

      · ¿Este mueble aporta? → margen sobre el COSTE DIRECTO. Sirve para decidir
        si vale la pena aceptar un pedido más con la fábrica ya montada.
      · ¿Este mueble gana dinero? → margen sobre el COSTE COMPLETO. Es el que
        dice si el precio de tarifa se sostiene.

    Un negocio que solo mira el primero llena la fábrica de trabajo que aporta y
    pierde dinero igual a fin de año.
    """
    mo_hora = cap.get("costeEquipoHora")
    horas = cap.get("horasAno")
    est_hora = (_r(estructura_total / horas)
                if (estructura_total is not None and horas) else None)
    total = _r(mo_hora + est_hora) if (mo_hora is not None and est_hora is not None) else None
    return {"manoObra": mo_hora, "estructura": est_hora, "total": total}


def coste_completo(materiales, minutos, tasa_total):
    """El coste de un mueble con su parte de estructura dentro."""
    if materiales is None or minutos is None or tasa_total is None:
        return None
    return _r(materiales + tasa_total * minutos / 60)


def horas_vendidas(ventas_esperadas, cap):
    """Las horas de fábrica que se van a ocupar de verdad con esas ventas."""
    ventas = _positivo(ventas_esperadas)
    mh = cap.get("mueblesHora")
    if ventas is None or not mh:
        return None
    return _r(ventas / mh, 1)


def _aviso_absorcion(cap, estructura_total, tasa, tasa_real, ventas):
    """LA TRAMPA DEL COSTE COMPLETO, DICHA EN VOZ ALTA.

    Repartir la estructura entre las horas del año da por hecho que esas horas
    SE VENDEN TODAS. Si la fábrica va a media carga, la misma estructura se
    reparte entre la mitad de muebles y cada uno carga el doble.

    O sea que el coste completo NO ES UN DATO FIJO DEL MUEBLE: depende de cuánto
    se venda. Callarlo es exactamente como se firman tarifas que solo salen a
    plena capacidad — y a plena capacidad no se está casi nunca el primer año.
    """
    capacidad = cap.get("capacidadAnual")
    if estructura_total is None or tasa.get("total") is None:
        return None

    if ventas is None or not capacidad:
        return {
            "nivel": "aviso",
            "texto": ("El coste completo de arriba reparte la estructura entre "
                      "TODAS las horas del año: sale suponiendo la fábrica llena. "
                      "Pon cuántos muebles esperas vender y se calcula el coste "
                      "de verdad."),
        }

    ocupacion = ventas / capacidad
    if tasa_real.get("total") is None:
        return None
    return {
        "nivel": "error" if ocupacion < 0.5 else "aviso",
        "ocupacion": _r(ocupacion, 4),
        "texto": (f"Con {ventas:g} muebles al año se ocupa el "
                  f"{ocupacion * 100:.0f} % de la fábrica. La hora deja de costar "
                  f"{tasa['total']:.0f} € y cuesta {tasa_real['total']:.0f} €: la "
                  "misma estructura repartida entre menos horas. Los márgenes "
                  "buenos son los de la columna «real», no los de plena capacidad."),
    }


def _cuadran_los_tiempos(cap, refs):
    """¿Los minutos medidos cuadran con los 3 muebles/hora declarados?

    DOS MEDIDAS DE LO MISMO QUE NO COINCIDEN NO SE PROMEDIAN: SE DICEN.

    La capacidad dice cuántos muebles salen en una hora; los minutos medidos
    dicen lo que tarda cada uno. Son la misma cosa contada de dos maneras, y si
    no cuadran una de las dos está mal — y las dos se están usando: la capacidad
    para el techo de producción y los minutos para el coste. Callarlo deja un
    plan que se contradice consigo mismo sin que se note.

    Devuelve None mientras no haya con qué comparar. Un margen del 15 % es de
    casa: por debajo de eso la diferencia es ruido de medir.
    """
    mh = cap.get("mueblesHora")
    medidos = [r.get("minutosPorMueble") for r in refs if r.get("minutosPorMueble")]
    if not mh or len(medidos) < 2:
        return None
    esperado = 60.0 / mh                      # minutos de equipo por mueble
    media = sum(medidos) / len(medidos)
    desvio = abs(media - esperado) / esperado
    if desvio <= 0.15:
        return None
    return {
        "esperado": _r(esperado, 1),
        "medido": _r(media, 1),
        "texto": (f"Los tiempos medidos dan una media de {media:.0f} min por mueble, "
                  f"pero {mh:g} muebles/hora son {esperado:.0f} min. Una de las dos "
                  "medidas está mal, y las dos se están usando: la capacidad para el "
                  "techo de producción y los minutos para el coste."),
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
    sin_coste = [r["nombre"] for r in refs if r["materiales"] is None]
    if sin_coste:
        falta.append({"que": f"Coste del material por mueble ({', '.join(sin_coste)})",
                      "donde": "referencias[].costeMaterialesMueble (o el desglose)",
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
