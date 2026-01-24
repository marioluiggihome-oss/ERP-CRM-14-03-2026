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
          <p style={{ marginBottom: '20px' }}>Ha ocurrido un error. Por favor, recarga la página.</p>
          <button 
            onClick={() => window.location.reload()} 
            style={{
              background: '#f97316',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Recargar Página
          </button>
          <details style={{ marginTop: '20px', textAlign: 'left', maxWidth: '600px', margin: '20px auto' }}>
            <summary style={{ cursor: 'pointer' }}>Detalles del error</summary>
            <pre style={{ 
              background: '#0f172a', 
              padding: '15px', 
              borderRadius: '8px',
              overflow: 'auto',
              fontSize: '12px'
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
