# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""«Detectar distribución»: el botón que el backend mandaba pulsar y no existía.

Tres avisos de `routes/estudio_cocinas.py` —la planta, el alzado y el plano de
instalaciones— llevaban meses diciéndole al usuario que pulsara «Detectar
distribución» cuando faltaban medidas. Ese botón NO ESTABA EN NINGUNA PANTALLA.
La lógica sí existía (`deducirDistribucion`), pero corría escondida dentro de
cada vía de dibujo: el usuario nunca veía las medidas que se iban a dibujar, y
el aviso que leía le pedía apretar algo que no se podía apretar.

Lo que protege este candado no es el botón por el botón: es el ORDEN que pide
este proyecto — primero se comprueba que la medida es real, y después se pinta.
El botón enseña las paredes y los módulos con su ancho, marcando cuáles están
escritos en el croquis y cuáles ha deducido la IA a ojo, ANTES de dibujar nada.
"""
import ast
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO_3D = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
RUTAS = os.path.join(RAIZ, "backend", "routes", "estudio_cocinas.py")


def _pantalla():
    with open(ESTUDIO_3D, encoding="utf-8") as f:
        return f.read()


def _cuerpo_de(nombre, fuente=None):
    fuente = fuente or _pantalla()
    ini = fuente.index(f"const {nombre} =")
    return fuente[ini:fuente.index("\n  };", ini)]


def test_el_boton_que_pide_el_backend_existe_en_la_pantalla():
    """CANDADO: si el aviso nombra un botón, el botón tiene que estar."""
    with open(RUTAS, encoding="utf-8") as f:
        backend = f.read()
    assert "«Detectar distribución»" in backend, \
        "los avisos ya no nombran el botón; si se han reescrito, revisa esta prueba"
    pantalla = _pantalla()
    assert "Detectar distribución" in pantalla, (
        "el backend manda pulsar «Detectar distribución» y ese botón no está en "
        "la pantalla: el usuario lee un error que le pide apretar algo que no existe.")
    assert "onClick={detectarDistribucion}" in pantalla, \
        "el botón ya no llama a detectarDistribucion"


def test_los_avisos_dicen_DONDE_esta_el_boton():
    """Un botón que existe pero en otra pantalla sigue sin encontrarse.

    Se lee con `ast` y no con un grep a propósito: los avisos están partidos en
    varios literales de Python, y buscando texto crudo se corta un mensaje por
    la mitad y la prueba se cree que le falta algo que sí está.
    """
    with open(RUTAS, encoding="utf-8") as f:
        codigo = f.read()
    avisos = [n.value for n in ast.walk(ast.parse(codigo))
              if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and "«Detectar distribución»" in n.value]
    assert avisos, "ningún aviso nombra ya el botón"
    for aviso in avisos:
        assert "Estudio 3D" in aviso, \
            f"este aviso no dice dónde está el botón: …{aviso[:90]}…"


def test_detectar_NO_dibuja_nada():
    """El botón es para MIRAR. Si dibujara, volveríamos a pintar medidas que
    nadie ha revisado, que es justo lo que este proyecto no admite."""
    cuerpo = _cuerpo_de("detectarDistribucion")
    for prohibido in ("setRenderResult", "setRenderHistory", "generarVistaAlambrica",
                      "/api/estudio-cocinas/alzado", "/api/estudio-cocinas/plano-2d"):
        assert prohibido not in cuerpo, (
            f"«Detectar distribución» ha pasado a dibujar ({prohibido}): deja de "
            "ser el paso de revisar y se convierte en un dibujo más.")
    assert "setDistDetectada" in cuerpo, \
        "el botón ya no enseña lo detectado: entonces no sirve para revisarlo"


def test_lo_detectado_se_enseña_diciendo_que_medida_es_real_y_cual_no():
    """La regla de oro en pantalla: una cota deducida por la IA no se puede
    presentar igual que una escrita por el cliente en su croquis."""
    pantalla = _pantalla()
    ini = pantalla.index("{distDetectada && (")
    panel = pantalla[ini:ini + 3000]
    assert "medida_escrita" in panel, \
        "el panel ya no distingue las medidas escritas de las deducidas"
    assert "ancho_escrito" in panel, \
        "el panel ya no dice si el ancho de pared es real o estimado por la IA"
    assert "~" in panel, \
        "se ha perdido la marca «~» que avisa de que esa medida la ha puesto la IA"


def test_la_suma_de_los_modulos_se_vigila_en_pantalla():
    """CLAUDE.md: la suma de anchos de una pared DEBE cuadrar con la pared. El
    validador ya la cuadra; esto es la red por si algún día deja de hacerlo."""
    pantalla = _pantalla()
    ini = pantalla.index("{distDetectada && (")
    panel = pantalla[ini:ini + 3000]
    assert "suma !== pared.ancho" in panel, \
        "la pantalla ya no avisa cuando los módulos no suman el ancho de la pared"


def test_lo_detectado_caduca_cuando_cambia_de_donde_salio():
    """Si no caduca, se dibujan las medidas de una cocina sobre otra."""
    pantalla = _pantalla()
    # `\s*` entre el cuerpo y las dependencias: uno de los efectos las lleva en
    # la línea siguiente, y con un espacio fijo la prueba no lo veía.
    efectos = re.findall(r"useEffect\(\(\) => \{(.*?)\}\s*,\s*\[(.*?)\]\)", pantalla, re.S)
    limpian = [deps for cuerpo, deps in efectos
               if "olvidarDistribucion()" in cuerpo or "distAceptada.current = null" in cuerpo]
    assert limpian, "nada invalida la distribución detectada"
    todas = " ".join(limpian)
    for fuente in ("renderResult", "originalRef", "refImage", "description", "medidas.ancho"):
        assert fuente in todas, (
            f"un cambio en «{fuente}» ya no caduca la distribución detectada: se "
            "dibujarían medidas de otro diseño.")


def test_dibujar_reutiliza_lo_que_el_usuario_ya_ha_revisado():
    """Si el usuario ha detectado y revisado, es ESO lo que se dibuja — y no se
    vuelve a pagar una lectura a la IA por cada vía."""
    cuerpo = _cuerpo_de("deducirDistribucion")
    assert "if (distAceptada.current) return distAceptada.current;" in cuerpo, \
        "las vías de dibujo vuelven a deducir por su cuenta y se saltan lo revisado"
    assert cuerpo.index("distAceptada.current") < cuerpo.index("detect-distribucion"), \
        "se llama a la IA antes de mirar si ya hay una distribución revisada"
