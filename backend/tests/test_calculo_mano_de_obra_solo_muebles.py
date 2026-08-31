# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA MANO DE OBRA ES SOLO DE LOS MUEBLES.

El master, 31/08: «la mano de obra sólo tiene que ser de los muebles».

QUÉ PASABA. `despiece` cobraba `p.mano` —17 €— en CADA línea. Una puerta suelta,
un costado, una regleta o un techo llevaban la mano de obra entera de un mueble.
Y eso no es «sale caro»: ese 17 € es LO MISMO que cobra el montador (CLAUDE.md,
regla 16, «su comisión ES la mano de obra por mueble que ya se teclea en
Rentabilidad MV — no tiene fórmula propia a propósito, porque dos números para
lo mismo acaban sin cuadrar»), y el backend paga SOLO los muebles desde el
25/08. O sea que la pantalla calculaba el margen con una nómina y la nómina
pagaba otra, sin que ninguna de las dos pareciera un error.

Y HABÍA UN SEGUNDO SITIO, PEOR. El bloque «Comisiones de cooperativistas» de
Rentabilidad MV contaba las unidades con `lineas.reduce((a, l) => a + l.cant, 0)`
—TODAS— y rotulaba «× N muebles». Además el tramo del comercial salía de
`calc.tot.pvp`, el PVP de TODO, así que el importe de las puertas y los costados
EMPUJABA EL TRAMO de los muebles de verdad. Es exactamente lo que la regla 16
dice que no puede pasar: «cuenta unidades que no existen Y su importe empuja el
TRAMO de todos los demás muebles. En un pedido corriente eran 990 € contra
420 € — un 136 % de más». El backend se arregló el 25/08; esta pantalla se quedó
prometiendo a la cara lo que la nómina no iba a pagar.

LO QUE SE PROTEGE
-----------------
1. LAS DOS LISTAS DICEN LO MISMO. El backend deduce las familias que no son
   mueble de dos sitios (`nomenclaturas_pdf` y el tipo `matrix` de la tarifa); el
   frontend no puede leer ninguno, así que las escribe. Esta prueba las compara
   NOMBRE A NOMBRE: si allí entra una familia nueva y aquí no, esto se pone rojo.

2. UN VITRINA QUE SÍ ES MUEBLE. `ALTO_VITRINA` y `MEDIACOLUMNA_VITRINA` son un
   casco con puerta de cristal y se montan igual. El corte va por nombres
   exactos, nunca por la palabra «vitrina».

3. SIN FAMILIA NO SE PAGA. Una línea tecleada a mano para un servicio no tiene
   familia del catálogo. Conservador a propósito: pagar de menos se reclama,
   pagar de más no se devuelve.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _rent():
    return sin_comentarios(_lee(RENT))


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def _lista_de_pantalla():
    bloque = _bloque(_rent(), "export const FAMILIAS_SIN_MANO_DE_OBRA = new Set([", "]);")
    return set(re.findall(r"'([A-Z0-9_]+)'", bloque))


def test_LAS_DOS_LISTAS_DE_LO_QUE_NO_ES_MUEBLE_DICEN_LO_MISMO():
    """La pantalla calcula el margen con la misma nómina que el backend paga."""
    from services.comisiones import FAMILIAS_SIN_COMISION

    pantalla = _lista_de_pantalla()
    backend = set(FAMILIAS_SIN_COMISION)
    assert pantalla == backend, (
        "la pantalla y la nómina no se ponen de acuerdo en qué es un mueble.\n"
        f"  solo en la pantalla: {sorted(pantalla - backend)}\n"
        f"  solo en el backend:  {sorted(backend - pantalla)}\n"
        "Si el backend deja de pagar una familia y la pantalla la sigue costeando "
        "(o al revés), el margen que se ve y el dinero que se paga se separan sin "
        "que ninguno de los dos parezca un error.")


def _es_mueble_en_pantalla(familias):
    """EJECUTA `esMuebleMV` en node, la función de verdad.

    Leer la lista no basta y costó una mutación: cambiar la FUNCIÓN a
    `... && !f.includes('VITRINA')` deja la lista intacta y tumba los cuatro
    muebles de cristal, con la prueba en verde. Un candado que lee una constante
    no protege el código que la usa.
    """
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar la función de verdad")
    cuerpo = _rent()
    lista = _bloque(cuerpo, "export const FAMILIAS_SIN_MANO_DE_OBRA = new Set([", "]);")
    fn = _bloque(cuerpo, "export const esMuebleMV", "\n};")
    js = "%s\n%s\nconsole.log(JSON.stringify(%s.map(esMuebleMV)));" % (
        lista.replace("export const", "const"),
        fn.replace("export const", "const"),
        json.dumps(list(familias)))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"esMuebleMV no se ejecuta: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_UNA_VITRINA_CON_CASCO_SIGUE_SIENDO_UN_MUEBLE():
    """El corte va por nombres exactos, no por la palabra «vitrina»: un
    ALTO_VITRINA es un casco con puerta de cristal y se monta igual."""
    from services.comisiones import es_mueble

    muebles = ("ALTO_VITRINA", "ALTILLO_VITRINA", "MEDIACOLUMNA_VITRINA",
               "MEDIACOL_VITRINA_GAVETA", "BAJO", "COLUMNA_HORNO")
    for fam, en_pantalla in zip(muebles, _es_mueble_en_pantalla(muebles)):
        assert en_pantalla, (
            f"{fam} es un mueble —lleva casco y se monta— y la pantalla no le "
            "cobra la mano de obra")
        assert es_mueble({"familia": fam}), f"el backend ha dejado de pagar {fam}"

    frentes = ("PUERTAS", "VITRINA", "COSTADOS_COLOR", "REGLETA_MELAMINA")
    for fam, en_pantalla in zip(frentes, _es_mueble_en_pantalla(frentes)):
        assert not en_pantalla, f"{fam} no se monta: no puede llevar mano de obra"
        assert not es_mueble({"familia": fam}), f"el backend paga {fam} como mueble"

    # Y sin familia, ni en una punta ni en la otra.
    assert _es_mueble_en_pantalla(["", None])[0] is False
    assert _es_mueble_en_pantalla(["", None])[1] is False


def test_SOLO_LOS_MUEBLES_LLEVAN_MANO_DE_OBRA_EN_EL_DESPIECE():
    """Una puerta suelta no se monta: no puede costar 17 € de montaje."""
    cuerpo = _rent()
    linea = _bloque(cuerpo, "const costeMo =", ";")
    assert "esMuebleMV(familia)" in linea, (
        f"la mano de obra se cobra en todas las líneas: {linea.strip()}")
    assert "? (Number(p.mano) || 0) : 0" in linea, (
        f"lo que no es mueble tiene que llevar CERO de montaje: {linea.strip()}")


def test_SIN_FAMILIA_NO_SE_PAGA_MONTAJE():
    """Una línea manual de servicio no tiene familia del catálogo. Conservador
    a propósito: pagar de menos se reclama, pagar de más no se devuelve."""
    cuerpo = _rent()
    fn = _bloque(cuerpo, "export const esMuebleMV", "\n};")
    assert "if (!f) return false;" in fn, (
        f"una línea sin familia se estaría pagando como mueble: {fn.strip()}")
    assert ".toUpperCase()" in fn, (
        "la familia no se normaliza: 'puertas' en minúsculas se colaría como mueble")


def test_LA_COMISION_CUENTA_MUEBLES_Y_NO_LINEAS():
    """El rótulo dice «× N muebles»: tiene que ser verdad."""
    cuerpo = _rent()
    bloque = _bloque(cuerpo, "const uds = ", ";")
    assert "calc.tot.udsMuebles" in bloque, (
        f"las comisiones cuentan todas las líneas como muebles: {bloque.strip()}")
    tot = _bloque(cuerpo, "const tot = rows.reduce(", "udsFuera: 0 });")
    assert "esMuebleMV(r.familia)" in tot, (
        "el total no distingue los muebles del resto")
    assert "udsMuebles: a.udsMuebles + (mueble ? r.cant : 0)" in tot, (
        "las unidades de mueble no se cuentan por línea")


def test_LOS_FRENTES_NO_EMPUJAN_EL_TRAMO_DEL_COMERCIAL():
    """Regla 16: su importe no puede subir de tramo a los muebles de verdad.
    Con el PVP de todo, un pedido con muchas puertas pagaría 60 €/mueble donde
    la nómina paga 40 €."""
    cuerpo = _rent()
    base = _bloque(cuerpo, "const baseImponible = Math.round(", ";")
    assert "calc.tot.pvpMuebles" in base, (
        f"el tramo sale del PVP de TODO, frentes incluidos: {base.strip()}")
    assert "calc.tot.pvp *" not in base, (
        "el tramo sigue saliendo del PVP total")
    tot = _bloque(cuerpo, "const tot = rows.reduce(", "udsFuera: 0 });")
    assert "pvpMuebles: a.pvpMuebles + (mueble ? r.pvp : 0)" in tot, (
        "el PVP de los muebles no se separa del total")


def test_SE_VE_LO_QUE_SE_HA_QUEDADO_FUERA():
    """Quien ve «14 muebles» en un pedido de 20 líneas tiene que entender por qué,
    o pensará que le están quitando."""
    cuerpo = _rent()
    assert 'data-testid="mv-uds-fuera"' in cuerpo, (
        "no se dice cuántas unidades se han quedado fuera de la comisión")
    aviso = _bloque(cuerpo, "{udsFuera > 0 && (", ")}")
    assert "frentes y lineales" in aviso, "el aviso no dice qué se ha dejado fuera"


def test_EL_PRESUPUESTADOR_DICE_CUANTOS_MUEBLES_PAGAN_MONTAJE():
    """El importe tiene que poder compararse con la liquidación del montador sin
    hacer ninguna cuenta."""
    cuerpo = sin_comentarios(_lee(CM3))
    conteo = _bloque(cuerpo, "const udsMuebles = filas.reduce(", ", 0);")
    assert "!esMuebleMV(m.familia)" in conteo, (
        f"el Presupuestador cuenta como mueble todo lo que tiene coste: {conteo.strip()}")
    assert "m.coste == null" in conteo, (
        "cuenta también las líneas sin coste, que no suman al importe de al lado")
    assert "(Number(m.qty) || 1)" in conteo, (
        "el conteo de muebles no multiplica por las unidades")
    assert "Montaje de ${udsMuebles} mueble" in cuerpo, (
        "el reparto del coste no dice cuántos muebles paga el montaje")
