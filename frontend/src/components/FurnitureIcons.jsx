// Iconos SVG para cada tipo de mueble del catálogo
// Basados en los dibujos técnicos de la tarifa

export const FURNITURE_ICONS = {
  // ALTOS - Muebles de pared superiores
  'ALTO_1_PUERTA': `<svg viewBox="0 0 40 50" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="36" height="46" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="4" y="4" width="32" height="42" rx="1" stroke="currentColor" stroke-width="1" fill="none"/>
    <circle cx="32" cy="25" r="2" fill="currentColor"/>
  </svg>`,
  
  'ALTO_2_PUERTAS': `<svg viewBox="0 0 60 50" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="56" height="46" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <line x1="30" y1="4" x2="30" y2="46" stroke="currentColor" stroke-width="1"/>
    <circle cx="26" cy="25" r="2" fill="currentColor"/>
    <circle cx="34" cy="25" r="2" fill="currentColor"/>
  </svg>`,
  
  'ALTO_1_VITRINA': `<svg viewBox="0 0 40 50" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="36" height="46" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="6" y="6" width="28" height="38" rx="1" stroke="currentColor" stroke-width="1" fill="none" stroke-dasharray="3 2"/>
    <line x1="6" y1="22" x2="34" y2="22" stroke="currentColor" stroke-width="1"/>
    <circle cx="32" cy="25" r="2" fill="currentColor"/>
  </svg>`,
  
  'ALTO_ABATIBLE': `<svg viewBox="0 0 60 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="56" height="36" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <line x1="5" y1="36" x2="55" y2="36" stroke="currentColor" stroke-width="2"/>
    <path d="M30 30 L30 20 L35 25 Z" fill="currentColor"/>
  </svg>`,

  // BAJOS - Muebles de base
  'BAJO_1_PUERTA': `<svg viewBox="0 0 40 45" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="36" height="36" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="4" y="4" width="32" height="32" rx="1" stroke="currentColor" stroke-width="1" fill="none"/>
    <circle cx="32" cy="20" r="2" fill="currentColor"/>
    <rect x="4" y="40" width="8" height="4" fill="currentColor" opacity="0.5"/>
    <rect x="28" y="40" width="8" height="4" fill="currentColor" opacity="0.5"/>
  </svg>`,
  
  'BAJO_2_PUERTAS': `<svg viewBox="0 0 60 45" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="56" height="36" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <line x1="30" y1="4" x2="30" y2="36" stroke="currentColor" stroke-width="1"/>
    <circle cx="26" cy="20" r="2" fill="currentColor"/>
    <circle cx="34" cy="20" r="2" fill="currentColor"/>
    <rect x="4" y="40" width="8" height="4" fill="currentColor" opacity="0.5"/>
    <rect x="48" y="40" width="8" height="4" fill="currentColor" opacity="0.5"/>
  </svg>`,
  
  'BAJO_CAJONES': `<svg viewBox="0 0 50 45" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="46" height="36" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <line x1="4" y1="14" x2="46" y2="14" stroke="currentColor" stroke-width="1"/>
    <line x1="4" y1="26" x2="46" y2="26" stroke="currentColor" stroke-width="1"/>
    <rect x="20" y="6" width="10" height="3" rx="1" fill="currentColor"/>
    <rect x="20" y="18" width="10" height="3" rx="1" fill="currentColor"/>
    <rect x="20" y="30" width="10" height="3" rx="1" fill="currentColor"/>
    <rect x="4" y="40" width="8" height="4" fill="currentColor" opacity="0.5"/>
    <rect x="38" y="40" width="8" height="4" fill="currentColor" opacity="0.5"/>
  </svg>`,

  'BAJO_RINCON': `<svg viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 2 L58 2 L58 58 L30 58 L30 30 L2 30 Z" stroke="currentColor" stroke-width="2" fill="none"/>
    <circle cx="44" cy="30" r="2" fill="currentColor"/>
  </svg>`,

  // COLUMNAS Y SEMICOLUMNAS
  'SEMICOLUMNA_1_PUERTA': `<svg viewBox="0 0 35 80" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="31" height="72" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="4" y="4" width="27" height="68" rx="1" stroke="currentColor" stroke-width="1" fill="none"/>
    <line x1="4" y1="24" x2="31" y2="24" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2 2"/>
    <line x1="4" y1="44" x2="31" y2="44" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2 2"/>
    <line x1="4" y1="54" x2="31" y2="54" stroke="currentColor" stroke-width="0.5" stroke-dasharray="2 2"/>
    <circle cx="28" cy="36" r="2" fill="currentColor"/>
    <rect x="4" y="76" width="6" height="3" fill="currentColor" opacity="0.5"/>
    <rect x="25" y="76" width="6" height="3" fill="currentColor" opacity="0.5"/>
  </svg>`,
  
  'SEMICOLUMNA_CAJONES': `<svg viewBox="0 0 35 80" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="31" height="72" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <line x1="4" y1="20" x2="31" y2="20" stroke="currentColor" stroke-width="1"/>
    <line x1="4" y1="38" x2="31" y2="38" stroke="currentColor" stroke-width="1"/>
    <line x1="4" y1="56" x2="31" y2="56" stroke="currentColor" stroke-width="1"/>
    <rect x="14" y="8" width="7" height="3" rx="1" fill="currentColor"/>
    <rect x="14" y="26" width="7" height="3" rx="1" fill="currentColor"/>
    <rect x="14" y="44" width="7" height="3" rx="1" fill="currentColor"/>
    <rect x="14" y="62" width="7" height="3" rx="1" fill="currentColor"/>
    <rect x="4" y="76" width="6" height="3" fill="currentColor" opacity="0.5"/>
    <rect x="25" y="76" width="6" height="3" fill="currentColor" opacity="0.5"/>
  </svg>`,
  
  'COLUMNA_COMPLETA': `<svg viewBox="0 0 35 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="31" height="92" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <line x1="2" y1="50" x2="33" y2="50" stroke="currentColor" stroke-width="1"/>
    <rect x="4" y="4" width="27" height="44" rx="1" stroke="currentColor" stroke-width="1" fill="none"/>
    <rect x="4" y="52" width="27" height="40" rx="1" stroke="currentColor" stroke-width="1" fill="none"/>
    <circle cx="28" cy="26" r="2" fill="currentColor"/>
    <circle cx="28" cy="72" r="2" fill="currentColor"/>
    <rect x="4" y="96" width="6" height="3" fill="currentColor" opacity="0.5"/>
    <rect x="25" y="96" width="6" height="3" fill="currentColor" opacity="0.5"/>
  </svg>`,
  
  'COLUMNA_HORNO': `<svg viewBox="0 0 45 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="41" height="92" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="6" y="30" width="33" height="35" rx="2" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="10" y="35" width="25" height="20" rx="1" stroke="currentColor" stroke-width="1" fill="none"/>
    <circle cx="22" cy="60" r="2" fill="currentColor"/>
    <rect x="4" y="96" width="6" height="3" fill="currentColor" opacity="0.5"/>
    <rect x="35" y="96" width="6" height="3" fill="currentColor" opacity="0.5"/>
  </svg>`,

  // PUERTAS Y VITRINAS
  'PUERTA': `<svg viewBox="0 0 30 50" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="26" height="46" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <circle cx="22" cy="25" r="2" fill="currentColor"/>
    <line x1="4" y1="4" x2="4" y2="46" stroke="currentColor" stroke-width="3"/>
  </svg>`,
  
  'VITRINA': `<svg viewBox="0 0 30 50" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="26" height="46" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
    <rect x="5" y="5" width="20" height="40" rx="1" stroke="currentColor" stroke-width="1" fill="none" stroke-dasharray="3 2"/>
    <line x1="5" y1="25" x2="25" y2="25" stroke="currentColor" stroke-width="1"/>
    <circle cx="22" cy="25" r="2" fill="currentColor"/>
  </svg>`,

  // COSTADOS Y REMATES
  'COSTADO': `<svg viewBox="0 0 15 60" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="11" height="56" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
  </svg>`,
  
  'ZOCALO': `<svg viewBox="0 0 80 15" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="76" height="11" rx="1" stroke="currentColor" stroke-width="2" fill="none"/>
  </svg>`,

  // ENCIMERAS
  'ENCIMERA': `<svg viewBox="0 0 80 10" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="76" height="6" rx="1" stroke="currentColor" stroke-width="2" fill="currentColor" fill-opacity="0.2"/>
  </svg>`,

  // DEFAULT
  'DEFAULT': `<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="36" height="36" rx="2" stroke="currentColor" stroke-width="2" fill="none"/>
    <circle cx="20" cy="20" r="5" stroke="currentColor" stroke-width="1" fill="none"/>
  </svg>`
};

// Función para determinar el icono según el código del producto
export const getProductIcon = (code, name) => {
  const c = (code || '').toUpperCase();
  const n = (name || '').toLowerCase();
  
  // SEMICOLUMNAS
  if (c.includes('SC') || c.includes('SM')) {
    if (n.includes('cajón') || n.includes('cajon') || c.includes('CLH') || c.includes('CLM')) {
      return FURNITURE_ICONS.SEMICOLUMNA_CAJONES;
    }
    return FURNITURE_ICONS.SEMICOLUMNA_1_PUERTA;
  }
  
  // COLUMNAS
  if (c.includes('COL') || n.includes('columna')) {
    if (n.includes('horno') || n.includes('microondas')) {
      return FURNITURE_ICONS.COLUMNA_HORNO;
    }
    return FURNITURE_ICONS.COLUMNA_COMPLETA;
  }
  
  // ALTOS
  if (c.match(/^\d+A/) || n.includes('alto')) {
    if (c.includes('2P') || n.includes('2 puerta')) {
      return FURNITURE_ICONS.ALTO_2_PUERTAS;
    }
    if (c.includes('V') || n.includes('vitrina')) {
      return FURNITURE_ICONS.ALTO_1_VITRINA;
    }
    if (n.includes('abatible')) {
      return FURNITURE_ICONS.ALTO_ABATIBLE;
    }
    return FURNITURE_ICONS.ALTO_1_PUERTA;
  }
  
  // BAJOS
  if (c.match(/^\d+B/) || n.includes('bajo')) {
    if (c.includes('2P') || n.includes('2 puerta')) {
      return FURNITURE_ICONS.BAJO_2_PUERTAS;
    }
    if (c.includes('CAJ') || n.includes('cajón') || n.includes('cajon')) {
      return FURNITURE_ICONS.BAJO_CAJONES;
    }
    if (n.includes('rincón') || n.includes('rincon') || n.includes('esquina')) {
      return FURNITURE_ICONS.BAJO_RINCON;
    }
    return FURNITURE_ICONS.BAJO_1_PUERTA;
  }
  
  // PUERTAS Y VITRINAS
  if (c.includes('PTA') || n.includes('puerta')) {
    return FURNITURE_ICONS.PUERTA;
  }
  if (c.includes('VIT') || n.includes('vitrina')) {
    return FURNITURE_ICONS.VITRINA;
  }
  
  // COSTADOS
  if (c.includes('COST') || n.includes('costado')) {
    return FURNITURE_ICONS.COSTADO;
  }
  
  // ZÓCALOS
  if (c.includes('ZOC') || n.includes('zócalo') || n.includes('zocalo')) {
    return FURNITURE_ICONS.ZOCALO;
  }
  
  // ENCIMERAS
  if (c.includes('ENC') || n.includes('encimera')) {
    return FURNITURE_ICONS.ENCIMERA;
  }
  
  return FURNITURE_ICONS.DEFAULT;
};

export default FURNITURE_ICONS;
