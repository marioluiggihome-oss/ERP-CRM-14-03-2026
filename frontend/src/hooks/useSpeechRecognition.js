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

export default function useSpeechRecognition({ lang = 'es-ES' } = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef(null);
  const previoRef = useRef('');   // lo dicho en sesiones ya cerradas
  const sesionRef = useRef('');   // lo dicho en la sesión en curso

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return undefined;

    setIsSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onresult = (event) => {
      // Se rehace el texto COMPLETO desde el principio de la sesión. Nada de
      // ir sumando: es lo que hacía que una palabra reentregada se duplicara.
      let texto = '';
      for (let i = 0; i < event.results.length; i++) {
        texto += event.results[i][0].transcript;
      }
      sesionRef.current = texto;
      setTranscript(unir(previoRef.current, texto));
    };

    recognition.onerror = () => setIsListening(false);

    recognition.onend = () => {
      // La sesión se cierra (el usuario para, o Android la corta solo): lo
      // dicho pasa a ser definitivo para que la siguiente no lo pise.
      previoRef.current = unir(previoRef.current, sesionRef.current);
      sesionRef.current = '';
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    return () => { try { recognition.abort(); } catch (_) { /* ya parado */ } };
  }, [lang]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    previoRef.current = '';
    sesionRef.current = '';
    setTranscript('');
    try { recognitionRef.current.start(); } catch (_) { /* ya estaba escuchando */ }
    setIsListening(true);
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
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
