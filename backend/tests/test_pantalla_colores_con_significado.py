# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL COLOR DICE POR QUÉ, NO QUÉ TONO ES.

El master, 25/08/2026, después de apagar la paleta: «prepáralo» — que el color
informe en vez de decorar.

QUÉ SE MIDIÓ ANTES DE TOCAR NADA. Se contaron las palabras que aparecían cerca
de cada color en los 92 componentes. Las de dinero salían junto al 46-58% de
TODOS los colores: es un ERP, el dinero está en todas partes, así que el color
no distinguía nada. El único que significaba algo era el rojo, en el 42% de los
casos junto a «error», «borrar» o «anular». Los demás decoraban.

O sea que esto no sustituye un sistema: monta el primero que hay.

LOS ALIAS. `bg-ok-600` en vez de `bg-emerald-600`. La pantalla explica qué
significa ese verde, y el día que el verde no convenza se cambia en un sitio.

EL DINERO NO LLEVA COLOR DE ESTADO, y esa es la decisión de fondo. Un importe no
es ni bueno ni malo; pintarlo de ámbar lo convierte en un aviso permanente y
entonces deja de destacar lo que sí es un aviso. Va en `dato` y destaca por
tamaño y peso. Eso libera el ámbar para lo que significa en todas partes.
"""
import os
import re
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONT = os.path.join(RAIZ, "frontend")
CONFIG = os.path.join(FRONT, "tailwind.config.js")
RENTA = os.path.join(FRONT, "src", "components", "RentabilidadMV.jsx")
GUIA = os.path.join(RAIZ, "docs", "DISENO.md")

TOKENS = ("accion", "ok", "aviso", "error", "master", "dato")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_existen_los_seis_tokens_y_los_resuelve_tailwind():
    """No basta con que estén escritos: se le pregunta a node qué color salen.

    Un alias mal puesto (`paletaApagada.indigos`) daría `undefined` y Tailwind
    simplemente no generaría la clase: `bg-accion-600` no pintaría NADA y el
    build seguiría en verde.
    """
    guion = ("const c=require('./tailwind.config.js').theme.extend.colors;"
             "console.log(JSON.stringify(Object.fromEntries("
             "%s.map(k=>[k, c[k] && c[k]['600']]))));" % list(TOKENS))
    r = subprocess.run(["node", "-e", guion], capture_output=True, text=True,
                       cwd=FRONT, timeout=120)
    assert r.returncode == 0, f"el config no carga: {r.stderr}"
    import json
    got = json.loads(r.stdout)
    for t in TOKENS:
        assert re.match(r"^#[0-9a-f]{6}$", got.get(t) or ""), (
            f"el token «{t}» no resuelve a un color: {got.get(t)!r}. La clase "
            f"`bg-{t}-600` no pintaría nada y el build seguiría en verde.")


def test_cada_token_apunta_a_la_PALETA_APAGADA_y_no_a_un_color_suelto():
    """Si un token llevara un hexadecimal a mano, se saldría del sistema: no se
    regeneraría con la paleta y acabaría desentonando con el resto."""
    cuerpo = _lee(CONFIG)
    for t in TOKENS:
        m = re.search(rf"^\s*{t}: (\S+),", cuerpo, re.M)
        assert m, f"falta el token «{t}» en el config"
        assert m.group(1).startswith("paletaApagada."), (
            f"«{t}» no sale de la paleta apagada sino de {m.group(1)}")


def test_EL_DINERO_NO_VA_DE_COLOR_DE_ESTADO():
    """La decisión de fondo, probada donde más duele: el bloque de comisiones.

    Es el sitio con más importes por centímetro de todo el ERP. Iba entero en
    ámbar —el color de «atención»— así que la pantalla avisaba de algo
    permanentemente y por eso no avisaba de nada.
    """
    cuerpo = _lee(RENTA)
    i = cuerpo.index("Comisiones de cooperativistas")
    bloque = cuerpo[i - 1200:i + 3000]
    assert "amber" not in bloque, (
        "el bloque de comisiones ha vuelto al ámbar: un importe no es un aviso")
    assert "text-dato-900" in bloque, (
        "los importes de comisiones ya no van en `dato`; el dinero destaca por "
        "peso y tamaño, no por color de estado")


def test_la_guia_de_diseno_EXISTE_y_dice_lo_mismo_que_el_config():
    """Una guía que se contradice con el código es peor que ninguna: el
    siguiente que llegue se fía de ella y hace lo contrario de lo que hay."""
    guia = _lee(GUIA)
    for t in TOKENS:
        assert f"`{t}`" in guia, f"la guía no explica el token «{t}»"
    assert "no lleva color de estado" in guia, (
        "la guía ya no explica por qué el dinero va en gris")


def test_la_herramienta_de_avance_FUNCIONA_y_no_miente():
    """El plan de migración necesita medirse. Si el contador se rompiera y
    dijera 0 decorativas, parecería que está todo hecho."""
    r = subprocess.run(["python3", os.path.join(RAIZ, "herramientas",
                                                "avance_semantico.py")],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, f"la herramienta de avance falla: {r.stderr}"
    m = re.search(r"con significado\s*:\s*(\d+)", r.stdout)
    d = re.search(r"a[úu]n decorativas\s*:\s*(\d+)", r.stdout)
    assert m and d, f"la herramienta ya no informa del avance:\n{r.stdout}"
    assert int(m.group(1)) > 0, (
        "no queda ni una clase semántica: se ha revertido la migración entera")
    assert int(d.group(1)) > 0, (
        "dice que no quedan clases decorativas, y quedan miles. El contador "
        "está roto y el avance parecería terminado")


# ── Las tres pantallas que pidió el master (25/08) ───────────────────────────
#
# «Empieza por la de Estudio 3D y la de Cocina Montada 3 y Cocina Desmontada.»
# Cocina Desmontada es `Cascos.jsx` — el nombre del fichero no lo dice, va por
# la pestaña 'cascos' del menú.
#
# Se guarda el recuento MÍNIMO que tenía cada una al migrarla. No el exacto: si
# fuera exacto, cualquier retoque legítimo lo rompería y acabaría subiéndose el
# número sin mirar, que es como muere un candado. Con un mínimo, lo que salta es
# lo que importa — que alguien revierta la pantalla a colores sin significado.
MIGRADAS = {
    "AIRenderStudio.jsx": 150,      # Estudio 3D          (eran 183)
    "CocinaMontada3.jsx": 85,       # Cocina Montada 3    (eran 105)
    "Cascos.jsx": 38,               # Cocina Desmontada   (eran 46)
}


def test_las_tres_pantallas_del_master_SIGUEN_MIGRADAS():
    import re as _re
    comp = os.path.join(FRONT, "src", "components")
    rx = _re.compile(r"\b(?:bg|text|border|from|to|ring|divide)-(%s)-\d{2,3}"
                     % "|".join(TOKENS))
    for fichero, minimo in MIGRADAS.items():
        cuerpo = _lee(os.path.join(comp, fichero))
        n = len(rx.findall(cuerpo))
        assert n >= minimo, (
            f"{fichero} ha bajado a {n} clases con significado (había {minimo} "
            "como mínimo). Se ha revertido la pantalla a colores que no dicen "
            "nada.")


def test_los_botones_de_BORRAR_van_de_error_y_no_de_accion():
    """El fallo que casi se cuela, y que enseña por qué esto no se automatiza.

    La pantalla está en español pero los identificadores en inglés
    (`deleteOrder`, `removeLine`). Mirando solo palabras españolas, cuatro
    botones de BORRAR de Cocina Desmontada salieron clasificados como «acción»
    corriente. Un botón destructivo pintado como uno normal es exactamente lo
    que hace que el color deje de avisar.
    """
    cuerpo = _lee(os.path.join(FRONT, "src", "components", "Cascos.jsx"))
    for fn in ("deleteOrder", "removeLine"):
        # Se busca el BOTÓN, no la función: `cuerpo.find(fn)` a secas encuentra
        # primero la definición, que no lleva clases de color, y la prueba
        # fallaba sin que hubiera nada roto.
        i = cuerpo.find(f"onClick={{() => {fn}(")
        assert i > 0, f"ya no está el botón de {fn} en Cocina Desmontada"
        trozo = cuerpo[i:i + 320]
        assert "error-" in trozo, (
            f"el botón de {fn} ya no va de `error`: un borrar pintado como una "
            "acción corriente es un accidente esperando")
