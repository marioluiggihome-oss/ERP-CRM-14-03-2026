# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
electro_hueco.py — ¿CABE ESE APARATO EN ESE HUECO?

Cálculo puro, sin base de datos, para poder probarlo. En MILÍMETROS.

POR QUÉ ESTO
------------
Es de los errores más caros y más tontos: la cocina está montada y el horno no
entra por ocho milímetros. Hoy el catálogo de electrodomésticos guarda código,
nombre, marca y precio — **ninguna medida**. O sea que nadie puede comprobar
nada, y la comprobación se hace de memoria o no se hace.

LO QUE NO SE INVENTA, QUE ES LO IMPORTANTE
------------------------------------------
**Sin ficha técnica NO se dice que cabe.** Se dice «pendiente de validación».
Un aparato sin medidas no es un aparato que quepa: es un aparato del que no se
sabe nada. Dar por bueno lo que no se ha mirado es exactamente cómo se llega al
montaje con un hueco de 596 y un horno de 600.

**El hueco que manda es el que pide el fabricante del aparato**, no el del
aparato. Un horno de 595 de ancho puede pedir 600 de hueco, y meterlo en 595
—que «cabe» mirando el aparato— lo deja sin poder abrir la puerta ni ventilar.

**La ventilación es medida, no un consejo.** Si el aparato pide 50 mm libres
por detrás, el fondo útil del hueco es el fondo menos esos 50. No contarlos es
la forma más habitual de que el frigorífico entre y luego no enfríe.

**No se ajusta nada por su cuenta.** Si no cabe, se dice cuánto falta y dónde.
Estirar el mueble o comerse la ventilación es una decisión de quien firma.
"""

# Las tres medidas sin las cuales no hay comprobación posible. El fondo se
# admite ausente en aparatos que no lo declaran (una placa encastrada), pero
# ancho y alto del hueco no: sin ellos no hay nada que comparar.
IMPRESCINDIBLES = ("anchoHueco", "altoHueco")

# Cómo se lee cada medida en un aviso.
NOMBRE = {"ancho": "ancho", "alto": "alto", "fondo": "fondo"}

SIN_FICHA = "sin_ficha"
CABE = "cabe"
NO_CABE = "no_cabe"


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


def ficha_completa(ficha):
    """¿Tiene esta ficha lo mínimo para poder comprobar algo?"""
    f = ficha or {}
    return all(_num(f.get(c)) is not None for c in IMPRESCINDIBLES)


def fondo_util(hueco, ficha):
    """El fondo que le queda al aparato después de la ventilación.

    La ventilación NO es un consejo: es milímetros que el aparato no puede
    ocupar. Restarla aquí es la diferencia entre un frigorífico que entra y uno
    que entra y no enfría.
    """
    fondo = _num((hueco or {}).get("fondo"))
    if fondo is None:
        return None
    vent = _num((ficha or {}).get("ventilacionFondo")) or 0
    return round(fondo - vent, 1)


def comprobar(ficha, hueco):
    """¿Cabe el aparato de `ficha` en el `hueco` diseñado?

    `ficha`: {marca, modelo, anchoHueco, altoHueco, fondoHueco,
              ventilacionFondo, ventilacionSuperior, tipoInstalacion, fuente}
    `hueco`: {ancho, alto, fondo}  — el hueco que deja el diseño, en mm

    Devuelve `cabe` a True, False o **None**. None es «no se sabe», y es un
    resultado legítimo: sin ficha no se afirma nada.
    """
    f = ficha or {}
    h = hueco or {}

    if not ficha_completa(f):
        faltan = [c for c in IMPRESCINDIBLES if _num(f.get(c)) is None]
        return {
            "estado": SIN_FICHA,
            "cabe": None,
            "aparato": _etiqueta(f),
            "holguras": {},
            "motivos": [],
            "avisos": [],
            "faltaEnFicha": faltan,
            "resumen": ("Sin ficha técnica fiable: pendiente de validación. "
                        "No se puede decir que quepa lo que no se ha medido."),
        }

    # Lo que pide el fabricante contra lo que deja el diseño.
    pares = [
        ("ancho", _num(f.get("anchoHueco")), _num(h.get("ancho"))),
        ("alto", _num(f.get("altoHueco")), _num(h.get("alto"))),
        ("fondo", _num(f.get("fondoHueco")), fondo_util(h, f)),
    ]

    holguras, motivos, avisos, sin_comprobar = {}, [], [], []
    for nombre, pide, hay in pares:
        if pide is None:
            # El aparato no declara esa medida. No es un problema: hay
            # aparatos que no la tienen (una placa no pide fondo de hueco).
            continue
        if hay is None:
            # El DISEÑO no la da. Eso sí es un agujero, y no se da por bueno.
            sin_comprobar.append(nombre)
            continue
        holgura = round(hay - pide, 1)
        holguras[nombre] = holgura
        if holgura < 0:
            motivos.append(f"Falta{'n' if abs(holgura) != 1 else ''} "
                           f"{abs(holgura):g} mm de {NOMBRE[nombre]}: "
                           f"el aparato pide {pide:g} y el hueco da {hay:g}.")
        elif holgura == 0:
            # Justo justo. Cabe según el fabricante, pero conviene saberlo: en
            # obra los milímetros aparecen y desaparecen.
            avisos.append(f"El {NOMBRE[nombre]} queda justo, sin un milímetro de holgura.")

    if (_num(f.get("ventilacionFondo")) or 0) > 0 and _num(h.get("fondo")) is not None:
        avisos.append(f"Descontados {_num(f.get('ventilacionFondo')):g} mm de ventilación por detrás.")

    if sin_comprobar:
        return {
            "estado": SIN_FICHA,
            "cabe": None,
            "aparato": _etiqueta(f),
            "holguras": holguras,
            "motivos": motivos,
            "avisos": avisos,
            "faltaEnHueco": sin_comprobar,
            "resumen": ("El diseño no da el " + ", ".join(NOMBRE[c] for c in sin_comprobar)
                        + " del hueco: no se puede comprobar. Pendiente de validación."),
        }

    cabe = not motivos
    return {
        "estado": CABE if cabe else NO_CABE,
        "cabe": cabe,
        "aparato": _etiqueta(f),
        "holguras": holguras,
        "motivos": motivos,
        "avisos": avisos,
        "resumen": _resumen(cabe, motivos, holguras),
    }


def _etiqueta(ficha):
    f = ficha or {}
    partes = [_txt(f.get("marca")), _txt(f.get("modelo"))]
    return " ".join(p for p in partes if p) or _txt(f.get("codigo")) or "Aparato sin identificar"


def _resumen(cabe, motivos, holguras):
    if not cabe:
        return motivos[0] if motivos else "No cabe."
    if holguras:
        justas = ", ".join(f"{NOMBRE[k]} {v:g} mm" for k, v in sorted(holguras.items()))
        return f"Cabe. Holgura: {justas}."
    return "Cabe."


def revisar(aparatos):
    """Todos los aparatos de la obra, con su comprobación.

    `aparatos`: [{ficha, hueco, donde}]

    Los que no tienen ficha se cuentan APARTE de los que no caben: no es lo
    mismo «no entra» que «no se sabe», y la acción a tomar es distinta —uno se
    arregla en el diseño, el otro llamando al proveedor por la ficha técnica.
    """
    filas = []
    for a in aparatos or []:
        r = comprobar((a or {}).get("ficha"), (a or {}).get("hueco"))
        r["donde"] = _txt((a or {}).get("donde"))
        filas.append(r)

    no_caben = [r for r in filas if r["estado"] == NO_CABE]
    sin_ficha = [r for r in filas if r["estado"] == SIN_FICHA]
    caben = [r for r in filas if r["estado"] == CABE]

    return {
        "aparatos": filas,
        "total": len(filas),
        "caben": len(caben),
        "noCaben": no_caben,
        "sinFicha": sin_ficha,
        # Se puede fabricar si NINGUNO falla Y ninguno está sin comprobar. Un
        # aparato sin ficha no es un aparato que quepa.
        "todoComprobado": not no_caben and not sin_ficha,
        "resumen": _resumen_global(len(filas), len(caben), len(no_caben), len(sin_ficha)),
    }


def _resumen_global(total, caben, no_caben, sin_ficha):
    if not total:
        return "No hay electrodomésticos apuntados en esta obra."
    partes = []
    if no_caben:
        partes.append(f"{no_caben} NO cabe(n)")
    if sin_ficha:
        partes.append(f"{sin_ficha} sin ficha técnica (pendiente de validación)")
    if not partes:
        return f"Los {caben} aparatos caben en su hueco."
    return " · ".join(partes) + f" (de {total})."
