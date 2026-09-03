/*
 * Entrada de plataforma. Centraliza la detección por dominio o ruta simulada
 * para que acceso, título, autenticación y carcasa usen exactamente la misma
 * identidad.
 */

export const PLATFORM_ENTRIES = {
  carpinter: {
    key: 'carpinter',
    brand: 'carpinteros',
    name: 'CARPINTER.IO',
    title: 'CARPINTER.IO · Acceso profesional',
    color: '#aa7257',
    background: '#17130F',
    icon: '/carpinter-logo-icon.png',
    favicon: '/carpinter-logo-icon.png',
  },
  studio3k: {
    key: 'studio3k',
    brand: 'studio3k',
    name: 'STUDIO3K.IO',
    title: 'STUDIO3K.IO · Acceso profesional',
    color: '#5f78ca',
    background: '#0b0b14',
    icon: '/studio3k-logo.png',
    favicon: '/studio3k-logo.png',
  },
};

export function detectPlatformEntry(locationObject = (typeof window !== 'undefined' ? window.location : null)) {
  if (!locationObject) return null;
  try {
    const host = String(locationObject.hostname || '').toLowerCase();
    const path = String(locationObject.pathname || '').toLowerCase().replace(/\/+$/, '');
    const params = new URLSearchParams(locationObject.search || '');
    const brand = String(params.get('brand') || params.get('platform') || '').toLowerCase();

    const carpinter = host.includes('carpinter.io') || host.includes('carpenter.io')
      || brand === 'carpinter' || brand === 'carpinteros'
      || params.has('carp') || params.has('carpinteros')
      || path === '/carp' || path.startsWith('/carp/') || path === '/carpinter' || path.startsWith('/carpinter/');
    if (carpinter) return PLATFORM_ENTRIES.carpinter;

    const studio3k = host.includes('studio3k.io') || host.includes('estudio3k.io')
      || brand === 'studio3k' || params.has('s3k') || params.has('studio3k')
      || path === '/s3k' || path.startsWith('/s3k/') || path === '/studio3k' || path.startsWith('/studio3k/');
    if (studio3k) return PLATFORM_ENTRIES.studio3k;
  } catch {
    return null;
  }
  return null;
}

export function platformEntryKey() {
  return detectPlatformEntry()?.key || '';
}

export function platformLoginPayload() {
  const platform = platformEntryKey();
  return platform ? { platformEntry: platform } : {};
}

export function applyPlatformDocumentIdentity(entry = detectPlatformEntry()) {
  if (typeof document === 'undefined' || !entry) return;
  document.title = entry.title;
  document.documentElement.dataset.platform = entry.key;
  const theme = document.querySelector('meta[name="theme-color"]');
  if (theme) theme.setAttribute('content', entry.background);
  const favicon = document.querySelector('link[rel~="icon"]');
  if (favicon && entry.favicon) favicon.setAttribute('href', entry.favicon);
}
