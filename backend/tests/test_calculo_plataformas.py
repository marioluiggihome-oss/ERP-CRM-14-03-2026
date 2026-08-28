# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
TRES PLATAFORMAS EN EL MISMO ERP, Y SOLO UNA REPARTE COMISIONES.

El master, 25/08/2026: «la red de carpinter.io y la red de Studio3K son solo
para vender suscripciones... no tienen nada que ver con el negocio de los
cooperativistas, son plataformas independientes aunque las tengamos metidas en
la misma gestión del ERP de momento».

QUÉ VIGILA ESTE CANDADO. Las tres plataformas comparten la colección de
usuarios, y ahí está el peligro: la palabra «comercial» significa cosas
distintas en cada negocio. Basta un clic en la pantalla de permisos —marcar
«comercial» a un suscriptor de carpinter.io— para que empiece a salir en la
liquidación cobrando comisiones de la cooperativa. No hace falta mala fe.

Se comprueban las dos mitades, porque romper cualquiera de ellas cuesta dinero:

  · que un suscriptor NO cobre aunque esté marcado con el rol, y
  · que un cooperativista de siempre SÍ siga cobrando aunque nadie le haya
    puesto todavía el campo `plataforma`.

La segunda es la que se rompe sola: si el defecto dejara de ser «cooperativa»,
el día del despliegue los cooperativistas de verdad se quedarían sin su área
sin que nadie hubiera tocado un solo usuario.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import area_cooperativista as AC          # noqa: E402
from services import plataformas as P                    # noqa: E402

COOPERATIVISTA = {"id": "u-coop", "esCooperativistaComercial": True}
MONTADOR_COOP = {"id": "u-mon", "esCooperativistaMontador": True,
                 "plataforma": "cooperativa"}
SUSCRIPTOR_CARPINTER = {"id": "u-car", "esCooperativistaComercial": True,
                        "plataforma": "carpinter"}
SUSCRIPTOR_STUDIO3K = {"id": "u-s3k", "esCooperativistaMontador": True,
                       "plataforma": "studio3k"}

# El comercial y el montador DE TODA LA VIDA de la casa. Tienen el rol genérico
# del ERP y NO son socios: no cobran ni un euro de comisión.
COMERCIAL_DE_LA_CASA = {"id": "u-com", "isComercial": True, "isRepresentative": True}
MONTADOR_DE_LA_CASA = {"id": "u-mnt", "isMontador": True}

# Un pedido aceptado, con sus líneas y con las dos manos puestas: el mismo
# pedido le llega al cooperativista y al suscriptor, para que la única
# diferencia entre los dos casos sea la plataforma.
PEDIDO = {
    "id": "PED-1", "confirmedAt": "2026-08-01",
    "comercialUserId": "u-car", "montadorUserId": "u-mon",
    "items": [{"familia": "BAJO", "qty": 10, "pvp": 1300.0}],
    "servidoAt": None, "cobradoAt": None, "pendienteCobro": 0,
}


def test_el_DEFECTO_es_la_cooperativa():
    """Un usuario sin el campo es del negocio de siempre.

    Es el caso de TODOS los usuarios que existen hoy: el campo se añade el
    27/08 y ninguno lo trae. Si el defecto fuera «carpinter» o `None`, los
    cooperativistas de verdad perderían su área el día del despliegue sin que
    nadie hubiera cambiado un solo usuario, y el error se vería en la nómina de
    fin de mes, no en el CI.
    """
    assert P.plataforma_de({}) == P.COOPERATIVA
    assert P.plataforma_de(None) == P.COOPERATIVA
    assert P.es_de_la_cooperativa(COOPERATIVISTA)
    assert AC.rol_de(COOPERATIVISTA) == AC.COMERCIAL
    assert AC.filtro_de(COOPERATIVISTA) == {"comercialUserId": "u-coop"}


def test_una_plataforma_QUE_NO_EXISTE_no_manda_al_usuario_a_un_limbo():
    """Un valor mal escrito se trata como cooperativa, no como «ninguna».

    Es mejor que un usuario mal etiquetado siga en el negocio de siempre —donde
    alguien lo verá y lo corregirá— que mandarlo a una plataforma que no existe
    y que no aparece en ninguna lista. Y de paso: si un día alguien pudiera
    quitarse el candado escribiendo cualquier cosa en el campo, no sería un
    candado.
    """
    for basura in ("", "  ", "COOPERATIVA_X", "carpinteria", None, 7, [],
                   "cooperativa; drop"):
        u = {"id": "u", "esCooperativistaComercial": True, "plataforma": basura}
        assert P.plataforma_de(u) == P.COOPERATIVA, f"con «{basura}»"
        assert AC.rol_de(u) == AC.COMERCIAL, f"con «{basura}»"


def test_el_nombre_de_la_plataforma_NO_distingue_mayusculas():
    """«Carpinter» y «carpinter» son la misma plataforma.

    El valor lo teclea o lo elige una persona en la pantalla de permisos. Si
    «Carpinter» cayera en el defecto, un suscriptor pasaría a cobrar comisiones
    por una mayúscula.
    """
    for escrito in ("Carpinter", "CARPINTER", " carpinter ", "Studio3K", "STUDIO3K"):
        u = {"id": "u", "esCooperativistaComercial": True,
             "esCooperativistaMontador": True, "plataforma": escrito}
        assert not P.es_de_la_cooperativa(u), f"«{escrito}» ha caído en la cooperativa"
        assert AC.rol_de(u) is None, f"«{escrito}» cobra comisión"


def test_un_SUSCRIPTOR_marcado_comercial_NO_es_cooperativista():
    """La mitad que cuesta dinero: el suscriptor no entra en la nómina.

    Está marcado `isComercial` —el mismo clic que hace cooperativista a
    cualquiera— y es de carpinter.io. No cobra.
    """
    assert not P.puede_tener_comision(SUSCRIPTOR_CARPINTER)
    # También se comprueba `es_cooperativista` A SOLAS, y no solo a través de
    # `rol_de`: `rol_de` mira la plataforma por su cuenta, así que esa
    # redundancia tapaba el fallo. Se vio rompiéndolo — quitar el corte de
    # plataforma de dentro de `es_cooperativista_*` dejaba las 30 pruebas en
    # verde. Una comprobación de más no es un candado de más.
    assert not P.es_cooperativista(SUSCRIPTOR_CARPINTER)
    assert not P.es_cooperativista_comercial(SUSCRIPTOR_CARPINTER)
    assert AC.rol_de(SUSCRIPTOR_CARPINTER) is None
    assert AC.filtro_de(SUSCRIPTOR_CARPINTER) is None


def test_un_SUSCRIPTOR_marcado_montador_tampoco():
    assert not P.es_cooperativista(SUSCRIPTOR_STUDIO3K)
    assert not P.es_cooperativista_montador(SUSCRIPTOR_STUDIO3K)
    assert AC.rol_de(SUSCRIPTOR_STUDIO3K) is None
    assert AC.filtro_de(SUSCRIPTOR_STUDIO3K) is None


def test_el_filtro_de_un_suscriptor_es_None_y_NUNCA_un_diccionario_vacio():
    """`None` no es «sin filtro»: `{}` en Mongo son TODOS los pedidos.

    Es el mismo error que ya se vigila en `area_cooperativista` para el usuario
    sin rol, y aquí vuelve a hacer falta porque el corte por plataforma es un
    camino NUEVO hasta el mismo `return`. Un `{}` aquí le enseñaría a un
    suscriptor de carpinter.io los pedidos, los clientes y los importes de toda
    la casa.
    """
    for u in (SUSCRIPTOR_CARPINTER, SUSCRIPTOR_STUDIO3K):
        f = AC.filtro_de(u)
        assert f is None, f"el filtro de un suscriptor es {f!r}"
        assert f != {}


def test_el_PANEL_de_un_suscriptor_viene_vacio_aunque_le_pasen_pedidos():
    """No basta con el filtro: el panel es la otra puerta.

    Se le pasan a propósito pedidos suyos ya encontrados —como si el filtro
    hubiera fallado o alguien llamara al servicio a mano— y aun así no puede
    salir un euro.
    """
    for u in (SUSCRIPTOR_CARPINTER, SUSCRIPTOR_STUDIO3K):
        panel = AC.panel_de(u, [PEDIDO], 12.0)
        assert panel is None, f"al suscriptor le sale un panel: {panel!r}"
        # `None` y no un panel a cero, por la misma razón que en
        # `area_cooperativista`: un panel vacío invita a preguntarse por qué
        # está vacío, y deja la estructura del dinero a la vista.
        volcado = repr(panel)
        assert "13000" not in volcado and "1300" not in volcado, (
            f"al suscriptor le llegan importes de la cooperativa: {volcado[:200]}")


def test_la_COOPERATIVA_sigue_cobrando_con_todo_esto_puesto():
    """La otra mitad: que el candado no se haya llevado por delante el negocio.

    Un candado que cierra de más no da error: da una nómina a cero que nadie
    reclama hasta fin de mes.
    """
    assert AC.rol_de(MONTADOR_COOP) == AC.MONTADOR
    assert AC.filtro_de(MONTADOR_COOP) == {"montadorUserId": "u-mon"}
    panel = AC.panel_de(MONTADOR_COOP, [PEDIDO], 12.0)
    assert panel is not None and panel["rol"] == AC.MONTADOR, panel
    assert panel["enProgreso"]["euros"] > 0, (
        "el montador de la cooperativa se ha quedado a cero: el corte por "
        "plataforma se ha llevado por delante a quien sí cobra")


def test_las_TRES_estan_y_solo_UNA_tiene_cooperativistas():
    assert set(P.TODAS) == {P.COOPERATIVA, P.CARPINTER, P.STUDIO3K}
    assert set(P.SOLO_SUSCRIPCIONES) == {P.CARPINTER, P.STUDIO3K}
    assert P.COOPERATIVA not in P.SOLO_SUSCRIPCIONES, (
        "la cooperativa ha entrado en las plataformas de suscripción: eso deja "
        "sin comisión a TODOS los cooperativistas de golpe")
    for k in P.TODAS:
        assert P.NOMBRES.get(k), f"la plataforma «{k}» no tiene nombre en pantalla"
    # Cada plataforma nueva tiene que decidir a conciencia si reparte nómina.
    for k in P.TODAS:
        u = {"id": "u", "esCooperativistaComercial": True, "plataforma": k}
        assert P.puede_tener_comision(u) == (k == P.COOPERATIVA), (
            f"«{k}» reparte comisiones sin que nadie lo haya decidido")


def test_el_COMERCIAL_DE_LA_CASA_no_cobra_comision():
    """La corrección del master del 27/08, y el euro que costaba.

    «No todos son de la cooperativa. Comercial cooperativista sí, montador
    cooperativista también. Los demás son independientes. El rol de comisiones
    solamente es para estos dos.»

    La primera versión deducía el socio del rol genérico del ERP, y ahí está el
    dinero: `isRepresentative` es el comercial de toda la vida de la casa —hay
    comerciales sembrados con ese flag en `scripts/seed_comerciales.py`— e
    `isMontador` es el de la agenda de montajes. Con aquello, TODOS ellos
    entraban en la liquidación cobrando comisión de cooperativista sin que nadie
    lo hubiera decidido, y el primero que lo habría notado es quien la cobrara.
    """
    for u, quien in ((COMERCIAL_DE_LA_CASA, "el comercial de la casa"),
                     (MONTADOR_DE_LA_CASA, "el montador de la casa")):
        assert not P.es_cooperativista(u), f"{quien} figura como socio"
        assert AC.rol_de(u) is None, f"{quien} entra en la nómina"
        assert AC.filtro_de(u) is None, f"{quien} tiene área"
        assert AC.panel_de(u, [PEDIDO], 12.0) is None, f"{quien} ve un panel"


def test_SER_SOCIO_SE_MARCA_y_no_se_deduce_de_ningun_otro_campo():
    """Ningún rol del ERP, por sí solo, convierte a nadie en socio.

    Se prueban de uno en uno todos los sombreros que reparte la pantalla de
    permisos. Si mañana alguien vuelve a colar aquí un `or user.get(...)`, esto
    se pone rojo con el nombre del campo que lo ha hecho.
    """
    for campo in ("isAdmin", "isMaster", "isPrimaryAdmin", "isGerente",
                  "isDirectorComercial", "isDirectorFabrica", "isRepresentative",
                  "isComercial", "isMontador", "isPrescriptor", "isTienda",
                  "isFabrica", "isResponsableDelegacion", "isController",
                  "canAccessMontajes", "canAccessRentabilidad"):
        u = {"id": "u", "plataforma": "cooperativa", campo: True}
        assert AC.rol_de(u) is None, (
            f"«{campo}» convierte a alguien en cooperativista él solo. El rol de "
            "comisiones es SOLO de las dos marcas de socio (master, 27/08).")


def test_las_DOS_MARCAS_pagan_distinto_y_el_montador_manda_si_lleva_las_dos():
    """Son dos marcas y no una casilla «es cooperativista» porque el rol decide
    CÓMO se paga: el comercial por tramos según la valoración, el montador la
    mano de obra por mueble. No es la misma nómina.

    Si lleva las dos, se devuelve MONTADOR, que es el más restrictivo en
    importes: su comisión no depende de la valoración del pedido y por tanto no
    deja deducir nada del PVP.
    """
    solo_com = {"id": "u", "esCooperativistaComercial": True}
    solo_mon = {"id": "u", "esCooperativistaMontador": True}
    las_dos = {"id": "u", "esCooperativistaComercial": True,
               "esCooperativistaMontador": True}
    assert AC.rol_de(solo_com) == AC.COMERCIAL
    assert AC.rol_de(solo_mon) == AC.MONTADOR
    assert AC.rol_de(las_dos) == AC.MONTADOR, (
        "quien lleva las dos marcas tiene que entrar como montador: es el rol "
        "que no deja deducir el PVP del pedido")


def test_la_pantalla_decide_igual_que_el_servidor(tmp_path):
    """El menú y el servidor tienen que estar de acuerdo, usuario a usuario.

    `frontend/src/plataformas.js` es una copia en pantalla de la regla, porque
    el menú tiene que decidir si enseña «Mi área» sin llamar a nadie. Copia que
    no se compara se separa: el suscriptor vería un botón que le da 403, o —lo
    que de verdad importa— el cooperativista dejaría de ver el suyo y nadie se
    enteraría hasta que preguntara.

    No se reescribe aquí la regla: se EJECUTA la del JSX en node.
    """
    import json
    import shutil
    import subprocess

    import pytest

    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")

    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "plataformas.js")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()

    casos = [
        {"id": "a", "esCooperativistaComercial": True},                  # sin plataforma
        {"id": "b", "esCooperativistaComercial": True, "plataforma": "cooperativa"},
        {"id": "c", "esCooperativistaMontador": True, "plataforma": "cooperativa"},
        {"id": "d", "esCooperativistaComercial": True,
         "esCooperativistaMontador": True},                              # las dos cosas
        {"id": "e", "esCooperativistaComercial": True, "plataforma": "carpinter"},
        {"id": "f", "esCooperativistaMontador": True, "plataforma": "studio3k"},
        {"id": "g", "esCooperativistaComercial": True, "plataforma": "CARPINTER"},
        {"id": "h", "esCooperativistaComercial": True, "plataforma": " carpinter "},
        {"id": "i", "esCooperativistaComercial": True, "plataforma": "loquesea"},
        # Los roles genéricos del ERP, que NO son socios.
        {"id": "j", "isComercial": True, "isRepresentative": True},
        {"id": "k", "isMontador": True, "plataforma": "cooperativa"},
        {"id": "l", "isAdmin": True},
        {"id": "m", "plataforma": "cooperativa"},
        {},
    ]

    guion = tmp_path / "plataformas.mjs"
    guion.write_text(
        cuerpo.replace("export const", "const")
        + "\nconst us = " + json.dumps(casos) + ";\n"
        + "console.log(JSON.stringify(us.map((u) => "
          "[plataformaDe(u), puedeTenerComision(u), esCooperativista(u)])));\n",
        encoding="utf-8")

    salida = subprocess.run([node, str(guion)], capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, (
        f"el código de plataformas de la pantalla no corre: {salida.stderr.strip()}")
    pantalla = json.loads(salida.stdout)

    for u, (plat, comision, coop) in zip(casos, pantalla):
        assert plat == P.plataforma_de(u), (
            f"{u}: la pantalla lo pone en «{plat}» y el servidor en "
            f"«{P.plataforma_de(u)}»")
        assert comision == P.puede_tener_comision(u), (
            f"{u}: la pantalla dice comisión={comision} y el servidor "
            f"{P.puede_tener_comision(u)}. Esto es nómina.")
        assert coop == (AC.rol_de(u) is not None), (
            f"{u}: la pantalla {'enseña' if coop else 'esconde'} «Mi área» y el "
            f"servidor le da rol={AC.rol_de(u)!r}. O ve un botón que le va a dar "
            "403, o ha perdido el suyo sin que nadie se entere.")
