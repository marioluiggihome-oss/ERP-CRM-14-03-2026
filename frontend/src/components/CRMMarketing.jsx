/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CRMMarketing — Marketing Hub (fase 1): segmentación de la base de contactos +
 * campañas de email (SendGrid). Define un segmento con filtros, previsualiza el
 * alcance, redacta la campaña con variables ({{nombre}}, {{empresa}}…) y la envía.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Megaphone, Users, Send, Save, Trash2, Loader, Mail, Filter, Eye, CheckCircle, AlertTriangle } from 'lucide-react';
import { authHeaders } from '../services/api';

const API = process.env.REACT_APP_BACKEND_URL;
const H = () => authHeaders({ 'Content-Type': 'application/json' });

const SEGMENTOS = [
  { v: '', l: 'Todos' }, { v: 'particular', l: 'Particular' }, { v: 'profesional', l: 'Profesional' },
  { v: 'empresa', l: 'Empresa' }, { v: 'prescriptor', l: 'Prescriptor' },
];
const STAGES = [
  { v: '', l: 'Cualquier etapa' }, { v: 'lead', l: 'Lead' }, { v: 'contacted', l: 'Contactado' },
  { v: 'proposal', l: 'Propuesta' }, { v: 'won', l: 'Ganado' }, { v: 'lost', l: 'Perdido' },
];

const PLANTILLA_HTML =
  `<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#1e293b">
  <h2 style="color:#4f46e5">Hola {{primernombre}} 👋</h2>
  <p>Te escribimos desde <b>Luiggi Home</b> para contarte…</p>
  <p>Un saludo,<br/>El equipo de Luiggi Home</p>
</div>`;

export default function CRMMarketing() {
  const [filtros, setFiltros] = useState({ segment: '', stage: '', status: '', province: '', source: '', tags: '', conEmail: true });
  const [preview, setPreview] = useState(null);
  const [cargandoPrev, setCargandoPrev] = useState(false);
  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [html, setHtml] = useState(PLANTILLA_HTML);
  const [guardando, setGuardando] = useState(false);
  const [enviandoId, setEnviandoId] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [aviso, setAviso] = useState('');

  const set = (k) => (e) => setFiltros(f => ({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const cargarPreview = useCallback(async () => {
    setCargandoPrev(true);
    try {
      const r = await fetch(`${API}/api/crm/marketing/segment/preview`, { method: 'POST', headers: H(), body: JSON.stringify({ filtros }) });
      const d = await r.json();
      if (d.success) setPreview(d);
    } catch { /* noop */ } finally { setCargandoPrev(false); }
  }, [filtros]);

  const cargarCampaigns = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/crm/marketing/campaigns`, { headers: authHeaders() });
      const d = await r.json();
      if (d.success) setCampaigns(d.campaigns || []);
    } catch { /* noop */ }
  }, []);

  useEffect(() => { cargarCampaigns(); }, [cargarCampaigns]);
  useEffect(() => { const t = setTimeout(cargarPreview, 400); return () => clearTimeout(t); }, [cargarPreview]);

  const guardar = async () => {
    if (!subject.trim()) { setAviso('Pon un asunto a la campaña.'); return; }
    setGuardando(true); setAviso('');
    try {
      const r = await fetch(`${API}/api/crm/marketing/campaigns`, {
        method: 'POST', headers: H(),
        body: JSON.stringify({ name, subject, html, filtros }),
      });
      const d = await r.json();
      if (d.success) { setName(''); setSubject(''); setHtml(PLANTILLA_HTML); cargarCampaigns(); setAviso('✅ Campaña guardada como borrador.'); }
      else setAviso(d.detail || 'No se pudo guardar.');
    } catch (e) { setAviso(`Error: ${e?.message || 'red'}`); } finally { setGuardando(false); }
  };

  const enviar = async (c) => {
    const dest = preview?.conEmail ?? '?';
    if (!window.confirm(`¿Enviar "${c.name}" al segmento guardado de la campaña?\n\nSe enviará a los contactos con email del segmento. Esta acción envía correos reales.`)) return;
    setEnviandoId(c.id); setAviso('');
    try {
      const r = await fetch(`${API}/api/crm/marketing/campaigns/${c.id}/send`, { method: 'POST', headers: H(), body: JSON.stringify({}) });
      const d = await r.json();
      if (d.success) { setAviso(`✅ Enviada: ${d.sentCount} correo(s) enviados${d.failCount ? `, ${d.failCount} fallidos` : ''}.`); cargarCampaigns(); }
      else setAviso(d.detail || 'No se pudo enviar.');
    } catch (e) { setAviso(`Error: ${e?.message || 'red'}`); } finally { setEnviandoId(null); }
  };

  const borrar = async (c) => {
    if (!window.confirm(`¿Borrar la campaña "${c.name}"?`)) return;
    await fetch(`${API}/api/crm/marketing/campaigns/${c.id}`, { method: 'DELETE', headers: authHeaders() });
    cargarCampaigns();
  };

  return (
    <div className="p-4 sm:p-6 space-y-5">
      <div className="flex items-center gap-2">
        <Megaphone className="text-rose-600" size={22} />
        <h2 className="text-xl font-black text-slate-800">Marketing — Campañas de email</h2>
      </div>

      {aviso && <div className="text-sm px-3 py-2 rounded-lg bg-slate-100 text-slate-700 border border-slate-200">{aviso}</div>}

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Segmento */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3"><Filter size={16} className="text-indigo-600" /><h3 className="font-black text-slate-700">1 · Segmento</h3></div>
          <div className="grid grid-cols-2 gap-2.5">
            <label className="text-xs font-bold text-slate-500">Tipo
              <select value={filtros.segment} onChange={set('segment')} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white">
                {SEGMENTOS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
              </select>
            </label>
            <label className="text-xs font-bold text-slate-500">Etapa
              <select value={filtros.stage} onChange={set('stage')} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white">
                {STAGES.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
              </select>
            </label>
            <label className="text-xs font-bold text-slate-500">Provincia
              <input value={filtros.province} onChange={set('province')} placeholder="p. ej. Salamanca" className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
            </label>
            <label className="text-xs font-bold text-slate-500">Origen
              <input value={filtros.source} onChange={set('source')} placeholder="p. ej. web, feria" className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
            </label>
            <label className="text-xs font-bold text-slate-500 col-span-2">Etiquetas (separadas por coma)
              <input value={filtros.tags} onChange={set('tags')} placeholder="vip, reforma, cocina" className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
            </label>
          </div>
          <div className="mt-3 flex items-center justify-between bg-indigo-50 rounded-xl px-3 py-2.5">
            <div className="flex items-center gap-2 text-indigo-800">
              <Users size={18} />
              <span className="text-sm font-bold">
                {cargandoPrev ? 'Calculando…' : preview ? `${preview.conEmail} con email` : '—'}
                {preview && <span className="text-indigo-400 font-normal"> · {preview.total} en total</span>}
              </span>
            </div>
            <Eye size={16} className="text-indigo-400" />
          </div>
          {preview?.muestra?.length > 0 && (
            <div className="mt-2 text-[11px] text-slate-500 max-h-24 overflow-y-auto">
              {preview.muestra.map((c, i) => <div key={i}>· {c.name} <span className="text-slate-400">&lt;{c.email}&gt;</span></div>)}
            </div>
          )}
        </div>

        {/* Redacción */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3"><Mail size={16} className="text-rose-600" /><h3 className="font-black text-slate-700">2 · Mensaje</h3></div>
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Nombre interno de la campaña" className="w-full mb-2 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm" />
          <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Asunto del email" className="w-full mb-2 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm" />
          <textarea value={html} onChange={e => setHtml(e.target.value)} rows={8} className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-mono" />
          <p className="text-[10px] text-slate-400 mt-1">Variables: {'{{nombre}}'} {'{{primernombre}}'} {'{{empresa}}'} {'{{ciudad}}'} {'{{provincia}}'}</p>
          <button onClick={guardar} disabled={guardando} className="mt-2 flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-sm disabled:opacity-50">
            {guardando ? <Loader size={15} className="animate-spin" /> : <Save size={15} />} Guardar campaña
          </button>
        </div>
      </div>

      {/* Campañas */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
        <div className="flex items-center gap-2 mb-3"><Send size={16} className="text-emerald-600" /><h3 className="font-black text-slate-700">3 · Campañas</h3></div>
        {!campaigns.length && <p className="text-sm text-slate-400 py-4 text-center">Aún no hay campañas. Crea una arriba.</p>}
        <div className="space-y-2">
          {campaigns.map(c => (
            <div key={c.id} className="flex items-center justify-between gap-3 border border-slate-100 rounded-xl px-3 py-2.5 flex-wrap">
              <div className="min-w-0">
                <div className="font-bold text-slate-800 text-sm truncate">{c.name}</div>
                <div className="text-xs text-slate-400 truncate">{c.subject}</div>
              </div>
              <div className="flex items-center gap-2">
                {c.status === 'enviada'
                  ? <span className="flex items-center gap-1 text-emerald-600 text-xs font-bold"><CheckCircle size={14} /> {c.sentCount} enviados{c.failCount ? ` · ${c.failCount} fallidos` : ''}</span>
                  : <span className="flex items-center gap-1 text-amber-600 text-xs font-bold"><AlertTriangle size={14} /> Borrador</span>}
                <button onClick={() => enviar(c)} disabled={enviandoId === c.id} title="Enviar campaña"
                  className="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-xs disabled:opacity-50">
                  {enviandoId === c.id ? <Loader size={13} className="animate-spin" /> : <Send size={13} />} {c.status === 'enviada' ? 'Reenviar' : 'Enviar'}
                </button>
                <button onClick={() => borrar(c)} className="p-1.5 text-slate-400 hover:text-red-600"><Trash2 size={15} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
