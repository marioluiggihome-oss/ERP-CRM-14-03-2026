#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Auditoría de licencias de las dependencias de terceros.

Por qué importa: el ERP es software propietario que se licencia a clientes. Si
una dependencia es COPYLEFT FUERTE (GPL, AGPL), distribuirla enlazada con tu
código puede obligarte a publicar el tuyo. Es el riesgo que revienta una venta
de licencias, y no se ve hasta que alguien lo mira.

Clasificación (ver AUDITORIA-LICENCIAS.md para el detalle):
    PERMISIVA   MIT, BSD, Apache-2.0, ISC…  — sin problema, solo atribución.
    DÉBIL       LGPL, MPL, EPL              — vigilar; suele bastar con no
                                              modificar la librería.
    FUERTE      GPL, AGPL                   — RIESGO en software propietario.
    DESCONOCIDA no declarada                — hay que mirarla a mano.

Uso:
    python3 herramientas/licencias_dependencias.py            # informe
    python3 herramientas/licencias_dependencias.py --md       # a AUDITORIA-LICENCIAS.md
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FUERTE = re.compile(r"\bA?GPL\b|GNU General Public", re.I)
DEBIL = re.compile(r"\bLGPL\b|Mozilla Public|\bMPL\b|Eclipse Public|\bEPL\b|\bCDDL\b", re.I)
PERMISIVA = re.compile(r"\bMIT\b|BSD|Apache|\bISC\b|Unlicense|Zlib|Python Software Foundation|\bPSF\b|CC0|WTFPL", re.I)


def _clase_simple(t: str) -> str:
    # El orden importa: "LGPL" contiene "GPL", así que lo débil se mira antes.
    if DEBIL.search(t):
        return "DÉBIL"
    if FUERTE.search(t):
        return "FUERTE"
    if PERMISIVA.search(t):
        return "PERMISIVA"
    return "DESCONOCIDA"


def clasificar(lic: str) -> str:
    """Clase de riesgo de una licencia, entendiendo las DOBLES.

    Una licencia doble con "OR" la eliges tú: `(BSD-3-Clause OR GPL-2.0)` se
    puede usar como BSD y no contamina nada. Marcarla como GPL es un falso
    positivo que hace que nadie se crea el informe.

    OJO con el caso contrario: PyMuPDF es "AGPL 3.0 **or** Artifex Commercial
    License". También lleva "or", pero la alternativa no es permisiva: es
    PAGAR. Mientras no se pague, manda la AGPL. Por eso solo se rebaja cuando
    alguna de las opciones es realmente permisiva.
    """
    t = (lic or "").strip()
    if not t or t.lower() in ("unknown", "none", "null"):
        return "DESCONOCIDA"
    partes = [p for p in re.split(r"\bor\b|\|\|", t, flags=re.I) if p.strip()]
    if len(partes) > 1:
        clases = [_clase_simple(p) for p in partes]
        if "PERMISIVA" in clases:
            return "PERMISIVA"
        if "DÉBIL" in clases:
            return "DÉBIL"
        return "FUERTE" if "FUERTE" in clases else "DESCONOCIDA"
    return _clase_simple(t)


# Paquetes del SISTEMA operativo del contenedor: están en el intérprete, no en
# nuestro requirements.txt, y no se distribuyen con el producto. Contarlos como
# riesgo es ruido.
DEL_SISTEMA = {"python-apt", "unattended-upgrades", "distro-info", "command-not-found"}


# ─── Frontend: se lee del propio node_modules, que es la verdad instalada ────
def licencias_npm():
    base = os.path.join(RAIZ, "frontend", "node_modules")
    pkg_json = os.path.join(RAIZ, "frontend", "package.json")
    if not os.path.isdir(base):
        return [], "node_modules no está instalado: `cd frontend && yarn install`"
    try:
        with open(pkg_json, encoding="utf-8") as f:
            manifiesto = json.load(f)
    except Exception as e:
        return [], f"no se ha podido leer package.json: {e}"
    directas = set(manifiesto.get("dependencies", {})) | set(manifiesto.get("devDependencies", {}))

    filas = []
    for nombre in sorted(os.listdir(base)):
        if nombre.startswith("."):
            continue
        rutas = []
        if nombre.startswith("@"):  # paquetes con ámbito: @scope/paquete
            sub = os.path.join(base, nombre)
            if os.path.isdir(sub):
                rutas = [(f"{nombre}/{s}", os.path.join(sub, s)) for s in sorted(os.listdir(sub))]
        else:
            rutas = [(nombre, os.path.join(base, nombre))]
        for pkg, ruta in rutas:
            j = os.path.join(ruta, "package.json")
            if not os.path.isfile(j):
                continue
            try:
                with open(j, encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue
            lic = d.get("license")
            if isinstance(lic, dict):
                lic = lic.get("type", "")
            if not lic and isinstance(d.get("licenses"), list):
                lic = ", ".join(x.get("type", "") for x in d["licenses"] if isinstance(x, dict))
            filas.append({
                "paquete": pkg,
                "version": d.get("version", ""),
                "licencia": (lic or "").strip(),
                "clase": clasificar(lic or ""),
                "directa": pkg in directas,
            })
    return filas, None


# ─── Backend: metadatos de los paquetes instalados ──────────────────────────
def licencias_pip():
    try:
        from importlib import metadata
    except Exception as e:  # pragma: no cover
        return [], f"sin importlib.metadata: {e}"

    req = os.path.join(RAIZ, "backend", "requirements.txt")
    directas = set()
    if os.path.isfile(req):
        with open(req, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                directas.add(re.split(r"[<>=!\[;]", linea)[0].strip().lower())

    filas, vistos = [], set()
    for dist in metadata.distributions():
        try:
            m = dist.metadata
            nombre = (m.get("Name") or "").strip()
        except Exception:
            continue
        if not nombre or nombre.lower() in vistos:
            continue
        vistos.add(nombre.lower())
        lic = (m.get("License") or "").strip()
        if not lic or len(lic) > 80:
            # Muchos paquetes dejan License vacío y lo dicen en los clasificadores.
            clas = [c for c in (m.get_all("Classifier") or []) if c.startswith("License ::")]
            if clas:
                lic = clas[0].split("::")[-1].strip()
            elif len(lic) > 80:
                lic = lic.splitlines()[0][:80]
        if nombre.lower() in DEL_SISTEMA:
            continue
        filas.append({
            "paquete": nombre,
            "version": (m.get("Version") or "").strip(),
            "licencia": lic,
            "clase": clasificar(lic),
            "directa": nombre.lower() in directas,
        })
    faltan = sorted(directas - vistos)
    return sorted(filas, key=lambda r: r["paquete"].lower()), (
        f"{len(faltan)} paquete(s) de requirements.txt no instalados aquí: "
        f"{', '.join(faltan[:12])}" if faltan else None)


# ─── Código de terceros COPIADO dentro del repo ─────────────────────────────
# No es una dependencia: son ficheros ajenos que viven en nuestro árbol. Van
# aparte porque no aparecen en ningún package.json y es fácil olvidarlos.
COPIADO_DENTRO = [
    {"ruta": "frontend/src/components/ui/", "origen": "shadcn/ui", "licencia": "MIT",
     "nota": "46 componentes copiados. MIT permite uso comercial y cerrado; "
             "solo exige conservar el aviso de copyright y la licencia."},
    {"ruta": "frontend/src/lib/utils.js", "origen": "shadcn/ui", "licencia": "MIT",
     "nota": "Helper `cn` (clsx + tailwind-merge)."},
]

NOTA_RESUELTO_PYMUPDF = [
    "PyMuPDF (`fitz`), que era **AGPL-3.0**, se retiró el 05/08/2026 y lo "
    "sustituyen `pypdf` (BSD-3-Clause) y `pypdfium2` (Apache-2.0 / BSD-3), "
    "ambas permisivas. Todo el trato con PDF pasa ahora por un único módulo, "
    "`backend/services/pdf_utils.py`.",
    "",
    "Por qué había que quitarlo: la AGPL obliga a poner el código fuente a "
    "disposición de quien usa el programa **incluso a través de la red**. Un "
    "carpintero entrando en `erp.luiggihome.es` activaba esa obligación sin que "
    "hiciera falta vender ni entregar nada.",
    "",
    "La sustitución se validó contra los PDFs reales del proyecto: mismos "
    "campos de formulario, mismas páginas, mismo tamaño de imagen y mismo "
    "recuento de trazos; en el render la diferencia media es de 1,1 sobre 255 "
    "(antialiasing). Lo protege `backend/tests/test_calculo_lectura_pdf.py`, "
    "que se pone en rojo si alguien vuelve a importar `fitz`.",
]

ORDEN = {"FUERTE": 0, "DESCONOCIDA": 1, "DÉBIL": 2, "PERMISIVA": 3}

# Explicación escrita a mano del único riesgo real detectado. Va aquí y no
# generada, porque lo que hay que entender no es el dato sino la consecuencia.
NOTA_PYMUPDF = [
    "**Este es el punto a resolver con un abogado.** PyMuPDF (`fitz`) se "
    "distribuye con licencia doble: **AGPL-3.0** o una licencia comercial de "
    "pago de Artifex. Mientras no se compre la comercial, aplica la AGPL.",
    "",
    "La AGPL no es como la GPL normal: tiene una cláusula de **uso en red**. "
    "No hace falta vender ni entregar el programa — basta con que un tercero lo "
    "use a través de Internet, que es exactamente lo que pasa cuando un "
    "carpintero entra en `erp.luiggihome.es`. En esa lectura, la obligación de "
    "poner el código fuente a disposición de ese usuario se activa sola.",
    "",
    "Dónde se usa hoy (3 ficheros, todo lectura y rasterizado de PDF):",
    "",
    "- `backend/services/pdf_utils.py`",
    "- `backend/services/proforma_cascos.py` — páginas de la proforma a imagen",
    "- `backend/services/mv_relacion.py` — lectura de los campos de la plantilla MV",
    "",
    "**Tres salidas, de menos a más trabajo:**",
    "",
    "1. **Comprar la licencia comercial de Artifex.** Cero cambios de código. "
    "Es la opción si el ERP se va a vender a terceros. Hay que pedirles precio.",
    "2. **Sustituir PyMuPDF por librerías permisivas.** Es viable porque el uso "
    "que se le da es sencillo: `pypdf` (BSD) lee los campos AcroForm de la "
    "plantilla MV, y `pypdfium2` (Apache-2.0 / BSD-3) rasteriza páginas a imagen. "
    "Ambas permiten producto cerrado sin pagar nada.",
    "3. **Asumir la AGPL.** Solo tiene sentido si el ERP nunca sale de casa. "
    "En cuanto haya un cliente externo usándolo por web, deja de valer.",
    "",
    "> Ojo: esto es un aviso técnico, no un dictamen. La lectura de la cláusula "
    "de red de la AGPL tiene matices y conviene que lo confirme un abogado de "
    "propiedad intelectual antes de firmar la primera licencia con un cliente.",
]


def resumen(filas):
    r = {}
    for f in filas:
        r[f["clase"]] = r.get(f["clase"], 0) + 1
    return r


def informe_md(npm, pip, aviso_npm, aviso_pip):
    hoy = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    L = []
    L.append("# Auditoría de licencias de terceros")
    L.append("")
    L.append(f"Generado el {hoy} con `herramientas/licencias_dependencias.py`.")
    L.append("")
    L.append("El ERP es **software propietario** que se licencia a clientes. Una "
             "dependencia con licencia copyleft fuerte (GPL/AGPL) puede obligar a "
             "publicar el código propio al distribuirlo. Este informe existe para "
             "que eso no aparezca por sorpresa el día de una venta.")
    L.append("")
    L.append("| Clase | Qué significa | Qué hacer |")
    L.append("|---|---|---|")
    L.append("| **PERMISIVA** | MIT, BSD, Apache-2.0, ISC | Nada. Basta con conservar los avisos de copyright. |")
    L.append("| **DÉBIL** | LGPL, MPL, EPL | Se puede usar en producto cerrado si no se modifica la librería y se enlaza sin incrustarla. |")
    L.append("| **FUERTE** | GPL, AGPL | **Riesgo.** Revisar con un abogado antes de distribuir. AGPL alcanza incluso al servicio por red. |")
    L.append("| **DESCONOCIDA** | No declarada | Mirarla a mano: sin licencia expresa, por defecto NO hay permiso de uso. |")
    L.append("")

    fuertes = [f for f in npm + pip if f["clase"] == "FUERTE"]
    declaradas = [f for f in fuertes if f["directa"]]
    residuales = [f for f in fuertes if not f["directa"]]
    L.append("## Hallazgo principal")
    L.append("")
    if not declaradas:
        L.append("**Ninguna dependencia declarada del producto tiene copyleft "
                 "fuerte.** Nada impide licenciar el ERP como producto cerrado.")
        L.append("")
        if any(f["paquete"].lower() == "pymupdf" for f in residuales):
            L.extend(NOTA_RESUELTO_PYMUPDF)
            L.append("")
    else:
        for f in declaradas:
            L.append(f"### `{f['paquete']}` {f['version']} — {f['licencia']}")
            L.append("")
        if any(f["paquete"].lower() == "pymupdf" for f in declaradas):
            L.extend(NOTA_PYMUPDF)
        L.append("")
    if residuales:
        L.append("> Nota: " + ", ".join(f"`{f['paquete']}`" for f in residuales) +
                 " aparece(n) instalada(s) en la máquina donde se generó este "
                 "informe pero **no** en `backend/requirements.txt`, así que no "
                 "viaja(n) con el producto. Es residuo del entorno, no una "
                 "dependencia.")
        L.append("")

    for titulo, filas, aviso in (("Frontend (npm)", npm, aviso_npm), ("Backend (Python)", pip, aviso_pip)):
        L.append(f"## {titulo}")
        L.append("")
        if aviso:
            L.append(f"> ⚠️ **Análisis incompleto.** {aviso}")
            L.append(">")
            L.append("> Estos paquetes no están instalados en la máquina donde se "
                     "generó el informe, así que su licencia NO se ha comprobado. "
                     "Para un informe completo hay que ejecutarlo en el entorno de "
                     "producción o tras `pip install -r backend/requirements.txt`.")
            L.append("")
        if not filas:
            L.append("_Sin datos._")
            L.append("")
            continue
        res = resumen(filas)
        L.append("**Total: %d paquetes** — %s" % (
            len(filas),
            " · ".join(f"{k}: {v}" for k, v in sorted(res.items(), key=lambda kv: ORDEN.get(kv[0], 9)))))
        L.append("")
        atencion = [f for f in filas if f["clase"] in ("FUERTE", "DÉBIL", "DESCONOCIDA")]
        if atencion:
            L.append("### Requieren atención")
            L.append("")
            L.append("| Paquete | Versión | Licencia | Clase | ¿Directa? |")
            L.append("|---|---|---|---|---|")
            for f in sorted(atencion, key=lambda f: (ORDEN.get(f["clase"], 9), f["paquete"].lower())):
                L.append(f"| `{f['paquete']}` | {f['version']} | {f['licencia'] or '—'} | "
                         f"{f['clase']} | {'sí' if f['directa'] else 'transitiva'} |")
            L.append("")
        else:
            L.append("Todas permisivas. Nada que revisar.")
            L.append("")

    L.append("## Código de terceros copiado dentro del repositorio")
    L.append("")
    L.append("No son dependencias: son ficheros ajenos que viven en nuestro árbol de "
             "código. Quedan EXCLUIDOS del aviso de copyright propio "
             "(`herramientas/cabeceras_copyright.py`), porque firmar como propio el "
             "código de otro no protege nada.")
    L.append("")
    L.append("| Ruta | Origen | Licencia | Nota |")
    L.append("|---|---|---|---|")
    for c in COPIADO_DENTRO:
        L.append(f"| `{c['ruta']}` | {c['origen']} | {c['licencia']} | {c['nota']} |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("_Informe automático. No sustituye el criterio de un abogado; sirve para "
             "saber qué preguntarle._")
    return "\n".join(L) + "\n"


def main():
    npm, aviso_npm = licencias_npm()
    pip, aviso_pip = licencias_pip()

    if "--md" in sys.argv:
        destino = os.path.join(RAIZ, "AUDITORIA-LICENCIAS.md")
        with open(destino, "w", encoding="utf-8") as f:
            f.write(informe_md(npm, pip, aviso_npm, aviso_pip))
        print(f"✓ informe escrito en {os.path.relpath(destino, RAIZ)}")

    # Solo cuenta como riesgo lo que el producto DECLARA: lo que este instalado
    # en la maquina del informe y no en requirements.txt no se distribuye.
    riesgos = [f for f in npm + pip if f["clase"] == "FUERTE" and f["directa"]]
    for titulo, filas, aviso in (("npm", npm, aviso_npm), ("python", pip, aviso_pip)):
        print(f"\n{titulo}: {len(filas)} paquetes — " +
              " · ".join(f"{k}: {v}" for k, v in sorted(resumen(filas).items(),
                                                        key=lambda kv: ORDEN.get(kv[0], 9))))
        if aviso:
            print(f"  ⚠️  {aviso}")
    otras = [f for f in npm + pip if f["clase"] == "FUERTE" and not f["directa"]]
    if otras:
        print("\n· copyleft fuerte instalado pero NO declarado (residuo del "
              "entorno, no viaja con el producto): " +
              ", ".join(f["paquete"] for f in otras))
    if riesgos:
        print(f"\n✗ {len(riesgos)} dependencia(s) DECLARADA(S) con COPYLEFT FUERTE (GPL/AGPL):")
        for f in riesgos:
            print(f"    {f['paquete']} {f['version']} — {f['licencia']} "
                  f"({'directa' if f['directa'] else 'transitiva'})")
        return 1
    print("\n✓ ninguna dependencia con copyleft fuerte (GPL/AGPL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
