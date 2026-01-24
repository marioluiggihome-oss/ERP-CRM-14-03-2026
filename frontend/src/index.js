import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Clear all caches and service workers on load
const clearAllCaches = async () => {
  try {
    // Unregister all service workers
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        await registration.unregister();
        console.log('Service Worker unregistered');
      }
    }
    
    // Clear all caches
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      for (const cacheName of cacheNames) {
        await caches.delete(cacheName);
        console.log('Cache deleted:', cacheName);
      }
    }
  } catch (e) {
    console.error('Error clearing caches:', e);
  }
};

// Run cache clearing
clearAllCaches();

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

  clearEverythingAndReload = async () => {
    // Clear localStorage
    localStorage.clear();
    // Clear sessionStorage
    sessionStorage.clear();
    
    // Clear service workers and caches
    await clearAllCaches();
    
    // Force reload without cache
    window.location.reload(true);
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
          <p style={{ marginBottom: '10px' }}>Ha ocurrido un error debido a datos en caché antiguos.</p>
          <p style={{ marginBottom: '20px', color: '#94a3b8', fontSize: '14px' }}>
            Haz clic en el botón verde para limpiar TODO el caché y recargar.
          </p>
          
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              onClick={this.clearEverythingAndReload}
              style={{
                background: '#22c55e',
                color: 'white',
                border: 'none',
                padding: '16px 32px',
                borderRadius: '8px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              🧹 LIMPIAR TODO Y RECARGAR
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
