/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * QUÉ SE VE MIENTRAS SE AÑADE UN MUEBLE.
 *
 * `añadirTexto` va al servidor (`/api/cascos/mv/detectar-relacion`) y eso tarda.
 * El master: «cuando meto un mueble tarda un poco, como un segundo, y se queda
 * la pantalla en blanco; da mala imagen».
 *
 * Aquí se pone el servidor lento a propósito (1,2 s) y se fotografía la
 * pantalla A MITAD de la espera, que es el momento del que se queja y el que
 * nunca se ve en una prueba normal.
 */
const { test } = require('@playwright/test');
const { entrar } = require('./arnes');

test('foto de la espera al añadir un mueble', async ({ page, baseURL }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 800, height: 1340 });   // tablet 8,6"
  await entrar(page, baseURL);

  // Después del arnés: Playwright da prioridad a la última ruta registrada.
  await page.route('**/cascos/mv/detectar-relacion', async (r) => {
    await new Promise((ok) => setTimeout(ok, 1200));
    await r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ success: true, muebles: [{
        qty: 1, cod: 'B60I', familia: 'BAJO', tipo: 'BAJO', ancho: 60,
        alto: 80, fondo: 58, mano: 'I', pts: 46, pvp: 153.18, encontrado: true,
      }] }),
    });
  });

  await page.getByText(/^Cocina Montada 3$/i).first().click({ force: true });
  await page.waitForTimeout(1500);

  const buscador = page.getByPlaceholder(/Escribe un c[oó]digo o descripci/i);
  await buscador.click();
  await buscador.pressSequentially('1 b60i', { delay: 80 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: 'espera-0-escrito.png' });

  await page.getByRole('button', { name: /A[ñn]adir Mueble/i }).first().click();
  await page.waitForTimeout(600);                 // mitad de la espera
  await page.screenshot({ path: 'espera-1-esperando.png' });

  await page.waitForTimeout(1400);                // ya ha contestado
  await page.screenshot({ path: 'espera-2-hecho.png' });
});
