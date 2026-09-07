# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
SI LA MEDIDA NO CABE EN EL ESCALÓN, SE SUBE AL SIGUIENTE.

El master, 07/09/2026: «que me deje modificar las medidas, y si me paso, por
ejemplo en columna de 200, aplique la tarifa de 220; y en los muebles altos, si
pongo 75 de altura, que aplique la tarifa de 90».

Un alto de 75 no se fabrica al precio del de 70: no cabe. Es el mismo criterio
que la tarifa de ACB ya aplica a las medidas especiales (CLAUDE.md, regla 31):
se factura la casilla INMEDIATA SUPERIOR, y nunca se interpola.

LO QUE HAY QUE VIGILAR, QUE ES POR DÓNDE SE ESCAPA EL DINERO
────────────────────────────────────────────────────────────
1. QUE SUBA, y con el precio detrás. Sin recalcular, el escalón diría 90 y el
   importe seguiría siendo el de 70.
2. QUE NO BAJE NUNCA. Escribir 65 en un alto tarifado a 90 no puede devolverlo
   a 70: eso abarata el presupuesto solo, mientras alguien ajusta cotas, que es
   lo que CLAUDE.md prohíbe. Para bajar está el desplegable, que es una
   decisión de una persona.
3. QUE UN PRECIO PACTADO A MANO SIGA MANDANDO. Si no, escribir una cota
   devuelve el presupuesto al precio de catálogo sin decir nada.
4. QUE LO QUE NO CABE EN NINGÚN ESCALÓN SE DIGA. Una columna de 240 no existe
   en MV; tarifarla como una de 220 es cobrar de menos un mueble que además va
   especial (regla 7).
5. QUE SE VEA POR QUÉ HA CAMBIADO EL PRECIO. Si el escalón sube solo y no se
   dice, el total se mueve y nadie sabe de dónde ha salido.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")
TARIFAS = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")


def _lee():
    with open(CM3, "r", encoding="utf-8") as f:
        return f.read()


def _trozo(nombre, corte=r"\n  const \w+ = "):
    src = _lee()
    i = src.index(f"  const {nombre} = ")
    m = re.search(corte, src[i + 10:])
    return src[i:i + 10 + m.start()] if m else src[i:]


def _corre(muebles_y_alturas):
    """EJECUTA `subeElEscalonSiNoCabe` —la de verdad— contra la tarifa real.

    Se le da también `alturasDe`, `puntosLocal` y las constantes de las que
    depende: si se probara con una copia, esto no diría nada del código que se
    ejecuta en la pantalla.
    """
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar la función de verdad")
    with open(TARIFAS, "r", encoding="utf-8") as f:
        datos = json.load(f)
    fams = datos["tariffs"]["T1"]
    pv = datos["_meta"]["pointValue"]
    src = _lee()
    piezas = [
        _trozo("OPCIONES_ALTURA", r"\n  //"),
        _trozo("ANCHO_POR_DEFECTO_LINEAL", r"\n"),
        _trozo("alturasDe"),
        # `puntosLocal` le pregunta a `entradaDeTarifa` (el buscador único que
        # sabe que «B45D» se escribe «B45D/I»): sin ella, node revienta.
        _trozo("entradaDeTarifa", r"\n  const \w+ = |\n  useEffect\("),
        _trozo("puntosLocal"),
        _trozo("subeElEscalonSiNoCabe", r"\n  const \w+ = |\Z"),
    ]
    js = (f"const familias = {json.dumps(fams)};\nconst pv = {pv};\n"
          + "\n".join(p.replace("  const ", "const ", 1) for p in piezas)
          + f"\nconst CASOS = {json.dumps(muebles_y_alturas)};\n"
          + "console.log(JSON.stringify(CASOS.map(([m, h]) => {\n"
          + "  const r = subeElEscalonSiNoCabe(m, h);\n"
          + "  return { alto: r.alto, pvp: r.pvp, subido: !!r.escalonSubido, obs: r.obs || '' };\n"
          + "})));")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node falló:\n{r.stderr[-2500:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _alto(cod="A60D/I", alto=70, **extra):
    return dict({"cod": cod, "familia": "ALTO", "alto": alto, "qty": 1}, **extra)


def _columna(cod="CD50D/I", alto=200, **extra):
    return dict({"cod": cod, "familia": "COLUMNA_DESPENSERO", "alto": alto, "qty": 1}, **extra)


# ─── LOS DOS EJEMPLOS DEL MASTER ─────────────────────────────────────────────

def test_UN_ALTO_DE_75_SE_TARIFA_A_90():
    """«En los muebles altos, si pongo 75 de altura, que aplique la de 90»."""
    (r,) = _corre([[_alto(alto=70), 75]])
    assert r["alto"] == 90, f"se ha quedado en el escalón de {r['alto']}"
    assert r["subido"] is True


def test_UNA_COLUMNA_QUE_SE_PASA_DE_200_SE_TARIFA_A_220():
    """«Si me paso, por ejemplo en columna de 200, aplique la tarifa de 220»."""
    (r,) = _corre([[_columna(alto=200), 210]])
    assert r["alto"] == 220
    assert r["subido"] is True


def test_EL_PRECIO_SUBE_CON_EL_ESCALON():
    """Sin esto, el escalón diría 90 y el importe seguiría siendo el de 70:
    el número que se firma sería el del mueble que no es.

    Con cifras de la tarifa T1 de verdad: un «A60D/I» son 47 puntos a 70 y 51 a
    90, y el punto vale 3,33 €. O sea 156,51 € contra 169,83 € — los mismos
    números que ya cita la regla 13 de CLAUDE.md.
    """
    with open(TARIFAS, "r", encoding="utf-8") as f:
        datos = json.load(f)
    p70, p90 = datos["tariffs"]["T1"]["ALTO"]["items"]["A60D/I"]
    pv = datos["_meta"]["pointValue"]
    (r,) = _corre([[_alto(alto=70), 75]])
    assert r["alto"] == 90
    assert r["pvp"] == round(p90 * pv * 100) / 100, (
        f"el escalón ha subido a 90 y el precio no le sigue: {r['pvp']}")
    assert r["pvp"] != round(p70 * pv * 100) / 100, (
        "se ha quedado con el precio del escalón de 70")

    # Y la columna igual: 102 puntos a 200, 107 a 220.
    c200, c220 = datos["tariffs"]["T1"]["COLUMNA_DESPENSERO"]["items"]["CD50D/I"]
    (rc,) = _corre([[_columna(alto=200), 210]])
    assert rc["alto"] == 220
    assert rc["pvp"] == round(c220 * pv * 100) / 100
    assert rc["pvp"] != round(c200 * pv * 100) / 100


# ─── LO QUE NO PUEDE PASAR ───────────────────────────────────────────────────

def test_NUNCA_BAJA_EL_ESCALON():
    """Escribir 65 en un alto tarifado a 90 no lo devuelve a 70: eso abarata el
    presupuesto solo mientras alguien ajusta cotas."""
    (r,) = _corre([[_alto(alto=90), 65]])
    assert r["alto"] == 90, "ha bajado el escalón solo, y con él el precio"
    assert r["subido"] is False


def test_SI_CABE_NO_SE_TOCA_NADA():
    """70 en un escalón de 70 no mueve ni el escalón ni el precio."""
    (r,) = _corre([[_alto(alto=70), 70], ])
    assert r["alto"] == 70 and r["subido"] is False


def test_UN_PRECIO_PACTADO_A_MANO_SIGUE_MANDANDO():
    """Si no, escribir una cota devuelve el presupuesto al precio de catálogo
    sin decir nada — el mismo criterio que `setAlto`."""
    (r,) = _corre([[_alto(alto=70, pvp=123.45, pvpManual=True), 75]])
    assert r["alto"] == 90, "el escalón sí tiene que subir: es lo que se fabrica"
    assert r["pvp"] == 123.45, "el precio pactado se ha perdido"


def test_LO_QUE_NO_CABE_EN_NINGUN_ESCALON_SE_DICE():
    """Una columna de 240 no existe en MV. Se sube al mayor y se avisa EN LA
    LÍNEA, que es donde lo ve quien monta el pedido (regla 7)."""
    (r,) = _corre([[_columna(alto=200), 240]])
    assert r["alto"] == 220
    assert "fuera de tarifa" in r["obs"], (
        f"se ha tarifado una columna de 240 como si cupiera: obs={r['obs']!r}")


def test_el_aviso_de_fuera_de_tarifa_NO_SE_DUPLICA():
    """Tecleando la cota se dispara una vez por pulsación: sin la comprobación,
    la observación se llenaba de la misma frase repetida."""
    (r,) = _corre([[_columna(alto=220, obs="ALTURA 240 cm: fuera de tarifa (el mayor es 220). Confirmar con MV."), 240]])
    assert r["obs"].count("fuera de tarifa") == 1


def test_UN_MUEBLE_SIN_ESCALONES_NO_SE_TOCA():
    """Un lineal o una pieza sin alturas de tarifa no tiene escalón que subir."""
    (r,) = _corre([[{"cod": "LCB", "familia": "LATERALES_COLOR", "alto": None, "qty": 1}, 85]])
    assert r["subido"] is False


# ─── QUE SE VEA ──────────────────────────────────────────────────────────────

def test_la_pantalla_DICE_que_ha_subido_el_escalon():
    """Si el escalón sube solo y no se dice, el total se mueve y nadie sabe de
    dónde ha salido."""
    src = _lee()
    assert 'data-testid="cm3-escalon-subido"' in src
    i = src.index('data-testid="cm3-escalon-subido"')
    assert "m.escalonSubido &&" in src[max(0, i - 400):i]


def test_la_medida_se_escribe_ANTES_de_mirar_el_escalon():
    """El orden importa: si se mirara el escalón con la medida vieja, haría
    falta teclear dos veces para que subiera."""
    cuerpo = _trozo("setMedidaReal", r"\n  /\*\*")
    i = cuerpo.index("const conMedida")
    j = cuerpo.index("subeElEscalonSiNoCabe(conMedida")
    assert i < j, "se está evaluando el escalón sobre el mueble sin la medida nueva"
