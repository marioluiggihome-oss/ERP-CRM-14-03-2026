# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
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


def _panel_de_lo_detectado():
    """El bloque JSX del panel, entero.

    Antes esto era `pantalla[ini:ini+3000]`, una ventana fija, y se rompio en
    cuanto el panel crecio al hacerse editable: la prueba miraba media pantalla
    y decia que faltaba algo que estaba justo debajo. Ahora se corta por el
    cierre del bloque, asi que el panel puede crecer lo que haga falta.
    """
    fuente = _pantalla()
    ini = fuente.index("{distDetectada && (")
    fin = fuente.index("\n          )}", ini)
    return fuente[ini:fin]


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
    arbol = ast.parse(codigo)

    # UNA EXCEPCIÓN, Y SOLO UNA: el aviso de `relacion_mv` se lee DENTRO del
    # propio Estudio 3D —ese panel no existe en ninguna otra pantalla—, así que
    # mandar ahí a quien ya está ahí es ruido. Todos los demás avisos pueden
    # salir desde otra pantalla y sí tienen que decir dónde está el botón; por
    # eso la excepción va por NOMBRE DE FUNCIÓN y no aflojando la regla: si
    # mañana aparece otro aviso en otro sitio, esta prueba lo caza igual.
    SOLO_DENTRO_DEL_ESTUDIO_3D = {"relacion_mv"}

    fallos = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for hijo in ast.walk(nodo):
            if not (isinstance(hijo, ast.Constant) and isinstance(hijo.value, str)):
                continue
            if "«Detectar distribución»" not in hijo.value:
                continue
            if nodo.name in SOLO_DENTRO_DEL_ESTUDIO_3D:
                continue
            if "Estudio 3D" not in hijo.value:
                fallos.append(f"{nodo.name}: …{hijo.value[:80]}…")
    vistos = [n.value for n in ast.walk(arbol)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)
              and "«Detectar distribución»" in n.value]
    assert vistos, "ningún aviso nombra ya el botón"
    assert not fallos, "estos avisos no dicen dónde está el botón: " + " · ".join(fallos)


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
    panel = _panel_de_lo_detectado()
    assert "medida_escrita" in panel, \
        "el panel ya no distingue las medidas escritas de las deducidas"
    assert "ancho_escrito" in panel, \
        "el panel ya no dice si el ancho de pared es real o estimado por la IA"
    assert "~" in panel, \
        "se ha perdido la marca «~» que avisa de que esa medida la ha puesto la IA"


def test_la_suma_de_los_modulos_se_vigila_en_pantalla():
    """CLAUDE.md: la suma de anchos de una pared DEBE cuadrar con la pared. El
    validador ya la cuadra; esto es la red por si algún día deja de hacerlo."""
    panel = _panel_de_lo_detectado()
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


# ── Corregir a mano lo que ha leido la IA (24/08/2026) ──────────────────────
# El comportamiento de las correcciones (que no estiren la pared, que tu medida
# se respete, que la suma cuadre) se prueba EJECUTANDO el validador, en
# `test_calculo_correccion_distribucion.py`. Aqui solo se vigila que la pantalla
# ofrezca corregir y que no se lo guise por su cuenta.

def test_el_panel_deja_corregir_lo_que_ha_leido_la_IA():
    """Sin esto el panel es un cartel: te dice que la IA se ha equivocado y te
    deja mirando. Corregir ahi es lo que convierte «la IA lo ha leido asi» en
    «esto es lo que se fabrica»."""
    panel = _panel_de_lo_detectado()
    assert "cambiarAnchoModulo" in panel, "ya no se puede corregir el ancho de un módulo"
    assert "quitarModulo" in panel, "ya no se puede quitar un módulo que la IA se ha inventado"
    assert "añadirModulo" in panel, "ya no se puede añadir un módulo que la IA no ha visto"
    assert "cambiarAnchoPared" in panel, "ya no se puede corregir el ancho de la pared"


def test_solo_se_ofrecen_anchos_de_CATALOGO():
    """Un mueble no mide 67 cm: mide 60 o 70. Si la pantalla dejara teclear
    cualquier numero, el validador lo corregiria por detras y el usuario veria
    un ancho distinto del que eligio."""
    pantalla = _pantalla()
    ini = pantalla.index("const ANCHOS_CATALOGO")
    lista = pantalla[ini:pantalla.index("]", ini)]
    for estandar in (15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120):
        assert str(estandar) in lista, f"falta el ancho estándar {estandar} en la lista de la pantalla"


def test_una_correccion_pasa_SIEMPRE_por_el_validador():
    """CANDADO (regla de oro). Corregir a mano no puede ser un atajo para
    saltarse la validacion de geometria: es entrar por la puerta buena, con un
    dato real en vez de una estimacion. La pantalla no recalcula nada por su
    cuenta — manda lo corregido al backend y dibuja lo que le devuelve."""
    cuerpo = _cuerpo_de("corregirDistribucion")
    assert "/api/estudio-cocinas/validar-distribucion" in cuerpo, \
        "la pantalla aplica las correcciones sin pasarlas por el validador de geometría"
    assert "distAceptada.current = r.distribucion" in cuerpo, \
        "se guarda la propuesta del usuario en vez de lo que ha devuelto el validador"


def test_corregir_tira_el_alzado_que_ya_estaba_dibujado():
    """El alzado guardado se dibujo con las medidas VIEJAS. Si no se tira, el
    interruptor de medidas enseñaria las cotas de antes de la correccion."""
    cuerpo = _cuerpo_de("corregirDistribucion")
    assert "alzadoGuardado.current = null" in cuerpo, (
        "una corrección ya no invalida el alzado dibujado: el botón de medidas "
        "enseñaría las cotas de antes de corregir.")
