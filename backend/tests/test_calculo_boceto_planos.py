# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del TRAZO de los planos vectoriales.

LA REGLA CAMBIO, Y LA DIJO EL MASTER MIRANDO SU ALZADO
------------------------------------------------------
    «no me gusta lo de los trazos cuando haces el alzado y la planta,
     prefiero que lo hagas con lineas rectas; queda muy distorsionado y
     queda muy feo»

Antes esta prueba protegia lo contrario: que el alzado y la planta pudieran
salir a lapiz. Se construyo asi porque el master habia ensenriado sus
referencias a mano; visto en su plano de verdad, decidio que no. La prueba no
se borra —eso dejaria el trazo sin nadie que lo vigile— sino que pasa a
proteger la regla nueva.

Y la regla nueva tiene una razon, no es un gusto: la planta y el alzado son
planos de TALLER. Con ellos se corta. Una linea que tiembla no solo afea: hace
dudar de si esa pared, esa balda o ese hueco estan donde parece. El lapiz se
queda en el boceto en PERSPECTIVA, que es un dibujo para ensenriar y no lleva
cotas.

Lo que se protege:

1. LINEA RECTA EN PLANTA, ALZADO Y ALZADO DE ARMARIO. Los tres son planos con
   los que se fabrica.

2. SE APAGA DE ENTRADA, NO SOLO AL SALIR. `path.sketch` es un ajuste GLOBAL de
   matplotlib, del proceso, no de la peticion. Limpiarlo solo en el `finally`
   protege al SIGUIENTE, no a este: si una peticion anterior lo dejo puesto
   —porque el proceso se corto por medio— este plano sale temblado sin que
   nadie lo haya pedido y sin dar ningun error. Paso: un alzado con el boceto
   apagado salio a lapiz.

3. NADIE PIDE UN FLAG QUE YA NO SE OBEDECE. Aceptar `boceto` en el alzado y no
   hacerle caso es peor que no aceptarlo, porque el que lo enciende cree que
   ha cambiado algo. Ni la pantalla lo manda ni el armario lo declara.

4. EL LAPIZ SIGUE VIVO DONDE TIENE SENTIDO: el boceto en perspectiva.

5. NO SE USA `plt.xkcd()`. Cambia tambien la tipografia y depende de una fuente
   que puede no estar instalada en el servidor. Una cota que no se lee no es
   una cota.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COCINAS = os.path.join(RAIZ, "backend", "routes", "estudio_cocinas.py")
ARMARIO = os.path.join(RAIZ, "backend", "routes", "armarios_alzado.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _cuerpo_de(fuente, decorador):
    """El codigo de un endpoint, desde su decorador hasta el siguiente."""
    i = fuente.index(decorador)
    j = fuente.find("\n@router.", i + len(decorador))
    return fuente[i:j if j != -1 else len(fuente)]


# El temblor, escrito como lo escribe matplotlib: tres numeros entre
# parentesis. Que aparezca en un plano de taller es el fallo.
_TEMBLOR = re.compile(r'path\.sketch"\]\s*=\s*\(')


# ─── 1. Linea recta en los planos con los que se fabrica ────────────────────

def test_la_planta_de_cocina_sale_a_linea_recta():
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/plano-2d")')
    assert not _TEMBLOR.search(cuerpo), (
        "la planta vuelve a dibujarse a lapiz: es un plano de taller y el "
        "temblor hace dudar de donde esta cada pared")


def test_el_alzado_de_cocina_sale_a_linea_recta():
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/alzado")')
    assert not _TEMBLOR.search(cuerpo), "el alzado de cocina vuelve a dibujarse a lapiz"


def test_el_alzado_de_armario_sale_a_linea_recta():
    assert not _TEMBLOR.search(_leer(ARMARIO)), (
        "el alzado de armario vuelve a dibujarse a lapiz")


# ─── 2. Se apaga de ENTRADA, no solo al salir ───────────────────────────────

def _apaga_de_entrada(cuerpo):
    """¿Pone `path.sketch` a None ANTES de dibujar, no solo en el `finally`?"""
    antes = cuerpo.split("finally:")[0]
    return bool(re.search(r'path\.sketch"\]\s*=\s*None', antes))


def _limpia_en_finally(cuerpo):
    tras_finally = cuerpo.split("finally:")
    return any(re.search(r'path\.sketch"\]\s*=\s*None', trozo) for trozo in tras_finally[1:])


def test_la_planta_apaga_el_lapiz_antes_de_dibujar():
    """CANDADO PRINCIPAL. Limpiar solo en el `finally` protege al SIGUIENTE
    plano, no a este."""
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/plano-2d")')
    assert _apaga_de_entrada(cuerpo), (
        "`path.sketch` es global del proceso: si no se apaga al entrar, una "
        "peticion anterior que lo dejara puesto hace salir esta planta "
        "temblada sin que nadie lo pida y sin dar error")


def test_el_alzado_apaga_el_lapiz_antes_de_dibujar():
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/alzado")')
    assert _apaga_de_entrada(cuerpo), "el alzado no apaga `path.sketch` al entrar"


def test_el_alzado_de_armario_apaga_el_lapiz_antes_de_dibujar():
    assert _apaga_de_entrada(_leer(ARMARIO)), (
        "el alzado de armario no apaga `path.sketch` al entrar")


def test_los_tres_siguen_limpiando_al_salir():
    """Cinturon y tirantes: apagarlo al entrar protege a este plano; limpiarlo
    al salir protege al siguiente, que puede dibujarlo otro modulo."""
    for cuerpo, quien in (
        (_cuerpo_de(_leer(COCINAS), '@router.post("/plano-2d")'), "la planta"),
        (_cuerpo_de(_leer(COCINAS), '@router.post("/alzado")'), "el alzado"),
        (_leer(ARMARIO), "el alzado de armario"),
    ):
        assert _limpia_en_finally(cuerpo), f"{quien} no limpia `path.sketch` en `finally`"


# ─── 3. Nadie pide un flag que ya no se obedece ─────────────────────────────

def test_la_pantalla_ya_no_pide_boceto_en_los_planos():
    """Aceptar el flag y no hacerle caso es peor que no aceptarlo: quien lo
    enciende cree que ha cambiado algo."""
    fuente = _leer(ESTUDIO)
    assert "bocetoAlzado" not in fuente, (
        "sigue habiendo interruptor de boceto para los planos, y ya no hace "
        "nada: un boton que no cambia nada es peor que no tener boton")


def test_el_alzado_de_armario_ya_no_declara_el_flag():
    assert not re.search(r"^\s*boceto\s*:", _leer(ARMARIO), re.M), (
        "el alzado de armario sigue aceptando `boceto` y ya no lo obedece")


# ─── 4. El lapiz sigue vivo donde tiene sentido ─────────────────────────────

def test_el_boceto_en_perspectiva_si_dibuja_a_lapiz():
    """Es un dibujo para ensenriar, sin cotas. Ahi el trazo a mano es lo que se
    pidio, y quitarlo de todas partes se habria llevado tambien esto."""
    cuerpo = _cuerpo_de(_leer(COCINAS), '@router.post("/perspectiva")')
    assert _TEMBLOR.search(cuerpo), (
        "el boceto en perspectiva ha dejado de dibujarse a lapiz")
    assert _limpia_en_finally(cuerpo), (
        "la perspectiva deja el lapiz puesto y el siguiente plano sale "
        "temblado: es justo como aparecio el fallo")


# ─── 5. Nunca `plt.xkcd()` ──────────────────────────────────────────────────

def _sin_comentarios(fuente):
    """El codigo, sin las lineas de comentario.

    Hace falta porque el propio codigo EXPLICA por que no se usa `xkcd`, y
    buscar la palabra a secas encontraria esa explicacion y daria por roto lo
    que precisamente esta bien.
    """
    return "\n".join(l for l in fuente.split("\n") if not l.strip().startswith("#"))


def test_no_se_usa_xkcd_en_ningun_plano():
    for ruta in (COCINAS, ARMARIO):
        assert "xkcd" not in _sin_comentarios(_leer(ruta)), (
            f"{os.path.basename(ruta)} usa xkcd(): las cotas pueden dejar de leerse")
