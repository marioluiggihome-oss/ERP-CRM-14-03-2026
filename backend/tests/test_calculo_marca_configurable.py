# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA MARCA SE CONFIGURA, NO SE ESCRIBE A MANO. Y SIN CONFIGURAR, NO SE IMPRIME.

El master, 25/08/2026: «revisa todos los PDFs y quita el texto de Luiggi Home
por todos los lados, y en el ERP también». El ERP se licencia a terceros, y un
cliente no puede encontrarse la marca de otro impresa en su presupuesto.

EL AJUSTE YA EXISTÍA: `SettingsModel` tiene `companyName`, `logo` y hasta
`marcaBlanca`, y el frontend tiene un `NeutralLogo`. Fallaban dos cosas:

  1. Los PDFs no lo usaban: escribían «LUIGGI HOME» a mano.
  2. Donde sí lo usaban, EL VALOR POR DEFECTO VOLVÍA A METER LA MARCA:
     `settings.get("companyName", "LUIGGI HOME")`.

Lo segundo es lo que hay que vigilar, porque es lo que vuelve solo. Un ajuste
cuyo defecto es la marca no despersonaliza nada: en cuanto una instalación deja
el campo vacío, reaparece. Un documento sin membrete es correcto; uno con el
membrete de otra empresa, no.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

import pytest  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACK = os.path.join(RAIZ, "backend")
FRONT = os.path.join(RAIZ, "frontend", "src")

# Donde se generan documentos o correos que ve alguien de fuera.
DE_CARA_AFUERA = (
    os.path.join(BACK, "services", "catalog_export.py"),
    os.path.join(BACK, "services", "nomenclaturas_pdf.py"),
    os.path.join(BACK, "services", "email_service.py"),
    os.path.join(BACK, "routes", "invoices.py"),
    os.path.join(BACK, "routes", "factory_reports.py"),
    os.path.join(FRONT, "components", "ProformaImporter.jsx"),
    os.path.join(FRONT, "components", "CocinaMontada3.jsx"),
    os.path.join(FRONT, "components", "CRMMarketing.jsx"),
)


def _lee(r):
    with open(r, "r", encoding="utf-8") as f:
        return f.read()


def _sin_cabecera(t):
    """Fuera la cabecera de copyright: ahí el titular SÍ tiene que estar."""
    return "\n".join(l for l in t.splitlines() if "ALEMAR-COPYRIGHT" not in l)


def _sin_comentarios(t):
    """Fuera los comentarios y las docstrings.

    Hace falta porque el código EXPLICA en un comentario cuál era la marca que
    se quitó, con su texto literal, y sin esto la prueba se caza a sí misma: la
    explicación de que ya no está parece que sigue estando. Pasó tres veces en
    esta misma sesión con candados distintos, así que aquí va desde el principio.

    Y no se pierde nada por el camino: un comentario no se imprime en un PDF ni
    se le manda a un cliente. Lo que se vigila es lo que SALE.
    """
    t = re.sub(r'"""[\s\S]*?"""', "", t)
    t = re.sub(r"/\*[\s\S]*?\*/", "", t)
    t = re.sub(r"^\s*(?:#|//).*$", "", t, flags=re.M)
    return t


# ── El motor ─────────────────────────────────────────────────────────────────
def test_sin_marca_configurada_NO_se_imprime_ninguna():
    from services.marca import nombre_comercial, POR_DEFECTO
    assert POR_DEFECTO == "", (
        "el valor por defecto de la marca ha dejado de estar vacío: cualquier "
        "instalación sin configurar imprimiría esa marca en sus documentos")
    assert nombre_comercial() == ""
    assert nombre_comercial({}) == ""
    assert nombre_comercial({"companyName": "   "}) == ""


def test_manda_el_ajuste_de_la_instalacion():
    from services.marca import nombre_comercial
    assert nombre_comercial({"companyName": "ACME COCINAS"}) == "ACME COCINAS"


def test_sin_marca_NO_queda_el_separador_colgando():
    """El detalle que delata un apaño: «Documento generado el 25/08 - » con el
    guion al aire canta más en un PDF que la propia marca."""
    from services.marca import con_marca
    assert con_marca("Documento generado el 25/08") == "Documento generado el 25/08"
    assert con_marca("pág. 3", separador=" · ") == "pág. 3"
    assert con_marca("pág. 3", {"companyName": "ACME"}) == "pág. 3 · ACME"


def test_los_AJUSTES_nacen_sin_marca():
    """El defecto de `SettingsModel` era «LUIGGI HOME»."""
    cuerpo = _lee(os.path.join(BACK, "routes", "settings.py"))
    for campo in ("companyName", "emailSenderName"):
        m = re.search(rf"{campo}: str = (.+)", cuerpo)
        assert m, f"ya no está el ajuste {campo}"
        assert m.group(1).startswith('""'), (
            f"`{campo}` vuelve a nacer con una marca puesta: {m.group(1)[:40]}")


# ── Que no vuelva a colarse ──────────────────────────────────────────────────
@pytest.mark.parametrize("ruta", DE_CARA_AFUERA, ids=lambda r: os.path.basename(r))
def test_NO_hay_marca_escrita_a_mano_en_lo_que_ve_un_cliente(ruta):
    cuerpo = _sin_comentarios(_sin_cabecera(_lee(ruta)))
    encontrados = re.findall(r"(?i)luiggi[ _-]?home", cuerpo)
    assert not encontrados, (
        f"{os.path.basename(ruta)} vuelve a llevar la marca escrita a mano "
        f"({len(encontrados)} veces). Se usa `marca.py` / `marca.js`.")


@pytest.mark.parametrize("ruta", DE_CARA_AFUERA, ids=lambda r: os.path.basename(r))
def test_NINGUN_VALOR_POR_DEFECTO_es_una_marca(ruta):
    """El fallo que vuelve solo.

    `settings.get("companyName", "LUIGGI HOME")` y
    `settings?.companyName || 'LUIGGI HOME'` parecen prudentes y son justo lo
    contrario: el día que alguien deje el ajuste vacío, el cliente ve la marca
    de otra empresa en su presupuesto.
    """
    cuerpo = _sin_comentarios(_sin_cabecera(_lee(ruta)))
    sospechas = re.findall(
        r"""(?ix) (?:companyName|empresa) \s* (?: \|\| | ,) \s* ['"][A-Za-zÁÉÍÓÚÑ ]{3,} ['"]""",
        cuerpo)
    assert not sospechas, (
        f"{os.path.basename(ruta)} tiene un valor por defecto con nombre "
        f"dentro: {sospechas[:2]}. El defecto tiene que ser vacío.")


def test_el_frontend_tiene_su_gemelo_y_dice_lo_mismo():
    """Hay documentos que se generan en el servidor y otros en el navegador.
    Si los dos no deciden igual, media factura sale con membrete y media sin."""
    js = _lee(os.path.join(FRONT, "marca.js"))
    assert "export const nombreComercial" in js and "export const conMarca" in js
    assert "|| ''" in js, "el gemelo del navegador no tiene el defecto vacío"

    import shutil
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    guion = (js.replace("export const", "const")
             + "\nconsole.log(JSON.stringify(["
               "nombreComercial(null), nombreComercial({companyName:'  '}),"
               "conMarca('pág. 3', null), conMarca('pág. 3', {companyName:'ACME'})]));")
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"marca.js no corre: {r.stderr}"
    import json
    assert json.loads(r.stdout) == ["", "", "pág. 3", "ACME · pág. 3"]
