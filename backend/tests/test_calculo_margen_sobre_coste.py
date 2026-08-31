# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL MARGEN SE CUENTA DESDE EL COSTE HASTA LA VENTA.

El master, 31/08: «el margen que lo ponga al incrementar desde costo hasta venta
y no al revés».

    margen % = (PVP − coste) / COSTE × 100

Antes se dividía entre el PVP —el «margen comercial» de los libros—. No estaba
mal calculado: estaba contado al revés de como se decide un precio en esta casa,
que es partiendo del coste y subiendo. En el presupuesto que lo destapó, un
mueble de 128,43 € que se vende a 206,46 € salía en 37,8 %, y lo que se quiere
leer ahí es que se le ha subido un 60,8 %.

LO QUE HABÍA QUE VIGILAR AL CAMBIARLO
-------------------------------------
1. EL SEMÁFORO. Los umbrales eran 40 % y 25 % SOBRE EL PVP. Cambiar la base y
   dejar los números habría repintado la pantalla entera sin que nadie lo
   decidiera: un mueble con un 20 % sobre PVP da un 25 % sobre coste, y con el
   corte en 25 pasaría de rojo a ámbar solo. La conversión es exacta —un margen
   `m` sobre PVP es `m / (100 − m)` sobre coste—, así que los MISMOS muebles se
   pintan del MISMO color que antes. Para mover el criterio hay que cambiar esos
   dos números a propósito.

2. SIN COSTE NO HAY INCREMENTO. Dividiendo entre el PVP, una línea sin coste
   daba un cómodo 100 %. Dividiendo entre el coste, dividiría entre cero. Se
   devuelve `null` y se pinta «—»: no se puede decir cuánto has subido algo que
   partía de cero (CLAUDE.md, regla 7).

3. LAS DOS PANTALLAS CUENTAN LO MISMO. El Presupuestador y Rentabilidad MV
   enseñan el margen del mismo mueble. Con dos fórmulas, una diría 37,8 % y la
   otra 60,8 % y ninguna parecería un error.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def _ejecuta(casos):
    """EJECUTA `margenSobreCoste` y `SEMAFORO_MARGEN` en node, los de verdad."""
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar el cálculo de verdad")
    cuerpo = sin_comentarios(_lee(RENT))
    fn = _bloque(cuerpo, "export const margenSobreCoste", "\n};")
    conv = _bloque(cuerpo, "const _sobrePvpAsobreCoste", ";")
    sem = _bloque(cuerpo, "export const SEMAFORO_MARGEN = {", "};")
    js = "%s\n%s\n%s\nconsole.log(JSON.stringify({r: %s.map(([p, c]) => margenSobreCoste(p, c)), s: SEMAFORO_MARGEN}));" % (
        fn.replace("export const", "const"), conv, sem.replace("export const", "const"),
        json.dumps(list(casos)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"el cálculo del margen no se ejecuta: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_EL_MARGEN_SE_CUENTA_SOBRE_EL_COSTE():
    """Los números del presupuesto que lo destapó (master, 31/08)."""
    salida = _ejecuta([[206.46, 128.43], [146.52, 82.41], [352.98, 210.84], [200, 100]])
    got = [None if v is None else round(v, 1) for v in salida["r"]]
    assert got == [60.8, 77.8, 67.4, 100.0], (
        f"el margen no se cuenta desde el coste hasta la venta: {got}. "
        "Sobre el PVP, esos mismos muebles darían 37,8 / 43,8 / 40,3 / 50,0.")


def test_SIN_COSTE_NO_HAY_INCREMENTO():
    """Dividir entre cero, o entre un coste que no se sabe, no da un 100 % ni un
    infinito: da «no se sabe» (regla 7)."""
    salida = _ejecuta([[200, 0], [200, None], [200, -5], [None, 100], [200, "x"]])
    assert salida["r"] == [None, None, None, None, None], (
        f"un coste que no existe está produciendo un porcentaje: {salida['r']}")


def test_EL_SEMAFORO_PINTA_LOS_MISMOS_MUEBLES_QUE_ANTES():
    """Los umbrales se TRADUJERON, no se reescribieron: 40 % y 25 % sobre PVP
    son 66,7 % y 33,3 % sobre coste. Con los números viejos, un mueble con un
    20 % sobre PVP (25 % sobre coste) habría pasado de rojo a ámbar solo."""
    sem = _ejecuta([])["s"]
    assert round(sem["bien"], 1) == 66.7, (
        f"el umbral verde no equivale al 40 % sobre PVP de siempre: {sem['bien']}")
    assert round(sem["regular"], 1) == 33.3, (
        f"el umbral ámbar no equivale al 25 % sobre PVP de siempre: {sem['regular']}")

    # La frontera, comprobada por los dos lados con muebles de verdad.
    justo_verde = _ejecuta([[100, 60]])["r"][0]      # 40 % sobre PVP
    assert justo_verde >= sem["bien"], "un mueble que antes era verde ya no lo es"
    rojo = _ejecuta([[100, 80]])["r"][0]             # 20 % sobre PVP
    assert rojo < sem["regular"], "un mueble que antes era rojo se ha puesto ámbar"


def test_LOS_UMBRALES_NO_ESTAN_ESCRITOS_A_MANO():
    """Escritos a mano, cambiar la base del margen los deja diciendo otra cosa
    sin que nadie lo note. Se derivan de los de siempre."""
    cuerpo = sin_comentarios(_lee(RENT))
    sem = _bloque(cuerpo, "export const SEMAFORO_MARGEN = {", "};")
    assert "_sobrePvpAsobreCoste(40)" in sem and "_sobrePvpAsobreCoste(25)" in sem, (
        f"los umbrales están escritos a mano: {sem.strip()}")


def test_NINGUNA_PANTALLA_DIVIDE_YA_ENTRE_EL_PVP():
    """Con dos fórmulas, una pantalla diría 37,8 % y la otra 60,8 % del mismo
    mueble, y ninguna parecería un error."""
    for ruta in (RENT, CM3):
        cuerpo = sin_comentarios(_lee(ruta))
        sobrantes = re.findall(r"margen[A-Za-z]*\s*/\s*[A-Za-z.]*pvp[A-Za-z]*", cuerpo, re.I)
        assert not sobrantes, (
            f"{os.path.basename(ruta)} sigue contando algún margen sobre el PVP: {sobrantes}")


def test_LAS_DOS_PANTALLAS_USAN_LA_MISMA_FUNCION():
    """Una copia de la fórmula se separa; y aquí separarse es enseñar dos
    márgenes distintos del mismo mueble."""
    cm3 = sin_comentarios(_lee(CM3))
    assert "margenSobreCoste" in cm3 and "SEMAFORO_MARGEN" in cm3, (
        "el Presupuestador no usa la función común del margen")
    imports = _bloque(cm3, "import { despiece,", "from './RentabilidadMV';")
    assert "margenSobreCoste" in imports and "SEMAFORO_MARGEN" in imports, (
        "el Presupuestador tiene su propia copia de la fórmula o de los umbrales")
    fila = _bloque(cm3, "const margenPct =", ";")
    assert "margenSobreCoste(pvp, coste)" in fila, (
        f"la fila calcula el margen por su cuenta: {fila.strip()}")


def test_LA_PANTALLA_DICE_QUE_ES_SOBRE_EL_COSTE():
    """Un 60,8 % leído como margen comercial es un precio mal puesto: el mismo
    mueble sobre PVP da 37,8 %. El rótulo tiene que decir sobre qué se cuenta."""
    for ruta in (RENT, CM3):
        cuerpo = sin_comentarios(_lee(ruta))
        assert "s/coste" in cuerpo, (
            f"{os.path.basename(ruta)} enseña un margen sin decir que es sobre el coste")
    cm3 = sin_comentarios(_lee(CM3))
    assert ">Margen s/coste<" in cm3, "la cabecera de la tabla no lo dice"
    assert "de incremento sobre un coste de" in cm3, (
        "el texto de ayuda de la celda no explica sobre qué se ha calculado")
