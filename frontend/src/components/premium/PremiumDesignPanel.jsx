/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
import React, { useState } from 'react';
import { ATMOSPHERES, normalizeBrief } from './premiumBrief';
import './premiumDesign.css';
import PremiumInstallations from './PremiumInstallations';

export default function PremiumDesignPanel({
  value, onChange, disabled = false, onDetectLayout, detectingLayout = false,
  detectedLayout = null, layoutConfirmed = false, onConfirmLayout,
}) {
  const [tab, setTab] = useState('distribucion');
  const brief = normalizeBrief(value);
  const update = change => onChange({ ...brief, ...change });
  const distribution = detectedLayout?.distribucion;
  const wallCount = distribution?.paredes?.length || 0;
  const moduleCount = distribution?.elementos?.length || 0;
  const status = brief.scene === 'croquis'
    ? (layoutConfirmed ? 'Distribución confirmada' : 'Croquis sin confirmar')
    : brief.scene === 'obra' ? 'Foto de obra' : 'Modo concepto';
  return (
    <section className="premium-design" aria-label="Control de proyecto Premium">
      <header className="premium-design__header">
        <div><span className="premium-design__eyebrow">CONTROL PREMIUM</span><strong>Revisa antes de renderizar</strong></div>
        <span className={`premium-design__status ${layoutConfirmed ? 'is-ready' : ''}`}>{status}</span>
      </header>
      <div className="premium-design__tabs" role="group" aria-label="Secciones del encargo">
        {[['distribucion', 'Distribución'], ['materiales', 'Acabados'], ['instalaciones', 'Instalaciones']].map(([id, label]) => (
          <button key={id} type="button" aria-pressed={tab === id} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      <div className="premium-design__body">
        {tab === 'instalaciones' && <PremiumInstallations rows={brief.installations} onChange={installations => update({ installations })} disabled={disabled} />}
        {tab === 'distribucion' && <>
          <label className="premium-design__field">Punto de partida<select value={brief.scene} disabled={disabled} onChange={e => update({ scene: e.target.value })}><option value="concepto">Idea desde una descripción</option><option value="croquis">Croquis con módulos o medidas</option><option value="obra">Foto de la estancia real</option></select></label>
          <label className="premium-design__field">Qué representa cada imagen<textarea rows={3} maxLength={1200} value={brief.sourceNotes} disabled={disabled} onChange={e => update({ sourceNotes: e.target.value })} placeholder="Ej.: foto 1, croquis de la pared del fondo; foto 2, esa misma pared en obra; foto 3, muestra de puerta." /></label>
          <div className="premium-design__workflow">
            <p><strong>1. Lee el croquis</strong><span>Detecta paredes, orden, niveles y anchos sin generar ni gastar los 7 créditos del render.</span></p>
            <button type="button" onClick={onDetectLayout} disabled={disabled || detectingLayout}>{detectingLayout ? 'Leyendo croquis…' : distribution ? 'Volver a leer el croquis' : 'Leer croquis y módulos'}</button>
            {distribution && <div className="premium-design__detected"><strong>{wallCount} {wallCount === 1 ? 'pared' : 'paredes'} · {moduleCount} módulos</strong><span>Revisa y corrige la relación que aparece junto al render.</span><button type="button" className={layoutConfirmed ? 'is-ready' : ''} onClick={onConfirmLayout} disabled={disabled}>{layoutConfirmed ? '✓ Distribución confirmada' : 'Confirmar esta distribución'}</button></div>}
          </div>
          {brief.scene === 'croquis' && !layoutConfirmed && <p className="premium-design__warning">El render Premium permanecerá bloqueado hasta confirmar la distribución. Así no se consumen créditos con una lectura incorrecta.</p>}
        </>}
        {tab === 'materiales' && <>
          <p className="premium-design__caption">ACABADOS QUE DEBE RESPETAR</p>
          <label className="premium-design__field">Marca, referencia y zona de aplicación
            <textarea rows={5} maxLength={1200} disabled={disabled} value={brief.materials} onChange={e => update({ materials: e.target.value })} placeholder="Ej.: altos centrales · Alvic · Agave · acabado según muestra adjunta. Encimera y aplacado · referencia exacta del proveedor." />
          </label>
          <p className="premium-design__help">Adjunta las muestras en las referencias del proyecto. El nombre del color por sí solo no garantiza su reproducción exacta.</p>
          <label className="premium-design__field">Encuentros, herrajes y detalles que conservar
            <textarea rows={4} maxLength={1200} disabled={disabled} value={brief.construction} onChange={e => update({ construction: e.target.value })} placeholder="Ej.: dos gavetas inferiores; veta vertical; tirador según referencia; cascada en el lateral derecho. Indica solo medidas comprobadas." />
          </label>
          <label className="premium-design__field">Presentación<select value={brief.atmosphere} disabled={disabled} onChange={e => update({ atmosphere: e.target.value })}>{ATMOSPHERES.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
        </>}
      </div>
    </section>
  );
}
