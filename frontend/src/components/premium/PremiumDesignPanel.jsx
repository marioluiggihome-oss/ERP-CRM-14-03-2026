/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
import React, { useState } from 'react';
import { SPECIALTIES, ATMOSPHERES, normalizeBrief, premiumDirection } from './premiumBrief';
import './premiumDesign.css';
import PremiumInstallations from './PremiumInstallations';
import PremiumModuleEditor from './PremiumModuleEditor';

export default function PremiumDesignPanel({ value, onChange, disabled = false }) {
  const [transferMessage, setTransferMessage] = useState('');
  const [tab, setTab] = useState('direccion');
  const brief = normalizeBrief(value);
  const update = change => onChange({ ...brief, ...change });
  const toggle = id => update({ specialties: brief.specialties.includes(id) ? brief.specialties.filter(s => s !== id) : [...brief.specialties, id] });
  const exportBrief = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ version: 1, brief }, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = 'encargo-premium.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); setTransferMessage('Copia descargada.');
  };
  const importBrief = async e => {
    const file = e.target.files?.[0]; e.target.value = ''; if (!file) return;
    try {
      if (file.size > 100000) throw new Error('El archivo supera 100 KB.');
      const data = JSON.parse(await file.text());
      if (data.version !== 1 || !data.brief || typeof data.brief !== 'object' || Array.isArray(data.brief)) throw new Error('No es una copia de encargo PREMIUM válida.');
      onChange(normalizeBrief(data.brief)); setTransferMessage('Encargo recuperado; revisa los datos antes de generar.');
    } catch (error) { setTransferMessage(error.message || 'No se pudo recuperar el archivo.'); }
  };
  return (
    <section className="premium-design" aria-label="Dirección de diseño Premium">
      <header className="premium-design__header">
        <span className="premium-design__eyebrow">ESTUDIO / PREMIUM</span>
        <h2>Diseñado para vivir.<br /><em>Pensado para construir.</em></h2>
        <p>Prepara el encargo con criterios de arquitectura, interiorismo y oficio.</p>
        <span className="premium-design__local">Configurar aquí no consume créditos</span>
      </header>
      <div className="premium-design__tabs" role="group" aria-label="Secciones del encargo">
        {[['direccion', 'Encargo'], ['modulos', 'Módulos'], ['materiales', 'Acabados'], ['instalaciones', 'Instalaciones'], ['revision', 'Revisión']].map(([id, label]) => (
          <button key={id} type="button" aria-pressed={tab === id} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      <div className="premium-design__body">
        {tab === 'instalaciones' && <PremiumInstallations rows={brief.installations} onChange={installations => update({ installations })} disabled={disabled} />}
        {tab === 'modulos' && <PremiumModuleEditor rows={brief.modules} onChange={modules => update({ modules })} disabled={disabled} />}
        {tab === 'direccion' && <>
          <label className="premium-design__field">Punto de partida<select value={brief.scene} disabled={disabled} onChange={e => update({ scene: e.target.value })}><option value="concepto">Idea desde una descripción</option><option value="croquis">Diseño a partir de un croquis</option><option value="obra">Diseño sobre la foto de obra</option></select></label>
          <label className="premium-design__field">Qué representa cada imagen<textarea rows={3} maxLength={1200} value={brief.sourceNotes} disabled={disabled} onChange={e => update({ sourceNotes: e.target.value })} placeholder="Ej.: foto 1, croquis de la pared del fondo; foto 2, esa misma pared en obra; foto 3, muestra de puerta." /></label>
          <p className="premium-design__help">Sube los archivos en las referencias y planos del proyecto. Si una cifra está tachada o no se lee, déjala pendiente.</p>
          <p className="premium-design__caption">01 / CRITERIOS DEL ENCARGO</p>
          <p className="premium-design__help">Elige qué aspectos debe cuidar la imagen. Son instrucciones de diseño, no especialistas contratados ni comprobaciones realizadas.</p>
          <fieldset disabled={disabled} className="premium-design__specialties">
            <legend className="premium-design__sr">Especialidades</legend>
            {SPECIALTIES.map(s => <label key={s.id}>
              <input type="checkbox" checked={brief.specialties.includes(s.id)} onChange={() => toggle(s.id)} />
              <span><strong>{s.name}</strong><small>{s.detail}</small></span>
            </label>)}
          </fieldset>
          <label className="premium-design__field">Ambiente de presentación
            <select value={brief.atmosphere} disabled={disabled} onChange={e => update({ atmosphere: e.target.value })}>
              {ATMOSPHERES.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </label>
          <p className="premium-design__help">El ambiente no autoriza a cambiar la distribución o los acabados definidos.</p>
        </>}
        {tab === 'materiales' && <>
          <p className="premium-design__caption">02 / MATERIALES CON IDENTIDAD</p>
          <label className="premium-design__field">Marca, referencia y zona de aplicación
            <textarea rows={5} maxLength={1200} disabled={disabled} value={brief.materials} onChange={e => update({ materials: e.target.value })} placeholder="Ej.: altos centrales · Alvic · Agave · acabado según muestra adjunta. Encimera y aplacado · referencia exacta del proveedor." />
          </label>
          <p className="premium-design__help">Adjunta las muestras en las referencias del proyecto. El nombre del color por sí solo no garantiza su reproducción exacta.</p>
          <label className="premium-design__field">Encuentros, herrajes y detalles que conservar
            <textarea rows={4} maxLength={1200} disabled={disabled} value={brief.construction} onChange={e => update({ construction: e.target.value })} placeholder="Ej.: dos gavetas inferiores; veta vertical; tirador según referencia; cascada en el lateral derecho. Indica solo medidas comprobadas." />
          </label>
        </>}
        {tab === 'revision' && <>
          <p className="premium-design__caption">03 / ANTES DE PRESENTAR O FABRICAR</p>
          <p className="premium-design__help">Lista de consulta manual. No evalúa automáticamente el proyecto ni certifica su fabricación.</p>
          <ul className="premium-design__review">
            <li><strong>Croquis y obra</strong><span>Relacionar bajos, altos y sobremódulos de cada pared. Confirmar cifras dudosas e identificar qué foto corresponde a cada estancia.</span></li>
            <li><strong>Espacio</strong><span>Contrastar paredes, altura, huecos y circulación con la medición.</span></li>
            <li><strong>Mobiliario</strong><span>Comprobar orden, anchos, puertas, gavetas y aperturas.</span></li>
            <li><strong>Oficio</strong><span>Resolver remates, encuentros, holguras y herrajes con el fabricante.</span></li>
            <li><strong>Instalaciones</strong><span>Contrastar tomas y ventilación con los equipos y la obra.</span></li>
            <li><strong>Oferta</strong><span>Confirmar referencias, tarifa vigente y versión aprobada por el cliente.</span></li>
          </ul>
          <details className="premium-design__details"><summary>Ver instrucciones de PREMIUM</summary><pre>{premiumDirection(brief)}</pre></details>
        </>}
        <div className="premium-design__transfer"><button type="button" onClick={exportBrief} disabled={disabled}>Descargar encargo</button><label>Recuperar copia<input type="file" accept=".json,application/json" disabled={disabled} onChange={importBrief} aria-label="Recuperar copia del encargo Premium" /></label></div><p className="premium-design__help" role="status">{transferMessage}</p>
        <footer className="premium-design__footer">Se aplica a nuevas generaciones por descripción y con planos en PREMIUM. Las ediciones mantienen su orden específica. El encargo se conserva al guardar el proyecto. También puedes copiar o recuperar una copia JSON sin consumir IA.</footer>
      </div>
    </section>
  );
}
