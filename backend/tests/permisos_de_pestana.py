# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""EJECUTA `canAccessTab` DE VERDAD, EN NODE.

POR QUÉ EXISTE (04/09/2026). Hasta ahora cada candado de puerta buscaba en
`App.js` el texto de su guardia: `esCooperativista(state.currentUser)`,
`isMaster`, y así. Eso protegía bien mientras cada pestaña llevaba su `if`
escrito a mano, pero el 04/09 los permisos se centralizaron en
`frontend/src/modulePermissions.js` y `App.js` pasó a preguntar `canOpenTab(...)`
para todas. Seis candados se pusieron rojos DE GOLPE sin que ninguna puerta
hubiera cambiado — lo comprobé leyendo `canAccessTab` función a función.

Un candado que se pone rojo porque el código está escrito de otra manera, y no
porque la promesa se haya roto, enseña a la gente a ignorarlo. Y el siguiente
que se ponga rojo de verdad se ignorará igual.

Así que dejan de leer texto y pasan a EJECUTAR la regla con usuarios de
mentira: se le pregunta a `canAccessTab` si este socio entra en COOP, si este
suscriptor entra en carpinter. Eso sigue siendo verdad se escriba como se
escriba, y es lo que de verdad hay que proteger.

LO QUE ESTO NO SUSTITUYE: el cierre del SERVIDOR. Un menú es una sugerencia
(CLAUDE.md, regla 20). Los candados del backend siguen donde estaban.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
MODULO = os.path.join(SRC, "modulePermissions.js")
PLATAFORMAS = os.path.join(SRC, "plataformas.js")
PRESUPUESTADOR = os.path.join(SRC, "presupuestador.js")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _sin_modulos(fuente):
    """Quita `import`/`export` para poder pegar los tres ficheros en un script.

    No se toca nada más: el cuerpo de las funciones es el de producción, que es
    justo el motivo de hacer esto en node y no reescribir la lógica en Python.
    """
    fuente = re.sub(r"^\s*import[^;]+;\s*$", "", fuente, flags=re.M)
    return re.sub(r"^export\s+", "", fuente, flags=re.M)


def puertas(usuarios, pestanas, settings=None):
    """Para cada usuario, qué pestañas le abre `canAccessTab`.

    Devuelve `{nombre_del_usuario: [pestañas que puede abrir]}`.
    """
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar los permisos de verdad")
    js = "\n".join([
        _sin_modulos(_lee(PLATAFORMAS)),
        _sin_modulos(_lee(PRESUPUESTADOR)),
        # `presupuestador.js` y `plataformas.js` exportan los dos un `NOMBRES`.
        # Pegados en un mismo ámbito, el segundo `const NOMBRES` revienta con
        # «Identifier has already been declared» y la prueba moriría por un
        # choque de nombres, no por un permiso.
        "",
        _sin_modulos(_lee(MODULO))
            .replace("puedeEntrarPresupuestador", "puedeEntrar"),
        "const USUARIOS = %s;" % json.dumps(usuarios),
        "const PESTANAS = %s;" % json.dumps(list(pestanas)),
        "const AJUSTES = %s;" % json.dumps(settings or {}),
        "const salida = {};",
        "for (const [nombre, u] of Object.entries(USUARIOS)) {",
        "  salida[nombre] = PESTANAS.filter(t => canAccessTab(t, u, AJUSTES));",
        "}",
        "console.log(JSON.stringify(salida));",
    ])
    # Los dos `NOMBRES` chocan; se le cambia el nombre al segundo antes de nada.
    js = js.replace("const NOMBRES = {", "const NOMBRES_1 = {", 1)
    js = js.replace("const NOMBRES = {", "const NOMBRES_2 = {", 1)
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, (
        f"la matriz de permisos no se ejecuta: {r.stderr[-500:]}")
    return json.loads(r.stdout)


# Usuarios de mentira, uno por cada puerta que hay que vigilar.
MASTER = {"isMaster": True}
ADMIN = {"isAdmin": True}
SOCIO_MONTADOR = {"esCooperativistaMontador": True}
SOCIO_COMERCIAL = {"esCooperativistaComercial": True}
SUSCRIPTOR = {"plataforma": "carpinter", "isRepresentative": True}
COMERCIAL_EN_NOMINA = {"isRepresentative": True}
GERENTE = {"isGerente": True}
