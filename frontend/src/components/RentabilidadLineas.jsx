import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText, Upload, Sparkles, Plus, Trash2, X, Save, Euro,
  Receipt, ClipboardList, FileCheck, Eye, Loader2, RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TABS = [
  { key: 'presupuesto', label: 'Presupuesto', icon: ClipboardList },
  { key: 'pedido', label: 'Pedido', icon: Receipt },
  { key: 'factura', label: 'Factura de venta', icon: FileCheck },
];

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

const fileToB64 = (file) => new Promise((res, rej) => {
  const fr = new FileReader();
  fr.onload = () => res(fr.result);
  fr.onerror = rej;
  fr.readAsDataURL(file);
});

// Abre un base64/data-url en una pestaña nueva (via blob, mas fiable que data: directo)
const openDoc = (dataUrl, mime) => {
  try {
    let b64 = dataUrl, m = mime || 'application/octet-stream';
    if (typeof dataUrl === 'string' && dataUrl.startsWith('data:')) {
      const comma = dataUrl.indexOf(',');
      m = dataUrl.slice(5, dataUrl.indexOf(';')) || m;
      b64 = dataUrl.slice(comma + 1);
    }
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const url = URL.createObjectURL(new Blob([bytes], { type: m }));
    window.open(url, '_blank');
  } catch (e) {
    alert('No se pudo abrir el documento');
  }
};

const RentabilidadLineas = ({ currentUser }) => {
  const [docType, setDocType] = useState('factura');
  const [fichas, setFichas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editor, setEditor] = useState(null);     // ficha en edicion
  const [viewing, setViewing] = useState(null);   // ficha en consulta (con docs)
  const [parsing, setParsing] = useState(false);
  const [matching, setMatching] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas`);
      setFichas(await r.json());
    } catch { /* noop */ } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const totals = (lines) => {
    const venta = (lines || []).reduce((s, l) => s + (Number(l.venta) || 0), 0);
    const coste = (lines || []).reduce((s, l) => s + (Number(l.coste) || 0), 0);
    const margen = venta - coste;
    return { venta, coste, margen, margenPct: venta > 0 ? (margen / venta * 100) : 0 };
  };

  // ── Subir documento de venta → IA extrae lineas ──
  const handleSaleDoc = async (e) => {
    const file = e.target.files?.[0]; e.target.value = '';
    if (!file) return;
    setParsing(true);
    try {
      const b64 = await fileToB64(file);
      const r = await fetch(`${API_URL}/api/rentabilidad/parse-sale-doc`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64 }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.error || 'No se pudo leer el documento'); return; }
      setEditor({
        ref: data.data.ref || '',
        cliente: data.data.cliente || '',
        fecha: data.data.fecha || '',
        docType,                       // manda la pestaña elegida por el usuario
        lines: data.data.lines || [],
        saleDoc: { b64, name: file.name },
        costDocs: [],
        existingDocs: [],
      });
    } catch { alert('Error al subir el documento'); }
    finally { setParsing(false); }
  };

  // ── Subir pantallazo de costes → IA empareja ──
  const handleCostShot = async (e) => {
    const file = e.target.files?.[0]; e.target.value = '';
    if (!file || !editor) return;
    setMatching(true);
    try {
      const b64 = await fileToB64(file);
      const r = await fetch(`${API_URL}/api/rentabilidad/match-line-costs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64, lines: editor.lines }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.error || 'No se pudo leer el pantallazo'); return; }
      setEditor({
        ...editor,
        lines: data.lines,
        costDocs: [...editor.costDocs, { b64, name: file.name }],
      });
    } catch { alert('Error al leer el pantallazo'); }
    finally { setMatching(false); }
  };

  const setLine = (i, field, val) => {
    const lines = [...editor.lines];
    lines[i] = { ...lines[i], [field]: field === 'concepto' || field === 'ref' ? val : (parseFloat(val) || 0) };
    setEditor({ ...editor, lines });
  };
  const addLine = () => setEditor({ ...editor, lines: [...editor.lines, { id: `ln-${Date.now()}`, ref: '', concepto: '', cantidad: 1, venta: 0, coste: 0 }] });
  const removeLine = (i) => setEditor({ ...editor, lines: editor.lines.filter((_, x) => x !== i) });

  const saveFicha = async () => {
    if (!editor) return;
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: editor.id, ref: editor.ref, cliente: editor.cliente, fecha: editor.fecha,
          docType: editor.docType, lines: editor.lines,
          createdBy: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username,
        }),
      });
      const data = await r.json();
      const fid = data?.ficha?.id;
      // Guardar los documentos subidos (venta + costes) para poder consultarlos
      if (fid) {
        const uploads = [];
        if (editor.saleDoc) uploads.push({ ...editor.saleDoc, kind: 'venta' });
        (editor.costDocs || []).forEach(d => uploads.push({ ...d, kind: 'coste' }));
        for (const u of uploads) {
          await fetch(`${API_URL}/api/rentabilidad/fichas/${fid}/docs`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileBase64: u.b64, filename: u.name, kind: u.kind }),
          });
        }
      }
      setEditor(null);
      load();
    } catch { alert('Error al guardar la ficha'); }
    finally { setSaving(false); }
  };

  const openFicha = async (id) => {
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas/${id}`);
      setViewing(await r.json());
    } catch { /* noop */ }
  };

  const viewDoc = async (fichaId, docId) => {
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas/${fichaId}/docs/${docId}`);
      const d = await r.json();
      openDoc(d.dataBase64, d.mime);
    } catch { alert('No se pudo abrir el documento'); }
  };

  const removeFicha = async (id) => {
    if (!window.confirm('¿Eliminar esta ficha y sus documentos?')) return;
    await fetch(`${API_URL}/api/rentabilidad/fichas/${id}`, { method: 'DELETE' });
    load();
  };

  const shown = fichas.filter(f => (f.docType || 'factura') === docType);
  const et = editor ? totals(editor.lines) : null;

  return (
    <div>
      {/* Pestañas: el usuario controla el estado del documento */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.key} onClick={() => setDocType(t.key)}
              className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 transition-all ${
                docType === t.key ? 'bg-emerald-600 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
              <Icon size={16} /> {t.label}
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-2">
          <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${parsing ? 'bg-purple-200 text-purple-500' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
            <Sparkles size={16} className={parsing ? 'animate-pulse' : ''} />
            {parsing ? 'Leyendo…' : 'Subir documento de venta'}
            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleSaleDoc} disabled={parsing} />
          </label>
          <button onClick={load} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Lista de fichas de la pestaña activa */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="text-left p-3 text-xs font-black uppercase">Nº / Ref</th>
              <th className="text-left p-3 text-xs font-black uppercase">Cliente</th>
              <th className="text-left p-3 text-xs font-black uppercase">Fecha</th>
              <th className="text-right p-3 text-xs font-black uppercase">Venta</th>
              <th className="text-right p-3 text-xs font-black uppercase">Coste</th>
              <th className="text-right p-3 text-xs font-black uppercase">Margen</th>
              <th className="text-center p-3 text-xs font-black uppercase">Docs</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {shown.map(f => {
              const tt = f.totals || totals(f.lines);
              return (
                <tr key={f.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => openFicha(f.id)}>
                  <td className="p-3 font-black text-indigo-700">{f.ref || '—'}</td>
                  <td className="p-3 text-slate-700">{f.cliente || '—'}</td>
                  <td className="p-3 text-slate-500">{f.fecha || '—'}</td>
                  <td className="p-3 text-right font-mono">{eur(tt.venta)}</td>
                  <td className="p-3 text-right font-mono text-orange-600">{eur(tt.coste)}</td>
                  <td className={`p-3 text-right font-mono font-black ${tt.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(tt.margen)}</td>
                  <td className="p-3 text-center text-slate-500">{f.numDocs || 0} 📎</td>
                  <td className="p-3 text-right">
                    <button onClick={(e) => { e.stopPropagation(); removeFicha(f.id); }} className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button>
                  </td>
                </tr>
              );
            })}
            {shown.length === 0 && (
              <tr><td colSpan={8} className="p-8 text-center text-slate-400">
                {loading ? 'Cargando…' : `Sin ${TABS.find(t => t.key === docType)?.label.toLowerCase()}. Sube un documento de venta para empezar.`}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Editor de ficha ── */}
      {editor && (
        <div className="fixed inset-0 bg-black/60 z-[140] flex items-center justify-center p-4" onClick={() => !saving && setEditor(null)}>
          <div className="bg-white rounded-3xl w-full max-w-4xl max-h-[92vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-emerald-600 text-white px-6 py-4 flex justify-between items-center shrink-0">
              <h2 className="text-lg font-black flex items-center gap-2"><FileText size={18} /> {TABS.find(t => t.key === editor.docType)?.label} — líneas y costes</h2>
              <button onClick={() => !saving && setEditor(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-5 overflow-y-auto">
              {/* Cabecera editable */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Nº / Ref</label>
                  <input value={editor.ref} onChange={e => setEditor({ ...editor, ref: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Cliente</label>
                  <input value={editor.cliente} onChange={e => setEditor({ ...editor, cliente: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Fecha</label>
                  <input value={editor.fecha} onChange={e => setEditor({ ...editor, fecha: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Estado</label>
                  <select value={editor.docType} onChange={e => setEditor({ ...editor, docType: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm font-bold">
                    {TABS.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
                  </select></div>
              </div>

              {/* Acciones de coste */}
              <div className="flex items-center gap-2 mb-2">
                <label className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 cursor-pointer ${matching ? 'bg-blue-200 text-blue-500' : 'bg-blue-600 text-white hover:bg-blue-700'}`}>
                  <Sparkles size={14} className={matching ? 'animate-pulse' : ''} />
                  {matching ? 'Emparejando…' : 'Subir pantallazo de costes (IA empareja)'}
                  <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleCostShot} disabled={matching} />
                </label>
                <button onClick={addLine} className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold flex items-center gap-1"><Plus size={14} /> Añadir línea</button>
              </div>

              {/* Tabla de lineas editable */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-slate-500">
                    <tr>
                      <th className="text-left p-2 text-[10px] font-black uppercase">Ref</th>
                      <th className="text-left p-2 text-[10px] font-black uppercase">Concepto</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Venta €</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Coste €</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Margen</th>
                      <th className="p-2"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {editor.lines.map((l, i) => {
                      const m = (Number(l.venta) || 0) - (Number(l.coste) || 0);
                      return (
                        <tr key={l.id || i}>
                          <td className="p-1"><input value={l.ref} onChange={e => setLine(i, 'ref', e.target.value)} className="w-20 px-1.5 py-1 border rounded text-xs" /></td>
                          <td className="p-1"><input value={l.concepto} onChange={e => setLine(i, 'concepto', e.target.value)} className="w-full px-1.5 py-1 border rounded text-xs" /></td>
                          <td className="p-1"><input type="number" step="0.01" value={l.venta} onChange={e => setLine(i, 'venta', e.target.value)} className="w-24 px-1.5 py-1 border rounded text-xs text-right" /></td>
                          <td className="p-1"><input type="number" step="0.01" value={l.coste} onChange={e => setLine(i, 'coste', e.target.value)} className={`w-24 px-1.5 py-1 border rounded text-xs text-right ${l._match ? 'bg-blue-50 border-blue-200' : ''}`} /></td>
                          <td className={`p-1 text-right font-mono font-bold ${m >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(m)}</td>
                          <td className="p-1 text-center"><button onClick={() => removeLine(i)} className="text-slate-300 hover:text-red-500"><Trash2 size={13} /></button></td>
                        </tr>
                      );
                    })}
                    {editor.lines.length === 0 && <tr><td colSpan={6} className="p-4 text-center text-slate-400 text-xs">Sin líneas</td></tr>}
                  </tbody>
                </table>
              </div>

              {/* Totales del editor */}
              {et && (
                <div className="grid grid-cols-3 gap-3 mt-4">
                  <div className="bg-indigo-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-indigo-500 font-black">Venta</p><p className="text-lg font-black text-indigo-700">{eur(et.venta)}</p></div>
                  <div className="bg-orange-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-orange-500 font-black">Coste</p><p className="text-lg font-black text-orange-700">{eur(et.coste)}</p></div>
                  <div className={`${et.margen >= 0 ? 'bg-emerald-50' : 'bg-red-50'} p-3 rounded-xl text-center`}><p className={`text-[10px] uppercase font-black ${et.margen >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>Margen ({et.margenPct.toFixed(1)}%)</p><p className={`text-lg font-black ${et.margen >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{eur(et.margen)}</p></div>
                </div>
              )}
            </div>
            <div className="p-4 border-t shrink-0">
              <button onClick={saveFicha} disabled={saving} className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2">
                {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} Guardar ficha
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Consulta de ficha (con documentos asociados) ── */}
      {viewing && (
        <div className="fixed inset-0 bg-black/60 z-[140] flex items-center justify-center p-4" onClick={() => setViewing(null)}>
          <div className="bg-white rounded-3xl w-full max-w-3xl max-h-[92vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-slate-800 text-white px-6 py-4 flex justify-between items-center shrink-0">
              <div>
                <h2 className="text-lg font-black">{viewing.ref || 'Ficha'} · {viewing.cliente}</h2>
                <p className="text-xs opacity-70">{TABS.find(t => t.key === viewing.docType)?.label} · {viewing.fecha}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => { setViewing(null); setEditor({ ...viewing, saleDoc: null, costDocs: [], existingDocs: viewing.docs || [] }); }}
                  className="px-3 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-xs font-bold">Editar</button>
                <button onClick={() => setViewing(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
              </div>
            </div>
            <div className="p-5 overflow-y-auto">
              {/* Documentos asociados */}
              <h3 className="text-xs font-black text-slate-500 uppercase mb-2">Documentos asociados</h3>
              <div className="flex flex-wrap gap-2 mb-5">
                {(viewing.docs || []).length === 0 && <p className="text-sm text-slate-400">Sin documentos.</p>}
                {(viewing.docs || []).map(d => (
                  <button key={d.id} onClick={() => viewDoc(viewing.id, d.id)}
                    className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 border ${d.kind === 'venta' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-blue-50 text-blue-700 border-blue-200'} hover:shadow`}>
                    <Eye size={14} /> {d.kind === 'venta' ? '📄 Venta' : '🧾 Coste'}: {d.filename}
                  </button>
                ))}
              </div>

              {/* Lineas */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-slate-500"><tr>
                    <th className="text-left p-2 text-[10px] font-black uppercase">Concepto</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">Venta</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">Coste</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">Margen</th>
                  </tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {(viewing.lines || []).map((l, i) => {
                      const m = (Number(l.venta) || 0) - (Number(l.coste) || 0);
                      return (<tr key={l.id || i}>
                        <td className="p-2">{l.ref ? <span className="text-slate-400 mr-1">[{l.ref}]</span> : null}{l.concepto}</td>
                        <td className="p-2 text-right font-mono">{eur(l.venta)}</td>
                        <td className="p-2 text-right font-mono text-orange-600">{eur(l.coste)}</td>
                        <td className={`p-2 text-right font-mono font-bold ${m >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(m)}</td>
                      </tr>);
                    })}
                  </tbody>
                </table>
              </div>
              {viewing.totals && (
                <div className="grid grid-cols-3 gap-3 mt-4">
                  <div className="bg-indigo-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-indigo-500 font-black">Venta</p><p className="text-lg font-black text-indigo-700">{eur(viewing.totals.venta)}</p></div>
                  <div className="bg-orange-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-orange-500 font-black">Coste</p><p className="text-lg font-black text-orange-700">{eur(viewing.totals.coste)}</p></div>
                  <div className={`${viewing.totals.margen >= 0 ? 'bg-emerald-50' : 'bg-red-50'} p-3 rounded-xl text-center`}><p className={`text-[10px] uppercase font-black ${viewing.totals.margen >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>Margen ({viewing.totals.margenPct}%)</p><p className={`text-lg font-black ${viewing.totals.margen >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{eur(viewing.totals.margen)}</p></div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RentabilidadLineas;
