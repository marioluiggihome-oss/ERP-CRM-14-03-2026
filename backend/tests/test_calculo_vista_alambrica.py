# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Vista alámbrica (alzado acotado): que falle BIEN cuando no hay medidas.

El 05/08/2026 la vista alámbrica "fallaba" siempre que no se había elegido
distribución. Y fallaba dos veces:

1. El aviso decía que no había medidas válidas, pero NO decía qué hacer. El
   usuario se quedaba delante de un error sin salida, cuando lo único que
   faltaba era elegir la distribución en el panel de la izquierda.
2. `HTTPException` hereda de `Exception`, así que el `except Exception` del
   final se tragaba el 422 y lo devolvía como un 500 con un "422:" incrustado
   dentro del texto. Un error de configuración del usuario se presentaba como
   una avería del servidor.

No se toca la regla de oro: sin medidas reales NO se dibuja (una cota inventada
en un alzado acaba en el taller). Lo que se arregla es cómo se cuenta.
"""
import ast
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA = os.path.join(RAIZ, "backend", "routes", "estudio_cocinas.py")
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "EstudioCocinas.jsx")


def _fuente_de_generar_alzado():
    """El cuerpo de `generar_alzado`, recortado del árbol del módulo.

    Se recorta con `ast` y no buscando texto: así el día que la función se mueva
    de sitio, la prueba sigue mirando la función y no unas líneas cualesquiera.
    """
    with open(RUTA, encoding="utf-8") as f:
        codigo = f.read()
    arbol = ast.parse(codigo)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.name == "generar_alzado":
            return ast.get_source_segment(codigo, nodo) or ""
    raise AssertionError("ya no existe generar_alzado en routes/estudio_cocinas.py")


def test_el_aviso_de_falta_de_medidas_no_se_devuelve_como_averia():
    """CANDADO: el 422 tiene que salir tal cual, no envuelto en un 500."""
    cuerpo = _fuente_de_generar_alzado()
    manejadores = []
    for nodo in ast.walk(ast.parse(cuerpo)):
        if isinstance(nodo, ast.Try):
            for h in nodo.handlers:
                if isinstance(h.type, ast.Name):          # except Foo:
                    manejadores.append(h.type.id)
                elif isinstance(h.type, ast.Tuple):       # except (Foo, Bar):
                    manejadores += [n.id for n in h.type.elts if isinstance(n, ast.Name)]
    assert "HTTPException" in manejadores, (
        "generar_alzado ha vuelto a tragarse HTTPException: un 422 con "
        "instrucciones para el usuario saldrá como un 500 de servidor caído.")


def test_el_aviso_dice_que_hacer_y_no_solo_que_falla():
    """Un error sin salida es un error a medias."""
    cuerpo = _fuente_de_generar_alzado()
    assert "Elige la distribución" in cuerpo, \
        "el aviso ya no dice dónde se eligen las paredes"
    assert "Detectar distribución" in cuerpo, \
        "el aviso ya no ofrece la otra vía (deducirla de un render)"


def test_sigue_prohibido_dibujar_sin_medidas_reales():
    """La regla de oro no se relaja para que 'no falle': si no hay paredes con
    medidas de verdad, no se dibuja. Una cota inventada acaba en el taller."""
    cuerpo = _fuente_de_generar_alzado()
    assert "validar_distribucion" in cuerpo, \
        "el alzado ya no valida la geometría antes de dibujar"
    assert "status_code=422" in cuerpo, \
        "el alzado ya no rechaza una distribución sin medidas válidas"


def test_la_pantalla_avisa_antes_de_llamar_al_servidor():
    """Si no hay distribución, no se manda una petición condenada a fallar."""
    with open(PANTALLA, encoding="utf-8") as f:
        fuente = f.read()
    ini = fuente.index("const genAlzado")
    fin = fuente.index("const genFicha", ini)
    bloque = fuente[ini:fin]
    assert "Falta la distribución" in bloque, \
        "la pantalla vuelve a mandar el alzado sin comprobar que hay paredes"
    assert bloque.index("Falta la distribución") < bloque.index("apiPost"), \
        "el aviso llega DESPUÉS de llamar al servidor: no sirve de nada"


# ── Estudio 3D: la misma vista alámbrica, por otro camino ────────────────────
# El botón «Alámbrica c/ medidas» del Estudio 3D no manda paredes: primero
# deduce la distribución del render y, si no puede, de la descripción. Esa
# segunda vía era código muerto.

ESTUDIO_3D = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _bloque_vista_alambrica():
    with open(ESTUDIO_3D, encoding="utf-8") as f:
        fuente = f.read()
    ini = fuente.index("const generarVistaAlambrica")
    fin = fuente.index("const generarPlanosExactos", ini)
    return fuente[ini:fin]


def _bloque_deducir_distribucion():
    """El codigo que deduce la distribucion.

    El 08/08 se saco de `generarVistaAlambrica` a una funcion propia, porque
    estaba COPIADO en cuatro sitios y arreglar uno dejaba los otros tres
    midiendo el render en vez del croquis. La promesa que protege la prueba de
    abajo no ha cambiado: solo se ha mudado de sitio.
    """
    with open(ESTUDIO_3D, encoding="utf-8") as f:
        fuente = f.read()
    ini = fuente.index("const deducirDistribucion")
    return fuente[ini:fuente.index("\n  };", ini)]


def test_si_falla_el_render_todavia_se_prueba_la_descripcion():
    """CANDADO: `postJson` lanza al recibir un error del servidor. Sin un try
    propio, un 422 del render se llevaba por delante la vía de la descripción,
    que podría haber funcionado."""
    bloque = _bloque_deducir_distribucion()
    # `rindex`: ahora hay DOS llamadas a detect-distribucion (croquis y render).
    # La que importa aqui es la ultima antes de la via del texto.
    detectar = bloque.rindex("detect-distribucion")
    desde_texto = bloque.index("distribucion-desde-texto")
    # Entre una llamada y otra tiene que haber un catch: si no, la segunda es
    # inalcanzable cuando la primera devuelve error.
    assert "catch" in bloque[detectar:desde_texto], (
        "la vía de la descripción ha vuelto a ser código muerto: un error del "
        "render salta al catch general y nunca se prueba el texto.")


def _bloque_que_hacer():
    """El consejo que se le da al usuario cuando no se puede deducir.

    El 24/08 dejó de estar COPIADO en las tres vías (alámbrica, perspectiva y
    el botón de detectar) y pasó a una función sola. La promesa no ha cambiado;
    solo se ha mudado, así que la prueba se muda con ella.
    """
    with open(ESTUDIO_3D, encoding="utf-8") as f:
        fuente = f.read()
    ini = fuente.index("const queHacerParaDeducir")
    return fuente[ini:fuente.index("\n  };", ini)]


def test_el_aviso_dice_donde_se_escriben_las_medidas():
    bloque = _bloque_que_hacer()
    assert "Medidas de la estancia" in bloque, \
        "el aviso ya no dice dónde se escribe el ancho de la pared"
    # Y las tres vías tienen que seguir usándolo: si una se copia el consejo
    # otra vez, volvemos a arreglar una y dejar dos mintiendo.
    with open(ESTUDIO_3D, encoding="utf-8") as f:
        fuente = f.read()
    # Las TRES vías (alámbrica, perspectiva y el botón de detectar) lo llaman.
    # `const queHacerParaDeducir = (` no cuenta: la definición lleva un « = »
    # por medio y no casa con este patrón, así que esto cuenta llamadas.
    assert fuente.count("queHacerParaDeducir(fallos") == 3, \
        "alguna vía ha vuelto a escribirse su propio consejo en vez de usar el común"


def test_si_el_servidor_no_responde_NO_se_le_pide_al_usuario_que_escriba_nada():
    """CANDADO. El master lo vio en su móvil el 24/08: el aviso decía «el
    servidor no responde, espera un momento» y, pegado detrás, «escribe al
    menos el ancho de la pared». Dos causas distintas en la misma frase.

    Si el servidor está reiniciándose, escribir el ancho no arregla nada: se le
    manda a hacer algo inútil y encima se le sugiere que la culpa es suya."""
    bloque = _bloque_que_hacer()
    assert "esFalloDelServidor" in bloque, \
        "el consejo ya no distingue un fallo del servidor de una falta de datos"
    corte = bloque.index("esFalloDelServidor")
    escribe = bloque.index("Escribe al menos el ancho")
    assert corte < escribe, (
        "el consejo de escribir el ancho se da ANTES de comprobar si el fallo "
        "era del servidor: vuelve el aviso que se contradice a sí mismo.")


# ── La PLANTA tenía el mismo fallo que el alzado ─────────────────────────────

def _fuente_de(nombre):
    with open(RUTA, encoding="utf-8") as f:
        codigo = f.read()
    for nodo in ast.walk(ast.parse(codigo)):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.name == nombre:
            return ast.get_source_segment(codigo, nodo) or ""
    raise AssertionError(f"ya no existe {nombre} en routes/estudio_cocinas.py")


def test_la_planta_no_se_inventa_una_pared_de_400():
    """CANDADO: caía a 400x240 en silencio y salía una planta con cotas que
    nadie había medido. Es el mismo fallo que tenía el alzado."""
    cuerpo = _fuente_de("generar_plano_2d")
    assert "'ancho': 400" not in cuerpo and '"ancho": 400' not in cuerpo, \
        "la planta vuelve a inventarse una pared de 400 cm cuando no hay medidas"
    assert "status_code=422" in cuerpo, \
        "la planta ya no pide las medidas cuando faltan: las inventa"


def test_la_planta_tampoco_disfraza_el_422_de_averia():
    cuerpo = _fuente_de("generar_plano_2d")
    manejadores = []
    for nodo in ast.walk(ast.parse(cuerpo)):
        if isinstance(nodo, ast.Try):
            for h in nodo.handlers:
                if isinstance(h.type, ast.Name):
                    manejadores.append(h.type.id)
    assert "HTTPException" in manejadores, \
        "la planta se traga el 422 y lo devuelve como un 500 de servidor caído"
