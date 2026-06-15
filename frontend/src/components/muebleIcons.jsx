/**
 * muebleIcons.jsx — iconos de línea por tipo de mueble (catálogo MV).
 * Asocia cada mueble a un dibujo según su familia/código/nombre.
 * Uso: <MuebleIcon mueble={producto} size={36} />  ó  classifyMueble(p) -> tipo.
 */
import React from 'react';

// Clasifica un mueble en un "tipo" de icono según categoría + código + nombre.
// El orden importa: primero lo específico, luego lo genérico.
export function classifyMueble(p) {
  const hay = `${p?.category || ''} ${p?.code || ''} ${p?.reference || ''} ${p?.name || ''}`.toUpperCase();
  const code = `${p?.code || p?.reference || ''}`.toUpperCase().trim();

  if (/FREGADERO/.test(hay) || /^BF/.test(code)) return 'fregadero';
  if (/CAMPANA/.test(hay) || /^ASC/.test(code)) return 'campana';
  if (/ESCURRE/.test(hay)) return 'escurreplatos';
  if (/MICRO/.test(hay) || /HORNO/.test(hay) || /CALENTADOR|CALDERA|SOBREFRIGO/.test(hay)) return 'horno';
  if (/VITRINA|VITRINA INGLESA|CRISTAL/.test(hay)) return 'vitrina';
  if (/BOTELLER/.test(hay) || /^BO[ASC]/.test(code)) return 'botellero';
  if (/RINCON|RINCÓN|CHAFLAN|ESCUADRA|CIEGO/.test(hay)) return 'rincon';
  if (/CAJON|CAJONES|GAVETA/.test(hay)) return 'cajones';
  if (/FRIGO|DESPENSER|ESCOBERO/.test(hay)) return 'columna';
  if (/MEDIACOLUMNA|MEDIA COLUMNA|MEDIA PUERTA|MEDIACOL/.test(hay) || /^M[0-9MVPGH]/.test(code)) return 'mediacolumna';
  if (/COLUMNA/.test(hay) || /^C[DHF]/.test(code)) return 'columna';
  if (/ALTILLO|BALDA|SOBREENCIMERA|SOBREENC/.test(hay) || /^L[DV0-9]/.test(code) || /^BAL/.test(code) || /^S[CV0-9]/.test(code)) return 'altillo';
  if (/SOBREM[OÓ]DULO/.test(hay)) return 'altillo';
  if (/REGLETA|LATERAL|COSTADO|TECHO|Z[OÓ]CALO|ZOC|ESTANTE|MOSTRADOR|CORNISA|PORTALUZ|ENCIMERA|COPETE|PERFIL|LINEAL/.test(hay)) return 'lineal';
  if (/PUERTA|^P[VR]?\d/.test(hay) || /^P[VR]?\d/.test(code)) return 'puerta';
  if (/^A/.test(code) || /\bALTO\b/.test(hay)) return 'alto';
  if (/^B/.test(code) || /\bBAJO\b/.test(hay)) return 'bajo';
  return 'box';
}

// Nº de puertas según el código: los códigos con sufijo "D/I" (derecha/izquierda)
// son de 1 puerta; el resto (p.ej. A60, B60 sin D/I) son de 2 puertas.
export function doorCount(p) {
  const code = `${p?.code || p?.reference || ''}`.toUpperCase();
  return /D\/I/.test(code) ? 1 : 2;
}

const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round' };

// Cada icono: contenido SVG (viewBox 0 0 24 24).
const ICONS = {
  bajo: (
    <>
      <rect x="3.5" y="7" width="17" height="13" rx="1" />
      <line x1="12" y1="7" x2="12" y2="20" />
      <circle cx="10.3" cy="13.5" r="0.6" /><circle cx="13.7" cy="13.5" r="0.6" />
    </>
  ),
  // 1 puerta (códigos D/I): sin división central, tirador a un lado
  bajo1: (
    <>
      <rect x="3.5" y="7" width="17" height="13" rx="1" />
      <circle cx="18.2" cy="13.5" r="0.6" />
    </>
  ),
  alto: (
    <>
      <rect x="4" y="4" width="16" height="11" rx="1" />
      <line x1="12" y1="4" x2="12" y2="15" />
      <circle cx="10.5" cy="12.5" r="0.6" /><circle cx="13.5" cy="12.5" r="0.6" />
    </>
  ),
  // 1 puerta (códigos D/I): sin división central, tirador a un lado
  alto1: (
    <>
      <rect x="4" y="4" width="16" height="11" rx="1" />
      <circle cx="18.5" cy="12.5" r="0.6" />
    </>
  ),
  cajones: (
    <>
      <rect x="3.5" y="5" width="17" height="15" rx="1" />
      <line x1="3.5" y1="10" x2="20.5" y2="10" />
      <line x1="3.5" y1="14.5" x2="20.5" y2="14.5" />
      <line x1="10" y1="7.5" x2="14" y2="7.5" /><line x1="10" y1="12.2" x2="14" y2="12.2" /><line x1="10" y1="17.2" x2="14" y2="17.2" />
    </>
  ),
  vitrina: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="1" />
      <line x1="12" y1="4" x2="12" y2="20" />
      <line x1="5.5" y1="6" x2="10.5" y2="11" /><line x1="13.5" y1="13" x2="18.5" y2="18" />
    </>
  ),
  fregadero: (
    <>
      <rect x="3.5" y="8" width="17" height="12" rx="1" />
      <ellipse cx="12" cy="5" rx="5.5" ry="2" />
      <line x1="12" y1="3" x2="12" y2="8" />
    </>
  ),
  horno: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="1" />
      <rect x="6.5" y="8.5" width="11" height="9" rx="0.8" />
      <line x1="8" y1="6.2" x2="16" y2="6.2" />
    </>
  ),
  campana: (
    <>
      <path d="M5 9 L8 5 H16 L19 9 Z" />
      <line x1="3.5" y1="9" x2="20.5" y2="9" />
      <line x1="9" y1="12" x2="9" y2="13.5" /><line x1="15" y1="12" x2="15" y2="13.5" />
    </>
  ),
  escurreplatos: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="1" />
      <line x1="7" y1="10" x2="17" y2="10" /><line x1="7" y1="13.5" x2="17" y2="13.5" />
      <line x1="9" y1="10" x2="9" y2="13.5" /><line x1="12" y1="10" x2="12" y2="13.5" /><line x1="15" y1="10" x2="15" y2="13.5" />
    </>
  ),
  columna: (
    <>
      <rect x="6.5" y="2.5" width="11" height="19" rx="1" />
      <line x1="6.5" y1="9" x2="17.5" y2="9" /><line x1="6.5" y1="15" x2="17.5" y2="15" />
      <circle cx="15.2" cy="12" r="0.6" />
    </>
  ),
  mediacolumna: (
    <>
      <rect x="6.5" y="5" width="11" height="14" rx="1" />
      <line x1="6.5" y1="12" x2="17.5" y2="12" />
      <circle cx="15.2" cy="9" r="0.6" /><circle cx="15.2" cy="15" r="0.6" />
    </>
  ),
  botellero: (
    <>
      <rect x="7.5" y="3" width="9" height="18" rx="1" />
      <path d="M8 6 L16 9 M16 6 L8 9 M8 11 L16 14 M16 11 L8 14 M8 16 L16 19 M16 16 L8 19" />
    </>
  ),
  rincon: (
    <>
      <path d="M3.5 7 H13 V13 H20.5 V20.5 H3.5 Z" />
      <line x1="13" y1="13" x2="3.5" y2="7" opacity="0" />
      <circle cx="6" cy="16.5" r="0.6" />
    </>
  ),
  altillo: (
    <>
      <rect x="3.5" y="8" width="17" height="7" rx="1" />
      <line x1="6" y1="15" x2="6" y2="18" /><line x1="18" y1="15" x2="18" y2="18" />
    </>
  ),
  puerta: (
    <>
      <rect x="7.5" y="3" width="9" height="18" rx="1.2" />
      <circle cx="14.2" cy="12" r="0.7" />
    </>
  ),
  lineal: (
    <>
      <rect x="3" y="10.5" width="18" height="3" rx="1" />
    </>
  ),
  box: (
    <>
      <rect x="4" y="5" width="16" height="15" rx="1" />
      <line x1="12" y1="5" x2="12" y2="20" />
    </>
  ),
};

export function MuebleIcon({ mueble, type, size = 24, className = '' }) {
  let t = type || classifyMueble(mueble);
  // Para alto/bajo: 1 puerta (código D/I) usa la variante sin división central
  if ((t === 'alto' || t === 'bajo') && doorCount(mueble) === 1) t = `${t}1`;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className}
      {...S} aria-hidden="true">
      {ICONS[t] || ICONS.box}
    </svg>
  );
}

// ── Nomenclatura de códigos MV (Muebles Valencia) ──────────────────────────────
// Referencia rápida: qué significa cada código y su dibujo/icono. Agrupada por zona.
export const NOMENCLATURA = [
  { grupo: 'BAJOS', items: [
    { code: 'B', type: 'bajo', desc: 'Bajo (1 balda). Ej. B25D/I…B100' },
    { code: 'BF', type: 'fregadero', desc: 'Bajo fregadero (opción chapa antihumedad = BFC)' },
    { code: 'BPC', type: 'bajo', desc: 'Bajo puerta y cajón' },
    { code: 'BC', type: 'cajones', desc: 'Bajo 5 cajones' },
    { code: 'BCG', type: 'cajones', desc: 'Bajo 3 cajones + 1 gaveta' },
    { code: 'BGC', type: 'cajones', desc: 'Bajo 2 gavetas + 1 cajón' },
    { code: 'BCGF', type: 'cajones', desc: 'Bajo 2 cajones + 1 gaveta + 1 frente' },
    { code: 'BGF', type: 'cajones', desc: 'Bajo 2 gavetas + 1 frente' },
    { code: 'BRI', type: 'rincon', desc: 'Bajo rincón escuadra, puertas independientes (93×95)' },
    { code: 'BRU', type: 'rincon', desc: 'Bajo rincón escuadra, puertas unidas (95×95)' },
    { code: 'BR', type: 'rincon', desc: 'Bajo rincón ciego (indicar situación de la puerta)' },
    { code: 'BH', type: 'horno', desc: 'Bajo horno (frente fijo inferior 9,5 cm)' },
    { code: 'BHC', type: 'horno', desc: 'Bajo horno con cajón' },
    { code: 'BHZ', type: 'horno', desc: 'Bajo horno con cajón en zócalo' },
    { code: 'BHG', type: 'horno', desc: 'Bajo horno con gaveta' },
    { code: 'BT', type: 'bajo', desc: 'Bajo terminal (BTS lats. al suelo, BTZ con zócalo, BTP en chaflán)' },
  ]},
  { grupo: 'ALTOS', items: [
    { code: 'A', type: 'alto', desc: 'Alto (alturas 70 y 90). Ej. A25D/I…A100' },
    { code: 'AV', type: 'vitrina', desc: 'Alto vitrina' },
    { code: 'AE', type: 'escurreplatos', desc: 'Alto escurreplatos' },
    { code: 'AM / AMF', type: 'horno', desc: 'Alto microondas (AMF con frente, A=90 y 110 F=45)' },
    { code: 'ACA', type: 'horno', desc: 'Alto calentador' },
    { code: 'ACC', type: 'horno', desc: 'Alto caldera (A=90·110 F=45)' },
    { code: 'ASF', type: 'horno', desc: 'Alto sobre-frigo (ASF60A abat. salvacorte, ASF60F abat. free)' },
    { code: 'ASCE / ASC', type: 'campana', desc: 'Alto campana (ASCE extraplana, ASC clásica)' },
    { code: 'AR', type: 'rincon', desc: 'Alto rincón ciego' },
    { code: 'ARI / ARU', type: 'rincon', desc: 'Alto rincón escuadra (ARI indep., ARU unidas)' },
    { code: 'ARC / ARCV', type: 'rincon', desc: 'Alto rincón chaflán' },
    { code: 'AD', type: 'box', desc: 'Alto decorativo (sin puerta)' },
    { code: 'AT', type: 'alto', desc: 'Alto terminal' },
    { code: 'AA', type: 'alto', desc: 'Alto abatible (2 ptas. abat. free)' },
    { code: 'AC / ACP / ACPJ', type: 'alto', desc: 'Alto combinado / combinado plus / plus J' },
  ]},
  { grupo: 'ALTILLOS / SOBREENCIMERA', items: [
    { code: 'L', type: 'altillo', desc: 'Altillo (abatible free)' },
    { code: 'LV', type: 'vitrina', desc: 'Altillo vitrina' },
    { code: 'LD', type: 'altillo', desc: 'Altillo decorativo' },
    { code: 'S', type: 'altillo', desc: 'Sobreencimera (alturas 127 y 147)' },
    { code: 'SV', type: 'vitrina', desc: 'Sobreencimera vitrina' },
    { code: 'SC', type: 'cajones', desc: 'Sobreencimera cajón' },
    { code: 'SVC', type: 'vitrina', desc: 'Sobreencimera vitrina cajón' },
  ]},
  { grupo: 'COLUMNAS / MEDIACOLUMNAS', items: [
    { code: 'CD', type: 'columna', desc: 'Columna despensero / escobero (alturas 200 y 220)' },
    { code: 'CF', type: 'columna', desc: 'Columna frigo' },
    { code: 'CH', type: 'horno', desc: 'Columna horno (CHPC puerta+cajón, CHGC gaveta, CHC cajones)' },
    { code: 'CHM', type: 'horno', desc: 'Columna horno+microondas' },
    { code: 'M', type: 'mediacolumna', desc: 'Mediacolumna (altura 130)' },
    { code: 'MPG', type: 'mediacolumna', desc: 'Media puerta gaveta' },
    { code: 'MPH / MPM', type: 'horno', desc: 'Mediacolumna horno / microondas' },
    { code: 'MV', type: 'vitrina', desc: 'Mediacolumna vitrina' },
    { code: 'MVG', type: 'vitrina', desc: 'Mediacolumna vitrina gaveta' },
  ]},
  { grupo: 'PUERTAS', items: [
    { code: 'P', type: 'puerta', desc: 'Puerta (matriz alto × ancho: P25…P60)' },
    { code: 'PV', type: 'vitrina', desc: 'Puerta vitrina' },
    { code: 'PVI', type: 'vitrina', desc: 'Puerta vitrina inglesa' },
    { code: 'PR', type: 'vitrina', desc: 'Rejilla confesionario (gris o blanca)' },
  ]},
  { grupo: 'COMPLEMENTOS / LINEALES', items: [
    { code: 'BOA/BOS/BOC', type: 'botellero', desc: 'Botelleros (anchos 7 y 9)' },
    { code: 'BAL', type: 'altillo', desc: 'Balda aérea (fondos 35/50/60)' },
    { code: 'TEC', type: 'lineal', desc: 'Techo color (fondos 35/50/60)' },
    { code: 'LC / CC', type: 'lineal', desc: 'Laterales / costados color' },
    { code: 'RA / RM', type: 'lineal', desc: 'Regletas (color / melamina)' },
    { code: 'COR / ZOC / POR', type: 'lineal', desc: 'Cornisa / zócalo / portaluz (enteros o medios)' },
    { code: 'ENC / MOSE / COPM', type: 'lineal', desc: 'Encimera / mostrador / copete' },
  ]},
];

// Aclaraciones de sufijos comunes en los códigos.
export const NOMENCLATURA_NOTAS = [
  'D/I = versión Derecha o Izquierda (indicar al pedir).',
  '* = variante (p. ej. 2 puertas) según el catálogo.',
  '-70 / -90 = altura del módulo en cm (altos, altillos…).',
  '-200 / -220 = altura de columnas; -127 / -147 = sobreencimera.',
  'Nº del código = ancho en cm (B60 = 60 cm de ancho).',
];

export default MuebleIcon;
