# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA PALETA NO GRITA, Y NO SE EDITA A MANO.

El master, 25/08/2026: «cambia a diseño con colores que no griten, que queden
bien y que quede todo bastante integrado y moderno».

POR QUÉ HACE FALTA UN CANDADO PARA ESTO. Todos los demás vigilan lo que se
CALCULA y lo que la pantalla DICE. Ninguno mira cómo se VE. Un cambio estético
—o su vuelta atrás— puede entrar entero con el CI en verde y nadie se entera
hasta que lo ve un cliente.

LAS DOS COSAS QUE SE VIGILAN:

  1. Que el fichero de paleta sea EXACTAMENTE el que sale del generador. Si se
     retoca un color a mano, deja de estar razonado y nadie sabe de dónde salió.

  2. Que siga habiendo UNA SOLA clave `colors` en tailwind.config.js. Esto no es
     manía: la primera versión metió una segunda clave y en JavaScript gana la
     última — la paleta entera se descartó EN SILENCIO. El fichero estaba
     escrito, el build pasaba, y en pantalla no cambiaba nada.
"""
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONT = os.path.join(RAIZ, "frontend")
PALETA = os.path.join(FRONT, "paleta.generada.js")
CONFIG = os.path.join(FRONT, "tailwind.config.js")
GEN = os.path.join(RAIZ, "herramientas", "paleta_erp.py")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_la_paleta_es_LA_QUE_SALE_DEL_GENERADOR():
    """Se regenera en un aparte y se compara. Un color retocado a mano deja de
    tener detrás el criterio de «misma luminosidad, menos saturación»."""
    antes = _lee(PALETA)
    r = subprocess.run([sys.executable, GEN, "--escribir"], capture_output=True,
                       text=True, timeout=300, cwd=RAIZ)
    despues = _lee(PALETA)
    if antes != despues:                       # dejarlo como estaba
        with open(PALETA, "w", encoding="utf-8") as f:
            f.write(antes)
    assert r.returncode == 0, f"el generador de paleta falla: {r.stderr}"
    assert antes == despues, (
        "paleta.generada.js no coincide con lo que produce el generador: se ha "
        "editado a mano. Se regenera con "
        "`python3 herramientas/paleta_erp.py --escribir`")


def test_HAY_UNA_SOLA_CLAVE_COLORS_en_el_config():
    """El fallo que hizo que la paleta no llegara a la pantalla.

    Dos claves `colors` en el mismo objeto no dan error en JavaScript: gana la
    última y la otra desaparece sin avisar. El build seguía en verde y la
    pantalla igual que antes.
    """
    cuerpo = _lee(CONFIG)
    cuantas = len(re.findall(r"^\s*colors\s*:", cuerpo, re.M))
    assert cuantas == 1, (
        f"hay {cuantas} claves `colors` en tailwind.config.js. Con más de una, "
        "JavaScript se queda con la última y la paleta se descarta en silencio.")
    assert "...paletaApagada" in cuerpo, (
        "el config ya no esparce la paleta apagada dentro de `colors`")


def test_los_pesos_de_letra_NO_VUELVEN_a_gritar():
    """2.132 `font-bold` y 1.929 `font-black` contra 29 `font-semibold`: si todo
    va en negrísima, no hay jerarquía y nada destaca."""
    cuerpo = _lee(CONFIG)
    i = cuerpo.index("fontWeight: {")
    trozo = cuerpo[i:i + 400]
    assert "bold: '600'" in trozo, "`font-bold` ha vuelto a pesar 700 o más"
    assert "black: '700'" in trozo, "`font-black` ha vuelto a pesar 900"


def test_inter_descarga_los_pesos_que_se_piden():
    """Antes se pedía `font-bold` = 700 y el 700 no estaba en el @import: el
    navegador lo sintetizaba engordando el 600. De ahí parte del aspecto tosco.
    """
    css = _lee(os.path.join(FRONT, "src", "index.css"))
    m = re.search(r"family=Inter:wght@([0-9;]+)", css)
    assert m, "ya no se importa Inter"
    cargados = set(m.group(1).split(";"))
    cfg = _lee(CONFIG)
    pedidos = set(re.findall(r"'(\d00)'", cfg[cfg.index("fontWeight: {"):][:400]))
    faltan = pedidos - cargados
    assert not faltan, (
        f"el config pide los pesos {sorted(faltan)} y el @import de Inter no los "
        "descarga: el navegador los falsifica engordando el más cercano")


def test_los_colores_APAGAN_de_verdad():
    """Que el fichero exista no prueba que el color sea más suave.

    Se comparan tres de los que más se usan contra el Tailwind de fábrica: si
    alguien regenerase con los factores a 1.0, todo seguiría «pasando» y la
    pantalla gritaría igual.
    """
    sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
    from paleta_erp import hex_a_oklch          # noqa: E402

    cuerpo = _lee(PALETA)
    originales = {"indigo": ("600", "#4f46e5"), "amber": ("500", "#f59e0b"),
                  "emerald": ("600", "#059669")}
    for fam, (tono, viejo) in originales.items():
        m = re.search(rf"^  {fam}: \{{(.+)\}},$", cuerpo, re.M)
        assert m, f"falta la familia {fam} en la paleta"
        n = re.search(rf"'{tono}': '(#[0-9a-f]{{6}})'", m.group(1))
        assert n, f"falta {fam}-{tono}"
        nuevo = n.group(1)
        _, c_viejo, _ = hex_a_oklch(viejo)
        l_n, c_nuevo, _ = hex_a_oklch(nuevo)
        assert c_nuevo < c_viejo * 0.75, (
            f"{fam}-{tono} apenas se ha apagado ({c_nuevo:.3f} contra "
            f"{c_viejo:.3f} del original)")
        l_v, _, _ = hex_a_oklch(viejo)
        assert abs(l_n - l_v) < 0.06, (
            f"{fam}-{tono} ha cambiado de LUMINOSIDAD ({l_v:.3f} -> {l_n:.3f}). "
            "Eso mueve los contrastes de las 92 pantallas, que es justo lo que "
            "este cambio no puede hacer.")


def test_no_quedan_HEX_CHILLONES_sueltos_en_los_componentes():
    """La paleta de Tailwind no alcanza a los colores escritos a pelo.

    Había 436 hexadecimales distintos en `style={{...}}`, degradados e iconos.
    Apagar solo las clases habría dejado la mitad de la pantalla gritando al
    lado de la otra mitad — peor que antes, porque antes gritaban todos a la vez.
    """
    comp = os.path.join(FRONT, "src", "components")
    sonados = ("#10b981", "#059669", "#4f46e5", "#f59e0b", "#f97316",
               "#d946ef", "#2563eb", "#22c55e", "#e11d48")
    encontrados = []
    for base, _, nombres in os.walk(comp):
        if os.path.join("components", "ui") in base:
            continue                            # shadcn: código de terceros
        for n in nombres:
            if not n.endswith((".jsx", ".js")):
                continue
            cuerpo = _lee(os.path.join(base, n))
            for h in sonados:
                if h in cuerpo.lower():
                    encontrados.append(f"{n}:{h}")
    assert not encontrados, (
        "han vuelto colores de Tailwind sin apagar escritos a mano: "
        + ", ".join(encontrados[:8])
        + ". Se arregla con `python3 herramientas/apagar_hex_sueltos.py --escribir`")
