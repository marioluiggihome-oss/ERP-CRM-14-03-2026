/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * LA TABLA DE NOMENCLATURAS SE MANEJA CON EL DEDO.
 *
 * El master, 25/08/2026: «muy intuitiva y muy facilona de manejar, para que se
 * vea perfectamente en tablet de 8,6" y en móviles».
 *
 * Lo que había era una TABLA de hasta 13 columnas (10 con el candado cerrado).
 * Medido antes de tocar nada, en una tablet de 800 px: 851 px de tabla en un
 * hueco de 693 — se desbordaba 158 px. Se podía arrastrar de lado, sí, pero
 * leer códigos MV arrastrando no es manejable, y en un móvil de 390 no hay
 * arrastre que valga.
 *
 * Ahora, hasta `lg`, cada mueble es una FICHA: el código grande —que es lo que
 * de verdad se lee—, las medidas como etiquetas, la cantidad con botones de
 * 40 px y las observaciones a lo ancho. De `lg` para arriba vuelve la tabla,
 * que ahí sí cabe y deja comparar en vertical.
 */
const { test, expect } = require('@playwright/test');
const { entrar } = require('./arnes');

const MUEBLES = [
  { qty: 1, cod: 'B60D/I', familia: 'BAJO', tipo: 'BAJO', ancho: 60, alto: 80, fondo: 58, mano: 'D', pts: 49, pvp: 163.17, raw: '1 b60d', encontrado: true },
  { qty: 2, cod: 'A60D/I', familia: 'ALTO', tipo: 'ALTO', ancho: 60, alto: 90, fondo: 33, mano: 'I', pts: 51, pvp: 169.83, raw: '2 a60i', encontrado: true },
  { qty: 1, cod: 'BF60', familia: 'BAJO_FREGADERO', tipo: 'BAJO', ancho: 60, alto: 80, fondo: 58, mano: null, pts: 44, pvp: 146.52, raw: '1 bf60', encontrado: true },
];

async function abrirConMuebles(page, baseURL, vista) {
  // Se ENTRA EN ANCHO y luego se encoge: en un móvil el menú está fuera de
  // pantalla hasta que se abre, y lo que se quiere medir es la tabla, no el
  // menú. Es el mismo camino que usa `nada-fuera-de-pantalla.spec.js`.
  await page.setViewportSize({ width: 1440, height: 900 });
  await entrar(page, baseURL);
  // Después del arnés, para que esta ruta gane.
  await page.route('**/cascos/mv/detectar-relacion*', (r) => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ success: true, muebles: MUEBLES, count: MUEBLES.length, total: 649 }),
  }));
  await page.locator('aside').first()
    .getByRole('button', { name: /Cocina Montada 3/i }).first().click();
  await page.waitForTimeout(2000);
  await page.locator('input[placeholder*="código o descripción"]').first().fill('1 b60d');
  await page.getByRole('button', { name: /Añadir Mueble/i }).first().click();
  await page.waitForTimeout(1500);
  await page.setViewportSize(vista);
  await page.waitForTimeout(900);
  const capa = page.getByTestId('mobile-sidebar-overlay');
  if (await capa.count()) {
    await capa.click({ force: true, timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
}

const MEDIDA = () => {
  const fichas = document.querySelectorAll('.lg\\:hidden > .rounded-2xl');
  const tabla = document.querySelector('table');
  const visible = (el) => !!el && el.getBoundingClientRect().width > 0;
  return {
    fichasVisibles: [...fichas].filter(visible).length,
    tablaVisible: visible(tabla),
    desbordaLaPagina: document.documentElement.scrollWidth - window.innerWidth,
    // Ningún control puede quedar INALCANZABLE. Estar fuera del ancho no basta:
    // la tira de las 21 tarifas vive dentro de un contenedor que se desliza a
    // propósito, y ésos sí se alcanzan. Se cuenta solo lo que cae fuera Y no
    // tiene por encima nada que se pueda deslizar — la misma regla que usa
    // `nada-fuera-de-pantalla.spec.js`.
    controlesFuera: [...document.querySelectorAll('main button, main input, main select')]
      .filter((el) => {
        const r = el.getBoundingClientRect();
        if (!r.width || (r.right <= window.innerWidth + 2 && r.left >= -2)) return false;
        for (let n = el.parentElement; n; n = n.parentElement) {
          if (n.scrollWidth > n.clientWidth + 4
              && /auto|scroll/.test(getComputedStyle(n).overflowX)) return false;
          if (n === document.body) break;
        }
        return true;
      }).length,
  };
};

test('en móvil de 390 los muebles se ven como fichas, sin desbordar', async ({ page, baseURL }) => {
  test.setTimeout(150000);
  await abrirConMuebles(page, baseURL, { width: 390, height: 844 });
  const r = await page.evaluate(MEDIDA);
  expect(r.fichasVisibles, 'no se pintan las fichas en el móvil').toBeGreaterThan(0);
  expect(r.tablaVisible, 'la tabla de 10 columnas vuelve a salir en el móvil').toBe(false);
  expect(r.desbordaLaPagina, `la página se va ${r.desbordaLaPagina} px de lado`).toBeLessThanOrEqual(0);
  expect(r.controlesFuera, 'hay controles fuera de la pantalla').toBe(0);
});

test('en tablet de 8,6" pasa lo mismo', async ({ page, baseURL }) => {
  test.setTimeout(150000);
  await abrirConMuebles(page, baseURL, { width: 800, height: 1280 });
  const r = await page.evaluate(MEDIDA);
  expect(r.fichasVisibles, 'no se pintan las fichas en la tablet').toBeGreaterThan(0);
  expect(r.tablaVisible, 'la tabla se desbordaba 158 px aquí; no puede volver').toBe(false);
  expect(r.desbordaLaPagina).toBeLessThanOrEqual(0);
  expect(r.controlesFuera, 'hay controles fuera de la pantalla').toBe(0);
});

test('en escritorio vuelve la tabla, que ahí sí cabe', async ({ page, baseURL }) => {
  test.setTimeout(150000);
  await abrirConMuebles(page, baseURL, { width: 1440, height: 900 });
  const r = await page.evaluate(MEDIDA);
  expect(r.tablaVisible, 'se ha perdido la tabla en escritorio').toBe(true);
  expect(r.fichasVisibles, 'las fichas no deben salir además de la tabla').toBe(0);
});
