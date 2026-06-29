import React, { useState, useMemo } from 'react';
import { Plus, Trash2, Download, Layers, FileText } from 'lucide-react';

// Resumen por cocinas: junta partidas a mano (Muebles, Electrodomésticos,
// Encimera…) por cada cocina, suma totales y forma de pago, y lo presenta /
// exporta a PDF con el logotipo. Pensado para presentar al cliente.

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const uid = () => Math.random().toString(36).slice(2, 9);

const ResumenCocinas = ({ state }) => {
  const today = new Date().toLocaleDateString('es-ES');
  const [cliente, setCliente] = useState('');
  const [fecha, setFecha] = useState(today);
  const [cocinas, setCocinas] = useState([
    { id: uid(), nombre: 'COCINA PRINCIPAL', lineas: [
      { id: uid(), concepto: 'MUEBLES', importe: '' },
      { id: uid(), concepto: 'ELECTRODOMÉSTICOS', importe: '' },
      { id: uid(), concepto: 'ENCIMERA', importe: '' },
    ] },
  ]);
  const [pagos, setPagos] = useState([
    { id: uid(), label: '50% al hacer pedido', percent: 50 },
    { id: uid(), label: '45% a la entrega de materiales', percent: 45 },
    { id: uid(), label: '5% al terminar', percent: 5 },
  ]);
  const [exporting, setExporting] = useState(false);

  const cocinaTotal = (c) => (c.lineas || []).reduce((s, l) => s + (Number(l.importe) || 0), 0);
  const totalGeneral = useMemo(() => cocinas.reduce((s, c) => s + cocinaTotal(c), 0), [cocinas]);

  // ── edición ──
  const addCocina = () => setCocinas(prev => [...prev, { id: uid(), nombre: `COCINA ${prev.length + 1}`, lineas: [
    { id: uid(), concepto: 'MUEBLES', importe: '' },
    { id: uid(), concepto: 'ELECTRODOMÉSTICOS', importe: '' },
    { id: uid(), concepto: 'ENCIMERA', importe: '' },
  ] }]);
  const removeCocina = (id) => setCocinas(prev => prev.filter(c => c.id !== id));
  const setCocinaNombre = (id, nombre) => setCocinas(prev => prev.map(c => c.id === id ? { ...c, nombre } : c));
  const addLinea = (cid) => setCocinas(prev => prev.map(c => c.id === cid ? { ...c, lineas: [...c.lineas, { id: uid(), concepto: '', importe: '' }] } : c));
  const removeLinea = (cid, lid) => setCocinas(prev => prev.map(c => c.id === cid ? { ...c, lineas: c.lineas.filter(l => l.id !== lid) } : c));
  const setLinea = (cid, lid, field, val) => setCocinas(prev => prev.map(c => c.id === cid ? { ...c, lineas: c.lineas.map(l => l.id === lid ? { ...l, [field]: val } : l) } : c));

  const addPago = () => setPagos(prev => [...prev, { id: uid(), label: '', percent: 0 }]);
  const removePago = (id) => setPagos(prev => prev.filter(p => p.id !== id));
  const setPago = (id, field, val) => setPagos(prev => prev.map(p => p.id === id ? { ...p, [field]: val } : p));

  // ── PDF ──
  const exportPDF = async () => {
    setExporting(true);
    try {
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const M = 16;
      let y = 16;
      const logo = state?.logo;
      if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
        try {
          const fmt = logo.includes('image/png') ? 'PNG' : (logo.includes('image/webp') ? 'WEBP' : 'JPEG');
          pdf.addImage(logo, fmt, M, y, 34, 17);
        } catch (_) { /* omitir */ }
      } else {
        pdf.setFontSize(16); pdf.setTextColor(30); pdf.setFont(undefined, 'bold');
        pdf.text('LUIGGI HOME', M, y + 9); pdf.setFont(undefined, 'normal');
      }
      pdf.setFontSize(17); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
      pdf.text('PRESUPUESTO', W - M, y + 6, { align: 'right' });
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(10); pdf.setTextColor(120);
      pdf.text(fecha || today, W - M, y + 12, { align: 'right' });
      y += 24;
      if (cliente) { pdf.setFontSize(12); pdf.setTextColor(30, 27, 75); pdf.setFont(undefined, 'bold'); pdf.text(cliente, M, y); pdf.setFont(undefined, 'normal'); y += 8; }

      const ensure = (need) => { if (y + need > pageH - M) { pdf.addPage(); y = 18; } };

      cocinas.forEach(c => {
        ensure(14 + c.lineas.length * 7 + 10);
        pdf.setFillColor(30, 27, 65); pdf.roundedRect(M, y, W - 2 * M, 8, 1.5, 1.5, 'F');
        pdf.setFontSize(11); pdf.setTextColor(255); pdf.setFont(undefined, 'bold');
        pdf.text((c.nombre || 'COCINA').toUpperCase(), M + 3, y + 5.5);
        pdf.setFont(undefined, 'normal'); y += 12;
        pdf.setFontSize(10.5); pdf.setTextColor(60);
        c.lineas.forEach(l => {
          pdf.text(l.concepto || '', M + 4, y);
          pdf.text(eur(l.importe), W - M - 2, y, { align: 'right' });
          y += 6.5;
        });
        // total cocina
        pdf.setDrawColor(210); pdf.line(W - M - 70, y - 2, W - M - 2, y - 2);
        pdf.setFont(undefined, 'bold'); pdf.setTextColor(30, 27, 65);
        pdf.text('TOTAL', W - M - 70, y + 3);
        pdf.text(eur(cocinaTotal(c)), W - M - 2, y + 3, { align: 'right' });
        pdf.setFont(undefined, 'normal');
        y += 12;
      });

      // total general (caja naranja)
      ensure(18);
      pdf.setFillColor(234, 120, 40); pdf.roundedRect(M, y, W - 2 * M, 13, 2, 2, 'F');
      pdf.setFontSize(12); pdf.setTextColor(255); pdf.setFont(undefined, 'bold');
      pdf.text('TOTAL GENERAL', M + 4, y + 8.5);
      pdf.setFontSize(14); pdf.text(eur(totalGeneral), W - M - 3, y + 8.5, { align: 'right' });
      pdf.setFont(undefined, 'normal'); y += 20;

      // forma de pago
      const pagosValidos = pagos.filter(p => p.label || p.percent);
      if (pagosValidos.length) {
        ensure(10 + pagosValidos.length * 7);
        pdf.setFontSize(11); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
        pdf.text('Forma de pago:', M, y); pdf.setFont(undefined, 'normal'); y += 7;
        pdf.setFontSize(10.5); pdf.setTextColor(60);
        pagosValidos.forEach(p => {
          pdf.text(p.label || '', M + 4, y);
          pdf.text(eur(totalGeneral * (Number(p.percent) || 0) / 100), W - M - 2, y, { align: 'right' });
          y += 6.5;
        });
      }

      pdf.save(`Presupuesto_${(cliente || 'cocinas').replace(/\s+/g, '_')}.pdf`);
    } catch (e) {
      alert('No se pudo generar el PDF: ' + (e.message || ''));
    } finally { setExporting(false); }
  };

  return (
    <div className="h-full min-h-screen flex flex-col p-6 bg-slate-50 overflow-y-auto">
      <div className="flex items-center justify-between mb-1 gap-3 flex-wrap">
        <h1 className="text-2xl font-black text-slate-800 ml-16 flex items-center gap-2"><Layers size={22} /> Resumen Totales</h1>
        <button onClick={exportPDF} disabled={exporting}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          <Download size={16} /> {exporting ? 'Generando…' : 'Exportar / Imprimir PDF'}
        </button>
      </div>
      <p className="text-sm text-slate-500 mb-5">Junta partidas por cocina, suma totales y forma de pago, y preséntalo con tu logo.</p>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 w-full max-w-4xl space-y-6">
        {/* Cliente + fecha */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-black text-slate-500 uppercase block mb-1">Cliente / Proyecto</label>
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Ej: MARIA JOSÉ / MARIA AUXILIADORA"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-bold" />
          </div>
          <div>
            <label className="text-xs font-black text-slate-500 uppercase block mb-1">Fecha</label>
            <input value={fecha} onChange={e => setFecha(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>

        {/* Cocinas */}
        {cocinas.map(c => (
          <div key={c.id} className="rounded-xl border border-slate-200 overflow-hidden">
            <div className="flex items-center gap-2 bg-slate-800 px-3 py-2">
              <input value={c.nombre} onChange={e => setCocinaNombre(c.id, e.target.value)}
                className="flex-1 bg-transparent text-white font-black uppercase text-sm outline-none placeholder-slate-400" placeholder="NOMBRE COCINA" />
              <button onClick={() => removeCocina(c.id)} className="text-slate-300 hover:text-red-400" title="Quitar cocina"><Trash2 size={15} /></button>
            </div>
            <div className="p-3 space-y-2">
              {c.lineas.map(l => (
                <div key={l.id} className="flex items-center gap-2">
                  <input value={l.concepto} onChange={e => setLinea(c.id, l.id, 'concepto', e.target.value)} placeholder="Concepto (ej. MUEBLES)"
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-sm" />
                  <input type="number" value={l.importe} onChange={e => setLinea(c.id, l.id, 'importe', e.target.value)} placeholder="0,00"
                    className="w-32 px-3 py-1.5 border border-slate-200 rounded-lg text-sm text-right" />
                  <button onClick={() => removeLinea(c.id, l.id)} className="p-1.5 text-slate-300 hover:text-red-500" title="Quitar partida"><Trash2 size={14} /></button>
                </div>
              ))}
              <div className="flex items-center justify-between pt-1">
                <button onClick={() => addLinea(c.id)} className="flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"><Plus size={14} /> Añadir partida</button>
                <div className="text-sm font-black text-slate-800">TOTAL: <span className="text-indigo-700">{eur(cocinaTotal(c))}</span></div>
              </div>
            </div>
          </div>
        ))}
        <button onClick={addCocina} className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-bold text-sm"><Plus size={16} /> Añadir cocina</button>

        {/* Total general */}
        <div className="rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white px-5 py-4 flex items-center justify-between">
          <span className="font-black uppercase tracking-wide">Total general</span>
          <span className="text-2xl font-black">{eur(totalGeneral)}</span>
        </div>

        {/* Forma de pago */}
        <div className="rounded-xl border border-slate-200 p-3">
          <p className="text-xs font-black text-slate-500 uppercase mb-2">Forma de pago</p>
          <div className="space-y-2">
            {pagos.map(p => (
              <div key={p.id} className="flex items-center gap-2">
                <input value={p.label} onChange={e => setPago(p.id, 'label', e.target.value)} placeholder="Ej: 50% al hacer pedido"
                  className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-sm" />
                <div className="flex items-center gap-1">
                  <input type="number" value={p.percent} onChange={e => setPago(p.id, 'percent', e.target.value)}
                    className="w-16 px-2 py-1.5 border border-slate-200 rounded-lg text-sm text-right" />
                  <span className="text-xs text-slate-400">%</span>
                </div>
                <span className="w-32 text-right text-sm font-bold text-slate-700">{eur(totalGeneral * (Number(p.percent) || 0) / 100)}</span>
                <button onClick={() => removePago(p.id)} className="p-1.5 text-slate-300 hover:text-red-500"><Trash2 size={14} /></button>
              </div>
            ))}
            <button onClick={addPago} className="flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"><Plus size={14} /> Añadir plazo</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumenCocinas;
