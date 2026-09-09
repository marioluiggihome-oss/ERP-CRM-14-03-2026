/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */

/**
 * EL DICTADO, SIN NAVEGADOR — para poder EJECUTARLO en una prueba.
 *
 * Esto no es una refactorización de adorno. El candado del dictado
 * (`test_calculo_dictado_por_voz.py`) tenía la regla REESCRITA EN PYTHON y no
 * llamaba nunca al JavaScript de verdad: podía estar en verde con el dictado
 * roto, que es exactamente lo que pasó. Es el mismo fallo que costó una caída
 * en producción con la tarifa de ACB (CLAUDE.md, regla 31): «hay que EJECUTAR
 * el fichero, no solo leerlo».
 *
 * Aquí vive TODA la lógica del dictado y no depende de `window`. El hook
 * `useSpeechRecognition` se queda en lo que solo puede hacer el navegador:
 * abrir el micro y traer eventos. Así el candado conduce la sesión ENTERA
 * —hablar, que Android la corte, reanudar, errores, parar— con este mismo
 * código, no con una copia.
 *
 * ── EL FALLO QUE SE ARREGLA (09/09/2026) ────────────────────────────────────
 * El master: «el botón de dictar no dicta bien, no funciona bien».
 *
 * En Android, Chrome lanza `no-speech` a los pocos segundos de silencio — es
 * lo normal, no una avería. El hook hacía `setIsListening(false)` ante
 * CUALQUIER error, y justo después `onend` volvía a arrancar el micro y salía
 * con un `return` SIN reponer el estado. Resultado: **el botón decía «Dictar»
 * con el micrófono grabando**. Y como `onstart` no estaba conectado, no se
 * recuperaba nunca.
 *
 * A partir de ahí todo lo que hiciera el usuario estaba mal: lo pulsa creyendo
 * que arranca y en realidad PARA; lo vuelve a pulsar y arranca otra sesión
 * encima. Un botón que miente sobre su propio estado no se puede usar.
 *
 * LA REGLA: quien dice si el micro está abierto es el NAVEGADOR (`onstart` /
 * `onend`), nunca lo que nosotros creíamos que iba a pasar.
 */

/** Une dos tramos con UN solo espacio. */
export const unir = (a, b) => {
  const x = (a || '').trim();
  const y = (b || '').trim();
  if (!x) return y;
  if (!y) return x;
  return `${x} ${y}`;
};

/**
 * Convierte lo que manda el navegador en texto.
 *
 *   firme       — lo que ya da por bueno. Se rehace ENTERO en cada evento, así
 *                 que da igual cuántas veces reentregue lo mismo.
 *   provisional — lo que está oyendo AHORA. SOLO EL ÚLTIMO, jamás sumado:
 *                 sumarlos era lo que producía «elelelel bajoel bajoel bajo».
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

/**
 * ERRORES QUE PARAN DE VERDAD — y solo estos.
 *
 * Reintentar contra un permiso denegado no lo concede: solo calienta el móvil.
 * Pero al revés es peor: `no-speech` y `aborted` son el pan de cada día en
 * Android y tratarlos como avería es lo que apagaba el botón a media frase.
 * `network` tampoco para: se reintenta, que es lo que hace falta en una obra
 * con mala cobertura.
 */
export const ERRORES_QUE_PARAN = ['not-allowed', 'service-not-allowed', 'audio-capture'];

export const hayQueRendirse = (error) => ERRORES_QUE_PARAN.includes(String(error || ''));

/** Lo que se le dice al usuario cuando el dictado se rinde. Sin tecnicismos. */
export function mensajeDeError(error) {
  const e = String(error || '');
  if (e === 'not-allowed' || e === 'service-not-allowed') {
    return 'El navegador no deja usar el micrófono. Dale permiso en el candado de la barra de direcciones y vuelve a intentarlo.';
  }
  if (e === 'audio-capture') return 'No se encuentra el micrófono.';
  return '';
}

/**
 * EL MOTOR DEL DICTADO. Sin `window`, sin React: se puede ejecutar y probar.
 *
 * Guarda las dos mitades del texto que no puede llevar el navegador:
 *   previo  — lo dicho en sesiones YA CERRADAS. Android corta la sesión sola
 *             cada pocos segundos y entonces `event.results` empieza de cero;
 *             sin esto, cada corte borraría lo dicho.
 *   sesion  — lo FIRME de la sesión en curso.
 *
 * Cada método devuelve lo que el hook tiene que hacer, para que la decisión
 * esté aquí —donde se puede probar— y no repartida por los manejadores.
 */
export class MotorDeDictado {
  constructor() {
    this.previo = '';
    this.sesion = '';
    this.quiereEscuchar = false;
    this.abierto = false;      // lo que dice el NAVEGADOR, no lo que suponemos
    this.error = '';
  }

  /** El usuario pulsa Dictar. */
  alPulsarDictar() {
    this.previo = '';
    this.sesion = '';
    this.error = '';
    this.quiereEscuchar = true;
    return { arrancar: true };
  }

  /** El usuario pulsa para parar. */
  alPulsarParar() {
    // PRIMERO se quita la intención y luego se para: al revés, el `onend` de
    // después volvería a arrancarlo y el micro no se apagaría.
    this.quiereEscuchar = false;
    return { parar: true };
  }

  /** El NAVEGADOR dice que el micro está abierto. */
  alArrancar() {
    this.abierto = true;
    return { escuchando: true };
  }

  /** Llega texto. Devuelve lo que hay que enseñar. */
  alResultado(resultados) {
    const { firme, provisional } = leerResultados(resultados);
    this.sesion = firme;   // solo lo FIRME se guarda
    return { texto: unir(unir(this.previo, firme), provisional) };
  }

  /**
   * Un error. Solo unos pocos paran de verdad; el resto son el día a día de
   * Android y NO pueden apagar el botón, porque `onend` va a reanudar.
   */
  alError(error) {
    if (hayQueRendirse(error)) {
      this.quiereEscuchar = false;
      this.error = mensajeDeError(error);
    }
    // No se toca `abierto`: lo dirá `onend`. Suponerlo era el fallo.
    return { rendirse: !this.quiereEscuchar, mensaje: this.error };
  }

  /**
   * El navegador ha cerrado la sesión. O para de verdad, o hay que reanudar.
   *
   * `escuchando` NO se pone a true al reanudar: eso lo dirá `onstart` cuando el
   * micro esté abierto de verdad. Si `start()` fallara, el botón se quedaría
   * diciendo que escucha sin escuchar — el mismo fallo por el otro lado.
   */
  alCerrarse() {
    this.previo = unir(this.previo, this.sesion);
    this.sesion = '';
    this.abierto = false;
    if (this.quiereEscuchar) return { reanudar: true, escuchando: null };
    return { reanudar: false, escuchando: false };
  }

  /** No se ha podido reanudar (el navegador no ha dejado). Se para de verdad. */
  alNoPoderReanudar() {
    this.quiereEscuchar = false;
    return { escuchando: false };
  }

  /** Todo lo dicho hasta ahora, cerrado. */
  texto() {
    return unir(this.previo, this.sesion);
  }

  limpiar() {
    this.previo = '';
    this.sesion = '';
    this.error = '';
  }
}
