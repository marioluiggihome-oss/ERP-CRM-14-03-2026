const path = require('path');
const { execSync } = require('child_process');
const webpack = require('webpack');

/* LA VERSIÓN QUE SE VE TIENE QUE CAMBIAR SOLA (master, 14/09/2026: «no veo
 * nada de las funciones nuevas en la tablet de 8,6 pulgadas»).
 *
 * La marca de la esquina ponía «ERP v4.1» ESCRITA A MANO, así que enseñaba lo
 * mismo en un despliegue de hoy que en uno de hace tres meses. Y `APP_VERSION`
 * estaba declarada en `App.js` sin que la leyera nadie. O sea que no había
 * forma de saber si un aparato tiene la versión nueva o se ha quedado con la
 * vieja en la caché — y la pregunta «¿está desplegado o es mi tablet?» no se
 * podía contestar mirando la pantalla.
 *
 * Se sella en el momento de compilar. El commit si se puede leer, y SIEMPRE la
 * fecha y hora: en Railway la copia puede venir sin `.git`, y una marca que
 * solo funciona a veces no sirve para comprobar nada. */
const sello = (() => {
  let commit = '';
  try {
    commit = execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
  } catch (_) { /* sin git en el contenedor de compilación: se queda la fecha */ }
  const f = new Date();
  const dos = (n) => String(n).padStart(2, '0');
  const fecha = `${dos(f.getDate())}/${dos(f.getMonth() + 1)} ${dos(f.getHours())}:${dos(f.getMinutes())}`;
  return commit ? `${fecha} · ${commit}` : fecha;
})();

/* SE INYECTA CON EL PLUGIN, NO ESCRIBIENDO `process.env` AQUÍ.
 * Lo segundo no funciona y encima no da error: react-scripts ya ha leído las
 * variables cuando se carga este fichero, así que el `REACT_APP_BUILD` se
 * quedaba SIN SUSTITUIR dentro del paquete —se veía el nombre de la variable
 * en el código compilado— y en pantalla habría salido el respaldo «dev» en
 * producción. Se cazó mirando el paquete después de compilar, que es la única
 * forma de saberlo. */
module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    plugins: {
      add: [
        new webpack.DefinePlugin({
          'process.env.REACT_APP_BUILD': JSON.stringify(sello),
        }),
      ],
    },
  },
};
