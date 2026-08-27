# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""El contrato de props con `RelacionReview`. Un `()` de más tira la aplicación.

El 24/08 el master pulsó «volcar al presupuesto» y se le quedó la pantalla en
«Algo ha fallado». La causa era de una línea:

    authHeaders={getAuthHeaders()}     ← el RESULTADO (un objeto)
    authHeaders={getAuthHeaders}       ← la FUNCIÓN, que es lo que espera

`RelacionReview` hace `authHeaders()` por dentro, así que al montarse llamaba a
un objeto, lanzaba «authHeaders is not a function» y el ErrorBoundary se comía
la aplicación entera.

NINGÚN CANDADO DE LOS QUE HABÍA PODÍA CAZARLO, y conviene decirlo: los de
pantalla comprueban que el código DICE lo correcto, no que FUNCIONE. Este mira
el contrato entre las dos partes, que es lo máximo que se puede hacer sin abrir
un navegador — para el resto de esta familia de fallos hace falta un Playwright
que pulse el botón.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
REVIEW = os.path.join(COMPONENTES, "RelacionReview.jsx")


def _props_que_se_invocan():
    """Las props que `RelacionReview` LLAMA como función (`prop(`)."""
    with open(REVIEW, encoding="utf-8") as f:
        fuente = f.read()
    firma = re.search(r"export default function RelacionReview\(\{([^}]*)\}", fuente)
    assert firma, "ha cambiado la firma de RelacionReview"
    props = [p.split(":")[0].strip() for p in firma.group(1).split(",") if p.strip()]
    cuerpo = fuente[firma.end():]
    return [p for p in props if re.search(rf"\b{re.escape(p)}\s*\(", cuerpo)]


def _usos():
    """Cada `<RelacionReview …>` del proyecto, con su bloque de props."""
    usos = []
    for nombre in os.listdir(COMPONENTES):
        if not nombre.endswith(".jsx"):
            continue
        ruta = os.path.join(COMPONENTES, nombre)
        with open(ruta, encoding="utf-8") as f:
            fuente = f.read()
        for m in re.finditer(r"<RelacionReview\b(.*?)/>", fuente, re.S):
            usos.append((nombre, m.group(1)))
    return usos


def test_hay_props_que_se_llaman_como_funcion():
    """Si dejaran de llamarse, esta prueba no protegería nada y hay que saberlo."""
    invocadas = _props_que_se_invocan()
    assert "authHeaders" in invocadas, (
        "RelacionReview ya no llama a authHeaders(): revisa si este candado "
        "sigue teniendo sentido.")


def test_nadie_le_pasa_el_RESULTADO_en_vez_de_la_funcion():
    """CANDADO del fallo que tiró la aplicación."""
    invocadas = _props_que_se_invocan()
    usos = _usos()
    assert usos, "no se encuentra ningún uso de <RelacionReview>"
    fallos = []
    for fichero, bloque in usos:
        for prop in invocadas:
            # `prop={algo()}` — con paréntesis de llamada y sin flecha detrás.
            m = re.search(rf"{re.escape(prop)}=\{{\s*([A-Za-z_$][\w$.]*)\(\s*\)\s*\}}", bloque)
            if m:
                fallos.append(f"{fichero}: {prop}={{{m.group(1)}()}}")
    assert not fallos, (
        "se está pasando el RESULTADO en vez de la función, y RelacionReview la "
        "llama por dentro: revienta al montarse y el ErrorBoundary se lleva la "
        "aplicación. " + " · ".join(fallos))


def _props_obligatorias():
    """Las que se llaman SIN comprobar antes que existan.

    No todas las que se invocan son obligatorias: los `on*` son avisos
    opcionales y el componente los protege (`if (onExportDesmontada) …`), así
    que no pasarlos es perfectamente válido. La que no se puede omitir es la
    que se llama a pelo — hoy, `authHeaders()` dentro de un efecto.
    """
    with open(REVIEW, encoding="utf-8") as f:
        fuente = f.read()
    obligatorias = []
    for prop in _props_que_se_invocan():
        protegida = re.search(
            rf"(if\s*\(\s*{re.escape(prop)}\b|{re.escape(prop)}\s*&&|{re.escape(prop)}\?\.\()",
            fuente)
        if not protegida:
            obligatorias.append(prop)
    return obligatorias


def test_todos_los_usos_pasan_las_props_que_NO_se_protegen():
    """Pasar `undefined` a una prop que se llama sin protección es el mismo
    fallo por el otro lado: revienta al montarse."""
    obligatorias = _props_obligatorias()
    assert obligatorias, (
        "ninguna prop se llama ya sin protección: revisa si este candado sigue "
        "teniendo sentido.")
    fallos = []
    for fichero, bloque in _usos():
        for prop in obligatorias:
            if not re.search(rf"\b{re.escape(prop)}=", bloque):
                fallos.append(f"{fichero}: falta {prop}")
    assert not fallos, " · ".join(fallos)
