/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { ChefHat, Sparkles, Image as ImageIcon, Loader, Upload, Download, Maximize2, X, Trash2, FolderOpen, Save, AlertTriangle, Zap } from 'lucide-react';
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
  const [savedId, setSavedId] = useState(null);
  const [designs, setDesigns] = useState(null);
  const [savingD, setSavingD] = useState(false);
  const [compare, setCompare] = useState(false);          // plano original vs render
  const [editRefImage, setEditRefImage] = useState(null); // elemento pegado (puerta, tirador…)
  const [aiCredits, setAiCredits] = useState(null);

  const fetchCredits = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/my-credits`, { headers: authH() });
      if (r.ok) setAiCredits(await r.json());
    } catch { /* silencioso */ }
  }, []);
  useEffect(() => { fetchCredits(); }, [fetchCredits]);

  const guardarDiseno = async () => {
    // Si no se han rellenado, se piden aquí mismo: el diseño debe quedar
    // guardado con cliente y referencia para poder localizarlo.
    let cli = cliente, rf = ref;
    if (!cli.trim()) { cli = (window.prompt('Nombre del cliente para guardar el diseño:', cliente) || '').trim(); if (cli) setCliente(cli); }
    if (!rf.trim()) { rf = (window.prompt('Referencia del proyecto (opcional):', ref) || '').trim(); if (rf) setRef(rf); }
    setSavingD(true);
    try {
      const r = await fetch(`${API_URL}/api/cocinasai/designs`, { method: 'POST', headers: authH(), body: JSON.stringify({ id: savedId || undefined, cliente: cli, ref: rf, kitchenType, style, notes, renders, plans }) });
      const d = await r.json(); if (!r.ok) throw new Error(d.detail || 'Error');
      if (d.design?.id) setSavedId(d.design.id);
      alert('✅ Diseño guardado.');
    } catch (e) { alert('No se pudo guardar: ' + (e.message || '')); }
    finally { setSavingD(false); }
  };
  const openDesigns = async () => { try { const r = await fetch(`${API_URL}/api/cocinasai/designs`, { headers: authH() }); const d = await r.json(); setDesigns(d.designs || []); } catch { setDesigns([]); } };
  const loadDesign = async (id) => {
    try {
      const r = await fetch(`${API_URL}/api/cocinasai/designs/${id}`, { headers: authH() }); const d = await r.json(); if (!r.ok) throw new Error();
      setCliente(d.cliente || ''); setRef(d.ref || ''); setKitchenType(d.kitchenType || 'Cocina Sola'); setStyle(d.style || 'Moderno'); setNotes(d.notes || '');
      setRenders(d.renders || []); setPlans(d.plans || []); setSel(0); setSavedId(d.id); setDesigns(null);
    } catch { alert('No se pudo abrir el diseño.'); }
  };
  const deleteDesign = async (id) => { if (!window.confirm('¿Eliminar este diseño?')) return; try { await fetch(`${API_URL}/api/cocinasai/designs/${id}`, { method: 'DELETE', headers: authH() }); setDesigns(ds => (ds || []).filter(x => x.id !== id)); } catch {} };

  const readFile = (f) => new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(String(fr.result)); fr.onerror = () => res(null); fr.readAsDataURL(f); });
  const addPlans = async (files) => {
    const arr = [];
    for (const f of files) { const b = await readFile(f); if (b) arr.push(b); }
    setPlans(p => [...p, ...arr]);
  };

  // Reduce una imagen (foto/captura grande) antes de usarla: evita payloads
  // enormes que revientan el guardado o la generación.
  const shrink = (dataUrl, maxDim = 1600) => new Promise((resolve) => {
    if (!String(dataUrl).startsWith('data:image')) return resolve(dataUrl);
    const im = new window.Image();
    im.onload = () => {
      try {
        const sc = Math.min(1, maxDim / Math.max(im.width, im.height));
        if (sc >= 1) return resolve(dataUrl);
        const c = document.createElement('canvas');
        c.width = Math.round(im.width * sc); c.height = Math.round(im.height * sc);
        c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
        resolve(c.toDataURL('image/jpeg', 0.87));
      } catch (_) { resolve(dataUrl); }
    };
    im.onerror = () => resolve(dataUrl);
    im.src = dataUrl;
  });

  // Ctrl+V en cualquier parte: si aún NO hay render, la imagen pegada entra como
  // PLANO; si ya hay render, entra como ELEMENTO a incorporar (puerta, tirador…).
  React.useEffect(() => {
    const onPaste = async (e) => {
      const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items || [];
      for (const it of items) {
        if (it.type && it.type.startsWith('image/')) {
          const file = it.getAsFile();
          if (!file) continue;
          e.preventDefault();
          const b64 = await shrink(await readFile(file));
          if (!b64) return;
          setRenders(rs => {
            if (rs.length) setEditRefImage(b64);   // elemento para la edición
            else setPlans(p => [...p, b64]);        // plano/croquis de partida
            return rs;
          });
          return;
        }
      }
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
    // eslint-disable-next-line
  }, []);

  const generar = async () => {
    setLoading(true); setError('');
    try {
      const r = await fetch(`${API_URL}/api/cocinasai/design`, { method: 'POST', headers: authH(), body: JSON.stringify({ images: plans, kitchenType, style, notes }) });
      const d = await r.json();
      if (r.status === 402) throw new Error(d.detail || 'Has agotado tus créditos de IA este mes. Contacta con tu administrador para ampliar.');
      if (!r.ok) throw new Error(d.detail || 'Error');
      setRenders(rs => { const n = [...rs, d.imageUrl]; setSel(n.length - 1); return n; });
      fetchCredits(); // Actualizar contador tras generar
    } catch (e) { setError(e.message || 'No se pudo generar el render.'); }
    finally { setLoading(false); }
  };
  const editar = async () => {
    if ((!editText.trim() && !editRefImage) || !renders.length) return;
    setLoading(true); setError('');
    try {
      const instruction = editText.trim()
        || 'Incorpora a la cocina el elemento de la imagen adjunta respetando su forma, color y acabado.';
      const r = await fetch(`${API_URL}/api/cocinasai/edit`, { method: 'POST', headers: authH(), body: JSON.stringify({ previousImageBase64: renders[sel], instruction, elementImageBase64: editRefImage || undefined }) });
      const d = await r.json();
      if (r.status === 402) throw new Error(d.detail || 'Has agotado tus créditos de IA este mes. Contacta con tu administrador para ampliar.');
      if (!r.ok) throw new Error(d.detail || 'Error');
      setRenders(rs => { const n = [...rs, d.imageUrl]; setSel(n.length - 1); return n; });
      setEditText(''); setEditRefImage(null);
      fetchCredits(); // Actualizar contador tras editar
    } catch (e) { setError(e.message || 'No se pudo editar el render.'); }
    finally { setLoading(false); }
  };
  const descargar = () => {
    if (!renders[sel]) return;
    const a = document.createElement('a'); a.href = renders[sel]; a.download = `cocina_${(ref || cliente || style).replace(/\s+/g, '_')}_${Date.now()}.png`; a.click();
  };
  const delRender = (i) => setRenders(rs => { const n = rs.filter((_, j) => j !== i); setSel(Math.max(0, Math.min(sel, n.length - 1))); return n; });
  const nuevo = () => { if (renders.length && !window.confirm('¿Empezar de cero? Se perderán los renders no descargados.')) return; setRenders([]); setPlans([]); setNotes(''); setCliente(''); setRef(''); setSel(0); setError(''); setSavedId(null); setEditRefImage(null); setCompare(false); };

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-24 bg-[#eef2ff] overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 text-white px-4 py-3 mb-4 shadow-lg flex items-center gap-3 flex-wrap">
        <h1 className="ml-14 sm:ml-2 text-base sm:text-lg font-black flex items-center gap-2"><ChefHat size={18} /> Cocinas IA 2 · Render desde plano</h1>
        {/* Widget de créditos de IA */}
        {aiCredits && (
          <span
            title="Créditos de IA disponibles este mes"
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-black ${
              aiCredits.ilimitado
                ? 'bg-white/20 text-white'
                : (aiCredits.restantes <= 0 ? 'bg-red-900/60 text-red-100' : 'bg-white/20 text-white')
            }`}
          >
            <Zap size={11} />
            {aiCredits.ilimitado ? 'Ilimitado' : `${aiCredits.restantes}/${aiCredits.asignados} renders`}
          </span>
        )}
        <div className="ml-auto flex items-center gap-1.5 flex-wrap">
          <button onClick={openDesigns} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-xs font-bold"><FolderOpen size={14} /> Mis diseños</button>
          <button onClick={guardarDiseno} disabled={savingD || !renders.length} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-xs font-bold disabled:opacity-50">{savingD ? <Loader size={14} className="animate-spin" /> : <Save size={14} />} Guardar</button>
          <button onClick={nuevo} className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-orange-700 rounded-lg text-xs font-bold hover:bg-orange-50"><X size={14} /> Nuevo</button>
        </div>
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
          {error && (
            <div className={`flex items-start gap-2 rounded-xl px-3 py-2 text-xs font-semibold ${
              error.includes('créditos') || error.includes('agotado')
                ? 'bg-red-50 border border-red-200 text-red-700'
                : 'bg-rose-50 text-rose-600'
            }`}>
              <AlertTriangle size={13} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          <p className="text-[10px] text-slate-400">Sin planos también genera una cocina de ejemplo con el estilo elegido. El render por IA consume créditos del motor de render.</p>
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
                  {plans.length > 0 && (
                    <button onClick={() => setCompare(true)} className="px-2.5 py-2 bg-black/50 text-white rounded-lg hover:bg-black/70 text-[11px] font-bold" title="Comparar plano original vs render">⇆ Comparar</button>
                  )}
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
              <div className="flex gap-2 mt-2 items-center flex-wrap">
                {editRefImage && (
                  <div className="relative shrink-0">
                    <img src={editRefImage} alt="Elemento" className="h-10 w-10 object-cover rounded-lg border-2 border-orange-300" title="Elemento pegado: se incorporará a la cocina" />
                    <button onClick={() => setEditRefImage(null)} className="absolute -top-1.5 -right-1.5 bg-rose-500 text-white rounded-full p-0.5" title="Quitar elemento"><X size={10} /></button>
                  </div>
                )}
                <input value={editText} onChange={e => setEditText(e.target.value)}
                  placeholder={editRefImage ? "Opcional: dónde/cómo colocar el elemento pegado…" : "Editar: 'encimera de mármol'… o pega una imagen (Ctrl+V) de una puerta/detalle"}
                  className="flex-1 min-w-[160px] px-3 py-2 border border-slate-200 rounded-lg text-sm" onKeyDown={e => { if (e.key === 'Enter') editar(); }} />
                <button onClick={editar} disabled={loading || (!editText.trim() && !editRefImage)} className="px-3 py-2 bg-slate-800 text-white rounded-lg text-sm font-bold disabled:opacity-50">Editar</button>
              </div>
            </>
          )}
        </div>
      </div>

      {Array.isArray(designs) && (
        <div className="fixed inset-0 bg-black/50 z-[190] flex items-center justify-center p-4" onClick={() => setDesigns(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-800">Mis diseños de cocina</h3>
              <button onClick={() => setDesigns(null)} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {designs.length === 0 ? <p className="text-sm text-slate-400 text-center py-8">Aún no has guardado diseños.</p> : designs.map(o => (
                <div key={o.id} className="flex items-center gap-3 border border-slate-200 rounded-xl p-2 mb-2 hover:bg-slate-50">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 text-sm truncate">{o.cliente || 'Sin cliente'}{o.ref ? ` · ${o.ref}` : ''}</p>
                    <p className="text-[10px] text-slate-400">{o.style} · {o.kitchenType} · {o.updatedAt ? new Date(o.updatedAt).toLocaleDateString('es-ES') : ''}</p>
                  </div>
                  <button onClick={() => loadDesign(o.id)} className="px-3 py-1.5 bg-orange-500 text-white rounded-lg text-xs font-bold hover:bg-orange-600">Abrir</button>
                  <button onClick={() => deleteDesign(o.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={15} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Comparativa: plano/croquis original vs render */}
      {compare && renders[sel] && (
        <div className="fixed inset-0 bg-black/90 z-[200] flex flex-col items-center justify-center p-4 gap-3" onClick={() => setCompare(false)}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-6xl" onClick={e => e.stopPropagation()}>
            <div className="bg-white rounded-xl p-2 flex flex-col">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 px-1 pb-1">Plano / croquis original</p>
              <img src={plans[0]} alt="Plano original" className="w-full max-h-[70vh] object-contain rounded-lg bg-slate-50" />
            </div>
            <div className="bg-white rounded-xl p-2 flex flex-col">
              <p className="text-[10px] font-black uppercase tracking-widest text-orange-600 px-1 pb-1">Render IA</p>
              <img src={renders[sel]} alt="Render" className="w-full max-h-[70vh] object-contain rounded-lg bg-slate-50" />
            </div>
          </div>
          <button onClick={() => setCompare(false)} className="absolute top-4 right-4 p-2 bg-white/20 text-white rounded-xl"><X size={22} /></button>
        </div>
      )}

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
