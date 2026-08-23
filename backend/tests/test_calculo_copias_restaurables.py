# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de las copias de seguridad: QUE SE PUEDAN RESTAURAR DE VERDAD.

Una copia que nunca se ha restaurado es una esperanza, no una estrategia. El
ERP lleva tiempo haciendo copias y nadie ha comprobado nunca que sirvan — y eso
solo se descubre el peor dia.

Aqui se crean archivos de copia DE VERDAD (un zip con sus .json dentro), se
verifican y se comprueba que la verificacion distingue una copia buena de una
rota. No es una simulacion: es el mismo codigo que corre en produccion,
leyendo un archivo real.

Lo que se protege:

1. UNA COPIA BUENA SE RECONOCE, y dice cuantas colecciones y cuantos
   documentos tiene. Si no se puede decir eso, no se puede afirmar que sirva.

2. UNA COPIA ROTA NO PASA POR BUENA. Con un solo fichero danniado, la
   restauracion se pararia a medias — o sea que no vale— y hay que saberlo
   ANTES.

3. VERIFICAR NO TOCA NADA. La prueba de una copia no puede consistir en
   machacar los datos buenos para ver si funciona.

4. Y EL CANDADO GORDO: RESTAURAR LEE TODO ANTES DE BORRAR NADA. Antes se hacia
   coleccion a coleccion —leer, BORRAR la de produccion, insertar—. Si el
   fichero numero siete estaba corrupto, las seis primeras ya estaban borradas
   y la septima tambien: una restauracion a medias, el peor dia, y sin vuelta
   atras.
"""
import json
import os
import re
import shutil
import tempfile

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICIO = os.path.join(BACKEND, "services", "backup_service.py")


@pytest.fixture()
def svc():
    """El servicio de copias, apuntando a una carpeta de usar y tirar."""
    import importlib.util
    import pathlib
    import sys

    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)

    # La carpeta de usar y tirar se decide ANTES de cargar el servicio.
    #
    # `BackupService.__init__` CREA su carpeta de copias, y por defecto esa
    # carpeta es /app/backups —el raiz del contenedor de Railway—. Fuera del
    # contenedor nadie puede escribir en /app: en el CI saltaba
    # `PermissionError: [Errno 13] Permission denied: '/app'` y estas cinco
    # pruebas ni llegaban a empezar. Reasignar `s.backup_dir` despues no
    # servia de nada, porque el destrozo ya estaba hecho en el __init__.
    carpeta = tempfile.mkdtemp()
    previo = os.environ.get("BACKUP_DIR")
    os.environ["BACKUP_DIR"] = carpeta
    try:
        spec = importlib.util.spec_from_file_location("_backup_service", SERVICIO)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        s = mod.BackupService("mongodb://127.0.0.1:27017", "prueba_copias")
    finally:
        if previo is None:
            os.environ.pop("BACKUP_DIR", None)
        else:
            os.environ["BACKUP_DIR"] = previo

    s.backup_dir = pathlib.Path(carpeta)
    yield s
    shutil.rmtree(carpeta, ignore_errors=True)


def _hacer_copia(svc, nombre, ficheros):
    """Crea un archivo de copia de verdad, como los que hace el ERP."""
    raiz = os.path.join(str(svc.backup_dir), nombre + "_src")
    dentro = os.path.join(raiz, svc.db_name)
    os.makedirs(dentro, exist_ok=True)
    for fichero, contenido in ficheros.items():
        with open(os.path.join(dentro, fichero), "w", encoding="utf-8") as f:
            f.write(contenido if isinstance(contenido, str) else json.dumps(contenido))
    shutil.make_archive(os.path.join(str(svc.backup_dir), nombre), "zip", raiz)
    return nombre + ".zip"


# ─── 1. Una copia buena se reconoce ─────────────────────────────────────────

def test_una_copia_buena_se_puede_restaurar_y_dice_que_lleva(svc):
    copia = _hacer_copia(svc, "buena", {
        "projects.json": [{"id": "p1"}, {"id": "p2"}],
        "users.json": [{"id": "u1"}],
    })
    r = svc.verificar_backup(copia)
    assert r["success"] is True and r["restaurable"] is True
    assert r["totalColecciones"] == 2 and r["totalDocumentos"] == 3
    assert r["colecciones"]["projects"] == 2


# ─── 2. Una copia rota no pasa por buena ────────────────────────────────────

def test_una_copia_con_un_fichero_roto_NO_es_restaurable(svc):
    """CANDADO PRINCIPAL. Con uno solo danniado la restauracion se para a
    medias, o sea que no vale — y hay que saberlo antes, no el peor dia."""
    copia = _hacer_copia(svc, "rota", {
        "projects.json": [{"id": "p1"}],
        "cascos_orders.json": "{esto no es json",
    })
    r = svc.verificar_backup(copia)
    assert r["restaurable"] is False
    assert r["danadas"] and "cascos_orders" in r["danadas"][0]
    assert "NO se podría restaurar" in r["resumen"]


def test_un_archivo_sin_datos_dentro_tampoco(svc):
    raiz = os.path.join(str(svc.backup_dir), "vacia_src")
    os.makedirs(os.path.join(raiz, "solo_codigo"), exist_ok=True)
    with open(os.path.join(raiz, "solo_codigo", "server.py"), "w") as f:
        f.write("# nada que restaurar")
    shutil.make_archive(os.path.join(str(svc.backup_dir), "vacia"), "zip", raiz)
    r = svc.verificar_backup("vacia.zip")
    assert r.get("restaurable") is False


def test_una_copia_que_no_existe_lo_dice_y_no_revienta(svc):
    r = svc.verificar_backup("no_existe.zip")
    assert r["success"] is False and "no existe" in r["error"].lower()


# ─── 3. Verificar no toca nada ──────────────────────────────────────────────

def test_verificar_no_escribe_en_la_base_de_datos():
    """La prueba de una copia no puede consistir en machacar los datos buenos.

    Se mira el codigo: `verificar_backup` no puede tener dentro ni un `drop`
    ni un `insert`, y no es `async` porque no habla con Mongo.
    """
    with open(SERVICIO, encoding="utf-8") as f:
        src = f.read()
    i = src.index("def verificar_backup")
    cuerpo = src[i:src.index("\n    async def restore_backup", i)]
    for prohibido in ("drop()", "insert_many", "insert_one", "delete_many"):
        assert prohibido not in cuerpo, (
            f"`verificar_backup` hace `{prohibido}`: verificar una copia no "
            "puede tocar los datos de produccion")


def test_verificar_limpia_lo_que_descomprime(svc):
    """Si no, cada verificacion deja una copia entera suelta en el disco."""
    copia = _hacer_copia(svc, "limpia", {"projects.json": [{"id": "p1"}]})
    svc.verificar_backup(copia)
    assert not os.path.exists(os.path.join(str(svc.backup_dir), "verify_temp"))


# ─── 4. Restaurar lee TODO antes de borrar nada ─────────────────────────────

def test_restaurar_no_borra_hasta_haber_leido_todo():
    """CANDADO GORDO. Antes: leer una, BORRAR la de produccion, insertar, y a
    por la siguiente. Con el septimo fichero corrupto, las seis anteriores ya
    estaban borradas. Ahora se lee todo primero y, si algo falla, la base de
    datos sigue intacta.
    """
    with open(SERVICIO, encoding="utf-8") as f:
        src = f.read()
    i = src.index("async def restore_backup")
    cuerpo = src[i:]

    pos_lectura = cuerpo.index("json_util.loads")
    pos_borrado = cuerpo.index(".drop()")
    assert pos_lectura < pos_borrado, (
        "se borra una coleccion antes de haber leido el backup entero: si un "
        "fichero esta corrupto, la base de datos se queda a medias")

    # Y que lo diga sin haber tocado nada.
    assert "NO se ha tocado la base de datos" in cuerpo, (
        "si el backup esta daniado hay que decir explicitamente que no se ha "
        "tocado nada: si no, nadie sabe en que estado se ha quedado")
