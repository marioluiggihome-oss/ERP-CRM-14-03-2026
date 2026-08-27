/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL MENÚ LATERAL EN EL MÓVIL — que al elegir algo, se quite de en medio.
 *
 * El master, 24/08, con el ERP en el teléfono: pulsaba MASTER y el Panel
 * Maestro no aparecía por ningún lado; el menú se quedaba puesto, tapando la
 * primera columna de todo («…venido, MARIO» en vez de «Bienvenido, MARIO»).
 *
 * LA CAUSA, y es de las que dan rabia: el código que cerraba el menú buscaba
 * `button[data-nav]`… y `data-nav` NO LO LLEVABA NI UN SOLO BOTÓN. El atributo
 * existía únicamente dentro del selector. O sea que el cierre automático
 * llevaba escrito desde siempre sin haber funcionado nunca, y nada lo delataba:
 * no da error, sencillamente no pasa.
 *
 * En el móvil la barra es `fixed`, 80 px de ancho, `z-50`, y va POR ENCIMA del
 * contenido con un fondo oscuro detrás. Quedarse abierta no es un detalle
 * estético: son 80 px menos de una pantalla de 390 y el módulo que acabas de
 * abrir, medio escondido.
 */
const { test, expect } = require('@playwright/test');
const { entrar } = require('./arnes');

const MOVIL = { width: 390, height: 844 };
const ANCHO_BARRA = 80;   // w-20 de Tailwind

test.use({ viewport: MOVIL });

async function abrirMenu(page) {
  await page.getByTestId('sidebar-toggle').click();
  await page.getByTestId('mobile-sidebar-overlay').waitFor({ timeout: 5000 });
}

test('el menú se abre y tapa el contenido, que es lo que debe hacer', async ({ page, baseURL }) => {
  // Esto NO es el fallo: un menú lateral en un móvil se pone encima a propósito.
  // Se comprueba para que la prueba de abajo signifique algo — si el menú no
  // llegara a taparlo, cerrarlo no tendría mérito.
  await entrar(page, baseURL);
  await abrirMenu(page);
  const barra = await page.locator('aside').first().boundingBox();
  expect(barra.x, 'el menú no está pegado a la izquierda').toBeLessThanOrEqual(1);
  expect(barra.width, `el menú mide ${Math.round(barra.width)} px`).toBeGreaterThan(ANCHO_BARRA - 10);
});

test('AL ELEGIR UN MÓDULO, EL MENÚ SE QUITA DE EN MEDIO', async ({ page, baseURL }) => {
  await entrar(page, baseURL);
  await abrirMenu(page);
  await page.locator('aside').first().getByText(/^CRM$/i).first().click();
  await expect(page.getByTestId('mobile-sidebar-overlay'),
    'el menú sigue abierto después de elegir un módulo: tapa 80 px de una ' +
    'pantalla de 390 y deja el módulo medio escondido detrás')
    .toHaveCount(0, { timeout: 5000 });
});

test('AL PULSAR MASTER, EL PANEL SE VE Y EL MENÚ SE QUITA', async ({ page, baseURL }) => {
  // El caso exacto que reportó el master.
  await entrar(page, baseURL);
  await abrirMenu(page);
  await page.locator('aside').first().getByText(/^Master$/i).first().click();

  await expect(page.getByTestId('mobile-sidebar-overlay'),
    'el menú se queda encima del Panel Maestro').toHaveCount(0, { timeout: 5000 });
  await expect(page.getByText(/PANEL MAESTRO/i).first(),
    'el Panel Maestro no aparece al pulsar MASTER en el móvil').toBeVisible({ timeout: 10000 });

  // Y que se vea ENTERO: nada del panel puede quedar debajo de donde estaba
  // la barra.
  const panel = await page.getByText(/PANEL MAESTRO/i).first().boundingBox();
  expect(panel.x, `el rótulo del panel empieza en x=${Math.round(panel.x)}, dentro de ` +
    `los ${ANCHO_BARRA} px que ocupaba el menú`).toBeGreaterThanOrEqual(0);
});
