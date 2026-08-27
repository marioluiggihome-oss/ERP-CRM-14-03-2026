/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * REPRODUCIR EL BLANCO: EL TECLADO DE LA TABLET LO DISPARA.
 *
 * `securityGuard.js` cree detectar las DevTools comparando el tamaño exterior
 * de la ventana con el interior: si se diferencian en más de 160 px, borra la
 * página entera con `document.body.innerHTML`.
 *
 * En un escritorio eso solo pasa al abrir las herramientas. En una tablet pasa
 * al TOCAR UN CAMPO DE TEXTO: sale el teclado en pantalla, `innerHeight` se
 * desploma 300-400 px y el guardia borra la aplicación. La comprobación corre
 * cada 1.000 ms, que es el «tarda como un segundo» del aviso.
 *
 * Aquí se simula el teclado tocando `outerHeight`, que es justo lo que hace el
 * navegador de la tablet, y se mira si la página desaparece.
 */
const { test, expect } = require('@playwright/test');
const { entrar } = require('./arnes');

test('el teclado de la tablet deja la pantalla en blanco', async ({ page, baseURL }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 800, height: 1340 });   // tablet 8,6"
  await entrar(page, baseURL);
  await page.getByText(/^Cocina Montada 3$/i).first().click({ force: true });
  await page.waitForTimeout(1500);

  const vivo = () => page.evaluate(() =>
    !/ACCESO RESTRINGIDO/i.test(document.body.innerText || ''));

  expect(await vivo(), 'la pantalla ya estaba borrada antes de tocar nada').toBe(true);

  // Sale el teclado: la ventana visible encoge ~380 px. El navegador de la
  // tablet mantiene `outerHeight`, así que la diferencia se dispara.
  await page.evaluate(() => {
    Object.defineProperty(window, 'outerHeight',
      { get: () => window.innerHeight + 380, configurable: true });
  });

  await page.waitForTimeout(1400);          // el guardia mira cada 1.000 ms
  const sigueViva = await vivo();
  await page.screenshot({ path: 'blanco-teclado.png' });

  expect(sigueViva,
    'CAZADO: con el teclado abierto el guardia antimanipulación borra la '
    + 'aplicación entera y deja «ACCESO RESTRINGIDO». Es el blanco que ve el '
    + 'master al escribir en el buscador desde la tablet.').toBe(true);
});
