# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LOS DOS COBROS DE UN PEDIDO: LA SEÑAL Y EL RESTO.

El master, 30/08: «50% al confirmar pedido, siempre», el otro 50% antes de
entregar, y sobre cómo se factura: «una factura que pasa de parcial a paid».

LO QUE VIGILA ESTE CANDADO:

  1. QUE LA MITAD SEA LA MITAD. El porcentaje es fijo porque el master dijo
     «siempre». No se hace configurable: un porcentaje que se puede cambiar es
     un porcentaje que alguien cambia sin querer, y aquí decide si una cocina
     entra en el taller.

  2. QUE NO SE INVENTE UN COBRO. Sin dato de pendiente no ha entrado nada, y sin
     importe no hay señal que comprobar — no se acusa a nadie con un dato que no
     consta (regla 7).

  3. QUE ESTO NO TOQUE LA COMISIÓN. Se sigue liberando con servido del todo Y
     cobrado del todo. Los hitos son para VER por dónde va el dinero, no para
     pagar antes. Si un día la comisión empezara a mirar la señal, alguien
     cobraría con media obra por entregar.

  4. QUE AVISE Y NO BLOQUEE. En una obra pasan cosas; un ERP que impide lo que
     la realidad ya ha hecho se acaba esquivando por fuera, que es peor que
     verlo marcado.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import estado_fabricacion as EF     # noqa: E402
from services import hitos_cobro as HC            # noqa: E402
from services import liquidaciones as L           # noqa: E402


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# ── 1. La mitad es la mitad ─────────────────────────────────────────────────

def test_LA_SENAL_ES_SIEMPRE_EL_50_POR_CIENTO():
    assert HC.PORCENTAJE_SENAL == 0.50, (
        "el master dijo «50% al confirmar pedido, SIEMPRE»")
    assert HC.senal_de({"total": 10000.0}) == 5000.0
    assert HC.senal_de({"total": 9922.35}) == 4961.18


def test_LA_SENAL_SE_CUBRE_CON_AL_MENOS_LA_MITAD():
    """«Cubierta» no es «se cobró exactamente la mitad»: es al menos la mitad.

    Si el cliente adelanta de más, la señal está cubierta de sobra y no hay nada
    que reclamar — avisar ahí sería un aviso falso.
    """
    assert HC.estado_de_cobro({"total": 10000.0, "pendienteCobro": 5000.0})["senalCubierta"]
    assert HC.estado_de_cobro({"total": 10000.0, "pendienteCobro": 2000.0})["senalCubierta"]
    assert not HC.estado_de_cobro({"total": 10000.0, "pendienteCobro": 5000.01})["senalCubierta"]


def test_MEDIO_CENTIMO_ES_REDONDEO_Y_NO_DEUDA():
    """Sin tolerancia, una señal de 4.999,999 € sobre 10.000 € se leería como
    «sin señal» y se reclamaría un cobro que ya está hecho."""
    e = HC.estado_de_cobro({"total": 10000.0, "pendienteCobro": 5000.004})
    assert e["senalCubierta"]


def test_EL_TOTAL_SE_LEE_COMO_LO_GUARDA_CADA_SECCION():
    """El Presupuestador guarda `total`; las secciones viejas `totalAmount`.

    Leyendo solo uno, los pedidos de las otras salían sin importe y por tanto
    sin señal que comprobar — el mismo fallo que costó el 28/08 con `qty`.
    """
    for clave in HC.ALIAS_TOTAL:
        assert HC.estado_de_cobro({clave: 10000.0, "pendienteCobro": 0})["cobradoDelTodo"], (
            f"un pedido que guarda el total en «{clave}» sale sin importe")


# ── 2. No se inventa un cobro ───────────────────────────────────────────────

def test_SIN_DATO_DE_PENDIENTE_NO_HA_ENTRADO_NADA():
    """No se sabe no es «cobrado» (regla 7). Dar por buena una señal que nadie
    ha confirmado mandaría una cocina al taller sin un euro dentro."""
    e = HC.estado_de_cobro({"total": 10000.0})
    assert e["cobrado"] == 0.0 and not e["senalCubierta"]


def test_SIN_IMPORTE_NO_HAY_SENAL_QUE_COMPROBAR():
    e = HC.estado_de_cobro({"pendienteCobro": 0})
    assert e["sinImporte"] and e["senal"] == 0.0
    assert not e["senalCubierta"] and not e["cobradoDelTodo"]
    assert HC.avisos_de({"pendienteCobro": 0}, servido=True, montador="m1") == [], (
        "se está avisando de un pedido cuyo importe no consta: no se acusa a "
        "nadie con un dato que no se tiene")


def test_LO_QUE_EL_PEDIDO_AFIRMA_MANDA():
    """Un pedido dado por cobrado del todo lo está, aunque nadie escribiera el
    pendiente: es la misma regla que con servido y cobrado."""
    e = HC.estado_de_cobro({"total": 10000.0, "cobradoAt": "2026-08-21"})
    assert e["cobradoDelTodo"] and e["senalCubierta"] and e["pendiente"] == 0.0


# ── 3. La comisión NO cambia ────────────────────────────────────────────────

def test_LOS_HITOS_NO_TOCAN_LA_COMISION():
    """Con la señal dentro y el resto pendiente, la comisión sigue SIN liberarse.

    Es lo más importante de este candado. Si un día la liberación empezara a
    mirar la señal, se pagaría una comisión con media obra por entregar y por
    cobrar — y eso no se recupera.
    """
    n = {"aceptadoAt": "2026-08-01", "servidoAt": "2026-08-20",
         "cobradoAt": None, "pendienteCobro": 5000.0,
         "muebles": 10, "baseImponible": 10000.0, "total": 10000.0}
    assert L.estado_de(n, L.COMERCIAL) == L.EN_PROGRESO, (
        "la comisión se está liberando con el pedido a medio cobrar")
    # Y con todo cobrado, sí.
    n2 = dict(n, cobradoAt="2026-08-21", pendienteCobro=0)
    assert L.estado_de(n2, L.COMERCIAL) == L.CONSOLIDADA


def test_LIQUIDACIONES_NO_SABE_NADA_DE_LOS_HITOS():
    """Los módulos de nómina no pueden depender de esto ni de rebote."""
    cuerpo = _lee(os.path.join(BACKEND, "services", "liquidaciones.py"))
    assert "hitos_cobro" not in cuerpo, (
        "`liquidaciones` ha empezado a mirar los hitos: la comisión dejaría de "
        "depender solo de servido y cobrado del todo")
    com = _lee(os.path.join(BACKEND, "services", "comisiones.py"))
    assert "hitos_cobro" not in com, "`comisiones` ha empezado a mirar los hitos"


# ── 4. Avisa, no bloquea ────────────────────────────────────────────────────

def test_MONTADOR_SIN_SENAL_SE_AVISA():
    """El master lo quiere después del primer pago: «asignarlo a montador una
    vez se confirma el primer pago»."""
    p = {"total": 10000.0, "pendienteCobro": 10000.0}
    claves = [a["clave"] for a in HC.avisos_de(p, montador="m1")]
    assert "montador_sin_senal" in claves
    # Con la señal dentro, ni un aviso.
    assert HC.avisos_de({"total": 10000.0, "pendienteCobro": 5000.0}, montador="m1") == []
    # Y sin montador asignado no se avisa de nada: aún no toca.
    assert HC.avisos_de(p, montador=None) == []


def test_SERVIDO_SIN_COBRAR_DEL_TODO_SE_AVISA():
    p = {"total": 10000.0, "pendienteCobro": 5000.0}
    claves = [a["clave"] for a in HC.avisos_de(p, servido=True)]
    assert "servido_sin_cobrar" in claves
    assert HC.avisos_de(dict(p, pendienteCobro=0), servido=True) == []


def test_NADA_DE_ESTO_BLOQUEA():
    """Se marca y se sigue. Un ERP que impide lo que la realidad ya ha hecho se
    acaba esquivando por fuera, y entonces no se ve nada."""
    cuerpo = _lee(os.path.join(BACKEND, "services", "hitos_cobro.py"))
    for prohibido in ("HTTPException", "raise ", "status_code"):
        assert prohibido not in cuerpo, (
            f"«{prohibido}» en los hitos: esto avisa, no corta")


# ── 5. Llega a la pantalla ──────────────────────────────────────────────────

def test_LOS_HITOS_LLEGAN_A_LA_LINEA_DE_PRODUCCION():
    l = EF.linea({"id": "p", "total": 10000.0, "pendienteCobro": 10000.0,
                  "montadorUserId": "m1"}, None)
    assert set(l) <= set(EF.CAMPOS_DE_LA_LINEA), (
        f"campos de más: {set(l) - set(EF.CAMPOS_DE_LA_LINEA)}")
    assert l["senal"] == 5000.0 and l["senalCubierta"] is False
    assert any(a["clave"] == "montador_sin_senal" for a in l["avisos"])


def test_LA_FACTURA_PARCIAL_YA_PUEDE_DECIR_CUANTO():
    """`partial` era un estado sin importe: se podía decir «cobrada a medias» y
    no había dónde apuntar cuánto — así que un pedido con la mitad dentro era
    indistinguible de uno sin cobrar un euro."""
    cuerpo = _lee(os.path.join(BACKEND, "routes", "invoices.py"))
    i = cuerpo.index("async def change_invoice_status")
    trozo = cuerpo[i:cuerpo.index("@router", i)]
    assert '"cobrado"' in trozo, (
        "una factura parcial sigue sin poder decir cuánto se ha cobrado")
    assert "mayor que el total" in trozo, (
        "se puede cobrar más que el total de la factura")
    assert 'update["cobrado"] = float(inv.get("total")' in trozo, (
        "al pasar a pagada no se da por cobrado el total")


def test_LA_PANTALLA_ENSEÑA_LOS_DOS_HITOS():
    jsx = _lee(os.path.join(RAIZ, "frontend", "src", "components", "CoopProduccion.jsx"))
    assert "senalCubierta" in jsx, "la pantalla no dice si la señal ha entrado"
    assert "p.avisos" in jsx, "los avisos no se pintan"
    assert "Falta la señal" in jsx and "p.senal" in jsx, (
        "no se dice CUÁNTO falta: obligaría a ir a buscarlo a Rentabilidad")
