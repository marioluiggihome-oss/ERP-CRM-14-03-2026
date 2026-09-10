/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
import React, { useState } from 'react';
import { downloadInstallationReport } from './premiumInstallationReport';
import { installationReady, installationsCsv } from './premiumBrief';

export default function PremiumInstallations({ rows, onChange, disabled }) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const downloadPdf = async () => {
    setExporting(true); setError('');
    try { await downloadInstallationReport(rows); }
    catch (e) { setError(e.message || 'No se pudo descargar el informe.'); }
    finally { setExporting(false); }
  };
  const ready = rows.length > 0 && rows.every(installationReady);
  const update = (id, change) => onChange(rows.map(r => r.id === id ? { ...r, ...change, confirmed: change.confirmed ?? false } : r));
  const download = () => {
    const url = URL.createObjectURL(new Blob([installationsCsv(rows)], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'instalaciones-cocina.csv'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <div>
    <p className="premium-design__caption">COTAS DE INSTALACIONES / CM</p>
    <p className="premium-design__help">Alturas desde suelo terminado hasta el eje de la toma. Distancias horizontales sobre la pared hasta ese mismo eje: identifica la pared lateral desde la que mides y el sentido. No se calculan desde los píxeles del render.</p>
    <fieldset disabled={disabled} className="premium-design__module-list"><legend className="premium-design__sr">Puntos de instalaciones</legend>
      {rows.map((r, i) => <article className="premium-design__module" key={r.id}>
        <header><strong>{i + 1} / {r.label || 'Nuevo punto'}</strong><button type="button" onClick={() => onChange(rows.filter(p => p.id !== r.id))}>Eliminar</button></header>
        <label className="premium-design__field">Oficio<select value={r.trade} onChange={e => update(r.id, { trade: e.target.value })}><option value="electricidad">Electricidad</option><option value="fontaneria">Fontanería</option></select></label>
        {[['label','Punto o equipo',100],['wall','Pared donde se instala',80],['origin','Pared de referencia y sentido de medición',160],['height','Altura desde suelo terminado (cm)',20],['distance','Distancia horizontal al eje (cm)',20]].map(([key, label, max]) => <label key={key} className="premium-design__field">{label}<input value={r[key]} maxLength={max} inputMode={['height','distance'].includes(key) ? 'decimal' : 'text'} onChange={e => update(r.id, { [key]: e.target.value })} /></label>)}
        <label><input type="checkbox" checked={r.confirmed} disabled={!installationReady({ ...r, confirmed: true })} onChange={e => update(r.id, { confirmed: e.target.checked })} /> Cotas comprobadas con la medición</label>
      </article>)}
      <button type="button" className="premium-design__add" disabled={rows.length >= 40} onClick={() => onChange([...rows, { id: `point-${Date.now()}-${Math.random().toString(36).slice(2)}`, label: '', wall: '', origin: '', height: '', distance: '', trade: 'electricidad', confirmed: false }])}>+ Añadir toma o punto de luz</button>
    </fieldset>
    <p className="premium-design__help">Incluye también la alimentación de luz bajo los altos y el enchufe de campana. Introduce sus alturas según el proyecto; no se asignan medidas automáticas.</p>
    <button type="button" disabled={disabled || !ready} onClick={download}>Descargar relación de instalaciones (CSV)</button>
    <button type="button" disabled={disabled || !ready || exporting} onClick={downloadPdf}>{exporting ? 'Preparando informe…' : 'Descargar informe PDF'}</button>
    {error && <p role="alert" className="premium-design__help">{error}</p>}
    <p className="premium-design__help" role="status">{ready ? 'Relación lista para exportar. Contrastar ubicación y accesibilidad con las fichas de los equipos.' : 'Completa y confirma cada punto para descargar la relación.'} Esta tabla no sustituye el plano de ejecución ni comprueba la normativa.</p>
  </div>;
}
