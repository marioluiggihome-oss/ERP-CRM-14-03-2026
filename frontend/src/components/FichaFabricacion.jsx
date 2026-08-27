/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { FileText, Download, Save } from 'lucide-react';
import { jsPDF } from 'jspdf';

/**
 * Ficha Técnica de Fabricación (estilo dossier de estudio). Formulario editable
 * + exportación a PDF profesional A4. Se usa como pestaña dentro de Estudio
 * Cocinas. Prefill opcional desde el proyecto (cliente/ref).
 */
const EMPTY = {
  codProyecto: '', proyecto: '', version: 'v1', responsable: '', fechaCierre: '',
  adjDistribucion: true, adjElectros: true, adjOtros: '',
  puertaA: { tipo: '', color: '', grosor: '', tirador: '', notas: '' },
  puertaB: { tipo: '', color: '', grosor: '', tirador: '', notas: '' },
  casco: { color: '', grosor: '', notas: '' },
  vitrina: { marco: '', cristal: '', casco: '', baldas: '', iluminacion: '', tirador: '', notas: '' },
  otros: { zocalo: '', gola: '', iluminacion: '' },
  encimera: { material: '', marca: '', modelo: '', acabado: '', cantoA: '', cantoB: '', fregadero: '' },
  notas: '',
};

const Field = ({ label, value, onChange, w = '' }) => (
  <label className={`flex flex-col gap-0.5 ${w}`}>
    <span className="text-[10px] font-black text-slate-400 uppercase tracking-wide">{label}</span>
    <input value={value || ''} onChange={e => onChange(e.target.value)}
      className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-slate-800" />
  </label>
);

const Section = ({ title, children }) => (
  <div className="rounded-2xl border border-slate-200 overflow-hidden">
    <div className="bg-slate-800 text-white px-3 py-1.5 text-[11px] font-black uppercase tracking-widest">{title}</div>
    <div className="p-3 grid grid-cols-2 gap-3">{children}</div>
  </div>
);

export default function FichaFabricacion({ proy, logo }) {
  const storeKey = `ficha_fab_${(proy?.nombre_cliente || 'default').replace(/\s+/g, '_')}`;
  const [f, setF] = useState(EMPTY);
  const [saved, setSaved] = useState(false);

  // Cargar de localStorage / prefill del proyecto.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storeKey);
      if (raw) { setF({ ...EMPTY, ...JSON.parse(raw) }); return; }
    } catch (_) {}
    setF(prev => ({
      ...EMPTY,
      proyecto: proy?.nombre_cliente ? `${proy.nombre_cliente} cocina` : prev.proyecto,
      encimera: { ...EMPTY.encimera, material: proy?.notas?.includes('mármol') ? 'Porcelánico' : '' },
    }));
    // eslint-disable-next-line
  }, [storeKey]);

  const set = (path, val) => setF(prev => {
    const next = { ...prev };
    if (path.includes('.')) { const [a, b] = path.split('.'); next[a] = { ...next[a], [b]: val }; }
    else next[path] = val;
    return next;
  });
  const guardar = () => { try { localStorage.setItem(storeKey, JSON.stringify(f)); setSaved(true); setTimeout(() => setSaved(false), 2000); } catch (_) {} };

  // ── PDF profesional (una hoja A4, estructura de dossier técnico) ──
  const exportarPDF = () => {
    const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
    const W = pdf.internal.pageSize.getWidth();
    let y = 14;
    // Cabecera
    pdf.setFontSize(15); pdf.setFont(undefined, 'bold'); pdf.setTextColor(20);
    pdf.text('DOSSIER TÉCNICO DE FABRICACIÓN', 14, y);
    if (logo) { try { pdf.addImage(logo, logo.includes('png') ? 'PNG' : 'JPEG', W - 46, y - 8, 32, 14); } catch (_) {} }
    y += 6;
    pdf.setDrawColor(180); pdf.line(14, y, W - 14, y); y += 5;
    // Datos de cabecera
    pdf.setFontSize(9); pdf.setFont(undefined, 'normal'); pdf.setTextColor(70);
    const hdr = [
      ['Cód. Proyecto', f.codProyecto], ['Proyecto', f.proyecto], ['Versión', f.version],
      ['Responsable', f.responsable], ['Fecha cierre', f.fechaCierre],
    ];
    hdr.forEach(([k, v], i) => {
      const x = 14 + (i % 3) * ((W - 28) / 3);
      if (i % 3 === 0 && i > 0) y += 8;
      pdf.setTextColor(150); pdf.setFontSize(7); pdf.text(k.toUpperCase(), x, y);
      pdf.setTextColor(30); pdf.setFontSize(9); pdf.text(String(v || '—'), x, y + 4);
    });
    y += 9;
    const adj = [];
    if (f.adjDistribucion) adj.push('Distribución acotada');
    if (f.adjElectros) adj.push('Listado electrodomésticos');
    if (f.adjOtros) adj.push(f.adjOtros);
    pdf.setTextColor(150); pdf.setFontSize(7); pdf.text('DOCUMENTACIÓN ADJUNTA', 14, y);
    pdf.setTextColor(30); pdf.setFontSize(9); pdf.text(adj.join('  ·  ') || '—', 14, y + 4);
    y += 10;

    // Helper para bloque de sección con filas clave:valor
    const block = (title, rows) => {
      if (y > 260) { pdf.addPage(); y = 16; }
      pdf.setFillColor(30, 30, 33); pdf.rect(14, y - 4, W - 28, 6, 'F');
      pdf.setTextColor(255); pdf.setFontSize(8); pdf.setFont(undefined, 'bold');
      pdf.text(title.toUpperCase(), 16, y);
      y += 6; pdf.setFont(undefined, 'normal');
      rows.forEach((pair, i) => {
        const cols = pair.length;
        pair.forEach(([k, v], c) => {
          const x = 16 + c * ((W - 32) / cols);
          pdf.setTextColor(150); pdf.setFontSize(7); pdf.text(k.toUpperCase(), x, y);
          pdf.setTextColor(30); pdf.setFontSize(9); pdf.text(String(v || '—'), x, y + 3.5);
        });
        y += 8;
      });
      y += 3;
    };

    block('Puerta A', [[['Tipo', f.puertaA.tipo], ['Color', f.puertaA.color]], [['Grosor', f.puertaA.grosor], ['Tirador', f.puertaA.tirador]], [['Notas', f.puertaA.notas]]]);
    if (f.puertaB.tipo || f.puertaB.color) block('Puerta B', [[['Tipo', f.puertaB.tipo], ['Color', f.puertaB.color]], [['Grosor', f.puertaB.grosor], ['Tirador', f.puertaB.tirador]]]);
    block('Casco', [[['Color', f.casco.color], ['Grosor', f.casco.grosor]], [['Notas', f.casco.notas]]]);
    if (f.vitrina.marco || f.vitrina.cristal) block('Vitrina', [[['Marco', f.vitrina.marco], ['Cristal', f.vitrina.cristal]], [['Casco', f.vitrina.casco], ['Baldas', f.vitrina.baldas]], [['Iluminación', f.vitrina.iluminacion], ['Tirador', f.vitrina.tirador]]]);
    block('Otros', [[['Zócalo', f.otros.zocalo], ['Gola', f.otros.gola]], [['Iluminación', f.otros.iluminacion]]]);
    block('Encimera', [[['Material', f.encimera.material], ['Marca', f.encimera.marca]], [['Modelo', f.encimera.modelo], ['Acabado', f.encimera.acabado]], [['Canto A', f.encimera.cantoA], ['Canto B', f.encimera.cantoB]], [['Fregadero', f.encimera.fregadero]]]);
    if (f.notas) block('Notas', [[['', f.notas]]]);

    pdf.save(`Ficha_Fabricacion_${(f.proyecto || 'cocina').replace(/\s+/g, '_')}.pdf`);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h3 className="flex items-center gap-2 text-sm font-black text-slate-800 uppercase tracking-wide"><FileText size={16} /> Ficha técnica de fabricación</h3>
        <div className="flex gap-2">
          <button onClick={guardar} className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700"><Save size={14} /> {saved ? 'Guardado' : 'Guardar'}</button>
          <button onClick={exportarPDF} className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 text-white rounded-lg text-xs font-bold hover:bg-slate-900"><Download size={14} /> Exportar PDF</button>
        </div>
      </div>

      {/* Cabecera */}
      <div className="rounded-2xl border border-slate-200 p-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Field label="Cód. Proyecto" value={f.codProyecto} onChange={v => set('codProyecto', v)} />
        <Field label="Proyecto" value={f.proyecto} onChange={v => set('proyecto', v)} />
        <Field label="Versión Doc." value={f.version} onChange={v => set('version', v)} />
        <Field label="Responsable" value={f.responsable} onChange={v => set('responsable', v)} />
        <Field label="Fecha cierre técnico" value={f.fechaCierre} onChange={v => set('fechaCierre', v)} />
        <div className="flex flex-col gap-1 justify-end">
          <span className="text-[10px] font-black text-slate-400 uppercase">Documentación adjunta</span>
          <div className="flex flex-col gap-1 text-[12px]">
            <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.adjDistribucion} onChange={e => set('adjDistribucion', e.target.checked)} /> Distribución acotada</label>
            <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.adjElectros} onChange={e => set('adjElectros', e.target.checked)} /> Listado electrodomésticos</label>
            <input value={f.adjOtros} onChange={e => set('adjOtros', e.target.value)} placeholder="Otros…" className="px-2 py-1 border border-slate-200 rounded text-[12px]" />
          </div>
        </div>
      </div>

      <Section title="Puertas · A">
        <Field label="Tipo" value={f.puertaA.tipo} onChange={v => set('puertaA.tipo', v)} />
        <Field label="Color" value={f.puertaA.color} onChange={v => set('puertaA.color', v)} />
        <Field label="Grosor" value={f.puertaA.grosor} onChange={v => set('puertaA.grosor', v)} />
        <Field label="Tirador" value={f.puertaA.tirador} onChange={v => set('puertaA.tirador', v)} />
        <Field label="Notas" value={f.puertaA.notas} onChange={v => set('puertaA.notas', v)} w="col-span-2" />
      </Section>

      <Section title="Puertas · B (si hay 2º acabado)">
        <Field label="Tipo" value={f.puertaB.tipo} onChange={v => set('puertaB.tipo', v)} />
        <Field label="Color" value={f.puertaB.color} onChange={v => set('puertaB.color', v)} />
        <Field label="Grosor" value={f.puertaB.grosor} onChange={v => set('puertaB.grosor', v)} />
        <Field label="Tirador" value={f.puertaB.tirador} onChange={v => set('puertaB.tirador', v)} />
      </Section>

      <Section title="Casco">
        <Field label="Color" value={f.casco.color} onChange={v => set('casco.color', v)} />
        <Field label="Grosor" value={f.casco.grosor} onChange={v => set('casco.grosor', v)} />
        <Field label="Notas" value={f.casco.notas} onChange={v => set('casco.notas', v)} w="col-span-2" />
      </Section>

      <Section title="Vitrina">
        <Field label="Tipo de marco" value={f.vitrina.marco} onChange={v => set('vitrina.marco', v)} />
        <Field label="Cristal" value={f.vitrina.cristal} onChange={v => set('vitrina.cristal', v)} />
        <Field label="Casco" value={f.vitrina.casco} onChange={v => set('vitrina.casco', v)} />
        <Field label="Baldas" value={f.vitrina.baldas} onChange={v => set('vitrina.baldas', v)} />
        <Field label="Iluminación" value={f.vitrina.iluminacion} onChange={v => set('vitrina.iluminacion', v)} />
        <Field label="Tirador" value={f.vitrina.tirador} onChange={v => set('vitrina.tirador', v)} />
      </Section>

      <Section title="Otros">
        <Field label="Zócalo" value={f.otros.zocalo} onChange={v => set('otros.zocalo', v)} />
        <Field label="Gola" value={f.otros.gola} onChange={v => set('otros.gola', v)} />
        <Field label="Iluminación" value={f.otros.iluminacion} onChange={v => set('otros.iluminacion', v)} w="col-span-2" />
      </Section>

      <Section title="Encimera">
        <Field label="Material" value={f.encimera.material} onChange={v => set('encimera.material', v)} />
        <Field label="Marca" value={f.encimera.marca} onChange={v => set('encimera.marca', v)} />
        <Field label="Modelo" value={f.encimera.modelo} onChange={v => set('encimera.modelo', v)} />
        <Field label="Acabado" value={f.encimera.acabado} onChange={v => set('encimera.acabado', v)} />
        <Field label="Canto A (encimera + isla)" value={f.encimera.cantoA} onChange={v => set('encimera.cantoA', v)} />
        <Field label="Canto B (desayunador)" value={f.encimera.cantoB} onChange={v => set('encimera.cantoB', v)} />
        <Field label="Fregadero" value={f.encimera.fregadero} onChange={v => set('encimera.fregadero', v)} w="col-span-2" />
      </Section>

      <div className="rounded-2xl border border-slate-200 overflow-hidden">
        <div className="bg-slate-800 text-white px-3 py-1.5 text-[11px] font-black uppercase tracking-widest">Notas</div>
        <textarea value={f.notas} onChange={e => set('notas', e.target.value)} rows={4}
          placeholder="Fregadero Tartufo · Grifo con metal · Cubiertero desayunador · Grifo aparte de ósmosis (instala fontanero)…"
          className="w-full p-3 text-sm focus:outline-none" />
      </div>
    </div>
  );
}
