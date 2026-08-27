/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * NADA QUE SE PUEDA PULSAR PUEDE QUEDAR FUERA DE LA PANTALLA.
 *
 * El master, 24/08: «revisa bien para que todo funcione en responsive».
 *
 * Se barren los módulos en un navegador de verdad, a 390 px (móvil de pie) y a
 * 850x430 (móvil girado), y se busca UNA cosa concreta: botones, campos y
 * enlaces que caigan fuera del viewport Y NO TENGAN NINGÚN CONTENEDOR
 * DESLIZABLE por encima. Eso no es un problema estético: es un botón al que no
 * hay forma de llegar con el dedo.
 *
 * Lo que encontró la primera pasada:
 *   · Cocina Montada 2 — 12, entre ellos EXPORTAR PDF, PDF SIN PRECIOS y
 *     CONFIRMAR PEDIDO. Se podía preparar un pedido entero en el teléfono y no
 *     había manera de confirmarlo.
 *   · Cocina Montada 3 — 12: de la tarifa T11 en adelante, o sea la mitad de
 *     las tarifas, inseleccionables.
 *   · Archivo — 6: los filtros, el buscador y «Guardar Actual».
 *   · Armarios — 1: el interruptor de puertas, medio fuera por la izquierda.
 *
 * CASI SIEMPRE ERA LA MISMA CAUSA, y conviene saberla: un hijo de un flex trae
 * `min-width: auto`, o sea que SE NIEGA a encogerse por debajo de su contenido.
 * Una fila de 819 px dentro de un padre de 332 no se recorta: desborda. Y
 * mientras eso pasa, poner `overflow-x-auto` más abajo no sirve de nada, porque
 * no tiene contra qué medirse. La pareja que lo arregla es `min-w-0` en quien
 * bloquea y `overflow-x-auto` + `shrink-0` en la tira.
 */
const { test, expect } = require('@playwright/test');
const { entrar } = require('./arnes');

const VISTAS = [
  ['móvil', { width: 390, height: 844 }],
  ['apaisado', { width: 850, height: 430 }],
];

// Los módulos donde se encontró algo, más los vecinos de siempre. No están los
// 26: cada uno cuesta ~8 s y el CI no puede irse a diez minutos por esto.
const MODULOS = ['Cocina Montada 2', 'Cocina Montada 3', 'Archivo', 'Armarios'];

/** Lo que se puede pulsar y no se puede alcanzar. */
const INALCANZABLES = () => {
  const W = window.innerWidth;
  const deslizable = (el) => {
    for (let n = el.parentElement; n; n = n.parentElement) {
      if (n.scrollWidth > n.clientWidth + 4 && /auto|scroll/.test(getComputedStyle(n).overflowX)) return true;
      if (n === document.body) break;
    }
    return false;
  };
  const fuera = [];
  for (const el of document.querySelectorAll('button, input, select, textarea, a[href]')) {
    if (typeof el.checkVisibility === 'function' &&
        !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) continue;
    const principal = document.querySelector('main');
    if (principal && !principal.contains(el)) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if ((r.right > W + 2 || r.left < -2) && !deslizable(el)) {
      fuera.push(`«${(el.textContent || el.placeholder || el.tagName).replace(/\s+/g, ' ').trim().slice(0, 24)}»@${Math.round(r.left)}`);
    }
  }
  return fuera;
};

for (const modulo of MODULOS) {
  test(`${modulo}: nada que pulsar se queda fuera de la pantalla`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await entrar(page, baseURL);
    // Se pulsa el botón DEL MENÚ, no la tarjeta de inicio: varios módulos
    // tienen las dos cosas con el mismo rótulo y el clic salía ambiguo.
    await page.locator('aside').first()
      .getByRole('button', { name: new RegExp(`^${modulo.replace(/\./g, '\\.')}$`, 'i') })
      .first().click();
    await page.waitForTimeout(2500);

    for (const [etiqueta, vista] of VISTAS) {
      await page.setViewportSize(vista);
      await page.waitForTimeout(900);
      // El menú se queda abierto al encoger desde escritorio; en el móvil de
      // verdad se cierra solo al elegir. Se cierra aquí también, o se estaría
      // midiendo una pantalla que nadie tiene delante.
      const capa = page.getByTestId('mobile-sidebar-overlay');
      if (await capa.count()) {
        await capa.click({ force: true, timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(600);
      }

      const fuera = await page.evaluate(INALCANZABLES);
      expect(fuera, `en ${modulo} (${etiqueta} ${vista.width}x${vista.height}) hay ` +
        `${fuera.length} cosa(s) que se pueden pulsar y a las que NO SE PUEDE LLEGAR: ` +
        `${fuera.join(', ')}. Casi siempre es lo mismo: a alguien de la cadena le ` +
        `falta \`min-w-0\` y por eso se niega a encogerse, y la tira de abajo no ` +
        `puede deslizarse aunque tenga \`overflow-x-auto\`.`).toEqual([]);

      const exceso = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(exceso, `${modulo} desborda ${exceso} px a lo ancho en ${etiqueta}`).toBeLessThanOrEqual(0);
    }
  });
}
