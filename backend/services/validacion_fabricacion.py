# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
validacion_fabricacion.py — EXPEDIENTE DE VALIDACIÓN antes de fabricar.

Contesta a una sola pregunta, que hoy se contesta a ojo: *¿está este proyecto
en condiciones de bajar al taller?*

Cálculo puro, sin base de datos, para poder probarlo.

TRES REGLAS QUE LO SEPARAN DE UNA LISTA DE CASILLAS
---------------------------------------------------
1. **Cada comprobación se DERIVA del proyecto**, no la marca nadie a mano. Una
   casilla que se marca sola acaba marcada siempre: el primer día se mira, el
   décimo se pulsa sin leer. Aquí no hay nada que pulsar — o el dato está, o no.

2. **"No se sabe" NO es "correcto".** Si un módulo no tiene fondo, la respuesta
   no es "correcto" ni "incorrecto": es que falta el dato. Y falta el dato es
   motivo suficiente para no bajar al taller, porque abajo alguien tendrá que
   inventárselo.

3. **Cada aviso dice DÓNDE.** No "faltan medidas", sino "falta el fondo del
   módulo M07". Un aviso que no lleva a ninguna parte obliga a repasar el
   proyecto entero, y eso no se hace: se ignora.

QUÉ BLOQUEA Y QUÉ SOLO AVISA
----------------------------
Bloquea lo que hace imposible fabricar bien (una medida que falta, un sentido
de apertura sin decidir). Avisa lo que conviene mirar pero no impide cortar.
Si todo bloqueara, se saltaría el circuito entero a la primera urgencia.
"""

# La medición de obra se carga a mano, no con un `from services import`.
#
# Este módulo es CÁLCULO PURO y se prueba cargándolo por ruta, suelto, sin
# levantar el paquete `services` —que arrastra la autenticación y exige un
# JWT_SECRET—. Un import normal lo ataría a todo eso y dejaría de poder
# probarse. `medicion_obra` tampoco importa nada, así que se carga igual de
# suelto y las dos formas funcionan.
#
# No es un respaldo silencioso: si el fichero no estuviera, las dos vías
# fallarían y se enteraría todo el mundo.
def _cargar_suelto(nombre, alias):
    import importlib.util as _ilu
    import os as _os
    ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), nombre + ".py")
    spec = _ilu.spec_from_file_location(alias, ruta)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    from services import medicion_obra           # dentro del ERP
except Exception:                                # cargado suelto, por ruta
    medicion_obra = _cargar_suelto("medicion_obra", "_medicion_obra_de_validacion")

try:
    from services import linea_pedido
except Exception:
    linea_pedido = _cargar_suelto("linea_pedido", "_linea_pedido_de_validacion")

# Estados de una comprobación.
OK = "ok"
FALTA = "falta"           # el dato deberia estar y no esta
SIN_DATOS = "sin_datos"   # no hay forma de comprobarlo
NO_APLICA = "no_aplica"


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _medida(v):
    """Un número que puede ser una MEDIDA, o None.

    UN CERO NO ES UNA MEDIDA, y es peor que un hueco vacío: un vacío se ve, y
    un 0 parece un dato. Un módulo con alto 0 y fondo 0 pasaba estas
    comprobaciones EN VERDE, y de ahí bajaba al taller.

    Vale solo para medidas. Una cantidad de 0 o un stock de 0 sí significan
    algo, y ahí se sigue usando `_num`.
    """
    n = _num(v)
    return None if n is None or n <= 0 else n


def _lineas(proyecto):
    p = proyecto or {}
    return (p.get("itemsMontada") or []) + (p.get("itemsDespiece") or [])


def _ident(linea, i):
    """Cómo se nombra una línea en un aviso, para poder ir a ella.

    Lo resuelve `linea_pedido`, que conoce los nombres de los tres
    presupuestadores. Con la lista de antes, una línea de Cocina Desmontada
    —que trae `cod` y `descripcion`— salía siempre como «línea 7», que no lleva
    a ninguna parte.
    """
    return linea_pedido.identificar(linea, i)


def _check(clave, grupo, etiqueta, estado, bloquea=False, detalle="", donde=None):
    return {"clave": clave, "grupo": grupo, "etiqueta": etiqueta, "estado": estado,
            "bloquea": bloquea and estado in (FALTA, SIN_DATOS),
            "detalle": detalle, "donde": donde}


# ─── Comprobaciones ─────────────────────────────────────────────────────────

def _medidas_de_modulos(proyecto):
    """Cada módulo tiene que traer ancho y alto. Sin eso no se corta nada."""
    lineas = _lineas(proyecto)
    if not lineas:
        return _check("medidas_modulos", "MEDIDAS", "Medidas de los módulos",
                      SIN_DATOS, True, "El proyecto no tiene ninguna línea.")
    faltan = []
    for i, l in enumerate(lineas):
        sin = [n for n, v in (("ancho", l.get("width") or l.get("ancho")),
                              ("alto", l.get("height") or l.get("alto")))
               if _medida(v) is None]
        if sin:
            faltan.append((_ident(l, i), sin))
    if not faltan:
        return _check("medidas_modulos", "MEDIDAS", "Medidas de los módulos", OK)
    # «falta» cubre las dos cosas —no está o está a cero— y las dos se
    # arreglan igual: yendo a esa línea y escribiendo la medida buena.
    detalle = "; ".join(f"{ident}: falta {' y '.join(qs)}" for ident, qs in faltan[:5])
    return _check("medidas_modulos", "MEDIDAS", "Medidas de los módulos", FALTA, True,
                  detalle + ("…" if len(faltan) > 5 else ""),
                  {"tipo": "linea", "ids": [i for i, _ in faltan]})


def _fondos(proyecto):
    """El fondo no siempre viaja en la línea; si falta en TODAS, no es que cada
    una lo haya perdido: es que ese dato no se está capturando."""
    lineas = _lineas(proyecto)
    if not lineas:
        return _check("fondos", "MEDIDAS", "Profundidades confirmadas", SIN_DATOS, False)
    sin_fondo = [_ident(l, i) for i, l in enumerate(lineas)
                 if _medida(l.get("depth") or l.get("fondo")) is None]
    if not sin_fondo:
        return _check("fondos", "MEDIDAS", "Profundidades confirmadas", OK)
    if len(sin_fondo) == len(lineas):
        return _check("fondos", "MEDIDAS", "Profundidades confirmadas", SIN_DATOS, False,
                      "Ninguna línea trae fondo: se usará el estándar de fábrica.")
    return _check("fondos", "MEDIDAS", "Profundidades confirmadas", FALTA, True,
                  "Sin fondo: " + ", ".join(sin_fondo[:5]),
                  {"tipo": "linea", "ids": sin_fondo[:5]})


def _sentido_apertura(proyecto):
    """CÓDIGOS MV SIN MANO DECIDIDA.

    En la nomenclatura MV el sufijo `D/I` significa "derecha o izquierda": es
    una referencia de tarifa, no un mueble concreto. Si un código llega a
    fábrica todavía con `D/I`, nadie ha decidido hacia dónde abre la puerta —
    y en el taller la decidirán ellos, con un 50 % de acertar.
    """
    lineas = _lineas(proyecto)
    pendientes = [_ident(l, i) for i, l in enumerate(lineas)
                  if "D/I" in linea_pedido.codigo(l).upper()]
    if not lineas:
        return _check("apertura", "DISEÑO", "Sentidos de apertura definidos", SIN_DATOS, False)
    if not pendientes:
        return _check("apertura", "DISEÑO", "Sentidos de apertura definidos", OK)
    return _check("apertura", "DISEÑO", "Sentidos de apertura definidos", FALTA, True,
                  "Sin mano decidida (siguen como D/I): " + ", ".join(pendientes[:5]),
                  {"tipo": "linea", "ids": pendientes[:5]})


def _acabados(proyecto):
    lineas = _lineas(proyecto)
    if not lineas:
        return _check("acabados", "DISEÑO", "Acabados definidos", SIN_DATOS, False)
    sin = [_ident(l, i) for i, l in enumerate(lineas)
           if not str(l.get("finish") or l.get("material") or "").strip()]
    if not sin:
        return _check("acabados", "DISEÑO", "Acabados definidos", OK)
    if len(sin) == len(lineas):
        return _check("acabados", "DISEÑO", "Acabados definidos", SIN_DATOS, False,
                      "Ninguna línea trae acabado: se tomará el general del proyecto.")
    return _check("acabados", "DISEÑO", "Acabados definidos", FALTA, True,
                  "Sin acabado: " + ", ".join(sin[:5]),
                  {"tipo": "linea", "ids": sin[:5]})


def _codigos_tarifa(proyecto):
    """Líneas sin código de tarifa.

    Una línea sin código no se puede pedir al proveedor tal cual: alguien
    tendrá que buscarle equivalencia a mano. AVISA pero no bloquea, porque las
    líneas manuales (un trabajo a medida, un porte) no llevan código y son
    legítimas.

    NOTA: `itemsMontada` e `itemsDespiece` son los dos juegos de líneas de
    presupuesto (Cocina Montada y Cocina Desmontada), NO una lista de piezas
    cortadas. Que uno de los dos esté vacío es normal según el tipo de
    proyecto, así que no se comprueba "hay despiece": no significaría nada.
    """
    lineas = _lineas(proyecto)
    if not lineas:
        return _check("codigos", "FABRICACIÓN", "Líneas con código de tarifa", SIN_DATOS, False)
    sin = [_ident(l, i) for i, l in enumerate(lineas)
           if not linea_pedido.codigo(l)]
    if not sin:
        return _check("codigos", "FABRICACIÓN", "Líneas con código de tarifa", OK)
    return _check("codigos", "FABRICACIÓN", "Líneas con código de tarifa", FALTA, False,
                  f"{len(sin)} línea(s) sin código: " + ", ".join(sin[:5]),
                  {"tipo": "linea", "ids": sin[:5]})


def _medidas_de_obra(proyecto):
    """Las medidas CRÍTICAS de la obra, confirmadas.

    Es el enganche con `medicion_obra`. Sin esto, el expediente podía decir
    «listo para fabricar» mientras el hueco de la columna seguía siendo el que
    se tecleó el día de la venta, sin que nadie hubiera ido con el metro.

    Una obra SIN medidas apuntadas no se bloquea: hay proyectos que no las
    llevan y bloquearlos por no tener una lista que nadie ha empezado sería
    parar la casa entera. Se dice que no hay, y ya.
    """
    medidas = (proyecto or {}).get("medidas") or []
    if not medidas:
        return _check("medidas_obra", "MEDIDAS", "Medidas de obra confirmadas",
                      NO_APLICA, False, "Esta obra no lleva medidas apuntadas.")

    rev = medicion_obra.revisar(medidas)
    sin_confirmar = rev["bloqueos"]
    if not sin_confirmar:
        # Las diferencias entre lo de la venta y lo de obra se cuentan aunque
        # estén confirmadas: no bloquean —la obra no siempre mide lo que decía
        # el presupuesto— pero explican por qué el mueble no es el que se
        # presupuestó, y eso hay que poder verlo antes de cortar.
        difs = len(rev["discrepancias"])
        detalle = f"{difs} medida(s) no coinciden con las de la venta." if difs else ""
        return _check("medidas_obra", "MEDIDAS", "Medidas de obra confirmadas",
                      OK, False, detalle)

    nombres = ", ".join(m["etiqueta"] for m in sin_confirmar[:5])
    return _check("medidas_obra", "MEDIDAS", "Medidas de obra confirmadas",
                  FALTA, True,
                  f"{len(sin_confirmar)} medida(s) crítica(s) sin confirmar: {nombres}",
                  {"tipo": "medidas", "claves": [m["clave"] for m in sin_confirmar[:5]]})


def _cambios_aprobados(proyecto, pendientes_cambios=0):
    if not pendientes_cambios:
        return _check("cambios", "FABRICACIÓN", "Cambios aprobados", OK)
    return _check("cambios", "FABRICACIÓN", "Cambios aprobados", FALTA, True,
                  f"{pendientes_cambios} cambio(s) sin aprobar tras aceptar el presupuesto.",
                  {"tipo": "cambios"})


# ─── Expediente completo ────────────────────────────────────────────────────

# ─── La valvula de escape, con nombre y apellidos ───────────────────────────

# Lo que hay que rellenar para saltarse un bloqueo. Sin esto no hay excepcion:
# hay un bloqueo que alguien ha quitado.
CAMPOS_EXCEPCION = ("motivo", "autorizadaPor", "riesgo")

ETIQUETA_EXCEPCION = {
    "motivo": "por qué se libera igualmente",
    "autorizadaPor": "quién lo autoriza",
    "riesgo": "qué puede pasar",
}


def excepcion(proyecto):
    """La autorización para fabricar con algo pendiente, si la hay.

    SIEMPRE puede haber una urgencia real: fabricar sin una medida secundaria
    para no perder el hueco de la máquina. Si el sistema no deja esa puerta, la
    puerta se abre igual —por fuera, borrando el aviso o cambiando el dato— y
    entonces no queda ni rastro.

    Lo que NO se admite es una excepción anónima. Hacen falta el motivo, quién
    la autoriza y qué riesgo se asume; con uno solo que falte, no libera y se
    dice cuál falta. Una excepción sin dueño es exactamente cómo las
    excepciones se vuelven invisibles y acaban siendo la norma.

    Y liberar con excepción NO borra los bloqueos: siguen contados y a la
    vista. Se fabrica sabiendo qué falta, que es lo contrario de fabricar como
    si no faltara nada.
    """
    e = (proyecto or {}).get("excepcionFabricacion") or {}
    faltan = [c for c in CAMPOS_EXCEPCION if not str(e.get(c) or "").strip()]
    if len(faltan) == len(CAMPOS_EXCEPCION):
        return None  # no hay excepcion, ni a medias
    return {
        "motivo": str(e.get("motivo") or "").strip(),
        "autorizadaPor": str(e.get("autorizadaPor") or "").strip(),
        "riesgo": str(e.get("riesgo") or "").strip(),
        "datosPendientes": str(e.get("datosPendientes") or "").strip(),
        "fecha": str(e.get("fecha") or "").strip(),
        "faltan": faltan,
        "completa": not faltan,
    }


def validar(proyecto, pendientes_cambios=0):
    """Pasa todas las comprobaciones y dice si se puede liberar a fabricación."""
    checks = [
        _medidas_de_modulos(proyecto),
        _fondos(proyecto),
        _sentido_apertura(proyecto),
        _acabados(proyecto),
        _codigos_tarifa(proyecto),
        _medidas_de_obra(proyecto),
        _cambios_aprobados(proyecto, pendientes_cambios),
    ]

    correctas = sum(1 for c in checks if c["estado"] == OK)
    bloqueos = [c for c in checks if c["bloquea"]]
    # Pendiente = no está bien pero tampoco corta. Se cuenta aparte para que el
    # resumen no dé por bueno lo que solo está "avisado".
    #
    # NO_APLICA no es pendiente NI correcto: no hay nada que mirar. Contarlo
    # como pendiente dejaba un proyecto entero sin poder decir nunca «listo
    # para fabricar» por una comprobación que no venía al caso — y quien lee
    # «1 pendiente» sin encontrar qué falta, deja de leer el resumen.
    pendientes = [c for c in checks
                  if c["estado"] not in (OK, NO_APLICA) and not c["bloquea"]]
    no_aplican = [c for c in checks if c["estado"] == NO_APLICA]

    grupos = {}
    for c in checks:
        grupos.setdefault(c["grupo"], []).append(c)

    # La excepcion autorizada: deja pasar SIN borrar lo que falta.
    exc = excepcion(proyecto)
    con_excepcion = bool(exc and exc["completa"] and bloqueos)

    return {
        "checks": checks,
        "grupos": grupos,
        "excepcion": exc,
        "conExcepcion": con_excepcion,
        "correctas": correctas,
        "noAplican": len(no_aplican),
        "pendientes": len(pendientes),
        "bloqueos": len(bloqueos),
        # Se libera si no hay bloqueos, o si hay una excepcion COMPLETA que los
        # asume. Los bloqueos siguen contados: no desaparecen porque alguien
        # firme, solo dejan de parar la fabrica.
        "puedeLiberar": (not bloqueos) or con_excepcion,
        # Los motivos van con su `donde` para que la pantalla pueda llevar al
        # sitio: un aviso que no lleva a ninguna parte se acaba ignorando.
        "motivos": [{"etiqueta": c["etiqueta"], "detalle": c["detalle"], "donde": c["donde"]}
                    for c in bloqueos],
        "resumen": _resumen(correctas, len(pendientes), len(bloqueos), exc),
    }


def _resumen(correctas, pendientes, bloqueos, exc=None):
    if not bloqueos and not pendientes:
        return f"Listo para fabricar: {correctas} comprobación(es) correctas."
    partes = [f"{correctas} correctas"]
    if pendientes:
        partes.append(f"{pendientes} pendiente(s)")
    if bloqueos:
        partes.append(f"{bloqueos} bloqueo(s)")
    texto = " · ".join(partes)
    if bloqueos and exc and exc["completa"]:
        # Se dice EN EL RESUMEN y con quién detrás. Una excepción que solo se
        # ve entrando en un detalle es una excepción invisible.
        return f"{texto} — LIBERADO CON EXCEPCIÓN, autoriza {exc['autorizadaPor']}"
    if bloqueos and exc:
        que_falta = ", ".join(ETIQUETA_EXCEPCION[c] for c in exc["faltan"])
        return f"{texto} — hay una excepción a medias: falta {que_falta}"
    return texto
