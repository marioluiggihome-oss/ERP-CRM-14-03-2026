/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
import { layoutPrompt, LEVELS } from './premiumLayout';
export const SPECIALTIES = [
  { id: 'arquitectura', name: 'Arquitectura', detail: 'Distribución, huecos y circulación', instruction: 'Respetar la envolvente, los huecos, las medidas aportadas y la circulación. No crear ventanas, puertas ni islas que no estén solicitadas.' },
  { id: 'interiorismo', name: 'Interiorismo', detail: 'Materiales, luz y composición', instruction: 'Coordinar los materiales especificados y la iluminación existente. Mantener las referencias exactas; no sustituir colores por nombres parecidos.' },
  { id: 'cocinas', name: 'Diseño de cocinas', detail: 'Módulos, frentes y equipamiento', instruction: 'Conservar orden, ancho, número de puertas y gavetas y tipo de integración de cada electrodoméstico. No reemplazar modelos especificados por otros decorativos.' },
  { id: 'carpinteria', name: 'Carpintería', detail: 'Encuentros, remates y montaje', instruction: 'Representar coherentemente los encuentros y remates indicados. No inventar espesores, holguras, mecanizados ni soluciones constructivas ausentes.' },
  { id: 'ebanisteria', name: 'Ebanistería', detail: 'Veta, cantos y continuidad', instruction: 'Respetar dirección y escala de veta y acabado de cantos cuando estén definidos. No transformar un laminado en madera maciza ni añadir molduras.' },
  { id: 'decoracion', name: 'Decoración', detail: 'Estilismo sin alterar el mobiliario', instruction: 'Añadir únicamente el estilismo solicitado, sin ocultar frentes, cotas, equipamiento ni zonas de paso y sin modificar muebles ni acabados.' },
];
export const ATMOSPHERES = [
  { id: 'fiel', name: 'Fiel al proyecto', note: 'Presentación limpia, con la decoración existente. No añadir objetos.' },
  { id: 'calido', name: 'Cálido y natural', note: 'Estilismo ligero con cerámica y textiles neutros; conservar todos los materiales y huecos del proyecto.' },
  { id: 'editorial', name: 'Editorial sobrio', note: 'Composición fotográfica cuidada, pocos objetos y luz equilibrada; mantener el diseño y las referencias exactas.' },
];
export const DEFAULT_BRIEF = Object.freeze({ specialties: ['arquitectura', 'interiorismo', 'cocinas', 'carpinteria', 'ebanisteria'], atmosphere: 'fiel', materials: '', construction: '' });
export function normalizeBrief(value) {
  const v = value && typeof value === 'object' ? value : {};
  return {
    specialties: Array.isArray(v.specialties) ? SPECIALTIES.filter(s => v.specialties.includes(s.id)).map(s => s.id) : [...DEFAULT_BRIEF.specialties],
    atmosphere: ATMOSPHERES.some(a => a.id === v.atmosphere) ? v.atmosphere : 'fiel',
    materials: typeof v.materials === 'string' ? v.materials.slice(0, 1200) : '',
    scene: ['concepto', 'croquis', 'obra'].includes(v.scene) ? v.scene : 'concepto',
    sourceNotes: typeof v.sourceNotes === 'string' ? v.sourceNotes.slice(0, 1200) : '',
    modules: Array.isArray(v.modules) ? v.modules.slice(0, 60).map((r, i) => {
      const row = r && typeof r === 'object' ? r : {};
      return { id: typeof row.id === 'string' ? row.id.slice(0, 100) : `mod-${i}`, wall: String(row.wall || '').slice(0, 80), level: LEVELS.includes(row.level) ? row.level : 'bajos', type: String(row.type || '').slice(0, 160), width: ['string','number'].includes(typeof row.width) ? String(row.width).slice(0, 20) : '', detail: String(row.detail || '').slice(0, 300), confirmed: row.confirmed === true };
    }) : [],
    installations: Array.isArray(v.installations) ? v.installations.slice(0, 40).map((row, i) => {
      const r = row && typeof row === 'object' ? row : {};
      const text = (key, limit) => String(r[key] ?? '').slice(0, limit);
      return { id: text('id', 100) || `point-${i}`, label: text('label', 100), wall: text('wall', 80), origin: text('origin', 160), height: text('height', 20), distance: text('distance', 20), trade: r.trade === 'fontaneria' ? 'fontaneria' : 'electricidad', confirmed: r.confirmed === true };
    }) : [],
    construction: typeof v.construction === 'string' ? v.construction.slice(0, 1200) : '',
  };
}
export function premiumDirection(value) {
  const v = normalizeBrief(value);
  return [
    'DIRECCIÓN DE DISEÑO PREMIUM (criterios de apoyo, no revisión profesional realizada):',
    `Objetivo: ${{concepto: 'propuesta conceptual; no presentar dimensiones inferidas como medidas reales', croquis: 'seguir el croquis aportado y la relación revisada', obra: 'integrar el proyecto sobre la foto de la obra identificada, conservando perspectiva y envolvente'}[v.scene]}.`,
    v.sourceNotes.trim() && `Identificación de referencias: ${v.sourceNotes.trim()}`,
    layoutPrompt(v.modules),
    'LECTURA DEL CROQUIS: las franjas de bajos, altos y sobremódulos pueden ser niveles de una MISMA pared. Relacionarlas por rótulos, flechas y cotas, no por su separación en el papel. En L o U, conservar esquinas y correspondencia de cada tramo; no duplicar rinconeras.',
    'FOTO DE OBRA: si se identifica expresamente como foto de la misma estancia, conservar perspectiva, paredes, pilares, huecos y techo. El croquis aporta los módulos y las muestras aportan materiales; no tratar una muestra como otra pared. No asumir que ejemplos distintos pertenecen a la misma obra.',
    'COTAS: los números tachados, ilegibles o contradictorios no son medidas confirmadas. No deducir escala exacta de una foto sin una dimensión real de referencia. No ocultar esas incertidumbres inventando cotas.',
    'El encargo explícito y los planos aportados tienen prioridad. No inferir medidas ni afirmar validación técnica o aptitud para fabricar a partir de una imagen.',
    ...SPECIALTIES.filter(s => v.specialties.includes(s.id)).map(s => `${s.name}: ${s.instruction}`),
    `Ambiente: ${ATMOSPHERES.find(a => a.id === v.atmosphere).note}`,
    v.materials.trim() && `Referencias de materiales del encargo: ${v.materials.trim()}`,
    v.construction.trim() && `Detalles constructivos aportados: ${v.construction.trim()}`,
  ].filter(Boolean).join('\n');
}
export function withPremiumDirection(motor, prompt, value) {
  return motor === 'premium' ? `${prompt}\n\n${premiumDirection(value)}` : prompt;
}

export function installationReady(point) {
  const dimension = value => /^\d+(?:[.,]\d+)?$/.test(String(value).trim()) && Number.isFinite(Number(String(value).replace(',', '.')));
  return Boolean(point.confirmed && point.label.trim() && point.wall.trim() && point.origin.trim() && dimension(point.height) && dimension(point.distance));
}
export function installationsCsv(rows) {
  if (!rows.length || !rows.every(installationReady)) throw new Error('Completa y confirma todos los puntos antes de exportar.');
  const cell = value => '"' + String(value).replace(/^[=+@\-]/, "'$&").replace(/"/g, '""') + '"';
  return '\ufeff' + [['Punto', 'Oficio', 'Pared', 'Origen de distancia horizontal', 'Altura desde suelo terminado (cm)', 'Distancia al eje (cm)'], ...rows.map(r => [r.label, r.trade, r.wall, r.origin, r.height, r.distance])].map(row => row.map(cell).join(';')).join('\r\n');
}
