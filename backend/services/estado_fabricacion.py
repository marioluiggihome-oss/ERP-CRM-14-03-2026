# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
POR DÓNDE VA CADA PEDIDO EN FÁBRICA.

El master, 30/08: una pestaña en COOP con «los pedidos y el estado de los
mismos en fábrica, vamos los procesos de producción y su estado».

DE DÓNDE SALE EL ESTADO, que es lo que no se puede inventar. La fábrica lleva su
propia colección, `fabrica_orders`, atada al pedido por `budgetNumber`, con un
`status` y un `progress`. Eso ya existía y ya lo traducía `routes/orders.py`
para «Mis Pedidos» — con la tabla escrita ahí dentro, a mano.

AQUÍ ESTÁ ESA TABLA, Y SOLO AQUÍ. Copiarla habría sido la cuarta vez en este
proyecto que una regla vive en dos sitios y se separan: la de `es_master` vivía
en cuatro ficheros, la del origen de los pedidos en dos, la de los tramos de
comisión en la pantalla y en el cálculo. Cuando se separan, una pantalla dice
«En producción» y la otra «Confirmado» del mismo pedido, y nadie sabe cuál
mentir.

LO QUE NO SE INVENTA: un pedido del que la fábrica no sabe nada NO está
«pendiente» ni «en producción» — está `confirmed`, que es lo que significa: se
vendió y todavía no ha entrado en el taller. Poner otra cosa sería adivinar.
"""
from __future__ import annotations

from typing import Optional

from services import comisiones as C
from services import hitos_cobro as HC
from services import liquidaciones as L
from services import origen_pedidos as OP

# EL `status` DEL TALLER → el estado que se enseña.
#
# ESTA TABLA ESTABA ESCRITA PARA UN ESQUEMA QUE NO EXISTE (30/08, auditando).
# El taller de verdad —`routes/fabrica.py`, el Portal Fábrica— escribe
# `draft · confirmed · in_production · ready · delivered · cancelled`. Aquí solo
# se reconocían `in_progress`, `completed` y `shipped`, que NO son valores que
# escriba nadie: son los nombres de SALIDA de esta misma tabla. O sea que una
# orden real en producción no encajaba en ninguna clave y caía en el valor por
# defecto: «Confirmado». Un pedido en el taller que en pantalla pone
# «Confirmado» no parece un fallo, parece un pedido parado.
#
# Se aceptan LAS DOS FAMILIAS: las que escribe el Portal Fábrica y las que
# esperaba la tabla vieja, por si algún documento antiguo las trae. Reconocer de
# más aquí no cuesta nada; reconocer de menos deja el pedido mudo.
DE_FABRICA = {
    "draft": "pending",
    "confirmed": "confirmed",
    # Lo que escribe el Portal Fábrica hoy
    "in_production": "in_production",
    "ready": "ready",
    "cancelled": "cancelled",
    # Nombres que esperaba la tabla vieja
    "in_progress": "in_production",
    "completed": "ready",
    "shipped": "shipped",
    "delivered": "delivered",
}

# LAS COLECCIONES DEL TALLER, en orden de preferencia.
#
# `manufacturing_orders` es donde escribe el Portal Fábrica de verdad.
# `fabrica_orders` es la que leían todas las pantallas… y no la escribía NADIE:
# se buscó quién hacía un `insert` o un `update` sobre ella en todo el backend y
# no había ni uno. Los índices se creaban al arrancar y la tabla se quedaba
# vacía, así que en COOP todos los pedidos salían «Confirmado» para siempre.
#
# Se leen las dos, y manda la primera que tenga ficha de ese pedido: si hay
# datos viejos en `fabrica_orders` no se pierden, y los nuevos se ven.
COLECCIONES_DEL_TALLER = ("manufacturing_orders", "fabrica_orders")

# Cuando la fábrica no tiene ficha de ese pedido. No es un error ni un hueco:
# es un pedido vendido que aún no ha entrado en el taller.
SIN_FICHA_EN_FABRICA = "confirmed"

# Los estados, EN ORDEN de proceso, con lo que se lee en pantalla. El orden es
# el del taller y se usa para ordenar la lista: lo que está más atrás primero,
# que es lo que hay que empujar.
ESTADOS = (
    ("pending", "Pendiente"),
    ("confirmed", "Confirmado"),
    ("in_production", "En producción"),
    ("ready", "Listo para envío"),
    ("shipped", "Enviado"),
    ("delivered", "Entregado"),
    # ANULADA VA LA ÚLTIMA y no es una etapa del proceso: es su final. Va aquí
    # para que se pueda DECIR — sin ella, una orden anulada caía en «Confirmado»
    # y el pedido salía como si estuviera esperando al taller. Y al ir la última
    # no se cuela entre lo que hay que empujar al ordenar por lo más atrasado.
    ("cancelled", "Anulada"),
)

ORDEN = {clave: i for i, (clave, _) in enumerate(ESTADOS)}
NOMBRES = dict(ESTADOS)


def estado_de(ficha_de_fabrica: Optional[dict]) -> str:
    """El estado de fabricación a partir de la ficha de `fabrica_orders`."""
    if not ficha_de_fabrica:
        return SIN_FICHA_EN_FABRICA
    return DE_FABRICA.get(ficha_de_fabrica.get("status"), SIN_FICHA_EN_FABRICA)


def progreso_de(ficha_de_fabrica: Optional[dict]) -> int:
    """El porcentaje, acotado. Un progreso corrupto es 0, no una barra rara."""
    try:
        v = int(float((ficha_de_fabrica or {}).get("progress") or 0))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, v))


# Lo único que sale de un pedido hacia la pestaña de producción. Lista BLANCA,
# como en todo este módulo: aquí se mira POR DÓNDE VA una cocina, no lo que
# vale. El dinero de estos pedidos ya tiene su sitio —Rentabilidad— y no viaja
# por rutas nuevas.
CAMPOS_DE_LA_LINEA = (
    "pedidoId", "referencia", "cliente", "origen", "fecha",
    "estado", "estadoNombre", "progreso", "servido", "cobrado",
    # LOS DOS HITOS DE COBRO (master, 30/08: «50% al confirmar pedido,
    # siempre»). Sale si la señal ha entrado y si queda algo pendiente, más los
    # avisos de lo que no cuadra. Ojo: `senal` y `pendiente` SÍ son euros, y van
    # a propósito — sin la cifra, «falta la señal» no dice cuánto hay que
    # reclamar y la pantalla obliga a ir a buscarlo a Rentabilidad, que es justo
    # lo que el montador no puede abrir. Esta pestaña ya es SOLO del master.
    "senal", "senalCubierta", "pendiente", "cobradoDelTodo", "avisos",
)


def linea(pedido: dict, ficha_de_fabrica: Optional[dict] = None) -> dict:
    """Una fila de la pestaña de producción."""
    p = pedido or {}
    clave = estado_de(ficha_de_fabrica)
    return {
        "pedidoId": p.get("id") or "",
        "referencia": (p.get("budgetNumber") or p.get("projectReference")
                       or p.get("ref") or ""),
        "cliente": (p.get("customerName") or p.get("cliente") or "").strip(),
        "origen": p.get("origenNombre") or p.get("origen") or "",
        "fecha": p.get("confirmedAt") or p.get("createdAt") or "",
        "estado": clave,
        "estadoNombre": NOMBRES.get(clave, clave),
        "progreso": progreso_de(ficha_de_fabrica),
        # El final del proceso, que ya sabe el ERP por el albarán y la factura
        # (`services/enlace_documentos.py`). Sin esto la pestaña se queda a
        # medias: «Entregado» en fábrica no quiere decir cobrado.
        "servido": bool(L.servido_de(p)),
        "cobrado": bool(L.cobrado_de(p)),
        **_hitos(p),
    }


def _hitos(p: dict) -> dict:
    """La señal y el resto, y lo que no cuadra con el orden que pidió el master.

    Los avisos NO bloquean nada: en una obra pasan cosas, y un ERP que impide lo
    que la realidad ya ha hecho se acaba esquivando por fuera. Se marcan, que es
    lo que permite arreglarlo.
    """
    e = HC.estado_de_cobro(p)
    return {
        "senal": e["senal"],
        "senalCubierta": e["senalCubierta"],
        "pendiente": e["pendiente"],
        "cobradoDelTodo": e["cobradoDelTodo"],
        "avisos": HC.avisos_de(
            p,
            servido=bool(L.servido_de(p)),
            montador=(p.get("montadorUserId") or None)),
    }


def lineas(pedidos, fichas_por_referencia: Optional[dict] = None) -> list:
    """Todas las filas, lo más atrasado primero: es lo que hay que empujar."""
    fichas = fichas_por_referencia or {}
    fuera = []
    for p in (pedidos or []):
        ref = ((p or {}).get("budgetNumber") or (p or {}).get("ref") or "")
        fuera.append(linea(p, fichas.get(str(ref).strip())))
    fuera.sort(key=lambda l: (ORDEN.get(l["estado"], 99), str(l["fecha"] or "")))
    return fuera


def resumen(filas) -> dict:
    """Cuántos hay en cada estado, en orden de proceso."""
    cuenta = {clave: 0 for clave, _ in ESTADOS}
    for f in (filas or []):
        if f.get("estado") in cuenta:
            cuenta[f["estado"]] += 1
    return {"total": len(filas or []),
            "porEstado": [{"estado": c, "nombre": n, "pedidos": cuenta[c]}
                          for c, n in ESTADOS]}


# ─── QUÉ LLEVA UN PEDIDO ────────────────────────────────────────────────────
#
# El master, 30/08: «que podamos entrar en los pedidos, si no no sabemos lo que
# hay en cada uno de ellos». La lista dice POR DÓNDE VA; esto dice QUÉ ES.
#
# SIN IMPORTES, igual que la lista. Para saber qué cocina hay que fabricar hacen
# falta los códigos y las unidades, no los euros: para eso está Rentabilidad,
# con su puerta. Lista BLANCA otra vez, porque dentro de una línea de pedido
# viajan `price`, `pvp` y los descuentos.
CAMPOS_DE_LA_LINEA_DEL_PEDIDO = ("codigo", "descripcion", "unidades", "familia",
                                 "medidas", "acabado", "esMueble")


def _medidas_de(d: dict) -> str:
    """`ancho × alto × fondo` de una línea, con lo que traiga y nada más.

    NO SE INVENTA NINGUNA COTA (regla 7): lo que no está no se rellena, y si no
    hay ni una medida se devuelve cadena vacía en vez de un «0 × 0 × 0» que
    parece un dato. Se admiten los nombres de las dos pantallas: Montada guarda
    las medidas DEFINITIVAS (`anchoReal`/`altoReal`) y Desmontada el ancho, alto
    y fondo del casco.
    """
    partes = []
    for claves in (("ancho", "anchoReal"), ("alto", "altoReal"), ("fondo", "fondoReal")):
        v = None
        for k in claves:
            if (d or {}).get(k) not in (None, ""):
                v = d[k]
                break
        partes.append(str(v) if v is not None else None)
    while partes and partes[-1] is None:
        partes.pop()
    if not partes or all(p is None for p in partes):
        return ""
    return " × ".join(p if p is not None else "?" for p in partes)


def linea_de_pedido(l: dict, familias: Optional[dict] = None) -> dict:
    """Una línea del pedido, con lo justo para saber qué es.

    LAS UNIDADES Y LA FAMILIA NO SE LEEN AQUÍ A MANO. Se las pide a
    `services/comisiones.py`, que es donde ya está escrito qué nombre usa cada
    pantalla del ERP (`qty`, `cant`, `quantity`, `unidades`) y qué es la familia
    de una línea. Escribirlo otra vez es exactamente el fallo del 28/08: las
    pruebas leían `qty`/`familia` y los pedidos de verdad guardan
    `quantity`/`code`, así que COOP enseñaba «0 muebles» en todos los pedidos.
    Si un día cambia el nombre, cambia en un sitio.
    """
    d = dict(l or {})
    if familias:
        d.setdefault("_familiaResuelta",
                     C.familia_de(d)
                     or familias.get(str(d.get("code") or "").strip().upper(), ""))
    # UN CASCO NO TIENE CÓDIGO MV, Y ESO NO ES UN HUECO. Cocina Desmontada
    # guarda `{tipo, ancho, alto, fondo, color, qty}` — sin `code` ni `name`—,
    # porque un casco se identifica por lo que ES y lo que MIDE. Leyendo solo
    # los nombres de Montada, un pedido entero de Desmontada salía como una
    # tabla de guiones: las líneas estaban, pero no se veía ni una.
    return {
        "codigo": str(d.get("code") or d.get("cod") or "").strip(),
        "descripcion": str(d.get("name") or d.get("desc") or d.get("etiqueta")
                           or d.get("tipo") or "").strip(),
        # Lo que se fabrica. Sale de la línea; nunca se estima.
        "medidas": _medidas_de(d),
        "acabado": str(d.get("colorLabel") or d.get("color") or "").strip(),
        "unidades": C.unidades_de(d),
        "familia": C.familia_de(d),
        # POR QUÉ SE MARCA. El panel del cooperativista enseña «14 muebles» en un
        # pedido de 20 líneas, y quien lo mira tiene que poder ver cuáles son las
        # otras seis o pensará que le están quitando. Es la MISMA función que
        # decide la comisión, no una copia: si se separaran, esta pantalla
        # explicaría una cosa y la nómina pagaría otra.
        "esMueble": C.es_mueble(d),
    }


def contenido_de(pedido: dict, familias: Optional[dict] = None) -> dict:
    """Lo que lleva un pedido: sus líneas y cuántos muebles suman.

    `muebles` cuenta con el mismo criterio que la comisión (solo muebles: ni
    puertas, ni costados, ni líneas manuales de servicios), y `unidades` cuenta
    todo lo que hay que fabricar y montar. Son dos números distintos a
    propósito, y por eso salen los dos: el de fábrica y el de la nómina.

    UN PEDIDO SIN LÍNEAS NO LLEVA «0 MUEBLES»: es que no se sabe lo que lleva
    (`sinDesglose`), y eso se rotula «?». Un 0 parece un dato (regla 7).
    """
    p = pedido or {}
    crudas = p.get("items") or p.get("lines") or p.get("lineas") or []
    lineas = [linea_de_pedido(l, familias) for l in crudas]

    # «NO SE SABE» NO ES «CERO», Y EL CRITERIO NO SE ESCRIBE AQUÍ.
    #
    # Si NINGUNA línea se ha podido clasificar, este pedido no lleva «0
    # muebles»: es que no se sabe lo que lleva, y eso se rotula «?» (regla 7).
    # Un 0 parece un dato y hace pensar que la comisión es cero de verdad.
    #
    # Se lo pregunta a `comisiones`, que es quien lo decide para la nómina. La
    # primera versión de esto usaba su propio criterio —«sin desglose» solo si
    # no había NI UNA línea— y con un pedido de Cocina Desmontada, cuyas líneas
    # no traen familia, la pantalla decía «0 muebles» mientras la liquidación
    # decía «no consta». El mismo pedido, dos respuestas, y ninguna parecía un
    # error.
    # LOS CASCOS NO COMISIONAN, y eso NO es «falta un dato» (master, 30/08).
    # Un pedido de Cocina Desmontada sale con cero muebles a propósito: solo
    # sirve para separar cascos cuando el cliente se lleva la cocina desmontada.
    # Rotularlo «?» mandaría a buscar un fallo que no existe, y un aviso que
    # sale siempre acaba sin leerse — que es como se pierden los que sí importan.
    solo_cascos = bool(crudas) and OP.es_solo_cascos(p)
    b = C.base_de_comision([dict(l, familia=l["familia"]) for l in lineas])
    sin_desglose = (not solo_cascos) and (
        (not lineas) or (b["sinClasificar"] >= b["lineas"] > 0))
    return {
        "pedidoId": p.get("id") or "",
        "referencia": (p.get("budgetNumber") or p.get("ref") or ""),
        "cliente": (p.get("customerName") or p.get("cliente") or "").strip(),
        "origen": p.get("origenNombre") or p.get("origen") or "",
        "lineas": lineas,
        "unidades": sum(l["unidades"] for l in lineas),
        "muebles": sum(l["unidades"] for l in lineas if l["esMueble"]),
        "sinDesglose": sin_desglose,
        "soloCascos": solo_cascos,
    }
