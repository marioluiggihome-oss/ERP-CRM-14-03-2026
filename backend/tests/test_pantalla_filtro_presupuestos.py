# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
BUSCAR ENTRE LOS PRESUPUESTOS GUARDADOS.

El master, 07/09/2026: «pon un filtro en presupuestos de cocina montada, para
buscar mejor los documentos».

LA LISTA CRECE POR OBRA, NO POR CLIENTE. En la pantalla que lo destapó había
SEIS presupuestos del mismo «DESI / DOMUS +», y lo único que los distingue es
la REFERENCIA: «APARTAMENTO 001 / 002 / 003», y de esos, tres con «/ ELECTROS».
Por eso se busca en el cliente Y en la referencia: filtrando solo por cliente,
los seis siguen ahí y no se ha avanzado nada.

TRES DECISIONES QUE NO SON DE ADORNO
────────────────────────────────────
· SIN TILDES Y SIN MAYÚSCULAS (`norm`, el mismo que ya usa el buscador de
  muebles): quien teclea «domus» tiene que encontrar «DOMUS».
· POR PALABRAS SUELTAS, no por la frase entera: «003 domus» tiene que
  encontrar «DESI / DOMUS + · APARTAMENTO 003» aunque el 003 vaya después.
  Buscando la cadena tal cual no daría nada y parecería que el documento no
  está.
· «NO HAY NINGUNO» Y «NINGUNO COINCIDE» SON COSAS DISTINTAS. Con el mismo
  texto para las dos, quien busca mal cree que ha perdido el presupuesto.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _lee():
    with open(CM3, "r", encoding="utf-8") as f:
        return f.read()


def _filtra(guardados, termino):
    """EJECUTA el filtro de verdad, sacado del fichero, en node."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar el filtro de verdad")
    src = _lee()
    i = src.index("const norm = (s) =>")
    norm = src[i:src.index(";", src.index("toLowerCase()", i)) + 1]
    j = src.index("const guardadosFiltrados = useMemo(() => {")
    cuerpo = src[j:src.index("}, [guardados, filtroGuardados]);", j)]
    cuerpo = cuerpo.replace("const guardadosFiltrados = useMemo(() => {",
                            "const filtrar = (guardados, filtroGuardados) => {")
    js = (norm + "\n" + cuerpo + "};\n"
          + f"console.log(JSON.stringify(filtrar({json.dumps(guardados)}, "
          + f"{json.dumps(termino)}).map(o => o.id)));")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node falló:\n{r.stderr[-2000:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


# Los seis del mismo cliente que salían en la pantalla del master.
GUARDADOS = [
    {"id": "1", "cliente": "DESI / DOMUS +", "ref": "APARTAMENTO 003 / ELECTROS", "createdAt": "2026-09-07"},
    {"id": "2", "cliente": "DESI / DOMUS +", "ref": "APARTAMENTO 002 / ELECTROS", "createdAt": "2026-09-07"},
    {"id": "3", "cliente": "DESI / DOMUS +", "ref": "APARTAMENTO 001 / ELECTROS", "createdAt": "2026-09-07"},
    {"id": "4", "cliente": "DESI / DOMUS +", "ref": "APARTAMENTO 003", "createdAt": "2026-09-07"},
    {"id": "5", "cliente": "DESI / DOMUS +", "ref": "APARTAMENTO 002", "createdAt": "2026-09-07"},
    {"id": "6", "cliente": "DESI / DOMUS +", "ref": "APARTAMENTO 001", "createdAt": "2026-09-07"},
    {"id": "7", "cliente": "PRUEBAS MARIO", "ref": "PRUEBA ALV IMPORTAR", "createdAt": "2026-08-30"},
    {"id": "8", "cliente": "MARIO", "ref": "Prueba 001", "createdAt": "2026-08-30"},
]


def test_sin_termino_salen_TODOS():
    assert _filtra(GUARDADOS, "") == [o["id"] for o in GUARDADOS]
    assert _filtra(GUARDADOS, "   ") == [o["id"] for o in GUARDADOS]


def test_se_busca_por_REFERENCIA_que_es_lo_que_los_distingue():
    """Seis presupuestos del mismo cliente: por cliente no se avanza nada."""
    assert _filtra(GUARDADOS, "003") == ["1", "4"]
    assert _filtra(GUARDADOS, "electros") == ["1", "2", "3"]


def test_se_busca_tambien_por_CLIENTE():
    assert _filtra(GUARDADOS, "domus") == ["1", "2", "3", "4", "5", "6"]


def test_NO_distingue_mayusculas_ni_tildes():
    assert _filtra(GUARDADOS, "DOMUS") == _filtra(GUARDADOS, "domus")
    con_tilde = [{"id": "x", "cliente": "JOSÉ", "ref": "OBRA", "createdAt": ""}]
    assert _filtra(con_tilde, "jose") == ["x"], (
        "escribir «jose» no encuentra a «JOSÉ»")


def test_busca_por_PALABRAS_SUELTAS_y_en_cualquier_orden():
    """«003 domus» tiene que encontrarlo aunque el 003 vaya después. Buscando
    la frase entera no daría nada y parecería que el documento no está."""
    assert _filtra(GUARDADOS, "003 domus") == ["1", "4"]
    assert _filtra(GUARDADOS, "domus 003") == ["1", "4"]
    assert _filtra(GUARDADOS, "electros 001") == ["3"]


def test_se_puede_buscar_por_FECHA():
    """Es como se busca un presupuesto del que solo se recuerda cuándo se
    hizo."""
    assert _filtra(GUARDADOS, "2026-08") == ["7", "8"]


def test_lo_que_no_esta_no_aparece():
    assert _filtra(GUARDADOS, "no existe esto") == []


# ─── LA PANTALLA ─────────────────────────────────────────────────────────────

def test_el_buscador_esta_en_el_modal():
    src = _lee()
    assert 'data-testid="cm3-filtro-guardados"' in src


def test_se_dice_CUANTOS_se_estan_viendo_de_cuantos_hay():
    """Sin el total, una búsqueda que deja tres a la vista parece la lista
    entera y nadie sabe que está filtrando."""
    src = _lee()
    assert 'data-testid="cm3-cuenta-guardados"' in src
    i = src.index('data-testid="cm3-cuenta-guardados"')
    assert "guardadosFiltrados.length} de {guardados.length}" in src[i:i + 300]


def test_NINGUNO_COINCIDE_no_se_dice_igual_que_NO_HAY_NINGUNO():
    """Con el mismo texto para las dos, quien busca mal cree que ha perdido el
    presupuesto."""
    src = _lee()
    assert "Todavía no hay ninguno guardado." in src
    assert "coincide con" in src, (
        "no se distingue «no hay ninguno» de «ninguno coincide con lo que "
        "has escrito»")
    assert "Ver todos" in src, "no hay forma de quitar el filtro desde el vacío"


def test_el_filtro_arranca_LIMPIO_cada_vez_que_se_abre():
    """Si se quedara el de la vez anterior, la lista saldría vacía y parecería
    que no hay nada guardado."""
    src = _lee()
    i = src.index("const abrirGuardados = async () =>")
    cuerpo = src[i:i + 600]
    assert "setFiltroGuardados('')" in cuerpo
