# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""IA PREMIUM — ChatGPT (OpenAI) en el CLON del Estudio 3D (09/09/2026).

El master: «podemos meter chatgpt con un botón de IA PREMIUM... quiero clonar
estudio 3D y en ese clon tenemos la IA de chatGPT para probarla».

LO QUE ESTE CANDADO PROTEGE, EN ORDEN DE LO QUE CUESTA SI SE ROMPE:

1. **QUE EL MOTOR PREMIUM NO APAREZCA COMO MOTOR DE DISEÑO EN PRODUCCIÓN.**
   Desde el 10/09 el Estudio 3D normal sí ofrece una pasada final de acabado
   PREMIUM sobre un render aprobado, con permiso y coste visibles. No abre el
   selector experimental ni permite generar el diseño inicial con ese motor.

2. **QUE EL CROQUIS LLEGUE A ASTRA.** Premium usa Responses API: Astra recibe
   el texto y todas las referencias y gobierna la herramienta de imagen.

3. **QUE SE COBRE LO QUE CUESTA.** Un motor sin entrada en `COSTE_POR_MOTOR`
   cobra 1 crédito por omisión, y sin precio en `MODEL_PRICES` cuenta 0,00 € en
   el informe de Consumo: el motor más caro sería el que menos parece gastar
   (reglas 15 y 32).

4. **QUE SIN LLAVE SE DIGA, NO SE DISIMULE.** Sin `OPENAI_API_KEY` este motor
   NO puede caer al de siempre: eso devolvería una imagen de otro motor con la
   etiqueta de este, que es exactamente el fallo del 03/08.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESPACHO = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")
USO = os.path.join(RAIZ, "backend", "services", "ai_usage.py")
PRODUCCION = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
CLON = os.path.join(RAIZ, "frontend", "src", "components", "Estudio3DLab.jsx")
PERMISOS = os.path.join(RAIZ, "frontend", "src", "modulePermissions.js")
PANEL = os.path.join(RAIZ, "frontend", "src", "components", "SettingsModal.jsx")
RUTA_IA = os.path.join(RAIZ, "backend", "routes", "ai_engine.py")
APP = os.path.join(RAIZ, "frontend", "src", "App.js")

MOTOR = "chatgpt"
MODELO_DIRECTOR = "gpt-6-astra"
MODELO = "gpt-image-2.5-sunburst"
PERMISO = "canUseIAPremium"


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _botonera(ruta):
    """El bloque de botones de motor, recortado.

    Se recorta a propósito: «premium» y «PREMIUM» aparecen también en el
    prefijo de prompt de IA 3 y en comentarios, y un candado que mirase el
    fichero entero se pondría rojo por texto que no es un botón."""
    fuente = _leer(ruta)
    inicio = fuente.index("{isMaster && (", fuente.index("Acción principal"))
    fin = fuente.index("</div>\n                )}", inicio)
    return fuente[inicio:fin]


# ─── 1. Que no se cuele en producción ───────────────────────────────────────

def test_el_boton_premium_NO_esta_en_el_estudio_3d_de_produccion():
    """CANDADO DURO. Es el que de verdad importa."""
    botonera = _botonera(PRODUCCION)
    for marca in ("'premium'", "IA PREMIUM"):
        assert marca not in botonera, (
            f"el botón premium ha aparecido en el Estudio 3D de PRODUCCIÓN. "
            f"Ese está congelado desde el 04/09 y es el único que ve un usuario "
            f"que no sea master: cada render pasaría a costar unas 7 veces más.")


def test_produccion_no_sabe_ni_traducir_el_motor_premium():
    """No basta con quitar el botón: si `providerOf()` supiera traducirlo,
    un 'premium' guardado en una pestaña vieja renderizaría con él."""
    assert f"return '{MOTOR}'" not in _leer(PRODUCCION), (
        "el Estudio 3D de producción puede volver a pedir el motor premium")


def test_produccion_ofrece_el_acabado_premium_SOLO_CON_PERMISO():
    """El botón se abre con la misma casilla que el motor (regla 33).

    EL RÓTULO YA NO DICE LOS CRÉDITOS (master, 10/09/2026: «que no ponga lo de
    los siete créditos»). Es una decisión suya y no contradice la regla 15 —
    esa prohíbe decir QUÉ IA se usa, no obliga a poner el precio.

    LO QUE NO SE PUEDE PERDER es el COBRO, que es otra cosa: sigue viviendo en
    `cobrar_render` en el servidor (regla 32). Quitar un aviso es cosmético;
    quitar el cobro sería renderizar gratis con el motor más caro del ERP. Por
    eso aquí abajo se sigue exigiendo que el coste se CALCULE, aunque no se
    enseñe: de él depende que el botón se deshabilite sin saldo."""
    produccion = _leer(PRODUCCION)
    assert "canUsePremiumFinish" in produccion
    assert "currentUser?.canUseIAPremium === true" in produccion
    assert ">Acabado PREMIUM<" in produccion, (
        "ha desaparecido el botón de acabado PREMIUM del Estudio 3D")
    assert "créditos</span>" not in produccion.split(">Acabado PREMIUM<")[0][-200:], (
        "ha vuelto la cifra de créditos al rótulo del botón (master, 10/09)")
    assert "creditosDeUnRender('chatgpt')" in produccion, (
        "ya no se calcula lo que cuesta: sin ese número el botón no puede "
        "deshabilitarse cuando no quedan créditos, que es la única defensa que "
        "queda desde que no hay ventana de confirmación")


def test_el_boton_premium_SE_DESHABILITA_SIN_SALDO():
    """CANDADO NUEVO, y hace falta justo desde hoy.

    Al quitar la ventana de confirmación se quedó sin la pregunta que frenaba
    una pulsación sin querer. Lo único que impide gastar 7 créditos de un toque
    es que el botón esté apagado cuando no llegan."""
    produccion = _leer(PRODUCCION)
    m = re.search(r"disabled=\{editing[^}]*premiumFinishCost > \(aiCredits\.restantes",
                  produccion)
    assert m, (
        "el botón de acabado PREMIUM ya no se apaga cuando no quedan créditos. "
        "Sin ventana de confirmación, era lo último que quedaba entre un toque "
        "y quedarse a cero.")


def test_acabado_premium_usa_el_render_actual_y_no_el_selector_de_motor():
    produccion = _leer(PRODUCCION)
    i = produccion.index("const mejorarAcabadoPremium")
    j = produccion.index("\n  };", i) + len("\n  };")
    cuerpo = produccion[i:j]
    assert "const img = currentImage()" in cuerpo
    assert "provider: 'chatgpt'" in cuerpo
    assert "referenceImage: dataUrl" in cuerpo
    assert "editingRender: true" in cuerpo
    assert "referenceIsSketch: false" in cuerpo
    assert "No rediseñes" in cuerpo
    # SIN VENTANA DE CONFIRMACIÓN (master, 10/09/2026: «que no salga la pantalla
    # de momento»). En una tablet ese `confirm` se come la pantalla entera y
    # corta el trabajo. Se comprueba que NO vuelva sola.
    assert "window.confirm" not in cuerpo, (
        "ha vuelto la ventana de confirmación al acabado PREMIUM; el master "
        "pidió quitarla el 10/09")


def test_los_cambios_posteriores_dejan_elegir_normal_o_premium():
    """El acabado se conserva, pero el motor de cada cambio lo elige el usuario."""
    produccion = _leer(PRODUCCION)
    assert "premiumFinish: true" in produccion
    assert "const premiumFinishActive = renderResult?.premiumFinish === true" in produccion
    assert "premiumEditMode" in produccion
    assert "provider: premiumChangeActive ? 'chatgpt' : providerOf()" in produccion
    assert "setPremiumEditMode(false)" in produccion
    assert "setPremiumEditMode(true)" in produccion


def test_editar_en_premium_SIN_PERMISO_se_sigue_cerrando():
    """Quitar el AVISO no puede quitar la PUERTA.

    Al retirar las dos ventanas de confirmación había que comprobar que no se
    llevaran por delante el cierre que hay al lado: sin la casilla, un render
    con acabado PREMIUM no se sigue editando en ese modo. Un aviso se quita
    porque molesta; un permiso no."""
    produccion = _leer(PRODUCCION)
    assert "premiumChangeActive && !canUsePremiumFinish" in produccion, (
        "ha desaparecido el cierre: cualquiera podría seguir editando en modo "
        "PREMIUM un render que lo tenga, gastando el motor más caro sin la "
        "casilla que lo autoriza")


def test_ya_NO_hay_ventanas_de_confirmacion_de_premium():
    """CANDADO DE LA DECISIÓN. Eran dos y las dos se quitaron el 10/09; que no
    vuelvan una por una sin que el master lo pida."""
    produccion = _leer(PRODUCCION)
    ventanas = produccion.count("window.confirm")
    premium = [l for l in produccion.splitlines()
               if "window.confirm" in l and "PREMIUM" in l]
    assert not premium, (
        f"han vuelto ventanas de confirmación de PREMIUM: {premium}")
    assert ventanas == 0 or "PREMIUM" not in produccion.split("window.confirm")[0][-300:], (
        "hay una confirmación nueva junto al acabado PREMIUM")


def test_el_clon_SI_lo_ofrece_y_lo_traduce():
    botonera = _botonera(CLON)
    assert "'premium'" in botonera and "IA PREMIUM" in botonera, (
        "el clon ha perdido el botón premium: entonces no sirve para lo que se "
        "hizo, que es probar ese motor")
    assert f"if (motor === 'premium') return '{MOTOR}';" in _leer(CLON), (
        "el clon ya no traduce 'premium': el botón caería al motor por defecto "
        "y pintaría con otro SIN dar ningún error")


def test_el_laboratorio_se_abre_por_SU_casilla_y_no_por_la_del_estudio_3d():
    """Las dos mitades: la pantalla Y el enrutado.

    Cerrar solo el botón del menú es un cierre de adorno — bastaría con llegar
    a la pestaña para que se pintara (regla 27, que se destapó con
    `landingStudio`)."""
    permisos = _leer(PERMISOS)
    m = re.search(r"if \(tab === 'estudio3dLab'\) \{(.*?)\}", permisos, re.S)
    assert m, "el laboratorio ya no tiene puerta propia en `canAccessTab`"
    puerta = m.group(1)
    assert "esMasterSistema(u)" in puerta, (
        "el master ha dejado de entrar en su propio banco de pruebas")
    assert PERMISO in puerta, (
        f"la puerta del laboratorio ya no mira «{PERMISO}»: la casilla de "
        f"permisos de usuario quedaría sin efecto")
    assert "canUseAIAnalysis" not in puerta, (
        "el laboratorio ha pasado a colgar del permiso del Estudio 3D de "
        "producción: quitarle uno le quitaría el otro (regla 26)")
    assert "canOpenTab('estudio3dLab')" in _leer(APP), (
        "el enrutado del laboratorio ya no comprueba el permiso: se pintaría "
        "con solo llegar a esa pestaña")


def test_la_casilla_EXISTE_y_no_muestra_la_cifra_de_creditos():
    """Un permiso que no se puede marcar no reparte nada (regla 8c), y uno que
    no dice lo que abre se marca sin saberlo (regla 26).

    El cobro interno permanece, pero el master pidió retirar su cifra visible."""
    panel = _leer(PANEL)
    assert f"'{PERMISO}'" in panel, (
        f"«{PERMISO}» no está en la lista de capacidades del panel Master: no "
        f"se guardaría al crear un usuario ni se limpiaría al pasar a Controller")
    assert f"userForm.{PERMISO}" in panel, (
        "la casilla de IA PREMIUM ha desaparecido del panel Master: el permiso "
        "existe en el servidor y no hay forma de dárselo a nadie")
    m = re.search(r"<span title=\"([^\"]*)\"[^>]*>([^<]*IA PREMIUM[^<]*)</span>", panel)
    assert m, "la casilla de IA PREMIUM ya no lleva rótulo visible"
    rotulo, ayuda = m.group(2), m.group(1)
    assert "Lab" in rotulo, (
        "el rótulo de la casilla ya no nombra la pantalla que abre: quien "
        "quiera quitarla no sabrá cuál buscar (regla 26)")
    assert "crédito" not in rotulo.lower()
    assert "crédito" not in ayuda.lower()


def test_LA_CASILLA_ABRE_EL_MOTOR_EN_EL_SERVIDOR_no_solo_el_boton():
    """CANDADO DURO. Es la mitad que se olvida siempre.

    Si el servidor no leyera la casilla, el usuario vería IA PREMIUM, la
    pulsaría, SE LE COBRARÍA, y recibiría un render del motor de siempre sin
    que nada diera error. Es el fallo del 03/08 y por lo que existe la regla
    11."""
    ruta = _leer(RUTA_IA)
    m = re.search(r"MOTORES_POR_PERMISO = \{(.*?)\}", ruta, re.S)
    assert m, (
        "`MOTORES_POR_PERMISO` ha desaparecido: el servidor vuelve a rebajar a "
        "TODO el que no sea master, y la casilla se queda de adorno")
    tabla = m.group(1)
    assert f'"{MOTOR}": "{PERMISO}"' in tabla, (
        f"el servidor ya no abre «{MOTOR}» con «{PERMISO}»")
    # Y SOLO ese. Los motores históricos son del master a secas (regla 1).
    for prohibido in ("julio11", "julio11_plus", "banana_pro", "flux"):
        assert prohibido not in tabla, (
            f"«{prohibido}» se reparte ahora por casilla. Los bancos de pruebas "
            f"del master no se abren «ya que estamos»: cuestan 3,3x por render "
            f"y esa decisión es suya (regla 1).")


def test_un_permiso_TORCIDO_no_abre_el_motor_caro():
    """`is True`, no un `if` a secas.

    Una ficha puede traer la clave con cualquier cosa dentro —un "false" de
    texto, un 1, un dict— y sobre un permiso que gasta dinero no se acepta un
    "algo que parece verdadero"."""
    ruta = _leer(RUTA_IA)
    i = ruta.index("MOTORES_POR_PERMISO.get(")
    bloque = ruta[i:i + 400]
    assert "is True" in bloque, (
        "el permiso de IA PREMIUM se comprueba por lo que «parece verdadero». "
        "Un 'false' de texto en la ficha abriría el motor de 7 créditos.")


# ─── 2. Que el croquis llegue al modelo ─────────────────────────────────────

def _cuerpo_del_motor():
    fuente = _leer(DESPACHO)
    i = fuente.index("async def _render_with_openai")
    j = fuente.index("\n    async def ", i + 10)
    return fuente[i:j]


def test_astra_dirige_el_render_y_recibe_las_imagenes():
    cuerpo = _cuerpo_del_motor()
    assert "client.responses.create" in cuerpo
    assert "model=_MODELO_OPENAI_DIRECTOR" in cuerpo
    assert 'reasoning={"effort": _ESFUERZO_OPENAI_DIRECTOR}' in cuerpo
    assert '"type": "input_image"' in cuerpo
    assert '"type": "image_generation"' in cuerpo
    assert '"model": _MODELO_OPENAI_IMAGEN' in cuerpo


def test_las_referencias_van_como_data_url_multimodal():
    cuerpo = _cuerpo_del_motor()
    assert "def _a_data_url" in cuerpo
    assert 'f"data:{mime};base64,{b64}"' in cuerpo
    assert '"detail": "high"' in cuerpo


def test_el_tope_de_siete_imagenes_se_respeta():
    """Regla 3 de CLAUDE.md."""
    cuerpo = _cuerpo_del_motor()
    assert "refs[:7]" in cuerpo, (
        "el motor premium ya no respeta el tope de 7 imágenes juntas (regla 3)")


# ─── 3. Que se cobre lo que cuesta ──────────────────────────────────────────

def test_el_motor_premium_cuesta_un_credito_como_pidio_el_master():
    uso = _leer(USO)
    assert f'"{MODELO}"' in uso, (
        f"«{MODELO}» no está en MODEL_PRICES: el informe de Consumo de IA lo "
        f"contaría a 0,00 € y el motor más caro sería el que menos parece gastar")
    m = re.search(r'"chatgpt":\s*([\d.]+)', uso)
    assert m, "el motor premium no está declarado en COSTE_POR_MOTOR"
    assert float(m.group(1)) == 1.0, (
        f"el motor premium cobra {m.group(1)} créditos y debe cobrar exactamente 1")


def test_el_modelo_esta_escrito_en_una_CONSTANTE_y_no_dentro_de_la_llamada():
    """Regla 10: un modelo cambiado no rompe nada, solo empeora el resultado.
    Escrito dentro de la llamada, cambia sin que nadie lo vea."""
    fuente = _leer(DESPACHO)
    assert f'_MODELO_OPENAI_IMAGEN = "{MODELO}"' in fuente, (
        f"el modelo del motor premium ya no es «{MODELO}» o ha dejado de estar "
        f"en una constante. Si el master lo ha cambiado, que quede escrito aquí.")
    cuerpo = _cuerpo_del_motor()
    assert f'"{MODELO}"' not in cuerpo, (
        "el nombre del modelo se ha vuelto a escribir dentro de la llamada: "
        "ahí cambia sin que la constante lo diga")
    assert f'_MODELO_OPENAI_DIRECTOR = "{MODELO_DIRECTOR}"' in fuente
    assert '_ESFUERZO_OPENAI_DIRECTOR = "medium"' in fuente


# ─── 4. Que sin llave se diga, no se disimule ───────────────────────────────

def test_sin_llave_NO_se_rinde_con_otro_motor():
    """Es el fallo del 03/08: el usuario pulsa un motor, recibe la imagen de
    otro y no se entera. Aquí se avisa y no se pinta."""
    cuerpo = _cuerpo_del_motor()
    m = re.search(r"if not openai_key:(.*?)\n\n", cuerpo, re.S)
    assert m, "ya no se comprueba que haya clave antes de llamar al proveedor"
    bloque = m.group(1)
    assert '"success": False' in bloque, (
        "sin clave el motor premium ya no falla: estaría cayendo a otro motor y "
        "devolviendo una imagen que no es la que se pidió")
    assert "logger.warning" in bloque, (
        "sin clave no queda ni una línea en el log: el master vería un error "
        "genérico y no tendría por dónde empezar")


def test_la_llave_es_la_MISMA_variable_que_ya_usa_el_ERP():
    """Dos nombres para la misma clave acaban con uno puesto y el otro no."""
    fuente = _leer(DESPACHO)
    i = fuente.index('if provider == "chatgpt"')
    assert 'os.environ.get("OPENAI_API_KEY"' in fuente[i:i + 900], (
        "el motor premium lee una variable de entorno distinta de "
        "OPENAI_API_KEY, que es la que el ERP ya usa para el dictado por voz")


def test_el_motor_premium_pasa_por_el_REPARTIDOR_como_todos():
    """Regla 1: nadie llama directo a un motor."""
    fuente = _leer(DESPACHO)
    assert 'if provider == "chatgpt":' in fuente, \
        "el motor premium ya no tiene rama en `_render_dispatch`"
    llamadas = fuente.count("_render_with_openai")
    assert llamadas == 2, (
        f"`_render_with_openai` aparece {llamadas} veces (se esperan 2: la "
        f"definición y la llamada del repartidor). Una llamada de más es un "
        f"camino que se salta el reparto de motores y el cobro.")


def test_la_lectura_verificada_gobierna_la_traduccion_visual():
    """La lectura correcta debe gobernar paredes, módulos, orden y cotas."""
    fuente = _leer(DESPACHO)
    i = fuente.index("async def generate_render_composed")
    j = fuente.index("\n    async def ", i + 10)
    cuerpo = fuente[i:j]
    assert "AUTHORITATIVE WRITTEN LAYOUT CONTRACT" in cuerpo
    assert "governs the translation into the render" in cuerpo
    assert "modules, columns, appliances, openings, order and explicit widths" in cuerpo
    assert "finishes-only request" in cuerpo
    assert "No verified written layout was supplied" in cuerpo
    assert "Apply ONLY these finishes/changes" not in cuerpo
