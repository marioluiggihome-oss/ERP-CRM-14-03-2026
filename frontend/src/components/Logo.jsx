/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from 'react';

// Marca neutra (modo MARCA BLANCA): logo genérico sin nombre de marca propia.
// Si hay companyName configurado, se usa como texto; si no, un rótulo neutro.
const NeutralLogo = ({ className = 'h-12', variant = 'light', companyName = '' }) => {
  const dark = variant === 'dark';
  const ink = dark ? '#0f172a' : '#1e293b';
  const accent = '#4f46e5';
  const nombre = (companyName || 'Gestión Profesional').trim();
  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <svg viewBox="0 0 40 40" className="h-full w-auto" aria-label="logo">
        <rect x="4" y="4" width="32" height="32" rx="9" fill={accent} />
        <rect x="12" y="12" width="16" height="16" rx="3" fill="none" stroke="#fff" strokeWidth="2.4" />
        <line x1="12" y1="20" x2="28" y2="20" stroke="#fff" strokeWidth="2.4" />
        <circle cx="24" cy="16" r="1.4" fill="#fff" />
        <circle cx="24" cy="24" r="1.4" fill="#fff" />
      </svg>
      <span className="font-black tracking-tight leading-none" style={{ color: ink, fontSize: '1.05rem' }}>
        {nombre}
      </span>
    </div>
  );
};

const Logo = ({ className = 'h-12', showSlogan = true, variant = 'light', customLogo, marcaBlanca = false, companyName = '' }) => {

  if (customLogo) {
    return (
      <div className={`flex items-center justify-center ${className} animate-in fade-in duration-500 overflow-hidden`}>
        <img
          src={customLogo}
          alt="Logo Corporativo"
          className="h-full w-auto object-contain drop-shadow-[0_2px_5px_rgba(0,0,0,0.05)]"
        />
      </div>
    );
  }

  // Modo marca blanca (sin logo propio subido): logo neutro genérico.
  if (marcaBlanca) {
    return <NeutralLogo className={className} variant={variant} companyName={companyName} />;
  }

  if (variant === 'dark') {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <div className="flex flex-col items-center text-center gap-0.5">
             <div className="flex items-center gap-2">
                <span className="text-slate-900 font-black italic text-3xl tracking-tighter leading-none">LUIGGI</span>
             </div>
             <span className="text-orange-600 font-black tracking-[0.3em] text-[10px] uppercase italic">
                HOME MASTER
             </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className="flex flex-col items-center text-center">
        <span className="text-stone-900 italic text-3xl font-serif leading-none">luiggi</span>
        <span className="text-orange-600 text-xl tracking-[0.3em] font-black -mt-1 italic">HOME</span>
        {showSlogan && (
          <div className="flex flex-col items-center gap-1 mt-2 border-t border-stone-100 pt-1">
            <span className="text-[5px] text-stone-300 font-black">SISTEMA INDUSTRIAL v2026</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default Logo;
