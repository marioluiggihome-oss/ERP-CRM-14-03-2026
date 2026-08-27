/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CAPTURAS DEL DISEÑO, PARA MIRARLO CON LOS OJOS.
 *
 * El cambio de paleta y de pesos de letra NO lo ve ningún candado: los que hay
 * vigilan lo que se calcula y lo que la pantalla DICE, no cómo se ve. Un cambio
 * estético puede colarse entero con el CI en verde.
 *
 * Así que esto no afirma nada: saca fotos de las pantallas para poder
 * compararlas antes y después a mano. Es una herramienta, no una prueba.
 */
const { test } = require('@playwright/test');
const { entrar } = require('./arnes');

const DEST = process.env.CAPTURAS || 'capturas';

/** Pulsa una entrada del menú lateral por su rótulo. */
const menu = (rotulo) => async (page) => {
  await page.getByText(new RegExp(`^${rotulo}$`, 'i')).first()
    .click({ force: true });
  await page.waitForTimeout(1200);
};

const PANTALLAS = [
  { nombre: 'inicio', abrir: async () => {} },
  {
    nombre: 'armarios',
    abrir: async (page) => {
      await page.getByText(/configurador por m[oó]dulos y despiece/i).click();
      await page.waitForTimeout(900);
    },
  },
  { nombre: 'cocina-montada-3', abrir: menu('Cocina Montada 3') },
  { nombre: 'cocina-desmontada', abrir: menu('Cocina Desmontada') },
  {
    nombre: 'estudio-3d',
    abrir: async (page) => {
      await page.getByText(/configurador por m[oó]dulos y despiece/i).click();
      await page.waitForTimeout(800);
      await page.getByRole('button', { name: /^ESTUDIO 3D$/i })
        .first().click({ force: true });
      await page.waitForTimeout(2500);
    },
  },
];

for (const p of PANTALLAS) {
  test(`captura ${p.nombre}`, async ({ page, baseURL }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 1280, height: 900 });
    await entrar(page, baseURL);
    await p.abrir(page);
    await page.waitForTimeout(700);
    await page.screenshot({ path: `${DEST}/${p.nombre}.png`, fullPage: false });
  });
}
