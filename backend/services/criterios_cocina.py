# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
criterios_cocina.py — El criterio profesional del proyecto, en un solo sitio.

Aquí vive lo que sabe un equipo de cocina cuando mira un proyecto:

  · DISEÑADOR DE COCINAS: zonas de trabajo, triángulo, orden de la secuencia,
    espacios de apoyo a los lados del fregadero y de la placa.
  · ARQUITECTO TÉCNICO: medidas reales de fabricación de ESTA fábrica, pasos
    mínimos, alturas, fondos, y qué es imposible aunque quede bonito.
  · INTERIORISTA: composición, alineaciones, cuántos acabados aguanta una
    cocina, luz, y por qué un remate mal resuelto se ve más que un mueble caro.
  · VENDEDOR DE COCINAS: qué hace que una imagen convenza y qué la hunde
    (encimeras llenas de trastos, electrodomésticos que nadie ha pedido).

Se usa en dos sitios y por eso está aquí y no repartido: el prompt del RENDER
(que dibuja) y el prompt del ANALIZADOR (que lee un plano), más un revisor
que compara una composición detectada contra estos criterios y devuelve avisos.

REGLA QUE MANDA SOBRE TODO LO DEMÁS: los números de fabricación de abajo son
los de esta casa. Una medida que no se conoce NO se rellena con un valor
plausible; se deja vacía y se avisa.
"""

# ─── Medidas REALES de fabricación (mm salvo que se diga) ────────────────────
# Fuente: la memoria del proyecto. Cualquier cifra fuera de estos rangos es un
# error, no una variante.
ESTANDARES = {
    "casco_bajo_alto": 800,            # en esta fábrica los bajos SOLO se hacen a 80
    "zocalo": (100, 150),
    "encimera_grosor": (20, 40),
    "altura_trabajo": (900, 940),      # cara superior de la encimera
    "casco_alto_alturas": (700, 900),
    "encimera_a_alto": (550, 600),     # hueco libre entre encimera y mueble alto
    "columna_alturas": (2000, 2200),
    "mediacolumna": 1300,
    "sobreencimera": (1270, 1470),
    "fondo_alto": 330,
    "fondo_bajo": 580,
    "anchos_estandar_cm": [15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120],
    "techo_libre": (2400, 2700),
}

# ─── Criterios de ergonomía y uso (diseñador de cocinas) ─────────────────────
ERGONOMIA = {
    "apoyo_junto_fregadero": 400,   # encimera libre a un lado del fregadero
    "apoyo_junto_placa": 400,       # encimera libre a un lado de la placa
    "placa_a_rincon": 300,          # separación mínima de la placa a una esquina/pared
    "placa_a_fregadero": 600,       # zona de preparación entre agua y fuego
    "campana_sobre_placa": (650, 750),
    "paso_un_cocinero": 1200,       # pasillo entre frentes enfrentados
    "paso_dos_cocineros": 1500,
    "isla_a_frente": 900,           # paso alrededor de una isla
    "triangulo_total": (3600, 6600),  # suma de los tres lados fregadero-placa-frigo
}


# ─── Bloque para el prompt del RENDER (va al modelo de imagen, en inglés) ────
# No lleva cotas escritas: un modelo de imagen no sabe escribir números. Lleva
# PROPORCIONES y relaciones, que es lo que sí sabe dibujar.
CRITERIOS_RENDER_COCINA = """
REAL CABINETRY GEOMETRY (this workshop's actual build, follow it strictly):
- Base cabinets: 80 cm tall carcass standing on a recessed plinth of 10-15 cm,
  so the worktop top surface sits at 90-94 cm from the floor. Base depth ~58 cm.
- Worktop: a single continuous slab of uniform 2-4 cm thickness, with a matching
  upstand or backsplash. It must read as one plane, never as segments.
- Wall units: 70 or 90 cm tall, ~33 cm deep, hung leaving a clear 55-60 cm gap
  between the worktop and the underside of the wall units.
- Tall units/columns: 200 or 220 cm tall, same depth as the base run.
- Toe-kick, worktop line and the underside of the wall units must run perfectly
  level and continuous across the whole composition.

PROFESSIONAL KITCHEN LAYOUT (work sequence, left to right or around the corner):
storage → sink (washing) → preparation worktop → hob (cooking) → serving.
- Keep clear worktop beside the sink and beside the hob; a hob or a sink jammed
  against a wall, a corner or a tall unit reads as amateur work.
- Never place the hob directly against a side wall, a corner or a fridge without
  a buffer of worktop.
- Leave usable preparation worktop between the sink and the hob.
- The extractor/hood is centred over the hob, clearly above it.
- In galley or parallel layouts keep a generous walking corridor between fronts;
  around an island keep a comfortable walkway on every side.

COMPOSITION AND FINISH (interior designer's eye):
- Align the top of the tall units with the top of the wall units; when heights
  differ, resolve it with a deliberate horizontal, never with a random step.
- Uniform reveal gaps between all fronts; door and drawer lines continue across
  neighbouring modules.
- End the run with a finished side panel or a filler strip against the wall,
  never with an exposed raw carcass edge.
- At most three finishes in the whole kitchen (cabinet colour, worktop, and one
  accent such as wood or metal). Matte or satin surfaces, not glossy plastic.
- Handles: keep one single system throughout (gola/handleless, or the same pull
  on every front). Do not mix systems in one composition.
- Integrated appliances sit flush with the fronts; free-standing ones align
  their faces with the fronts.

WHAT MAKES A KITCHEN IMAGE SELL (and what ruins it):
- Clean, nearly empty worktops. At most two or three restrained props.
- Natural daylight from the side, soft shadows, believable reflections.
- No clutter, no random plants on every surface, no food styling.
- Do NOT add appliances, islands, windows or furniture that the brief does not
  mention: an invented element turns the render into a promise nobody can build.
"""


# ─── Bloque para el prompt del ANALIZADOR (lo lee un modelo de visión) ───────
CRITERIOS_ANALISIS = """

CRITERIO PROFESIONAL AL LEER LA COMPOSICIÓN (úsalo para no dejarte muebles):
- Una cocina real sigue una secuencia: almacenaje → fregadero → encimera de
  preparación → placa → servicio. Si en el plano ves fregadero y placa, entre
  medias casi siempre hay uno o dos módulos de preparación: no los omitas.
- Bajo el fregadero SIEMPRE hay un mueble (bajo fregadero). Bajo la placa
  también (bajo placa o de cajones). El aparato va DENTRO del mueble.
- El lavavajillas y la lavadora NO llevan mueble: ocupan un hueco entre bajos.
  Cuenta ese hueco por su ancho, pero no lo cuentes como casco.
- Encima de la placa hay campana; encima del fregadero, muchas veces un
  escurreplatos o un alto. Si el plano lo dibuja, va en la lista.
- Los extremos de una fila se rematan con un costado visto o una regleta de
  ajuste a la pared: son piezas del pedido y se olvidan siempre.
- Las columnas (horno, microondas, despensa, frigorífico) van juntas formando
  una torre; su altura es la del conjunto, no la de cada hueco.

MEDIDAS QUE PUEDES DAR POR CIERTAS EN ESTA FÁBRICA (si no están rotuladas):
- Bajos: 80 cm de alto de casco, sobre zócalo de 10-15 cm; fondo 58 cm.
- Altos: 70 o 90 cm de alto; fondo 33 cm.
- Columnas: 200 o 220 cm de alto.
- Anchos estándar en cm: 15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120.
NO uses estos valores para inventar un ANCHO que no está escrito: el ancho se
lee del plano o se deja vacío.
"""


# ─── Criterio gráfico (lo que sale impreso o en pantalla) ───────────────────
# Un presupuesto o un pedido mal compuesto se lee mal, y lo que se lee mal se
# firma con dudas. Esto se aplica a los PDF que genera el ERP y a cómo se
# presentan los listados.
CRITERIOS_GRAFICOS = """
JERARQUÍA: una sola cosa manda en cada página (el título), lo demás baja de
tamaño y de peso. Tres niveles bastan: título, encabezado de tabla, dato.
NÚMEROS: siempre alineados a la DERECHA y con el mismo número de decimales;
así se comparan de un vistazo y los errores de coma saltan solos. Las medidas,
con su unidad indicada una vez en la cabecera, no repetida en cada celda.
ALINEACIÓN: todo cuelga de una rejilla. Márgenes iguales arriba/abajo y a los
lados. Nada centrado "a ojo".
AIRE: el espacio en blanco no es espacio perdido; es lo que separa bloques sin
tener que dibujar líneas. Antes de añadir una raya, prueba a añadir aire.
COLOR: sirve para SIGNIFICAR, no para decorar. Un color por estado (correcto,
aviso, error) y nada más. Si el documento se imprime en blanco y negro tiene
que seguir entendiéndose: el color nunca es el único portador del mensaje.
TIPOGRAFÍA: una familia, dos pesos. Cuerpo de texto legible antes que grande.
TABLAS: cabecera con fondo suave, filas alternas muy tenues, sin cuadrícula
completa; la línea horizontal separa, la vertical casi nunca hace falta.
CONTRASTE: texto oscuro sobre fondo claro. Un gris demasiado claro sobre blanco
no se lee ni en pantalla ni impreso, por elegante que parezca.
IDENTIDAD: el logotipo va donde no compita con el contenido, a un tamaño
discreto y constante. La marca no debe pisar el dato.
"""


# ─── Revisor de composición ─────────────────────────────────────────────────
def _cm(v):
    """Pasa una medida a cm venga en mm o en cm. Devuelve None si no hay dato."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n / 10.0 if n >= 200 else n


def _texto(m):
    return " ".join(str(m.get(k) or "") for k in
                    ("tipo", "subtipo", "nombre", "descripcion", "nombre_catalogo",
                     "posicion")).upper()


def revisar_composicion(muebles: list) -> list:
    """Repasa una composición detectada con criterio de oficio.

    Devuelve una lista de avisos {nivel, texto}: nivel 'error' es algo
    imposible de fabricar, 'aviso' es algo que un profesional miraría dos veces.
    NO corrige nada por su cuenta: quien decide es quien firma el proyecto.
    """
    avisos = []
    if not muebles:
        return avisos

    def añadir(nivel, texto):
        if not any(a["texto"] == texto for a in avisos):
            avisos.append({"nivel": nivel, "texto": texto})

    anchos_ok = set(ESTANDARES["anchos_estandar_cm"])
    hay_fregadero = hay_placa = hay_campana = hay_bajo_fregadero = False
    n_bajos = n_altos = 0

    for m in muebles:
        t = _texto(m)
        tipo = (m.get("tipo") or "").upper()
        uds = int(m.get("cantidad") or m.get("qty") or 1)
        ancho = _cm(m.get("ancho_real") or m.get("ancho_estimado") or m.get("ancho"))
        alto = _cm(m.get("alto_real") or m.get("alto_estimado") or m.get("alto"))

        if "FREGADERO" in t:
            hay_fregadero = True
            if tipo == "BAJO" or "BAJO" in t:
                hay_bajo_fregadero = True
        if "PLACA" in t or "COCCION" in t or "COCCIÓN" in t or "INDUCCION" in t:
            hay_placa = True
        if "CAMPANA" in t or "EXTRACTOR" in t:
            hay_campana = True
        if tipo == "BAJO":
            n_bajos += uds
        if tipo in ("ALTO", "ALTILLO"):
            n_altos += uds

        # Ancho fuera de los estándar de fabricación.
        if ancho and round(ancho) not in anchos_ok:
            cercano = min(anchos_ok, key=lambda x: abs(x - ancho))
            if abs(cercano - ancho) > 2:
                añadir("aviso", f"Ancho de {round(ancho)} cm fuera de los estándar "
                                f"(el más cercano sería {cercano} cm): confírmalo antes de pedir.")

        # Alturas imposibles para su tipo.
        if alto:
            if tipo == "BAJO" and abs(alto - 80) > 2:
                añadir("error", f"Un bajo de {round(alto)} cm: en esta fábrica los bajos "
                                f"se fabrican SOLO a 80 cm de casco.")
            if tipo == "ALTO" and round(alto) not in (70, 90):
                añadir("aviso", f"Un alto de {round(alto)} cm: las alturas de alto son 70 o 90.")
            if tipo == "COLUMNA" and round(alto) not in (200, 220):
                añadir("aviso", f"Una columna de {round(alto)} cm: las alturas de columna "
                                f"son 200 o 220.")

    # Coherencia de la composición (lo que miraría un diseñador).
    if hay_fregadero and not hay_bajo_fregadero:
        añadir("aviso", "Hay fregadero pero no aparece el mueble bajo fregadero: "
                        "el seno va apoyado en un mueble, revisa si falta.")
    if hay_placa and not hay_campana:
        añadir("aviso", "Hay placa de cocción y no se ha detectado campana: "
                        "comprueba si el plano la lleva.")
    if n_bajos and not n_altos:
        añadir("aviso", "Solo se han detectado muebles bajos. Si la cocina lleva altos "
                        "o columnas, se han quedado fuera del listado.")
    if n_bajos > 3 and not any("COSTADO" in _texto(m) or "REGLETA" in _texto(m)
                               for m in muebles):
        añadir("aviso", "No hay costados vistos ni regletas de ajuste: los remates de "
                        "los extremos son piezas del pedido y se olvidan casi siempre.")
    return avisos
