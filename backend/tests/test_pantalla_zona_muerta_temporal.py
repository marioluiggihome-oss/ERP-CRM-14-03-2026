# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UNA CONSTANTE USADA ANTES DE DECLARARLA DEJA LA PANTALLA EN NEGRO.

El master, 30/08: «da fallo mi área», con «ERROR AL CARGAR EL MÓDULO — Cannot
access 'z' before initialization».

QUÉ PASÓ. Al reestructurar COOP, la lista de pestañas quedó ARRIBA y la función
que decide quién ve cada una, ABAJO:

    const PESTANAS = [ { id: 'usuarios', ve: esMaster }, ... ];   // línea 50
    const esMaster = (u) => ...;                                  // línea 70

`ve: esMaster` es una referencia DIRECTA —no está dentro de otra función—, así
que se lee al evaluar el módulo. Con `const`, eso es la zona muerta temporal:
el navegador lanza `ReferenceError` y NO carga el módulo. Minificado, `esMaster`
se llama `z`, y por eso el mensaje no dice nada.

POR QUÉ NO LO CAZÓ NADA. `CI=true npx craco build` compiló SIN UN AVISO: no es
un error de sintaxis ni de tipos, es de orden de evaluación, y solo se ve al
EJECUTAR. Es el mismo agujero que la regla 23 (hooks bajo un `return`): el build
en verde y la pantalla en negro.

CÓMO SE COMPRUEBA. Ejecutando de verdad la parte de módulo de cada pantalla
—las constantes de arriba, sin JSX— en node. Leerlo a ojo no sirve: el orden se
rompe con mover diez líneas.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

from jsx_limpio import sin_comentarios as _limpia_jsx

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")

# El patrón exacto que rompió: una lista/objeto de módulo que nombra una función
# declarada más abajo. Se buscan las pantallas donde una constante de módulo
# referencia otra constante de módulo declarada DESPUÉS.
DECL = re.compile(r"^const (\w+) = ", re.M)


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _sin_comentarios(cuerpo: str) -> str:
    """Sin comentarios: los ficheros EXPLICAN el fallo citándolo, y el
    reconocedor se creía la explicación. Ya van cuatro veces en el proyecto."""
    return _limpia_jsx(cuerpo)


def _constantes_de_modulo(cuerpo: str):
    """(nombre, posición) de cada `const X = ...` en el nivel del módulo."""
    return [(m.group(1), m.start()) for m in DECL.finditer(cuerpo)]


def test_NINGUNA_CONSTANTE_SE_USA_ANTES_DE_DECLARARSE():
    """El barrido de las 92 pantallas.

    Solo se mira el nivel de módulo (`^const`, sin sangrar) y solo hasta el
    primer `export default`, que es lo que se evalúa al cargar. Dentro de un
    componente el orden no importa: cuando corre, el módulo ya está entero.
    """
    revisadas = 0
    for nombre in sorted(os.listdir(COMPONENTES)):
        if not nombre.endswith(".jsx"):
            continue
        crudo = _lee(os.path.join(COMPONENTES, nombre))
        corte = crudo.find("export default")
        cabeza = _sin_comentarios(crudo[:corte if corte > 0 else len(crudo)])
        constantes = _constantes_de_modulo(cabeza)
        if len(constantes) < 2:
            continue
        revisadas += 1
        for i, (nom, pos) in enumerate(constantes):
            # Lo declarado DESPUÉS de esta constante no se puede nombrar aquí.
            fin = constantes[i + 1][1] if i + 1 < len(constantes) else len(cabeza)
            cuerpo_const = cabeza[pos:fin]
            for posterior, pos_post in constantes[i + 1:]:
                # Dentro de una función flecha sí vale: se ejecuta más tarde.
                for uso in re.finditer(rf"\b{re.escape(posterior)}\b", cuerpo_const):
                    antes = cuerpo_const[:uso.start()]
                    if "=>" in antes.split("\n")[-1] or "function" in antes.split("\n")[-1]:
                        continue
                    # `ve: esMaster` — referencia directa, sin envolver.
                    linea = cuerpo_const[:uso.end()].split("\n")[-1]
                    if re.search(rf":\s*{re.escape(posterior)}\s*[,}}]", linea):
                        pytest.fail(
                            f"{nombre}: `{nom}` nombra a `{posterior}`, que se "
                            f"declara DESPUÉS. Al cargar el módulo eso es "
                            f"«Cannot access '{posterior}' before "
                            f"initialization» y la pantalla NO carga. Línea: "
                            f"{linea.strip()[:90]}")
    assert revisadas >= 10, (
        f"solo se han revisado {revisadas} pantallas: el reconocedor no está "
        "encontrando las constantes de módulo y el barrido pasa por vacío")


def test_EL_MODULO_DE_COOP_SE_EVALUA_DE_VERDAD():
    """No se lee: se EJECUTA. Es la única forma de estar seguro del orden.

    Y de paso se comprueba lo que reparte: el master ve todas las pestañas y un
    socio ve solo la suya. Si esto se rompe, o el socio pierde su área o ve la
    liquidación.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    crudo = _lee(os.path.join(COMPONENTES, "CoopPanel.jsx"))
    ini = crudo.index("const esMaster")
    trozo = crudo[ini:crudo.index("export default function")]
    trozo = re.sub(r"icono: \w+", "icono: null", trozo)
    trozo = trozo.replace("ve: (u) => esCooperativista(u)", "ve: () => true")
    trozo = trozo.replace("u?.canAccessMontajes || u?.isMontador", "false")
    trozo = trozo.replace("u?.canAccessInvoices !== false", "false")
    guion = trozo + """
console.log(JSON.stringify({
  ids: PESTANAS.map(p => p.id),
  master: PESTANAS.filter(p => p.ve({ isMaster: true })).map(p => p.id),
  socio: PESTANAS.filter(p => p.ve({})).map(p => p.id),
}));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False,
                                     encoding="utf-8") as f:
        f.write(guion)
        ruta = f.name
    try:
        salida = subprocess.run([node, ruta], capture_output=True, text=True,
                                timeout=60)
    finally:
        os.unlink(ruta)
    assert salida.returncode == 0, (
        "el módulo de COOP no se puede evaluar, así que la pantalla no carga: "
        f"{salida.stderr.strip()[:200]}")
    d = json.loads(salida.stdout)
    assert d["ids"][0] == "miarea", "«Mi área» ha dejado de ir la primera"
    assert "liquidar" in d["master"], "el master ha perdido la liquidación"
    assert d["socio"] == ["miarea"], (
        f"un socio ve {d['socio']}: solo puede ver su área")
