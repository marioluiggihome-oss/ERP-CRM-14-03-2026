/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * ArticleCostsIAModal — Alta masiva de costes de artículo con IA.
 * Se pega una captura/PDF/Excel de un pedido o tarifa de proveedor y una orden
 * en texto libre (ej. "sube todo y la campana ponla como sin venderse", "mete
 * un 10% para calcular nuestro costo"). La IA (o la lectura del Excel) propone
 * los artículos; el usuario revisa/edita y solo se guarda lo que confirme.
 * Reutilizable desde Panel Maestro > Costes artículos y desde el editor de
 * fichas de Rentabilidad, para no tener que salir de la factura para dar de
 * alta un artículo nuevo.
 */
import React, { useState, useEffect } from 'react';
import { Sparkles, X, Loader2, Save } from 'lucide-react';
import { authHeaders } from '../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;

const leerArchivoB64 = (file) => new Promise((res) => {
  const fr = new FileReader();
  fr.onload = () => res(String(fr.result));
  fr.onerror = () => res(null);
  fr.readAsDataURL(file);
});

const ArticleCostsIAModal = ({ onClose, onSaved }) => {
  const [ia, setIa] = useState({ fileB64: '', mime: '', name: '', instruccion: '', loading: false, articulos: null, saving: false, error: '' });

  const cargarArchivo = async (file) => {
    if (!file) return;
    const b64 = await leerArchivoB64(file);
    setIa(s => ({ ...s, fileB64: b64, mime: file.type, name: file.name, articulos: null, error: '' }));
  };

  // Pegar (Ctrl+V) una imagen del portapapeles mientras el modal está abierto.
  useEffect(() => {
    const onPaste = (e) => {
      const clip = (e.clipboardData && e.clipboardData.items) || [];
      for (let i = 0; i < clip.length; i++) {
        if (clip[i].type && clip[i].type.startsWith('image/')) {
          const file = clip[i].getAsFile();
          if (file) { e.preventDefault(); cargarArchivo(file); break; }
        }
      }
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, []);

  const analizar = async () => {
    if (!ia.fileB64) { alert('Pega (Ctrl+V) o adjunta una captura, PDF o Excel primero'); return; }
    setIa(s => ({ ...s, loading: true, error: '' }));
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/parse-article-costs`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: ia.fileB64, instruccion: ia.instruccion, filename: ia.name }),
      });
      const data = await r.json();
      if (!data.success) throw new Error(data.error || 'No se pudo leer el documento');
      setIa(s => ({ ...s, loading: false, articulos: (data.articulos || []).map(a => ({ ...a, incluir: true })), margenAplicado: data.margenAplicado }));
    } catch (e) {
      setIa(s => ({ ...s, loading: false, error: e.message }));
    }
  };

  const setArticulo = (i, campo, val) => {
    setIa(s => ({ ...s, articulos: s.articulos.map((a, x) => x === i ? { ...a, [campo]: val } : a) }));
  };

  const guardarTodos = async () => {
    const seleccionados = (ia.articulos || []).filter(a => a.incluir && a.codigo.trim());
    if (!seleccionados.length) { alert('No hay artículos seleccionados (revisa que tengan código)'); return; }
    setIa(s => ({ ...s, saving: true }));
    try {
      for (const a of seleccionados) {
        await fetch(`${BASE}/api/rentabilidad/article-costs`, {
          method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({
            codigo: a.codigo, nombre: a.nombre,
            costeUnitario: String(a.costeUnitario).replace(',', '.'),
            revisar: a.revisar || '', source: 'ia',
          }),
        });
      }
      onSaved && onSaved(seleccionados.length);
      onClose && onClose();
    } catch { alert('Error al guardar los artículos'); setIa(s => ({ ...s, saving: false })); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-[160] flex items-center justify-center p-4" onClick={() => !ia.saving && onClose && onClose()}>
      <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[88vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="bg-gradient-to-r from-fuchsia-600 to-indigo-600 text-white px-5 py-3 flex items-center justify-between shrink-0">
          <h3 className="font-black text-sm uppercase flex items-center gap-2"><Sparkles size={16} /> Subir costes de artículos con IA</h3>
          <button onClick={() => !ia.saving && onClose && onClose()} className="p-1.5 hover:bg-white/20 rounded-lg"><X size={18} /></button>
        </div>
        <div className="p-5 overflow-y-auto space-y-3">
          {!ia.articulos ? (
            <>
              <label className="block border-2 border-dashed border-slate-200 rounded-xl p-6 text-center text-sm text-slate-500 cursor-pointer hover:border-fuchsia-300 hover:bg-fuchsia-50/40">
                {ia.fileB64 ? (
                  <span className="font-bold text-emerald-700">✓ {ia.name || 'Archivo cargado'}</span>
                ) : (
                  <span>Pega una captura con <b>Ctrl+V</b>, o haz clic para adjuntar una foto, PDF o Excel (.xlsx)</span>
                )}
                <input type="file" accept="image/*,application/pdf,.xlsx,.xls" className="hidden"
                  onChange={e => cargarArchivo(e.target.files?.[0])} />
              </label>
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Orden (texto libre, opcional)</label>
                <input
                  value={ia.instruccion}
                  onChange={e => setIa(s => ({ ...s, instruccion: e.target.value }))}
                  placeholder='Ej: "sube todo y la campana ponla como sin venderse" o "mete un 10% para calcular nuestro costo"'
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              {ia.error && <p className="text-rose-600 text-xs font-bold">{ia.error}</p>}
              <button onClick={analizar} disabled={ia.loading || !ia.fileB64}
                className="w-full py-2.5 bg-fuchsia-600 hover:bg-fuchsia-700 disabled:opacity-50 text-white rounded-xl font-black text-sm flex items-center justify-center gap-2">
                {ia.loading ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
                {ia.loading ? 'Leyendo…' : 'Analizar'}
              </button>
            </>
          ) : (
            <>
              <p className="text-xs text-slate-500 bg-slate-50 rounded-lg p-2">
                {ia.articulos.length} artículo(s) detectado(s)
                {ia.margenAplicado ? ` · margen aplicado sobre el neto: +${ia.margenAplicado}%` : ''}.
                Revisa antes de guardar — desmarca lo que no quieras dar de alta.
              </p>
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-slate-100 text-slate-500">
                    <tr>
                      <th className="p-2"></th>
                      <th className="text-left p-2 font-black uppercase">Código</th>
                      <th className="text-left p-2 font-black uppercase">Nombre</th>
                      <th className="text-right p-2 font-black uppercase">Neto</th>
                      <th className="text-right p-2 font-black uppercase">Coste unit.</th>
                      <th className="text-left p-2 font-black uppercase">Revisar</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {ia.articulos.map((a, i) => (
                      <tr key={i} className={a.revisar ? 'bg-amber-50' : ''}>
                        <td className="p-2 text-center">
                          <input type="checkbox" checked={a.incluir} onChange={e => setArticulo(i, 'incluir', e.target.checked)} />
                        </td>
                        <td className="p-2">
                          <input value={a.codigo} onChange={e => setArticulo(i, 'codigo', e.target.value)}
                            className="w-28 px-1.5 py-1 border border-slate-200 rounded text-xs font-mono font-bold" />
                        </td>
                        <td className="p-2">
                          <input value={a.nombre} onChange={e => setArticulo(i, 'nombre', e.target.value)}
                            className="w-full min-w-[140px] px-1.5 py-1 border border-slate-200 rounded text-xs" />
                        </td>
                        <td className="p-2 text-right text-slate-400">{a.netoUnitario}</td>
                        <td className="p-2 text-right">
                          <input value={a.costeUnitario} onChange={e => setArticulo(i, 'costeUnitario', e.target.value)}
                            className="w-20 px-1.5 py-1 border border-slate-200 rounded text-xs text-right font-bold" />
                        </td>
                        <td className="p-2">
                          <input value={a.revisar} onChange={e => setArticulo(i, 'revisar', e.target.value)}
                            placeholder="—" className="w-28 px-1.5 py-1 border border-slate-200 rounded text-[11px] text-amber-700" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setIa(s => ({ ...s, articulos: null }))} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold">
                  ← Volver a analizar
                </button>
                <button onClick={guardarTodos} disabled={ia.saving}
                  className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl font-black text-sm flex items-center justify-center gap-2">
                  {ia.saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                  {ia.saving ? 'Guardando…' : `Guardar seleccionados (${ia.articulos.filter(a => a.incluir).length})`}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticleCostsIAModal;
