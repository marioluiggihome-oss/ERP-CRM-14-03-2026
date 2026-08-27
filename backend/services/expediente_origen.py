# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
expediente_origen.py — UNA OBRA DE COCINA DESMONTADA, VISTA COMO EXPEDIENTE.

Cálculo puro, sin base de datos.

POR QUÉ HACE FALTA
------------------
El expediente, la validación técnica y las medidas de obra estaban escritos
para un PROYECTO de Cocina Montada. Cocina Desmontada guarda lo suyo en otro
sitio y con otra forma: un pedido de cascos, con `cliente`, `ref`, `lines` y un
número de `expediente` que ya existía para atar la venta con la compra.

El master lo pidió claro: **Desmontada tiene que tener expediente también.**

CÓMO, Y POR QUÉ ASÍ
-------------------
No se convierte un pedido en proyecto —eso sería duplicar la obra en dos
sitios, y al día siguiente uno de los dos estaría desactualizado—. Se
**traduce** al vuelo: este módulo dice cómo se lee un pedido de cascos con las
gafas del expediente, y los motores de siempre hacen el resto sin enterarse de
que vienen de otro sitio.

Así hay UN expediente, UNA validación y UNAS medidas para toda la casa. Si
mañana aparece un tercer origen, se le escribe aquí su traducción y hereda todo
lo que ya funciona.

LA TRADUCCIÓN ES DE NOMBRES, NO DE CONTENIDO
--------------------------------------------
La primera versión de esto marcaba media validación como «no aplica» dando por
hecho que un casco no tiene fondo, ni acabado, ni código. **Era falso**: una
línea de casco trae `ancho`, `alto`, `fondo`, su color y su firma. Lo único que
pasaba es que los llamaba por otros nombres.

Así que aquí no se ablanda ninguna comprobación: se traducen los nombres y las
comprobaciones de siempre se contestan solas, con datos de verdad. Apagar un
control «porque este módulo es distinto» es como se acaba con un semáforo verde
que no mira nada.

LO QUE NO SE INVENTA
--------------------
Si una línea no trae un dato, no se rellena. La comprobación dirá que falta, y
dirá la verdad.
"""

# Qué significa cada tipo de pedido en la vida de la obra. Es la traducción
# honesta de lo único que Desmontada sabe de su propio estado.
ESTADO_DE = {
    "presupuesto": "borrador",   # todavía se está vendiendo
    "pedido": "aceptado",        # el cliente ha dicho que sí
    "compra": "aceptado",        # ya se ha pedido al proveedor
}

def _txt(v):
    return str(v or "").strip()


def es_pedido_de_casco(doc):
    """¿Esto es un pedido de Cocina Desmontada y no un proyecto?

    Se mira por lo que TIENE, no por una etiqueta: un pedido de cascos trae
    `lines` y `kind`. Una etiqueta se puede quedar sin poner al guardar; la
    forma del documento, no.
    """
    d = doc or {}
    return "lines" in d and "itemsMontada" not in d


def traducir_linea(linea):
    """Una línea de casco con los nombres que buscan los motores.

    Es TODA la magia, y es solo un cambio de nombres:

        sig        → referencia   (módulo + acabado: identifica la pieza)
        qty        → quantity
        ancho/alto → width/height
        fondo      → depth
        colorLabel → material     (el acabado de un casco ES su color)

    La firma vale como referencia porque es lo que identifica físicamente la
    pieza: dos cascos con la misma firma son el mismo artículo en la estantería
    y en el pedido al proveedor. Es la misma por la que la pantalla junta dos
    líneas iguales en el carro.
    """
    l = linea or {}
    fuera = dict(l)
    fuera.setdefault("referencia", _txt(l.get("sig")))
    if l.get("qty") is not None:
        fuera.setdefault("quantity", l.get("qty"))
    for origen, destino in (("ancho", "width"), ("alto", "height"), ("fondo", "depth")):
        if l.get(origen) is not None:
            fuera.setdefault(destino, l.get(origen))
    acabado = _txt(l.get("colorLabel")) or _txt(l.get("color"))
    if acabado:
        fuera.setdefault("material", acabado)
    # El nombre legible, para que un aviso diga «Bajo Con Balda 600» y no
    # «línea 3».
    nombre = " ".join(_txt(x) for x in (l.get("tipo"), l.get("ancho"), acabado) if _txt(x))
    if nombre:
        fuera.setdefault("descripcion", nombre)
    return fuera


def desde_pedido_casco(pedido):
    """El pedido de cascos, con la forma que entienden los motores.

    NO copia nada a ninguna parte: es una vista. El pedido sigue siendo el
    dueño de sus datos y se sigue editando donde siempre.
    """
    p = pedido or {}
    kind = _txt(p.get("kind")).lower()

    return {
        "id": _txt(p.get("id")),
        # El número de expediente ya existía en el pedido para atar la venta
        # con la compra. Se usa ese: inventarle otro número a la misma obra es
        # la forma más rápida de que dejen de encontrarse.
        "budgetNumber": _txt(p.get("expediente")) or _txt(p.get("ref")) or _txt(p.get("id")),
        "customerName": _txt(p.get("cliente")),
        "internalReference": _txt(p.get("ref")),
        "status": ESTADO_DE.get(kind, "borrador"),
        # Las líneas van al lado del despiece: son material que se fabrica o se
        # compra, no muebles montados.
        "itemsMontada": [],
        "itemsDespiece": [traducir_linea(l) for l in (p.get("lines") or [])],
        # Lo que el expediente añade sobre el pedido y vive con él.
        "medidas": list(p.get("medidas") or []),
        "cambios": list(p.get("cambios") or []),
        "excepcionFabricacion": p.get("excepcionFabricacion") or {},
        # De dónde ha salido esto, para que la pantalla lo diga y nadie crea
        # que está mirando un proyecto de Cocina Montada.
        "origen": "cocina_desmontada",
        "origenEtiqueta": "Cocina Desmontada",
        "tipoPedido": kind or "presupuesto",
    }
