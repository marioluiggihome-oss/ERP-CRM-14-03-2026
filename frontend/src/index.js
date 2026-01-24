import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error capturado:', error, errorInfo);
  }

  clearCacheAndReload = () => {
    // Clear all localStorage
    localStorage.clear();
    // Clear sessionStorage
    sessionStorage.clear();
    // Reload
    window.location.reload();
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center', 
          fontFamily: 'system-ui',
          background: '#1e293b',
          minHeight: '100vh',
          color: 'white'
        }}>
          <h1 style={{ color: '#f97316', marginBottom: '20px' }}>⚠️ Error en la Aplicación</h1>
          <p style={{ marginBottom: '20px' }}>Ha ocurrido un error debido a datos en caché antiguos.</p>
          
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              onClick={this.clearCacheAndReload}
              style={{
                background: '#22c55e',
                color: 'white',
                border: 'none',
                padding: '14px 28px',
                borderRadius: '8px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              🧹 Limpiar Caché y Recargar
            </button>
            
            <button 
              onClick={() => window.location.reload()} 
              style={{
                background: '#6b7280',
                color: 'white',
                border: 'none',
                padding: '14px 28px',
                borderRadius: '8px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              🔄 Solo Recargar
            </button>
          </div>
          
          <details style={{ marginTop: '30px', textAlign: 'left', maxWidth: '600px', margin: '30px auto' }}>
            <summary style={{ cursor: 'pointer', color: '#94a3b8' }}>Detalles del error</summary>
            <pre style={{ 
              background: '#0f172a', 
              padding: '15px', 
              borderRadius: '8px',
              overflow: 'auto',
              fontSize: '11px',
              color: '#f87171',
              marginTop: '10px'
            }}>
              {this.state.error?.toString()}
            </pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);
