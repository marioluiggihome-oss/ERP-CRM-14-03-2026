// © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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
export default function BotonPantallaCompleta({ className = '', mostrarTexto = true }) {
  const [activa, setActiva] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const raiz = document.documentElement;
    const soportado = Boolean(raiz.requestFullscreen || raiz.webkitRequestFullscreen);
    setVisible(soportado);

    const alCambiar = () => setActiva(
      Boolean(document.fullscreenElement || document.webkitFullscreenElement)
    );
    alCambiar();
    document.addEventListener('fullscreenchange', alCambiar);
    document.addEventListener('webkitfullscreenchange', alCambiar);
    return () => {
      document.removeEventListener('fullscreenchange', alCambiar);
      document.removeEventListener('webkitfullscreenchange', alCambiar);
    };
  }, []);

  const alternar = useCallback(async () => {
    try {
      if (document.fullscreenElement || document.webkitFullscreenElement) {
        if (document.exitFullscreen) await document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
        return;
      }
      const raiz = document.documentElement;
      if (raiz.requestFullscreen) await raiz.requestFullscreen({ navigationUI: 'hide' });
      else if (raiz.webkitRequestFullscreen) raiz.webkitRequestFullscreen();
    } catch (e) {
      // El navegador puede negarlo (iPhone no lo permite, o falta el gesto del
      // usuario). No es un fallo del ERP: se queda como está y no se avisa.
    }
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
        <span className="text-[7px] font-black uppercase tracking-widest">
          {activa ? 'Reducir' : 'Pantalla'}
        </span>
      )}
    </button>
  );
}
