/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * ARMARIOS EN EL MÓVIL — comprobado en un navegador, con medidas reales.
 *
 * El master trabaja este módulo sobre todo con el teléfono, y en el teléfono no
 * fallaba nada: sencillamente no se podía usar. Un módulo que no da error pero
 * no deja trabajar es peor que uno que revienta, porque nadie abre una
 * incidencia — se deja de usar y se vuelve al papel.
 *
 * `backend/tests/test_pantalla_armarios_movil.py` protege lo mismo LEYENDO EL
 * JSX: comprueba que ponga `max-lg:flex-col`, `shrink-0`, `overflow-x-auto`.
 * Eso caza un borrado, y por eso sigue ahí. Pero no puede responder a la
 * pregunta de verdad —«¿cabe?»— porque un nombre de clase no mide nada. Aquí
 * se mide: viewport de 390 px, y se preguntan los rectángulos al navegador.
 */
const { test, expect } = require('@playwright/test');
const { entrar, contenedorQueSeDesliza, deslizarHastaElFinal } = require('./arnes');

const MOVIL = { width: 390, height: 844 };          // iPhone de pie
const BOTONES = ['IA', 'RENDER', 'ESTUDIO 3D', 'PLANOS', 'PROYECTOS',
                 'DESPIECE', 'GUARDAR', 'PDF', 'ENVIAR AL PRESUPUESTO'];

test.use({ viewport: MOVIL });

test.beforeEach(async ({ page, baseURL }) => {
  await entrar(page, baseURL);
  await page.getByText(/configurador por m[oó]dulos y despiece/i).click();
  await page.getByRole('button', { name: /^DESPIECE$/i }).waitFor({ timeout: 20000 });
});

test('la página no se sale de ancho', async ({ page }) => {
  // Si la página desborda, el móvil deja desplazar en horizontal TODA la
  // pantalla y trabajar se vuelve un baile: se pierde la columna de la
  // izquierda cada vez que se toca algo.
  const exceso = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth);
  expect(exceso, 'la pantalla de Armarios desborda a lo ancho en un móvil').toBeLessThanOrEqual(0);
});

test('los nueve botones de la cabecera existen y ninguno está aplastado', async ({ page }) => {
  // El fallo que se protege: en una fila que ni se envuelve ni se desliza, los
  // nueve botones se reparten los 390 px y quedan a ~40 px cada uno, ilegibles.
  // Con `shrink-0` cada uno conserva su tamaño y la tira se desliza.
  for (const nombre of BOTONES) {
    const boton = page.getByRole('button', { name: new RegExp(`^${nombre}$`, 'i') }).first();
    await expect(boton, `falta el botón ${nombre}`).toHaveCount(1);
    const caja = await boton.boundingBox();
    expect(caja, `el botón ${nombre} no ocupa sitio`).not.toBeNull();
    expect(caja.width, `el botón ${nombre} se ha aplastado a ${Math.round(caja.width)} px: ` +
      'alguien le ha quitado el shrink-0 y ya no se lee').toBeGreaterThan(60);
    expect(caja.height, `el botón ${nombre} no tiene alto`).toBeGreaterThan(20);
  }
});

test('la cabecera se desliza, que es como se llega al último botón', async ({ page }) => {
  const ultimo = page.getByRole('button', { name: /^ENVIAR AL PRESUPUESTO$/i }).first();

  const tira = await contenedorQueSeDesliza(ultimo);
  expect(tira.desliza, 'la botonera de la cabecera no se desliza: con nueve botones ' +
    'que no caben, los últimos quedan fuera y no hay forma de guardar ni de ' +
    'mandar al presupuesto').toBe(true);
  expect(tira.scrollWidth).toBeGreaterThan(tira.clientWidth);

  // Y deslizarla tiene que SERVIR: el último botón acaba dentro de la pantalla.
  const antes = await ultimo.boundingBox();
  expect(antes.x, 'el último botón ya estaría dentro; esta prueba no comprobaría nada')
    .toBeGreaterThan(MOVIL.width);

  await deslizarHastaElFinal(ultimo);
  await page.waitForTimeout(300);

  const despues = await ultimo.boundingBox();
  expect(despues.x, 'la tira se ha deslizado y el último botón sigue fuera de la pantalla')
    .toBeLessThan(MOVIL.width);
  expect(despues.x + despues.width, 'el último botón queda cortado por el borde')
    .toBeLessThanOrEqual(MOVIL.width + 1);
});

test('las tres columnas se apilan en vez de aplastarse', async ({ page }) => {
  // En escritorio son tres columnas: configuración (320 px), el armario en el
  // centro y el presupuesto (320 px). En 390 px las dos laterales se comían
  // casi todo y el armario quedaba en una tira. Apiladas, cada una ocupa el
  // ancho entero y van una debajo de otra.
  //
  // CÓMO SE MIDE, sin mirar ni una clase de CSS: los tres campos de dimensiones
  // —ANCHO, ALTO, FONDO— viven en el panel de configuración y van en fila. Lo
  // que ocupan de punta a punta ES el ancho útil de ese panel.
  //
  //   · apilado (bien):  abarcan ~358 px de 390  →  92 %
  //   · clavado a 320:   abarcarían ~287 px      →  74 %
  //
  // Entre 92 y 74 hay sitio de sobra para un umbral que no parpadee.
  const medidas = await page.evaluate(() => [...document.querySelectorAll('input')]
    .filter((e) => /^(2400|600)$/.test(e.value))
    .map((e) => { const r = e.getBoundingClientRect(); return { x: r.x, w: r.width }; }));

  expect(medidas.length, 'no se encuentran los campos ANCHO/ALTO/FONDO: ' +
    'ha cambiado la configuración por defecto del armario y esta prueba ya no ' +
    'mide lo que cree').toBe(3);

  const izquierda = Math.min(...medidas.map((m) => m.x));
  const derecha = Math.max(...medidas.map((m) => m.x + m.w));
  const abarca = (derecha - izquierda) / MOVIL.width;

  expect(abarca, `el panel de configuración abarca el ${Math.round(abarca * 100)} % ` +
    'del ancho del móvil. Sigue clavado a 320 px en vez de apilarse: el armario, ' +
    'que es lo único que hay que mirar, vuelve a quedarse en una tira estrecha')
    .toBeGreaterThan(0.85);
});

test('el armario queda DEBAJO de la configuración, no al lado', async ({ page }) => {
  // Ésta es la que de verdad vigila el apilado (`max-lg:flex-col`).
  //
  // Sin él las tres columnas siguen en fila dentro de un contenedor con
  // `overflow-hidden`: el armario no se encoge, se queda FUERA por la derecha
  // —medido: x=410 en una pantalla de 390— y no hay forma de llegar a él. No da
  // ningún error, no se ve nada raro en la parte de arriba, y el módulo
  // sencillamente no sirve. Apilado, el mismo elemento cae en x=21, y=1634.
  const centro = page.getByText(/2400mm × 2400mm × 600mm/).first();
  await expect(centro, 'no se encuentra el rótulo del armario; ha cambiado el ' +
    'formato de las medidas y esta prueba ya no mide lo que cree').toHaveCount(1);

  const caja = await centro.boundingBox();
  expect(caja.x, `el armario está en x=${Math.round(caja.x)} con una pantalla de ` +
    `${MOVIL.width} px: sigue AL LADO de la configuración en vez de debajo, o sea ` +
    'fuera de la pantalla y sin manera de llegar a él').toBeGreaterThanOrEqual(0);
  expect(caja.x + caja.width, 'el armario se sale por la derecha de la pantalla')
    .toBeLessThanOrEqual(MOVIL.width);

  // Y debajo quiere decir DEBAJO: por detrás de los campos de dimensiones.
  const finConfiguracion = await page.evaluate(() => Math.max(
    ...[...document.querySelectorAll('input')]
      .filter((e) => /^(2400|600)$/.test(e.value))
      .map((e) => e.getBoundingClientRect().bottom + window.scrollY)));
  const yCentro = await centro.evaluate((e) => e.getBoundingClientRect().top + window.scrollY);
  expect(yCentro, 'el armario no está por debajo del panel de configuración')
    .toBeGreaterThan(finConfiguracion);
});
