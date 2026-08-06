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
· IA 2, IA 3 e IA 4 son motores de PRUEBAS del master, para comparar y mejorar.
  Ahí puede cambiar lo que quiera — pero que el cambio se vea, no que aparezca
  solo. Por eso la prueba también los mira: no para prohibir, para que quien lo
  cambie tenga que decirlo aquí y el master se entere.

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
    """gemini-3-pro puede quedarse como RESPALDO, nunca como principal."""
    fuente = _leer(VISION)
    modelos = re.findall(r'"(gemini-[0-9a-z.\-]*image[0-9a-z.\-]*)"', fuente)
    if "gemini-3-pro-image-preview" in modelos:
        assert modelos.index("gemini-3-pro-image-preview") > 0, \
            "gemini-3-pro-image-preview ha vuelto a ser el modelo principal"


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
    porqué al lado, el siguiente que pase lo vuelve a cambiar."""
    assert "fidelidad al boceto" in _leer(VISION), \
        "se ha borrado la nota que explica por qué manda gemini-2.5-flash-image"
    assert "NO flux-schnell" in _leer(RENDER), \
        "se ha borrado la nota que explica por qué IA 3 va con Flux Pro"
