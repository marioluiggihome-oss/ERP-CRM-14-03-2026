# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de la cabecera de autenticacion del proveedor (IA 2 / Manus).

Estas pruebas no comprueban un calculo: comprueban que la clave del proveedor
viaja SIEMPRE con el nombre de cabecera que ese proveedor entiende.

Que paso el 07/08: el nombre estaba copiado a mano en cuatro sitios y dos lo
tenian mal, con `Authorization: Bearer`, que el proveedor rechaza siempre:

  1. `/api/ai-engine/diagnostics` devolvia 401 aunque la clave fuese correcta.
     Es la pantalla a la que se va uno a mirar por que IA 2 no responde, o sea
     que mentia justo cuando mas falta hacia la verdad.
  2. El proxy de assets se comia un 401 al descargar imagenes alojadas en el
     host de la API, y la imagen salia rota sin explicacion.

Los dos sitios correctos estaban en `engine_core.py`. Nadie los toco: el fallo
es de copiar el literal en vez de tener un solo sitio donde se escribe.

Ahora solo se escribe en `AIConfig.provider_auth_headers()`. Si alguien vuelve a
poner el literal a mano —o vuelve al esquema Bearer— estas pruebas se ponen en
rojo y el CI corta.

OJO: `Authorization: Bearer` SI es correcto para Replicate (IA 3, Flux) y para
el JWT propio del ERP. Lo que se prohibe es usarlo con la clave del proveedor.
"""
import ast
import importlib.util
import os
import re

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CABECERA = "x-manus-api-key"

# Ficheros que tratan con la clave del proveedor.
FICHEROS = [
    os.path.join(BACKEND, "routes", "ai_engine.py"),
    os.path.join(BACKEND, "services", "luiggi_ai", "engine_core.py"),
    os.path.join(BACKEND, "services", "luiggi_ai", "config.py"),
]


@pytest.fixture()
def config():
    """Carga `AIConfig` de su fichero, sin arrastrar el paquete entero."""
    ruta = os.path.join(BACKEND, "services", "luiggi_ai", "config.py")
    spec = importlib.util.spec_from_file_location("_cfg_proveedor", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AIConfig


def test_la_cabecera_del_proveedor_es_la_suya_y_no_bearer(config):
    """CANDADO: la clave viaja en `x-manus-api-key`, nunca en `Authorization`."""
    cabeceras = config(provider_api_key="CLAVE-DE-PRUEBA").provider_auth_headers()

    assert cabeceras == {CABECERA: "CLAVE-DE-PRUEBA"}, (
        "La clave del proveedor debe viajar en la cabecera propia del proveedor. "
        f"Con otro esquema responde 401 aunque la clave sea buena. Recibido: {cabeceras}"
    )
    assert "Authorization" not in cabeceras, (
        "`Authorization: Bearer` es el esquema equivocado para este proveedor: "
        "fue la causa de los 401 falsos del diagnostico y de las imagenes rotas."
    )


def test_la_cabecera_arrastra_la_clave_configurada(config):
    """Si no hay clave, la cabecera va vacia — no se inventa ni se omite."""
    assert config(provider_api_key="").provider_auth_headers() == {CABECERA: ""}


@pytest.mark.parametrize("ruta", FICHEROS, ids=lambda r: os.path.basename(r))
def test_nadie_manda_la_clave_del_proveedor_con_bearer(ruta):
    """CANDADO: prohibido volver a juntar `Bearer` con la clave del proveedor.

    Replicate (IA 3) y el JWT del ERP siguen pudiendo usar Bearer: aqui solo se
    mira que no se use con la clave de ESTE proveedor.
    """
    with open(ruta, encoding="utf-8") as f:
        lineas = f.read().splitlines()

    culpables = [
        (n, linea.strip())
        for n, linea in enumerate(lineas, 1)
        if "Bearer" in linea
        and re.search(r"provider_api_key|manus_key", linea)
    ]

    assert not culpables, (
        "La clave del proveedor se esta mandando con `Authorization: Bearer`, "
        f"que devuelve 401 siempre. Usa `config.provider_auth_headers()`. En {ruta}: "
        + "; ".join(f"linea {n}: {t}" for n, t in culpables)
    )


def _literales_de_cabecera(ruta):
    """Lineas donde el nombre de la cabecera se usa COMO VALOR en el codigo.

    Se mira el arbol de sintaxis, no el texto: asi la documentacion que la
    nombra (el docstring de `engine_core.py` la explica) no cuenta como copia.
    Solo salta si alguien vuelve a escribir el literal para usarlo.
    """
    with open(ruta, encoding="utf-8") as f:
        arbol = ast.parse(f.read())

    return [
        nodo.lineno
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant) and nodo.value == CABECERA
    ]


@pytest.mark.parametrize("ruta", FICHEROS, ids=lambda r: os.path.basename(r))
def test_el_nombre_de_la_cabecera_solo_se_escribe_en_un_sitio(ruta):
    """El literal vive solo en `config.py`; el resto pide la cabecera hecha.

    Es el fallo de origen: cuatro copias a mano, dos mal. Una sola fuente hace
    imposible que vuelvan a divergir.
    """
    lineas = _literales_de_cabecera(ruta)

    if os.path.basename(ruta) == "config.py":
        assert lineas, (
            "config.py debe seguir siendo el sitio donde se define la cabecera."
        )
        return

    assert not lineas, (
        f"El nombre de la cabecera vuelve a estar escrito a mano en {ruta} "
        f"(lineas {lineas}). Usa `config.provider_auth_headers()`: cuatro copias "
        "a mano fue justo lo que dejo dos de ellas mal."
    )
