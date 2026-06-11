/**
 * WelcomeScreen — saludo inicial tras iniciar sesión.
 * Muestra "Bienvenido" + el nombre del usuario y su fotografía (o iniciales).
 * Tras unos segundos (o al pulsar "Entrar") da paso a los menús del usuario.
 * En móvil/tablet NO se muestra (se entra directo); eso lo decide App.js.
 */
import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight } from 'lucide-react';

const initials = (name) => {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

const WelcomeScreen = ({ user, logo, onContinue, autoMs = 3200 }) => {
  const name = user?.clientName || user?.username || 'Usuario';
  const photo = user?.photoUrl || user?.photo || user?.avatar || '';
  const [leaving, setLeaving] = useState(false);
  const onContinueRef = useRef(onContinue);
  onContinueRef.current = onContinue;

  const finish = () => {
    if (leaving) return;
    setLeaving(true);
    setTimeout(() => onContinueRef.current && onContinueRef.current(), 350);
  };

  useEffect(() => {
    const t = setTimeout(() => {
      setLeaving(true);
      setTimeout(() => onContinueRef.current && onContinueRef.current(), 350);
    }, autoMs);
    return () => clearTimeout(t);
  }, [autoMs]);

  return (
    <div
      onClick={finish}
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 cursor-pointer transition-opacity duration-300 ${leaving ? 'opacity-0' : 'opacity-100'}`}
    >
      {logo && (
        <img src={logo} alt="Logo" className="h-12 sm:h-14 w-auto object-contain mb-10 opacity-90" />
      )}

      {/* Avatar / foto */}
      <div className={`relative mb-7 transition-transform duration-500 ${leaving ? 'scale-95' : 'scale-100'}`}>
        <div className="absolute inset-0 rounded-full blur-2xl bg-brand opacity-30" />
        {photo ? (
          <img
            src={photo}
            alt={name}
            className="relative w-32 h-32 sm:w-40 sm:h-40 rounded-full object-cover ring-4 ring-brand shadow-2xl"
          />
        ) : (
          <div className="relative w-32 h-32 sm:w-40 sm:h-40 rounded-full ring-4 ring-brand shadow-2xl bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
            <span className="text-4xl sm:text-5xl font-black text-white tracking-wider">{initials(name)}</span>
          </div>
        )}
      </div>

      <p className="text-brand text-sm sm:text-base font-black uppercase tracking-[0.35em] mb-2">Bienvenido</p>
      <h1 className="text-white text-3xl sm:text-5xl font-black text-center px-6 leading-tight">{name}</h1>

      <button
        onClick={(e) => { e.stopPropagation(); finish(); }}
        className="mt-12 flex items-center gap-2 px-7 py-3 rounded-full bg-brand text-white font-black text-sm uppercase tracking-widest shadow-xl hover:scale-105 transition-transform"
      >
        Entrar <ArrowRight size={18} />
      </button>
      <p className="mt-5 text-slate-500 text-[11px]">Toca en cualquier sitio para continuar</p>
    </div>
  );
};

export default WelcomeScreen;
