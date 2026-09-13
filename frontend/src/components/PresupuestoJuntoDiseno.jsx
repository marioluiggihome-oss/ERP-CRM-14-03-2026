/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE. */
import React, { useEffect, useRef, useState, Suspense } from 'react';
import { createPortal } from 'react-dom';
const CocinaMontada3 = React.lazy(() => import('./CocinaMontada3'));

// El mismo presupuestador y sus permisos, sin duplicar tarifas ni cálculos.
// Mover el contenedor del portal conserva el borrador al abrir/cerrar la ventana.
export default function PresupuestoJuntoDiseno({ abierto, onClose, imagen, state, entrada, cliente, referencia }) {
  const [datos, setDatos] = useState({ currentUser: state?.currentUser });
  const [ampliado, setAmpliado] = useState(false);
  const [separado, setSeparado] = useState(false);
  const [aviso, setAviso] = useState('');
  const [contenedor] = useState(() => document.createElement('div'));
  const host = useRef(null);
  const ventana = useRef(null);
  const ultimaEntrada = useRef(null);
  useEffect(() => {
    contenedor.className = 'min-h-full bg-white';
    host.current?.appendChild(contenedor);
    return () => { ventana.current?.close(); contenedor.remove(); };
  }, [contenedor]);
  useEffect(() => {
    if (entrada && entrada !== ultimaEntrada.current) {
      ultimaEntrada.current = entrada;
      setDatos(p => ({ ...p, revisionTecnicaOrigen: null, ...entrada }));
    }
  }, [entrada]);
  const volver = () => {
    host.current?.appendChild(contenedor);
    ventana.current = null;
    setSeparado(false);
  };
  const abrirVentana = () => {
    if (ventana.current && !ventana.current.closed) { ventana.current.focus(); return; }
    const nueva = window.open('', '', 'popup,width=1280,height=900');
    if (!nueva) {
      setAmpliado(true);
      setAviso('El navegador bloqueó la ventana. El presupuesto se ha ampliado aquí.');
      return;
    }
    nueva.document.title = 'Presupuesto · Estudio 3D';
    document.querySelectorAll('link[rel="stylesheet"], style').forEach(el => {
      nueva.document.head.appendChild(el.cloneNode(true));
    });
    nueva.document.body.style.margin = '0';
    nueva.document.body.appendChild(contenedor);
    nueva.addEventListener('beforeunload', volver, { once: true });
    ventana.current = nueva;
    setSeparado(true);
    nueva.focus();
  };
  return (
    <section hidden={!abierto} className="fixed inset-0 z-[150] bg-slate-100 flex flex-col" aria-label="Diseño y presupuesto" style={!abierto ? { display: 'none' } : undefined}>
      <header className="flex flex-wrap gap-2 items-center p-3 bg-white border-b">
        <strong className="mr-auto">Diseño y presupuesto</strong>
        <button className="border rounded-lg px-3 py-2" onClick={() => setAmpliado(v => !v)}>{ampliado ? 'Ver junto al diseño' : 'Ampliar presupuesto'}</button>
        <button className="border rounded-lg px-3 py-2" onClick={abrirVentana}>Abrir en otra ventana</button>
        <button className="border rounded-lg px-3 py-2" onClick={() => { ventana.current?.close(); onClose(); }}>Volver al estudio</button>
      </header>
      {aviso && <p role="status" className="p-2 text-sm">{aviso}</p>}
      {(entrada?.avisosMV?.length > 0 || entrada?.familiasPorRevisar?.length > 0) && <details className="p-3 bg-amber-50 border-b text-sm" open>
        <summary className="font-bold">Presupuesto provisional: hay elementos por revisar</summary>
        {entrada.avisosMV?.map((a, i) => <p key={i}>{a}</p>)}
        {entrada.familiasPorRevisar?.length > 0 && <p>Confirmar familia: {entrada.familiasPorRevisar.join(', ')}.</p>}
      </details>}
      <div className={`flex-1 min-h-0 grid ${ampliado ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]'} overflow-auto`}>
        {!ampliado && <aside className="bg-slate-900 flex flex-col items-center justify-center p-3 min-h-48">
          {imagen ? <img src={imagen} alt="Diseño de referencia del presupuesto" className="max-w-full max-h-[75vh] object-contain" /> : <p className="text-white">Relación de muebles del proyecto</p>}
          <p className="text-xs text-slate-300 mt-3">Referencia al volcar. Revisa los muebles antes de incorporarlos y guarda el presupuesto antes de salir del estudio.</p>
        </aside>}
        <div className="min-w-0 overflow-auto bg-white">
          {separado && <p className="p-4">Presupuesto abierto en otra ventana. Al cerrarla volverá aquí con tus cambios.</p>}
          <div ref={host} />
        </div>
      </div>
      {createPortal(<Suspense fallback={<p className="p-4">Cargando presupuesto…</p>}>
        {entrada?.revisionTecnicaOrigen && <p className="p-3 bg-indigo-50 text-sm">Origen: revisión técnica {entrada.revisionTecnicaOrigen.revision.slice(0, 12)}. Las modificaciones realizadas en este presupuesto requieren una nueva revisión del diseño.</p>}
        <CocinaMontada3 currentUser={state?.currentUser} state={{ ...datos, currentUser: state?.currentUser }} setState={setDatos} logo={state?.logo} clienteInicial={cliente} referenciaInicial={referencia} />
      </Suspense>, contenedor)}
    </section>
  );
}
