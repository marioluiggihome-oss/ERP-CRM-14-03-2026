/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * Pruebas de PANTALLA en un navegador de verdad.
 *
 * POR QUÉ UN NAVEGADOR Y NO jsdom
 * -------------------------------
 * Porque lo que se comprueba aquí es LAYOUT, y jsdom no tiene motor de layout:
 * con jsdom sólo se pueden mirar nombres de clases CSS, que es exactamente lo
 * que ya hacían las pruebas de `backend/tests/test_pantalla_*.py` leyendo el
 * JSX con expresiones regulares. Cambiar un `grep` por un `getAttribute` no
 * responde a la pregunta: «¿caben los nueve botones en un móvil de 390 px?».
 * Sólo un navegador con un viewport real lo sabe.
 *
 * Las de Python siguen donde están y siguen sirviendo — son baratas y cazan un
 * borrado accidental en un segundo—, pero la VERDAD sobre el layout está aquí.
 *
 * Se sirve `build/`, no el servidor de desarrollo: es lo que de verdad llega al
 * móvil del master.
 */
const { defineConfig, devices } = require('@playwright/test');

const PUERTO = Number(process.env.PUERTO || 4321);

module.exports = defineConfig({
  testDir: './e2e',
  // Un fallo de layout no se arregla solo al reintentar: si esto parpadea es
  // que la prueba está mal escrita, y se quiere ver.
  retries: 0,
  workers: 1,
  // El Estudio 3D obliga a conducir el flujo entero —entrar, Armarios, abrir
  // el estudio, generar— antes de poder medir nada: pasa de 40 s por prueba.
  timeout: 120000,
  reporter: process.env.CI ? 'list' : 'line',
  use: {
    baseURL: `http://127.0.0.1:${PUERTO}`,
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `node e2e/servidor-estatico.js`,
    url: `http://127.0.0.1:${PUERTO}`,
    reuseExistingServer: !process.env.CI,
    // El Estudio 3D obliga a conducir el flujo entero —entrar, Armarios, abrir
  // el estudio, generar— antes de poder medir nada: pasa de 40 s por prueba.
  timeout: 120000,
    env: { PUERTO: String(PUERTO) },
  },
});
