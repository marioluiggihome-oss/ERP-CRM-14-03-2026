import React from 'react';
import { Hammer, Sparkles, Image as ImageIcon, Ruler, Scissors, FileText } from 'lucide-react';

/**
 * Armarios 2 — Diseñador de armarios con IA (portado del app de AI Studio
 * "LUIGGI HOME - Presupuestador ARMARIOS"). Esqueleto: la integración se hará
 * por fases reutilizando la IA del servidor (Gemini). Ver plan en el chat.
 */
const Armarios2 = ({ state }) => {
  const pasos = [
    { icon: Ruler, t: 'Medidas desde plano', d: 'Sube el plano y la IA detecta ancho/alto/fondo y la distribución.' },
    { icon: Sparkles, t: 'Configurar diseño', d: 'Tipo (vestidor/armario), material, estilo, puertas y modelo.' },
    { icon: ImageIcon, t: 'Render con IA', d: 'Genera una imagen realista del armario y edítala en lenguaje natural.' },
    { icon: Scissors, t: 'Despiece + presupuesto', d: 'Lista de corte y cálculo de coste (fábrica o instalador externo).' },
    { icon: FileText, t: 'PDF / dibujo técnico', d: 'Ficha técnica y presupuesto con marca de agua.' },
  ];
  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-24 bg-slate-50 overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-purple-600 via-fuchsia-600 to-rose-500 text-white px-4 py-3 mb-4 shadow-lg flex items-center gap-3 flex-wrap">
        <h1 className="ml-14 sm:ml-2 text-base sm:text-lg font-black flex items-center gap-2"><Hammer size={18} /> Armarios 2 · Diseñador IA</h1>
        <span className="text-[10px] font-black bg-white/20 px-2 py-0.5 rounded-full">EN INTEGRACIÓN</span>
      </div>
      <div className="bg-white rounded-2xl border border-slate-200 p-5 max-w-3xl">
        <p className="text-sm text-slate-600 mb-4">Diseñador de armarios desde plano con IA (Gemini). Se está integrando en el ERP por fases, reutilizando la clave de IA del servidor. Estas serán sus funciones:</p>
        <div className="space-y-2.5">
          {pasos.map((p, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 bg-slate-50/60">
              <div className="w-9 h-9 rounded-lg bg-fuchsia-100 text-fuchsia-600 flex items-center justify-center shrink-0"><p.icon size={18} /></div>
              <div><p className="font-black text-slate-800 text-sm">{p.t}</p><p className="text-xs text-slate-500">{p.d}</p></div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-4">Nota: el render por IA consume créditos de Gemini por imagen. Se activará cada fase según acordemos.</p>
      </div>
    </div>
  );
};

export default Armarios2;
