import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Clean the root element before mounting
const rootElement = document.getElementById("root");
if (rootElement) {
  // Remove all children to ensure clean state
  while (rootElement.firstChild) {
    rootElement.removeChild(rootElement.firstChild);
  }
}

// Simple Error Boundary
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('React Error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, textAlign: 'center', fontFamily: 'system-ui', background: '#1e293b', minHeight: '100vh', color: 'white' }}>
          <h1 style={{ color: '#f97316', marginBottom: 20 }}>⚠️ Error</h1>
          <p style={{ marginBottom: 20 }}>Prueba limpiar la caché del navegador completamente:</p>
          <p style={{ marginBottom: 10, color: '#94a3b8', fontSize: 14 }}>Chrome: Ctrl+Shift+Delete → Selecciona "Todo el tiempo" → Marca todas las opciones → Borrar</p>
          <button onClick={() => window.location.reload(true)} style={{ background: '#22c55e', color: 'white', border: 'none', padding: '14px 28px', borderRadius: 8, fontWeight: 'bold', cursor: 'pointer', fontSize: 16, marginTop: 20 }}>
            🔄 Recargar
          </button>
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
