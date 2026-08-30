# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LOS DOS COBROS DE UN PEDIDO: LA SEÑAL Y EL RESTO.

El master, 30/08: «50% al confirmar pedido, siempre», y el otro 50% antes de
entregar. Sobre cómo se factura: «una factura que pasa de parcial a paid».

O SEA QUE NO HAY DOS FACTURAS. Hay UNA por el total, y lo que cambia es cuánto
se ha cobrado de ella: primero la mitad (`partial`), después el resto (`paid`).
Por eso los hitos no se guardan a mano en el pedido: SE DEDUCEN del importe
cobrado, que es un dato que ya existe y que nadie tiene que acordarse de marcar
dos veces. Un dato que hay que teclear dos veces acaba cuadrado en un sitio y no
en el otro.

EL PORCENTAJE ES FIJO Y ES LA MITAD (master: «siempre»). No se hace configurable
«por si acaso»: un porcentaje que se puede cambiar es un porcentaje que alguien
cambia sin querer, y aquí decide si una cocina entra en el taller.

ESTO NO PAGA NI RETIENE COMISIONES. La comisión se sigue liberando exactamente
igual que antes —servido del todo Y cobrado del todo (`liquidaciones.py`)—, y
este módulo no toca esa regla ni de lejos. Los hitos son para VER por dónde va
el dinero de una obra, no para pagar antes.

Y AVISAN, NO BLOQUEAN. Asignar montador sin señal, o entregar sin haber cobrado
el resto, se MARCAN. No se impiden: en una obra pasan cosas, y un ERP que impide
lo que la realidad ya ha hecho se acaba esquivando por fuera, que es peor que
verlo marcado. Es la misma decisión que con `es_anomalia` en las liquidaciones.
"""
from __future__ import annotations

from typing import Optional

# La mitad, y punto (master, 30/08: «50% al confirmar pedido, siempre»).
PORCENTAJE_SENAL = 0.50

# Medio céntimo, igual que en las liquidaciones: por debajo es redondeo. Sin
# esto, una señal de 4.999,995 € sobre 10.000 € se leería como «sin señal».
TOLERANCIA = 0.005


def _num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


# CÓMO SE LLAMA EL TOTAL EN CADA SECCIÓN DEL ERP. El Presupuestador guarda
# `total`; las secciones viejas `totalAmount` y `totalPvp`. Leyendo solo uno, los
# pedidos de las otras salían sin importe y por tanto sin señal que comprobar —
# el mismo fallo que costó el 28/08 con `qty` y `quantity`.
ALIAS_TOTAL = ("total", "totalAmount", "totalPvp")


def importe_de(pedido: dict) -> float:
    """Lo que vale el pedido. Sin él no hay mitad que calcular."""
    p = pedido or {}
    for clave in ALIAS_TOTAL:
        if p.get(clave) not in (None, ""):
            return _num(p[clave])
    return 0.0


def cobrado_de(pedido: dict) -> float:
    """Cuánto ha entrado ya.

    Sale de `total - pendienteCobro`, que es lo que ya calcula
    `services/enlace_documentos.py` mirando las facturas. No se vuelve a sumar
    aquí: dos sitios sumando lo mismo acaban dando cifras distintas.

    Un pedido dado por cobrado del todo (`cobradoAt`) es el total, aunque nadie
    haya escrito el pendiente: lo que el pedido afirma manda sobre la deducción.
    """
    p = pedido or {}
    total = importe_de(p)
    if p.get("cobradoAt"):
        return total
    if p.get("pendienteCobro") is None:
        # NO SE SABE NO ES CERO (regla 7). Sin dato de pendiente no se puede
        # afirmar que haya entrado nada.
        return 0.0
    return max(0.0, total - _num(p.get("pendienteCobro")))


def senal_de(pedido: dict) -> float:
    """Lo que hay que cobrar al confirmar: la mitad exacta."""
    return round(importe_de(pedido) * PORCENTAJE_SENAL, 2)


def estado_de_cobro(pedido: dict) -> dict:
    """Por dónde va el dinero de un pedido, en los dos hitos.

    `senalCubierta` no significa «se cobró exactamente la mitad»: significa que
    ha entrado AL MENOS la mitad. Si el cliente adelanta más, la señal está
    cubierta de sobra y no hay nada que avisar.

    Con un pedido sin importe todo sale a cero y `sinImporte` en `True`: no se
    inventa una señal del 50% de un total que no consta.
    """
    p = pedido or {}
    total = importe_de(p)
    cobrado = cobrado_de(p)
    senal = senal_de(p)
    return {
        "total": round(total, 2),
        "cobrado": round(cobrado, 2),
        "pendiente": round(max(0.0, total - cobrado), 2),
        "senal": senal,
        "senalCubierta": bool(total > 0 and cobrado + TOLERANCIA >= senal),
        "cobradoDelTodo": bool(total > 0 and cobrado + TOLERANCIA >= total),
        # Sin importe no hay hitos que comprobar, y decirlo evita que un pedido
        # sin total se lea como «sin cobrar nada» cuando es «no se sabe».
        "sinImporte": not (total > 0),
    }


def avisos_de(pedido: dict, servido: bool = False,
              montador: Optional[str] = None) -> list:
    """Lo que no cuadra con el orden que pidió el master. AVISOS, no bloqueos.

    Dos, y los dos son de dinero:

      · Montador asignado sin la señal dentro. El master lo quiere después del
        primer pago: «asignarlo a montador una vez se confirma el primer pago».
      · Servido sin haber cobrado el total. «Todos los pedidos antes de salir
        del almacén tienen que estar cobrados» es la norma de la casa, y ya se
        marcaba en las liquidaciones; aquí se ve antes de que sea tarde.

    Un pedido sin importe no genera avisos: no se acusa a nadie con un dato que
    no consta.
    """
    e = estado_de_cobro(pedido)
    if e["sinImporte"]:
        return []
    fuera = []
    if montador and not e["senalCubierta"]:
        fuera.append({
            "clave": "montador_sin_senal",
            "texto": f"Montador asignado y la señal ({e['senal']:.2f} €) "
                     "todavía no ha entrado.",
        })
    if servido and not e["cobradoDelTodo"]:
        fuera.append({
            "clave": "servido_sin_cobrar",
            "texto": f"Servido con {e['pendiente']:.2f} € pendientes de cobro.",
        })
    return fuera
