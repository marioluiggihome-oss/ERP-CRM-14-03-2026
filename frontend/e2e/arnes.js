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
  // Sin este permiso el Estudio 3D NO SE PINTA —`App.js` lo cierra con
  // `currentTab === 'renderStudio' && currentUser?.canUseAIAnalysis`— y la
  // pantalla se queda en blanco sin dar ningún error. Costó un rato entenderlo.
  canUseAIAnalysis: true, canUseCocinasAI: true,
  // El resto de permisos de un master de verdad. Sin ellos el menú sale corto
  // y los módulos que faltan no se pueden ni abrir para medirlos — es lo que
  // pasó con Archivo, que no aparecía y la prueba se quedaba esperando un
  // botón que no existía.
  canAccessAlmacen: true, canAccessArchivo: true, canAccessExpediente: true,
  canAccessFloor: true, canAccessGastos: true, canAccessInvoices: true,
  canAccessMando: true, canAccessMaster: true, canAccessMontajes: true,
  canAccessPedidos: true, canAccessRentabilidad: true,
  canUseAgentesIA: true, canUseCascos: true, canUseDigitalizador: true,
  canUsePresupuestador2: true,
};

// Un PNG de verdad, 4x3, para que el render simulado tenga proporción y ocupe
// sitio. Con una imagen de 2x2 el hueco del render mide casi nada y una prueba
// que mire su altura no comprobaría nada.
const PNG_FALSO = (
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAIAAAA7ljmRAAAAHElEQVR4nGP'
  + '8//8/AwMDAwMDEwMMMDIyMjIyAgB2sQPFn8i6TwAAAABJRU5ErkJggg=='
);

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
    // El render se simula: aquí no se llama a ninguna IA de verdad. Lo que se
    // comprueba es DÓNDE cae la imagen en la pantalla, no qué imagen es.
    if (/ai-engine\/render/.test(url)) {
      return json({ success: true, result: { images: [PNG_FALSO], description: 'render de prueba' } });
    }
    if (/ai-engine\/my-credits/.test(url)) return json({ restantes: 99, ilimitado: false });
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

/**
 * Deja la pantalla en el ESTUDIO 3D, con un render ya hecho.
 *
 * El camino no es evidente y conviene dejarlo escrito:
 *  1. Se entra por Armarios, que es de donde sale el botón «ESTUDIO 3D».
 *  2. El panel de opciones va FUERA DE PANTALLA hasta que se abre: en apaisado
 *     el botón de generar está en x=-304 con una ventana de 850. Hay que
 *     pulsar «Opciones» antes de poder escribir y generar.
 *  3. Se pide un ARMARIO, no una cocina. Al entrar desde Armarios el estudio
 *     abre en modo armario, y `guardTipo()` rechaza en silencio lo que no
 *     cuadre con el tipo. Pedir una cocina aquí no da error visible: no pasa
 *     nada, que es peor.
 *  4. La tira del historial SOLO EXISTE después del primer render
 *     (`renderHistory.length > 0`), así que hay que generar uno para poder
 *     medirla.
 */
async function entrarEnEstudio3D(page, baseURL) {
  await entrar(page, baseURL);
  await page.getByText(/configurador por m[oó]dulos y despiece/i).click();
  await page.getByRole('button', { name: /^DESPIECE$/i }).waitFor({ timeout: 20000 });

  const boton = page.getByRole('button', { name: /^ESTUDIO 3D$/i }).first();
  await boton.scrollIntoViewIfNeeded().catch(() => {});
  await boton.click({ force: true });
  await page.getByRole('button', { name: /Generar desde la descripci/i })
    .first().waitFor({ timeout: 20000 });

  // El panel de opciones va FUERA DE PANTALLA en móvil y ABIERTO en escritorio.
  // Por eso se mira antes de tocar nada: pulsar «Opciones» a ciegas lo abre en
  // el móvil y lo CIERRA en el escritorio, y entonces no hay dónde escribir.
  const fuera = await page.locator('textarea').first()
    .evaluate((el) => el.getBoundingClientRect().left < 0);
  if (fuera) {
    await page.getByRole('button', { name: /^Opciones$|Abrir opciones de dise/i })
      .first().click();
    await page.locator('textarea').first()
      .evaluate((el) => el.getBoundingClientRect().left >= 0);
  }
  await page.locator('textarea').first()
    .fill('armario empotrado de 3 metros con puertas correderas blancas');
  await page.getByRole('button', { name: /Generar desde la descripci/i }).first().click();
  await page.locator('.tira-historial').waitFor({ timeout: 30000 });
}


module.exports = {
  USUARIO_MASTER, PNG_FALSO, simularBackend, entrar, entrarEnEstudio3D,
  contenedorQueSeDesliza, deslizarHastaElFinal,
};
