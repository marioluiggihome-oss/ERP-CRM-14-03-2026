# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: IA 2 (Manus) está APAGADA, y apagada de verdad.

POR QUÉ SE APAGA
----------------
El master, 18/08/2026: «a la IA 2, cada vez que le mando hacer algo tarda un
montón». Y después: «vamos a ir apagando lo que no estamos usando, apaga la
IA 2».

Tardaba por lo que es. Manus NO es un modelo de imagen: es un AGENTE. Gemini
es una llamada —le mandas el encargo y devuelve la foto en unos segundos—;
Manus crea una tarea, un agente se pone a trabajar en ella, y el ERP pregunta
cada 5 segundos HASTA 5 MINUTOS (`wait_for_completion(timeout=300)`). Que
tarde minutos no era una avería: era lo que es.

Lo que sí era culpa nuestra es lo que costaba cuando NO salía: se agotaban los
300 segundos y SOLO ENTONCES se caía a Gemini. Cinco minutos de espera para
acabar con el render que Gemini habría dado al principio.

APAGADA, NO BORRADA
-------------------
El motor entero sigue en el código. Encenderlo otra vez es poner
MOTOR_MANUS_ACTIVO=1 en el entorno. Borrar una integración que costó escribir,
para tener que rehacerla si algún día se quiere, es tirar trabajo.

LO QUE SE PROTEGE
-----------------
1. Que esté apagada POR DEFECTO. Un interruptor que viene encendido no es un
   interruptor.
2. Que pedirla no cueste los cinco minutos. Una pestaña vieja abierta, o una
   llamada guardada, seguirán mandando 'manus': el render tiene que salir EN
   EL ACTO por el motor de siempre, no tras agotar el tiempo de espera.
3. Que no desaparezca en silencio. Si algo sigue pidiéndola, queda escrito.
4. Que el botón no esté en la pantalla — ni para el master ni para nadie.
"""
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(BACKEND)
RENDER = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _codigo_jsx():
    return "\n".join(l.split("//")[0] for l in _leer(ESTUDIO).splitlines())


def _bloque_dispatch():
    src = _leer(RENDER)
    i = src.index("_manus_encendido")
    return src[i:src.index("# IA 3:", i)]


# ─── 1. Apagada por defecto ────────────────────────────────────────────────

def test_manus_esta_apagada_salvo_que_se_encienda_a_mano():
    bloque = _bloque_dispatch()
    assert 'os.environ.get("MOTOR_MANUS_ACTIVO"' in bloque, (
        "IA 2 vuelve a encenderse sola con solo tener clave: cada render que "
        "alguien pida por ahi se ira a minutos")
    assert "manus_ready = _manus_encendido and" in bloque, (
        "el interruptor existe pero no manda: tener la clave vuelve a bastar "
        "para encender Manus")


def test_el_interruptor_no_viene_encendido():
    """Un interruptor con valor por defecto encendido no es un interruptor."""
    bloque = _bloque_dispatch()
    i = bloque.index('os.environ.get("MOTOR_MANUS_ACTIVO"')
    llamada = bloque[i:i + 160]
    # El segundo argumento de `environ.get` es lo que vale si NADIE lo define.
    assert 'MOTOR_MANUS_ACTIVO", ""' in llamada, (
        "el interruptor de Manus trae un valor por defecto: si ese valor cuenta "
        "como encendido, IA 2 sigue viva sin que nadie lo haya pedido")


def test_pedir_ia2_apagada_no_cuesta_los_cinco_minutos():
    """Es el motivo de la queja. Una pestaña vieja sigue mandando 'manus'; el
    render tiene que salir EN EL ACTO por el motor de siempre."""
    src = _leer(RENDER)
    i = src.index("_manus_encendido")
    # La rama que llama a Manus tiene que seguir exigiendo `manus_ready`.
    j = src.index('if provider == "manus" and manus_ready:', i)
    assert j > i, (
        "la llamada a Manus ya no comprueba que este encendida: se volveran a "
        "esperar hasta 5 minutos por un motor apagado")


def test_no_desaparece_en_silencio():
    bloque = _bloque_dispatch()
    assert "logger.info(" in bloque and "apagado" in bloque, (
        "si algo sigue pidiendo IA 2 no queda dicho en ningun sitio: un motor "
        "que desaparece sin avisar es un fallo que nadie puede diagnosticar")


# ─── 2. Apagada, NO borrada ────────────────────────────────────────────────

def test_el_motor_sigue_ahi_para_poder_volver():
    """Borrar la integracion obligaria a reescribirla si algun dia se quiere."""
    src = _leer(RENDER)
    assert "async def _render_with_manus" in src, (
        "se ha borrado el motor de Manus en vez de apagarlo: volver a tenerlo "
        "costaria reescribir la integracion entera")
    motor = os.path.join(BACKEND, "services", "luiggi_ai", "engine_core.py")
    assert os.path.exists(motor), "se ha borrado el nucleo del motor alternativo"


# ─── 3. Fuera de la pantalla ───────────────────────────────────────────────

def test_el_boton_de_ia2_ya_no_se_ofrece():
    codigo = _codigo_jsx()
    i = codigo.index("<span className=\"text-[11px] font-black text-slate-500 uppercase tracking-wider\">Motor</span>")
    fila = codigo[i:i + 1400]
    assert "'ia2'" not in fila, (
        "el boton de IA 2 ha vuelto a la fila de motores: se pulsara y se "
        "esperaran minutos")
    # Y tampoco para el usuario normal, que es la lista corta del final.
    assert fila.count("'ia1'") >= 2, \
        "la lista de motores del usuario normal ha cambiado de forma inesperada"


def test_la_pantalla_no_puede_pedir_manus():
    """Aunque quede un 'ia2' guardado en el navegador de alguien."""
    codigo = _codigo_jsx()
    assert "return 'manus'" not in codigo, (
        "la pantalla puede volver a pedir el motor Manus: un 'ia2' guardado en "
        "una pestaña vieja mandara al usuario a esperar cinco minutos")
