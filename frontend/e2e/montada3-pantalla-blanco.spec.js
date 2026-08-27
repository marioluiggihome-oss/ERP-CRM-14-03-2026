/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * LA PANTALLA EN BLANCO AL AÑADIR UN MUEBLE EN COCINA MONTADA 3.
 *
 * El master, dos veces: «cuando meto un mueble tarda un poco, como un segundo,
 * y se queda la pantalla en blanco; da mala imagen al meterlo en la barra de
 * búsqueda».
 *
 * No es una prueba: es una trampa para cazarlo. Escribe en el buscador como una
 * persona, pulsa Añadir, y va mirando QUÉ hay pintado cada 100 ms mientras
 * recoge todo lo que diga la consola. Si algo revienta, aquí sale.
 */
const { test, expect } = require('@playwright/test');
const { entrar } = require('./arnes');

test('cazar el blanco al añadir un mueble', async ({ page, baseURL }) => {
  test.setTimeout(180000);

  const consola = [];
  page.on('console', (m) => consola.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => consola.push(`[PAGEERROR] ${e.message}`));
  page.on('requestfailed', (r) =>
    consola.push(`[RED-FALLA] ${r.url().slice(0, 90)} :: ${r.failure()?.errorText}`));

  await page.setViewportSize({ width: 1280, height: 900 });
  await entrar(page, baseURL);
  await page.getByText(/^Cocina Montada 3$/i).first().click({ force: true });
  await page.waitForTimeout(1500);

  const buscador = page.getByPlaceholder(/Escribe un c[oó]digo o descripci/i);
  await buscador.waitFor({ timeout: 20000 });

  // Como lo escribe una persona, no de un pegote.
  await buscador.click();
  await buscador.pressSequentially('1 b60i', { delay: 90 });
  await page.waitForTimeout(400);

  const medir = async (etiqueta) => {
    const v = await page.evaluate(() => {
      const r = document.querySelector('#root');
      const txt = (document.body.innerText || '').trim();
      return {
        nodosRoot: r ? r.querySelectorAll('*').length : -1,
        largoTexto: txt.length,
        veMenu: /COCINA MONTADA 3/i.test(txt),
        veBuscador: !!document.querySelector('input[placeholder*="código"],input[placeholder*="codigo"]'),
      };
    });
    return `${etiqueta.padEnd(22)} nodos=${String(v.nodosRoot).padStart(5)} `
      + `texto=${String(v.largoTexto).padStart(6)} menu=${v.veMenu ? 'si' : 'NO'} `
      + `buscador=${v.veBuscador ? 'si' : 'NO'}`;
  };

  const linea = [];
  linea.push(await medir('antes de pulsar'));

  await page.getByRole('button', { name: /A[ñn]adir Mueble/i }).first().click();

  // Los dos segundos siguientes, cada 100 ms.
  for (let i = 1; i <= 20; i++) {
    await page.waitForTimeout(100);
    linea.push(await medir(`+${i * 100} ms`));
  }

  console.log('\n===== QUÉ SE VE, MILISEGUNDO A MILISEGUNDO =====');
  linea.forEach((l) => console.log('   ' + l));
  console.log('\n===== CONSOLA DEL NAVEGADOR =====');
  if (!consola.length) console.log('   (nada)');
  consola.slice(0, 40).forEach((l) => console.log('   ' + l.slice(0, 200)));

  await page.screenshot({ path: 'blanco-final.png' });
  expect(true).toBe(true);
});
