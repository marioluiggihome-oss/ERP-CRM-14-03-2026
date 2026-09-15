# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA WEB ANUNCIABA UN PRECIO Y STRIPE COBRABA OTRO.

El master, 15/09/2026: «cuadra los packs de la web con los del ERP», y al
elegir, que mande la web.

Había TRES listas de packs de renders y ninguna decía lo mismo:

  · `services/stripe_pagos.py`  20/15 € · 50/35 € · 100/60 €   ← la que COBRA
  · `routes/admin.py`           20/15 € · 50/35 € · 100/60 €   ← el panel
  · `CarpinterosLanding.jsx`    10/15 € · 30/39 € · 100/99 €   ← la que LEE el cliente

Así que el cliente leía «100 renders, 99 €» y Stripe le cobraba 60. En el
escalón pequeño leía 10 renders y recibía 20. Siempre a favor del cliente y
nunca de la casa — y sin dar ningún error, que es lo de siempre: no se cae
nada, solo se factura mal.

LO QUE ESTE CANDADO VIGILA:

1. QUE LAS TRES DIGAN LO MISMO. La del panel ya no es una copia (importa la de
   Stripe), pero la de la web es JavaScript en otro fichero y no se puede
   importar: se EJECUTA en node y se compara pack a pack. Una copia que no se
   compara se separa — es lo que acaba de pasar.

2. QUE UN PAGO EN VUELO CON UN ID RETIRADO SIGA ABONANDO. Es lo que de verdad
   podía costar dinero el día del despliegue: quien pagó `pack20` cinco minutos
   antes recibe el webhook DESPUÉS. Sin los retirados, `renders` sale 0 y el
   cliente ha PAGADO SIN RECIBIR NADA, sin error y sin que nadie lo relacione
   con el cambio de precios.

3. QUE UN PACK RETIRADO NO VUELVA AL ESCAPARATE. Resolverlo para abonar es una
   cosa; ofrecerlo para vender es otra.

4. QUE LOS RENDERS SALGAN DEL SERVIDOR Y NO DE LOS METADATOS DE STRIPE. Los
   metadatos viajan con el cliente; si de ahí saliera la cantidad, bastaría
   manipular la sesión para regalarse mil renders.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import stripe_pagos as SP  # noqa: E402

LANDING = os.path.join(RAIZ, "frontend", "src", "components", "CarpinterosLanding.jsx")


def _packs_de_la_web():
    """Los packs publicados, EJECUTANDO el JS de la landing."""
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    with open(LANDING, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    m = re.search(r"const RENDER_PACKS = (\[.*?\]);", cuerpo, re.S)
    assert m, "la landing ya no declara `RENDER_PACKS` como se esperaba"
    guion = "console.log(JSON.stringify(%s));" % m.group(1)
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_LA_WEB_Y_LO_QUE_SE_COBRA_DICEN_LO_MISMO():
    """El caso del master, medido: anunciar 99 € y cobrar 60 no puede volver."""
    web = {(int(p["renders"]), float(p["price"])) for p in _packs_de_la_web()}
    servidor = {(int(p["renders"]), float(p["price"])) for p in SP.RENDER_PACKS.values()}
    assert web == servidor, (
        "la web anuncia %s y el servidor cobra %s: el cliente lee un precio y "
        "paga otro, y no salta ningún error"
        % (sorted(web), sorted(servidor)))


def test_EL_PANEL_DEL_MASTER_NO_VUELVE_A_TENER_SU_PROPIA_LISTA():
    """Tres copias fue lo que causó esto. El panel le pregunta a quien cobra.

    SE MIRA EL FICHERO, NO EL OBJETO IMPORTADO. La primera versión comparaba
    `admin.RENDER_PACKS is SP.RENDER_PACKS`, y eso PASABA EN SOLITARIO Y FALLABA
    EN LA SUITE: `test_calculo_recarga_renders.py` mete un `services` falso en
    `sys.modules` y lo deja ahí para el resto de la sesión, así que la identidad
    del objeto depende de qué fichero se haya ejecutado antes. Un candado que
    cambia de resultado según el orden no protege nada (regla 25).

    Leyendo el fichero se comprueba lo que de verdad importa: que el panel NO
    declare su propia lista y que se la pida a quien cobra.
    """
    ruta = os.path.join(RAIZ, "backend", "routes", "admin.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    # Sin comentarios: este fichero EXPLICA el arreglo citando la lista vieja,
    # y un candado que se cree su propia nota no protege nada (reglas 24, 34).
    limpio = "\n".join(l for l in cuerpo.split("\n") if not l.strip().startswith("#"))
    assert "RENDER_PACKS" in limpio, "el recorte de comentarios se comió el código"
    assert re.search(r"from services\.stripe_pagos import [^\n]*RENDER_PACKS", limpio), (
        "`routes/admin.py` ya no le pide los packs a quien cobra")
    assert not re.search(r"^RENDER_PACKS\s*=\s*\{", limpio, re.M), (
        "`routes/admin.py` ha vuelto a declarar sus propios packs: conceder un "
        "pack desde el panel dejaría de coincidir con lo que se ha cobrado")


def test_UN_PAGO_EN_VUELO_CON_UN_ID_RETIRADO_SIGUE_ABONANDO():
    """Lo que podía costar dinero el día del despliegue.

    Quien pagó `pack20` antes del cambio recibe el webhook después. Tiene que
    cobrar los 20 QUE COMPRÓ, no los 10 del pack que ocupa hoy ese escalón, y
    desde luego no 0.
    """
    for viejo, esperados in (("pack20", 20), ("pack50", 50)):
        evento = {
            "type": "checkout.session.completed",
            "data": {"object": {
                "id": "cs_test_1", "payment_status": "paid", "amount_total": 1815,
                "metadata": {"pack_id": viejo, "user_id": "u1"},
            }},
        }
        datos = SP.datos_de_pago(evento)
        assert datos["renders"] == esperados, (
            "un pago de '%s' abona %s renders en vez de %s: el cliente ha "
            "pagado y no recibe lo que compró, sin ningún error"
            % (viejo, datos["renders"], esperados))


def test_UN_PACK_RETIRADO_NO_SE_PUEDE_COMPRAR():
    """Resolverlo para abonar no es ofrecerlo para vender."""
    for viejo in ("pack20", "pack50"):
        assert viejo not in SP.RENDER_PACKS, (
            "'%s' ha vuelto al escaparate: se venderían dos packs distintos "
            "para el mismo escalón" % viejo)
        assert SP.pack_por_id(viejo), (
            "'%s' ha dejado de resolverse: un pago en vuelo se quedaría sin "
            "abonar" % viejo)


def test_LOS_IDS_DICEN_CUANTOS_RENDERS_LLEVAN():
    """`pack20` valiendo 10 renders es una trampa para el siguiente que lo lea."""
    for clave, pack in SP.RENDER_PACKS.items():
        m = re.fullmatch(r"pack(\d+)", clave)
        assert m, "id de pack con una forma inesperada: %s" % clave
        assert int(m.group(1)) == int(pack["renders"]), (
            "el pack '%s' lleva %s renders: el id miente"
            % (clave, pack["renders"]))


def test_LOS_RENDERS_SALEN_DEL_SERVIDOR_Y_NO_DE_LOS_METADATOS():
    """Los metadatos viajan con el cliente: si mandaran ellos, bastaría
    manipular la sesión de pago para regalarse mil renders."""
    evento = {
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_2", "payment_status": "paid", "amount_total": 1815,
            "metadata": {"pack_id": "pack10", "user_id": "u1", "renders": "1000"},
        }},
    }
    assert SP.datos_de_pago(evento)["renders"] == 10, (
        "la cantidad de renders se está leyendo de los metadatos de Stripe")


def test_UN_PAGO_SIN_COBRAR_NO_ABONA_NADA():
    """La otra mitad de lo mismo: solo se abona con el cobro confirmado."""
    evento = {
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_3", "payment_status": "unpaid", "amount_total": 0,
            "metadata": {"pack_id": "pack100", "user_id": "u1"},
        }},
    }
    assert SP.datos_de_pago(evento) == {}


def test_EL_PRECIO_POR_RENDER_BAJA_AL_SUBIR_DE_PACK():
    """Un pack mayor tiene que salir más barato por render, o no es un pack.

    Si se invirtiera, el cliente que compra el grande paga más por unidad que
    el que compra el pequeño — y eso no da ningún error, solo indigna a quien
    lo descubre.
    """
    escala = sorted(((int(p["renders"]), float(p["price"])) for p in SP.RENDER_PACKS.values()))
    unitarios = [precio / renders for renders, precio in escala]
    assert unitarios == sorted(unitarios, reverse=True), (
        "el precio por render no baja al crecer el pack: %s"
        % [(r, round(p / r, 3)) for r, p in escala])
