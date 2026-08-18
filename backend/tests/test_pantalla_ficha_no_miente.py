# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: la hoja de especificaciones no imprime lo que nadie ha elegido.

EL CASO, CON NOMBRE Y APELLIDOS
-------------------------------
Proyecto de RUBÉN, ref. ZAMORA, 18/08/2026. El master pasó el PDF que el ERP
le había generado. En la página 3, «ESPECIFICACIONES DEL DISEÑO»:

    Distribución:  En L
    Encimera:      Cuarzo Blanco
    Muebles:       Blanco Mate
    Tiradores:     Barra Negro
    Suelo:         Roble

Y JUSTO DEBAJO, en la misma página, la descripción que la IA había sacado del
croquis a boli del cliente:

    «... modelo Palma en acabado blanco alto BRILLO (Br), con un sistema de
    apertura gola de aluminio para un diseño SIN TIRADORES. La encimera es de
    cuarzo compacto en color GRIS CLARO ... El suelo es de gres porcelánico
    de gran formato en GRIS neutro.»

sobre una cocina que en el croquis es LINEAL, no en L.

Las cinco líneas de la ficha mentían. Y no era la IA equivocándose: eran los
VALORES CON LOS QUE ARRANCA EL FORMULARIO —layout 'L-shape', countertop
'quartz_white', cabinets 'white_matte', handles 'bar_black', floor 'wood_oak'—
impresos como si alguien los hubiera decidido.

POR QUÉ ESTO ES DE LOS GRAVES
-----------------------------
· No da ningún error. La hoja sale bonita y con pinta de ficha técnica.
· Contradice al render de la página anterior y a la descripción de debajo, o
  sea que el propio documento se desmiente a sí mismo y nadie lo nota.
· Va AL CLIENTE, y se firma. Firmaría blanco mate con tiradores de barra
  negros; se fabricaría blanco brillo con gola. Eso es una reclamación.

La descripción, en cambio, estaba BIEN: sacó del croquis el pilar estructural,
el «Palma blanco alto brillo», el escurreplatos y el microondas. El fallo no
estaba en leer el dibujo. Estaba en el formulario que lo acompañaba.

LO QUE SE PROTEGE
-----------------
Que solo se imprima lo que alguien ha tocado. Un hueco se pregunta; un dato
falso se cree.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _codigo():
    """El fichero sin comentarios: este candado busca CÓDIGO, y los comentarios
    de aquí abajo nombran a propósito lo que no debe existir."""
    with open(ESTUDIO, encoding="utf-8") as f:
        src = f.read()
    return "\n".join(l.split("//")[0] for l in src.splitlines())


def test_se_apunta_lo_que_el_usuario_elige():
    codigo = _codigo()
    assert "paramsElegidos" in codigo, (
        "ya no se distingue lo que alguien ha elegido de lo que trae el "
        "formulario de fábrica: la hoja del cliente volverá a imprimir «Blanco "
        "Mate» sobre una cocina que es blanco brillo")
    assert "const elegirParams" in codigo, \
        "se ha quitado el punto único por el que pasan los cambios del formulario"


def test_ningun_selector_se_salta_el_registro():
    """Si un selector vuelve a llamar a `setParams` por su cuenta, ESE campo
    deja de contar como elegido y no se imprimirá nunca — o peor, si alguien
    invierte la lógica, se imprimirá siempre. El punto de entrada es uno."""
    codigo = _codigo()
    sueltos = [l.strip() for l in codigo.splitlines()
               if "setParams(" in l and "const elegirParams" not in l]
    # El único `setParams` permitido es el de DENTRO del propio helper.
    assert len(sueltos) == 1 and "...cambios" in sueltos[0], (
        "hay selectores que cambian los parámetros sin pasar por "
        f"`elegirParams`, así que su elección no se registra: {sueltos}")


def test_la_hoja_solo_imprime_lo_elegido():
    codigo = _codigo()
    i = codigo.index("ESPECIFICACIONES DEL DISEÑO")
    hoja = codigo[i:i + 2200]
    assert "paramsElegidos.has(clave)" in hoja, (
        "la hoja del PDF vuelve a imprimir las siete líneas siempre, vengan de "
        "una decisión o del valor de arranque del formulario")
    # Y las líneas siguen siendo las siete, con su clave: si alguien quita una
    # clave del filtro, ese campo se imprimiría de nuevo sin control.
    for clave in ("'layout'", "'countertop'", "'cabinets'", "'handles'",
                  "'floor'", "'style'", "'lighting'"):
        assert clave in hoja, f"la línea {clave} ha salido del control de elegidos"


def test_si_no_se_eligio_nada_la_hoja_lo_dice():
    """Un título suelto sin nada debajo se lee como «se han olvidado de
    rellenarlo». Tiene que decir de dónde salen entonces los acabados."""
    codigo = _codigo()
    i = codigo.index("ESPECIFICACIONES DEL DISEÑO")
    hoja = codigo[i:i + 2600]
    assert "if (!specs.length)" in hoja, \
        "cuando no se ha elegido nada, la hoja se queda con un título y un hueco"
    assert "No se fijaron acabados en el formulario" in hoja, \
        "ya no se explica de dónde salen los acabados cuando la ficha va vacía"


def test_los_valores_de_arranque_siguen_siendo_los_de_siempre():
    """No se han tocado: el formulario puede seguir arrancando relleno, que es
    cómodo para diseñar desde cero. Lo que cambia es que arrancar relleno ya no
    significa haber decidido."""
    codigo = _codigo()
    i = codigo.index("const [params, setParams] = useState({")
    arranque = codigo[i:i + 400]
    for valor in ("'L-shape'", "'quartz_white'", "'white_matte'",
                  "'bar_black'", "'wood_oak'"):
        assert valor in arranque, (
            f"ha cambiado el valor de arranque {valor}: este candado protege "
            "que no se IMPRIMAN sin elegir, no que desaparezcan")
