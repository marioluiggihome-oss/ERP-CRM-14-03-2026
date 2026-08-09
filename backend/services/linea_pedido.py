# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
linea_pedido.py — CÓMO SE LEE UNA LÍNEA, VENGA DE DONDE VENGA.

Cálculo puro, sin base de datos.

EL PROBLEMA QUE RESUELVE
------------------------
En esta casa una línea de material puede venir de tres sitios, y cada uno la
escribe con otros nombres:

    Cocina Montada 1 y 2 →  code / productCode  ·  quantity / qty
    Cocina Desmontada    →  cod                 ·  cantidad
    Despiece y armarios  →  referencia          ·  cantidad

Son la misma cosa: un código y unas unidades. Pero el almacén y la validación
técnica solo miraban `code` y `productCode`, así que **una proforma de Cocina
Desmontada entera era invisible para ellos**: el plan de compra decía «ninguna
línea trae referencia» y la validación daba por bueno un proyecto sin mirarle
un solo código.

Y no daba ningún error. Simplemente no encontraba nada.

POR QUÉ AQUÍ Y NO EN CADA SITIO
-------------------------------
Porque ya estaba escrito en cuatro sitios con cuatro listas distintas, y esa
es exactamente la forma de que un módulo nuevo se quede fuera sin que nadie se
entere. Cuando aparezca un cuarto origen, se añade su nombre AQUÍ y lo ven
todos a la vez.

LO QUE NO HACE
--------------
No adivina. Si una línea no trae código, devuelve cadena vacía; no se inventa
uno con la descripción ni le pone «MANUAL». Una línea sin código es una línea
que alguien tiene que mirar, y el que la lea decidirá qué hacer con ella.
"""

# Los nombres con los que puede venir el CÓDIGO, en orden de preferencia. El
# orden importa: `referencia` es el más explícito y `cod` el más corto, y una
# línea puede traer los dos si ha pasado por dos módulos.
NOMBRES_CODIGO = ("referencia", "code", "productCode", "cod", "codigo", "ref")

# Los nombres de las UNIDADES.
NOMBRES_CANTIDAD = ("cantidad", "quantity", "qty", "uds", "unidades")

# Y los de la DESCRIPCIÓN, para poder nombrar la línea en un aviso.
NOMBRES_DESCRIPCION = ("descripcion", "description", "name", "productName",
                       "nombre", "label")


def _txt(v):
    return str(v or "").strip()


def _num(v):
    """Número, o None si no consta. Cadena vacía NO es cero."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def codigo(linea):
    """El código de la línea, se llame como se llame. Vacío si no trae.

    No se rellena con nada: una línea sin código es una línea sin código, y
    ponerle uno inventado la haría pasar por buena en el plan de compra.
    """
    l = linea or {}
    for nombre in NOMBRES_CODIGO:
        v = _txt(l.get(nombre))
        if v:
            return v
    return ""


def cantidad(linea, por_defecto=1.0):
    """Las unidades de la línea.

    Sin cantidad se cuenta UNA, que es lo que significa una línea suelta en un
    pedido. Un cero la haría desaparecer del plan de compra sin decir nada.
    """
    l = linea or {}
    for nombre in NOMBRES_CANTIDAD:
        v = _num(l.get(nombre))
        if v is not None:
            return v
    return por_defecto


def descripcion(linea):
    """El texto de la línea, para poder nombrarla en un aviso."""
    l = linea or {}
    for nombre in NOMBRES_DESCRIPCION:
        v = _txt(l.get(nombre))
        if v:
            return v
    return ""


def identificar(linea, indice=0):
    """Cómo se nombra esta línea en un aviso, para poder ir a ella.

    Primero el código, luego la descripción y, si no hay nada, su número. Un
    aviso que dice «una línea» obliga a repasar el pedido entero, y eso no se
    hace: se ignora.
    """
    return codigo(linea) or descripcion(linea) or f"línea {indice + 1}"


def normalizar(lineas, quitar=None):
    """Deja una lista de líneas en el formato que entienden los motores.

    `quitar`: índices que NO entran (líneas borradas o desmarcadas en pantalla).
    Se filtran por POSICIÓN porque así es como las guarda la proforma, y
    hacerlo aquí evita que cada pantalla se invente su propia forma de
    descartar líneas.
    """
    fuera = set(int(i) for i in (quitar or []) if str(i).lstrip("-").isdigit())
    salida = []
    for i, l in enumerate(lineas or []):
        if i in fuera:
            continue
        cod = codigo(l)
        salida.append({
            "referencia": cod,
            "cantidad": cantidad(l),
            "descripcion": descripcion(l),
            # El índice original viaja para poder volver a la línea de la
            # pantalla de donde salió.
            "indice": i,
        })
    return salida


def sin_codigo(lineas):
    """Las líneas que no traen código, con su nombre para poder buscarlas.

    Se devuelven APARTE en vez de descartarlas en silencio: en un plan de
    compra son justo las que hay que mirar a mano.
    """
    return [identificar(l, i) for i, l in enumerate(lineas or []) if not codigo(l)]
