/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL PANEL DEL ESTUDIO 3D SE DESLIZA. NO SE CORTA.
 *
 * El master, 25/08/2026, en una tablet de 8,6": «no se ve la pantalla completa
 * y no me deja hacer scroll hacia abajo».
 *
 * El panel del render llevaba `overflow-hidden`. Mientras aquí dentro solo
 * hubiera una foto daba igual —el render se ajusta solo—, pero ahora viven aquí
 * el panel de distribución (con sus tres paredes, sus módulos, sus avisos y los
 * desplegables de alturas) y la relación MV entera. Eso pasa de largo del alto
 * de cualquier tablet, y con `overflow-hidden` lo que sobraba SE CORTABA: ni
 * barra, ni scroll, ni indicio de que hubiera nada debajo. El botón de sacar
 * los muebles quedaba fuera del alcance.
 *
 * OJO AL MEDIRLO. El panel es un `flex flex-col`, así que un hijo de relleno
 * SIN `flex-shrink: 0` se encoge en vez de desbordar y la prueba daría un falso
 * verde: pareció que no se deslizaba cuando lo que pasaba es que la sonda
 * estaba mal. El contenido de verdad —texto, filas de módulos— no se encoge por
 * debajo de su tamaño mínimo, y por eso el relleno tiene que imitarlo.
 */
const { test, expect } = require('@playwright/test');
const { entrarEnEstudio3D } = require('./arnes');

const TAMANOS = [
  ['tablet 8,6" vertical', { width: 800, height: 1280 }],
  ['tablet 8,6" apaisada', { width: 1280, height: 800 }],
  ['móvil vertical', { width: 390, height: 844 }],
];

for (const [etiqueta, vista] of TAMANOS) {
  test(`${etiqueta}: el panel del Estudio 3D se desliza si el contenido no cabe`,
    async ({ page, baseURL }) => {
      test.setTimeout(120000);
      await page.setViewportSize(vista);
      await entrarEnEstudio3D(page, baseURL);

      const r = await page.evaluate(() => {
        const p = [...document.querySelectorAll('div')]
          .find((n) => /bg-slate-50/.test(n.className || '') && /min-w-0/.test(n.className || ''));
        if (!p) return { falta: true };
        const cs = getComputedStyle(p);
        const relleno = document.createElement('div');
        relleno.style.height = '3000px';
        relleno.style.flexShrink = '0';   // como el contenido real: no se encoge
        p.appendChild(relleno);
        const puede = p.scrollHeight > p.clientHeight + 4;
        p.scrollTop = 99999;
        const deslizado = p.scrollTop;
        relleno.remove();
        return { overflowY: cs.overflowY, overflowX: cs.overflowX, puede, deslizado };
      });

      expect(r.falta, 'no se encuentra el panel del render').toBeFalsy();
      expect(r.overflowY,
        'el panel del Estudio 3D ha vuelto a `overflow-hidden`: la distribución y '
        + 'la relación MV se cortan por abajo y no hay forma de llegar a los '
        + 'botones del final').toBe('auto');
      expect(r.puede, 'el panel no crece con el contenido').toBe(true);
      expect(r.deslizado,
        'el panel dice que se puede deslizar pero no se mueve').toBeGreaterThan(100);
      // A lo ANCHO sí se recorta: es lo que evita que una tabla ancha empuje la
      // página entera de lado.
      expect(r.overflowX, 'el ancho debe seguir contenido').toBe('hidden');
    });
}
