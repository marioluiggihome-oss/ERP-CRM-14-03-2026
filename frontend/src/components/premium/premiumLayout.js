/* © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT] */
export const LEVELS = ['bajos', 'altos', 'sobremodulos'];
export const LEVEL_NAMES = { bajos: 'Bajos y columnas', altos: 'Altos', sobremodulos: 'Sobremódulos' };
export const newModule = () => ({ id: `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, wall: 'Pared 1', level: 'bajos', type: '', width: '', detail: '', confirmed: false });
export function layoutReview(rows = []) {
  const issues = [];
  const groups = new Map();
  rows.forEach((r, i) => {
    const width = Number(r.width);
    if (!String(r.wall || '').trim()) issues.push(`Módulo ${i + 1}: indica la pared.`);
    if (!String(r.type || '').trim()) issues.push(`Módulo ${i + 1}: indica el tipo.`);
    if (!LEVELS.includes(r.level)) issues.push(`Módulo ${i + 1}: nivel desconocido.`);
    if (!Number.isFinite(width) || width <= 0) issues.push(`Módulo ${i + 1}: falta un ancho válido en cm.`);
    if (!r.confirmed) issues.push(`Módulo ${i + 1}: lectura pendiente de confirmar.`);
    const key = `${String(r.wall || '').trim()} / ${LEVEL_NAMES[r.level] || r.level}`;
    const group = groups.get(key) || { label: key, total: 0, complete: true, rows: [] };
    group.complete = group.complete && Number.isFinite(width) && width > 0;
    group.total += Number.isFinite(width) && width > 0 ? width : 0;
    group.rows.push(r);
    groups.set(key, group);
  });
  return { issues, groups: [...groups.values()].map(g => ({ ...g, total: Math.round(g.total * 100) / 100 })) };
}
export function layoutPrompt(rows = []) {
  if (!rows.length) return '';
  const { groups } = layoutReview(rows);
  return 'RELACIÓN DE MÓDULOS DEL USUARIO (orden de izquierda a derecha en cada pared y nivel):\n' + groups.map(g => `${g.label}: ${g.rows.map(r => `${r.type || 'tipo pendiente'} · ${r.width || '?'} cm${r.detail ? ` · ${r.detail}` : ''}${r.confirmed ? '' : ' [PENDIENTE, NO INVENTAR]'}`).join(' → ')}`).join('\n') + '\nLos anchos de niveles distintos no se suman entre sí. Una columna ocupa también la altura: no colocar altos encima de ella salvo indicación expresa. Los totales son sumas de módulos, no medidas de pared ni validaciones de encaje.';
}
export function moveModule(rows, id, direction) {
  const next = [...rows], at = next.findIndex(r => r.id === id);
  const to = at + direction;
  if (at < 0 || to < 0 || to >= next.length) return rows;
  [next[at], next[to]] = [next[to], next[at]];
  return next;
}
