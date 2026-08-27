/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * Servidor estático mínimo para servir `build/` durante las pruebas de pantalla.
 *
 * POR QUÉ NO SE USA UNA LIBRERÍA
 * ------------------------------
 * Porque son treinta líneas y una dependencia menos. `http-server` o `serve`
 * harían lo mismo, pero cada paquete que entra hay que mirarle la licencia
 * (regla de la casa) y, en el CI, descargarlo antes de poder comprobar nada.
 * Un servidor de ficheros no es un problema que merezca una dependencia.
 *
 * Todo lo que no existe cae en index.html: la app es una SPA.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const RAIZ = path.join(__dirname, '..', 'build');
const TIPOS = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2',
};

function crearServidor() {
  return http.createServer((req, res) => {
    const limpia = decodeURIComponent((req.url || '/').split('?')[0]);
    // Nada de subir por encima de build/: `..` en la URL no saca del directorio.
    let destino = path.normalize(path.join(RAIZ, limpia));
    if (!destino.startsWith(RAIZ)) destino = RAIZ;
    if (!fs.existsSync(destino) || fs.statSync(destino).isDirectory()) {
      destino = path.join(RAIZ, 'index.html');
    }
    if (!fs.existsSync(destino)) {
      res.writeHead(404); return res.end('no hay build: ejecuta primero `yarn build`');
    }
    res.writeHead(200, { 'Content-Type': TIPOS[path.extname(destino)] || 'application/octet-stream' });
    fs.createReadStream(destino).pipe(res);
  });
}

if (require.main === module) {
  const puerto = Number(process.env.PUERTO || 4321);
  crearServidor().listen(puerto, () => console.log(`sirviendo build/ en http://127.0.0.1:${puerto}`));
}

module.exports = { crearServidor };
