import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

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

    // Si es la primera vez en esta sesión, intentar auto-recargar (puede ser bundle desfasado)
    try {
      const reloaded = sessionStorage.getItem(AUTO_RELOAD_KEY);
      if (!reloaded) {
        sessionStorage.setItem(AUTO_RELOAD_KEY, '1');
        // pequeño delay para evitar bucle infinito
        setTimeout(() => window.location.reload(), 800);
      }
    } catch {}
  }

  handleManualReload = () => {
    try { sessionStorage.removeItem(AUTO_RELOAD_KEY); } catch {}
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const errMsg = this.state.error?.message || String(this.state.error || 'Error desconocido');
      return (
        <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', background: '#0f172a', minHeight: '100vh', color: 'white' }}>
          <div style={{ maxWidth: 560, margin: '40px auto', background: '#1e293b', borderRadius: 16, padding: 24, border: '1px solid #334155' }}>
            <h1 style={{ color: '#f97316', marginBottom: 12, fontSize: 22 }}>⚠️ Algo ha fallado</h1>
            <p style={{ marginBottom: 16, color: '#cbd5e1', fontSize: 14 }}>
              La aplicación ha encontrado un error inesperado.
            </p>
            <details style={{ background: '#0f172a', padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 12, color: '#94a3b8' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Ver detalles técnicos</summary>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: 8 }}>{errMsg}</pre>
            </details>
            <button
              onClick={this.handleManualReload}
              style={{ background: '#22c55e', color: 'white', border: 'none', padding: '12px 24px', borderRadius: 8, fontWeight: 'bold', cursor: 'pointer', fontSize: 15, marginRight: 10 }}
            >
              🔄 Recargar
            </button>
            <button
              onClick={() => { try { localStorage.clear(); sessionStorage.clear(); } catch{}; window.location.reload(); }}
              style={{ background: '#64748b', color: 'white', border: 'none', padding: '12px 24px', borderRadius: 8, fontWeight: 'bold', cursor: 'pointer', fontSize: 15 }}
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

