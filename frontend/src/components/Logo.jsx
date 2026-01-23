import React from 'react';

const Logo = ({ className = 'h-12', showSlogan = true, variant = 'light', customLogo }) => {
  
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

  if (variant === 'dark') {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <div className="flex flex-col items-center text-center gap-1">
             <div className="flex items-center gap-3">
                <span className="text-slate-900 font-black italic text-5xl tracking-tighter leading-none">LUIGGI</span>
             </div>
             <span className="text-orange-600 font-black tracking-[0.4em] text-xs uppercase italic -mt-1">
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
