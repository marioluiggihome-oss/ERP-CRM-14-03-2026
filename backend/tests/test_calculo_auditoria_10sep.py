# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""AUDITORÍA EXTERNA DEL 10/09/2026 — los cuatro que no tocan permisos.

El master trajo un informe de auditoría hecho por otra IA sobre el commit
`ab3e60ca`. Se comprobaron los NUEVE hallazgos uno a uno contra el código: los
nueve eran ciertos. Aquí se cierran los cuatro que NO cambian quién entra a
nada, así que no pueden dejar a nadie fuera:

  5. Las contraseñas acababan en el log de errores.
  7. Se aceptaban cobros NEGATIVOS.
  6. Una compra podía abonar los renders DOS VECES.
  4. «Cerrar sesiones» no cerraba nada: el refresh seguía emitiendo.

Los cinco restantes —clientes ajenos, el Excel con márgenes de toda la casa,
las cuentas desactivadas, las medidas inventadas del diseñador y el bajo
fregadero mal tarifado— van aparte porque aprietan permisos o cambian lo que
la fábrica recibe, y ahí el orden lo decide el master (regla 8c: primero se
comprueba a quién se deja fuera).

LO QUE TIENEN EN COMÚN LOS CUATRO: ninguno daba un error. Ni uno. El ERP
seguía funcionando y devolviendo 200 mientras guardaba una contraseña, doblaba
un saldo o dejaba entrar a una sesión cerrada.
"""
import asyncio
import importlib.util
import math
import os
import sys
import types

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")


def _modulo(nombre, ruta):
    """Carga un módulo REAL del disco, sin arrastrar el paquete entero."""
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(BACKEND, ruta))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _leer(ruta):
    with open(os.path.join(BACKEND, ruta), encoding="utf-8") as f:
        return f.read()


# ════ 5. LAS CONTRASEÑAS NO PUEDEN ACABAR EN EL LOG ════════════════════════

R = _modulo("redaccion_logs_real", "services/redaccion_logs.py")


def test_una_contrasenia_NUNCA_llega_al_log():
    """CANDADO DURO. Solo se registran POST/PUT/PATCH/DELETE, que es
    EXACTAMENTE donde viajan las credenciales: cada login mal tecleado —cosa de
    todos los días— dejaba la contraseña en claro en `error_log`."""
    guardado = R.cuerpo_para_el_log(
        "/api/auth/login", '{"username":"ana","password":"la-de-verdad"}')
    assert "la-de-verdad" not in guardado, (
        f"la contraseña sigue llegando al log de errores: «{guardado}»")
    assert guardado == "", (
        "en una ruta de credenciales no se guarda cuerpo NINGUNO, ni redactado")


def test_se_redacta_ENTRANDO_en_lo_anidado():
    """Un `{"user": {"password": ...}}` es lo que manda el alta de usuario. Una
    redacción de un solo nivel lo dejaría escrito."""
    guardado = R.cuerpo_para_el_log(
        "/api/users", '{"user":{"name":"ana","newPassword":"secreta"},"ok":1}')
    assert "secreta" not in guardado, f"contraseña anidada sin redactar: «{guardado}»"
    assert "ana" in guardado, (
        "se ha redactado de más: sin los campos normales el log no sirve para "
        "diagnosticar nada")


@pytest.mark.parametrize("campo", [
    "password", "Password", "new_password", "newPassword", "passwd",
    "contrasena", "clave", "token", "accessToken", "api_key", "apiKey",
    "secret", "authorization", "cookie", "iban", "cvv",
])
def test_todas_las_formas_de_escribirlo_caen(campo):
    """Se mira el nombre SIN separadores y en minúsculas. Escribir cada
    variante a mano es garantizar que falte una."""
    assert R.es_campo_sensible(campo), f"«{campo}» ya no se considera sensible"


def test_un_cuerpo_QUE_NO_SE_PUEDE_MIRAR_no_se_guarda():
    """En la duda no se guarda. Un formulario `a=1&password=x` no es JSON: no
    se puede redactar campo a campo, así que no se copia."""
    guardado = R.cuerpo_para_el_log("/api/x", "username=ana&password=secreta")
    assert "secreta" not in guardado, f"cuerpo opaco copiado tal cual: «{guardado}»"


def test_el_servidor_USA_la_redaccion_y_no_el_cuerpo_crudo():
    """El módulo puede estar perfecto: si el servidor no lo llama, no protege."""
    src = _leer("server.py")
    assert "cuerpo_para_el_log(request.url.path, body_text)" in src, (
        "`_log_request_error` ya no redacta el cuerpo")
    assert '"body": (body_text or "")[:2000]' not in src, (
        "ha vuelto el cuerpo en crudo al log de errores")


# ════ 7. UN COBRO ES DINERO QUE ENTRA ══════════════════════════════════════

class _FalsaColeccion:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.insertados = []

    async def find_one(self, *a, **k):
        return self.docs[0] if self.docs else None

    def find(self, *a, **k):
        class _C:
            def __init__(self, d): self.d = d
            async def to_list(self, n): return self.d
        return _C([])

    async def insert_one(self, doc):
        self.insertados.append(doc)
        return types.SimpleNamespace(inserted_id="x")

    async def update_one(self, *a, **k):
        return types.SimpleNamespace(modified_count=1, upserted_id=None)


class _FalsaDB:
    def __init__(self, factura):
        self.invoices = _FalsaColeccion([factura])
        self.payments = _FalsaColeccion()


def _tracker():
    mod = _modulo("payment_tracker_real", "services/facturacion/payment_tracker.py")
    clase = next(getattr(mod, n) for n in dir(mod)
                 if n.endswith("Tracker") and isinstance(getattr(mod, n), type))
    return clase


@pytest.mark.parametrize("importe", [-25, -0.01, 0, -1000])
def test_un_cobro_NEGATIVO_o_CERO_se_rechaza(importe):
    """CANDADO DURO. Solo había tope por ARRIBA, así que un -25 pasaba entero y
    la factura se quedaba con `totalPaid = -25` en estado «parcial».

    Y no es solo contabilidad: «cobrado del TODO» es una de las dos condiciones
    que liberan la comisión de un cooperativista (regla 17). Un cobro negativo
    mete el pedido en un limbo del que no sale, sin que salte ningún error."""
    Tracker = _tracker()
    t = Tracker(_FalsaDB({"id": "F1", "total": 100, "status": "issued"}))
    with pytest.raises(ValueError) as e:
        asyncio.get_event_loop().run_until_complete(
            t.register_payment("F1", importe, "transferencia"))
    assert "mayor que cero" in str(e.value) or "número" in str(e.value), (
        f"un cobro de {importe} se ha rechazado por el motivo equivocado: {e.value}")


@pytest.mark.parametrize("importe", [float("nan"), float("inf"), float("-inf")])
def test_un_importe_QUE_NO_ES_UN_NUMERO_se_rechaza(importe):
    """Un `inf` pasa cualquier comparación de «mayor que cero» y envenena todas
    las sumas que toque después."""
    Tracker = _tracker()
    t = Tracker(_FalsaDB({"id": "F1", "total": 100, "status": "issued"}))
    with pytest.raises(ValueError):
        asyncio.get_event_loop().run_until_complete(
            t.register_payment("F1", importe, "transferencia"))


def test_un_cobro_NORMAL_sigue_entrando():
    """La otra mitad: cerrar el negativo no puede impedir cobrar."""
    Tracker = _tracker()
    t = Tracker(_FalsaDB({"id": "F1", "total": 100, "status": "issued"}))
    res = asyncio.get_event_loop().run_until_complete(
        t.register_payment("F1", 50, "transferencia"))
    assert res is not None, "se ha cerrado también el cobro bueno"


def test_la_suma_de_cobros_NO_tiene_tope():
    """`to_list(100)` dejaba el pago 101 fuera de la suma: la factura se quedaba
    «a medias» para siempre, y con ella la comisión que espera a que esté
    cobrada del todo."""
    # SIN COMENTARIOS. La primera versión miraba el fichero entero y se puso
    # roja por el comentario que EXPLICA el arreglo, que cita `to_list(100)`.
    # Misma trampa que en la regla 24: un reconocedor que lee prosa no lee
    # código. Y de paso descubrió lo importante: quedaban TRES sitios más.
    codigo = "\n".join(l.split("#")[0] for l in
                       _leer("services/facturacion/payment_tracker.py").splitlines())
    assert ".to_list(100)" not in codigo, (
        "ha vuelto un tope de 100 pagos. Con más de 100, la suma se queda "
        "corta: la factura parece a medio cobrar para siempre y congela la "
        "comisión del socio (regla 17) sin dar ningún error.")


def test_el_modelo_de_entrada_TAMBIEN_lo_cierra():
    """Los dos cierres. Uno solo en la puerta se rodea por la ventana."""
    src = _leer("routes/invoices.py")
    assert "amount: float = Field(gt=0" in src, (
        "el modelo de cobro vuelve a aceptar cualquier número")


# ════ 6. UNA COMPRA ABONA UNA VEZ ══════════════════════════════════════════

def _codigo_del_webhook():
    """El CÓDIGO del webhook, sin comentarios.

    Sin quitarlos, este candado se engaña solo: el comentario que explica el
    arreglo cita `update_one(upsert=True)` y `añadir_saldo`, así que buscar
    posiciones en el texto completo mide la prosa, no el orden de ejecución."""
    src = _leer("routes/render_packs.py")
    i = src.index("async def webhook")
    cuerpo = src[i:src.index("@router.get", i)]
    limpio = "\n".join(l.split("#")[0] for l in cuerpo.splitlines())
    # Que el recorte no se coma el código: si se quedara vacío, todas las
    # comprobaciones de abajo pasarían por no encontrar nada.
    assert "upsert=True" in limpio and "añadir_saldo(" in limpio, (
        "el recorte del webhook ha dejado fuera el código que hay que mirar")
    return limpio


def test_el_abono_se_RESERVA_antes_de_darlo():
    """CANDADO DURO. Dos entregas simultáneas del mismo webhook abonaban 40
    renders de un pack de 20: entre MIRAR si ya está y ABONAR caben las dos.

    El arreglo es de ORDEN, no de comprobaciones: se reserva con un upsert
    —una sola operación atómica— y solo quien la crea abona."""
    # SIN COMENTARIOS, Y ESTO COSTÓ CAZARLO. La primera versión buscaba
    # `upsert=True` en el fichero entero y lo encontraba en el COMENTARIO que
    # explica el arreglo —que cita `update_one(upsert=True)` literalmente—, o
    # sea 700 caracteres antes que en el código. La mutación «abona antes de
    # reservar» pasaba en verde. Tercera vez que un candado de este repo se
    # engaña con su propia explicación (reglas 24 y 34).
    cuerpo = _codigo_del_webhook()

    pos_reserva = cuerpo.index("upsert=True")
    pos_abono = cuerpo.index("añadir_saldo(")
    assert pos_reserva < pos_abono, (
        "se abona ANTES de reservar la compra: dos entregas a la vez abonarían "
        "las dos")
    assert "upserted_id is None" in cuerpo, (
        "ya no se mira quién creó la reserva: si abonan las dos, da igual "
        "haberla reservado")
    assert "find_one" not in cuerpo[:pos_reserva], (
        "ha vuelto el «mirar y luego abonar»: entre las dos cosas caben dos "
        "entregas simultáneas y las dos abonan")


def test_una_caida_a_medias_NO_abona_dos_veces():
    """La otra forma de repetir: si el servidor se cae entre reservar y abonar,
    el reintento tiene que TERMINAR el trabajo, no empezarlo otra vez."""
    cuerpo = _codigo_del_webhook()
    assert "abonadoAt" in cuerpo, (
        "no se marca cuándo se abonó: no hay forma de distinguir una compra "
        "terminada de una que se quedó a medias")
    assert 'previa.get("abonadoAt")' in cuerpo, (
        "el reintento no mira si la compra ya se abonó: o abona dos veces, o "
        "deja al cliente sin sus renders")
    assert '"abonadoAt": None' in cuerpo, (
        "la reserva no nace marcada como SIN abonar, así que una compra a "
        "medias parecerá terminada")


# ════ 4. CERRAR SESIONES TIENE QUE CERRARLAS ═══════════════════════════════

def test_el_refresh_comprueba_la_REVOCACION():
    """CANDADO DURO. `require_auth` sí la comprobaba y el refresh NO: el token
    de acceso caduca en minutos, pero con el de renovación vivo se pedía otro y
    se seguía dentro. «Cerrar todas las sesiones» parecía hecho y no lo estaba."""
    src = _leer("routes/auth_routes.py")
    i = src.index("async def refresh_token")
    cuerpo = src[i:i + 2500]
    assert "token_revocado" in cuerpo, (
        "el refresh ha dejado de comprobar la revocación: cerrar sesiones no "
        "cierra nada mientras viva el token de renovación")
    pos_revoc = cuerpo.index("token_revocado")
    pos_emitir = cuerpo.index("create_access_token")
    assert pos_revoc < pos_emitir, (
        "se comprueba la revocación DESPUÉS de emitir el token nuevo: llega "
        "tarde")


def test_el_refresh_sigue_mirando_que_la_cuenta_este_activa():
    """No se puede arreglar una mitad rompiendo la otra."""
    src = _leer("routes/auth_routes.py")
    i = src.index("async def refresh_token")
    assert 'isActive' in src[i:i + 2500], (
        "el refresh ha dejado de mirar si la cuenta está activa")
