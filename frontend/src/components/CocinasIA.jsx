import React, { useState } from 'react';
import { ChefHat, Sparkles, Image as ImageIcon, Loader, Upload, Download, Maximize2, X, Trash2 } from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const authH = () => ({ 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' });
const TYPES = ['Cocina Sola', 'Salón-Cocina'];
const STYLES = ['Moderno', 'Rústico', 'Minimalista', 'Industrial', 'Escandinavo'];

const CocinasIA = ({ state }) => {
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [kitchenType, setKitchenType] = useState('Cocina Sola');
  const [style, setStyle] = useState('Moderno');
  const [notes, setNotes] = useState('');
  const [plans, setPlans] = useState([]); // data URLs
  const [renders, setRenders] = useState([]);
  const [sel, setSel] = useState(0);
  const [loading, setLoading] = useState(false);
  const [editText, setEditText] = useState('');
  const [error, setError] = useState('');
  const [full, setFull] = useState(false);

  const readFile = (f) => new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(String(fr.result)); fr.onerror = () => res(null); fr.readAsDataURL(f); });
  const addPlans = async (files) => {
    const arr = [];
    for (const f of files) { const b = await readFile(f); if (b) arr.push(b); }
    setPlans(p => [...p, ...arr]);
  };

  const generar = async () => {
    setLoading(true); setError('');
    try {
      const r = await fetch(`${API_URL}/api/cocinasai/design`, { method: 'POST', headers: authH(), body: JSON.stringify({ images: plans, kitchenType, style, notes }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setRenders(rs => { const n = [...rs, d.imageUrl]; setSel(n.length - 1); return n; });
    } catch (e) { setError(e.message || 'No se pudo generar el render.'); }
    finally { setLoading(false); }
  };
  const editar = async () => {
    if (!editText.trim() || !renders.length) return;
    setLoading(true); setError('');
    try {
      const r = await fetch(`${API_URL}/api/cocinasai/edit`, { method: 'POST', headers: authH(), body: JSON.stringify({ previousImageBase64: renders[sel], instruction: editText.trim() }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setRenders(rs => { const n = [...rs, d.imageUrl]; setSel(n.length - 1); return n; });
      setEditText('');
    } catch (e) { setError(e.message || 'No se pudo editar el render.'); }
    finally { setLoading(false); }
  };
  const descargar = () => {
    if (!renders[sel]) return;
    const a = document.createElement('a'); a.href = renders[sel]; a.download = `cocina_${(ref || cliente || style).replace(/\s+/g, '_')}_${Date.now()}.png`; a.click();
  };
  const delRender = (i) => setRenders(rs => { const n = rs.filter((_, j) => j !== i); setSel(Math.max(0, Math.min(sel, n.length - 1))); return n; });
  const nuevo = () => { if (renders.length && !window.confirm('¿Empezar de cero? Se perderán los renders no descargados.')) return; setRenders([]); setPlans([]); setNotes(''); setCliente(''); setRef(''); setSel(0); setError(''); };

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-24 bg-[#eef2ff] overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 text-white px-4 py-3 mb-4 shadow-lg flex items-center gap-3 flex-wrap">
        <h1 className="ml-14 sm:ml-2 text-base sm:text-lg font-black flex items-center gap-2"><ChefHat size={18} /> Cocinas IA 2 · Render desde plano</h1>
        <button onClick={nuevo} className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-white text-orange-700 rounded-lg text-xs font-bold hover:bg-orange-50"><X size={14} /> Nuevo</button>
      </div>

      <div className="grid lg:grid-cols-[360px_1fr] gap-4 items-start">
        {/* Configuración */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente" className="px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-orange-400" />
            <input value={ref} onChange={e => setRef(e.target.value)} placeholder="Referencia" className="px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-orange-400" />
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Tipo</label>
            <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
              {TYPES.map(t => <button key={t} onClick={() => setKitchenType(t)} className={`flex-1 px-2 py-1.5 rounded-md text-xs font-bold ${kitchenType === t ? 'bg-white text-orange-700 shadow-sm' : 'text-slate-500'}`}>{t}</button>)}
            </div>
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Estilo</label>
            <div className="flex flex-wrap gap-1.5">
              {STYLES.map(s => <button key={s} onClick={() => setStyle(s)} className={`px-2.5 py-1 rounded-lg text-xs font-bold ${style === s ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>{s}</button>)}
            </div>
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Detalles (opcional)</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} placeholder="Encimera de mármol, muebles verde salvia, isla central…" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:border-orange-400 resize-none" />
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Planos / alzados</label>
            <label className="flex items-center justify-center gap-2 px-3 py-2 bg-slate-100 rounded-lg text-xs font-bold text-slate-600 cursor-pointer hover:bg-slate-200">
              <Upload size={14} /> Subir plano(s)
              <input type="file" accept="image/*,application/pdf" multiple className="hidden" onChange={e => e.target.files && addPlans([...e.target.files])} />
            </label>
            {plans.length > 0 && (
              <div className="grid grid-cols-3 gap-2 mt-2">
                {plans.map((p, i) => (
                  <div key={i} className="relative group">
                    <img src={p} alt="" className="w-full h-16 object-cover rounded-lg border border-slate-200" />
                    <button onClick={() => setPlans(ps => ps.filter((_, j) => j !== i))} className="absolute -top-1.5 -right-1.5 bg-rose-500 text-white rounded-full p-0.5"><X size={11} /></button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button onClick={generar} disabled={loading} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-orange-500 text-white rounded-xl font-black text-sm hover:bg-orange-600 disabled:opacity-50">{loading ? <Loader size={16} className="animate-spin" /> : <Sparkles size={16} />} Generar render</button>
          {error && <p className="text-xs text-rose-600 font-bold">{error}</p>}
          <p className="text-[10px] text-slate-400">Sin planos también genera una cocina de ejemplo con el estilo elegido. El render por IA consume créditos de Gemini.</p>
        </div>

        {/* Resultado */}
        <div className="bg-white rounded-2xl border border-slate-200 p-3">
          {renders.length === 0 ? (
            <div className="h-72 flex flex-col items-center justify-center text-slate-300">
              <ImageIcon size={64} strokeWidth={1} /><p className="font-black uppercase tracking-widest text-xs mt-3">Vista fotorrealista IA</p>
            </div>
          ) : (
            <>
              <div className="relative">
                <img src={renders[sel]} alt="Render cocina" className="w-full rounded-xl border border-slate-100" />
                {loading && <div className="absolute inset-0 bg-white/70 rounded-xl flex items-center justify-center"><span className="flex items-center gap-2 text-sm font-bold text-orange-700"><Loader className="animate-spin" size={18} /> Generando…</span></div>}
                <div className="absolute top-2 right-2 flex gap-1.5">
                  <button onClick={() => setFull(true)} className="p-2 bg-black/50 text-white rounded-lg hover:bg-black/70" title="Pantalla completa"><Maximize2 size={15} /></button>
                  <button onClick={descargar} className="p-2 bg-black/50 text-white rounded-lg hover:bg-black/70" title="Descargar"><Download size={15} /></button>
                </div>
              </div>
              {renders.length > 1 && (
                <div className="flex gap-2 mt-2 overflow-x-auto">
                  {renders.map((r, i) => (
                    <div key={i} className="relative group shrink-0">
                      <img src={r} onClick={() => setSel(i)} alt="" className={`h-14 w-24 object-cover rounded-lg cursor-pointer border-2 ${sel === i ? 'border-orange-500' : 'border-transparent'}`} />
                      <button onClick={() => delRender(i)} className="absolute -top-1.5 -right-1.5 bg-rose-500 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100"><X size={10} /></button>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2 mt-2">
                <input value={editText} onChange={e => setEditText(e.target.value)} placeholder="Editar: 'encimera de mármol', 'muebles verdes'…" className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" onKeyDown={e => { if (e.key === 'Enter') editar(); }} />
                <button onClick={editar} disabled={loading || !editText.trim()} className="px-3 py-2 bg-slate-800 text-white rounded-lg text-sm font-bold disabled:opacity-50">Editar</button>
              </div>
            </>
          )}
        </div>
      </div>

      {full && renders[sel] && (
        <div className="fixed inset-0 bg-black/90 z-[200] flex items-center justify-center p-4" onClick={() => setFull(false)}>
          <img src={renders[sel]} alt="Render" className="max-w-full max-h-full object-contain rounded-xl" onClick={e => e.stopPropagation()} />
          <button onClick={() => setFull(false)} className="absolute top-4 right-4 p-2 bg-white/20 text-white rounded-xl"><X size={22} /></button>
          <button onClick={descargar} className="absolute bottom-4 right-4 flex items-center gap-2 px-4 py-2 bg-white text-slate-900 rounded-xl font-bold"><Download size={16} /> Descargar</button>
        </div>
      )}
    </div>
  );
};

export default CocinasIA;
