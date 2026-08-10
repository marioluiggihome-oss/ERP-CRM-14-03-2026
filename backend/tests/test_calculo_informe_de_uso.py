# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del informe de uso: QUE UN SERVICIO NO SE LLEVE A OTRO POR DELANTE.

EL FALLO
--------
En el Panel Maestro, la pestania «Uso usuarios» contestaba:

    Error: Error cargando informe

Y no era el informe. Era esto, en el arranque del servidor:

    try:
        backup_svc = init_backup_service(...)
        await backup_svc.start_scheduler(hour=3)      # <- si esto revienta...
        tracker = init_activity_tracker(db)           # <- ...esto NO SE EJECUTA
        await tracker.setup_indexes()
    except Exception as e:
        logger.warning(...)                            # y solo queda un warning

Dos servicios que no tienen NADA que ver compartiendo el mismo `except`. Si
falla el programador de copias, el tracker de actividad no llega a arrancar, y
semanas despues el informe de uso contesta «Tracker no inicializado» sin que
nadie relacione una cosa con la otra. El fallo no estaba donde salia el error.

LO QUE SE PROTEGE
-----------------
1. CADA SERVICIO EN SU PROPIO `try`. Uno que falla no puede saltarse al
   siguiente, y menos en silencio.

2. UN FALLO DE ARRANQUE SE REGISTRA COMO ERROR, no como aviso. Un `warning`
   entre mil lineas de log no lo lee nadie.

3. EL INFORME NO DEPENDE DE QUE EL ARRANQUE SALIERA BIEN. El tracker es una
   consulta con un puntero a la base de datos: si no esta, se hace uno. Un
   informe de solo lectura no puede quedarse caido hasta el proximo despliegue.

4. EL ERROR DICE QUE HA PASADO. «Error cargando informe» valia para una sesion
   caducada, para un permiso y para un servicio caido — o sea, para nada.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER = os.path.join(RAIZ, "backend", "server.py")
TRACKER = os.path.join(RAIZ, "backend", "services", "activity_tracker.py")
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "settings",
                        "UsageReportTab.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. Cada servicio en su propio try ──────────────────────────────────────

def test_el_backup_y_el_tracker_no_comparten_except():
    """CANDADO PRINCIPAL. Es literalmente lo que rompio el informe."""
    src = _leer(SERVER)
    i = src.index("init_backup_service(mongo_url")
    j = src.index("init_activity_tracker(db)")
    assert j > i, "ha cambiado el orden; revisa esta prueba"
    entre = src[i:j]
    assert "except Exception" in entre, (
        "el arranque del servicio de copias y el del tracker de actividad "
        "vuelven a compartir el mismo `try`: si falla el primero, el segundo no "
        "llega a ejecutarse y el informe de uso se cae semanas despues, sin que "
        "nada relacione una cosa con la otra")


def test_los_dos_arranques_tienen_su_propio_except():
    src = _leer(SERVER)
    i = src.index("INICIALIZAR SERVICIOS DE BACKUP Y TRACKING")
    bloque = src[i:i + 2000]
    assert bloque.count("try:") >= 2, "falta separar los arranques"
    assert bloque.count("except Exception") >= 2


def test_un_arranque_fallido_se_registra_como_ERROR_no_como_aviso():
    """Un `warning` entre mil lineas de log no lo lee nadie, y menos el dia que
    pasa: se lee tres semanas despues, buscando otra cosa."""
    src = _leer(SERVER)
    i = src.index("INICIALIZAR SERVICIOS DE BACKUP Y TRACKING")
    bloque = src[i:i + 2000]
    assert "logger.error" in bloque, (
        "el fallo de arranque de un servicio sigue siendo un simple aviso")
    assert bloque.count("logger.error") >= 2


# ─── 2. El informe no depende del arranque ──────────────────────────────────

def test_el_tracker_se_crea_solo_si_no_estaba():
    """CANDADO. Es una consulta con un puntero a la base de datos, no un estado
    que haya que conservar: no hay razon para que un informe de lectura se
    quede caido hasta el proximo despliegue."""
    src = _leer(TRACKER)
    i = src.index("def get_tracker")
    cuerpo = src[i:]
    assert "if activity_tracker is None" in cuerpo, (
        "`get_tracker` vuelve a devolver None a secas: si el arranque se salto "
        "la inicializacion, el informe de uso se cae y no se recupera solo")
    assert "ActivityTracker(get_db())" in cuerpo


def test_si_ni_asi_se_puede_no_revienta():
    """Sin base de datos delante tiene que contestar None, no lanzar: quien
    llama ya sabe dar un 500 con un mensaje decente."""
    src = _leer(TRACKER)
    i = src.index("def get_tracker")
    cuerpo = src[i:]
    assert "except Exception" in cuerpo and "return None" in cuerpo


def test_crear_el_tracker_a_destiempo_no_pierde_datos():
    """Lo unico que se salta es `setup_indexes`, que es velocidad, no
    resultado. Si algun dia los indices hicieran falta para que la consulta sea
    correcta, esta prueba tiene que cambiar A PROPOSITO."""
    src = _leer(TRACKER)
    i = src.index("async def setup_indexes")
    cuerpo = src[i:src.index("async def", i + 10)]
    assert "create_index" in cuerpo
    for prohibido in ("insert_one", "update_one", "delete_many", "drop("):
        assert prohibido not in cuerpo, (
            f"`setup_indexes` hace `{prohibido}`: entonces saltarselo SI cambia "
            "los datos, y crear el tracker a destiempo deja de ser inofensivo")


# ─── 3. El error dice que ha pasado ─────────────────────────────────────────

def test_la_pantalla_distingue_los_motivos():
    """«Error cargando informe» valia para una sesion caducada, para un permiso
    y para un servicio caido. O sea, para nada."""
    src = _leer(PANTALLA)
    assert "response.status === 401" in src, "no distingue la sesion caducada"
    assert "response.status === 403" in src, "no distingue el permiso"
    assert "detail" in src, "no ensenia lo que dice el servidor"


def test_un_fallo_de_red_no_se_confunde_con_un_fallo_del_informe():
    """Confundirlos manda a buscar el problema al sitio equivocado."""
    src = _leer(PANTALLA)
    assert "Failed to fetch" in src
    assert "conectar con el servidor" in src


def test_ya_no_queda_el_mensaje_que_no_decia_nada():
    src = _leer(PANTALLA)
    assert "throw new Error('Error cargando informe')" not in src
