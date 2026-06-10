/**
 * Luiggi Floor — división de suelo SPC porcelánico.
 * 3 colores (Roble Volare, Roble Fusión, Roble Vera) en fichas llamativas.
 * Presupuestador por m²/paquetes (1 paquete = 2,787 m²) y STOCK real (admin).
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { jsPDF } from 'jspdf';
import {
  Layers, Calculator, Package, Boxes, Loader, Printer, Plus, Minus,
  Save, CheckCircle2, AlertTriangle, Warehouse, Download, FileText, Trash2, Upload, Share2,
} from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const m2fmt = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} m²`;

const LuiggiFloor = ({ currentUser }) => {
  const isAdmin = !!currentUser?.isAdmin;
  const [items, setItems] = useState([]);
  const [m2pp, setM2pp] = useState(2.787);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState(null);          // color seleccionado para presupuestar
  const [mode, setMode] = useState('m2');         // 'm2' | 'paq'
  const [value, setValue] = useState('');
  const [descuento, setDescuento] = useState(0);
  const [cliente, setCliente] = useState('');
  const [edit, setEdit] = useState({});           // edición admin {id:{pricePerM2,stockPackages}}
  const [savingId, setSavingId] = useState('');
  const [docs, setDocs] = useState([]);           // catálogos descargables
  const [uploadingDoc, setUploadingDoc] = useState(false);

  const loadDocs = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/floor/docs`, { headers: authHeaders() });
      if (r.ok) { const j = await r.json(); setDocs(j.items || []); }
    } catch { /* noop */ }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/floor/products`, { headers: authHeaders() });
      if (r.ok) { const j = await r.json(); setItems(j.items || []); setM2pp(j.m2PerPackage || 2.787); }
      await loadDocs();
    } catch { /* noop */ } finally { setLoading(false); }
  }, [loadDocs]);

  const docUrl = (id, dl) => `${API_URL}/api/floor/docs/${id}/file${dl ? '?download=true' : ''}`;

  const uploadDoc = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setUploadingDoc(true);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(fr.result); fr.onerror = rej;
        fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/floor/docs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ name: file.name.replace(/\.pdf$/i, ''), fileBase64: b64, mime: file.type || 'application/pdf' }),
      });
      if (r.ok) await loadDocs(); else alert('No se pudo subir el catálogo');
    } catch (err) { alert('Error al subir: ' + err.message); }
    finally { setUploadingDoc(false); }
  };

  const delDoc = async (id) => {
    if (!window.confirm('¿Eliminar este catálogo?')) return;
    await fetch(`${API_URL}/api/floor/docs/${id}`, { method: 'DELETE', headers: authHeaders() });
    loadDocs();
  };

  const shareDocWhatsApp = (d) => {
    const url = docUrl(d.id, false);
    const t = `*LUIGGI FLOOR* — Catálogo: ${d.name}\nDescárgalo aquí: ${url}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(t)}`, '_blank');
  };

  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (!sel && items.length) setSel(items[0]); }, [items, sel]);

  const selected = useMemo(() => items.find(i => i.id === sel?.id) || sel, [items, sel]);

  // ── Cálculo del presupuesto ──
  const calc = useMemo(() => {
    const v = parseFloat(value) || 0;
    let paquetes, m2req;
    if (mode === 'm2') { m2req = v; paquetes = v > 0 ? Math.ceil(v / m2pp) : 0; }
    else { paquetes = Math.ceil(v); m2req = v * m2pp; }
    const m2reales = +(paquetes * m2pp).toFixed(3);
    const precioM2 = Number(selected?.pricePerM2) || 0;
    const subtotal = +(m2reales * precioM2).toFixed(2);
    const dto = +(subtotal * (Number(descuento) || 0) / 100).toFixed(2);
    const base = +(subtotal - dto).toFixed(2);
    const iva = +(base * 0.21).toFixed(2);
    const total = +(base + iva).toFixed(2);
    const stock = Number(selected?.stockPackages) || 0;
    return { paquetes, m2req, m2reales, precioM2, subtotal, dto, base, iva, total, stock,
             falta: Math.max(0, paquetes - stock) };
  }, [value, mode, m2pp, selected, descuento]);

  // ── Admin: guardar precio/stock ──
  const saveEdit = async (it) => {
    const e = edit[it.id] || {};
    setSavingId(it.id);
    try {
      const r = await fetch(`${API_URL}/api/floor/products/${it.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          pricePerM2: e.pricePerM2 ?? it.pricePerM2,
          stockPackages: e.stockPackages ?? it.stockPackages,
        }),
      });
      if (r.ok) await load();
    } catch { alert('No se pudo guardar'); } finally { setSavingId(''); }
  };
  const adjustStock = async (it, delta) => {
    try {
      await fetch(`${API_URL}/api/floor/products/${it.id}/stock`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ delta }),
      });
      await load();
    } catch { /* noop */ }
  };

  // ── Imprimir oferta (PDF) ──
  const printOffer = () => {
    if (!selected || calc.paquetes <= 0) { alert('Selecciona color e indica metros o paquetes'); return; }
    const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
    const W = pdf.internal.pageSize.getWidth();
    pdf.setFillColor(24, 24, 27); pdf.rect(0, 0, W, 28, 'F');
    pdf.setTextColor(202, 169, 104); pdf.setFontSize(10); pdf.text('LUIGGI FLOOR', 14, 11);
    pdf.setTextColor(255); pdf.setFontSize(16); pdf.text('Oferta de suelo SPC', 14, 20);
    pdf.setTextColor(60); pdf.setFontSize(10);
    let y = 40;
    pdf.text(`Cliente: ${cliente || '—'}`, 14, y); y += 6;
    pdf.text(`Fecha: ${new Date().toLocaleDateString('es-ES')}`, 14, y); y += 10;
    pdf.setFontSize(13); pdf.setTextColor(20);
    pdf.text(`${selected.name}`, 14, y); y += 6;
    pdf.setFontSize(10); pdf.setTextColor(90);
    pdf.text(`${selected.dims}`, 14, y); y += 10;
    const rows = [
      ['Paquetes', `${calc.paquetes} (${m2pp} m²/paq.)`],
      ['Superficie servida', m2fmt(calc.m2reales)],
      ['Precio/m²', eur(calc.precioM2)],
      ['Subtotal', eur(calc.subtotal)],
      ['Descuento', `${descuento}%  (−${eur(calc.dto)})`],
      ['Base', eur(calc.base)],
      ['IVA 21%', eur(calc.iva)],
    ];
    pdf.setFontSize(11); pdf.setTextColor(40);
    rows.forEach(([k, v]) => { pdf.text(k, 16, y); pdf.text(String(v), W - 16, y, { align: 'right' }); y += 7; });
    pdf.setDrawColor(202, 169, 104); pdf.line(14, y, W - 14, y); y += 8;
    pdf.setFontSize(15); pdf.setTextColor(24, 24, 27);
    pdf.text('TOTAL', 16, y); pdf.text(eur(calc.total), W - 16, y, { align: 'right' });
    pdf.save(`Oferta_LuiggiFloor_${selected.name.replace(/\s+/g, '_')}.pdf`);
  };

  const shareWhatsApp = () => {
    if (!selected || calc.paquetes <= 0) { alert('Indica metros o paquetes'); return; }
    const t = `*LUIGGI FLOOR — Oferta suelo SPC*\n${selected.name} (${selected.dims})\n`
      + `\nPaquetes: ${calc.paquetes} (${m2pp} m²/paq)\nSuperficie: ${m2fmt(calc.m2reales)}\n`
      + `Precio/m²: ${eur(calc.precioM2)}\nSubtotal: ${eur(calc.subtotal)}\n`
      + (descuento ? `Descuento ${descuento}%: −${eur(calc.dto)}\n` : '')
      + `IVA 21%: ${eur(calc.iva)}\n*TOTAL: ${eur(calc.total)}*`;
    window.open(`https://wa.me/?text=${encodeURIComponent(t)}`, '_blank');
  };

  return (
    <div className="h-full overflow-auto bg-gradient-to-br from-zinc-900 to-zinc-800">
      {/* Cabecera */}
      <div className="px-4 sm:px-6 py-5 flex items-center gap-3 flex-wrap">
        <div className="w-12 h-12 rounded-2xl bg-amber-500/15 ring-1 ring-amber-400/40 flex items-center justify-center text-amber-300"><Layers size={24} /></div>
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">LUIGGI <span className="text-amber-400">FLOOR</span></h1>
          <p className="text-xs text-zinc-400">Suelo SPC porcelánico · 1 paquete = {m2pp} m²</p>
        </div>
      </div>

      <div className="px-4 sm:px-6 pb-8 max-w-6xl mx-auto">
        {loading ? (
          <div className="flex items-center justify-center py-24 text-zinc-400"><Loader className="animate-spin" size={30} /></div>
        ) : (
          <>
            {/* Fichas de color */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              {items.map(it => {
                const active = selected?.id === it.id;
                return (
                  <button key={it.id} onClick={() => setSel(it)}
                    className={`group text-left rounded-3xl overflow-hidden transition-all ${active ? 'ring-4 ring-amber-400 scale-[1.02]' : 'ring-1 ring-white/10 hover:ring-amber-400/50'}`}>
                    {/* Muestra de madera */}
                    <div className="h-40 relative" style={{ background: it.image ? undefined : `linear-gradient(135deg, ${it.swatchFrom}, ${it.swatchTo})` }}>
                      {it.image && <img src={it.image} alt={it.name} className="w-full h-full object-cover" />}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                      {active && <div className="absolute top-3 right-3 bg-amber-400 text-zinc-900 rounded-full p-1.5"><CheckCircle2 size={16} /></div>}
                      <div className="absolute bottom-3 left-4 right-4">
                        <p className="text-white font-black text-lg drop-shadow uppercase tracking-wide">{it.name}</p>
                        <p className="text-white/80 text-[11px]">{it.dims}</p>
                      </div>
                    </div>
                    <div className="bg-zinc-800/80 px-4 py-3 flex items-center justify-between">
                      <div>
                        <p className="text-[10px] text-zinc-400 uppercase">Precio/m²</p>
                        <p className="text-amber-300 font-black">{Number(it.pricePerM2) ? eur(it.pricePerM2) : '— a definir'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-zinc-400 uppercase">Stock</p>
                        <p className="text-white font-bold text-sm">{Math.floor(it.stockPackages)} paq · {m2fmt((it.stockPackages || 0) * m2pp)}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Presupuestador */}
            <div className="bg-white rounded-3xl p-5 sm:p-6 shadow-xl">
              <div className="flex items-center gap-2 mb-4">
                <Calculator size={18} className="text-amber-600" />
                <h2 className="font-black text-slate-800 uppercase text-sm">Presupuestador {selected ? `· ${selected.name}` : ''}</h2>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {/* Entrada */}
                <div className="space-y-3">
                  <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="👤 Nombre del cliente…"
                    className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-amber-500" />
                  <div className="flex gap-2">
                    <button onClick={() => setMode('m2')} className={`flex-1 py-2 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 ${mode === 'm2' ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-600'}`}><Boxes size={14} /> Por m²</button>
                    <button onClick={() => setMode('paq')} className={`flex-1 py-2 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 ${mode === 'paq' ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-600'}`}><Package size={14} /> Por paquetes</button>
                  </div>
                  <div>
                    <label className="text-[11px] font-black text-slate-400 uppercase">{mode === 'm2' ? 'Metros cuadrados necesarios' : 'Número de paquetes'}</label>
                    <input value={value} onChange={e => setValue(e.target.value)} type="number" min="0" step={mode === 'm2' ? '0.1' : '1'} placeholder="0"
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl text-2xl font-black text-slate-800 focus:outline-none focus:border-amber-500" />
                  </div>
                  <div>
                    <label className="text-[11px] font-black text-slate-400 uppercase">Descuento %</label>
                    <input value={descuento} onChange={e => setDescuento(parseFloat(e.target.value) || 0)} type="number" min="0" max="100"
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-amber-500" />
                  </div>
                </div>

                {/* Resultado */}
                <div className="bg-zinc-900 rounded-2xl p-5 text-white">
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-[10px] text-zinc-400 uppercase">Paquetes</p>
                      <p className="text-2xl font-black text-amber-400">{calc.paquetes}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-[10px] text-zinc-400 uppercase">Superficie servida</p>
                      <p className="text-2xl font-black">{m2fmt(calc.m2reales)}</p>
                    </div>
                  </div>
                  {mode === 'm2' && calc.paquetes > 0 && calc.m2reales > calc.m2req + 0.001 && (
                    <p className="text-[11px] text-amber-300 mb-2">Se sirven {m2fmt(calc.m2reales)} (paquete completo); pediste {m2fmt(calc.m2req)}.</p>
                  )}
                  <div className="space-y-1.5 text-sm border-t border-white/10 pt-3">
                    <div className="flex justify-between text-zinc-300"><span>Subtotal ({eur(calc.precioM2)}/m²)</span><span className="font-mono">{eur(calc.subtotal)}</span></div>
                    {descuento > 0 && <div className="flex justify-between text-zinc-300"><span>Descuento {descuento}%</span><span className="font-mono">−{eur(calc.dto)}</span></div>}
                    <div className="flex justify-between text-zinc-300"><span>IVA 21%</span><span className="font-mono">{eur(calc.iva)}</span></div>
                    <div className="flex justify-between items-center pt-2 border-t border-white/10">
                      <span className="text-xs font-black uppercase text-amber-300">Total</span>
                      <span className="text-2xl font-black text-amber-400">{eur(calc.total)}</span>
                    </div>
                  </div>
                  {/* Stock */}
                  {calc.paquetes > 0 && (
                    calc.falta > 0
                      ? <p className="mt-3 text-[12px] text-red-300 flex items-center gap-1.5"><AlertTriangle size={14} /> Stock insuficiente: faltan {calc.falta} paquete(s) (hay {Math.floor(calc.stock)}).</p>
                      : <p className="mt-3 text-[12px] text-emerald-300 flex items-center gap-1.5"><CheckCircle2 size={14} /> Stock disponible ({Math.floor(calc.stock)} paq.).</p>
                  )}
                  <div className="grid grid-cols-2 gap-2 mt-4">
                    <button onClick={printOffer} className="py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-900 rounded-xl text-xs font-black flex items-center justify-center gap-1.5"><Printer size={14} /> Oferta PDF</button>
                    <button onClick={shareWhatsApp} className="py-2.5 bg-green-600 hover:bg-green-700 rounded-xl text-xs font-black flex items-center justify-center gap-1.5">WhatsApp</button>
                  </div>
                </div>
              </div>
            </div>

            {/* Catálogos y material descargable */}
            <div className="bg-white rounded-3xl p-5 mt-6 shadow-xl">
              <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <FileText size={18} className="text-amber-600" />
                  <h2 className="font-black text-slate-800 uppercase text-sm">Catálogos y material</h2>
                </div>
                {isAdmin && (
                  <label className={`px-4 py-2 rounded-xl font-bold text-xs flex items-center gap-2 cursor-pointer ${uploadingDoc ? 'bg-amber-200 text-amber-500' : 'bg-amber-500 hover:bg-amber-600 text-zinc-900'}`}>
                    <Upload size={14} className={uploadingDoc ? 'animate-pulse' : ''} />
                    {uploadingDoc ? 'Subiendo…' : 'Subir catálogo (PDF)'}
                    <input type="file" accept="application/pdf,image/*" className="hidden" onChange={uploadDoc} disabled={uploadingDoc} />
                  </label>
                )}
              </div>
              {docs.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">
                  {isAdmin ? 'Sube el catálogo en PDF para poder descargarlo y compartirlo con clientes.' : 'Aún no hay catálogos disponibles.'}
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {docs.map(d => (
                    <div key={d.id} className="flex items-center gap-3 border border-slate-200 rounded-2xl p-3 hover:border-amber-300 transition-colors">
                      <div className="w-10 h-10 rounded-xl bg-red-50 text-red-500 flex items-center justify-center shrink-0"><FileText size={20} /></div>
                      <div className="min-w-0 flex-1">
                        <p className="font-bold text-slate-800 text-sm truncate">{d.name}</p>
                        <p className="text-[11px] text-slate-400">{d.size ? `${(d.size / 1024 / 1024).toFixed(1)} MB · ` : ''}PDF</p>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <a href={docUrl(d.id, true)} target="_blank" rel="noreferrer" title="Descargar" className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600"><Download size={15} /></a>
                        <button onClick={() => shareDocWhatsApp(d)} title="Compartir por WhatsApp" className="w-8 h-8 rounded-lg bg-green-100 hover:bg-green-200 flex items-center justify-center text-green-700"><Share2 size={15} /></button>
                        {isAdmin && <button onClick={() => delDoc(d.id)} title="Eliminar" className="w-8 h-8 rounded-lg hover:bg-red-50 flex items-center justify-center text-slate-300 hover:text-red-500"><Trash2 size={15} /></button>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Gestión de stock (admin) */}
            {isAdmin && (
              <div className="bg-white rounded-3xl p-5 mt-6 shadow-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Warehouse size={18} className="text-amber-600" />
                  <h2 className="font-black text-slate-800 uppercase text-sm">Gestión de stock y precios</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100 text-slate-500">
                      <tr>
                        <th className="text-left p-2.5 text-xs font-black uppercase">Color</th>
                        <th className="text-right p-2.5 text-xs font-black uppercase">Precio/m² (€)</th>
                        <th className="text-right p-2.5 text-xs font-black uppercase">Stock (paquetes)</th>
                        <th className="text-center p-2.5 text-xs font-black uppercase">Ajuste rápido</th>
                        <th className="p-2.5"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {items.map(it => {
                        const e = edit[it.id] || {};
                        return (
                          <tr key={it.id}>
                            <td className="p-2.5 font-bold text-slate-800 flex items-center gap-2">
                              <span className="w-5 h-5 rounded" style={{ background: `linear-gradient(135deg, ${it.swatchFrom}, ${it.swatchTo})` }} /> {it.name}
                            </td>
                            <td className="p-2.5 text-right">
                              <input type="number" step="0.01" defaultValue={it.pricePerM2}
                                onChange={ev => setEdit(p => ({ ...p, [it.id]: { ...p[it.id], pricePerM2: parseFloat(ev.target.value) || 0 } }))}
                                className="w-24 text-right px-2 py-1 border border-slate-200 rounded-lg font-mono" />
                            </td>
                            <td className="p-2.5 text-right">
                              <input type="number" step="0.001" defaultValue={it.stockPackages}
                                onChange={ev => setEdit(p => ({ ...p, [it.id]: { ...p[it.id], stockPackages: parseFloat(ev.target.value) || 0 } }))}
                                className="w-24 text-right px-2 py-1 border border-slate-200 rounded-lg font-mono" />
                            </td>
                            <td className="p-2.5">
                              <div className="flex items-center justify-center gap-1">
                                <button onClick={() => adjustStock(it, -1)} className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center"><Minus size={13} /></button>
                                <button onClick={() => adjustStock(it, 1)} className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center"><Plus size={13} /></button>
                              </div>
                            </td>
                            <td className="p-2.5 text-right">
                              <button onClick={() => saveEdit(it)} disabled={savingId === it.id}
                                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-zinc-900 rounded-lg text-xs font-bold inline-flex items-center gap-1">
                                {savingId === it.id ? <Loader size={13} className="animate-spin" /> : <Save size={13} />} Guardar
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <p className="text-[11px] text-slate-400 mt-2">El stock se descuenta manualmente con −/+ o editando los paquetes. 1 paquete = {m2pp} m².</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default LuiggiFloor;
