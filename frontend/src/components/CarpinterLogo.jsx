/**
 * CarpinterLogo — Identidad de marca carpinter.io (Carpinteros & Ebanistas).
 * Símbolo: un gramil de ebanista (marca líneas) cruzando una "C" abierta.
 * Recreado en SVG a partir del logo aprobado. Colores por props para poder
 * usarlo sobre fondo claro y oscuro.
 *
 *   <CarpinterMark size={48} />                 -> solo el símbolo
 *   <CarpinterLogo height={40} tone="dark" />   -> símbolo + "carpinter.io"
 */
import React from 'react';

const ORANGE = '#C4622D';

export function CarpinterMark({ size = 48, orange = ORANGE, ink = '#1A1A1A', className = '' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className} aria-label="carpinter.io">
      {/* C abierta (naranja), detrás del gramil */}
      <path
        d="M30 12 A20 20 0 1 0 30 52"
        fill="none" stroke={orange} strokeWidth="4.2" strokeLinecap="round"
      />
      {/* Gramil: vástago vertical */}
      <rect x="20.4" y="9" width="4.2" height="46" rx="1.4" fill="none" stroke={orange} strokeWidth="3" />
      {/* Cabeza superior */}
      <rect x="19.2" y="4.6" width="6.6" height="5" rx="1" fill="none" stroke={orange} strokeWidth="2.6" />
      {/* Fijo / tope (rectángulo) con tornillo */}
      <rect x="9.5" y="24.5" width="26" height="13" rx="1.6" fill="none" stroke={orange} strokeWidth="3" />
      <circle cx="17.5" cy="31" r="3.4" fill="none" stroke={orange} strokeWidth="2.6" />
      {/* Punta inferior */}
      <path d="M22.5 55 L20.4 60.5 L24.6 60.5 Z" fill={orange} />
    </svg>
  );
}

export default function CarpinterLogo({ height = 40, tone = 'dark', orange = ORANGE, className = '' }) {
  const ink = tone === 'light' ? '#F4EFE6' : '#1A1A1A';
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`} style={{ height }}>
      <CarpinterMark size={height} orange={orange} ink={ink} />
      <span
        className="font-black tracking-tight leading-none"
        style={{ fontFamily: "'DM Sans', system-ui, sans-serif", fontSize: height * 0.62, color: ink }}
      >
        carpinter<span style={{ color: orange }}>.io</span>
      </span>
    </span>
  );
}
