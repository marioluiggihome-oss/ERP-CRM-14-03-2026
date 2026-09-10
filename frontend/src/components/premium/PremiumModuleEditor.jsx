/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
import React from 'react';
import { LEVELS, LEVEL_NAMES, layoutReview, newModule, moveModule } from './premiumLayout';
export default function PremiumModuleEditor({ rows, onChange, disabled }) {
  const review = layoutReview(rows);
  const update = (id, change) => onChange(rows.map(r => r.id === id ? { ...r, ...change, confirmed: Object.keys(change).includes('confirmed') ? change.confirmed : false } : r));
  return <div>
    <p className="premium-design__caption">RELACIÓN REVISADA / CENTÍMETROS</p>
    <p className="premium-design__help">Transcribe o corrige los módulos del croquis. El orden es de izquierda a derecha en cada pared y nivel. Editar un dato vuelve a dejar su lectura pendiente.</p>
    {rows.length === 0 && <p className="premium-design__empty">Empieza por el primer mueble. No se precargan medidas ni módulos inventados.</p>}
    <fieldset disabled={disabled} className="premium-design__module-list"><legend className="premium-design__sr">Módulos del proyecto</legend>
    {rows.map((r, i) => <article className="premium-design__module" key={r.id}>
      <header><strong>{String(i + 1).padStart(2, '0')} / {r.type || 'Nuevo módulo'}</strong><button type="button" aria-label={`Eliminar módulo ${i + 1}`} onClick={() => onChange(rows.filter(item => item.id !== r.id))}>Eliminar</button></header>
      <div className="premium-design__pair">
        <label className="premium-design__field">Pared<input value={r.wall} maxLength={80} onChange={e => update(r.id, { wall: e.target.value })} /></label>
        <label className="premium-design__field">Nivel<select value={r.level} onChange={e => update(r.id, { level: e.target.value })}>{LEVELS.map(l => <option key={l} value={l}>{LEVEL_NAMES[l]}</option>)}</select></label>
      </div>
      <label className="premium-design__field">Tipo de mueble o equipo<input value={r.type} maxLength={160} placeholder="Ej.: bajo fregadero, frigo francés…" onChange={e => update(r.id, { type: e.target.value })} /></label>
      <label className="premium-design__field">Ancho (cm)<input type="number" min="0.1" step="0.1" value={r.width} placeholder="Sin confirmar" onChange={e => update(r.id, { width: e.target.value })} /></label>
      <label className="premium-design__field">Frentes, fondo y observaciones<input value={r.detail} maxLength={300} placeholder="Ej.: 2 gavetas, fondo 60 cm" onChange={e => update(r.id, { detail: e.target.value })} /></label>
      <footer><label><input type="checkbox" checked={r.confirmed} onChange={e => update(r.id, { confirmed: e.target.checked })} /> Lectura confirmada</label><div><button type="button" disabled={i === 0} aria-label={`Subir módulo ${i + 1}`} onClick={() => onChange(moveModule(rows, r.id, -1))}>↑</button><button type="button" disabled={i === rows.length - 1} aria-label={`Bajar módulo ${i + 1}`} onClick={() => onChange(moveModule(rows, r.id, 1))}>↓</button></div></footer>
    </article>)}
    <button type="button" className="premium-design__add" disabled={rows.length >= 60} onClick={() => onChange([...rows, newModule()])}>+ Añadir módulo</button>
    </fieldset>
    {review.groups.map(g => <div className="premium-design__group" key={g.label}><strong>{g.label}</strong><span>{g.complete ? `${g.total} cm de módulos` : 'Suma pendiente de medidas'}</span>{g.complete && <svg viewBox="0 0 300 40" role="img" aria-label={`Secuencia proporcional de ${g.label}`}>
      {g.rows.map((r, i) => { const x = g.rows.slice(0, i).reduce((t, m) => t + Number(m.width), 0) / g.total * 300; const w = Number(r.width) / g.total * 300; return <g key={r.id}><title>{r.type}: {r.width} cm</title><rect x={x} y="2" width={w} height="36" fill={r.confirmed ? '#d6e1d7' : '#efe2c9'} stroke="#667b6c" />{w > 22 && <text x={x + w / 2} y="25" textAnchor="middle" fontSize="10">{r.width}</text>}</g>; })}
    </svg>}</div>)}
    {rows.length > 0 && <p className="premium-design__help" role="status">{review.issues.length ? `${review.issues.length} puntos pendientes. Revísalos antes de generar con esta relación.` : 'Lecturas completas. La suma no comprueba huecos, colisiones ni aptitud para fabricar.'}</p>}
  </div>;
}
