# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA TARIFA MV, BARRIDA ENTERA: QUE NO FALTE NADA Y QUE NADA VAYA AL REVÉS.

El master, 07/09/2026: «pero revisa la tarifa para que no falte nada».

Son 21 tarifas transcritas A MANO desde un catálogo escaneado, 12.963 códigos.
Una casilla mal leída no da ningún error: da un presupuesto plausible y
equivocado, y se firma. Este candado hace tres preguntas al fichero entero.

1. ¿FALTA UNA CASILLA QUE EN LAS DEMÁS TARIFAS SÍ ESTÁ?
   Es lo que destapó el `MV60` de la T9: vacío en una tarifa y con precio en
   las otras veinte. Y era peligroso porque la búsqueda se caía al `MV60D/I`,
   o sea al mueble de UNA puerta.

2. ¿HAY UN MUEBLE MÁS ANCHO QUE CUESTA MENOS QUE EL MISMO MÁS ESTRECHO?
   Salen CUATRO en 12.963 códigos, y las cuatro están escritas en el propio
   fichero con la evidencia de las tarifas vecinas. No se corrigen: un precio
   de proveedor no se deduce (regla 7). Lo que hace esta prueba es que no
   aparezca una QUINTA sin que nadie se entere.

   OJO CON LA COMPARACIÓN, que tiene dos trampas y por las dos se pasa de 4 a
   cientos de falsos avisos:
     · Al MISMO ancho conviven el de dos puertas y el de una («B60» y
       «B60D/I»), y el de dos cuesta más. Eso es correcto (CLAUDE.md).
     · Al mismo ancho conviven muebles DISTINTOS de la misma familia
       («CHC60» columna de horno completa contra «CHPC60»). También correcto.
   Por eso se compara solo el MISMO prefijo, con la MISMA forma de puerta, a
   anchos ESTRICTAMENTE distintos.

3. ¿SIGUE SIENDO VERDAD QUE NINGÚN CÓDIGO TRAE LA MANO DECIDIDA?
   De ella depende que `mv_relacion` pueda dar por «sin decidir» todo lo que
   llega por el camino del código exacto.
"""
import collections
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARIFAS = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")


def _tarifa():
    with open(TARIFAS, "r", encoding="utf-8") as f:
        return json.load(f)


def _ranuras(v):
    """(columna, valor) de una entrada, sea `single`, `dual`, `h7090`…"""
    if isinstance(v, (int, float)) or v is None:
        return [("", v)]
    if isinstance(v, list):
        return [(str(i), x) for i, x in enumerate(v)]
    if isinstance(v, dict):
        return [(k, x) for k, x in v.items() if k != "desc"]
    return []


def _numero(v):
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, list):
        xs = [x for x in v if isinstance(x, (int, float))]
        return xs[0] if xs else None
    if isinstance(v, dict):
        xs = [x for x in v.values() if isinstance(x, (int, float))]
        return xs[0] if xs else None
    return None


_CODIGO = re.compile(r"^([A-Za-z]+)(\d{2,3})(D/I)?$")


# ─── 1. CASILLAS QUE FALTAN ──────────────────────────────────────────────────

def test_NO_falta_una_casilla_que_las_demas_tarifas_SI_tienen():
    """Un hueco de transcripción, no una columna que no aplique.

    Se distinguen por comparación entre tarifas: si la misma casilla tiene
    precio en ocho o más y está vacía en tres o menos, es que se saltó al
    copiarla. Con esa regla, el `MV60` de la T9 saltaba solo.
    """
    tfs = _tarifa()["tariffs"]
    con, sin = collections.defaultdict(set), collections.defaultdict(set)
    for tarifa, familias in tfs.items():
        for familia, fam in familias.items():
            for cod, v in (fam.get("items") or {}).items():
                for col, x in _ranuras(v):
                    destino = con if isinstance(x, (int, float)) else sin
                    destino[(familia, cod, col)].add(tarifa)
            for alto, fila in (fam.get("rows") or {}).items():
                for ancho, x in (fila or {}).items():
                    destino = con if isinstance(x, (int, float)) else sin
                    destino[(familia, f"fila{alto}", ancho)].add(tarifa)

    huecos = sorted(
        (sorted(vacias), clave)
        for clave, vacias in sin.items()
        if len(con.get(clave, ())) >= 8 and len(vacias) <= 3)

    # El único que queda, y está escrito: `COST` (costadillo de campana) sin la
    # columna «media» en la T16. Es una pieza suelta de un solo uso, no un
    # mueble: no lo tarifa el presupuestador por ancho.
    conocidos = {("ELEMENTOS_LINEALES", "COST", "med")}
    nuevos = [(t, c) for t, c in huecos if c not in conocidos]
    assert not nuevos, (
        f"{len(nuevos)} casillas están vacías en unas tarifas y con precio en "
        f"otras — eso es una transcripción a medias, y la búsqueda de precio "
        f"puede acabar cogiendo la del mueble de al lado: {nuevos[:5]}")


# ─── 2. PRECIOS QUE VAN AL REVÉS ─────────────────────────────────────────────

def _inversiones():
    """Mismo mueble, misma forma de puerta, más ancho y más barato."""
    fuera = []
    for tarifa, familias in _tarifa()["tariffs"].items():
        for familia, fam in familias.items():
            grupos = collections.defaultdict(list)
            for cod, v in (fam.get("items") or {}).items():
                m = _CODIGO.match(cod)
                precio = _numero(v)
                if not m or precio is None:
                    continue
                grupos[(m.group(1).upper(), bool(m.group(3)))].append(
                    (int(m.group(2)), cod, precio))
            for xs in grupos.values():
                xs.sort()
                for i in range(1, len(xs)):
                    # ESTRICTAMENTE más ancho: al mismo ancho conviven el de
                    # una puerta y el de dos, y ahí el de dos cuesta más.
                    if xs[i][0] > xs[i - 1][0] and xs[i][2] < xs[i - 1][2]:
                        fuera.append((tarifa, familia, xs[i - 1][1], xs[i - 1][2],
                                      xs[i][1], xs[i][2]))
    return fuera


# Las CUATRO conocidas, con su evidencia escrita en el propio fichero de la
# tarifa (`_meta.anomalias_pendientes_de_hoja`). No se corrigen aquí: un precio
# de proveedor no se deduce.
CONOCIDAS = {
    ("T1", "TECHO_COLOR", "TEC260", "TEC280"),
    ("T2", "ALTILLO", "L35", "L40"),
    ("T4", "ALTILLO", "L50", "L60"),
    ("T17", "ALTO_RINCON_CIEGO", "AR60D/I", "AR65D/I"),
}


def test_NO_hay_mas_precios_al_reves_que_los_CUATRO_conocidos():
    fuera = _inversiones()
    vistas = {(t, f, a, b) for t, f, a, _, b, _ in fuera}
    nuevas = vistas - CONOCIDAS
    assert not nuevas, (
        f"han aparecido {len(nuevas)} casillas nuevas en las que un mueble más "
        f"ancho cuesta MENOS que el mismo más estrecho: {sorted(nuevas)}. "
        "O se ha tocado la tarifa, o hay una casilla mal leída")
    # Y las cuatro siguen ahí: si alguien las corrige, que sea a propósito y
    # quitándolas de esta lista y de la nota de la tarifa.
    faltan = CONOCIDAS - vistas
    assert not faltan, (
        f"estas anomalías ya no están: {sorted(faltan)}. Si se han corregido "
        "contra la hoja, quítalas de CONOCIDAS y de "
        "`_meta.anomalias_pendientes_de_hoja`")


def test_las_CUATRO_estan_ESCRITAS_en_la_propia_tarifa():
    """Una anomalía que solo vive en una prueba no la ve quien abre el fichero
    de la tarifa buscando por qué un precio le cuadra raro."""
    notas = _tarifa()["_meta"].get("anomalias_pendientes_de_hoja")
    assert notas, "no está la nota de anomalías pendientes en la tarifa"
    for clave in ("T1_TECHO_COLOR_TEC260", "T2_ALTILLO_L35",
                  "T4_ALTILLO_L50_L60", "T17_ALTO_RINCON_CIEGO"):
        assert clave in notas, f"falta la anomalía «{clave}» en la nota"


# ─── 3. LA PREMISA DE LA MANO ────────────────────────────────────────────────

def test_ningun_codigo_de_la_tarifa_trae_la_mano_ya_decidida():
    """De esto depende que `mv_relacion` pueda dar por «sin decidir» todo lo
    que le llega por el camino del código exacto."""
    tfs = _tarifa()["tariffs"]
    raros = sorted({cod for familias in tfs.values() for fam in familias.values()
                    for cod in (fam.get("items") or {})
                    if not cod.upper().endswith("D/I")
                    and cod.upper().endswith(("D", "I"))})
    assert not raros, f"códigos con la mano ya decidida: {raros[:5]}"


def test_el_barrido_mira_LA_TARIFA_ENTERA():
    """Si un día se recorta el fichero, esta prueba diría que todo está bien
    sobre la mitad del catálogo."""
    tfs = _tarifa()["tariffs"]
    assert len(tfs) == 21, f"faltan tarifas: hay {len(tfs)}"
    total = sum(len(fam.get("items") or {})
                for familias in tfs.values() for fam in familias.values())
    assert total > 7000, f"el catálogo se ha quedado en {total} códigos"
