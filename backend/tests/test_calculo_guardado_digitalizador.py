# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""El digitalizador guarda de verdad, y si no puede lo dice.

06/08/2026: el master pulsaba GUARDAR y el presupuesto no aparecía en el
historial. Dos fallos encadenados:

1. Las peticiones del digitalizador salían con `headers: {'Content-Type': ...}`
   y SIN el token. El router exige permiso (`canUseDigitalizador`), así que el
   servidor contestaba 401 y no se guardaba nada.
2. El código solo miraba `if (response.ok) savedItems.push(...)`. Si fallaba,
   no hacía nada: la pantalla decía "guardado" igual. Un guardado que falla en
   silencio es peor que uno que falla: se pierde el trabajo y nadie se entera.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "Digitalizador.jsx")
RUTA = os.path.join(RAIZ, "backend", "routes", "digitalizador.py")


def _fuente():
    with open(PANTALLA, encoding="utf-8") as f:
        return f.read()


def test_el_backend_sigue_exigiendo_permiso():
    """Si algún día deja de exigirlo, esta prueba avisa: el token del frontend
    dejaría de ser obligatorio y el candado de módulo sería de adorno."""
    with open(RUTA, encoding="utf-8") as f:
        assert "canUseDigitalizador" in f.read(), \
            "el digitalizador ya no comprueba el permiso de módulo"


def test_ninguna_peticion_sale_sin_token():
    """CANDADO: 9 peticiones iban sin `Authorization` y todas recibían 401."""
    sin_token = re.findall(r"headers:\s*\{\s*'Content-Type':\s*'application/json'\s*\}",
                           _fuente())
    assert not sin_token, (
        f"{len(sin_token)} petición(es) del digitalizador vuelven a salir sin el "
        f"token. El servidor las rechazará con 401 y el guardado no llegará.")


def test_se_manda_el_token():
    assert "authHeaders" in _fuente(), \
        "el digitalizador ya no importa authHeaders: sus peticiones irán sin token"


def test_un_guardado_fallido_no_pasa_por_bueno():
    """Lo peor del fallo no era el 401: era que la pantalla decía «guardado»."""
    fuente = _fuente()
    ini = fuente.index("const executeSave")
    fin = fuente.index("savedItems.length", ini)
    bloque = fuente[ini:fin]
    for respuesta in ("historyResponse", "presupuestoResponse"):
        pos = bloque.index(f"if ({respuesta}.ok)")
        tramo = bloque[pos:pos + 500]
        assert "else" in tramo and "throw" in tramo, (
            f"un fallo de {respuesta} vuelve a ignorarse: el usuario creerá que "
            f"ha guardado y habrá perdido el presupuesto.")
