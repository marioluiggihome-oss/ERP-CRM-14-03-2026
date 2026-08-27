# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: si la imagen no se puede leer, NO se llama al modelo de vision.

El 07/08 el master pulso "Detectar auto (IA)" y le salio esto:

    400 INVALID_ARGUMENT. Unable to process input image. Please retry or
    report in https://developers.generativeai.google/guide/troubleshooting

Un error de Google, con enlace a la documentacion de Google, que no dice ni lo
que paso ni que hacer. La causa estaba dos pasos antes: la imagen llegaba
inservible, la normalizacion con PIL fallaba, y el codigo se limitaba a dejar un
aviso en el log y llamar a Gemini IGUALMENTE.

Ese patron --- avisar por lo bajo y seguir --- es el que convierte un fallo
localizable en uno que aparece disfrazado de otra cosa mucho mas lejos. Si la
imagen no se puede preparar no hay nada que analizar: hay que cortar ahi y
decirlo en castellano.

Pillow esta fijado en requirements.txt (pillow==12.1.0) y lo usan otros cinco
sitios del backend, asi que un fallo de normalizacion significa que la imagen es
mala, no que falte la libreria.
"""
import ast
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(BACKEND, "routes", "ai_engine.py")


def _funcion(nombre):
    with open(RUTA, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"no se encuentra la funcion {nombre} en ai_engine.py")


def test_si_no_se_puede_normalizar_la_imagen_se_corta():
    """CANDADO: el `except` de la normalizacion tiene que LEVANTAR, no seguir.

    Se mira el arbol de sintaxis, no el texto: lo que importa es que ese camino
    termine en un raise, se escriba como se escriba.
    """
    fn = _funcion("detect_installations")

    manejadores = [h for nodo in ast.walk(fn) if isinstance(nodo, ast.Try)
                   for h in nodo.handlers]
    # El manejador de la normalizacion es el que registra el aviso con ese texto.
    normalizacion = [
        h for h in manejadores
        if "no se pudo normalizar la imagen" in ast.dump(h)
    ]
    assert normalizacion, (
        "ya no existe el manejador de la normalizacion de imagen; si se ha "
        "reorganizado, hay que actualizar esta prueba a proposito"
    )

    for h in normalizacion:
        assert any(isinstance(n, ast.Raise) for n in ast.walk(h)), (
            "la normalizacion vuelve a fallar EN SILENCIO: se avisa por el log y "
            "se sigue llamando al modelo con una imagen que no se pudo preparar. "
            "Eso devuelve el error de Google que no dice nada. Tiene que cortar."
        )


def test_el_mensaje_de_corte_es_para_una_persona():
    """No vale con cortar: hay que decir que hacer, y en castellano."""
    with open(RUTA, encoding="utf-8") as f:
        codigo = f.read()
    assert "No se pudo leer la imagen del render" in codigo, (
        "el corte tiene que explicarse en castellano, no con el error crudo del "
        "proveedor"
    )
