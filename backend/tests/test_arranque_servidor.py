# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO DEL ARRANQUE: que el programa se pueda IMPORTAR, no solo entender.

POR QUE EXISTE ESTE FICHERO
---------------------------
Porque el ERP entero se cayo y ninguna prueba se entero. Una insercion dejo
escrito dos veces el decorador de una ruta en la misma linea:

    @router.post(".../comparar")@router.post(".../comparar")

Eso es sintaxis VALIDA —un decorador aplicado a otro— asi que `ast.parse` da
verde. Pero al importar revienta con `unsupported operand type(s) for @`, y al
reventar `routes/projects.py` no arranca `server.py`: la API entera muerta,
Railway en CRASHED y la pantalla en «CARGANDO...» para siempre.

Las 539 pruebas de calculo tampoco lo cogieron, y no es un fallo suyo: cargan
cada modulo POR RUTA, uno a uno, para poder probar las cuentas sin levantar
Mongo. Comprueban que los numeros salen bien, no que el programa arranque.

Faltaba justo esto: IMPORTAR de verdad los modulos de rutas. Es lo unico que
habria cantado ese fallo, y es barato.

LO QUE ESTA PRUEBA NO PUEDE HACER
---------------------------------
No levanta `server.py` entero, porque hay modulos que hacen consultas a Mongo
EN EL MOMENTO DE IMPORTARSE (`routes/fabrica.py` siembra fabricas por defecto).
Sin base de datos delante, eso falla por una razon que no tiene nada que ver
con el codigo. Asi que se importan los modulos que no tocan la base de datos al
cargarse, que son la inmensa mayoria — y son donde se escriben las rutas.

Si algun dia se quita esa consulta del import, esta prueba puede pasar a
importar `server` entero y sera mejor todavia.
"""
import importlib
import os
import sys

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Los modulos de rutas que se importan sin necesitar base de datos. Se listan a
# mano, y no con un `glob`, para que aniadir uno nuevo sea una decision: la
# lista es tambien el inventario de lo que esta protegido.
MODULOS_DE_RUTAS = [
    "routes.projects",
    "routes.almacen",
    "routes.electro_fichas",
    "routes.armarios_alzado",
    "routes.estudio_cocinas",
    "routes.cascos",
    "routes.expedient",
    "routes.digitalizador",
    "routes.exports",
]


# Los paquetes que otras pruebas SUSTITUYEN por modulos de mentira para poder
# probar sin Mongo ni autenticacion. Aqui hay que quitarlos de en medio: el
# servidor arranca con los de verdad, y esta prueba es sobre el arranque.
PAQUETES_A_LIMPIAR = ("services", "routes", "models")


def _quitar_de_sys_modules():
    """Se lleva los modulos falsos —y tambien los buenos— para importar limpio.

    Sin esto, la prueba fallaba o pasaba SEGUN EL ORDEN en que pytest ejecutara
    los ficheros, que es la peor clase de prueba que hay: la que un dia dice una
    cosa y otro dia la contraria sin que nada haya cambiado.
    """
    guardados = {}
    for nombre in list(sys.modules):
        if nombre in PAQUETES_A_LIMPIAR or any(
                nombre.startswith(p + ".") for p in PAQUETES_A_LIMPIAR):
            guardados[nombre] = sys.modules.pop(nombre)
    return guardados


@pytest.fixture(scope="module", autouse=True)
def _entorno():
    """Lo minimo para que los modulos se dejen importar.

    JWT_SECRET es obligatorio a proposito (un secreto por defecto seria un
    agujero), asi que aqui se pone uno de mentira: esta prueba no comprueba
    seguridad, comprueba que el fichero se puede cargar.
    """
    previo = dict(os.environ)
    os.environ.setdefault("JWT_SECRET", "solo_para_probar_el_arranque_no_es_un_secreto")
    os.environ.setdefault("MONGO_URL", "mongodb://127.0.0.1:27017")
    os.environ.setdefault("DB_NAME", "arranque_de_prueba")
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)

    guardados = _quitar_de_sys_modules()
    yield
    # Y al salir se deja todo como estaba, para no romperle el escenario a las
    # pruebas que vengan detras.
    _quitar_de_sys_modules()
    sys.modules.update(guardados)
    os.environ.clear()
    os.environ.update(previo)


@pytest.mark.parametrize("modulo", MODULOS_DE_RUTAS)
def test_el_modulo_de_rutas_se_puede_importar(modulo):
    """CANDADO. `ast.parse` dice si el fichero SE ENTIENDE; esto dice si se
    puede CARGAR, que es lo que hace el servidor al arrancar."""
    try:
        importlib.import_module(modulo)
    except Exception as e:  # noqa: BLE001 - se quiere ver CUALQUIER fallo de carga
        pytest.fail(
            f"`{modulo}` no se puede importar: {type(e).__name__}: {e}\n"
            "El servidor no arrancaria y la API entera se quedaria muerta.")


def test_las_rutas_quedan_registradas_y_sin_repetirse(_entorno=None):
    """Dos rutas con el mismo metodo y el mismo camino: la segunda no se llama
    NUNCA, y no da ningun error — simplemente una de las dos deja de existir."""
    import routes.projects as rp

    vistas = {}
    for r in rp.router.routes:
        camino = getattr(r, "path", "")
        for metodo in sorted(getattr(r, "methods", []) or []):
            if metodo in ("HEAD", "OPTIONS"):
                continue
            clave = (metodo, camino)
            assert clave not in vistas, (
                f"{metodo} {camino} esta declarada dos veces: la segunda no se "
                "llamara nunca y nada avisa de ello")
            vistas[clave] = True
    assert vistas, "el router de proyectos se ha quedado sin rutas"


def test_las_rutas_nuevas_de_medidas_siguen_vivas():
    """Se cayeron una vez y nadie se entero hasta que el ERP no cargaba."""
    import routes.projects as rp

    caminos = {getattr(r, "path", "") for r in rp.router.routes}
    for esperada in (
        "/projects/{project_id}/medidas",
        "/projects/{project_id}/medidas/{clave}/tomar",
        "/projects/{project_id}/medidas/{clave}/confirmar",
        "/projects/{project_id}/medidas/{clave}/impacto",
        "/projects/{project_id}/medidas/comparar",
        "/projects/{project_id}/excepcion",
    ):
        assert esperada in caminos, f"falta la ruta {esperada}"
