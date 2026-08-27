# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: NADA opcional puede impedir que el ERP arranque.

14/08/2026, el master: «mira a ver que está caída la web y no puedo entrar».

`routes/fabrica.py` sembraba unas fábricas de ejemplo A NIVEL DE MÓDULO:

    try:
        loop = asyncio.get_event_loop()
        ...
        loop.run_until_complete(seed_default_factories())
    except RuntimeError:
        pass

O sea una consulta a Mongo DURANTE EL IMPORT de la ruta. Y el `except` solo
recogía `RuntimeError` —lo que lanza asyncio— y no lo que lanza la base de
datos, que es `ServerSelectionTimeoutError`.

Si Mongo tarda en levantar o está un momento inaccesible cuando arranca el
contenedor —que es justo cuando arranca todo a la vez—, la consulta revienta,
el import de `routes.fabrica` revienta, `server.py` no llega a construir la app
y NO HAY WEB. En el log pone «factories», así que además se busca donde no es.

La regla que se protege:

    Sembrar datos de ejemplo, calentar cachés, avisar a un servicio externo…
    todo eso es OPCIONAL. Ninguna de esas cosas puede decidir si el ERP
    arranca. Si fallan, se anotan en el log y el ERP arranca igual.

Se comprueba de dos formas, porque una sola no basta:
 1. Que el patrón no vuelva al código (nadie llama a la base al importar).
 2. Que la app se construye ENTERA con la base de datos caída de verdad.
"""
import ast
import os
import subprocess
import sys

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTAS = os.path.join(BACKEND, "routes")
SERVICIOS = os.path.join(BACKEND, "services")


def _ficheros_py(carpeta):
    for raiz, _, ficheros in os.walk(carpeta):
        for f in ficheros:
            if f.endswith(".py"):
                yield os.path.join(raiz, f)


# ─── 1. Nadie llama a la base de datos al importar ──────────────────────────

def test_ningun_modulo_ejecuta_corrutinas_al_importarse():
    """CANDADO PRINCIPAL. `run_until_complete` / `asyncio.run` a nivel de módulo
    es una llamada bloqueante en el momento más frágil del arranque."""
    malos = []
    for ruta in list(_ficheros_py(RUTAS)) + list(_ficheros_py(SERVICIOS)):
        with open(ruta, encoding="utf-8") as f:
            fuente = f.read()
        try:
            arbol = ast.parse(fuente)
        except SyntaxError:
            continue
        for nodo in arbol.body:              # SOLO el nivel de módulo
            for sub in ast.walk(nodo):
                if not isinstance(sub, ast.Call):
                    continue
                nombre = ast.unparse(sub.func) if hasattr(ast, "unparse") else ""
                if nombre.endswith("run_until_complete") or nombre == "asyncio.run":
                    malos.append(f"{os.path.relpath(ruta, BACKEND)}:{sub.lineno}")
    assert not malos, (
        "vuelve a ejecutarse una corrutina al importar el módulo, y eso se hace "
        "antes de que exista la app: si la base de datos tarda en levantar, el "
        "ERP no arranca y el log habla de otra cosa. Muévelo al `startup` de "
        "server.py. Sitios: " + ", ".join(malos))


def test_la_siembra_de_fabricas_no_puede_tumbar_el_arranque():
    """Y donde estaba, que quede dicho por qué se fue."""
    ruta = os.path.join(RUTAS, "fabrica.py")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    assert "async def sembrar_fabricas_por_defecto" in fuente, (
        "ya no existe la siembra envuelta: o se ha vuelto a hacer al importar, "
        "o se ha perdido")
    i = fuente.index("async def sembrar_fabricas_por_defecto")
    cuerpo = fuente[i:i + 700]
    assert "except Exception" in cuerpo, (
        "la siembra vuelve a dejar escapar la excepción de la base de datos: "
        "un Mongo lento volvería a impedir que arranque el ERP")


def test_server_siembra_las_fabricas_al_arrancar():
    """Se movió, no se borró: las fábricas por defecto siguen creándose."""
    with open(os.path.join(BACKEND, "server.py"), encoding="utf-8") as f:
        fuente = f.read()
    i = fuente.index("async def startup_event")
    assert "sembrar_fabricas_por_defecto" in fuente[i:i + 1500], (
        "se quitó la siembra del import y no se puso en el arranque: las "
        "fábricas por defecto ya no se crean nunca")


# ─── 2. Y se comprueba de verdad, con la base caída ─────────────────────────

def test_la_app_se_construye_entera_con_la_base_de_datos_caida():
    """CANDADO DURO. No se mira el código: se ARRANCA apuntando a un puerto
    donde no hay nada y se cuenta cuántos endpoints quedan en pie."""
    guion = (
        "import warnings; warnings.filterwarnings('ignore')\n"
        "import server\n"
        "print('ENDPOINTS', len(server.app.openapi().get('paths', {})))\n"
    )
    entorno = dict(os.environ)
    entorno.update({
        "JWT_SECRET": "candado-de-arranque-solo-para-esta-prueba-0123456789abcdef",
        "MONGO_URL": "mongodb://127.0.0.1:59999",   # aquí no escucha nadie
        "DB_NAME": "no_existe",
    })
    res = subprocess.run([sys.executable, "-c", guion], cwd=BACKEND, env=entorno,
                         capture_output=True, text=True, timeout=420)
    assert res.returncode == 0, (
        "el ERP NO ARRANCA con la base de datos caída. Algo del arranque la "
        f"necesita y no debería:\n{res.stderr[-2500:]}")
    linea = [l for l in res.stdout.splitlines() if l.startswith("ENDPOINTS")]
    assert linea, f"la app no llegó a construirse:\n{res.stdout[-800:]}\n{res.stderr[-1500:]}"
    n = int(linea[0].split()[1])
    assert n > 300, (
        f"la app arranca pero solo con {n} endpoints: se han caído routers por "
        f"el camino y el ERP quedaría a medias, que es peor que no arrancar "
        f"porque parece que funciona")
