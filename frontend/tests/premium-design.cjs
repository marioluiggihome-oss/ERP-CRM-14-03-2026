/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const dir = path.join(__dirname, '../src/components/premium');
const asUrl = text => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64');
(async () => {
  const layoutUrl = asUrl(fs.readFileSync(path.join(dir, 'premiumLayout.js'), 'utf8'));
  const layout = await import(layoutUrl);
  const briefUrl = asUrl(fs.readFileSync(path.join(dir, 'premiumBrief.js'), 'utf8').replace("'./premiumLayout'", JSON.stringify(layoutUrl)));
  const brief = await import(briefUrl);
  const report = await import(asUrl(fs.readFileSync(path.join(dir, 'premiumInstallationReport.js'), 'utf8').replace("'./premiumBrief'", JSON.stringify(briefUrl))));
  for (const motor of ['ia0', 'ia1', 'ia7']) assert.equal(brief.withPremiumDirection(motor, 'encargo original', { materials: 'Agave' }), 'encargo original');
  const sample = [
    { id: 'a', wall: 'Pared 1', level: 'bajos', type: 'Lavavajillas', width: '60', detail: '', confirmed: true },
    { id: 'b', wall: 'Pared 1', level: 'bajos', type: 'Fregadero', width: '90', detail: '2 gavetas', confirmed: true },
    { id: 'c', wall: 'Pared 1', level: 'altos', type: 'Alto', width: '120', detail: '', confirmed: true },
  ];
  assert.deepEqual(layout.layoutReview(sample).groups.map(g => g.total), [150, 120]);
  assert.equal(layout.layoutReview(sample).issues.length, 0);
  for (const width of ['', '0', '-1', 'Infinity', 'NaN']) assert(layout.layoutReview([{ ...sample[0], width }]).issues.some(i => i.includes('ancho')));
  assert(layout.layoutReview([{ ...sample[0], confirmed: false }]).issues.some(i => i.includes('confirmar')));
  const moved = layout.moveModule(sample, 'a', 1);
  assert.deepEqual(moved.map(r => r.id), ['b', 'a', 'c']);
  assert.deepEqual(sample.map(r => r.id), ['a', 'b', 'c']);
  assert.equal(layout.moveModule(sample, 'a', -1), sample);
  const normalized = brief.normalizeBrief({ materials: 'Alvic Agave', atmosphere: 'wrong', specialties: ['ebanisteria', 'unknown'], modules: sample });
  assert.equal(normalized.atmosphere, 'fiel'); assert.deepEqual(normalized.specialties, ['ebanisteria']);
  const prompt = brief.withPremiumDirection('premium', 'Mi cocina', normalized);
  for (const required of ['Alvic Agave','Lavavajillas · 60 cm','Fregadero · 90 cm','2 gavetas','MISMA pared','FOTO DE OBRA']) assert(prompt.includes(required), required);
  assert.equal(brief.normalizeBrief(null).modules.length, 0);
  assert.equal(brief.normalizeBrief({ modules: Array(65).fill(null) }).modules.length, 60);
  const point = { id: 'e1', label: 'Luz bajo altos', wall: 'Fondo', origin: 'Pared izquierda hacia derecha', height: '165', distance: '120,5', trade: 'electricidad', confirmed: true };
  assert(brief.installationReady(point));
  assert.throws(() => report.installationReportData([{ ...point, confirmed: false }]));
  const groups = report.installationReportData([point, { ...point, id: 'f1', label: 'Agua fría', trade: 'fontaneria' }]);
  assert.equal(groups.length, 2);
  assert.deepEqual(groups[0].body[0].slice(-2), ['165 cm', '120,5 cm']);
  assert.equal(groups[1].body[0][0], 'Agua fría');
  for (const distance of ['', '-1', 'Infinity', '1e4']) assert(!brief.installationReady({ ...point, distance }));
  assert(!brief.installationReady({ ...point, origin: '' }));
  assert.throws(() => brief.installationsCsv([{ ...point, confirmed: false }]));
  assert(brief.installationsCsv([point]).includes('120,5'));
  assert.deepEqual(brief.normalizeBrief({ installations: [point] }).installations, [point]);
  assert(brief.installationsCsv([{ ...point, label: '=FORMULA' }]).includes("'=FORMULA"));
  console.log('PREMIUM: aislamiento, cotas, niveles, orden, referencias y recuperación comprobados.');
})().catch(e => { console.error(e); process.exitCode = 1; });
