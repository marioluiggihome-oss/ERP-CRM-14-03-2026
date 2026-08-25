/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/*
 * Que no quede nada fuera del alcance del dedo, y que «Pantalla completa» haga
 * algo.
 *
 * EL ERP ESTABA MONTADO COMO UNA APLICACIÓN DE ESCRITORIO: la ventana se llena
 * y cada panel se desliza por dentro. En un portátil funciona. En un MÓVIL EN
 * APAISADO quedan 390 px de alto, y tres `overflow: hidden` encadenados —el
 * marco, el lienzo y el módulo— recortaban lo que no cabía SIN dejar deslizar
 * nada. Medido antes del arreglo, con el Estudio 3D abierto:
 *
 *     móvil apaisado  844x390   la página se desliza 0 px
 *     tablet apaisada 1024x600  la página se desliza 0 px
 *
 * O sea que había botones a los que no se podía llegar de ninguna manera. No
 * es que estuvieran incómodos: no existían para el dedo.
 *
 * ESTAS PRUEBAS MIDEN EN UN NAVEGADOR DE VERDAD, que es la única forma. Y
 * miden lo que importa: no «cuántas cosas hay debajo del pliegue» —en una
 * página que se desliza eso es normal— sino CUÁNTAS NO SE PUEDEN ALCANZAR ni
 * desplazándose.
 */
const { test, expect } = require('@playwright/test');
const { entrarEnEstudio3D } = require('./arnes');

/** Lo que está fuera de la ventana Y sin ningún antepasado que se desplace. */
async function inalcanzables(page) {
  return page.evaluate(() => {
    const sePuedeDesplazar = (el) => {
      for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
        const cs = getComputedStyle(n);
        const desliza = /auto|scroll/.test(cs.overflowY) || /auto|scroll/.test(cs.overflowX);
        if (desliza && (n.scrollHeight > n.clientHeight + 4 || n.scrollWidth > n.clientWidth + 4)) return true;
      }
      const doc = document.scrollingElement;
      return doc.scrollHeight > doc.clientHeight + 4;
    };
    const perdidos = [];
    for (const el of document.querySelectorAll('button, input, select, h1, h2, h3, label')) {
      const r = el.getBoundingClientRect();
      if (r.height === 0 && r.width === 0) continue;
      if (getComputedStyle(el).visibility === 'hidden') continue;
      // Un CAJÓN CERRADO no es contenido perdido: el menú lateral se aparta
      // fuera de la pantalla a propósito y se llega abriéndolo.
      if (el.closest('aside') && r.right <= 0) continue;
      const dentro = r.top < window.innerHeight && r.bottom > 0
                  && r.left < window.innerWidth && r.right > 0;
      if (!dentro && !sePuedeDesplazar(el)) {
        perdidos.push((el.innerText || el.getAttribute('title') || el.tagName).trim().slice(0, 30));
      }
    }
    return [...new Set(perdidos)];
  });
}

const TAMANOS = [
  { nombre: 'móvil apaisado', width: 844, height: 390, deslizable: true },
  { nombre: 'móvil vertical', width: 390, height: 844, deslizable: false },
  { nombre: 'tablet apaisada', width: 1024, height: 600, deslizable: true },
];

for (const t of TAMANOS) {
  test(`${t.nombre}: no hay nada fuera del alcance`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: t.width, height: t.height });
    await entrarEnEstudio3D(page, testInfo.project.use.baseURL);
    await page.waitForTimeout(400);
    const perdidos = await inalcanzables(page);
    expect(perdidos, `no se puede llegar a: ${perdidos.join(' · ')}`).toEqual([]);
  });
}

test('en apaisado la página SE DESLIZA hasta el final', async ({ page }, testInfo) => {
  // La prueba de arriba pasaría también escondiendo cosas. Esta comprueba el
  // mecanismo: que con poca altura la aplicación deje de comportarse como una
  // ventana fija y pase a ser una página que se desliza.
  await page.setViewportSize({ width: 844, height: 390 });
  await entrarEnEstudio3D(page, testInfo.project.use.baseURL);
  await page.waitForTimeout(400);
  const recorrido = await page.evaluate(() => {
    const d = document.scrollingElement;
    return d.scrollHeight - d.clientHeight;
  });
  expect(recorrido, 'la página no se desliza en apaisado: vuelven los tres overflow-hidden encadenados')
    .toBeGreaterThan(40);
});

test('en pantalla alta la aplicación NO se desliza: sigue siendo una ventana', async ({ page }, testInfo) => {
  // El arreglo va por ALTO de ventana a propósito. Si se aplicara siempre,
  // el ERP dejaría de comportarse como una aplicación en el escritorio, que es
  // como se usa a diario.
  await page.setViewportSize({ width: 1440, height: 900 });
  await entrarEnEstudio3D(page, testInfo.project.use.baseURL);
  await page.waitForTimeout(400);
  const recorrido = await page.evaluate(() => {
    const d = document.scrollingElement;
    return d.scrollHeight - d.clientHeight;
  });
  expect(recorrido, 'en una pantalla grande la página se desliza: la regla de alto se está aplicando de más')
    .toBeLessThanOrEqual(40);
});
