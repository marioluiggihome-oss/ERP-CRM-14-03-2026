# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del dictado por voz. EJECUTA EL CÓDIGO DE VERDAD.

LO PRIMERO, PORQUE ES LO QUE FALLÓ DOS VECES
--------------------------------------------
La versión anterior de este fichero traía la regla REESCRITA EN PYTHON:

    def leer_resultados(resultados):        # ← una COPIA, no el código
        ...

Probaba una copia hecha a mano y no llamaba al JavaScript ni una vez. O sea que
podía estar en verde con el dictado roto — y lo estuvo. Es el mismo fallo que
costó una caída en producción con la tarifa de ACB (CLAUDE.md, regla 31): «hay
que EJECUTAR el fichero, no solo leerlo», y el mismo que dejó el área del
cooperativista sin consolidar un solo pedido (regla 17), donde el candado
pasaba porque le daban diccionarios preparados a mano.

Ahora todo lo de aquí abajo se ejecuta EN NODE contra `frontend/src/dictado.js`,
que es el fichero que corre en la tablet del master.

LOS TRES FALLOS QUE HA TENIDO ESTE BOTÓN
----------------------------------------
1ª (jul.) «cuandocuandocuando dicto» — se sumaban los finales dando por hecho
   que llegan una sola vez. En Android se reentregan.

2ª (09/08) «elelelel bajoel bajoel bajo fre» — se seguían sumando los
   PROVISIONALES, que son el navegador pensando en voz alta y manda la frase a
   medias una y otra vez.

3ª (09/09) EL BOTÓN MENTÍA SOBRE SÍ MISMO. El master: «no dicta bien, no
   funciona bien». En Android, Chrome lanza `no-speech` a los pocos segundos de
   silencio —es lo normal—, y el hook apagaba el botón ante CUALQUIER error;
   justo después `onend` reabría el micro y salía sin reponer el estado. El
   botón decía «Dictar» con el micrófono grabando. Desde ahí cada pulsación
   hacía lo contrario de lo que parecía: la siguiente PARABA en vez de
   arrancar. Ninguna de las dos vueltas anteriores lo habría cazado, porque las
   dos miraban el TEXTO y esto es el ESTADO.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jsx_limpio  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOTOR = os.path.join(RAIZ, "frontend", "src", "dictado.js")
HOOK = os.path.join(RAIZ, "frontend", "src", "hooks", "useSpeechRecognition.js")

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="hace falta node para ejecutar el dictado")


def _leer(ruta=HOOK):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _en_node(cuerpo):
    """Ejecuta `cuerpo` con el módulo REAL importado y devuelve lo que imprima.

    Nada de copias: si `dictado.js` cambia, esto cambia con él."""
    guion = (
        f"import {{ unir, leerResultados, MotorDeDictado, hayQueRendirse, "
        f"mensajeDeError }} from {json.dumps(MOTOR)};\n"
        "const R = (t, f) => ({ 0: { transcript: t }, isFinal: f });\n"
        f"{cuerpo}\n"
    )
    r = subprocess.run(["node", "--input-type=module", "-e", guion],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node ha fallado:\n{r.stderr}"
    return json.loads(r.stdout.strip().splitlines()[-1])


# ─── 1. EL ESTADO DEL BOTÓN — el fallo del 09/09 ────────────────────────────

def test_un_no_speech_NO_apaga_el_boton():
    """CANDADO PRINCIPAL DE ESTA VUELTA.

    `no-speech` salta a los pocos segundos de silencio en Android: es el día a
    día, no una avería. Si apagara el botón, el usuario lo pulsaría creyendo
    que arranca cuando en realidad PARA."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        const err = m.alError('no-speech');
        const fin = m.alCerrarse();
        console.log(JSON.stringify({
          rendirse: err.rendirse, reanudar: fin.reanudar, escuchando: fin.escuchando,
        }));
    """)
    assert salida["rendirse"] is False, (
        "un `no-speech` rinde el dictado. En Android salta cada pocos segundos "
        "de silencio: el micro se apagaría solo a media frase.")
    assert salida["reanudar"] is True, (
        "tras un `no-speech` ya no se reanuda: el dictado se muere en el primer "
        "silencio")
    assert salida["escuchando"] is None, (
        "al reanudar se está decidiendo el estado del botón por adelantado. Eso "
        "es justo el fallo: lo tiene que decir `onstart`, cuando el micro esté "
        "abierto DE VERDAD.")


def test_quien_enciende_el_boton_es_el_NAVEGADOR():
    """`alArrancar` es lo que llama `onstart`. Sin ese camino, el botón se
    queda apagado con el micro grabando — que es lo que veía el master."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar();
        const antes = m.abierto;
        const r = m.alArrancar();
        console.log(JSON.stringify({ antes, escuchando: r.escuchando, abierto: m.abierto }));
    """)
    assert salida["antes"] is False, (
        "el motor da por abierto el micro antes de que el navegador lo diga")
    assert salida["escuchando"] is True and salida["abierto"] is True


def test_el_hook_CONECTA_onstart():
    """El motor puede estar perfecto: si nadie llama a `alArrancar`, el botón
    no se enciende nunca. La primera versión del hook no tenía `onstart`."""
    src = _leer()
    assert re.search(r"recognition\.onstart\s*=", src), (
        "el hook no conecta `onstart`: el botón nunca sabrá que el micro se ha "
        "abierto y se quedará diciendo «Dictar» mientras graba")
    i = src.index("recognition.onstart")
    assert "alArrancar" in src[i:i + 200], (
        "`onstart` ya no avisa al motor de que el micro está abierto")


def test_el_hook_NO_apaga_el_boton_dentro_de_onerror():
    """Ahí estaba el fallo, literal: `setIsListening(false)` ante cualquier
    error, y `onend` reabriendo el micro justo después."""
    src = _leer()
    i = src.index("recognition.onerror")
    cuerpo = src[i:src.index("recognition.onend", i)]
    assert "setIsListening" not in cuerpo, (
        "`onerror` vuelve a tocar el estado del botón. Un `no-speech` —normal "
        "en Android— lo apagaría mientras `onend` reabre el micro: el botón "
        "diría «Dictar» grabando, y la siguiente pulsación pararía en vez de "
        "arrancar.")


# ─── 2. REANUDAR DE VERDAD ──────────────────────────────────────────────────

def test_reanudar_no_es_en_el_mismo_instante():
    """`start()` dentro del propio `onend` lanza `InvalidStateError`: el
    reconocedor aún no se ha soltado. El `catch` de antes se lo tragaba y el
    dictado se moría en silencio."""
    src = _leer()
    i = src.index("recognition.onend")
    cuerpo = src[i:i + 400]
    assert "recognition.start()" not in cuerpo, (
        "se vuelve a llamar a `start()` dentro de `onend`: eso lanza "
        "InvalidStateError a menudo y el dictado muere sin decir nada")
    assert "setTimeout" in src, (
        "ya no se cede el turno al navegador antes de reabrir el micro")


def test_si_no_se_puede_reanudar_se_PARA_de_verdad():
    """Rendirse dejando el botón encendido sobre un micro que no graba es la
    misma mentira por el otro lado."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar(); m.alCerrarse();
        const r = m.alNoPoderReanudar();
        console.log(JSON.stringify({ escuchando: r.escuchando, quiere: m.quiereEscuchar }));
    """)
    assert salida["escuchando"] is False and salida["quiere"] is False, (
        "al no poder reabrir el micro, el botón se queda encendido sobre un "
        "micrófono que no graba")


def test_lo_dicho_SOBREVIVE_al_corte_de_android():
    """Android corta la sesión cada pocos segundos y `event.results` empieza de
    cero. Sin guardar lo anterior, cada corte borraría lo dicho."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        m.alResultado([R('el bajo fregadero de noventa', true)]);
        m.alCerrarse();                 // Android corta
        m.alArrancar();                 // y se reanuda
        const t = m.alResultado([R('con dos gavetas', true)]).texto;
        console.log(JSON.stringify({ texto: t }));
    """)
    assert salida["texto"] == "el bajo fregadero de noventa con dos gavetas", (
        f"el corte de Android se ha comido lo dicho: «{salida['texto']}»")


# ─── 3. EL TEXTO — las dos vueltas anteriores, ahora ejecutadas ─────────────

def test_los_provisionales_no_se_amontonan():
    """La secuencia que dio «elelelel bajoel bajoel bajo fre»."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        const pasos = [
          [R('el', false)], [R('el', false)], [R('el bajo', false)],
          [R('el bajo fre', false)], [R('el bajo fregadero', true)],
        ].map(e => m.alResultado(e).texto);
        console.log(JSON.stringify({ pasos }));
    """)
    pasos = salida["pasos"]
    assert pasos[-1] == "el bajo fregadero", f"sale «{pasos[-1]}»"
    for texto in pasos:
        assert "elel" not in texto.replace(" ", ""), (
            f"vuelve a amontonar los provisionales: «{texto}»")


def test_varios_provisionales_EN_EL_MISMO_evento_no_se_suman():
    """Chrome manda la lista ENTERA en cada evento, y ahí dentro puede haber
    más de un provisional. Con un solo provisional por evento, sumar y asignar
    dan lo mismo — por eso la prueba de arriba no basta: pasaba con el fallo
    puesto. Este es el caso que los separa."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        const t = m.alResultado([
          R('el bajo fregadero', true),
          R('de', false), R('de no', false), R('de noventa', false),
        ]).texto;
        console.log(JSON.stringify({ texto: t }));
    """)
    assert salida["texto"] == "el bajo fregadero de noventa", (
        f"se están sumando los provisionales del mismo evento: "
        f"«{salida['texto']}». Del provisional solo vale EL ÚLTIMO.")


def test_un_final_reentregado_no_se_duplica():
    """En Android el mismo final llega varias veces. Rehacerlo entero en cada
    evento lo hace inofensivo."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        const uno = [R('el bajo fregadero', true)];
        console.log(JSON.stringify({
          a: m.alResultado(uno).texto, b: m.alResultado(uno).texto,
          c: m.alResultado(uno).texto,
        }));
    """)
    assert salida["a"] == salida["b"] == salida["c"] == "el bajo fregadero"


def test_la_reentrega_no_se_amontona_TAMPOCO_al_cerrar_la_sesion():
    """El texto que se ENSEÑA puede estar bien y el guardado estar podrido.

    `alResultado` devuelve el texto calculado del evento, así que un `+=` sobre
    lo firme no se nota hasta que Android corta la sesión y lo guardado pasa a
    `previo`. Ahí es donde aparecía el «cuandocuandocuando» de julio."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        const uno = [R('el bajo fregadero', true)];
        m.alResultado(uno); m.alResultado(uno); m.alResultado(uno);
        m.alCerrarse();                       // Android corta
        console.log(JSON.stringify({ guardado: m.texto() }));
    """)
    assert salida["guardado"] == "el bajo fregadero", (
        f"lo guardado se ha triplicado: «{salida['guardado']}». En pantalla se "
        f"veía bien; el churro aparece al cortarse la sesión.")


def test_el_provisional_NO_se_guarda_al_cortarse_la_sesion():
    """Si Android corta con una palabra a medias, esa palabra a medias NO puede
    quedarse: el navegador la va a reentregar entera en la sesión siguiente y
    saldría dos veces, una de ellas partida."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        m.alResultado([R('el bajo', true), R('fregade', false)]);
        m.alCerrarse();                       // corta con el provisional vivo
        console.log(JSON.stringify({ guardado: m.texto() }));
    """)
    assert salida["guardado"] == "el bajo", (
        f"se ha guardado la palabra a medias: «{salida['guardado']}». Al "
        f"reanudar, el navegador la dirá entera y saldrá dos veces.")


def test_el_provisional_se_ve_pero_no_se_queda():
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        const viendo = m.alResultado([R('el bajo', true), R('fregade', false)]).texto;
        const final = m.alResultado([R('el bajo', true), R('fregadero', true)]).texto;
        console.log(JSON.stringify({ viendo, final }));
    """)
    assert salida["viendo"] == "el bajo fregade", (
        "el provisional ya no se enseña: sin verlo, el micro parece colgado")
    assert salida["final"] == "el bajo fregadero", (
        "el provisional se ha quedado pegado cuando llegó el final")


def test_sin_nada_dicho_no_revienta():
    salida = _en_node("""
        const m = new MotorDeDictado();
        console.log(JSON.stringify({
          vacio: m.alResultado([]).texto, nulo: m.alResultado(null).texto,
        }));
    """)
    assert salida["vacio"] == "" and salida["nulo"] == ""


# ─── 4. RENDIRSE, Y DECIRLO ─────────────────────────────────────────────────

def test_no_se_insiste_contra_un_permiso_denegado():
    """Reintentar en bucle no concede el permiso; solo gasta batería."""
    salida = _en_node("""
        const out = {};
        for (const e of ['not-allowed', 'service-not-allowed', 'audio-capture']) {
          const m = new MotorDeDictado();
          m.alPulsarDictar(); m.alArrancar();
          const r = m.alError(e);
          out[e] = { rendirse: r.rendirse, mensaje: r.mensaje,
                     reanudar: m.alCerrarse().reanudar };
        }
        console.log(JSON.stringify(out));
    """)
    for error, r in salida.items():
        assert r["rendirse"] is True, f"«{error}» ya no rinde el dictado"
        assert r["reanudar"] is False, (
            f"con «{error}» se sigue reintentando: no concede el permiso, solo "
            f"gasta batería")


def test_rendirse_SE_DICE_al_usuario():
    """Antes, quedarse sin permiso de micrófono no producía ni un aviso: el
    botón volvía a su sitio y el usuario hablaba contra una pantalla sorda."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        console.log(JSON.stringify({
          permiso: m.alError('not-allowed').mensaje,
          micro: new MotorDeDictado().alError('audio-capture').mensaje,
          normal: new MotorDeDictado().alError('no-speech').mensaje,
          // DIRECTO, sin pasar por `alError`: ahí el mensaje ni se pide cuando
          // el error no rinde, así que un texto puesto de más no se vería.
          directo: mensajeDeError('no-speech'),
        }));
    """)
    assert salida["permiso"], "sin permiso de micrófono no se avisa de nada"
    assert "micrófono" in salida["permiso"].lower(), (
        "el aviso no dice que el problema es el micrófono")
    assert salida["micro"], "sin micrófono no se avisa de nada"
    assert salida["normal"] == "" and salida["directo"] == "", (
        "un `no-speech` saca un aviso. Salta cada pocos segundos en Android: "
        "sería un aviso permanente por algo que no es un problema.")


def test_las_pantallas_ENSENIAN_el_aviso():
    """Un mensaje que no se pinta es un mensaje que no existe."""
    for nombre in ("AIRenderStudio.jsx", "Estudio3DLab.jsx"):
        ruta = os.path.join(RAIZ, "frontend", "src", "components", nombre)
        if not os.path.exists(ruta):
            continue
        src = _leer(ruta)
        assert "speechError" in src, (
            f"{nombre} no recoge el aviso del dictado: quedarse sin permiso de "
            f"micrófono no diría nada")
        assert re.search(r"if \(speechError\) setError\(speechError\)", src), (
            f"{nombre} recibe el aviso y no lo pinta")


# ─── 5. Que siga habiendo UN solo dictado, y ejecutable ─────────────────────

def test_parar_de_verdad_para():
    """Si `stop()` fuera antes de quitar la intención, el `onend` de después
    volvería a arrancarlo: el micro no se apagaría nunca."""
    salida = _en_node("""
        const m = new MotorDeDictado();
        m.alPulsarDictar(); m.alArrancar();
        m.alPulsarParar();
        console.log(JSON.stringify({ reanudar: m.alCerrarse().reanudar }));
    """)
    assert salida["reanudar"] is False, (
        "tras pedir parar, el cierre vuelve a reabrir el micro: no habría forma "
        "de apagarlo")
    src = _leer()
    i = src.index("const stopListening")
    cuerpo = src[i:i + 600]
    assert cuerpo.index("alPulsarParar") < cuerpo.index(".stop()"), (
        "se para el micro antes de quitar la intención de escuchar")


def test_la_logica_del_dictado_NO_vive_dentro_del_hook():
    """Si vuelve al hook, deja de poder ejecutarse en una prueba — y este
    fichero volvería a ser una copia hecha a mano que no protege de nada."""
    src = _leer()
    assert "from '../dictado'" in src, (
        "el hook ya no usa el módulo ejecutable: la lógica ha vuelto a un sitio "
        "donde solo se puede LEER, y así es como se coló el fallo del 09/09")
    assert "class MotorDeDictado" not in src, (
        "el motor se ha copiado dentro del hook: la copia se separará del "
        "original y el candado probará la que no corre")
    # SIN LOS COMENTARIOS. La primera versión miraba el fichero entero y se
    # ponía roja por su propia explicación, que dice «no depende de `window`».
    # Es la misma trampa de `test_pantalla_no_traducir.py` (regla 24): un
    # reconocedor que lee prosa no lee código.
    motor = jsx_limpio.sin_comentarios(_leer(MOTOR))
    assert "window" not in motor, (
        "`dictado.js` ha empezado a depender del navegador: deja de poder "
        "ejecutarse en el candado")
    # Y que el candado no pase por no encontrar nada: el fichero tiene que
    # seguir teniendo el motor dentro.
    assert "class MotorDeDictado" in motor, (
        "se está mirando un fichero que ya no trae el motor: la prueba pasaría "
        "por el motivo equivocado")


def test_el_hook_sigue_siendo_el_unico_sitio_con_dictado():
    """Estuvo copiado en dos pantallas y las dos arrastraban el mismo fallo."""
    comp = os.path.join(RAIZ, "frontend", "src", "components")
    malos = []
    for raiz, _, ficheros in os.walk(comp):
        for f in ficheros:
            if not f.endswith(".jsx"):
                continue
            src = _leer(os.path.join(raiz, f))
            if "webkitSpeechRecognition" in src and "useSpeechRecognition" not in src:
                malos.append(f)
    assert not malos, (
        "vuelven a montarse su propio dictado: " + ", ".join(malos)
        + ". El fallo se arregla en el hook o no se arregla.")
