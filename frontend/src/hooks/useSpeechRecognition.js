/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * useSpeechRecognition — dictado por voz (Web Speech API del navegador).
 *
 * ÚNICO sitio donde vive el dictado. Estuvo copiado en AIRenderStudio y en
 * EstudioCocinas, y las dos copias arrastraban el mismo fallo.
 *
 * LA LÓGICA NO ESTÁ AQUÍ: está en `frontend/src/dictado.js`, que no depende de
 * `window` y por eso se puede EJECUTAR en el candado. Aquí queda solo lo que
 * únicamente puede hacer el navegador — abrir el micro y traer eventos.
 * Léete la cabecera de aquel fichero: ahí está por qué el dictado se rompía y
 * por qué el candado no lo veía.
 *
 * ── TRES VUELTAS, Y LA TERCERA ES LA QUE IMPORTA ────────────────────────────
 *
 * 1ª (jul.) «cuandocuandocuando dicto»: se SUMABAN los trozos dando por hecho
 *    que cada final llega una sola vez. Se arregló rehaciendo el texto entero
 *    en cada evento — idempotente, da igual cuántas veces reentregue Android.
 *
 * 2ª (09/08) «elelelel bajoel bajoel bajo fre»: rehacerlo entero vale para los
 *    FINALES, pero los PROVISIONALES son el navegador pensando en voz alta y
 *    manda la frase a medias una y otra vez. Del provisional solo vale EL
 *    ÚLTIMO, y no se suma nunca.
 *
 * 3ª (09/09) EL BOTÓN MENTÍA SOBRE SÍ MISMO, que es lo que el master notaba
 *    como «no funciona bien». En Android, Chrome lanza `no-speech` a los pocos
 *    segundos de silencio: es lo normal. El hook hacía `setIsListening(false)`
 *    ante CUALQUIER error y, acto seguido, `onend` reabría el micro y salía con
 *    un `return` sin reponer el estado. El botón decía «Dictar» con el micro
 *    grabando — y `onstart` no estaba conectado, así que no se recuperaba.
 *    Desde ahí, cada pulsación hacía lo contrario de lo que parecía.
 *
 *    Ahora quien dice si el micro está abierto es el NAVEGADOR (`onstart` /
 *    `onend`), nunca lo que nosotros creíamos que iba a pasar.
 *
 * Y DOS COSAS MÁS DE LA TERCERA VUELTA:
 *
 *  · REANUDAR NO PUEDE SER EN EL MISMO INSTANTE. Llamar a `start()` dentro del
 *    propio `onend` lanza `InvalidStateError` a menudo: el reconocedor aún no
 *    se ha soltado. Aquel `catch` se lo tragaba y el dictado se moría en
 *    silencio a media frase. Se reanuda en el tick siguiente y, si tampoco
 *    puede, se reintenta UNA vez más antes de rendirse.
 *  · RENDIRSE SE DICE. Antes, quedarse sin permiso de micrófono no producía ni
 *    un aviso: el botón volvía a su sitio y el usuario hablaba contra una
 *    pantalla que no le oía.
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { MotorDeDictado } from '../dictado';

// Cuánto se espera para reabrir el micro cuando Android corta la sesión. No es
// un número mágico: hace falta CEDER EL TURNO al navegador para que suelte el
// reconocedor. Con 0 ya vale; 250 ms es el segundo intento, más holgado.
const REANUDAR_MS = 0;
const REANUDAR_MS_REINTENTO = 250;

export { leerResultados, unir } from '../dictado';

export default function useSpeechRecognition({ lang = 'es-ES' } = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const [speechError, setSpeechError] = useState('');

  const recognitionRef = useRef(null);
  const motorRef = useRef(null);
  if (!motorRef.current) motorRef.current = new MotorDeDictado();
  const temporizadorRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return undefined;

    setIsSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    const motor = motorRef.current;

    // Reabrir el micro cediendo antes el turno al navegador, con UN reintento.
    // Si ninguno entra, se para de verdad en vez de dejar el botón encendido
    // sobre un micrófono que ya no graba.
    const reanudar = (espera = REANUDAR_MS, segundoIntento = false) => {
      clearTimeout(temporizadorRef.current);
      temporizadorRef.current = setTimeout(() => {
        if (!motor.quiereEscuchar) return;
        try {
          recognition.start();
        } catch (_) {
          if (!segundoIntento) { reanudar(REANUDAR_MS_REINTENTO, true); return; }
          setIsListening(motor.alNoPoderReanudar().escuchando);
        }
      }, espera);
    };

    // EL NAVEGADOR manda sobre el estado del botón.
    recognition.onstart = () => setIsListening(motor.alArrancar().escuchando);

    recognition.onresult = (event) => {
      setTranscript(motor.alResultado(event.results).texto);
    };

    recognition.onerror = (e) => {
      const { rendirse, mensaje } = motor.alError(e?.error);
      if (mensaje) setSpeechError(mensaje);
      // NO se toca `isListening` aquí: lo dirá `onend`. Suponerlo era el fallo
      // que apagaba el botón con el micro grabando.
      if (rendirse) {
        try { recognition.stop(); } catch (_) { /* ya parado */ }
      }
    };

    recognition.onend = () => {
      const { reanudar: hayQueReanudar, escuchando } = motor.alCerrarse();
      if (hayQueReanudar) { reanudar(); return; }
      setIsListening(escuchando);
    };

    recognitionRef.current = recognition;
    return () => {
      motor.quiereEscuchar = false;   // si no, el `onend` del cierre lo revive
      clearTimeout(temporizadorRef.current);
      try { recognition.abort(); } catch (_) { /* ya parado */ }
    };
  }, [lang]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    motorRef.current.alPulsarDictar();
    setTranscript('');
    setSpeechError('');
    // NO se pone `isListening` a true aquí: lo pone `onstart` cuando el micro
    // esté abierto de verdad. Si `start()` fallara, el botón diría que escucha
    // sin escuchar — el mismo fallo del revés.
    try { recognitionRef.current.start(); } catch (_) { /* ya estaba escuchando */ }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    motorRef.current.alPulsarParar();
    clearTimeout(temporizadorRef.current);
    try { recognitionRef.current.stop(); } catch (_) { /* ya estaba parado */ }
    // Aquí sí se apaga en el acto: el usuario ha pedido parar y la pantalla
    // tiene que responderle ya, aunque el `onend` tarde un instante en llegar.
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    motorRef.current.limpiar();
    setTranscript('');
    setSpeechError('');
  }, []);

  return {
    isListening, transcript, isSupported, speechError,
    startListening, stopListening, resetTranscript, setTranscript,
  };
}
