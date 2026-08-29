# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUIÉN ES EL MASTER: UNA SOLA LISTA, Y YA SIN `isAdmin`.

Por esta puerta pasan la tarifa MV, el coste, el margen, la rentabilidad, las
comisiones de los cooperativistas y el cierre del mes.

DOS COSAS QUE VIGILA ESTE CANDADO.

1. QUE `isAdmin` SIGA FUERA (master, 29/08). Administrar el ERP y ver lo que le
   cuesta a la casa cada mueble no son el mismo permiso, y el día que se le dé
   admin a quien lleve carpinter.io o Studio3K la diferencia se nota en euros.

   ESTO MISMO SE INTENTÓ EL 28/08 Y HUBO QUE REVERTIRLO EL MISMO DÍA, con toda
   la relación de Cocina Montada 3 saliendo a 0,00 €. Y no fue por la idea: fue
   porque `isPrimaryAdmin` NO LLEGABA AL SERVIDOR —el usuario se reconstruía con
   trece campos del token y ese no estaba—, así que apretar era imposible por
   definición. Eso se arregló el 29 (regla 25) y por eso ahora sí se puede.

2. QUE LA VÁLVULA SIGA AHÍ. Si no queda NI UNA cuenta marcada, el ERP vuelve
   solo a la lista ancha y lo grita en el log. Un candado que deja la casa sin
   dueño no es un candado, es una avería — y aquí «sin dueño» significa que
   nadie puede presupuestar.

3. QUE NADIE VUELVA A COPIAR LA LISTA. Vivía copiada en cuatro ficheros mientras
   `services/master.py` decía ser la única fuente sin serlo: cambiarla allí no
   cambiaba nada en las rutas. Ahora se le pregunta.
"""
import asyncio
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import master as M  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dónde está copiada la lista, y con qué nombre.
COPIAS = (
    ("routes/cascos.py", "_MASTER_FLAGS"),
    ("routes/plan_negocio.py", "_MASTER_FLAGS"),
    ("routes/auth_routes.py", "_FLAGS_MASTER"),
)


def _tupla(ruta, nombre):
    """Lee la tupla del fichero sin importarlo: se mira el CÓDIGO, no el módulo
    ya cargado, porque lo que se vigila es lo que está escrito."""
    with open(os.path.join(RAIZ, ruta), "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Assign) and len(nodo.targets) == 1
                and isinstance(nodo.targets[0], ast.Name)
                and nodo.targets[0].id == nombre):
            return tuple(ast.literal_eval(nodo.value))
    raise AssertionError(f"no está «{nombre}» en {ruta}")


def test_un_ADMIN_A_SECAS_ya_no_ve_el_dinero():
    """El cambio del 29/08, y el que costó un apagón la primera vez.

    Administrar el ERP y ver lo que le cuesta a la casa cada mueble no son el
    mismo permiso. Lo que hacía imposible este cambio era otra cosa —que
    `isPrimaryAdmin` no llegara al servidor (regla 25)— y ya está arreglado.
    """
    M.desactivar_rescate()
    assert not M.es_master({"isAdmin": True}), (
        "`isAdmin` ha vuelto a la lista del master: cualquier administrador ve "
        "la tarifa del proveedor, el margen y la nómina de los cooperativistas")
    assert "isAdmin" not in M.FLAGS_MASTER
    assert set(M.FLAGS_MASTER) < set(M.FLAGS_ANCHOS)
    assert M.FLAGS_QUE_SE_QUITAN == ("isAdmin",)


def test_quien_NO_es_master_sigue_fuera():
    """Lo que la reversión NO puede llevarse por delante: gerencia y dirección
    comercial siguen sin ver la tarifa del proveedor ni el margen."""
    for flag in ("isGerente", "isDirectorComercial", "isDirectorFabrica",
                 "isResponsableDelegacion", "isRepresentative", "isController",
                 "isMontador", "isFabrica", "isTienda"):
        assert not M.es_master({flag: True}), f"{flag} está entrando al dinero"
    assert not M.es_master({})
    assert not M.es_master(None)


def test_el_master_de_verdad_SI_entra():
    """La otra mitad: un candado que cierra de más deja la casa sin dueño.

    Aquí había escrito que la cuenta `admin` ya lleva `isPrimaryAdmin` y que por
    eso apretar la lista no dejaba fuera al master. NO ERA VERDAD, y se vio en
    producción el 28/08: se apretó, el master se quedó sin sus propios precios y
    Cocina Montada 3 salió a 0,00 €. Queda escrito porque el error no fue el
    cambio, fue darlo por hecho: lo que dice un script de sincronización no es lo
    que hay en la base de datos, y antes de estrechar un permiso hay que MIRAR
    quién queda dentro.
    """
    M.desactivar_rescate()
    assert M.es_master({"isPrimaryAdmin": True})
    assert M.es_master({"isMaster": True})
    assert set(M.FLAGS_MASTER), "la lista se ha quedado vacía: nadie sería master"


def test_YA_NO_HAY_COPIAS_de_la_lista():
    """`services/master.py` decía ser la única fuente y no lo era.

    La misma tupla vivía copiada en tres ficheros de rutas, así que cambiarla
    aquí no cambiaba nada allí — y el módulo entero era código muerto con un
    docstring que prometía lo contrario. Ahora las rutas preguntan.
    """
    for ruta, nombre in COPIAS:
        with open(os.path.join(RAIZ, ruta), "r", encoding="utf-8") as f:
            cuerpo = f.read()
        assert nombre not in cuerpo, (
            f"ha vuelto a aparecer «{nombre}» en {ruta}. Una regla de permisos "
            "copiada es una que se aprieta y las demás que se quedan abiertas: "
            "se le pregunta a `services.master.es_master`.")
        assert "from services.master import es_master" in cuerpo, (
            f"{ruta} ya no le pregunta a `services/master.py` quién es master")


def test_queda_ESCRITO_lo_que_costo_la_primera_vez():
    """Para que dentro de seis meses nadie repita el intento del 28/08."""
    cuerpo = open(M.__file__, encoding="utf-8").read()
    assert "0,00" in cuerpo or "cero" in cuerpo, (
        "se ha borrado la explicación de lo que pasó al apretar esto la primera "
        "vez: sin ella, alguien quita la válvula «porque no hace falta»")


# ─── LA VÁLVULA ─────────────────────────────────────────────────────────────

def test_SIN_NINGUNA_CUENTA_MARCADA_el_ERP_no_se_queda_sin_dueno():
    """Un candado que cierra de más deja la casa sin dueño.

    Y aquí «sin dueño» no es una molestia: es que NADIE puede leer la tarifa MV,
    o sea que la relación entera sale a 0,00 € y eso no da ningún error — se
    imprime igual y se puede enviar a un cliente. Por eso, si no queda ni una
    cuenta marcada, se vuelve solo a la lista ancha.
    """
    M.activar_rescate("prueba")
    try:
        assert M.hay_rescate()
        assert M.es_master({"isAdmin": True}), (
            "con el rescate abierto, un administrador tiene que poder seguir "
            "entrando: si no, no hay rescate que valga")
        assert M.flags_en_vigor() == M.FLAGS_ANCHOS
    finally:
        M.desactivar_rescate()
    assert not M.es_master({"isAdmin": True})
    assert M.flags_en_vigor() == M.FLAGS_MASTER


def test_LA_VALVULA_NO_ABRE_LA_PUERTA_A_NADIE_MAS():
    """Ni siquiera abierta del todo entra un gerente. El rescate devuelve la
    lista de ayer, no una barra libre."""
    M.activar_rescate("prueba")
    try:
        for flag in ("isGerente", "isDirectorComercial", "isController",
                     "isRepresentative", "isMontador", "isTienda"):
            assert not M.es_master({flag: True}), f"{flag} entra con el rescate"
    finally:
        M.desactivar_rescate()


def test_EL_ARRANQUE_CUENTA_Y_DECIDE():
    """Se cuenta al arrancar: si hay alguien marcado se aprieta, si no, no."""
    class _Users:
        def __init__(self, con_marca, solo_admin):
            self.con_marca, self.solo_admin = con_marca, solo_admin
        async def count_documents(self, filtro):
            return self.con_marca if "$or" in filtro else self.solo_admin

    class _Db:
        def __init__(self, u): self.users = u

    r = asyncio.run(M.comprobar_que_hay_master(_Db(_Users(2, 1))))
    assert r == {"conMarca": 2, "soloAdmin": 1, "rescate": False}
    assert not M.hay_rescate()

    r = asyncio.run(M.comprobar_que_hay_master(_Db(_Users(0, 3))))
    assert r["rescate"] is True and M.hay_rescate(), (
        "sin ninguna cuenta marcada el ERP se aprieta igual y se queda sin dueño")
    M.desactivar_rescate()


def test_SI_NO_SE_PUEDE_CONTAR_tampoco_se_apreta():
    """Un Mongo lento al arrancar no puede dejar a la casa sin presupuestar."""
    class _Roto:
        async def count_documents(self, filtro):
            raise RuntimeError("mongo no responde")

    class _Db:
        users = _Roto()

    r = asyncio.run(M.comprobar_que_hay_master(_Db()))
    assert r["rescate"] is True and M.hay_rescate()
    M.desactivar_rescate()


def test_el_ARRANQUE_DEL_SERVIDOR_hace_esa_comprobacion():
    """El recuento no sirve de nada si no lo llama nadie."""
    with open(os.path.join(RAIZ, "server.py"), "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert "comprobar_que_hay_master(db)" in cuerpo, (
        "el arranque ya no comprueba si queda alguien que pueda ver el dinero: "
        "la válvula está escrita y no la abre nadie")


# ─── LA LLAVE SE TIENE QUE PODER REPARTIR ───────────────────────────────────

# RAIZ es la carpeta `backend`; el repo está un escalón por encima.
PANEL = os.path.join(os.path.dirname(RAIZ), "frontend", "src", "components",
                     "SettingsModal.jsx")


def _panel():
    with open(PANEL, "r", encoding="utf-8") as f:
        return f.read()


def test_el_PANEL_MASTER_deja_MARCAR_isPrimaryAdmin():
    """Lo que hacía IMPOSIBLE arreglar el apagón del 28/08 desde el ERP.

    `isPrimaryAdmin` se leía en cinco sitios y no se podía poner desde ninguna
    pantalla: solo lo escribía un script suelto contra la base de datos. Así que
    al quitar `isAdmin` de la lista del master, el master se quedó fuera de su
    propia tarifa y no había forma de devolverse el permiso sin un despliegue.

    Mientras esa casilla no exista, estrechar `FLAGS_MASTER` no se puede hacer.
    """
    cuerpo = _panel()
    assert 'data-testid="primary-admin-checkbox"' in cuerpo, (
        "el panel Master ya no deja marcar «Admin principal». Sin eso, "
        "`isPrimaryAdmin` solo se puede poner tocando la base de datos a mano, y "
        "estrechar la lista del master vuelve a ser un viaje sin billete de "
        "vuelta.")
    assert "userForm.isPrimaryAdmin" in cuerpo, (
        "la casilla no está atada al formulario del usuario: no guardaría nada")


def test_la_CASILLA_la_ve_QUIEN_YA_VE_EL_DINERO_no_solo_el_primary():
    """La pescadilla que se muerde la cola, y por la que casi vuelve a pasar.

    Si la casilla se enseñara solo a `isPrimaryAdmin`, quedaría invisible justo
    para quien tiene que marcarla: la cuenta con la que trabaja el master es
    `isAdmin`. Se enseña a quien YA ve el dinero —la misma puerta que
    `FLAGS_MASTER`—, que además es lo correcto: la llave la reparte quien la
    tiene, no un gerente marcándosela a sí mismo.
    """
    cuerpo = _panel()
    i = cuerpo.index("const veElDineroDeLaCasa")
    puerta = cuerpo[i:cuerpo.index("\n\n", i)]
    for flag in M.FLAGS_MASTER:
        assert flag in puerta, (
            f"«{flag}» abre la tarifa MV en el servidor pero no ve la casilla de "
            "«Admin principal» en pantalla. Con eso, quien tiene que repartir la "
            "llave no la encuentra.")
    for prohibido in ("isGerente", "isDirectorComercial", "isController"):
        assert prohibido not in puerta, (
            f"«{prohibido}» puede marcarse a sí mismo la llave del dinero: "
            "entraría al coste y al margen por la puerta de atrás")
    assert 'data-testid="primary-admin-checkbox"' in cuerpo


def test_la_PANTALLA_CUENTA_a_quien_dejaria_fuera_apretar_la_lista():
    """La comprobación que faltó, puesta donde se toma la decisión.

    «Primero se mira a quién afecta, después se cierra» estaba escrito en
    `services/master.py` y en ningún sitio donde alguien lo fuera a leer. Ahora
    el panel cuenta, con los usuarios que ya tiene en pantalla, cuántas cuentas
    entran al dinero y cuántas lo hacen SOLO por ser administrador — que son
    exactamente las que se quedarían fuera.
    """
    cuerpo = _panel()
    i = cuerpo.index("Quién ve el dinero de la casa")
    trozo = cuerpo[max(0, i - 1500):i + 1500]
    assert "!u.isPrimaryAdmin && !u.isMaster" in trozo, (
        "el aviso ya no distingue quién entra SOLO por `isAdmin`, que son "
        "justo los que perderían el acceso al estrechar la lista")
