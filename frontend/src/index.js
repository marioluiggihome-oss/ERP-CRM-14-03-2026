/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import "@/services/authFetch"; // instala el interceptor de fetch (adjunta el JWT) antes de montar la app
import App from "@/App";

// En producción, silenciar logs informativos para no filtrar datos de negocio por consola.
// Se mantienen console.warn y console.error para diagnóstico de problemas reales.
if (process.env.NODE_ENV === 'production') {
  const noop = () => {};
  console.log = noop;
  console.info = noop;
  console.debug = noop;
}

// ── Auto-recarga ante fallo de carga de "chunk" tras un deploy ────────────────
// Al desplegar una versión nueva, el navegador puede tener cacheada la página
// vieja y fallar al pedir un trozo de código que ya cambió de nombre
// (ChunkLoadError / "Loading chunk failed" / "dynamically imported module").
// Recargamos UNA vez para traer la versión nueva; si tras recargar sigue
// fallando, no reintentamos (evita bucle). Al cargar bien se limpia el flag.
const CHUNK_RELOAD_KEY = 'luiggi-chunk-reload';
const isChunkError = (msg) => /Loading chunk [\w]+ failed|ChunkLoadError|Loading CSS chunk|Failed to fetch dynamically imported module|error loading dynamically imported module|importing a module script failed/i.test(String(msg || ''));
const tryChunkReload = (msg) => {
  if (!isChunkError(msg)) return;
  try {
    if (!sessionStorage.getItem(CHUNK_RELOAD_KEY)) {
      sessionStorage.setItem(CHUNK_RELOAD_KEY, '1');
      window.location.reload();
    }
  } catch (_) { window.location.reload(); }
};
window.addEventListener('error', (e) => tryChunkReload(e?.message || e?.error?.message));
window.addEventListener('unhandledrejection', (e) => tryChunkReload(e?.reason?.message || e?.reason));
window.addEventListener('load', () => { setTimeout(() => { try { sessionStorage.removeItem(CHUNK_RELOAD_KEY); } catch (_) {} }, 5000); });

// Clean the root element before mounting
const rootElement = document.getElementById("root");
if (rootElement) {
  while (rootElement.firstChild) {
    rootElement.removeChild(rootElement.firstChild);
  }
}

// Error Boundary mejorado - intenta auto-recargar 1 vez antes de mostrar el error visible
const AUTO_RELOAD_KEY = 'luiggi-err-reload';

class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null, errorInfo: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('React Error:', error, info);
    this.setState({ errorInfo: info });

    // Un fallo de carga de chunk (bundle desfasado tras deploy) SIEMPRE se
    // recarga una vez, con su propio flag, sin quedar bloqueado por otros errores.
    const msg = error?.message || String(error || '');
    if (isChunkError(msg)) { tryChunkReload(msg); return; }

    // LOS DEMÁS ERRORES NO SE AUTO-RECARGAN.
    //
    // Aquí había una recarga automática a los 0,8 s. La idea era buena para un
    // bundle desfasado —y ese caso sigue cubierto arriba, con `isChunkError`—,
    // pero para un fallo de verdad hacía dos cosas malas:
    //
    //  · Se llevaba por delante la pantalla del error antes de que nadie
    //    pudiera leerla. El master, literalmente: «no me das tiempo de copiar
    //    los detalles técnicos del error». Sin traza, un fallo se reporta como
    //    «da fallo» y hay que buscarlo a ciegas.
    //  · Y recargar no arregla un error de programación: vuelve a salir en
    //    cuanto se repite el gesto. Lo único que consigue es esconderlo.
    //
    // Un fallo se queda en pantalla hasta que alguien lo lee y decide.
  }

  handleManualReload = () => {
    try { sessionStorage.removeItem(AUTO_RELOAD_KEY); } catch {}
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const errMsg = this.state.error?.message || String(this.state.error || 'Error desconocido');
      // EL DETALLE TIENE QUE DECIR DÓNDE, NO SOLO QUÉ.
      //
      // Antes solo se pintaba `error.message`, así que un fallo llegaba
      // reportado como «da fallo» y había que adivinar la pantalla. Con la PILA
      // DE COMPONENTES, el mismo pantallazo ya dice en qué componente ha
      // reventado, que es la mitad del trabajo de arreglarlo.
      const pila = (this.state.errorInfo?.componentStack || '')
        .split('\n').filter(Boolean).slice(0, 12).join('\n');
      const detalle = [
        errMsg,
        this.state.error?.stack ? `\n${String(this.state.error.stack).split('\n').slice(0, 6).join('\n')}` : '',
        pila ? `\nDónde:${pila}` : '',
        `\n${window.location.pathname}${window.location.hash || ''}`,
      ].filter(Boolean).join('\n');
      return (
        <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', background: '#111726', minHeight: '100vh', color: 'white' }}>
          <div style={{ maxWidth: 560, margin: '40px auto', background: '#212937', borderRadius: 16, padding: 24, border: '1px solid #364150' }}>
            <h1 style={{ color: '#d08e6c', marginBottom: 12, fontSize: 22 }}>⚠️ Algo ha fallado</h1>
            <p style={{ marginBottom: 16, color: '#cdd5de', fontSize: 14 }}>
              La aplicación ha encontrado un error inesperado.
            </p>
            <details style={{ background: '#111726', padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 12, color: '#97a3b2' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Ver detalles técnicos</summary>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: 8 }}>{detalle}</pre>
              {/* Para poder MANDARLO en vez de transcribirlo a mano desde una
                  pantalla de móvil. */}
              <button
                onClick={() => { try { navigator.clipboard.writeText(detalle); } catch { /* noop */ } }}
                style={{ marginTop: 10, background: '#364150', color: 'white', border: 'none', padding: '8px 14px', borderRadius: 6, fontWeight: 'bold', cursor: 'pointer', fontSize: 12 }}
              >
                Copiar detalle
              </button>
            </details>
            <button
              onClick={this.handleManualReload}
              style={{ background: '#75b882', color: 'white', border: 'none', padding: '12px 24px', borderRadius: 8, fontWeight: 'bold', cursor: 'pointer', fontSize: 15, marginRight: 10 }}
            >
              🔄 Recargar
            </button>
            <button
              onClick={() => { try { localStorage.clear(); sessionStorage.clear(); } catch{}; window.location.reload(); }}
              style={{ background: '#687485', color: 'white', border: 'none', padding: '12px 24px', borderRadius: 8, fontWeight: 'bold', cursor: 'pointer', fontSize: 15 }}
            >
              Cerrar sesión y recargar
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

// Limpiar el flag de auto-reload si la app cargó OK durante 5s
setTimeout(() => { try { sessionStorage.removeItem(AUTO_RELOAD_KEY); } catch {} }, 5000);

