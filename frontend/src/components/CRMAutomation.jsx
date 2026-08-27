/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CRMAutomation — Automatizaciones / Workflows (fase 4): reglas "disparador →
 * acción" sobre los contactos, evaluadas al entrar (sin email) y con botón
 * "Ejecutar ahora" (con email). Estilo Workflows de HubSpot.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Zap, Plus, Loader, Play, Trash2, X, Power } from 'lucide-react';
import { authHeaders } from '../services/api';

const API = process.env.REACT_APP_BACKEND_URL;
const H = () => authHeaders({ 'Content-Type': 'application/json' });

const TRIGGERS = [
  { v: 'lead_sin_contacto', l: 'Lead sin contacto en N días' },
  { v: 'followup_vencido', l: 'Seguimiento vencido (nextFollowUp pasado)' },
];
const ACCIONES = [
  { v: 'crear_tarea', l: 'Crear tarea de seguimiento' },
  { v: 'enviar_email', l: 'Enviar email de plantilla' },
  { v: 'cambiar_etapa', l: 'Cambiar etapa del contacto' },
];
const STAGES = ['lead', 'contacted', 'proposal', 'won', 'lost'];

const NUEVA = { name: '', active: true, trigger: 'lead_sin_contacto', action: 'crear_tarea', cooldownDays: 7,
  params: { dias: 7, texto: 'Llamar al lead: sin contacto reciente', diasFollowup: 3, stage: 'contacted', subject: '', html: '' } };

export default function CRMAutomation() {
  const [rules, setRules] = useState([]);
  const [form, setForm] = useState(null);
  const [ejecutando, setEjecutando] = useState(false);
  const [resumen, setResumen] = useState(null);

  const cargar = useCallback(async () => {
    try { const d = await fetch(`${API}/api/crm/automation/rules`, { headers: authHeaders() }).then(r => r.json());
      if (d.success) setRules(d.rules || []); } catch { /* noop */ }
  }, []);

  // Ejecuta automáticamente al entrar (sin enviar emails).
  const run = useCallback(async (incluirEmail) => {
    setEjecutando(true); setResumen(null);
    try {
      const d = await fetch(`${API}/api/crm/automation/run`, { method: 'POST', headers: H(), body: JSON.stringify({ incluirEmail }) }).then(r => r.json());
      if (d.success) setResumen(d.resumen || []);
    } catch { /* noop */ } finally { setEjecutando(false); cargar(); }
  }, [cargar]);

  useEffect(() => { cargar(); run(false); }, [cargar, run]);

  const guardar = async () => {
    if (!form.name.trim()) return;
    const url = form.id ? `${API}/api/crm/automation/rules/${form.id}` : `${API}/api/crm/automation/rules`;
    const method = form.id ? 'PATCH' : 'POST';
    const d = await fetch(url, { method, headers: H(), body: JSON.stringify(form) }).then(r => r.json());
    if (d.success) { setForm(null); cargar(); }
  };
  const toggle = async (r) => { await fetch(`${API}/api/crm/automation/rules/${r.id}`, { method: 'PATCH', headers: H(), body: JSON.stringify({ active: !r.active }) }); cargar(); };
  const borrar = async (r) => { if (!window.confirm(`¿Borrar "${r.name}"?`)) return; await fetch(`${API}/api/crm/automation/rules/${r.id}`, { method: 'DELETE', headers: authHeaders() }); cargar(); };

  const setP = (k, v) => setForm(f => ({ ...f, params: { ...f.params, [k]: v } }));
  const trigLabel = (v) => TRIGGERS.find(t => t.v === v)?.l || v;
  const actLabel = (v) => ACCIONES.find(a => a.v === v)?.l || v;

  return (
    <div className="p-4 sm:p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2"><Zap className="text-amber-500" size={22} /><h2 className="text-xl font-black text-slate-800">Automatizaciones</h2></div>
        <div className="flex gap-2">
          <button onClick={() => run(true)} disabled={ejecutando} className="flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-bold text-sm disabled:opacity-50">
            {ejecutando ? <Loader size={15} className="animate-spin" /> : <Play size={15} />} Ejecutar ahora (con email)
          </button>
          <button onClick={() => setForm({ ...NUEVA })} className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-sm"><Plus size={16} /> Nueva regla</button>
        </div>
      </div>

      <p className="text-xs text-slate-400">Al entrar se evalúan las reglas automáticamente (sin enviar emails). El botón «Ejecutar ahora» sí dispara los emails. Cada acción respeta un enfriamiento por contacto para no repetirse.</p>

      {resumen && (
        <div className="bg-white rounded-xl border border-slate-200 p-3 text-sm">
          <div className="font-bold text-slate-700 mb-1">Última ejecución</div>
          {!resumen.length && <span className="text-slate-400">No hay reglas activas.</span>}
          {resumen.map(r => (
            <div key={r.ruleId} className="text-slate-600 flex justify-between border-b border-slate-50 py-0.5">
              <span>{r.name}</span>
              <span className="text-xs"><b className="text-emerald-600">{r.ejecutadas}</b> ejecutadas · {r.coincidencias} coincidencias · {r.saltadas} saltadas</span>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {!rules.length && <p className="text-center text-slate-400 py-8 text-sm">Sin reglas. Crea tu primera automatización.</p>}
        {rules.map(r => (
          <div key={r.id} className="bg-white rounded-xl border border-slate-200 p-3 flex items-center justify-between gap-3 flex-wrap">
            <div className="min-w-0">
              <div className="font-bold text-slate-800 text-sm">{r.name}</div>
              <div className="text-xs text-slate-400">Si <b className="text-slate-600">{trigLabel(r.trigger)}</b> → <b className="text-slate-600">{actLabel(r.action)}</b></div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => toggle(r)} title={r.active ? 'Activa' : 'Pausada'} className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${r.active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'}`}><Power size={12} /> {r.active ? 'Activa' : 'Pausada'}</button>
              <button onClick={() => setForm(r)} className="px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg text-xs font-bold">Editar</button>
              <button onClick={() => borrar(r)} className="p-1.5 text-slate-300 hover:text-red-600"><Trash2 size={15} /></button>
            </div>
          </div>
        ))}
      </div>

      {form && (
        <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-3" onClick={() => setForm(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg p-5 space-y-3 max-h-[92vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between"><h3 className="font-black text-slate-800">{form.id ? 'Editar regla' : 'Nueva regla'}</h3><button onClick={() => setForm(null)}><X size={18} /></button></div>
            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nombre de la regla *" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            <label className="text-xs font-bold text-slate-500 block">Disparador
              <select value={form.trigger} onChange={e => setForm({ ...form, trigger: e.target.value })} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-2 text-sm bg-white">
                {TRIGGERS.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
              </select>
            </label>
            {form.trigger === 'lead_sin_contacto' && (
              <label className="text-xs font-bold text-slate-500 block">Días sin contacto
                <input type="number" min="1" value={form.params.dias} onChange={e => setP('dias', Number(e.target.value))} className="w-24 mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
              </label>
            )}
            <label className="text-xs font-bold text-slate-500 block">Acción
              <select value={form.action} onChange={e => setForm({ ...form, action: e.target.value })} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-2 text-sm bg-white">
                {ACCIONES.map(a => <option key={a.v} value={a.v}>{a.l}</option>)}
              </select>
            </label>
            {form.action === 'crear_tarea' && (
              <>
                <input value={form.params.texto} onChange={e => setP('texto', e.target.value)} placeholder="Texto de la tarea" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
                <label className="text-xs font-bold text-slate-500 block">Vencimiento (días)
                  <input type="number" min="0" value={form.params.diasFollowup} onChange={e => setP('diasFollowup', Number(e.target.value))} className="w-24 mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
                </label>
              </>
            )}
            {form.action === 'cambiar_etapa' && (
              <label className="text-xs font-bold text-slate-500 block">Etapa destino
                <select value={form.params.stage} onChange={e => setP('stage', e.target.value)} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-2 text-sm bg-white">
                  {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
            )}
            {form.action === 'enviar_email' && (
              <>
                <input value={form.params.subject} onChange={e => setP('subject', e.target.value)} placeholder="Asunto del email" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
                <textarea value={form.params.html} onChange={e => setP('html', e.target.value)} rows={4} placeholder="Cuerpo (HTML). Variables {{nombre}} {{empresa}}…" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono" />
              </>
            )}
            <label className="text-xs font-bold text-slate-500 block">Enfriamiento por contacto (días)
              <input type="number" min="0" value={form.cooldownDays} onChange={e => setForm({ ...form, cooldownDays: Number(e.target.value) })} className="w-24 mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm" />
            </label>
            <button onClick={guardar} disabled={!form.name.trim()} className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-sm disabled:opacity-50">Guardar</button>
          </div>
        </div>
      )}
    </div>
  );
}
