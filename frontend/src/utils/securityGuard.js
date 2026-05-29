/**
 * Security Guard - Protección contra copia del sistema
 * LUIGGI HOME - Sistema blindado
 */

// Deshabilitar clic derecho
const disableRightClick = () => {
  document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    return false;
  });
};

// Deshabilitar atajos de teclado peligrosos
const disableKeyboardShortcuts = () => {
  document.addEventListener('keydown', (e) => {
    // F12 - DevTools
    if (e.key === 'F12') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+Shift+I - DevTools
    if (e.ctrlKey && e.shiftKey && e.key === 'I') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+Shift+J - Console
    if (e.ctrlKey && e.shiftKey && e.key === 'J') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+Shift+C - Inspect Element
    if (e.ctrlKey && e.shiftKey && e.key === 'C') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+U - View Source
    if (e.ctrlKey && e.key === 'u') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+S - Save Page
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+P - Print (can be used to save as PDF)
    if (e.ctrlKey && e.key === 'p') {
      e.preventDefault();
      return false;
    }
    
    // Ctrl+Shift+K - Firefox Console
    if (e.ctrlKey && e.shiftKey && e.key === 'K') {
      e.preventDefault();
      return false;
    }
  });
};

// Detectar y bloquear DevTools
const detectDevTools = () => {
  const threshold = 160;
  
  const checkDevTools = () => {
    const widthThreshold = window.outerWidth - window.innerWidth > threshold;
    const heightThreshold = window.outerHeight - window.innerHeight > threshold;
    
    if (widthThreshold || heightThreshold) {
      // DevTools detectado - redirigir o mostrar advertencia
      document.body.innerHTML = `
        <div style="
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          color: white;
          font-family: system-ui, -apple-system, sans-serif;
          text-align: center;
          padding: 20px;
        ">
          <div style="font-size: 80px; margin-bottom: 20px;">🔒</div>
          <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 10px;">
            ACCESO RESTRINGIDO
          </h1>
          <p style="font-size: 1rem; opacity: 0.8; max-width: 400px;">
            Las herramientas de desarrollo están deshabilitadas por seguridad.
            Por favor, cierra las DevTools para continuar.
          </p>
          <p style="font-size: 0.8rem; opacity: 0.5; margin-top: 30px;">
            LUIGGI HOME - Sistema Protegido
          </p>
        </div>
      `;
    }
  };
  
  // Verificar periódicamente
  setInterval(checkDevTools, 1000);
  
  // También detectar usando debugger
  const detectDebugger = () => {
    const start = performance.now();
    // debugger; // Descomentar para activar detección más agresiva
    const end = performance.now();
    if (end - start > 100) {
      // Debugger detectado
      checkDevTools();
    }
  };
  
  setInterval(detectDebugger, 1000);
};

// Deshabilitar selección de texto en elementos sensibles
const disableTextSelection = () => {
  const style = document.createElement('style');
  style.textContent = `
    /* Deshabilitar selección en toda la app excepto inputs */
    body {
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
    }
    
    /* Permitir selección en inputs y textareas */
    input, textarea, [contenteditable="true"] {
      -webkit-user-select: text;
      -moz-user-select: text;
      -ms-user-select: text;
      user-select: text;
    }
    
    /* Deshabilitar arrastrar imágenes */
    img {
      -webkit-user-drag: none;
      -khtml-user-drag: none;
      -moz-user-drag: none;
      -o-user-drag: none;
      user-drag: none;
      pointer-events: none;
    }
  `;
  document.head.appendChild(style);
};

// Deshabilitar copiar/pegar excepto en inputs
const disableCopyPaste = () => {
  document.addEventListener('copy', (e) => {
    const activeElement = document.activeElement;
    const isInput = activeElement.tagName === 'INPUT' || 
                    activeElement.tagName === 'TEXTAREA' ||
                    activeElement.isContentEditable;
    
    if (!isInput) {
      e.preventDefault();
      return false;
    }
  });
  
  document.addEventListener('cut', (e) => {
    const activeElement = document.activeElement;
    const isInput = activeElement.tagName === 'INPUT' || 
                    activeElement.tagName === 'TEXTAREA' ||
                    activeElement.isContentEditable;
    
    if (!isInput) {
      e.preventDefault();
      return false;
    }
  });
};

// Deshabilitar arrastrar y soltar
const disableDragDrop = () => {
  document.addEventListener('dragstart', (e) => {
    if (e.target.tagName !== 'INPUT') {
      e.preventDefault();
      return false;
    }
  });
  
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    return false;
  });
};

// Limpiar console
const clearConsole = () => {
  const clear = () => {
    console.clear();
    console.log('%c⚠️ SISTEMA PROTEGIDO', 'color: red; font-size: 30px; font-weight: bold;');
    console.log('%cLUIGGI HOME - Acceso no autorizado prohibido', 'color: orange; font-size: 14px;');
  };
  
  // Mostrar aviso de marca una sola vez. NOTA: no se limpia la consola periódicamente
  // porque ocultaría errores reales y dificulta el soporte/diagnóstico.
  clear();
};

// Detectar y bloquear iframes externos
const preventIframeEmbed = () => {
  if (window.self !== window.top) {
    // Estamos en un iframe - redirigir
    window.top.location = window.self.location;
  }
};

// Añadir marca de agua invisible (fingerprint)
const addWatermark = () => {
  const watermark = document.createElement('div');
  watermark.id = 'luiggi-watermark';
  watermark.style.cssText = `
    position: fixed;
    bottom: 10px;
    right: 10px;
    font-size: 10px;
    color: rgba(0,0,0,0.03);
    pointer-events: none;
    z-index: 99999;
    font-family: monospace;
  `;
  watermark.textContent = `LUIGGI-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  document.body.appendChild(watermark);
};

// Inicializar todas las protecciones
export const initSecurityGuard = () => {
  // Solo activar en producción (en desarrollo entorpece el trabajo y oculta errores)
  if (process.env.NODE_ENV === 'production') {
    disableRightClick();
    disableKeyboardShortcuts();
    disableTextSelection();
    disableCopyPaste();
    disableDragDrop();
    clearConsole();
    preventIframeEmbed();
    addWatermark();
    
    // Detección de DevTools (puede ser molesto, activar con cuidado)
    // detectDevTools();
    
    console.log('%c🔒 Security Guard Activated', 'color: green; font-weight: bold;');
  }
};

export default initSecurityGuard;
