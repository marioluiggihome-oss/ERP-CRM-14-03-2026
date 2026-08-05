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

**Ninguna dependencia declarada del producto tiene copyleft fuerte.** Nada impide licenciar el ERP como producto cerrado.

PyMuPDF (`fitz`), que era **AGPL-3.0**, se retiró el 05/08/2026 y lo sustituyen `pypdf` (BSD-3-Clause) y `pypdfium2` (Apache-2.0 / BSD-3), ambas permisivas. Todo el trato con PDF pasa ahora por un único módulo, `backend/services/pdf_utils.py`.

Por qué había que quitarlo: la AGPL obliga a poner el código fuente a disposición de quien usa el programa **incluso a través de la red**. Un carpintero entrando en `erp.luiggihome.es` activaba esa obligación sin que hiciera falta vender ni entregar nada.

La sustitución se validó contra los PDFs reales del proyecto: mismos campos de formulario, mismas páginas, mismo tamaño de imagen y mismo recuento de trazos; en el render la diferencia media es de 1,1 sobre 255 (antialiasing). Lo protege `backend/tests/test_calculo_lectura_pdf.py`, que se pone en rojo si alguien vuelve a importar `fitz`.

> Nota: `pymupdf` aparece(n) instalada(s) en la máquina donde se generó este informe pero **no** en `backend/requirements.txt`, así que no viaja(n) con el producto. Es residuo del entorno, no una dependencia.

## Frontend (npm)

**Total: 1257 paquetes** — DESCONOCIDA: 2 · DÉBIL: 1 · PERMISIVA: 1254

### Requieren atención

| Paquete | Versión | Licencia | Clase | ¿Directa? |
|---|---|---|---|---|
| `argparse` | 2.0.1 | Python-2.0 | DESCONOCIDA | transitiva |
| `caniuse-lite` | 1.0.30001761 | CC-BY-4.0 | DESCONOCIDA | transitiva |
| `axe-core` | 4.11.0 | MPL-2.0 | DÉBIL | transitiva |

## Backend (Python)

> ⚠️ **Análisis incompleto.** 109 paquete(s) de requirements.txt no instalados aquí: --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/, aiohappyeyeballs, aiohttp, aiosignal, apscheduler, attrs, bcrypt, black, boto3, botocore, cffi, click
>
> Estos paquetes no están instalados en la máquina donde se generó el informe, así que su licencia NO se ha comprobado. Para un informe completo hay que ejecutarlo en el entorno de producción o tras `pip install -r backend/requirements.txt`.

**Total: 51 paquetes** — FUERTE: 1 · DESCONOCIDA: 17 · DÉBIL: 6 · PERMISIVA: 27

### Requieren atención

| Paquete | Versión | Licencia | Clase | ¿Directa? |
|---|---|---|---|---|
| `pymupdf` | 1.28.0 | Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License | FUERTE | transitiva |
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
