# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA FICHA DE LA AGENDA Y LA CUENTA DE USUARIO, UNIDAS — SIN PAGAR POR DEDUCCIÓN.

La agenda de montajes ya sabe quién montó cada cocina: el montaje apunta a una
FICHA y lleva la referencia del presupuesto. La liquidación apunta a una CUENTA.
El puente es `usuario.montadorId`, un campo que existía en el modelo desde antes
y que no leía nadie.

LA REGLA QUE NO SE TOCA: SE SUGIERE, NO SE ASIGNA. Asignar montador es del
master (regla 20), porque mueve una comisión de un bolsillo a otro. Esto propone;
aplicarlo es un clic suyo. Ahorrar clics no puede convertirse en pagar por
deducción.

Y EN LA DUDA SE CALLA. Tres casos, y los tres se prueban aquí: ficha sin cuenta,
cuenta que no es socio montador, y varios montadores distintos en el mismo
pedido. En los tres el pedido se queda sin sugerencia y sigue saliendo como «sin
asignar», que es justo donde el master lo va a ver.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import enlace_montador as EM  # noqa: E402

SOCIO = {"id": "u-mon", "clientName": "Bea", "esCooperativistaMontador": True,
         "montadorId": "ficha-1"}
EN_NOMINA = {"id": "u-nom", "clientName": "Carlos", "isMontador": True,
             "montadorId": "ficha-2"}
SIN_CUENTA = "ficha-3"

PEDIDO = {"id": "PED-1", "budgetNumber": "PRE-2026-0001"}
MONTAJE = {"id": "M-1", "montadorId": "ficha-1", "montadorName": "Bea",
           "budgetRef": "PRE-2026-0001"}


def test_la_agenda_PROPONE_al_socio_que_monto_la_cocina():
    s = EM.sugerencias([PEDIDO], [MONTAJE], [SOCIO, EN_NOMINA])
    assert s["PED-1"]["montadorUserId"] == "u-mon"
    assert s["PED-1"]["nombre"] == "Bea"
    assert s["PED-1"]["porque"], (
        "la sugerencia no dice de dónde sale: una propuesta sobre nómina que no "
        "se puede comprobar no es de fiar")


def test_una_ficha_SIN_CUENTA_no_propone_nada():
    """El montaje existe y está agendado, pero esa ficha no tiene usuario: no
    hay a quién pagarle, y no se puede inventar."""
    montaje = dict(MONTAJE, montadorId=SIN_CUENTA)
    assert EM.sugerencias([PEDIDO], [montaje], [SOCIO, EN_NOMINA]) == {}


def test_un_montador_EXTERNO_no_se_propone_JAMAS():
    """El master, 28/08: «los montadores pueden ser externos o miembros de la
    cooperativa; tenlo muy presente».

    En la agenda están LOS DOS, mezclados, porque los dos montan cocinas. Un
    externo puede tener su ficha, su agenda y sus montajes hechos y aun así no
    cobra comisión de cooperativista. La agenda no puede ser la puerta por la
    que entre en la nómina.
    """
    externo = {"id": "u-ext", "clientName": "Externo SL", "montadorId": "ficha-4"}
    montaje = dict(MONTAJE, montadorId="ficha-4", montadorName="Externo SL")
    assert EM.sugerencias([PEDIDO], [montaje], [SOCIO, externo]) == {}, (
        "un montador externo ha entrado en la propuesta de nómina por la agenda")

    # Y tampoco si además le dan el rol genérico de montador del ERP.
    externo_con_rol = dict(externo, isMontador=True)
    assert EM.sugerencias([PEDIDO], [montaje], [SOCIO, externo_con_rol]) == {}


def test_un_montador_EN_NOMINA_no_se_propone():
    """Monta cocinas igual, y no cobra comisión de cooperativista. Si se
    propusiera, un clic de más lo metería en la liquidación."""
    montaje = dict(MONTAJE, montadorId="ficha-2", montadorName="Carlos")
    assert EM.sugerencias([PEDIDO], [montaje], [SOCIO, EN_NOMINA]) == {}


def test_VARIOS_MONTADORES_en_el_mismo_pedido_no_proponen_nada():
    """Quién cobra ahí lo decide el master, no un desempate escrito por mí."""
    otro = dict(MONTAJE, id="M-2", montadorId="ficha-9", montadorName="Otro")
    tercero = {"id": "u-9", "clientName": "Dani", "esCooperativistaMontador": True,
               "montadorId": "ficha-9"}
    s = EM.sugerencias([PEDIDO], [MONTAJE, otro], [SOCIO, tercero])
    assert s == {}, f"se ha elegido uno de los dos montadores por su cuenta: {s}"


def test_LO_YA_ASIGNADO_no_se_propone_cambiar():
    """Una sugerencia encima de una decisión del master es una invitación a
    deshacerla sin querer."""
    puesto = dict(PEDIDO, montadorUserId="u-otro")
    assert EM.sugerencias([puesto], [MONTAJE], [SOCIO]) == {}


def test_DOS_CUENTAS_con_la_misma_ficha_no_proponen_ninguna():
    """Es un error de datos, y resolverlo a dedo sería pagarle a una de las dos
    por sorteo."""
    gemelo = dict(SOCIO, id="u-mon2", clientName="Bea (duplicada)")
    assert EM.cuentas_por_ficha([SOCIO, gemelo]) == {}
    assert EM.sugerencias([PEDIDO], [MONTAJE], [SOCIO, gemelo]) == {}


def test_el_montaje_se_ata_por_las_REFERENCIAS_del_pedido_y_no_por_el_nombre():
    """Por `budgetRef`/`budgetId` contra las referencias del pedido. Nunca por
    el nombre del cliente: dos cocinas del mismo cliente son cosa corriente."""
    por_project = {"id": "PED-2", "projectId": "proj-7"}
    montaje = dict(MONTAJE, budgetId="proj-7", budgetRef="")
    assert EM.sugerencias([por_project], [montaje], [SOCIO])["PED-2"]["montadorUserId"] == "u-mon"

    # Mismo cliente, referencia distinta: no se ata.
    ajeno = {"id": "PED-3", "budgetNumber": "PRE-2026-0999",
             "customerName": "Pérez"}
    assert EM.sugerencias([ajeno], [MONTAJE], [SOCIO]) == {}


def test_un_pedido_SIN_MONTAJE_no_propone_nada():
    assert EM.sugerencias([{"id": "PED-4", "budgetNumber": "PRE-X"}], [MONTAJE], [SOCIO]) == {}


def test_no_revienta_con_datos_absurdos():
    for basura in (None, [], [{}], [{"montadorId": ""}]):
        assert isinstance(EM.sugerencias([PEDIDO], basura, [SOCIO]), dict)
        assert isinstance(EM.sugerencias(basura, [MONTAJE], [SOCIO]), dict)


def test_aplicar_sugerencias_es_del_MASTER_y_NO_PISA_lo_ya_asignado():
    """Se comprueba en el fichero de rutas: si solo se cierra la pantalla, el
    cierre es de adorno."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cooperativistas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('@router.post("/aplicar-sugerencias")')
    j = cuerpo.index("@router", i + 10)
    trozo = cuerpo[i:j]
    assert "_es_master" in trozo, "aplicar sugerencias no está cerrado al master"
    assert '"montadorUserId": {"$in": [None, ""]}' in trozo, (
        "el update no lleva la condición de estar sin asignar: podría cambiarle "
        "el montador a un pedido que el master acaba de asignar a mano")
