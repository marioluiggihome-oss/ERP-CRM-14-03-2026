/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * Arnés de las pruebas de pantalla: entra en el ERP sin backend y sin datos.
 *
 * TODA LA RED VA SIMULADA. Ninguna prueba de pantalla puede depender de que
 * haya un Mongo levantado ni de lo que hubiera dentro: si hiciera falta, no se
 * ejecutarían en el CI, y una prueba que no se ejecuta no protege nada — que es
 * exactamente lo que le pasó a estos candados hasta el 23/08/2026.
 *
 * El usuario simulado es MASTER a propósito: es quien ve todos los botones, y
 * son los botones de más los que se salen de una pantalla estrecha.
 */

const USUARIO_MASTER = {
  id: 'u-pruebas', username: 'master', name: 'Master de pruebas', role: 'master',
  isMaster: true, isAdmin: true, isPrimaryAdmin: true, isTienda: false, isMontador: false,
  canAccessArmarios: true, canAccessCRM: true, canAccessFabrica: true, canUseArmarios2: true,
};

/** Corta TODA llamada a `/api/` y devuelve algo inofensivo. */
async function simularBackend(page, extras = {}) {
  await page.route('**/*', async (ruta) => {
    const url = ruta.request().url();
    if (!/\/api\//.test(url)) return ruta.continue();
    const json = (cuerpo) => ruta.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(cuerpo),
    });
    for (const [patron, cuerpo] of Object.entries(extras)) {
      if (new RegExp(patron).test(url)) return json(cuerpo);
    }
    if (/auth\/login/.test(url)) {
      return json({ success: true, user: USUARIO_MASTER, tokens: { access_token: 't', refresh_token: 'r' } });
    }
    if (/\/api\/users/.test(url)) return json([USUARIO_MASTER]);
    if (/\/api\/(products|materials|libraries)/.test(url)) return json([]);
    return json({});
  });
}

/** Entra como master y deja la app en la pantalla de inicio. */
async function entrar(page, base) {
  await simularBackend(page);
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.locator('input[type=text]').first().fill('master');
  await page.locator('input[type=password]').first().fill('lo-que-sea');
  await page.getByRole('button', { name: /entrar/i }).click();
  await page.getByText(/elige un m[oó]dulo/i).waitFor({ timeout: 20000 });
}

/**
 * El contenedor que de verdad se desliza para un elemento dado.
 *
 * Se busca subiendo por el DOM en vez de con un selector de clases: una prueba
 * clavada a `.max-lg\:overflow-x-auto` se rompe el día que alguien renombra una
 * clase de Tailwind sin haber roto nada, y eso es un rojo que no significa nada.
 */
function contenedorQueSeDesliza(locator) {
  return locator.evaluate((el) => {
    for (let n = el.parentElement; n; n = n.parentElement) {
      if (n.scrollWidth > n.clientWidth + 4) {
        return { desliza: true, scrollWidth: n.scrollWidth, clientWidth: n.clientWidth };
      }
      if (n === document.body) break;
    }
    return { desliza: false };
  });
}

/** Desplaza hasta el final la tira que contiene a `locator`. */
function deslizarHastaElFinal(locator) {
  return locator.evaluate((el) => {
    for (let n = el.parentElement; n; n = n.parentElement) {
      if (n.scrollWidth > n.clientWidth + 4) { n.scrollLeft = n.scrollWidth; return true; }
      if (n === document.body) break;
    }
    return false;
  });
}

module.exports = {
  USUARIO_MASTER, simularBackend, entrar, contenedorQueSeDesliza, deslizarHastaElFinal,
};
