# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""IA PREMIUM — ChatGPT (OpenAI) en el CLON del Estudio 3D (09/09/2026).

El master: «podemos meter chatgpt con un botón de IA PREMIUM... quiero clonar
estudio 3D y en ese clon tenemos la IA de chatGPT para probarla».

LO QUE ESTE CANDADO PROTEGE, EN ORDEN DE LO QUE CUESTA SI SE ROMPE:

1. **QUE NO SE CUELE EN PRODUCCIÓN.** El Estudio 3D de producción está
   congelado (04/09) y es el único que ve un usuario que no sea master
   (regla 1). Si el botón premium apareciera allí, un render pasaría de 0,036 €
   a ~0,25 € — unas SIETE veces — sin que nadie lo hubiera decidido.

2. **QUE EL CROQUIS LLEGUE AL MODELO.** La API de imágenes de OpenAI tiene DOS
   llamadas y solo UNA acepta imágenes de entrada. Si el croquis se mandara por
   `images.generate`, se perdería EN SILENCIO: saldría una cocina bonita que no
   es la del cliente, sin un solo error. Es el fallo de la regla 2 con otro
   nombre.

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
APP = os.path.join(RAIZ, "frontend", "src", "App.js")

MOTOR = "chatgpt"
MODELO = "gpt-image-1"


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


def test_el_clon_SI_lo_ofrece_y_lo_traduce():
    botonera = _botonera(CLON)
    assert "'premium'" in botonera and "IA PREMIUM" in botonera, (
        "el clon ha perdido el botón premium: entonces no sirve para lo que se "
        "hizo, que es probar ese motor")
    assert f"if (motor === 'premium') return '{MOTOR}';" in _leer(CLON), (
        "el clon ya no traduce 'premium': el botón caería al motor por defecto "
        "y pintaría con otro SIN dar ningún error")


def test_el_laboratorio_es_SOLO_DEL_MASTER_en_permiso_y_en_enrutado():
    """Las dos mitades. Cerrar solo el botón es un cierre de adorno: bastaría
    con llegar a la pestaña para que la pantalla se pintara (regla 27)."""
    permisos = _leer(PERMISOS)
    m = re.search(r"if \(tab === 'estudio3dLab'\) \{(.*?)\}", permisos, re.S)
    assert m, "el laboratorio ya no tiene puerta propia en `canAccessTab`"
    assert "esMasterSistema(u)" in m.group(1), \
        "la puerta del laboratorio ya no es solo del master"
    assert "canUseAIAnalysis" not in m.group(1), (
        "el laboratorio ha pasado a colgar del permiso del Estudio 3D de "
        "producción: quitarle uno le quitaría el otro (regla 26)")
    assert "canOpenTab('estudio3dLab')" in _leer(APP), (
        "el enrutado del laboratorio ya no comprueba el permiso: se pintaría "
        "con solo llegar a esa pestaña")


# ─── 2. Que el croquis llegue al modelo ─────────────────────────────────────

def _cuerpo_del_motor():
    fuente = _leer(DESPACHO)
    i = fuente.index("async def _render_with_openai")
    j = fuente.index("\n    async def ", i + 10)
    return fuente[i:j]


def test_con_croquis_se_usa_la_llamada_QUE_ADMITE_IMAGENES():
    """`images.generate` NO acepta imágenes de entrada. Mandar el croquis por
    ahí no da error: devuelve una cocina que no es la del cliente."""
    cuerpo = _cuerpo_del_motor()
    assert "images.edit" in cuerpo, (
        "el motor premium ya no usa `images.edit`: el croquis del cliente no "
        "llegaría al modelo y la cocina que salga no será la suya (regla 2)")
    assert "images.generate" in cuerpo, (
        "sin `images.generate` no se puede renderizar desde texto solo")
    # LO QUE SE MIRA ES QUÉ LLAMADA CUELGA DE QUÉ CONDICIÓN, no en qué orden
    # aparecen los nombres en el fichero. La primera versión comparaba
    # posiciones y se ponía roja por el COMENTARIO de aquí arriba, que nombra
    # las dos llamadas para explicarlas: un candado que lee prosa no lee código.
    assert re.search(r"if refs:\s*\n\s*resp = await client\.images\.edit", cuerpo), (
        "`images.edit` ya no cuelga de que HAYA referencias: o se llama "
        "siempre (y falla sin imagen) o nunca — y entonces el croquis del "
        "cliente se pierde en silencio")
    assert re.search(r"else:\s*\n\s*resp = await client\.images\.generate", cuerpo), (
        "`images.generate` ya no es el camino SIN referencias: si se llamara "
        "habiendo croquis, saldría una cocina que no es la del cliente")


def test_las_referencias_van_como_FICHERO_y_con_nombre():
    """La librería deduce el tipo de fichero del `.name`. Sin él, la llamada se
    cae — y se cae DESPUÉS de que el master haya pagado el crédito."""
    cuerpo = _cuerpo_del_motor()
    assert "b64decode" in cuerpo, \
        "las referencias ya no se decodifican: OpenAI no admite base64 en el cuerpo"
    assert ".name = " in cuerpo, \
        "el fichero de referencia va sin nombre: la subida fallará"


def test_el_tope_de_siete_imagenes_se_respeta():
    """Regla 3 de CLAUDE.md."""
    cuerpo = _cuerpo_del_motor()
    assert "refs[:7]" in cuerpo, (
        "el motor premium ya no respeta el tope de 7 imágenes juntas (regla 3)")


# ─── 3. Que se cobre lo que cuesta ──────────────────────────────────────────

def test_el_motor_premium_tiene_precio_y_coste_en_creditos():
    uso = _leer(USO)
    assert f'"{MODELO}"' in uso, (
        f"«{MODELO}» no está en MODEL_PRICES: el informe de Consumo de IA lo "
        f"contaría a 0,00 € y el motor más caro sería el que menos parece gastar")
    m = re.search(r'"chatgpt":\s*([\d.]+)', uso)
    assert m, (
        "el motor premium no está en COSTE_POR_MOTOR: cobraría 1 crédito por "
        "omisión, como el motor de producción, costando unas 7 veces más")
    assert float(m.group(1)) > 1.0, (
        f"el motor premium cobra {m.group(1)} créditos, lo mismo o menos que el "
        f"de producción, y al proveedor se le paga bastante más por imagen")


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
