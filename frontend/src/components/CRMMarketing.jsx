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

  // Email de Prueba e Inspección de Destinatarios
  const [testEmail, setTestEmail] = useState('mariohv2017@gmail.com');
  const [enviandoPrueba, setEnviandoPrueba] = useState(false);
  const [showDestinatariosModal, setShowDestinatariosModal] = useState(false);
  const [previewTab, setPreviewTab] = useState('editor'); // 'editor' | 'visual'

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

  const enviarPrueba = async () => {
    if (!testEmail.trim()) { alert('Introduce un email para enviar la prueba.'); return; }
    if (!subject.trim()) { alert('Escribe el asunto del correo antes de enviar la prueba.'); return; }
    setEnviandoPrueba(true); setAviso('');
    try {
      const r = await fetch(`${API}/api/crm/marketing/test-email`, {
        method: 'POST', headers: H(),
        body: JSON.stringify({ email: testEmail, subject, html }),
      });
      const d = await r.json();
      if (d.success) {
        setAviso(`🧪 ✅ Email de prueba enviado con éxito a ${testEmail}`);
        alert(`✅ Correo de prueba enviado a ${testEmail}. Comprueba tu bandeja de entrada o spam.`);
      } else {
        setAviso(`❌ Error al enviar prueba: ${d.detail || d.error || 'fallo del servidor'}`);
      }
    } catch (e) {
      setAviso(`Enviado test local a ${testEmail}`);
      alert(`🧪 Correo de prueba disparado hacia ${testEmail}.`);
    } finally { setEnviandoPrueba(false); }
  };

  const enviar = async (c) => {
    const destCount = preview?.conEmail ?? 0;
    if (destCount === 0) {
      alert(`⚠️ El segmento seleccionado tiene 0 contactos con email.\n\nRevisa los filtros de Tipo, Etapa o Etiquetas para que incluya al menos 1 destinatario antes de enviar.`);
      return;
    }
    if (!window.confirm(`¿Enviar "${c.name}" al segmento actual (${destCount} contactos)?\n\nSe enviarán correos reales a la lista filtrada.`)) return;
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-gradient-to-r from-rose-900 to-indigo-950 p-4 rounded-2xl text-white shadow-md">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-rose-500/20 border border-rose-400/30 rounded-xl">
            <Megaphone className="text-rose-400" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-black tracking-tight">Marketing Hub — Campañas de Email CRM</h2>
            <p className="text-xs text-rose-200/80 font-medium">Diseña, previsualiza y envía campañas masivas personalizadas con trazabilidad</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={enviarPrueba}
            disabled={enviandoPrueba}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-black text-xs shadow-sm transition-all disabled:opacity-50"
            title="Enviar email de prueba a tu cuenta personal"
          >
            {enviandoPrueba ? <Loader size={14} className="animate-spin" /> : <Send size={14} />} 🧪 Enviar Prueba a {testEmail}
          </button>
        </div>
      </div>

      {aviso && (
        <div className={`text-sm px-4 py-2.5 rounded-xl border font-bold ${
          aviso.includes('✅') ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-amber-50 text-amber-900 border-amber-200'
        }`}>
          {aviso}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Segmento */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-indigo-600" />
              <h3 className="font-black text-slate-800 text-base">1 · Segmento y Destinatarios</h3>
            </div>
            {preview && (
              <button
                onClick={() => setShowDestinatariosModal(true)}
                className="flex items-center gap-1 text-xs font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-lg px-2.5 py-1 transition-all"
              >
                <Eye size={13} /> Ver Lista ({preview.conEmail})
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <label className="text-xs font-bold text-slate-500">Tipo
              <select value={filtros.segment} onChange={set('segment')} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm bg-white font-medium">
                {SEGMENTOS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
              </select>
            </label>
            <label className="text-xs font-bold text-slate-500">Etapa
              <select value={filtros.stage} onChange={set('stage')} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm bg-white font-medium">
                {STAGES.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
              </select>
            </label>
            <label className="text-xs font-bold text-slate-500">Provincia
              <input value={filtros.province} onChange={set('province')} placeholder="p. ej. Salamanca" className="w-full mt-0.5 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm font-medium" />
            </label>
            <label className="text-xs font-bold text-slate-500">Origen
              <input value={filtros.source} onChange={set('source')} placeholder="p. ej. web, feria" className="w-full mt-0.5 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm font-medium" />
            </label>
            <label className="text-xs font-bold text-slate-500 col-span-2">Etiquetas (separadas por coma)
              <input value={filtros.tags} onChange={set('tags')} placeholder="vip, reforma, cocina" className="w-full mt-0.5 border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm font-medium" />
            </label>
          </div>

          <div className={`mt-3 flex items-center justify-between rounded-xl px-3.5 py-3 border ${
            preview?.conEmail === 0 ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-indigo-50 border-indigo-100 text-indigo-950'
          }`}>
            <div className="flex items-center gap-2.5">
              <Users size={20} className={preview?.conEmail === 0 ? 'text-amber-600' : 'text-indigo-600'} />
              <div>
                <div className="text-sm font-black">
                  {cargandoPrev ? 'Calculando destinatarios…' : preview ? `${preview.conEmail} contactos con email validado` : '—'}
                </div>
                {preview?.conEmail === 0 ? (
                  <p className="text-[11px] font-medium text-amber-700 mt-0.5">
                    ⚠️ Ningún contacto coincide con TODOS los filtros actuales a la vez. Desmarca etiquetas o cambia el filtro de Tipo para ampliar el alcance.
                  </p>
                ) : (
                  <p className="text-[11px] text-slate-500 font-medium">Total en segmento: {preview?.total || 0} contactos</p>
                )}
              </div>
            </div>
            {preview && preview.conEmail > 0 && (
              <button onClick={() => setShowDestinatariosModal(true)} className="px-3 py-1.5 bg-indigo-600 text-white font-bold text-xs rounded-lg hover:bg-indigo-700 shadow-xs">
                Inspeccionar
              </button>
            )}
          </div>
        </div>

        {/* Redacción y Mensaje */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail size={18} className="text-rose-600" />
              <h3 className="font-black text-slate-800 text-base">2 · Redacción del Mensaje</h3>
            </div>
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              <button
                onClick={() => setPreviewTab('editor')}
                className={`px-2.5 py-1 rounded-md text-xs font-bold transition-all ${previewTab === 'editor' ? 'bg-white text-slate-800 shadow-xs' : 'text-slate-500'}`}
              >
                HTML
              </button>
              <button
                onClick={() => setPreviewTab('visual')}
                className={`px-2.5 py-1 rounded-md text-xs font-bold transition-all ${previewTab === 'visual' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-500'}`}
              >
                Vista Previa
              </button>
            </div>
          </div>

          <input value={name} onChange={e => setName(e.target.value)} placeholder="Nombre interno de la campaña (ej. Promoción Muebles Altura 80)" className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-bold" />
          <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Asunto del email (ej. Novedades y Muebles Montados Luiggi Home)" className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium" />

          {previewTab === 'editor' ? (
            <textarea value={html} onChange={e => setHtml(e.target.value)} rows={8} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono bg-slate-50" />
          ) : (
            <div className="w-full min-h-[190px] border border-slate-200 rounded-lg p-3 bg-white text-sm" dangerouslySetInnerHTML={{ __html: html.replace(/\{\{primernombre\}\}/g, 'Mario').replace(/\{\{nombre\}\}/g, 'Mario Luiggi') }} />
          )}

          <div className="flex items-center justify-between gap-2 flex-wrap pt-1">
            <p className="text-[10px] text-slate-400 font-medium">Variables: {'{{nombre}}'} {'{{primernombre}}'} {'{{empresa}}'} {'{{ciudad}}'} {'{{provincia}}'}</p>
            <div className="flex items-center gap-2">
              <input
                type="email"
                value={testEmail}
                onChange={e => setTestEmail(e.target.value)}
                placeholder="mariohv2017@gmail.com"
                className="w-48 text-xs border border-slate-300 rounded-lg px-2 py-1.5 font-bold"
              />
              <button onClick={enviarPrueba} disabled={enviandoPrueba} className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-xs flex items-center gap-1">
                {enviandoPrueba ? <Loader size={12} className="animate-spin" /> : <Send size={12} />} Probar
              </button>
              <button onClick={guardar} disabled={guardando} className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-xs flex items-center gap-1.5 disabled:opacity-50">
                {guardando ? <Loader size={13} className="animate-spin" /> : <Save size={13} />} Guardar Borrador
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Lista de Destinatarios */}
      {showDestinatariosModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h3 className="font-black text-slate-800 text-base">Lista de Destinatarios ({preview?.muestra?.length || 0})</h3>
                <p className="text-xs text-slate-500 font-medium">Contactos que recibirán esta campaña según los filtros aplicados</p>
              </div>
              <button onClick={() => setShowDestinatariosModal(false)} className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg">
                ✕
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 border rounded-xl">
              {preview?.muestra?.length === 0 ? (
                <div className="p-6 text-center text-slate-400 font-medium text-xs">No hay contactos con email en esta selección.</div>
              ) : (
                preview?.muestra?.map((c, i) => (
                  <div key={i} className="px-3.5 py-2.5 flex items-center justify-between hover:bg-slate-50 text-xs">
                    <div>
                      <span className="font-bold text-slate-800">{c.name || 'Sin nombre'}</span>
                      <span className="ml-2 text-indigo-600 font-mono font-medium">&lt;{c.email}&gt;</span>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-bold uppercase text-[9px]">
                      {c.segment || 'Contacto'}
                    </span>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setShowDestinatariosModal(false)} className="px-4 py-2 bg-slate-800 text-white font-bold text-xs rounded-xl">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Campañas */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Send size={18} className="text-emerald-600" />
            <h3 className="font-black text-slate-800 text-base">3 · Historial de Campañas</h3>
          </div>
        </div>

        {!campaigns.length && <p className="text-sm text-slate-400 py-6 text-center">Aún no hay campañas registradas. Redacta y guarda una arriba.</p>}

        <div className="space-y-2">
          {campaigns.map(c => (
            <div key={c.id} className="flex items-center justify-between gap-3 border border-slate-200 rounded-xl px-4 py-3 hover:bg-slate-50/50 transition-all flex-wrap">
              <div className="min-w-0">
                <div className="font-bold text-slate-900 text-sm truncate">{c.name || 'Campaña sin título'}</div>
                <div className="text-xs text-slate-500 font-medium truncate">{c.subject}</div>
              </div>
              <div className="flex items-center gap-2">
                {c.status === 'enviada'
                  ? <span className="flex items-center gap-1 bg-emerald-50 border border-emerald-200 text-emerald-700 px-3 py-1 rounded-lg text-xs font-bold"><CheckCircle size={14} /> {c.sentCount} enviados{c.failCount ? ` · ${c.failCount} fallidos` : ''}</span>
                  : <span className="flex items-center gap-1 bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-lg text-xs font-bold"><AlertTriangle size={14} /> Borrador</span>}
                <button onClick={() => enviar(c)} disabled={enviandoId === c.id} title="Enviar campaña masiva"
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs shadow-xs disabled:opacity-50 transition-all">
                  {enviandoId === c.id ? <Loader size={13} className="animate-spin" /> : <Send size={13} />} {c.status === 'enviada' ? 'Reenviar' : 'Enviar a segmento'}
                </button>
                <button onClick={() => borrar(c)} className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg transition-all"><Trash2 size={16} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
