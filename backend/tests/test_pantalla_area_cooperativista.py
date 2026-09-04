# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA PANTALLA DEL COOPERATIVISTA: LO QUE ENSEÑA Y LO QUE NO MEZCLA.

El master, 25/08/2026, sobre el plan de estimulación continua: «que cuando
accedan a su área puedan estar viendo lo que tienen que producir y los
beneficios que van a tener cuando lo produzcan».

LA DECISIÓN DE DISEÑO QUE HAY QUE VIGILAR: LOS TRES MONTONES NO SE SUMAN.
«En progreso», «a cobrar» y «ya cobrado» son promesas de distinto valor — lo que
está en progreso todavía se puede caer con el pedido. Un total único sería
enseñarle como suyo un dinero que aún no lo es, y el día que se anule un pedido
la cifra bajaría sola sin que nadie entienda por qué.

Es la misma regla que ya está en `liquidaciones.py`; aquí se comprueba que la
pantalla tampoco la rompe, porque una suma en el JSX es un renglón y nadie la
notaría.
"""
import os

import permisos_de_pestana as P
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "AreaCooperativista.jsx")


def _lee():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def test_los_TRES_MONTONES_NO_SE_SUMAN():
    """Se busca CUALQUIER expresión que junte dos montones con un `+`.

    La primera versión de esta prueba usaba una expresión literal
    (`enProgreso?.euros\s*\+`) y se le escapó la suma de verdad, porque entre
    medias había un `|| 0)`. Se comprobó rompiéndolo: se añadió un total a la
    pantalla y la prueba siguió en verde. Un candado que solo caza la forma
    exacta que se te ocurrió no es un candado, es una casualidad.

    Ahora se localizan las apariciones de los tres montones y se mira si dos
    DISTINTAS caen cerca con un `+` en medio, escriba lo que escriba entre ellas.
    """
    cuerpo = _lee()
    montones = ("enProgreso", "consolidada", "liquidada")
    posiciones = [(m.start(), n) for n in montones
                  for m in re.finditer(n, cuerpo)]
    posiciones.sort()
    for (pa, na), (pb, nb) in zip(posiciones, posiciones[1:]):
        if na == nb or pb - pa > 140:
            continue
        if "+" in cuerpo[pa:pb]:
            trozo = cuerpo[pa:pb].replace("\n", " ")
            assert False, (
                f"la pantalla suma «{na}» con «{nb}»: {trozo[:110]}. «En "
                "progreso» no es dinero suyo todavía: si se cae el pedido, se "
                "cae con él.")
    assert "no se suman" in cuerpo, (
        "ha desaparecido la explicación de por qué van separados; sin ella, el "
        "primero que la vea sumará los tres «para que quede más claro»")


def test_estan_LOS_TRES_y_con_su_explicacion():
    cuerpo = _lee()
    for titulo, pista in (("En progreso", "aún no cobrados"),
                          ("A cobrar", "servidos y cobrados"),
                          ("Ya cobrado", "liquidado")):
        assert titulo in cuerpo, f"falta el montón «{titulo}»"
        assert pista in cuerpo, (
            f"«{titulo}» ya no explica qué significa; los tres se parecen "
            "demasiado como para dejarlos sin pie")


def test_el_GANCHO_dice_cuanto_falta_Y_CUANTO_SE_GANA():
    """Lo que convierte un dato en un motivo. «10 € más por mueble» no mueve a
    nadie; «140 € más para ti», sí."""
    cuerpo = _lee()
    assert "Lo que tienes a tiro" in cuerpo
    assert "faltan" in cuerpo and "por\n                  mueble" in cuerpo.replace("\r", "")
    assert "más para ti" in cuerpo, (
        "el gancho ya no dice lo que se lleva el cooperativista si lo consigue")


def test_al_MONTADOR_no_se_le_enseña_un_tramo_que_no_le_aplica():
    """Su comisión es la mano de obra por mueble (CLAUDE.md, regla 16): no
    depende de la valoración, así que no hay tramo que perseguir. Enseñárselo
    sería prometerle algo que no va a pasar."""
    cuerpo = _lee()
    assert "!esMontador && aTiro.length > 0" in cuerpo, (
        "el gancho de tramos se le está enseñando también al montador")


def test_los_IMPORTES_no_llevan_color_de_estado():
    """docs/DISENO.md: un importe no es ni bueno ni malo. Pintarlo de verde o de
    ámbar lo convierte en un juicio permanente."""
    cuerpo = _lee()
    i = cuerpo.index("text-3xl font-black")
    trozo = cuerpo[i:i + 120]
    assert "text-dato-900" in trozo, (
        "la cifra grande ha dejado de ir en `dato`: el dinero destaca por "
        "tamaño y peso, no por color de estado")


def test_un_area_VACIA_se_explica_y_no_se_queda_en_blanco():
    cuerpo = _lee()
    assert "Todavía no tienes pedidos asignados" in cuerpo, (
        "sin pedidos la pantalla se queda muda: quien entre creerá que está rota")


def test_un_FALLO_AL_CARGAR_se_dice():
    """Un área en blanco sin explicación se lee como «no he ganado nada», que es
    muy distinto de «no se ha podido cargar»."""
    cuerpo = _lee()
    assert "No se pudo conectar" in cuerpo and "setError" in cuerpo


def test_las_ANOMALIAS_se_cuentan_y_se_explican():
    """`liquidaciones.es_anomalia` marca la mercancía que salió sin cobrar. Que
    el motor lo marque no sirve de nada si la pantalla no lo enseña."""
    cuerpo = _lee()
    assert "anomalia" in cuerpo and "sin estar cobrados" in cuerpo, (
        "la pantalla no enseña los pedidos marcados como anomalía")


# ── EL ENLACE DEL MENÚ ────────────────────────────────────────────────────────
#
# El master lo pidió por su nombre el 25/08: «el enlace en el menú tienes que
# crear en la red de distribución varias cosas que vamos a diferenciar». Una
# pantalla sin puerta no existe: `AreaCooperativista.jsx` estuvo escrita, con
# sus rutas y sus candados, y sin un solo sitio desde el que abrirla.
#
# Estas tres pruebas vigilan las tres mitades del enlace: que esté en la barra,
# que esté en la pantalla de bienvenida, y que las dos decidan quién lo ve con
# la MISMA regla que el servidor —nunca con una copia escrita a mano—.

APP = os.path.join(RAIZ, "frontend", "src", "App.js")
BIENVENIDA = os.path.join(RAIZ, "frontend", "src", "components", "WelcomeScreen.jsx")


def _lee_ruta(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_el_AREA_SE_ABRE_DESDE_COOP():
    """SE MUDÓ, PERO SIGUE TENIENDO PUERTA (master, 30/08: «Mi área debería
    estar dentro de COOP»; «que cuelguen dentro del área de COOP, no fuera»).

    Este candado nació porque `AreaCooperativista.jsx` estuvo escrita, con sus
    rutas y sus pruebas, y sin UN SOLO SITIO desde el que abrirla. Eso es lo que
    sigue vigilando; lo que ha cambiado es dónde está la puerta: antes un botón
    en la barra, ahora la primera pestaña de COOP.
    """
    panel = _lee_ruta(os.path.join(RAIZ, "frontend", "src", "components",
                                   "CoopPanel.jsx"))
    assert "AreaCooperativista" in panel, (
        "la pantalla del cooperativista no se monta en COOP: está escrita y no "
        "hay forma de abrirla")
    assert "id: 'miarea'" in panel, "no hay pestaña de «Mi área» en COOP"

    cuerpo = _lee_ruta(APP)
    assert "'miArea'" in cuerpo, (
        "se ha perdido el camino viejo: los enlaces que ya existen llevarían a "
        "una pantalla en blanco (regla 22)")
    # SE EJECUTA LA REGLA, NO SE BUSCA SU TEXTO. Hasta el 04/09/2026 aquí se
    # miraba que `App.js` llevara escrito `esCooperativista(state.currentUser)`.
    # Ese día los permisos se centralizaron en `modulePermissions.js` y `App.js`
    # pasó a preguntar `canOpenTab(...)`: la puerta seguía abierta al socio,
    # exactamente igual, y el candado se puso rojo igualmente. Un candado que se
    # pone rojo por cómo está escrito el código, y no por que la promesa se haya
    # roto, enseña a la gente a ignorarlo.
    abre = P.puertas({"socio": P.SOCIO_MONTADOR}, ["coop", "miArea"])["socio"]
    assert "miArea" in abre, (
        "la puerta de «Mi área» no se abre al socio: acaba de perder lo único "
        "suyo que hay en el ERP")
    assert "coop" in abre, (
        "el socio no entra en COOP, que es donde vive «Mi área»: la pestaña "
        "existe y no hay forma de llegar a ella")


def test_el_AREA_YA_NO_ESTA_SUELTA_EN_LA_BIENVENIDA():
    """SE QUITÓ A PROPÓSITO (master, 31/08: «este área quítala, ya está en COOP»).

    Estuvo en la bienvenida mientras «Mi área» era una pantalla suelta. Desde
    que se mudó dentro de COOP —es su primera pestaña— tenerla también aquí son
    DOS PUERTAS A LA MISMA PANTALLA, y eso ya ha costado un disgusto en este
    ERP: «Planificación» se enseñaba con un permiso en el menú y con otro en la
    bienvenida, el master la desactivó y le siguió saliendo (CLAUDE.md, regla
    26). Dos sitios que deciden quién entra son uno que se aprieta y otro que se
    queda abierto.

    Esta prueba es la de antes DEL REVÉS, y eso es lo que hay que ver al leerla:
    lo que se protegía —que el socio pueda llegar a su área— lo protege ahora
    `test_el_AREA_SE_ABRE_DESDE_COOP`, que sigue vivo justo encima. Aquí solo se
    vigila que no vuelva a aparecer una segunda puerta.
    """
    cuerpo = _lee_ruta(BIENVENIDA)
    assert "tab: 'miArea'" not in cuerpo, (
        "«Mi área» ha vuelto a la pantalla de bienvenida: son dos puertas a la "
        "misma pantalla y el día que cambie quién entra se cambiará en una y no "
        "en la otra")


def test_EL_CAMINO_VIEJO_SIGUE_ABRIENDO_ALGO():
    """Quitar el botón NO puede dejar muerto el nombre `miArea`: hay enlaces y
    estado de navegador con él, y tiene que seguir abriendo la pestaña dentro de
    COOP (CLAUDE.md, regla 22: los caminos viejos siguen vivos)."""
    cuerpo = _lee_ruta(APP)
    assert "'miArea'" in cuerpo, (
        "se ha perdido el camino viejo: un enlace con `miArea` llevaría a una "
        "pantalla en blanco")


def test_QUIEN_ENTRA_A_COOP_lo_decide_la_regla_comun_y_no_una_copia_a_mano():
    """`App.js` pregunta a `plataformas.js`, que es lo que se compara con el
    servidor en `test_calculo_plataformas.py`.

    Si aquí se escribiera la condición a mano —`isMontador || isComercial`— el
    menú le enseñaría COOP a un suscriptor de carpinter.io, que al entrar se
    comería un 403; y el día que la regla cambie, cambiaría en un sitio y no en
    el otro. Es exactamente lo que ya pasó con el rótulo de los tramos de
    comisión: el importe bien y la explicación mintiendo.
    """
    modulo = _lee_ruta(os.path.join(RAIZ, "frontend", "src", "modulePermissions.js"))
    assert "esCooperativista" in modulo and "plataformas" in modulo, (
        "la matriz de permisos no le pregunta a `plataformas.js`: si escribiera "
        "la condición a mano, el menú y el servidor se separarían")

    # Y LA PRUEBA DE VERDAD: quién entra. Escrita a mano —`isMontador ||
    # isComercial`— el menú le enseñaría COOP a un suscriptor de carpinter.io,
    # que al entrar se comería un 403.
    abre = P.puertas({
        "socio": P.SOCIO_MONTADOR,
        "comercial_socio": P.SOCIO_COMERCIAL,
        "suscriptor": P.SUSCRIPTOR,
        "comercial_en_nomina": P.COMERCIAL_EN_NOMINA,
    }, ["coop", "miArea"])
    assert "miArea" in abre["socio"] and "miArea" in abre["comercial_socio"], (
        "un socio marcado no entra en su área")
    assert abre["suscriptor"] == [], (
        "un suscriptor de carpinter.io entra en COOP: se comerá un 403, y lo "
        "que es peor, puede acabar en una liquidación (regla 21)")
    assert abre["comercial_en_nomina"] == [], (
        "el comercial de toda la vida de la casa —`isRepresentative`— entra en "
        "el área de los cooperativistas. Ser comercial no basta: hay que ser "
        "comercial DE LA COOPERATIVA, y eso se MARCA, no se deduce del rol")
