# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: en el móvil, el alto se lo queda el RENDER.

EL CASO
-------
El master, 18/08, mandando dos pantallazos del Estudio 3D desde su móvil:
«estoy con el móvil, optimiza todo bien q se vea todo mejor».

En esos pantallazos, de arriba abajo:

  · «ESTUDIO 3D» partido en DOS líneas,
  · «Créditos: 37 restantes» ocupando media fila,
  · «Clien·» cortado, porque Cliente/Ref habían bajado a otra fila,
  · la barra de acciones (Deco, HD, Render 8K, PDF, CAD DXF…) en TRES filas,
  · y el render, que es lo único que hay que ver, en una franja del medio.

Entre la cabecera y la barra se iba un tercio largo de la pantalla en cosas
que no son el diseño.

LO QUE SE PROTEGE
-----------------
Nada de esto da un error ni rompe un cálculo: simplemente hace el ERP
incómodo en el aparato desde el que más se usa. Y por eso mismo se deshace
solo — cualquiera que añada un botón a esa barra o alargue un rótulo vuelve a
partirla sin enterarse, porque en su pantalla grande se ve bien.

Los cambios son SOLO por debajo del ancho de móvil (`sm:` / `max-sm:`): en
pantalla grande todo se queda como estaba.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _codigo():
    with open(ESTUDIO, encoding="utf-8") as f:
        src = f.read()
    return "\n".join(l.split("//")[0] for l in src.splitlines())


def test_el_titulo_no_se_parte_en_dos_lineas():
    codigo = _codigo()
    i = codigo.index(">Estudio 3D</h1>")
    linea = codigo[max(0, i - 260):i]
    assert "whitespace-nowrap" in linea, (
        "«ESTUDIO 3D» vuelve a poder partirse en dos lineas en el movil, y esa "
        "segunda linea se la quita al render")


def test_los_creditos_van_cortos_en_movil():
    """«Créditos: 37 restantes» empujaba Cliente/Ref a otra fila, y ahi es
    donde el campo Cliente se quedaba en «Clien·»."""
    codigo = _codigo()
    assert 'className="sm:hidden">{aiCredits.restantes}' in codigo, (
        "el contador de creditos vuelve a salir con su texto largo en el "
        "movil: parte la cabecera en una fila mas")
    assert 'className="hidden sm:inline"' in codigo, \
        "se ha perdido el texto completo de creditos para pantalla grande"


def test_la_barra_de_acciones_no_se_parte_en_movil():
    """Envuelta eran TRES filas de botones. Deslizandose es una."""
    codigo = _codigo()
    assert "max-sm:flex-nowrap" in codigo, (
        "la barra de acciones vuelve a envolverse en el movil: tres filas de "
        "botones comiendose el alto del render")
    assert "max-sm:overflow-x-auto" in codigo, (
        "la barra no se puede deslizar: sin envolver y sin scroll, los botones "
        "del final quedan inalcanzables, que es peor que antes")


def test_el_render_tiene_alto_garantizado_en_movil():
    codigo = _codigo()
    assert "min-h-[42vh] sm:min-h-0" in codigo, (
        "el render vuelve a quedarse sin alto minimo en el movil: encajonado "
        "entre la cabecera, la barra y el cuadro de edicion se queda en una "
        "franja, y es lo unico que hay que ver")


def test_en_pantalla_grande_no_se_ha_cambiado_nada():
    """Los arreglos son de movil. Si se cuelan en el escritorio, se arregla una
    pantalla rompiendo la otra."""
    codigo = _codigo()
    # La barra sigue envolviendo por defecto; el `nowrap` es solo `max-sm:`.
    assert "'flex-wrap max-sm:flex-nowrap" in codigo, (
        "el «no envolver» ha dejado de ser solo de movil: en el escritorio la "
        "barra de acciones se saldra por un lado")
    assert 'hidden sm:inline' in codigo, \
        "los rotulos completos han desaparecido tambien de la pantalla grande"
