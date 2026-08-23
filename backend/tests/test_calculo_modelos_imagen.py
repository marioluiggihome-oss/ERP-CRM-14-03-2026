# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del MODELO de imagen. No se cambia sin permiso del master.

El 04/08 se puso candado al REPARTO de motores (IA 1→gemini, IA 2→manus,
IA 3→flux, IA 4→gemini flash) y ha aguantado. Pero quedaba un hueco: qué
modelo usa cada motor POR DENTRO. Por ahí se coló todo esto:

· `gemini-3-pro-image-preview` pasó a ser el modelo principal de IA 1. Hace
  imágenes más vistosas pero es más "creativo": se inventa la distribución y
  deja de seguir el boceto. El master lo notó como «IA 1 interpreta peor» sin
  que nada del reparto de motores hubiera cambiado. Revertido el 06/08.
· IA 3 pasó de `flux-1.1-pro` a `flux-schnell` el 01/08, por coste
  (~0,003 $/img). Schnell genera en 4 pasos de difusión frente a los ~25-50
  del Pro: es otro producto. El master pulsaba IA 3 creyendo que usaba el
  motor de calidad. Revertido el 06/08.

Los dos cambios se hicieron sin pedírselo al master, y ninguno rompió nada:
el ERP seguía funcionando y devolviendo imágenes. Por eso hace falta esta
prueba — un cambio de modelo no da error, solo da PEOR RESULTADO, y eso no
se ve hasta que el master mira un render y dice «esto no es mi cocina».

NO todas pesan igual (lo dijo el master el 06/08):

· **IA 1 es la de producción.** Es la que usa para los clientes y la que tiene
  que ser fiel al boceto. Su modelo NO se toca. Cierre duro.
· IA 3, IA 4 e IA 7 son motores de PRUEBAS del master, para comparar y mejorar.
  Ahí puede cambiar lo que quiera — pero que el cambio se vea, no que aparezca
  solo. Por eso la prueba también los mira: no para prohibir, para que quien lo
  cambie tenga que decirlo aquí y el master se entere.
  (IA 2 se apagó el 18/08; su candado es `test_calculo_ia2_apagada.py`.)

Para cambiar un modelo: pedírselo al master, y actualizar este fichero a
propósito y dejando constancia.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VISION = os.path.join(RAIZ, "backend", "services", "llm_vision.py")
RENDER = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")

# Modelo de imagen de IA 1. Manda la FIDELIDAD AL BOCETO, no lo bonito que
# quede: el usuario sube un croquis acotado y espera SU cocina.
MODELO_PRINCIPAL = "gemini-2.5-flash-image"
# Modelo de IA 3 en Replicate. Pro, no Schnell.
MODELO_FLUX = "black-forest-labs/flux-1.1-pro"
# Modelo de IA 7 (Nano Banana Pro), puesto por el master el 18/08: «ponlo en la
# IA 7 con banana pro». Se deja escrito AQUI porque es lo que pide la regla 10
# de CLAUDE.md, y porque es justo el modelo que este fichero prohíbe en IA 1.
#
# Las dos cosas son verdad a la vez y conviene entender por qué:
#   · En IA 1 está PROHIBIDO. IA 1 es producción: tiene que salir la cocina del
#     cliente, y este modelo es más "creativo" —más bonito, menos fiel—.
#   · En IA 7 está PUESTO A PROPÓSITO. IA 7 es el banco de pruebas del master:
#     mismo encargo que IA 1, solo cambia el modelo, para poder comparar.
# Entra por `model_override` en `render_3d.py`, NO por la cascada de
# `llm_vision.py`. Esa distinción es la que hace que las dos cosas convivan, y
# por eso hay abajo una prueba que la vigila.
MODELO_IA7_PRO = "gemini-3-pro-image-preview"


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def test_el_modelo_principal_de_imagen_es_el_que_sigue_el_boceto():
    """CANDADO DURO — IA 1, la de producción.

    El primero de la lista es el que se usa. Si alguien pone otro delante,
    IA 1 deja de respetar el boceto y nadie se entera hasta que el master mira
    un render y ve que no es la cocina del cliente. Esta es LA que importa."""
    fuente = _leer(VISION)
    modelos = re.findall(r'"(gemini-[0-9a-z.\-]*image[0-9a-z.\-]*)"', fuente)
    assert modelos, "ya no hay lista de modelos de imagen en llm_vision.py"
    assert modelos[0] == MODELO_PRINCIPAL, (
        f"el modelo principal de imagen es ahora «{modelos[0]}» y debe ser "
        f"«{MODELO_PRINCIPAL}». Un modelo más 'creativo' se inventa la "
        f"distribución en vez de seguir el boceto del cliente. Si el cambio "
        f"es a propósito, pídeselo al master y actualiza este fichero.")


def test_el_modelo_creativo_no_se_cuela_por_delante():
    """gemini-3-pro no va NI de principal NI de respaldo.

    Antes se le dejaba quedarse detrás. Ya no: un respaldo se usa justo el día
    que falla el principal, o sea el día que nadie está mirando, y entonces el
    render deja de seguir el boceto — pero sale igual de bonito, así que no se
    nota en la imagen. Si algún día se quiere de verdad, que sea una decisión
    del master y se escriba aquí; ver también
    `test_el_respaldo_es_el_mismo_modelo_y_no_uno_mas_creativo`."""
    fuente = _leer(VISION)
    modelos = re.findall(r'"(gemini-[0-9a-z.\-]*image[0-9a-z.\-]*)"', fuente)
    assert "gemini-3-pro-image-preview" not in modelos, (
        "gemini-3-pro-image-preview ha vuelto a la cascada: es más 'creativo' e "
        "ignora el layout, o sea que se inventa la distribución del cliente")


def test_ia7_usa_el_modelo_pro_y_solo_por_override():
    """AVISO — IA 7 es el banco de pruebas del master, no producción.

    El 18/08 el master pidió «ponlo en la IA 7 con banana pro». Queda escrito
    aquí, que es lo que manda la regla 10: en IA 2/3/4/7 el master cambia de
    modelo cuando quiera, pero el cambio se escribe y así no aparece solo.

    Y se comprueba una cosa más, que es la que de verdad importa: que este
    modelo entra por `model_override` y NO por la cascada de `llm_vision.py`.
    Es lo único que separa «el master lo ha elegido para comparar» de «se ha
    colado en producción y ahora IA 1 se inventa la distribución»."""
    fuente = _leer(RENDER)
    assert MODELO_IA7_PRO in fuente, (
        f"IA 7 ya no usa {MODELO_IA7_PRO}. Si el master lo ha cambiado, que "
        f"quede escrito aquí; si se ha cambiado solo, esto es el aviso.")
    assert f'model_override="{MODELO_IA7_PRO}"' in fuente, (
        f"{MODELO_IA7_PRO} ya no entra por `model_override`. Como entre por la "
        f"cascada, se convierte en el respaldo de IA 1 y el día que falle el "
        f"principal la cocina del cliente deja de ser la del cliente.")


def test_el_modelo_pro_no_se_escapa_de_IA_7():
    """CANDADO DURO — el Pro se queda donde el master lo puso, y en ningún
    sitio más.

    La prueba de arriba mira que IA 7 lo tenga; esta mira que NADIE MÁS lo
    tenga. Sin ella bastaría con que alguien copiase la línea del
    `model_override` al render de IA 1 «para probar»: las dos pruebas seguirían
    en verde y producción se habría movido de modelo."""
    fuente = _leer(RENDER)
    apariciones = re.findall(rf'"{re.escape(MODELO_IA7_PRO)}"', fuente)
    assert len(apariciones) == 1, (
        f"{MODELO_IA7_PRO} aparece {len(apariciones)} veces en render_3d.py y "
        f"solo puede aparecer UNA, la de IA 7. Cada copia extra es un camino "
        f"por el que el modelo creativo llega a un cliente.")
    # Y en el trozo de IA 7, no en el de otro.
    ini = fuente.index('if provider == "banana_pro"')
    fin = fuente.index("if provider ==", ini + 10)
    assert MODELO_IA7_PRO in fuente[ini:fin], (
        f"{MODELO_IA7_PRO} ya no está dentro de la rama de IA 7: se ha movido "
        f"a otro motor")


def test_ia3_usa_flux_pro_y_no_la_version_barata():
    """AVISO — IA 3 es motor de pruebas del master, no de producción.

    Aquí el master SÍ puede cambiar de modelo cuando quiera: para eso lo tiene.
    Lo que no vale es que el modelo cambie solo. Schnell son 4 pasos de difusión
    frente a los ~25-50 del Pro, y se cambió por coste sin decirlo. Si el master
    quiere probar otro, que lo ponga aquí y así queda dicho."""
    fuente = _leer(RENDER)
    assert MODELO_FLUX in fuente, (
        f"IA 3 ya no usa {MODELO_FLUX}. Si se ha vuelto a cambiar por coste, "
        f"eso lo decide el master, no el código.")
    # Se mira el CÓDIGO, no los comentarios: "flux-schnell" aparece a propósito
    # en la nota que explica por qué NO se usa.
    codigo = "\n".join(l.split("#")[0] for l in fuente.splitlines())
    assert "flux-schnell" not in codigo, (
        "IA 3 ha vuelto a flux-schnell: el master pulsará IA 3 creyendo que "
        "usa el motor de calidad y recibirá el barato.")


def test_el_motivo_de_cada_modelo_queda_escrito_en_el_codigo():
    """Un modelo cambiado no rompe nada: solo empeora el resultado. Sin el
    porqué al lado, el siguiente que pase lo vuelve a cambiar.

    Lo que se exige es que el porqué esté escrito, no una redacción concreta:
    «fidelidad al boceto» y «fidelidad del boceto» dicen lo mismo."""
    assert re.search(r"fidelidad (al|del) boceto", _leer(VISION)), \
        "se ha borrado la nota que explica por qué manda gemini-2.5-flash-image"
    assert "NO flux-schnell" in _leer(RENDER), \
        "se ha borrado la nota que explica por qué IA 3 va con Flux Pro"


def test_el_render_no_se_queda_sin_respaldo():
    """Cuando Google retira o renombra un modelo, la llamada devuelve NOT_FOUND.
    Con UN SOLO nombre en la lista, el Estudio 3D se queda sin renders de golpe
    y sin nada a lo que caer: no es que salgan peor, es que no sale ninguno y la
    fábrica se para. El respaldo tiene que existir."""
    fuente = _leer(VISION)
    modelos = re.findall(r'"(gemini-[0-9a-z.\-]*image[0-9a-z.\-]*)"', fuente)
    assert len(modelos) >= 2, (
        "la cascada de imagen se ha quedado con un solo modelo: el día que "
        "Google le cambie el nombre, el Estudio 3D deja de generar renders")


def test_el_respaldo_es_el_mismo_modelo_y_no_uno_mas_creativo():
    """El respaldo está para cubrir un CAMBIO DE NOMBRE, no para cambiar de
    motor. Si detrás se cuela uno más creativo, el día que falle el principal
    el render dejará de seguir el boceto — y saldrá igual de bonito, así que
    nadie lo notará mirando la imagen."""
    fuente = _leer(VISION)
    modelos = re.findall(r'"(gemini-[0-9a-z.\-]*image[0-9a-z.\-]*)"', fuente)
    principal = modelos[0]
    # La familia es el nombre sin el sufijo de publicación (-preview, -exp…).
    familia = principal.replace("-preview", "").replace("-exp", "")
    for m in modelos[1:]:
        assert m.replace("-preview", "").replace("-exp", "") == familia, (
            f"«{m}» no es el mismo modelo que «{principal}»: como respaldo "
            f"cambia el motor, no solo el nombre, y la fidelidad al boceto "
            f"dejaría de estar garantizada sin que se vea en la imagen")


# ── Qué modelo hay detrás NO se le enseña al cliente ─────────────────────────

ESTUDIO_3D = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
PANEL_MASTER = os.path.join(
    RAIZ, "frontend", "src", "components", "settings", "UsageReportTab.jsx")


def test_el_modelo_no_se_ensena_en_la_pantalla_del_cliente():
    """Qué motor y qué modelo hay detrás es SECRETO INDUSTRIAL (Ley 1/2019, y
    está en las condiciones de uso). El Estudio 3D lo ve cualquier carpintero
    con cuenta: ahí no se escribe el nombre del modelo."""
    fuente = _leer(ESTUDIO_3D)
    visibles = [m for m in ("gemini-2.5-flash-image", "gemini-3-pro-image-preview",
                            "flux-1.1-pro", "flux-schnell")
                if m in "\n".join(l.split("//")[0] for l in fuente.splitlines())]
    assert not visibles, (
        f"el nombre del modelo {visibles} ha llegado a la pantalla del Estudio "
        f"3D, que ve cualquier cliente. Eso va en Ajustes → Consumo de IA, que "
        f"está cerrado a master.")


def test_el_master_si_puede_ver_que_modelos_se_estan_usando():
    """Sin poder verlo, un cambio de modelo vuelve a ser invisible hasta que
    salga un render malo."""
    assert "by_model" in _leer(PANEL_MASTER), \
        "el panel de master ya no enseña los modelos realmente usados"
