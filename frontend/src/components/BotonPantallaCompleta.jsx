// © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
// Software propietario y confidencial. Ver LICENSE.
// Prohibida su copia, distribución, modificación o uso sin autorización
// escrita del titular.
import React, { useCallback, useEffect, useState } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';

/**
 * El F11 del portátil, pero para tablet y móvil.
 *
 * En una tablet de 8" el navegador se queda con la barra de pestañas y la de
 * direcciones: unos 150 px de alto, casi un quinto de la pantalla, en el
 * dispositivo que MENOS alto tiene. Esto lo recupera.
 *
 * Lo definitivo es instalar el ERP en la pantalla de inicio (manifest.json con
 * display: standalone): así abre sin barras y no hay que acordarse de nada. Este
 * botón es para quien no lo tiene instalado. Por eso, si ya se está ejecutando
 * como app instalada, el botón NO se pinta: no hay ninguna barra que quitar y
 * sería un botón que no hace nada.
 */
export default function BotonPantallaCompleta({ className = '', mostrarTexto = true }) {
  const [activa, setActiva] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const raiz = document.documentElement;
    const soportado = Boolean(raiz.requestFullscreen || raiz.webkitRequestFullscreen);
    // Instalada en la pantalla de inicio ya no hay barras que ocultar.
    const comoApp = Boolean(
      window.matchMedia && window.matchMedia('(display-mode: standalone)').matches
    ) || window.navigator.standalone === true;
    setVisible(soportado && !comoApp);

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
        <span className="text-[7px] font-black uppercase tracking-widest">
          {activa ? 'Salir' : 'Pantalla'}
        </span>
      )}
    </button>
  );
}
