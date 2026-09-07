# -*- coding: utf-8 -*-
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""LA PUBLIOFERTA DE ELECTROSTOCK: EL CATÁLOGO ES DE TODOS, LA CESIÓN NO.

El master, 07/09/2026: «vuelca estas ofertas a la sección electros y mete una
línea en presupuestador de cocina montada... un artículo para que metiendo el
modelo meta el precio, descripción y precio».

LA CESIÓN ES COSTE, Y ADEMÁS COSTE INCOMPLETO. La columna «€ CESIÓN» del papel
es lo que Electrostock le cobra a la casa, sin IVA y SIN PORTES («Portes de
envío a consultar»). Vender por esa cifra es vender a coste, y enseñarla es
enseñar lo que le cuesta a la casa cada aparato.

Se parte igual que la tarifa MV (CLAUDE.md, regla 8b): **el corte va en el
PRECIO, no en el CÓDIGO**.

    catalogo()          modelo, descripción, marca, epígrafe  →  TODOS
    catalogo(cesion=True)  + la cesión                        →  solo el master

Sin la mitad abierta, el presupuestador se quedaría MUERTO —sin un aparato que
buscar—, que es exactamente el error que se cometió con el MV el 28/08 y hubo
que deshacer.

EL PVP NO ESTÁ EN ESTE PAPEL Y AQUÍ NO SE INVENTA. Lo que sale de aquí es
coste; el precio de venta lo pone el master al volcar el catálogo a Electros, y
queda escrito de dónde salió. Un PVP inventado por el ERP es un margen que
nadie ha decidido (CLAUDE.md, regla 7).

Y CADUCA. «Precios válidos para el mes de Tarifa o fin de existencias»: es la
oferta de septiembre de 2026. Presupuestar en diciembre con estos precios no da
ningún error — da un pedido que se sirve más caro de lo vendido. Por eso
`vigencia_de()` existe y la pantalla lo enseña; NO se bloquea nada, porque
puede quedar género de la oferta anterior y un ERP que impide lo que la
realidad ya ha hecho se acaba esquivando por fuera (misma decisión que en los
hitos de cobro, regla 30).
"""
import json
import os
import re
from typing import Dict, List, Optional

_RUTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "electrostock_publioferta.json")

# La familia con la que viaja un electrodoméstico en una línea de pedido.
# NO es una familia del catálogo MV: es un aparato que se compra hecho y se
# revende. Está escrita aquí, en un solo sitio, porque de ella depende que un
# aparato NO cuente como mueble para la comisión (`services/comisiones.py`).
FAMILIA = "ELECTRODOMESTICO"

_cache: Optional[dict] = None


def _doc() -> dict:
    """El papel entero. Se lee una vez; si falta el fichero no se revienta el
    ERP: se devuelve un catálogo vacío y quien pregunte verá que no hay nada."""
    global _cache
    if _cache is None:
        try:
            with open(_RUTA, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:                                # noqa: BLE001
            _cache = {"articulos": []}
    return _cache


def normalizar(modelo: str) -> str:
    """La clave de búsqueda de un modelo TECLEADO.

    En el papel conviven «TD 3002 BK», «EFT-1711 WH» y «3EB715LR». Quien lo
    teclea no va a poner los espacios y los guiones donde los puso el
    proveedor, así que se comparan sin ellos y en mayúsculas. Sin esto,
    escribir «TD3002BK» no encuentra nada y el usuario da por hecho que el
    aparato no está.
    """
    return re.sub(r"[^A-Z0-9]", "", (modelo or "").upper())


def cabecera() -> dict:
    d = _doc()
    return {k: d.get(k) for k in
            ("proveedor", "tarifa", "fecha", "vigencia", "ivaIncluido",
             "transporteIncluido", "pie")}


def _sin_cesion(a: dict) -> dict:
    """El artículo SIN lo que le cuesta a la casa.

    Se QUITA la clave, no se pone a cero: un 0,00 € es una afirmación —«esto no
    cuesta nada»— y además cuadraría márgenes solo. Misma decisión que en el
    expediente de obra (regla 28).
    """
    return {k: v for k, v in a.items() if k != "cesion"}


def catalogo(cesion: bool = False, q: str = "") -> List[dict]:
    """El catálogo. `cesion=True` SOLO para quien puede ver el dinero.

    El filtro `q` busca por modelo, descripción y marca; se normaliza el modelo
    para que «td3002bk» encuentre «TD 3002 BK».
    """
    arts = _doc().get("articulos", [])
    texto = (q or "").strip()
    if texto:
        clave = normalizar(texto)
        suelto = texto.lower()
        arts = [a for a in arts
                if (clave and clave in a.get("modeloNorm", ""))
                or suelto in a.get("descripcion", "").lower()
                or suelto in a.get("marca", "").lower()]
    return [a if cesion else _sin_cesion(a) for a in arts]


def por_modelo(modelo: str, cesion: bool = False) -> Optional[dict]:
    """El artículo que se corresponde EXACTAMENTE con ese modelo, o `None`.

    Exacto a propósito: esto es lo que rellena una línea de presupuesto sola.
    Si con un modelo a medias devolviera «el que más se parece», el
    presupuesto saldría con otro aparato y otro precio sin que nadie hubiera
    elegido nada.
    """
    clave = normalizar(modelo)
    if not clave:
        return None
    for a in _doc().get("articulos", []):
        if a.get("modeloNorm") == clave:
            return a if cesion else _sin_cesion(a)
    return None


def pvp_desde_cesion(cesion: float, margen_pct: float) -> float:
    """El precio de venta que sale de aplicarle un margen a la cesión.

    El margen NO se decide aquí: llega de fuera porque lo pone el master. Esta
    función solo garantiza que la cuenta se hace en un solo sitio y que un
    margen absurdo no pasa: por debajo de 0 se vendería por debajo de coste sin
    que nadie lo hubiera pedido.
    """
    try:
        base = float(cesion or 0)
    except (TypeError, ValueError):
        base = 0.0
    try:
        pct = float(margen_pct)
    except (TypeError, ValueError):
        pct = 0.0
    if base <= 0 or pct < 0:
        return 0.0
    return round(base * (1 + pct / 100.0), 2)


def vigencia_de(hoy: str = "") -> Dict[str, object]:
    """¿Sigue en pie esta oferta?

    Devuelve el mes de la tarifa y si el de hoy es posterior. No decide nada:
    AVISA. Puede quedar género del mes anterior, y bloquear un presupuesto por
    una fecha obligaría a esquivar el ERP por fuera.
    """
    mes = str(_doc().get("vigencia") or "")
    hoy = (hoy or "").strip()
    if not hoy:
        from datetime import datetime, timezone
        hoy = datetime.now(timezone.utc).strftime("%Y-%m")
    return {"vigencia": mes, "hoy": hoy[:7],
            "caducada": bool(mes) and hoy[:7] > mes,
            "pie": _doc().get("pie", "")}
