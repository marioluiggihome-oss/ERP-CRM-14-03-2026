/**
 * CRMParteDiario - Parte/Informe de visitas por VOZ (IA), solo CRM.
 * Dictas las visitas de la mañana -> la IA estructura el informe -> exportar a
 * PDF, enviar por email o compartir por WhatsApp. Maquetación "Luiggi Home — Informe CRM".
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Mic, MicOff, Sparkles, FileDown, Mail, Send, Trash2, RefreshCw, Loader, ClipboardList } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const authHeaders = () => {
  const t = localStorage.getItem('luiggi_access_token') || localStorage.getItem('token') || localStorage.getItem('access_token');
  return { 'Content-Type': 'application/json', ...(t ? { Authorization: `Bearer ${t}` } : {}) };
};

const PERIODOS = [
  { key: 'hoy', label: 'Hoy' },
  { key: 'semana', label: 'Esta semana' },
  { key: 'mes', label: 'Este mes' },
];

const periodoLabel = (key) => {
  const hoy = new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  if (key === 'hoy') return `Hoy, ${hoy}`;
  if (key === 'semana') return `Esta semana (${new Date().toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })})`;
  if (key === 'mes') return `Mes de ${new Date().toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}`;
  return hoy;
};

const CRMParteDiario = ({ currentUser }) => {
  const [periodo, setPeriodo] = useState('hoy');
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [report, setReport] = useState(null);
  const [reports, setReports] = useState([]);
  const recognitionRef = useRef(null);
  const baseTextRef = useRef('');

  const loadReports = useCallback(async () => {
    try {
      const qs = currentUser?.id ? `?userId=${currentUser.id}` : '';
      const r = await fetch(`${API_URL}/api/crm/reports${qs}`, { headers: authHeaders() });
      if (r.ok) { const j = await r.json(); setReports(j.items || []); }
    } catch { /* noop */ }
  }, [currentUser]);

  useEffect(() => { loadReports(); }, [loadReports]);

  // ── Dictado por voz ──
  const toggleMic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Tu navegador no soporta dictado por voz. Escribe el parte a mano.'); return; }
    if (listening) { try { recognitionRef.current?.stop(); } catch (_) {} return; }
    const rec = new SR();
    rec.continuous = true; rec.interimResults = true; rec.lang = 'es-ES';
    baseTextRef.current = transcript ? transcript + ' ' : '';
    rec.onresult = (e) => {
      let interim = '', final = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const txt = e.results[i][0].transcript;
        if (e.results[i].isFinal) final += txt + ' '; else interim += txt;
      }
      if (final) baseTextRef.current += final;
      setTranscript((baseTextRef.current + interim).trimStart());
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    try { rec.start(); setListening(true); } catch (_) {}
  };

  const generar = async () => {
    if (!transcript.trim()) { alert('Dicta o escribe lo que hiciste en las visitas'); return; }
    try { recognitionRef.current?.stop(); } catch (_) {}
    setGenerating(true);
    try {
      const r = await fetch(`${API_URL}/api/crm/voice-report`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          transcript, periodo, periodoLabel: periodoLabel(periodo),
          userId: currentUser?.id, userName: currentUser?.clientName || currentUser?.username,
        }),
      });
      const j = await r.json();
      if (!r.ok || !j.success) throw new Error(j.detail || 'No se pudo generar');
      setReport(j.report);
      setTranscript('');
      await loadReports();
    } catch (e) { alert('Error al generar el informe: ' + e.message); }
    finally { setGenerating(false); }
  };

  const openReport = async (id) => {
    try {
      const r = await fetch(`${API_URL}/api/crm/reports/${id}`, { headers: authHeaders() });
      if (r.ok) setReport(await r.json());
    } catch { /* noop */ }
  };

  const delReport = async (id) => {
    if (!window.confirm('¿Eliminar este informe?')) return;
    await fetch(`${API_URL}/api/crm/reports/${id}`, { method: 'DELETE', headers: authHeaders() });
    if (report?.id === id) setReport(null);
    loadReports();
  };

  // ── Exportar a PDF (maquetación Luiggi Home) ──
  const exportPDF = (rep) => {
    const r = rep || report;
    if (!r) return;
    const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
    const W = pdf.internal.pageSize.getWidth();
    pdf.setFillColor(55, 48, 163); pdf.rect(0, 0, W, 26, 'F');
    pdf.setTextColor(255); pdf.setFontSize(9); pdf.text('LUIGGI HOME · INFORME CRM', 14, 10);
    pdf.setFontSize(16); pdf.text(r.titulo || 'Parte de visitas', 14, 18);
    pdf.setFontSize(9); pdf.setTextColor(80);
    pdf.text(`${r.periodoLabel || ''}  ·  ${r.userName || ''}  ·  ${r.totalVisitas || (r.visitas || []).length} visita(s)`, 14, 32);
    autoTable(pdf, {
      startY: 38,
      head: [['Cliente', 'Hora', 'Resumen', 'Resultado', 'Próxima acción']],
      body: (r.visitas || []).map(v => [v.cliente || '', v.hora || '', v.resumen || '', v.resultado || '', v.proximaAccion || '']),
      styles: { fontSize: 8, cellPadding: 2, valign: 'top' },
      headStyles: { fillColor: [241, 245, 249], textColor: [51, 65, 85] },
      columnStyles: { 0: { fontStyle: 'bold', cellWidth: 30 }, 1: { cellWidth: 14 } },
      margin: { left: 14, right: 14 },
    });
    let y = (pdf.lastAutoTable?.finalY || 60) + 8;
    if (r.resumen) {
      pdf.setFontSize(10); pdf.setTextColor(109, 40, 217); pdf.text('Resumen de la jornada', 14, y);
      pdf.setFontSize(9); pdf.setTextColor(51); y += 5;
      pdf.text(pdf.splitTextToSize(r.resumen, W - 28), 14, y);
    }
    pdf.save(`Informe_CRM_${(r.titulo || 'visitas').replace(/\s+/g, '_')}_${r.fecha || ''}.pdf`);
  };

  const enviarEmail = async (rep) => {
    const r = rep || report;
    if (!r) return;
    const to = window.prompt('Enviar informe a (correo):', currentUser?.email || '');
    if (!to) return;
    try {
      const res = await fetch(`${API_URL}/api/crm/reports/${r.id}/email`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify({ to }),
      });
      const j = await res.json();
      if (!res.ok) throw new Error(j.detail || 'Error');
      alert('Informe enviado a ' + to);
    } catch (e) { alert('No se pudo enviar: ' + e.message); }
  };

  const enviarWhatsApp = (rep) => {
    const r = rep || report;
    if (!r) return;
    let t = `*LUIGGI HOME — INFORME CRM*\n${r.titulo || 'Parte de visitas'}\n${r.periodoLabel || ''}\n`;
    (r.visitas || []).forEach((v, i) => {
      t += `\n${i + 1}. *${v.cliente || ''}*${v.hora ? ' (' + v.hora + ')' : ''}\n`;
      if (v.resumen) t += `   ${v.resumen}\n`;
      if (v.resultado) t += `   ✅ ${v.resultado}\n`;
      if (v.proximaAccion) t += `   ➡️ ${v.proximaAccion}\n`;
    });
    if (r.resumen) t += `\n📋 ${r.resumen}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(t)}`, '_blank');
  };

  return (
    <div className="h-full overflow-auto bg-slate-50 p-4 sm:p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white"><ClipboardList size={24} /></div>
          <div>
            <h1 className="text-2xl font-black text-slate-900">Parte diario por voz</h1>
            <p className="text-sm text-slate-500">Dicta tus visitas y la IA genera el informe del CRM</p>
          </div>
        </div>

        {/* Dictado */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 mb-5">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <div className="flex gap-1.5">
              {PERIODOS.map(p => (
                <button key={p.key} onClick={() => setPeriodo(p.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold ${periodo === p.key ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>{p.label}</button>
              ))}
            </div>
            <button onClick={toggleMic}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm ${listening ? 'bg-red-500 text-white animate-pulse' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
              {listening ? <MicOff size={16} /> : <Mic size={16} />} {listening ? 'Detener' : 'Dictar'}
            </button>
          </div>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Ej: 'He visitado a Cocinas García, interesados en una cocina en L, paso presupuesto el viernes. Luego en Muebles López, recogen muestras la semana que viene...'"
            className="w-full min-h-[120px] p-3 border border-slate-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          <button onClick={generar} disabled={generating}
            className="mt-3 w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2">
            {generating ? <Loader size={16} className="animate-spin" /> : <Sparkles size={16} />} {generating ? 'Generando informe…' : 'Generar informe (IA)'}
          </button>
        </div>

        {/* Vista previa del informe generado */}
        {report && (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden mb-5">
            <div className="bg-gradient-to-r from-indigo-800 to-purple-800 text-white px-5 py-4">
              <div className="text-[10px] uppercase tracking-widest opacity-80">Luiggi Home · Informe CRM</div>
              <h2 className="text-lg font-black">{report.titulo}</h2>
              <div className="text-xs opacity-90">{report.periodoLabel} · {report.userName} · {report.totalVisitas || (report.visitas || []).length} visita(s)</div>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-slate-500"><tr>
                  <th className="text-left p-2 text-[10px] uppercase">Cliente</th>
                  <th className="text-left p-2 text-[10px] uppercase">Hora</th>
                  <th className="text-left p-2 text-[10px] uppercase">Resumen</th>
                  <th className="text-left p-2 text-[10px] uppercase">Resultado</th>
                  <th className="text-left p-2 text-[10px] uppercase">Próxima acción</th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {(report.visitas || []).map((v, i) => (
                    <tr key={i}>
                      <td className="p-2 font-bold text-slate-800">{v.cliente || '—'}</td>
                      <td className="p-2 text-slate-500">{v.hora || '—'}</td>
                      <td className="p-2 text-slate-600">{v.resumen || '—'}</td>
                      <td className="p-2 text-slate-600">{v.resultado || '—'}</td>
                      <td className="p-2 text-slate-600">{v.proximaAccion || '—'}</td>
                    </tr>
                  ))}
                  {(report.visitas || []).length === 0 && <tr><td colSpan={5} className="p-4 text-center text-slate-400">{report.resumen || 'Sin visitas'}</td></tr>}
                </tbody>
              </table>
              {report.resumen && (report.visitas || []).length > 0 && (
                <div className="mt-3 p-3 bg-slate-50 border-l-4 border-indigo-500 rounded text-sm text-slate-700">{report.resumen}</div>
              )}
            </div>
            <div className="px-4 pb-4 flex gap-2 flex-wrap">
              <button onClick={() => exportPDF()} className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-white rounded-xl text-sm font-bold hover:bg-slate-900"><FileDown size={15} /> PDF</button>
              <button onClick={() => enviarEmail()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700"><Mail size={15} /> Email</button>
              <button onClick={() => enviarWhatsApp()} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl text-sm font-bold hover:bg-green-700"><Send size={15} /> WhatsApp</button>
            </div>
          </div>
        )}

        {/* Historial de informes */}
        <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h3 className="text-xs font-black text-slate-500 uppercase">Informes guardados</h3>
            <button onClick={loadReports} className="text-slate-400 hover:text-slate-600"><RefreshCw size={15} /></button>
          </div>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-slate-100">
              {reports.map(rep => (
                <tr key={rep.id} className="hover:bg-slate-50">
                  <td className="p-3 cursor-pointer" onClick={() => openReport(rep.id)}>
                    <p className="font-bold text-indigo-700">{rep.titulo}</p>
                    <p className="text-xs text-slate-400">{rep.periodoLabel} · {rep.totalVisitas || 0} visita(s)</p>
                  </td>
                  <td className="p-3 text-right whitespace-nowrap">
                    <button onClick={() => exportPDF(rep)} title="PDF" className="mr-1 text-slate-400 hover:text-slate-700"><FileDown size={15} /></button>
                    <button onClick={() => enviarEmail(rep)} title="Email" className="mr-1 text-slate-400 hover:text-blue-600"><Mail size={15} /></button>
                    <button onClick={() => enviarWhatsApp(rep)} title="WhatsApp" className="mr-1 text-slate-400 hover:text-green-600"><Send size={15} /></button>
                    <button onClick={() => delReport(rep.id)} title="Eliminar" className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button>
                  </td>
                </tr>
              ))}
              {reports.length === 0 && <tr><td className="p-6 text-center text-slate-400">Aún no hay informes. Dicta tu primer parte arriba.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CRMParteDiario;
