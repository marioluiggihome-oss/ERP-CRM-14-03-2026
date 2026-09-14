/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE. */
import React, { useState } from 'react';

export default function RevisionTecnicaCocina({ informe, onClose, onApprove, onTransfer, vigente }) {
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');
  const [aprobado, setAprobado] = useState(false);
  const ejecutar = async (fn) => {
    setOcupado(true); setError('');
    try { await fn(); } catch (e) { setError(e.message || 'No se pudo completar la operación.'); }
    finally { setOcupado(false); }
  };
  return <section role="dialog" aria-modal="true" aria-label="Revisión técnica de cocina" className="fixed inset-0 z-[160] bg-white overflow-auto p-4">
    <header className="flex gap-3 items-center mb-4"><h2 className="font-bold text-xl flex-1">Revisión técnica · Premium</h2><button onClick={onClose}>Volver al diseño</button></header>
    <p>Una misma relación para muebles, despiece y presupuesto. Los cascos se consideran comprados; los frentes y herrajes requieren una ficha MV verificada.</p>
    {!vigente && <p role="alert" className="p-3 bg-amber-100">El diseño ha cambiado. Cierra esta revisión y vuelve a analizarlo.</p>}
    {error && <p role="alert" className="p-3 bg-red-100">{error}</p>}
    <div className="overflow-x-auto my-4"><table className="w-full text-sm"><thead><tr>{['Mueble', 'Referencia MV', 'Pared / posición cm', 'Ancho × alto × fondo cm', 'Cantidad'].map(t => <th className="text-left border p-2" key={t}>{t}</th>)}</tr></thead>
      <tbody>{informe.relacion.map(m => <tr key={m.uid}><td className="border p-2">{m.uid} · {m.descripcion}</td><td className="border p-2">{m.referencia_mv || 'Pendiente'}</td><td className="border p-2">{m.pared_idx == null ? '?' : m.pared_idx + 1} / {m.posicion_cm ?? '?'}</td><td className="border p-2">{[m.ancho, m.alto, m.fondo].map(v => v ?? '?').join(' × ')}</td><td className="border p-2">{m.cantidad ?? '?'}</td></tr>)}</tbody></table></div>
    {informe.skills.map(s => <details className="border rounded p-3 mb-2" key={s.skill} open={s.skill === 7}>
      <summary>{s.skill}. {s.nombre} · {s.estado} · confianza {s.confianza}</summary>
      {s.datos_pendientes.map((p, i) => <p className="text-amber-900 my-1" key={i}>{p}</p>)}
      {s.advertencias.map((p, i) => <p key={i}>{p}</p>)}
      {s.skill === 7 && ['frentes', 'herrajes'].map(g => <div key={g}><h3 className="font-bold mt-2">{g === 'frentes' ? 'Puertas y frentes' : 'Herrajes'}</h3>{s.resultado[g].length ? s.resultado[g].map((p, i) => <p key={i}>{p.mueble_uid} · {p.referencia} · {p.cantidad} uds.{p.ancho && ` · ${p.ancho} × ${p.alto} cm`} · ficha {p.ficha_version}</p>) : <p>Sin piezas verificadas en esta revisión.</p>}</div>)}
      {s.skill === 8 && <p>{s.resultado.precios_ocultos ? 'Tarifas restringidas a usuarios autorizados.' : `Importe de tarifa conocido: ${s.resultado.importe_tarifa_conocido} €. ${s.resultado.alcance}`}</p>}
    </details>)}
    <p className="text-sm my-3">Revisión {informe.revision.slice(0, 12)} · Tarifa {informe.tarifa} · {informe.tarifa_version.slice(0, 12)}</p>
    <div className="flex flex-wrap gap-3 sticky bottom-0 bg-white py-3 border-t">
      <button className="border rounded px-4 py-2 disabled:opacity-40" disabled={ocupado || !vigente || !informe.puede_aprobar || aprobado} onClick={() => ejecutar(async () => { await onApprove(); setAprobado(true); })}>{aprobado ? 'Revisión aprobada' : 'Aprobar revisión técnica'}</button>
      <button className="bg-indigo-700 text-white rounded px-4 py-2 disabled:opacity-40" disabled={ocupado || !vigente || !aprobado} onClick={() => ejecutar(onTransfer)}>Volcar a presupuesto junto al diseño</button>
    </div>
    {!informe.puede_aprobar && <p>La aprobación está bloqueada. Corrige los datos de la distribución y completa las fichas MV pendientes antes de volver a revisar.</p>}
  </section>;
}
