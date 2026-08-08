# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
expediente.py — EL EXPEDIENTE ÚNICO DEL PROYECTO.

Todo lo de una obra en un sitio, para no saltar entre diez módulos para saber
qué está pasando. Pensado para una tablet de 8" usada de pie en obra.

Cálculo puro, sin base de datos, para poder probarlo.

LO IMPORTANTE DE VERDAD: EL DINERO NO VIAJA SI NO SE PUEDE VER
--------------------------------------------------------------
El candado de Rentabilidad OCULTA los importes en pantalla (regla 9), y los
descuentos no salen en nada que vea un cliente (regla 5). Pero ocultar en el
navegador no es proteger: si el importe viaja en la respuesta, se ve abriendo
el inspector, y en una tienda asociada eso es enseñar el margen a alguien que
no debería verlo.

Aquí los campos de dinero **no se ponen a cero ni se enmascaran: no se
incluyen**. Un cero es un dato falso; un campo ausente es la verdad —esa
persona no tiene por qué recibirlo—. Por eso las pruebas comprueban que la
clave NO ESTÁ, no que valga 0.

QUIÉN RESUELVE QUÉ
------------------
Cada cosa pendiente lleva responsable, para que cada uno vea lo suyo en vez de
una lista genérica que no es de nadie y por eso no la mira ninguno.
"""

# Flags que dan acceso a importes. Los mismos que usa `require_admin`, para que
# no haya dos definiciones de "mando" que puedan separarse con el tiempo.
FLAGS_CON_IMPORTES = (
    "isAdmin",
    "isResponsableDelegacion",
    "isGerente",
    "isDirectorComercial",
    "isDirectorFabrica",
)

# La línea de proceso de la obra, en orden.
ETAPAS = ("VENTA", "DISEÑO", "MEDICIÓN", "VALIDACIÓN", "FABRICACIÓN", "MONTAJE", "CIERRE")

# Quién resuelve cada cosa. Sale de la comprobación que falló.
RESPONSABLE = {
    "medidas_modulos": "Diseñador",
    "fondos": "Diseñador",
    "apertura": "Diseñador",
    "acabados": "Comercial",
    "codigos": "Comercial",
    # Las medidas de obra las toma y las confirma quien va con el metro. No es
    # el diseñador desde la oficina: por eso tiene responsable propio y no cae
    # en «Sin asignar», que es como se queda una tarea sin dueño.
    "medidas_obra": "Montador",
    "cambios": "Gerencia",
}

# Los totales del proyecto. `descuentoAplicado` es el nombre real del campo en
# el proyecto (`models/schemas.py`); `descuento` se mantiene porque hay líneas
# y documentos antiguos que lo traen así, y quitar de más aquí no rompe nada.
CAMPOS_DE_DINERO = ("totalPvp", "totalCoste", "margen", "totalConIVA",
                    "descuento", "descuentoAplicado")

# Lo que lleva de dinero UNA LÍNEA de presupuesto, que no son los mismos
# nombres que los totales del proyecto: una línea trae `unitPrice`/`totalPrice`.
# Con solo los nombres de los totales, `limpiar_lineas` no quitaba nada de una
# línea y el precio viajaba entero.
#
# Los PUNTOS también se van: punto × coeficiente = precio. Dejarlos es dejar el
# precio puesto en otra unidad, y quien no puede ver importes tampoco tiene que
# poder deducirlos.
CAMPOS_DE_DINERO_LINEA = CAMPOS_DE_DINERO + (
    "unitPrice", "totalPrice", "price", "precio", "pvp",
    "cost", "coste", "importe", "subtotal", "total",
    "unitPoints", "totalPoints", "puntos",
)


def puede_ver_importes(usuario):
    """¿Este usuario puede recibir importes?

    Nota: es una decisión de QUÉ SE ENVÍA, no de qué se pinta. Si devuelve
    False, los importes no salen del servidor.
    """
    return bool(usuario and any(usuario.get(f) for f in FLAGS_CON_IMPORTES))


def _sin_dinero(d, campos=CAMPOS_DE_DINERO_LINEA):
    """Copia sin los campos de importe. No los pone a 0: los QUITA."""
    return {k: v for k, v in (d or {}).items() if k not in campos}


def acciones_pendientes(validacion, cambios_sin_aprobar=None):
    """Lo que hay que resolver AHORA, con responsable y a dónde ir.

    No es una lista de tareas: sale de comprobaciones que han fallado de
    verdad, así que no hay nada que inventar ni que mantener a mano.
    """
    acciones = []
    for c in (validacion or {}).get("checks", []):
        # «Correcto» no da tarea, y «no aplica» tampoco: no hay nada que
        # resolver. Una tarea que dice «esta obra no lleva medidas apuntadas»
        # es ruido, y el ruido es lo que hace que se deje de leer la lista.
        if c.get("estado") in ("ok", "no_aplica"):
            continue
        acciones.append({
            "clave": c.get("clave"),
            "titulo": c.get("etiqueta"),
            "detalle": c.get("detalle") or "",
            "responsable": RESPONSABLE.get(c.get("clave"), "Sin asignar"),
            "bloquea": bool(c.get("bloquea")),
            "donde": c.get("donde"),
            "accion": "Resolver",
        })

    for i, cam in enumerate(cambios_sin_aprobar or []):
        acciones.append({
            "clave": f"cambio-{i}",
            "titulo": "Cambio pendiente de aprobar",
            "detalle": (cam.get("motivo") or "").strip()
                       or f"Cambio del {str(cam.get('fecha', ''))[:10]} sin aprobar.",
            "responsable": "Gerencia",
            "bloquea": True,
            "donde": {"tipo": "cambios", "indice": i},
            "accion": "Revisar",
        })

    # Lo que bloquea, primero: es lo que impide avanzar.
    acciones.sort(key=lambda a: (not a["bloquea"], a["titulo"]))
    return acciones


def etapa_actual(proyecto, validacion):
    """En qué punto del proceso está la obra.

    Se deduce del estado y de si la validación pasa; no es un campo que alguien
    mueva a mano, porque entonces diría lo que alguien quiso y no lo que hay.
    """
    estado = str((proyecto or {}).get("status") or "").lower()
    if estado in ("borrador", ""):
        return "VENTA"
    if estado == "rechazado":
        return "CIERRE"
    if estado == "entregado":
        return "MONTAJE"
    if estado == "aceptado":
        return "VALIDACIÓN" if not (validacion or {}).get("puedeLiberar") else "FABRICACIÓN"
    return "DISEÑO"


def montar(proyecto, validacion=None, cambios_pendientes=None, usuario=None):
    """Arma el expediente completo, filtrado por lo que este usuario puede ver."""
    p = proyecto or {}
    con_importes = puede_ver_importes(usuario)

    cabecera = {
        "cliente": p.get("customerName") or p.get("clientCode") or "Sin cliente",
        "proyecto": p.get("budgetNumber") or p.get("id") or "",
        # El campo del proyecto se llama `internalReference`; `reference` se
        # mira primero por si viene de otro sitio. Sin el segundo, la
        # referencia de la obra salía SIEMPRE vacía en la cabecera y nadie
        # sabía por qué.
        "referencia": p.get("reference") or p.get("internalReference") or "",
        "estado": p.get("status") or "borrador",
    }

    acciones = acciones_pendientes(validacion, cambios_pendientes)
    bloqueos = sum(1 for a in acciones if a["bloquea"])

    exp = {
        "cabecera": cabecera,
        "etapas": list(ETAPAS),
        "etapaActual": etapa_actual(p, validacion),
        "acciones": acciones,
        "bloqueos": bloqueos,
        "puedeLiberar": bool((validacion or {}).get("puedeLiberar")),
        "lineas": len((p.get("itemsMontada") or [])) + len((p.get("itemsDespiece") or [])),
        "verImportes": con_importes,
    }

    if con_importes:
        exp["importes"] = {c: p.get(c) for c in CAMPOS_DE_DINERO if c in p}
    # Si no puede verlos, la clave `importes` NO existe. No va a 0 ni a null:
    # no se manda. Un 0 sería un dato falso y encima creíble.

    return exp


def limpiar_lineas(lineas, usuario):
    """Quita los importes de cada línea si el usuario no puede verlos."""
    if puede_ver_importes(usuario):
        return list(lineas or [])
    return [_sin_dinero(l) for l in (lineas or [])]
