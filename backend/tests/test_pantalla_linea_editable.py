# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA LÍNEA IMPORTADA SE PUEDE CORREGIR ENTERA.

El master, 31/08: «que la línea importada se puedan modificar todos los campos,
desde unidades, descripción, cantidad, precio, etc. … y totalice abajo con los
cambios».

Una relación que entra por PDF trae lo que el proveedor escribió, no lo que se
va a vender. Sin poder tocarla, la única salida era borrar la línea y volver a
teclearla a mano — y entonces se pierde el código, la familia y el despiece.

LAS DOS COSAS QUE HAY QUE SOSTENER, Y LA SEGUNDA ES LA QUE MUERDE
-----------------------------------------------------------------
1. QUE SE PUEDA TOCAR, y que el total de abajo lo siga.

2. QUE UN PRECIO ESCRITO A MANO NO SE BORRE SOLO.
   El PVP de una línea se recalcula desde la tarifa al cambiar el alto o el
   escalón de ancho. Sin la marca `pvpManual`, el master escribe un precio
   pactado, después ajusta el alto —que es lo normal— y el precio VUELVE al de
   catálogo sin decir nada. El presupuesto sale por otra cifra, se imprime y se
   manda. No hay error, no hay aviso: solo un número distinto.

3. Y QUE RENOMBRAR NO CAMBIE EL CÁLCULO.
   `familia` decide el despiece, el coste y si la línea comisiona (regla 16).
   La descripción se guarda APARTE (`desc`). Si escribir un texto pisara la
   familia, renombrar «BAJO» a «Mueble del office» sacaría esa línea del cálculo
   de la comisión del comercial sin que nadie lo hubiera pedido.

LA COMA DEL TECLADO ESPAÑOL: `Number('40,5')` es `NaN`. Sin admitir la coma, el
precio tecleado se pierde EN SILENCIO — es el mismo cuidado que ya lleva la
pantalla de medidas definitivas (CLAUDE.md, regla del escalón).
"""
import json
import os
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _lee():
    with open(CM3, "r", encoding="utf-8") as f:
        return f.read()


def test_TODOS_LOS_CAMPOS_DE_LA_LINEA_SE_PUEDEN_TOCAR():
    cuerpo = sin_comentarios(_lee())
    for campo, testid in (("descripción", "cm3-desc-linea"),
                          ("ancho", "cm3-ancho-linea"),
                          ("precio", "cm3-pvp-linea")):
        assert testid in cuerpo, f"la línea no deja cambiar {campo}"
    # La cantidad ya se podía, y tiene que seguir pudiéndose.
    assert "onChange={e => setQty(m._k, e.target.value)}" in cuerpo, (
        "se ha perdido la edición de la cantidad")


def test_EL_TOTAL_DE_ABAJO_SALE_DE_LAS_LINEAS_Y_NO_DE_OTRO_SITIO():
    """«Y totalice abajo con los cambios». Si el subtotal se guardara aparte,
    tocar una línea dejaría de moverlo."""
    cuerpo = sin_comentarios(_lee())
    assert "const subtotalBruto = filas.reduce(" in cuerpo, (
        "el subtotal ya no se calcula desde las líneas: los cambios de una "
        "línea no llegarían al total")
    i = cuerpo.index("const subtotalBruto = filas.reduce(")
    linea = cuerpo[i:cuerpo.index("\n", i)]
    assert "m.pvp" in linea and "m.qty" in linea, (
        f"el subtotal no usa el precio y las unidades de cada línea: {linea}")


# ── EJECUTANDO LOS SETTERS DE VERDAD ─────────────────────────────────────────

def _corre(guion):
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar los setters de verdad")
    cuerpo = _lee()
    i = cuerpo.index("const setPvp = (k, v)")
    fin = cuerpo.index("\n  }));", cuerpo.index("const setMedidaMueble")) + len("\n  }));")
    fuente = cuerpo[i:fin]
    js = """
const arranque = %s;
let prev = arranque;
const setMuebles = (f) => { prev = f(prev); };
const puntosLocal = (m) => 999;   // «el precio de tarifa», para distinguirlo
%s
const total = () => prev.reduce((t, m) => t + (Number(m.pvp) || 0) * (Number(m.qty) || 1), 0);
%s
""" % (json.dumps(guion["muebles"]), fuente, guion["acciones"])
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"los setters no se ejecutan: {r.stderr[-400:]}"
    return json.loads(r.stdout)


UNA_LINEA = [{"_k": "a", "cod": "B90D/I", "familia": "BAJO", "pvp": 276, "qty": 2, "alto": 70}]


def test_CAMBIAR_EL_PRECIO_MUEVE_EL_TOTAL():
    out = _corre({"muebles": UNA_LINEA, "acciones": """
        const antes = total();
        setPvp('a', '250');
        console.log(JSON.stringify([antes, total(), prev[0].pvp]));
    """})
    assert out[0] == 552, f"el total de partida debería ser 276x2: {out[0]}"
    assert out[1] == 500, f"tras poner 250 el total debería ser 500: {out[1]}"
    assert out[2] == 250


def test_LA_COMA_DEL_TECLADO_ESPAÑOL_NO_PIERDE_EL_PRECIO():
    """`Number('40,5')` es NaN. Sin admitir la coma, el precio se pierde sin
    que salte nada: el campo se queda como estaba y parece que no se ha
    tecleado bien."""
    out = _corre({"muebles": UNA_LINEA, "acciones": """
        setPvp('a', '40,50');
        console.log(JSON.stringify([prev[0].pvp, total()]));
    """})
    assert out[0] == 40.5, (
        f"un precio tecleado con coma se ha perdido: {out[0]}. En un teclado "
        "español se escribe 40,50")
    assert out[1] == 81.0


def test_UN_PRECIO_A_MANO_NO_LO_PISA_EL_RECALCULO():
    """LO QUE DE VERDAD PROTEGE ESTE CANDADO. Se pone un precio pactado, se
    cambia el alto —que es lo normal— y el precio tiene que seguir ahí."""
    cuerpo = _lee()
    i = cuerpo.index("const setAlto = (k, v)")
    setalto = sin_comentarios(cuerpo[i:cuerpo.index("\n  }));", i)])
    assert "m.pvpManual" in setalto, (
        "cambiar el alto vuelve a calcular el precio desde la tarifa aunque se "
        "haya escrito uno a mano: el precio pactado desaparece en silencio y el "
        "presupuesto sale por otra cifra")
    j = cuerpo.index("const setAnchoTarifa = (k, v)")
    setancho = sin_comentarios(cuerpo[j:cuerpo.index("\n  }));", j)])
    assert "m.pvpManual" in setancho, (
        "cambiar el escalón de ancho pisa el precio escrito a mano")


def test_SE_PUEDE_VOLVER_AL_PRECIO_DE_TARIFA():
    """Hace falta una forma de deshacer que no sea borrar la línea y volver a
    añadirla — eso perdería el código, la familia y el despiece."""
    out = _corre({"muebles": UNA_LINEA, "acciones": """
        setPvp('a', '250');
        const manual = !!prev[0].pvpManual;
        setPvp('a', '');
        console.log(JSON.stringify([manual, prev[0].pvp, !!prev[0].pvpManual]));
    """})
    assert out[0] is True, "poner un precio no lo marca como escrito a mano"
    assert out[1] == 999, (
        f"vaciar el precio no vuelve al de tarifa: {out[1]}")
    assert out[2] is False, (
        "la línea sigue marcada «a mano» con el campo vacío: el próximo cambio "
        "de alto ya no le actualizaría el precio")


def test_UN_PRECIO_IMPOSIBLE_NO_ENTRA():
    out = _corre({"muebles": UNA_LINEA, "acciones": """
        setPvp('a', '-5');   const trasNegativo = prev[0].pvp;
        setPvp('a', 'abc');  const trasLetras = prev[0].pvp;
        console.log(JSON.stringify([trasNegativo, trasLetras]));
    """})
    assert out == [276, 276], (
        f"un precio negativo o que no es un número está entrando: {out}")


def test_RENOMBRAR_UNA_LINEA_NO_TOCA_SU_FAMILIA():
    """`familia` decide el despiece, el coste y si la línea comisiona (regla
    16). El rótulo va aparte."""
    cuerpo = sin_comentarios(_lee())
    i = cuerpo.index("const setDesc = (k, desc)")
    setdesc = cuerpo[i:cuerpo.index("\n", cuerpo.index("_k === k", i))]
    assert "familia" not in setdesc, (
        "escribir la descripción está tocando la familia: renombrar «BAJO» "
        "sacaría esa línea del cálculo de la comisión del comercial")
    assert "{ ...m, desc }" in setdesc


def test_LA_DESCRIPCION_SALE_DE_UN_SOLO_SITIO():
    """La usan la tabla, la ficha y el PDF. Escrita tres veces, el día que se
    cambie una la pantalla diría una cosa y el presupuesto del cliente otra —
    que es el fallo que ya tuvo el rótulo de los tramos de comisión."""
    cuerpo = sin_comentarios(_lee())
    assert "export const descDe" in cuerpo, "no hay una función única de descripción"
    assert "const descBase = descDe(m);" in cuerpo, (
        "el PDF no usa la misma descripción que la pantalla: un mueble "
        "renombrado saldría con el nombre viejo en el presupuesto del cliente")


def test_CAMBIAR_LAS_MEDIDAS_NO_MUEVE_EL_PRECIO():
    """El precio de un mueble MV sale de su CÓDIGO. Si escribir el ancho de
    fabricación lo moviera, el presupuesto cambiaría solo mientras alguien
    ajusta cotas y nadie lo relacionaría (CLAUDE.md, regla del escalón)."""
    out = _corre({"muebles": UNA_LINEA, "acciones": """
        setMedidaMueble('a', 'ancho', '92,5');
        console.log(JSON.stringify([prev[0].ancho, prev[0].pvp]));
    """})
    assert out[0] == 92.5, f"la medida no admite decimales con coma: {out[0]}"
    assert out[1] == 276, f"cambiar la medida ha movido el precio: {out[1]}"
