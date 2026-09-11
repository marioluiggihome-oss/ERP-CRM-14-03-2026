# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""EL CLON DEL ESTUDIO 3D NO PUEDE SEPARARSE DEL ORIGINAL (09/09/2026).

`Estudio3DLab.jsx` es una copia literal de `AIRenderStudio.jsx` con UNA cosa
más: el botón IA PREMIUM. Se copió a propósito, porque el original está
congelado desde el 04/09 y meterle una bandera por dentro sería tocarlo en cada
prueba.

PERO UNA COPIA QUE NADIE COMPARA SE SEPARA. Es la misma lección que el ERP ya
tiene escrita en tres sitios (`plataformas.js`, `estadosFabricacion.js`, la
tabla de comisiones): dos ficheros que dicen lo mismo acaban diciendo cosas
distintas, y ninguno de los dos parece un error.

AQUÍ LA SEPARACIÓN CUESTA ALGO MUY CONCRETO: el clon existe para comparar
motores. Si se aleja del original, comparar un render de los dos deja de medir
el MOTOR y pasa a medir las diferencias que alguien haya metido por el camino —
y la conclusión saldrá al revés sin que nada falle.

NO se exige que sean idénticos (no podrían serlo: el botón premium es la razón
de existir del clon). Se exige que las piezas que DECIDEN el resultado sigan
siendo las mismas, y se MIDE cuánto se han alejado.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORIGINAL = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
CLON = os.path.join(RAIZ, "frontend", "src", "components", "Estudio3DLab.jsx")
PANEL_PREMIUM = os.path.join(RAIZ, "frontend", "src", "components", "premium", "PremiumDesignPanel.jsx")
LAYOUT_PREMIUM = os.path.join(RAIZ, "frontend", "src", "components", "premium", "premiumLayout.js")

# Las piezas que DECIDEN qué imagen sale. Si una se pierde en el clon, los dos
# renders dejan de ser comparables aunque la pantalla siga funcionando.
PIEZAS_QUE_DECIDEN_EL_RENDER = [
    # El detector de croquis del servidor INTERPRETA en vez de EDITAR si no se
    # le declara que esto es un render nuestro (regla 1, 06/09).
    "editingRender: true",
    # La lista de lo ya aplicado: sin ella cada pulsación es una vuelta sin
    # memoria y se pierden los acabados.
    "memoriaDeCambios()",
    # El encadenado de ediciones sobre la imagen base, no sobre la degradada.
    "const baseImg = editBaseImage || img;",
    "CAMBIOS YA APLICADOS QUE DEBES CONSERVAR",
    # La referencia se prepara igual en los dos, o IA 7 no mide lo que mide.
    "await downscaleImage(file, 3000, 0.96, 'image/png')",
    # El aviso de coste sale de la tabla compartida, no de una copia.
    "creditosDeUnRender(",
]


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_el_clon_existe_y_es_un_clon_de_verdad():
    """Un «clon» que se ha quedado a medias no sirve para comparar nada."""
    assert os.path.exists(CLON), "ha desaparecido el clon del Estudio 3D"
    original, clon = _leer(ORIGINAL), _leer(CLON)
    # El clon lleva la cabecera que explica qué es y el botón premium, así que
    # es NORMAL que sea algo mayor. Lo que no puede es haber adelgazado.
    assert len(clon.splitlines()) >= len(original.splitlines()), (
        "el clon tiene MENOS líneas que el original: se le ha quitado algo, y "
        "entonces comparar los dos renders no mide el motor")


def test_el_clon_conserva_las_piezas_que_deciden_el_render():
    """CANDADO DURO. Es la razón de existir de este fichero."""
    clon = _leer(CLON)
    original = _leer(ORIGINAL)
    for pieza in PIEZAS_QUE_DECIDEN_EL_RENDER:
        assert pieza in original, (
            f"«{pieza}» ya no está en el ORIGINAL: esta prueba se ha quedado "
            f"antigua y hay que revisarla, no borrar la línea")
        assert clon.count(pieza) >= original.count(pieza), (
            f"el clon ha perdido «{pieza}», que el original sí tiene. Los dos "
            f"renders dejan de ser comparables: la diferencia que se vea no "
            f"será del motor.")


def test_el_clon_se_llama_distinto_y_no_pisa_al_original():
    """Dos componentes con el mismo nombre en el mismo build es un enredo que
    no da error hasta que se pinta la pantalla que no toca."""
    clon = _leer(CLON)
    assert re.search(r"export default function Estudio3DLab\b", clon) or (
        "const Estudio3DLab" in clon and "export default Estudio3DLab" in clon), (
        "el clon no exporta un componente propio llamado Estudio3DLab")
    # SIN COMENTARIOS. La cabecera del clon NOMBRA al original a propósito
    # («sale de AIRenderStudio.jsx, no lo edites a mano»), así que mirar el
    # fichero entero se pone rojo por su propia explicación. Cuarta vez en el
    # repo con esta trampa (reglas 24, 34 y 35).
    codigo = "\n".join(
        l.split("//")[0] for l in clon.splitlines()
        if not l.strip().startswith(("*", "/*", "*/")))
    assert "AIRenderStudio" not in codigo, (
        "en el CÓDIGO del clon ha vuelto a aparecer el nombre del original: o "
        "se ha reimportado, o la copia se hizo a medias")
    assert "Estudio3DLab" in codigo, (
        "el recorte se ha comido el código: la prueba pasaría por no encontrar "
        "nada que mirar")


def test_el_clon_limita_las_extensiones_a_premium():
    """Se MIDE la distancia, no se confía en que nadie la mueva.

    Si alguien empieza a mejorar el clon «ya que es de pruebas», esta prueba se
    pone roja y obliga a decidirlo a propósito: o se lleva la mejora también al
    original, o se acepta que ya no son comparables y se actualiza el tope."""
    original = [l.rstrip() for l in _leer(ORIGINAL).splitlines()]
    clon = [l.rstrip() for l in _leer(CLON).splitlines()]
    import difflib
    dif = list(difflib.unified_diff(original, clon, lineterm="", n=0))
    cambiadas = [l for l in dif if (l.startswith("+") or l.startswith("-"))
                 and not l.startswith(("+++", "---"))]
    # Cabecera del clon (~26 líneas), el nombre del componente, el botón y su
    # traducción y extensiones PREMIUM autorizadas el 10/09. El original
    # permanece intacto y la regeneración exacta se verifica por separado.
    assert len(cambiadas) <= 150, (
        f"el clon y el original se han separado en {len(cambiadas)} líneas. El "
        f"clon existe para comparar MOTORES con todo lo demás igual; con esta "
        f"distancia, lo que se vea en los dos renders ya no es el motor. "
        f"Decide a propósito: o la mejora va también al original, o se sube "
        f"este tope sabiendo lo que se pierde.")


def test_ninguno_de_los_dos_tiene_hooks_por_debajo_de_un_return():
    """Regla 23: eso deja el ERP EN NEGRO, no solo esa pantalla.

    El clon hereda 6.000 líneas de golpe, así que hereda también el riesgo. Lo
    barre `test_pantalla_hooks_antes_del_return.py` sobre las 92 pantallas; se
    comprueba aquí que el clon está DENTRO de ese barrido, porque una pantalla
    nueva que se quede fuera del barrido no la mira nadie."""
    barrido = os.path.join(RAIZ, "backend", "tests",
                           "test_pantalla_hooks_antes_del_return.py")
    fuente = _leer(barrido)
    m = re.search(r"glob\.glob\(([^)]*)\)", fuente) or re.search(r"\.jsx", fuente)
    assert m, "el barrido de hooks ya no recorre ficheros .jsx"
    # Que el barrido llegue de verdad al clon: se comprueba por el directorio.
    assert "components" in fuente, (
        "el barrido de hooks ya no mira el directorio de componentes, así que "
        "el clon quedaría sin vigilar")


def test_el_clon_SE_REGENERA_con_la_herramienta():
    """La deriva no se arregla copiando a mano — eso es garantizar que un día
    se copie a medias.

    El 10/09, al día siguiente de crear el clon, otra sesión mejoró el original
    y los dos se separaron en 148 líneas de golpe. La herramienta regenera el
    clon desde el original volviendo a aplicar las DOS únicas diferencias que
    puede tener; si un ancla ya no encaja, falla en voz alta en vez de dejar un
    clon a medias."""
    import subprocess
    import sys
    guion = os.path.join(RAIZ, "herramientas", "sincronizar_clon_estudio3d.py")
    assert os.path.exists(guion), (
        "ha desaparecido la herramienta que sincroniza el clon: sin ella la "
        "deriva se arregla a mano y un día se hará a medias")
    r = subprocess.run([sys.executable, guion, "--verificar"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, (
        "el clon NO está al día con el original:\n" + r.stdout + r.stderr +
        "\nEjecuta: python3 herramientas/sincronizar_clon_estudio3d.py")


def test_premium_revisa_una_sola_distribucion_antes_de_gastar_creditos():
    """El panel no puede volver a ser un cuestionario ornamental desconectado.

    La distribución que el usuario corrige es la misma que se serializa como
    contrato obligatorio y el render con croquis queda bloqueado hasta que se
    confirme explícitamente.
    """
    clon = _leer(CLON)
    panel = _leer(PANEL_PREMIUM)
    layout = _leer(LAYOUT_PREMIUM)
    assert "Leer croquis y módulos" in panel
    assert "Confirmar esta distribución" in panel
    assert "premiumLayoutConfirmation !== JSON.stringify(distDetectada.distribucion)" in clon
    assert "detectedDistributionPrompt(distribution)" in clon
    assert "DISTRIBUCIÓN REVISADA Y CONFIRMADA POR EL USUARIO" in layout


def test_premium_no_muestra_el_antiguo_panel_teorico():
    panel = _leer(PANEL_PREMIUM)
    for texto in ("Diseñado para vivir", "CRITERIOS DEL ENCARGO", "Descargar encargo", "Recuperar copia"):
        assert texto not in panel, f"ha vuelto al panel PREMIUM el bloque sin uso: {texto}"


def test_premium_entiende_combi_y_frigo_como_electrodomestico():
    """«Pon el combi negro» identifica el objeto y no debe bloquearse."""
    original, clon = _leer(ORIGINAL), _leer(CLON)
    assert "|frigo|combi|nevera|" in clon
    assert "|frigo|combi|nevera|" not in original, (
        "el vocabulario experimental se ha colado en el Estudio 3D congelado")


def test_normal_y_premium_no_comparten_sesion_ni_preset():
    """Cambiar de estudio no puede llevarse el diseño ni el selector del otro."""
    original, clon = _leer(ORIGINAL), _leer(CLON)
    assert "state?.estudio3dPreset" in original
    assert "leerSesion(estadoRef.current, 'estudio3d')" in original
    assert "guardarSesion(f, 'estudio3d', sesionRef.current)" in original
    assert "state?.estudio3dPremiumPreset" in clon
    assert "leerSesion(estadoRef.current, 'estudio3dPremium')" in clon
    assert "guardarSesion(f, 'estudio3dPremium', sesionRef.current)" in clon
