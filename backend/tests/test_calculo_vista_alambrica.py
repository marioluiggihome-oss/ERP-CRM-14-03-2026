# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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
