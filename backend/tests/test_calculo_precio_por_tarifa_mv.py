# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
«B45D» SE BUSCA EN LA TARIFA COMO «B45D/I».

El master, 07/09/2026, con la T4 seleccionada en pantalla: «OJO, el bajo de 45
D, B45D/I, su valor del punto es de 54 puntos en tarifa 4 y aquí lo refleja
mal».

Y así era. La línea enseñaba **146,52 €**, que son **44 × 3,33** — los puntos
de la TARIFA 1 — con la TARIFA 4 elegida. Lo correcto son 54 × 3,33 = 179,82 €:
un **18,5 % por debajo**, en un presupuesto que se firma.

EL MOTIVO, Y POR QUÉ NO SALTABA NADA
────────────────────────────────────
En la tarifa MV un mueble de UNA puerta se escribe con el sufijo `D/I`
(«B45D/I»); la línea, una vez elegida la mano, lleva «B45D». Se buscaba «B45D»
y, al no estar, «B45» — que tampoco está. Sin entrada de tarifa, el código
devolvía el precio que la línea YA TRAÍA, o sea el de la tarifa anterior. Un
`return` silencioso: ni error, ni aviso, ni un hueco en blanco que hiciera
sospechar. La pantalla decía T4 y cobraba T1.

NO ES UN CASO RARO: 125 de los 366 códigos de la T4 llevan `D/I`, un tercio
del catálogo. Cualquier mueble de una puerta al que se le haya elegido la mano
—que son casi todos— se quedaba con el precio de la tarifa anterior.

QUÉ VIGILA ESTE CANDADO
───────────────────────
No se lee el código: se EJECUTA en node la función de verdad
(`entradaDeTarifa`, sacada del fichero) contra la TARIFA REAL del proyecto, y
se comprueba mueble a mueble que encuentra los puntos que están impresos. Una
prueba escrita contra un diccionario preparado a mano habría pasado igual de
verde que pasó el fallo.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")
TARIFAS = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")


def _fuente():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def _tarifas():
    with open(TARIFAS, "r", encoding="utf-8") as f:
        return json.load(f)


def _extrae(nombre):
    """La función TAL CUAL está en la pantalla, no una copia."""
    src = _fuente()
    i = src.index(f"  const {nombre} = ")
    # Se corta en el siguiente arranque de primer nivel, que puede ser otra
    # `const` o un `useEffect`: `entradaDeTarifa` está justo encima del efecto
    # que recarga la tarifa, y cortando solo por `const` se arrastraba el
    # efecto entero —con sus `useEffect` y sus `fetch`— a un node que no los
    # tiene.
    m = re.search(r"\n  (?:const \w+ = |useEffect\()", src[i + 10:])
    return src[i:i + 10 + m.start()] if m else src[i:]


def _en_node(js):
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar la función de verdad")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node falló:\n{r.stderr[-3000:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _busca(codigos_y_familias, tarifa="T4"):
    """Ejecuta `entradaDeTarifa` contra la tarifa REAL."""
    fams = _tarifas()["tariffs"][tarifa]
    fn = _extrae("entradaDeTarifa")
    js = (fn.replace("const entradaDeTarifa", "const entradaDeTarifa", 1)
          + f"\nconst FAMS = {json.dumps(fams)};\n"
          + f"const CASOS = {json.dumps(codigos_y_familias)};\n"
          + "console.log(JSON.stringify(CASOS.map(c => entradaDeTarifa(FAMS, c).e)));")
    return _en_node(js)


PV = 3.33          # el valor de punto del catálogo MV


def test_EL_CASO_DEL_MASTER_el_B45D_en_T4_vale_54_puntos():
    """146,52 € eran los 44 puntos de la T1. En T4 son 54 → 179,82 €."""
    (e,) = _busca([{"cod": "B45D", "familia": "BAJO"}], "T4")
    assert e == 54, f"«B45D» no encuentra su entrada en la T4 (devuelve {e})"
    assert round(e * PV, 2) == 179.82
    (t1,) = _busca([{"cod": "B45D", "familia": "BAJO"}], "T1")
    assert t1 == 44 and round(t1 * PV, 2) == 146.52, (
        "146,52 € tienen que seguir siendo los de la T1: si esto cambia, el "
        "número del que se quejó el master ya no significa lo mismo")


def test_la_mano_ESCRITA_no_esconde_el_mueble():
    """Da igual la mano elegida: es el mismo mueble y el mismo precio."""
    d, i, di = _busca([{"cod": "B45D", "familia": "BAJO"},
                       {"cod": "B45I", "familia": "BAJO"},
                       {"cod": "B45D/I", "familia": "BAJO"}], "T4")
    assert d == i == di == 54


def test_UN_TERCIO_del_catalogo_lleva_el_sufijo_D_BARRA_I():
    """Para que se vea que esto no era un caso raro."""
    fams = _tarifas()["tariffs"]["T4"]
    todos = [k for v in fams.values() for k in (v.get("items") or {})]
    con_di = [k for k in todos if k.endswith("D/I")]
    assert len(todos) > 300
    assert len(con_di) > 100, (
        f"solo {len(con_di)} de {len(todos)} códigos llevan D/I; si el catálogo "
        "ha cambiado de forma, revisa que la búsqueda siga teniendo sentido")


def test_TODOS_los_codigos_de_una_puerta_se_encuentran_con_su_mano():
    """La prueba de verdad: se recorre el catálogo ENTERO.

    Por cada código `X D/I` de la tarifa se busca «XD» y «XI», que es como
    quedan escritos en la línea después de elegir la mano, y tiene que salir
    exactamente el mismo precio que el impreso.
    """
    fams = _tarifas()["tariffs"]["T4"]
    casos, esperados = [], []
    for familia, v in fams.items():
        for cod, puntos in (v.get("items") or {}).items():
            if not cod.endswith("D/I"):
                continue
            base = cod[:-3]
            for mano in ("D", "I"):
                casos.append({"cod": f"{base}{mano}", "familia": familia})
                esperados.append(puntos)
    assert len(casos) > 200
    obtenidos = _busca(casos, "T4")
    fallos = [(c["cod"], esp, obt)
              for c, esp, obt in zip(casos, esperados, obtenidos) if esp != obt]
    assert not fallos, (
        f"{len(fallos)} códigos de una puerta no encuentran su precio; el "
        f"primero: {fallos[0]}. Cada uno de estos se quedaría con el precio de "
        f"la tarifa anterior al cambiar de tarifa, sin dar ningún error")


def test_los_de_DOS_puertas_siguen_encontrandose():
    """No puede arreglarse una mitad rompiendo la otra: los de dos puertas van
    SIN sufijo, y su código no lleva mano."""
    fams = _tarifas()["tariffs"]["T4"]
    casos, esperados = [], []
    for familia, v in fams.items():
        for cod, puntos in (v.get("items") or {}).items():
            if cod.endswith("D/I") or not re.search(r"\d$", cod):
                continue
            casos.append({"cod": cod, "familia": familia})
            esperados.append(puntos)
    assert len(casos) > 50
    obtenidos = _busca(casos, "T4")
    fallos = [(c["cod"], e, o) for c, e, o in zip(casos, esperados, obtenidos) if e != o]
    assert not fallos, f"{len(fallos)} códigos de dos puertas se han roto: {fallos[:3]}"


def test_un_proyecto_VIEJO_con_la_mano_pegada_a_un_dos_puertas_sigue_valiendo():
    """El tercer intento de la búsqueda, el del código SIN mano.

    Los de dos puertas van sin sufijo en la tarifa («B60»), pero en proyectos
    guardados hay líneas escritas «B60D» — de cuando la mano se pegaba a
    cualquier código. Sin este intento, esas líneas dejan de encontrar su
    precio y se quedan con el de la tarifa anterior: el mismo fallo del 07/09,
    solo que en los proyectos que ya están grabados.
    """
    fams = _tarifas()["tariffs"]["T4"]
    # SOLO los que NO tienen gemelo `D/I`. En el 60 clavado existen los dos
    # («B60»=72 y «B60D/I»=64) y ahí manda el de UNA hoja, que es lo que dice
    # CLAUDE.md: una línea «B60D» es un B60 de una puerta y vale 64, no 72.
    dos_puertas = [(fam, cod, pts)
                   for fam, v in fams.items()
                   for cod, pts in (v.get("items") or {}).items()
                   if not cod.endswith("D/I") and re.search(r"\d$", cod)
                   and isinstance(pts, (int, float))
                   and f"{cod}D/I" not in (v.get("items") or {})]
    assert dos_puertas, "no hay códigos sin gemelo D/I en la T4"
    fam, cod, pts = dos_puertas[0]
    (e,) = _busca([{"cod": f"{cod}D", "familia": fam}], "T4")
    assert e == pts, (
        f"«{cod}D» (una línea vieja de un {cod} de dos puertas) no encuentra "
        f"su precio: se quedaría con el de la tarifa anterior")


def test_un_codigo_que_NO_esta_devuelve_NADA_y_no_se_inventa_un_precio():
    """Sin entrada de tarifa no hay precio. Lo que NO puede es dar el de otro
    mueble parecido: en la relación MV eso es pedirle al proveedor otra cosa."""
    (e,) = _busca([{"cod": "XX999D", "familia": "BAJO"}], "T4")
    assert e is None


def test_LAS_VEINTIUNA_TARIFAS_ENTERAS_encuentran_su_precio():
    """«Revisa por si hay alguno más» (master, 07/09/2026).

    No se comprueban unos cuantos códigos: se recorren las 21 tarifas enteras,
    los 12.963 códigos, cada uno de una puerta con sus dos manos. Es la única
    forma de responder a esa pregunta con un número en vez de con una
    impresión.
    """
    tfs = _tarifas()["tariffs"]
    casos, esperados = [], []
    for tarifa, fams in tfs.items():
        for familia, v in fams.items():
            for cod, pts in (v.get("items") or {}).items():
                manos = ([cod[:-3] + "D", cod[:-3] + "I", cod]
                         if cod.endswith("D/I") else [cod])
                for c in manos:
                    casos.append((tarifa, {"cod": c, "familia": familia}))
                    esperados.append(pts)
    assert len(casos) > 12000, f"solo se están comprobando {len(casos)} códigos"
    fallos = []
    for tarifa in tfs:
        idx = [k for k, (t, _) in enumerate(casos) if t == tarifa]
        obtenidos = _busca([casos[k][1] for k in idx], tarifa)
        for k, obt in zip(idx, obtenidos):
            if obt != esperados[k]:
                fallos.append((tarifa, casos[k][1]["cod"], esperados[k], obt))
    assert not fallos, (
        f"{len(fallos)} códigos no devuelven el precio que está impreso; el "
        f"primero: {fallos[0]}")


def _busca_en(familias, casos):
    """Igual que `_busca`, pero contra un catálogo dado. Hace falta para poder
    probar la regla del código SIN precio ahora que el hueco de la T9 está
    tapado: la regla sigue valiendo, y una prueba que dependa de que exista un
    hueco concreto se apaga sola el día que se rellene."""
    fn = _extrae("entradaDeTarifa")
    js = (fn + f"\nconst FAMS = {json.dumps(familias)};\n"
          + f"const CASOS = {json.dumps(casos)};\n"
          + "console.log(JSON.stringify(CASOS.map(c => entradaDeTarifa(FAMS, c).e)));")
    return _en_node(js)


def test_un_codigo_SIN_PRECIO_no_coge_el_del_mueble_de_al_lado():
    """Lo que salió al barrer las 21 tarifas, y era silencioso.

    En la T9, `MEDIACOLUMNA_VITRINA` traía `MV60: null` y la búsqueda seguía
    hasta encontrar `MV60D/I`: un mueble de DOS puertas presupuestado al precio
    del de UNA. El master dio los valores buenos el 07/09 y ese hueco ya está
    tapado, pero LA REGLA sigue haciendo falta —hay 21 tarifas transcritas a
    mano—, así que se prueba con un catálogo de laboratorio.

    `null` significa «de este no se sabe el precio»: se enseña vacío para que
    alguien pregunte (regla 7). Distinto de un código que NO ESTÁ, que sí sigue
    buscando — es lo que salva a los proyectos viejos con la mano pegada a un
    código de dos puertas.
    """
    fams = {"X": {"type": "single", "items": {"ZZ60D/I": 111, "ZZ60": None}}}
    assert _busca_en(fams, [{"cod": "ZZ60", "familia": "X"}]) == [None], (
        "un código sin precio está cogiendo el del mueble de al lado")
    # Y el que sí lo tiene se sigue encontrando.
    assert _busca_en(fams, [{"cod": "ZZ60D", "familia": "X"}]) == [111]
    # Un código que NO ESTÁ sí sigue buscando: son cosas distintas.
    fams2 = {"X": {"type": "single", "items": {"ZZ60": 222}}}
    assert _busca_en(fams2, [{"cod": "ZZ60D", "familia": "X"}]) == [222]


def test_LOS_VALORES_QUE_DIO_EL_MASTER_para_la_T9():
    """El master, 07/09/2026: «MV60 EN T9 = a 230 y MV60D/I = a 188»."""
    t9 = _tarifas()["tariffs"]["T9"]["MEDIACOLUMNA_VITRINA"]["items"]
    assert t9["MV60"] == 230
    assert t9["MV60D/I"] == 188
    assert t9["MV60"] > t9["MV60D/I"], (
        "el de DOS puertas tiene que costar más que el de una")


def test_LO_QUE_QUEDA_DUDOSO_DE_LA_T9_ESTA_ESCRITO():
    """Los dos valores que dio el master son los que estaban una columna a la
    izquierda, así que la fila parece transcrita CORRIDA: MV50D/I sigue
    valiendo lo mismo que MV60D/I, que es raro para un 50 y un 60.

    Eso no se arregla por deducción —sería inventarse un precio de proveedor—
    pero tampoco se deja sin decir: queda anotado en el propio fichero de la
    tarifa, que es donde lo va a encontrar el siguiente que pase.
    """
    cambios = _tarifas()["_meta"]["cambios_del_master"]
    ultimo = [c for c in cambios if c.get("fecha") == "2026-09-07"]
    assert ultimo, "el cambio de la T9 no está registrado en la tarifa"
    assert "lo_que_queda_dudoso" in ultimo[0], (
        "no se ha dejado escrito qué queda por comprobar de esa fila")


def test_HAY_UN_SOLO_BUSCADOR_para_el_precio_y_para_el_cambio_de_tarifa():
    """Aquí estaba el fallo: el cambio de tarifa llevaba su propia búsqueda,
    escrita a mano y distinta. Con dos, vuelven a separarse a la primera."""
    src = _fuente()
    assert src.count("const entradaDeTarifa = ") == 1
    # El re-tarifado y el cálculo del precio, los dos por la misma puerta.
    assert src.count("entradaDeTarifa(") >= 2, (
        "el buscador único ya no lo usan las dos rutas")
    assert "info?.items?.[m.cod] || info?.items?.[baseCod]" not in src, (
        "ha vuelto la búsqueda escrita a mano del cambio de tarifa, que es la "
        "que no encontraba «B45D/I»")
