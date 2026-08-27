/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL ESTUDIO 3D CON EL MÓVIL GIRADO — medido en un navegador.
 *
 * El master, con el Estudio 3D en apaisado: «en móvil y posición horizontal se
 * ve todo mejor, LOS DISEÑOS NO SE VEN».
 *
 * Y era exacto. Girado, el móvil pasa a ser una pantalla ANCHA —o sea que se le
 * aplican las reglas de escritorio— pero con MUY POCO ALTO: unos 430 px. La
 * cabecera, la barra de acciones, el cuadro de edición y la tira del historial
 * sumaban más que eso, y el render —lo único que hay que mirar— se quedaba con
 * cero de alto y desaparecía.
 *
 * El arreglo es una regla de CSS que va por ALTO de ventana, no por ancho
 * (`@media (max-height: 560px)` en `index.css`): en apaisado la tira del
 * historial se encoge y suelta el sitio que le hace falta al diseño.
 *
 * POR QUÉ ESTO NO SE PODÍA COMPROBAR ANTES
 * ----------------------------------------
 * Porque es puro layout, y porque la tira del historial NO EXISTE hasta que hay
 * un render: `renderHistory.length > 0`. Hace falta un navegador de verdad Y
 * conducir una generación entera. Aquí se hacen las dos cosas —con el render
 * simulado, sin llamar a ninguna IA— y luego se le preguntan las medidas al
 * navegador.
 *
 * Medido: en 850x430 la tira mide 61 px y el título se oculta; en 1280x900 la
 * misma tira mide 82 px con su título. La regla hace lo que dice.
 */
const { test, expect } = require('@playwright/test');
const { entrarEnEstudio3D } = require('./arnes');

const APAISADO = { width: 850, height: 430 };   // móvil girado
const TOPE_TIRA = 68;                            // 4.25rem, lo que fija el CSS

test.describe('móvil en apaisado', () => {
  test.use({ viewport: APAISADO });

  test('la tira del historial se encoge y suelta el sitio', async ({ page, baseURL }) => {
    await entrarEnEstudio3D(page, baseURL);
    const alto = await page.locator('.tira-historial')
      .evaluate((el) => el.getBoundingClientRect().height);
    expect(alto, `la tira del historial mide ${Math.round(alto)} px con una ventana de ` +
      `${APAISADO.height} px de alto. Se ha perdido la regla @media (max-height: 560px) ` +
      'y vuelve a comerse el sitio del render').toBeLessThanOrEqual(TOPE_TIRA);
  });

  test('el título del historial no gasta alto en apaisado', async ({ page, baseURL }) => {
    await entrarEnEstudio3D(page, baseURL);
    const visible = await page.locator('.tira-historial .titulo-historial')
      .evaluate((el) => getComputedStyle(el).display !== 'none');
    expect(visible, 'el rótulo del historial vuelve a mostrarse en apaisado: son ' +
      'líneas de alto gastadas en decir lo que ya se ve').toBe(false);
  });

  test('EL RENDER NO SE QUEDA EN CERO DE ALTO', async ({ page, baseURL }) => {
    // Ésta es la avería que reportó el master, en una sola frase: los diseños
    // no se ven. No daba error ninguno — el render se generaba, se pagaba y
    // caía en un hueco de altura cero.
    //
    // SE MIDE EL HUECO, NO LA IMAGEN. La imagen que se ve aquí es un PNG falso
    // del arnés, así que su tamaño lo decide la prueba y no el layout: medirla
    // sería comprobar mi propio fixture. Lo que decide si el diseño se ve es el
    // hijo `flex-1` del panel de render, que es quien se queda lo que sobra
    // después de la barra de arriba y de la tira del historial.
    //
    // Medido con todo en su sitio: panel 312 px = barra 31 + hueco 177 + tira 61.
    await entrarEnEstudio3D(page, baseURL);
    const g = await page.locator('.tira-historial').evaluate((tira) => {
      const panel = tira.parentElement;
      const hueco = [...panel.children]
        .filter((e) => e !== tira)
        .map((e) => e.getBoundingClientRect().height)
        .sort((a, b) => b - a)[0];
      return { panel: panel.getBoundingClientRect().height, hueco };
    });

    expect(g.hueco, 'el hueco del render tiene CERO de alto: se ha generado y no se ' +
      've, que es exactamente lo que reportó el master').toBeGreaterThan(0);
    expect(g.hueco / g.panel, `al render le queda el ${Math.round(g.hueco / g.panel * 100)} % ` +
      'del panel. Algo de alrededor —la cabecera, la tira del historial, el cuadro de ' +
      'edición— ha vuelto a comerse el sitio del diseño')
      .toBeGreaterThan(0.4);
  });
});

test.describe('pantalla alta', () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test('con alto de sobra la tira NO se recorta', async ({ page, baseURL }) => {
    // El contraste importa: sin esto, una tira que midiera siempre 20 px
    // pasaría la prueba de arriba sin que la regla del CSS existiera. Aquí se
    // comprueba que el recorte lo hace la ventana baja y no otra cosa.
    await entrarEnEstudio3D(page, baseURL);
    const alto = await page.locator('.tira-historial')
      .evaluate((el) => el.getBoundingClientRect().height);
    expect(alto, `la tira mide ${Math.round(alto)} px en una pantalla alta: está ` +
      'recortada siempre, así que la prueba de apaisado no demuestra nada')
      .toBeGreaterThan(TOPE_TIRA);
  });
});
