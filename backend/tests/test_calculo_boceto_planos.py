# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del BOCETO A LAPIZ de los planos vectoriales.

El master ensenio sus referencias —bocetos a lapiz, con profundidad— y pidio
que los planos del ERP pudieran salir asi. El trazo es lo UNICO que cambia: los
mismos modulos, los mismos anchos y las mismas cotas. Si el boceto redibujara
algo, dejaria de ser el mismo plano y pasaria a ser un dibujo con autoridad de
diseniador y medidas de nadie.

Lo que se protege:

1. LA PLANTA Y EL ALZADO VAN A JUEGO. Salen en la MISMA lamina. Si el lapiz
   valiera solo para uno, al encender el boceto saldria una hoja con el alzado
   dibujado a mano y la planta a linea de CAD. `plano-2d` acepto el flag desde
   el primer dia SIN implementarlo: aceptar y no hacer es peor que no aceptar,
   porque nadie se entera.

2. EL TRAZO SE LIMPIA SIEMPRE. `path.sketch` es un ajuste GLOBAL de
   matplotlib, de proceso, no de peticion. Si una peticion lo deja puesto, el
   SIGUIENTE plano —de otro proyecto, de otro usuario— sale temblado sin que
   nadie lo haya pedido. Y eso no da error en ningun sitio: solo sale mal. Por
   eso la limpieza va en `finally` y no al final del `try`.

3. NO SE USA `plt.xkcd()`. Cambia tambien la tipografia y depende de una fuente
   que puede no estar instalada en el servidor. Las cotas tienen que leerse
   siempre, incluso cuando el dibujo parece hecho a mano.

4. EL INTERRUPTOR LLEGA A TODAS LAS VIAS. En la pantalla hay cuatro botones que
   acaban dibujando el alzado. Si el flag se pasara solo en una, el master lo
   encenderia y por las otras tres seguiria saliendo a linea limpia sin que
   nada explicara por que.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COCINAS = os.path.join(RAIZ, "backend", "routes", "estudio_cocinas.py")
ARMARIO = os.path.join(RAIZ, "backend", "routes", "armarios_alzado.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")

# Los tres numeros del temblor: amplitud, longitud de onda y aleatoriedad.
# Se fijan para que "ajustar el boceto" sea un cambio consciente y no un
# retoque que nadie recuerde haber hecho.
TRAZO = "(2.0, 120.0, 16.0)"


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _cuerpo_de(fuente, decorador):
    """El codigo de un endpoint, desde su decorador hasta el siguiente."""
    i = fuente.index(decorador)
    j = fuente.find("\n@router.", i + len(decorador))
    return fuente[i:j if j != -1 else len(fuente)]


# ─── 1. La planta y el alzado van a juego ───────────────────────────────────

def test_el_alzado_de_cocina_dibuja_a_lapiz_cuando_se_pide():
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/alzado")')
    assert "path.sketch" in cuerpo, "el alzado de cocina ya no hace el boceto"
    assert TRAZO in cuerpo, f"el trazo del alzado ha cambiado de {TRAZO}"


def test_la_planta_de_cocina_dibuja_a_lapiz_cuando_se_pide():
    """Aceptaba el flag `boceto` y no hacia nada con el: el alzado salia a mano
    y la planta de la misma lamina a linea de CAD."""
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/plano-2d")')
    assert "path.sketch" in cuerpo, (
        "la planta acepta el flag `boceto` pero no lo aplica: saldria a linea "
        "limpia junto a un alzado dibujado a mano")
    assert TRAZO in cuerpo, "el trazo de la planta no es el mismo que el del alzado"


def test_el_alzado_de_armario_dibuja_a_lapiz_cuando_se_pide():
    cuerpo = _leer(ARMARIO)
    assert "path.sketch" in cuerpo and TRAZO in cuerpo, (
        "el alzado de armario no hace el boceto, o usa otro trazo")


# ─── 2. El trazo se limpia SIEMPRE ──────────────────────────────────────────

def _limpia_en_finally(cuerpo):
    """¿Hay un `finally` que devuelve `path.sketch` a None?"""
    tras_finally = cuerpo.split("finally:")
    return any(re.search(r'path\.sketch"\]\s*=\s*None', trozo) for trozo in tras_finally[1:])


def test_la_planta_de_cocina_no_deja_el_lapiz_puesto():
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/plano-2d")')
    assert _limpia_en_finally(cuerpo), (
        "`path.sketch` es GLOBAL: sin limpiarlo en `finally`, la siguiente "
        "planta sale temblada sin que nadie lo haya pedido y sin dar error")


def test_el_alzado_de_cocina_no_deja_el_lapiz_puesto():
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/alzado")')
    assert _limpia_en_finally(cuerpo), "el alzado de cocina no limpia `path.sketch`"


def test_el_alzado_de_armario_no_deja_el_lapiz_puesto():
    assert _limpia_en_finally(_leer(ARMARIO)), (
        "el alzado de armario no limpia `path.sketch`")


# ─── 3. Nunca `plt.xkcd()` ──────────────────────────────────────────────────

def test_no_se_usa_xkcd_en_ningun_plano():
    """Cambia la tipografia y depende de una fuente que puede faltar en el
    servidor. Una cota que no se lee no es una cota."""
    for ruta in (COCINAS, ARMARIO):
        assert "xkcd" not in _leer(ruta).replace("NO `plt.xkcd()`", ""), (
            f"{os.path.basename(ruta)} usa xkcd(): las cotas pueden dejar de leerse")


# ─── 4. El interruptor llega a todas las vias ───────────────────────────────

def test_las_dos_vias_del_alzado_pasan_el_flag():
    """En la pantalla hay cuatro botones que acaban aqui: la alambrica llama
    directa y los otros tres pasan por `generarPlanosExactos`. Las dos vias
    tienen que mandar el flag o el interruptor solo funcionaria a medias."""
    fuente = _leer(ESTUDIO)
    llamadas = fuente.count("estudio-cocinas/alzado")
    assert llamadas == 2, (
        f"hay {llamadas} sitios que piden el alzado y la prueba conoce 2: "
        f"revisa si el nuevo pasa `boceto` (barre el fichero ENTERO antes de "
        f"decir cuantos son)")
    assert fuente.count("boceto: bocetoAlzado") == 2, (
        "alguna via dibuja el alzado sin pasar el interruptor de boceto")


def test_el_interruptor_existe_en_pantalla():
    fuente = _leer(ESTUDIO)
    assert "setBocetoAlzado" in fuente, "no hay interruptor de boceto en pantalla"
    assert "bocetoAlzado" in fuente
