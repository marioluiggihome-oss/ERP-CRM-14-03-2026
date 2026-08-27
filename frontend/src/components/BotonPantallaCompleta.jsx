// © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
// Software propietario y confidencial. Ver LICENSE.
// Prohibida su copia, distribución, modificación o uso sin autorización
// escrita del titular.
import React, { useCallback, useEffect, useState } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';

/**
 * El F11 del portátil, en cualquier sitio y para cualquiera.
 *
 * En una tablet de 8" el navegador se queda con la barra de pestañas y la de
 * direcciones: unos 150 px de alto, casi un quinto de la pantalla, en el
 * dispositivo que MENOS alto tiene. En el ordenador recupera la barra de
 * pestañas y la de marcadores. Esto lo quita todo.
 *
 * ANTES SE ESCONDÍA SOLO cuando el ERP estaba instalado en la pantalla de
 * inicio, con el razonamiento de que ahí ya no hay barras que ocultar. Se ha
 * quitado esa condición: aun instalado, la pantalla completa se lleva también
 * la barra de estado del sistema, y sobre todo el botón desaparecía sin que
 * nadie entendiera por qué —el master lo pidió "en todos los usuarios, PC,
 * móvil o tablet", y un botón que a veces está y a veces no es peor que uno
 * que no hace nada—.
 *
 * Solo queda una razón para no pintarlo: que el navegador NO sepa hacerlo
 * (Safari de iPhone, por ejemplo, no lo permite). Ahí no es que sobre: es que
 * pulsarlo no haría nada.
 */
/** ¿Estamos en pantalla completa DE VERDAD, ahora mismo? Se pregunta al DOM. */
const enPantallaCompleta = () =>
  Boolean(document.fullscreenElement || document.webkitFullscreenElement);

/**
 * `claseTexto` y `textos` existen porque este botón vive en dos sitios con
 * tipografías muy distintas: el carril de la izquierda, donde el rótulo es de
 * 7 px en mayúsculas debajo del icono, y la barra del render del Estudio 3D,
 * donde va al lado y a 11 px. Sin esto, el del Estudio 3D salía con la letra
 * del carril —«Pantalla» en microscópico— y parecía otra cosa.
 */
export default function BotonPantallaCompleta({
  className = '',
  mostrarTexto = true,
  claseTexto = 'text-[7px] font-black uppercase tracking-widest',
  textos = { dentro: 'Reducir', fuera: 'Pantalla' },
}) {
  const [activa, setActiva] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const raiz = document.documentElement;
    const soportado = Boolean(raiz.requestFullscreen || raiz.webkitRequestFullscreen);
    setVisible(soportado);

    const alCambiar = () => setActiva(enPantallaCompleta());
    alCambiar();
    document.addEventListener('fullscreenchange', alCambiar);
    document.addEventListener('webkitfullscreenchange', alCambiar);
    // ADEMÁS de los eventos de pantalla completa. En Android, salir con el
    // gesto de volver no siempre dispara `fullscreenchange`: el botón se
    // quedaba diciendo «Reducir» para siempre. Estos dos SÍ llegan, y con ellos
    // el estado se vuelve a sincronizar solo.
    window.addEventListener('resize', alCambiar);
    document.addEventListener('visibilitychange', alCambiar);
    return () => {
      document.removeEventListener('fullscreenchange', alCambiar);
      document.removeEventListener('webkitfullscreenchange', alCambiar);
      window.removeEventListener('resize', alCambiar);
      document.removeEventListener('visibilitychange', alCambiar);
    };
  }, []);

  const alternar = useCallback(async () => {
    // SE MIRA EL ESTADO DE VERDAD, no lo que creíamos tener. Y pase lo que
    // pase, el botón acaba sincronizado: aquí es donde se quedaba pillado.
    //
    // Si el navegador había salido de pantalla completa por su cuenta y no
    // avisó, `activa` seguía en true, se llamaba a `exitFullscreen` sobre un
    // documento que ya no estaba en pantalla completa, la promesa fallaba, el
    // error se tragaba en silencio y el botón no volvía a funcionar NUNCA. Un
    // botón muerto que además sigue diciendo «Reducir».
    const raiz = document.documentElement;
    let dentro = enPantallaCompleta();
    try {
      if (dentro) {
        if (document.exitFullscreen) await document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
      } else if (raiz.requestFullscreen) {
        await raiz.requestFullscreen({ navigationUI: 'hide' });
      } else if (raiz.webkitRequestFullscreen) {
        raiz.webkitRequestFullscreen();
      }
    } catch (e) {
      // El navegador puede negarlo (iPhone no lo permite, o falta el gesto del
      // usuario). No es un fallo del ERP: se sincroniza y se sigue.
    }
    // Se relee del DOM, no se da por hecho. Si el evento llega, mejor; si no
    // llega —que es el caso que rompía esto—, el botón queda igualmente bien.
    setActiva(enPantallaCompleta());
    setTimeout(() => setActiva(enPantallaCompleta()), 250);
  }, []);

  if (!visible) return null;

  return (
    <button
      type="button"
      onClick={alternar}
      className={className || 'flex flex-col items-center gap-1 p-2 rounded-xl text-slate-500 hover:text-white hover:bg-white/10 transition-colors duration-200'}
      aria-label={activa ? 'Salir de pantalla completa' : 'Pantalla completa'}
      title={activa ? 'Salir de pantalla completa' : 'Pantalla completa (oculta las barras del navegador)'}
      data-testid="toggle-pantalla-completa"
    >
      {activa ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
      {mostrarTexto && (
        /* «Reducir», NO «Salir»: justo debajo, en la misma columna, está el
           botón de cerrar sesión, que también dice «Salir». Dos botones
           pegados con la misma palabra y distinto efecto es una trampa. */
        <span className={claseTexto}>
          {activa ? textos.dentro : textos.fuera}
        </span>
      )}
    </button>
  );
}
