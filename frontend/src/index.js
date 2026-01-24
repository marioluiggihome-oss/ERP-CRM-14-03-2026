import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Patch to handle insertBefore errors caused by browser extensions
const originalInsertBefore = Node.prototype.insertBefore;
Node.prototype.insertBefore = function(newNode, referenceNode) {
  if (referenceNode && referenceNode.parentNode !== this) {
    // The reference node is not a child of this node, likely due to extension interference
    // Just append the node instead
    return this.appendChild(newNode);
  }
  return originalInsertBefore.call(this, newNode, referenceNode);
};

// Also patch removeChild for similar issues
const originalRemoveChild = Node.prototype.removeChild;
Node.prototype.removeChild = function(child) {
  if (child && child.parentNode !== this) {
    // The child is not actually a child of this node
    return child;
  }
  return originalRemoveChild.call(this, child);
};

// Clear caches on load
(async () => {
  try {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      for (const reg of regs) await reg.unregister();
    }
    if ('caches' in window) {
      const names = await caches.keys();
      for (const name of names) await caches.delete(name);
    }
  } catch (e) { console.error(e); }
})();

// Simple Error Boundary
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('React Error:', error, info);
  }

  clearAndReload = async () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload(true);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, textAlign: 'center', fontFamily: 'system-ui', background: '#1e293b', minHeight: '100vh', color: 'white' }}>
          <h1 style={{ color: '#f97316', marginBottom: 20 }}>⚠️ Error en la Aplicación</h1>
          <p style={{ marginBottom: 10 }}>Este error suele ser causado por extensiones del navegador.</p>
          <p style={{ marginBottom: 20, color: '#94a3b8' }}>Prueba en modo incógnito o desactiva extensiones como Grammarly, AdBlock, React DevTools.</p>
          <button onClick={this.clearAndReload} style={{ background: '#22c55e', color: 'white', border: 'none', padding: '14px 28px', borderRadius: 8, fontWeight: 'bold', cursor: 'pointer', fontSize: 16 }}>
            🔄 Recargar Página
          </button>
          <details style={{ marginTop: 30, textAlign: 'left', maxWidth: 600, margin: '30px auto' }}>
            <summary style={{ cursor: 'pointer', color: '#94a3b8' }}>Detalles</summary>
            <pre style={{ background: '#0f172a', padding: 15, borderRadius: 8, overflow: 'auto', fontSize: 11, color: '#f87171', marginTop: 10 }}>
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
