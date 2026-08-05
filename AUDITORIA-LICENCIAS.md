# Auditoría de licencias de terceros

Generado el 05/08/2026 con `herramientas/licencias_dependencias.py`.

El ERP es **software propietario** que se licencia a clientes. Una dependencia con licencia copyleft fuerte (GPL/AGPL) puede obligar a publicar el código propio al distribuirlo. Este informe existe para que eso no aparezca por sorpresa el día de una venta.

| Clase | Qué significa | Qué hacer |
|---|---|---|
| **PERMISIVA** | MIT, BSD, Apache-2.0, ISC | Nada. Basta con conservar los avisos de copyright. |
| **DÉBIL** | LGPL, MPL, EPL | Se puede usar en producto cerrado si no se modifica la librería y se enlaza sin incrustarla. |
| **FUERTE** | GPL, AGPL | **Riesgo.** Revisar con un abogado antes de distribuir. AGPL alcanza incluso al servicio por red. |
| **DESCONOCIDA** | No declarada | Mirarla a mano: sin licencia expresa, por defecto NO hay permiso de uso. |

## Hallazgo principal

### `pymupdf` 1.28.0 — Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License

**Este es el punto a resolver con un abogado.** PyMuPDF (`fitz`) se distribuye con licencia doble: **AGPL-3.0** o una licencia comercial de pago de Artifex. Mientras no se compre la comercial, aplica la AGPL.

La AGPL no es como la GPL normal: tiene una cláusula de **uso en red**. No hace falta vender ni entregar el programa — basta con que un tercero lo use a través de Internet, que es exactamente lo que pasa cuando un carpintero entra en `erp.luiggihome.es`. En esa lectura, la obligación de poner el código fuente a disposición de ese usuario se activa sola.

Dónde se usa hoy (3 ficheros, todo lectura y rasterizado de PDF):

- `backend/services/pdf_utils.py`
- `backend/services/proforma_cascos.py` — páginas de la proforma a imagen
- `backend/services/mv_relacion.py` — lectura de los campos de la plantilla MV

**Tres salidas, de menos a más trabajo:**

1. **Comprar la licencia comercial de Artifex.** Cero cambios de código. Es la opción si el ERP se va a vender a terceros. Hay que pedirles precio.
2. **Sustituir PyMuPDF por librerías permisivas.** Es viable porque el uso que se le da es sencillo: `pypdf` (BSD) lee los campos AcroForm de la plantilla MV, y `pypdfium2` (Apache-2.0 / BSD-3) rasteriza páginas a imagen. Ambas permiten producto cerrado sin pagar nada.
3. **Asumir la AGPL.** Solo tiene sentido si el ERP nunca sale de casa. En cuanto haya un cliente externo usándolo por web, deja de valer.

> Ojo: esto es un aviso técnico, no un dictamen. La lectura de la cláusula de red de la AGPL tiene matices y conviene que lo confirme un abogado de propiedad intelectual antes de firmar la primera licencia con un cliente.

## Frontend (npm)

**Total: 1257 paquetes** — DESCONOCIDA: 2 · DÉBIL: 1 · PERMISIVA: 1254

### Requieren atención

| Paquete | Versión | Licencia | Clase | ¿Directa? |
|---|---|---|---|---|
| `argparse` | 2.0.1 | Python-2.0 | DESCONOCIDA | transitiva |
| `caniuse-lite` | 1.0.30001761 | CC-BY-4.0 | DESCONOCIDA | transitiva |
| `axe-core` | 4.11.0 | MPL-2.0 | DÉBIL | transitiva |

## Backend (Python)

> ⚠️ **Análisis incompleto.** 107 paquete(s) de requirements.txt no instalados aquí: --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/, aiohappyeyeballs, aiohttp, aiosignal, apscheduler, attrs, bcrypt, black, boto3, botocore, cffi, click
>
> Estos paquetes no están instalados en la máquina donde se generó el informe, así que su licencia NO se ha comprobado. Para un informe completo hay que ejecutarlo en el entorno de producción o tras `pip install -r backend/requirements.txt`.

**Total: 51 paquetes** — FUERTE: 1 · DESCONOCIDA: 17 · DÉBIL: 6 · PERMISIVA: 27

### Requieren atención

| Paquete | Versión | Licencia | Clase | ¿Directa? |
|---|---|---|---|---|
| `pymupdf` | 1.28.0 | Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License | FUERTE | sí |
| `annotated-doc` | 0.0.5 | — | DESCONOCIDA | transitiva |
| `anyio` | 4.14.2 | — | DESCONOCIDA | sí |
| `fastapi` | 0.141.1 | — | DESCONOCIDA | sí |
| `fasteners` | 0.20 | — | DESCONOCIDA | transitiva |
| `idna` | 3.11 | — | DESCONOCIDA | sí |
| `iniconfig` | 2.3.0 | — | DESCONOCIDA | sí |
| `MarkupSafe` | 3.0.3 | — | DESCONOCIDA | sí |
| `pillow` | 12.3.0 | — | DESCONOCIDA | sí |
| `pydantic` | 2.13.4 | — | DESCONOCIDA | sí |
| `pydantic_core` | 2.46.4 | — | DESCONOCIDA | sí |
| `Pygments` | 2.20.0 | — | DESCONOCIDA | sí |
| `pytest` | 9.1.1 | — | DESCONOCIDA | sí |
| `python-dateutil` | 2.9.0.post0 | Dual License | DESCONOCIDA | sí |
| `starlette` | 1.3.1 | — | DESCONOCIDA | sí |
| `typing-inspection` | 0.4.2 | — | DESCONOCIDA | sí |
| `typing_extensions` | 4.16.0 | — | DESCONOCIDA | sí |
| `urllib3` | 2.6.3 | — | DESCONOCIDA | sí |
| `certifi` | 2026.2.25 | MPL-2.0 | DÉBIL | sí |
| `launchpadlib` | 1.11.0 | LGPL v3 | DÉBIL | transitiva |
| `lazr.restfulclient` | 0.14.6 | LGPL v3 | DÉBIL | transitiva |
| `lazr.uri` | 1.0.6 | LGPL v3 | DÉBIL | transitiva |
| `PyGObject` | 3.48.2 | GNU LGPL | DÉBIL | transitiva |
| `wadllib` | 1.3.6 | LGPL v3 | DÉBIL | transitiva |

## Código de terceros copiado dentro del repositorio

No son dependencias: son ficheros ajenos que viven en nuestro árbol de código. Quedan EXCLUIDOS del aviso de copyright propio (`herramientas/cabeceras_copyright.py`), porque firmar como propio el código de otro no protege nada.

| Ruta | Origen | Licencia | Nota |
|---|---|---|---|
| `frontend/src/components/ui/` | shadcn/ui | MIT | 46 componentes copiados. MIT permite uso comercial y cerrado; solo exige conservar el aviso de copyright y la licencia. |
| `frontend/src/lib/utils.js` | shadcn/ui | MIT | Helper `cn` (clsx + tailwind-merge). |

---

_Informe automático. No sustituye el criterio de un abogado; sirve para saber qué preguntarle._
