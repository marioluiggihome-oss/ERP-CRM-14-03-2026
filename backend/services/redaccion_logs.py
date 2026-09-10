# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""LO QUE NUNCA PUEDE ACABAR EN EL LOG DE ERRORES (10/09/2026).

Encontrado en la auditoría externa del 10/09. `_log_request_error` guardaba
2.000 caracteres del CUERPO de toda petición de escritura que fallara, sin
filtrar nada:

    "body": (body_text or "")[:2000],

Y solo guarda POST/PUT/PATCH/DELETE, que es EXACTAMENTE donde viajan las
credenciales. O sea que cada intento de login fallido —una contraseña mal
tecleada, que pasa todos los días— dejaba la contraseña EN CLARO dentro de
`error_log`, en la misma base de datos y sin caducidad.

No daba ningún error. Nadie lo iba a ver, porque el log de errores se mira
cuando algo falla y entonces se mira el `detail`, no el `body`.

DOS CIERRES, PORQUE UNO SOLO NO BASTA:

  1. **Las rutas de autenticación no guardan cuerpo, punto.** Ahí no hay nada
     que aporte al diagnóstico que valga el riesgo: el `detail` ya dice qué
     falló. Es una lista BLANCA al revés — se dice qué NO se guarda.
  2. **Y en todas las demás se REDACTA por nombre de campo**, recursivamente.
     Porque una contraseña no solo viaja en el login: viaja al crear un
     usuario, al cambiarla, y hay tokens y claves de API en otras rutas.

Se redacta por NOMBRE y no por valor: buscar «algo que parezca una contraseña»
es imposible de acertar, y fallar por defecto ahí es dejarla escrita.
"""
import json
import re

# Los nombres que NO se guardan nunca, mirando el nombre en minúsculas y SIN
# separadores: así `password`, `Password`, `new_password`, `newPassword`,
# `master-password` y `apiKey` caen todos con la misma regla. Escribir la lista
# con cada variante a mano es garantizar que falte una.
PALABRAS_PROHIBIDAS = (
    "password", "passwd", "contrasena", "contrasenya", "clave",
    "token", "secret", "apikey", "authorization", "cookie",
    "creditcard", "cvv", "iban",
)

REDACTADO = "«redactado»"

# Las rutas donde NO se guarda cuerpo NI redactado. Se comparan por trozo de
# ruta, no por igualdad: `/api/auth/login` y `/api/auth/register` caen las dos.
RUTAS_SIN_CUERPO = ("/auth/", "/login", "/register", "/password", "/token")

_SEPARADORES = re.compile(r"[^a-z0-9]")


def es_campo_sensible(nombre) -> bool:
    """¿El nombre de este campo delata algo que no puede guardarse?"""
    limpio = _SEPARADORES.sub("", str(nombre or "").lower())
    return any(p in limpio for p in PALABRAS_PROHIBIDAS)


def redactar(valor):
    """Sustituye los valores sensibles, ENTRANDO en listas y diccionarios.

    Recursivo a propósito: un `{"user": {"password": "..."}}` es exactamente lo
    que manda una pantalla de alta de usuario, y una redacción de un solo nivel
    lo dejaría escrito."""
    if isinstance(valor, dict):
        return {k: (REDACTADO if es_campo_sensible(k) else redactar(v))
                for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [redactar(v) for v in valor]
    return valor


def ruta_sin_cuerpo(path) -> bool:
    """¿Es una ruta de credenciales? Entonces no se guarda cuerpo ninguno."""
    p = str(path or "").lower()
    return any(t in p for t in RUTAS_SIN_CUERPO)


def cuerpo_para_el_log(path, body_text, tope=2000) -> str:
    """El cuerpo tal y como puede guardarse. Es la función que llama el server.

    EN LA DUDA NO SE GUARDA. Si el cuerpo no es un JSON que se pueda mirar
    campo a campo, no se puede saber qué lleva dentro — y un cuerpo opaco que
    resulta ser un formulario con la contraseña dentro es el mismo problema con
    otra forma. Se dice que había cuerpo y no se copia."""
    if ruta_sin_cuerpo(path):
        return ""
    texto = body_text or ""
    if not texto.strip():
        return ""
    try:
        datos = json.loads(texto)
    except Exception:
        return "«cuerpo no JSON: no se guarda»"
    return json.dumps(redactar(datos), ensure_ascii=False)[:tope]
