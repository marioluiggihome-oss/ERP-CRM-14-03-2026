# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUIÉN ES EL MASTER: UNA SOLA LISTA, Y HOY CON `isAdmin` DENTRO.

Por esta puerta pasan la tarifa MV, el coste, el margen, la rentabilidad, las
comisiones de los cooperativistas y el cierre del mes.

DOS COSAS QUE VIGILA ESTE CANDADO.

1. QUE `isAdmin` SIGA DENTRO — hoy, y esto sorprende, porque la intención es la
   contraria. Se quitó el 28/08 con buen criterio (administrar el ERP y ver lo
   que le cuesta a la casa cada mueble no son el mismo permiso) y hubo que
   devolverlo el mismo día: la cuenta con la que trabaja el master es `isAdmin`
   y Cocina Montada 3 salió entera a 0,00 €. El candado lo sujeta AHÍ para que
   nadie lo vuelva a apretar sin marcar antes `isPrimaryAdmin` a quien tiene que
   entrar. `FLAGS_ESTRECHOS` guarda a dónde se va cuando eso esté hecho.

2. QUE LAS COPIAS NO SE SEPAREN. La misma tupla vive en tres ficheros de rutas
   —porque hay pruebas que ejecutan trozos sueltos de esos ficheros y un import
   no llegaría—, y tres copias de una regla de permisos son una que se aprieta y
   dos que se quedan abiertas. Aquí se comparan con `services/master.py`.
"""
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


def test_el_ADMIN_entra_y_por_ahora_tiene_que_seguir_entrando():
    """REVERTIDO el 28/08, el mismo día, y conviene que quede escrito por qué.

    Se quitó `isAdmin` de esta lista con buen criterio: administrar el ERP y ver
    lo que le cuesta a la casa cada mueble no son el mismo permiso. Pero la
    cuenta con la que trabaja el master ES `isAdmin`, así que al apretarlo se
    quedó fuera de su propia tarifa: Cocina Montada 3 no pudo leer los precios
    MV y TODA la relación salió a 0,00 €.

    Un presupuesto a cero es lo peor que puede pasar aquí: no da error, se
    imprime igual y se puede enviar a un cliente.

    El orden correcto es al revés — primero marcar `isPrimaryAdmin` o `isMaster`
    a quien tenga que entrar, comprobar que entra, y después estrechar la lista.
    """
    assert M.es_master({"isAdmin": True}), (
        "`isAdmin` ha vuelto a salir de la lista del master. Antes de hacer eso "
        "hay que marcar `isPrimaryAdmin` a las cuentas que trabajan, o se "
        "quedan sin ver los precios y los presupuestos salen a cero.")
    assert set(M.FLAGS_ESTRECHOS) < set(M.FLAGS_MASTER), (
        "`FLAGS_ESTRECHOS` es a dónde se quiere ir: tiene que ser más estrecha")


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
    assert M.es_master({"isPrimaryAdmin": True})
    assert M.es_master({"isMaster": True})
    assert M.es_master({"isAdmin": True})
    assert set(M.FLAGS_MASTER), "la lista se ha quedado vacía: nadie sería master"


def test_las_TRES_COPIAS_dicen_lo_mismo():
    for ruta, nombre in COPIAS:
        assert _tupla(ruta, nombre) == tuple(M.FLAGS_MASTER), (
            f"«{nombre}» de {ruta} se ha separado de `services/master.py`. Una "
            "regla de permisos copiada es una que se aprieta y las demás que se "
            "quedan abiertas.")


def test_queda_ESCRITO_hacia_donde_se_quiere_ir():
    """Para que dentro de seis meses se sepa que esto está a medias, y por qué
    se revirtió — y no se vuelva a intentar en el mismo orden."""
    assert "isAdmin" not in M.FLAGS_ESTRECHOS
    assert "0,00" in open(M.__file__, encoding="utf-8").read() or \
        "cero" in open(M.__file__, encoding="utf-8").read(), (
        "se ha borrado la explicación de por qué se revirtió: sin ella alguien "
        "lo vuelve a apretar y los presupuestos vuelven a salir a cero")
