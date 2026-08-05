#!/usr/bin/env python3
# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Inventario firmado del código: qué ficheros hay y qué contiene cada uno.

Para qué sirve: el derecho de autor sobre el software nace solo, pero en un
pleito lo que decide es la PRUEBA. Un depósito notarial o un registro en el
Registro de la Propiedad Intelectual acredita una fecha; lo que no acredita por
sí solo es *qué* había exactamente ese día si luego el código sigue cambiando.

Este inventario cierra ese hueco: para cada fichero deja su huella SHA-256, y
para el conjunto una huella global. Con eso, enseñar un fichero años después y
demostrar que es el mismo que se depositó es comparar dos cadenas. Si alguien
copia el producto, la comparación de huellas fichero a fichero también sirve
para señalar qué se copió.

No sustituye al depósito: es el documento que se deposita (o que se adjunta al
sellado de tiempo).

Uso:
    python3 herramientas/inventario_codigo.py             # genera los dos ficheros
    python3 herramientas/inventario_codigo.py --verificar # comprueba que nada cambió
"""
import csv
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_SALIDA = os.path.join(RAIZ, "INVENTARIO-CODIGO.csv")
MD_SALIDA = os.path.join(RAIZ, "INVENTARIO-CODIGO.md")

TITULAR = "Luiggi Home"
# Código de terceros: se inventaría igual (forma parte de lo entregado) pero
# marcado, para no reclamar autoría sobre lo que no es nuestro.
DE_TERCEROS = ("frontend/src/components/ui/", "frontend/src/lib/utils.js")

# El propio inventario queda fuera: un fichero no puede contener su propia
# huella (cambiaría al escribirla). Sin esto, `--verificar` daría siempre
# "modificado" sobre sí mismo y el inventario no serviría para nada.
GENERADOS = ("INVENTARIO-CODIGO.csv", "INVENTARIO-CODIGO.md")


def _git(*args, defecto=""):
    try:
        return subprocess.run(["git", "-C", RAIZ, *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return defecto


def _ficheros_versionados():
    """Los ficheros que git controla. Es la definición correcta de "el código":
    deja fuera builds, node_modules y basura local sin tener que listarlos."""
    salida = _git("ls-files", "-z")
    return sorted(p for p in salida.split("\0") if p)


def _huella(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(65536), b""):
            h.update(trozo)
    return h.hexdigest()


def _es_de_terceros(rel):
    return any(rel.startswith(p) or rel == p.rstrip("/") for p in DE_TERCEROS)


def recolectar():
    filas = []
    for rel in _ficheros_versionados():
        if rel in GENERADOS:
            continue
        ruta = os.path.join(RAIZ, rel)
        if not os.path.isfile(ruta):   # enlaces rotos, submódulos
            continue
        filas.append({
            "ruta": rel,
            "bytes": os.path.getsize(ruta),
            "sha256": _huella(ruta),
            "autoria": "terceros" if _es_de_terceros(rel) else TITULAR,
        })
    return filas


def huella_global(filas):
    """Huella del conjunto: se firma la lista de (ruta, huella), no los bytes.

    Así el resultado no depende del orden en que se recorra el disco y sigue
    cambiando si se añade, se borra o se modifica cualquier fichero.
    """
    h = hashlib.sha256()
    for f in sorted(filas, key=lambda f: f["ruta"]):
        h.update(f"{f['ruta']}\0{f['sha256']}\n".encode("utf-8"))
    return h.hexdigest()


def escribir_csv(filas):
    with open(CSV_SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ruta", "bytes", "sha256", "autoria"])
        w.writeheader()
        for fila in sorted(filas, key=lambda x: x["ruta"]):
            w.writerow(fila)


def escribir_md(filas, global_):
    ahora = datetime.now(timezone.utc)
    commit = _git("rev-parse", "HEAD", defecto="(sin git)")
    fecha_commit = _git("log", "-1", "--format=%cI", defecto="")
    rama = _git("rev-parse", "--abbrev-ref", "HEAD", defecto="")
    propios = [f for f in filas if f["autoria"] == TITULAR]
    ajenos = [f for f in filas if f["autoria"] != TITULAR]
    total_bytes = sum(f["bytes"] for f in filas)

    por_ext = {}
    for f in propios:
        ext = os.path.splitext(f["ruta"])[1].lower() or "(sin extensión)"
        d = por_ext.setdefault(ext, {"n": 0, "bytes": 0})
        d["n"] += 1
        d["bytes"] += f["bytes"]

    L = []
    L.append(f"# Inventario del código fuente — {TITULAR}")
    L.append("")
    L.append(f"**Huella global SHA-256:** `{global_}`")
    L.append("")
    L.append("| Dato | Valor |")
    L.append("|---|---|")
    L.append(f"| Generado (UTC) | {ahora.strftime('%Y-%m-%d %H:%M:%S')} |")
    L.append(f"| Commit | `{commit}` |")
    L.append(f"| Fecha del commit | {fecha_commit or '—'} |")
    L.append(f"| Rama | {rama or '—'} |")
    L.append(f"| Ficheros inventariados | {len(filas)} |")
    L.append(f"| — de autoría {TITULAR} | {len(propios)} |")
    L.append(f"| — de terceros (ver AUDITORIA-LICENCIAS.md) | {len(ajenos)} |")
    L.append(f"| Tamaño total | {total_bytes / 1024 / 1024:.2f} MB |")
    L.append("")
    L.append("## Para qué sirve este documento")
    L.append("")
    L.append("Acredita **qué contenía** el código en la fecha de arriba. La huella "
             "SHA-256 de un fichero cambia si cambia un solo carácter, así que "
             "comparar la huella de un fichero de hoy con la de esta lista "
             "demuestra si es o no el mismo. La *huella global* resume todo el "
             "conjunto en una sola cadena: es la que conviene hacer constar en un "
             "acta notarial o en un sellado de tiempo, porque protege la lista "
             "entera con un solo dato.")
    L.append("")
    L.append("El detalle fichero a fichero está en "
             "[`INVENTARIO-CODIGO.csv`](INVENTARIO-CODIGO.csv) "
             f"({len(filas)} líneas), que es el que se adjunta al depósito.")
    L.append("")
    L.append("## Cómo comprobar que un fichero no ha cambiado")
    L.append("")
    L.append("```bash")
    L.append("sha256sum backend/services/mv_relacion.py")
    L.append("# y buscar esa misma cadena en INVENTARIO-CODIGO.csv")
    L.append("")
    L.append("# o de una vez, todo el repositorio:")
    L.append("python3 herramientas/inventario_codigo.py --verificar")
    L.append("```")
    L.append("")
    L.append("## Composición del código propio")
    L.append("")
    L.append("| Tipo | Ficheros | Tamaño |")
    L.append("|---|---|---|")
    for ext, d in sorted(por_ext.items(), key=lambda kv: -kv[1]["bytes"])[:15]:
        L.append(f"| `{ext}` | {d['n']} | {d['bytes'] / 1024:.0f} KB |")
    L.append("")
    L.append("## Qué NO cubre")
    L.append("")
    L.append("- Los ficheros de terceros van marcados como `terceros` en el CSV. "
             "Están inventariados porque forman parte de lo que se entrega, pero "
             f"**no** se reclama autoría sobre ellos.")
    L.append("- Solo entra lo que está bajo control de versiones. Las claves, la "
             "base de datos y los ficheros de entorno quedan fuera a propósito: "
             "son secreto empresarial y no deben salir del servidor.")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"© {ahora.year} {TITULAR}. Documento generado automáticamente por "
             "`herramientas/inventario_codigo.py`.")
    with open(MD_SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def verificar():
    """Compara el estado actual con el CSV guardado."""
    if not os.path.isfile(CSV_SALIDA):
        print("✗ no hay INVENTARIO-CODIGO.csv: genéralo primero")
        return 1
    with open(CSV_SALIDA, encoding="utf-8") as f:
        guardado = {r["ruta"]: r["sha256"] for r in csv.DictReader(f)}
    actual = {f["ruta"]: f["sha256"] for f in recolectar()}

    cambiados = sorted(r for r in guardado.keys() & actual.keys()
                       if guardado[r] != actual[r])
    borrados = sorted(guardado.keys() - actual.keys())
    nuevos = sorted(actual.keys() - guardado.keys())

    if not (cambiados or borrados or nuevos):
        print(f"✓ los {len(actual)} ficheros coinciden con el inventario")
        return 0
    print(f"El código ha cambiado desde el último inventario:")
    for titulo, lista in (("modificados", cambiados), ("nuevos", nuevos),
                          ("borrados", borrados)):
        if lista:
            print(f"\n  {len(lista)} {titulo}:")
            for r in lista[:20]:
                print(f"    {r}")
            if len(lista) > 20:
                print(f"    … y {len(lista) - 20} más")
    print("\n  Esto NO es un error: el código evoluciona. Vuelve a generar el "
          "inventario antes de depositarlo:")
    print("    python3 herramientas/inventario_codigo.py")
    return 1


def main():
    if "--verificar" in sys.argv:
        return verificar()
    filas = recolectar()
    g = huella_global(filas)
    escribir_csv(filas)
    escribir_md(filas, g)
    propios = sum(1 for f in filas if f["autoria"] == TITULAR)
    print(f"✓ inventariados {len(filas)} ficheros ({propios} propios, "
          f"{len(filas) - propios} de terceros)")
    print(f"  huella global SHA-256: {g}")
    print(f"  → {os.path.relpath(CSV_SALIDA, RAIZ)} y {os.path.relpath(MD_SALIDA, RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
