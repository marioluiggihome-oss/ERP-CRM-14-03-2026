/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * useSpeechRecognition — dictado por voz (Web Speech API del navegador).
 *
 * ÚNICO sitio donde vive este hook. Estaba copiado en AIRenderStudio y en
 * EstudioCocinas, y los dos arrastraban el mismo fallo: al dictar salía
 * «cuandocuandocuandocuando dicto» en vez de «cuando dicto».
 *
 * POR QUÉ PASABA. La versión anterior iba SUMANDO trozos:
 *
 *     for (let i = event.resultIndex; i < event.results.length; i++)
 *         if (result.isFinal) finalRef.current += result[0].transcript;
 *
 * Eso da por hecho que cada resultado final llega EXACTAMENTE UNA VEZ. En
 * Chrome de Android no se cumple: con `continuous` los resultados se
 * reentregan y `resultIndex` no es de fiar, así que la misma palabra se sumaba
 * en cada evento y el texto crecía en progresión.
 *
 * CÓMO SE ARREGLA. No se suman trozos: en cada evento se REHACE el texto
 * entero leyendo `event.results` de principio a fin. Así la operación es
 * idempotente — que el navegador entregue el mismo resultado dos, tres o diez
 * veces da igual, porque el resultado es el mismo. Se ataca la causa (depender
 * de que no haya repeticiones) en vez de intentar detectarlas.
 *
 * Lo único que sí hay que acumular entre SESIONES: `continuous` se corta solo
 * cada pocos segundos en Android. Cuando eso pasa, `event.results` empieza de
 * cero, así que lo dicho hasta ahí se guarda en `previoRef` al cerrarse la
 * sesión y se antepone a lo siguiente. Si no, cada corte borraría lo dicho.
 *
 * ─────────────────────────────────────────────────────────────────────────
 * SEGUNDA VUELTA (09/08). Seguía saliendo mal en la tablet:
 *
 *     «elelelel bajoel bajoel bajoel bajo fre»
 *
 * Lo de arriba arreglaba una cosa y dejaba otra viva. Rehacer el texto desde
 * `event.results` es correcto SOLO si se leen los resultados FINALES. Los
 * PROVISIONALES son otra cosa: son el navegador pensando en voz alta, y va
 * mandando la frase a medias una y otra vez —«el», «el bajo», «el bajo fre»—.
 * Sumarlos todos da exactamente ese churro: cada versión intermedia pegada
 * detrás de la anterior.
 *
 * La regla, ahora sí:
 *
 *   · LOS FINALES SE SUMAN (rehaciéndolos enteros cada vez: sigue siendo
 *     idempotente, que era lo bueno de la primera vuelta).
 *   · DEL PROVISIONAL SOLO VALE EL ÚLTIMO, y no se suma NUNCA: se enseña
 *     detrás para que se vea que el micro está oyendo, y en cuanto llega el
 *     final se sustituye por él.
 *
 * Y una cosa más que no era un fallo pero lo parecía: en Android el dictado se
 * corta solo cada pocos segundos. Antes eso paraba el micro y había que volver
 * a tocarlo a media frase. Ahora, mientras el usuario no diga que para, se
 * vuelve a arrancar solo y lo dicho se conserva.
 */
import { useState, useRef, useCallback, useEffect } from 'react';

// Une dos tramos con UN solo espacio. La versión anterior concatenaba a pelo y
// por eso salía todo pegado además de repetido.
const unir = (a, b) => {
  const x = (a || '').trim();
  const y = (b || '').trim();
  if (!x) return y;
  if (!y) return x;
  return `${x} ${y}`;
};

/**
 * Convierte lo que manda el navegador en texto. Es la regla entera, aparte para
 * poder mirarla sin tener que leer el hook.
 *
 * Devuelve { firme, provisional }:
 *   firme       — lo que el navegador ya da por bueno. Se rehace ENTERO en cada
 *                 evento, así que da igual cuántas veces reentregue lo mismo.
 *   provisional — lo que está oyendo ahora mismo. SOLO EL ÚLTIMO, y no se suma
 *                 jamás: sumarlos era lo que producía «elelelel bajoel bajoel».
 */
export function leerResultados(resultados) {
  let firme = '';
  let provisional = '';
  for (let i = 0; i < (resultados?.length || 0); i++) {
    const r = resultados[i];
    const texto = r?.[0]?.transcript || '';
    if (r?.isFinal) firme = unir(firme, texto);
    else provisional = texto;   // asignación, NUNCA suma
  }
  return { firme, provisional };
}

export default function useSpeechRecognition({ lang = 'es-ES' } = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef(null);
  const previoRef = useRef('');   // lo dicho en sesiones ya cerradas
  const sesionRef = useRef('');   // lo FIRME de la sesión en curso
  // ¿El usuario sigue queriendo dictar? Android corta la sesión solo cada pocos
  // segundos; mientras esto sea true, se vuelve a arrancar sin que él lo note.
  const quiereEscuchar = useRef(false);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return undefined;

    setIsSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onresult = (event) => {
      const { firme, provisional } = leerResultados(event.results);
      // Solo lo FIRME se guarda. Lo provisional se enseña, pero no se queda:
      // en cuanto el navegador se decida, llegará como firme.
      sesionRef.current = firme;
      setTranscript(unir(unir(previoRef.current, firme), provisional));
    };

    recognition.onerror = (e) => {
      // Si es que no hay permiso o no hay micro, no se insiste: reintentar en
      // bucle contra un permiso denegado no lo concede, solo calienta el móvil.
      if (e?.error === 'not-allowed' || e?.error === 'service-not-allowed'
          || e?.error === 'audio-capture') {
        quiereEscuchar.current = false;
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      // La sesión se cierra (el usuario para, o Android la corta solo): lo
      // FIRME pasa a ser definitivo para que la siguiente no lo pise.
      previoRef.current = unir(previoRef.current, sesionRef.current);
      sesionRef.current = '';
      if (quiereEscuchar.current) {
        // Android corta cada pocos segundos. Se vuelve a abrir enseguida: antes
        // esto dejaba el micro parado a media frase y había que tocarlo otra vez.
        try { recognition.start(); return; } catch (_) { /* no ha dejado */ }
      }
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    return () => {
      quiereEscuchar.current = false;   // si no, el `onend` del cierre lo revive
      try { recognition.abort(); } catch (_) { /* ya parado */ }
    };
  }, [lang]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    previoRef.current = '';
    sesionRef.current = '';
    quiereEscuchar.current = true;
    setTranscript('');
    try { recognitionRef.current.start(); } catch (_) { /* ya estaba escuchando */ }
    setIsListening(true);
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    // PRIMERO se quita la intención y luego se para: al revés, el `onend` que
    // llega justo después volvería a arrancarlo y el micro no se apagaría.
    quiereEscuchar.current = false;
    try { recognitionRef.current.stop(); } catch (_) { /* ya estaba parado */ }
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    previoRef.current = '';
    sesionRef.current = '';
    setTranscript('');
  }, []);

  return { isListening, transcript, isSupported, startListening, stopListening, resetTranscript, setTranscript };
}
