/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * LOS CRÉDITOS SIEMPRE DICEN ALGO. AUNQUE NO SE PUEDAN LEER.
 *
 * El master, 25/08/2026: «no sale lo de créditos en mi pantalla».
 *
 * Y no salía nada de nada. `fetchCredits` estaba escrito así:
 *
 *     if (r.ok) setAiCredits(await r.json());
 *     } catch { /* silencioso: el contador nunca rompe la UI *\/ }
 *
 * O sea que si la llamada fallaba —un 500, un 401, el servidor sin arrancar—
 * `aiCredits` se quedaba en nulo y la pastilla de créditos DESAPARECÍA de la
 * cabecera. Sin error, sin hueco, sin nada. Y el aviso de coste que se acababa
 * de añadir colgaba de la misma variable, así que desaparecía también.
 *
 * El comentario decía «nunca rompe la UI», que suena prudente y no lo es: el
 * usuario no ve un fallo, ve que la cosa NO ESTÁ, y no tiene forma de saber si
 * es que no tiene créditos, si la pantalla está a medias o si el servidor no
 * contesta.
 *
 * Dos reglas ahora:
 *
 *   1. Si el saldo no se puede leer, se DICE («Créditos: sin lectura»).
 *   2. El COSTE del render se enseña igualmente, porque no depende del
 *      contador: sale del motor elegido. Lo único que hace falta el contador es
 *      para el «te quedan N».
 *
 * Esto va en un navegador de verdad y no leyendo el JSX porque lo que se
 * comprueba es qué VE una persona cuando el servidor falla, y eso solo lo sabe
 * un navegador.
 */
const { test, expect } = require('@playwright/test');
const { entrar } = require('./arnes');

/** Entra en el Estudio 3D. `romperCreditos` corta la llamada del contador. */
async function abrirEstudio(page, baseURL, romperCreditos = false) {
  await entrar(page, baseURL);
  if (romperCreditos) {
    // DESPUÉS del arnés a propósito: Playwright da prioridad a la última ruta
    // registrada, y el arnés captura `**/*`. Puesta antes, no ganaría.
    await page.route('**/ai-engine/my-credits*', (r) => r.fulfill({
      status: 500, contentType: 'application/json', body: '{}',
    }));
  }
  await page.getByText(/configurador por m[oó]dulos y despiece/i).click();
  await page.getByRole('button', { name: /^ESTUDIO 3D$/i }).first().click({ force: true });
  await page.getByRole('button', { name: /Generar desde la descripci/i })
    .first().waitFor({ timeout: 20000 });
  await page.waitForTimeout(1200);
}

const loQueSeVe = () => ({
  pastilla: (() => {
    const e = [...document.querySelectorAll('span,button')]
      .find((n) => /Cr[ée]ditos/.test(n.textContent || '') && n.getBoundingClientRect().width);
    return e ? e.textContent.trim() : null;
  })(),
  aviso: (() => {
    const e = [...document.querySelectorAll('p')]
      .find((n) => /Vas a gastar|Te faltan cr/.test(n.textContent || ''));
    return e ? e.textContent.trim() : null;
  })(),
});

test('con el contador OK se ve el saldo y lo que va a costar', async ({ page, baseURL }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 1280, height: 800 });
  await abrirEstudio(page, baseURL);
  const v = await page.evaluate(loQueSeVe);
  expect(v.pastilla, 'no se ve la pastilla de créditos').toContain('Créditos');
  expect(v.aviso, 'no se ve lo que va a costar el render').toContain('Vas a gastar');
});

test('CON EL CONTADOR CAIDO se sigue diciendo lo que cuesta, y que no hay saldo',
  async ({ page, baseURL }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 1280, height: 800 });
    await abrirEstudio(page, baseURL, true);
    const v = await page.evaluate(loQueSeVe);

    expect(v.pastilla,
      'con el contador caído no se dice NADA de los créditos: la pastilla '
      + 'desaparece de la cabecera y el usuario no sabe si es que no tiene, si '
      + 'la pantalla está rota o si el servidor no contesta').toBeTruthy();
    expect(v.pastilla).toMatch(/sin lectura/i);

    expect(v.aviso,
      'ha desaparecido el aviso de coste porque no se pudo leer el saldo. El '
      + 'coste NO depende del contador: sale del motor elegido, y se sabe '
      + 'siempre').toBeTruthy();
    expect(v.aviso).toContain('Vas a gastar');
  });

test('el aviso de coste NUNCA dice qué IA se usa, ni cuando el contador falla',
  async ({ page, baseURL }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 1280, height: 800 });
    await abrirEstudio(page, baseURL, true);
    const v = await page.evaluate(loQueSeVe);
    const texto = `${v.pastilla || ''} ${v.aviso || ''}`.toLowerCase();
    for (const palabra of ['gemini', 'banana', 'flux', 'manus', 'ia 1', 'ia 3', 'ia 7', 'motor']) {
      expect(texto,
        `el aviso nombra «${palabra}». El master: «que no ponga nunca qué IA se `
        + 'usa» — y el camino de error es justo por donde se cuela lo que nadie '
        + 'revisa').not.toContain(palabra);
    }
  });
