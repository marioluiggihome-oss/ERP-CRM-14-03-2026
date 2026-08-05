#!/usr/bin/env python3
"""Pone (y comprueba) el aviso de copyright en el código propio del ERP.

Para qué sirve: el derecho de autor sobre el código nace solo, sin registrar
nada, pero en un pleito lo que cuenta es lo que puedas DEMOSTRAR. Un aviso en
cada fichero deja constancia de titularidad y de que el código es confidencial
y propietario, y le quita a nadie la excusa de "no sabía que no era libre".

OJO con lo que NO se firma: el repo lleva código de terceros copiado dentro
(shadcn/ui, MIT). Ponerle "propiedad exclusiva de Luiggi Home" a código ajeno
no protege nada y encima es falso, así que va excluido a propósito (ver
EXCLUIDOS y la auditoría de licencias).

Uso:
    python3 herramientas/cabeceras_copyright.py            # las pone
    python3 herramientas/cabeceras_copyright.py --verificar # solo avisa (CI)
"""
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TITULAR = "Luiggi Home"
ANIOS = "2024-2026"
# Marca de agua para reconocer la cabecera y no duplicarla ni al reescribirla.
MARCA = "LUIGGI-COPYRIGHT"

LINEAS = [
    f"© {ANIOS} {TITULAR}. Todos los derechos reservados. [{MARCA}]",
    "Software propietario y confidencial. Ver LICENSE.",
    "Prohibida su copia, distribución, modificación o uso sin autorización",
    "escrita del titular.",
]

# Carpetas que no se tocan nunca.
DIRS_FUERA = {
    ".git", "node_modules", "build", "dist", "__pycache__", ".venv", "venv",
    "site-packages", ".pytest_cache", "coverage", ".next", "out",
}

# Codigo de TERCEROS que vive dentro del repo: no es nuestro y no se firma.
# Si se anade mas codigo ajeno, va aqui Y en la auditoria de licencias.
EXCLUIDOS = (
    "frontend/src/components/ui/",   # shadcn/ui — MIT
    "frontend/src/lib/utils.js",     # helper `cn` de shadcn/ui — MIT
)

# Extension -> como se escribe un comentario en ese lenguaje.
# (inicio_de_bloque, prefijo_de_linea, fin_de_bloque)
COMENTARIO = {
    ".py": (None, "# ", None),
    ".js": ("/*", " * ", " */"),
    ".jsx": ("/*", " * ", " */"),
    ".ts": ("/*", " * ", " */"),
    ".tsx": ("/*", " * ", " */"),
    ".css": ("/*", " * ", " */"),
}

# Solo se firma lo que escribimos nosotros.
CARPETAS = ("backend", "frontend/src", "scripts", "herramientas")


def _es_tercero(rel: str) -> bool:
    return any(rel.startswith(p) or rel == p.rstrip("/") for p in EXCLUIDOS)


def _ficheros():
    for base in CARPETAS:
        raiz_base = os.path.join(RAIZ, base)
        if not os.path.isdir(raiz_base):
            continue
        for carpeta, subdirs, nombres in os.walk(raiz_base):
            subdirs[:] = [d for d in subdirs if d not in DIRS_FUERA]
            for n in sorted(nombres):
                ext = os.path.splitext(n)[1]
                if ext not in COMENTARIO:
                    continue
                ruta = os.path.join(carpeta, n)
                rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")
                if _es_tercero(rel):
                    continue
                yield ruta, rel


def _cabecera(ext: str) -> str:
    ini, pre, fin = COMENTARIO[ext]
    cuerpo = "\n".join(f"{pre}{l}".rstrip() for l in LINEAS)
    if ini:
        return f"{ini}\n{cuerpo}\n{fin}\n"
    return cuerpo + "\n"


def _punto_de_insercion(texto: str, ext: str) -> int:
    """Dónde empieza a poder escribirse la cabecera.

    En Python hay dos cosas que TIENEN que seguir siendo lo primero del
    fichero: el shebang (`#!`) y la declaración de codificación, que Python
    solo reconoce en las dos primeras líneas. Meter la cabecera por encima las
    rompe. El docstring, en cambio, sigue siendo docstring aunque lleve
    comentarios delante: un comentario no es una sentencia.
    """
    if ext != ".py":
        return 0
    pos = 0
    for _ in range(2):
        fin = texto.find("\n", pos)
        if fin == -1:
            break
        linea = texto[pos:fin]
        if linea.startswith("#!") or re.match(r"^#.*coding[:=]", linea):
            pos = fin + 1
            continue
        break
    return pos


def _ya_tiene(texto: str) -> bool:
    # Solo cuenta si está arriba del todo; una mención en mitad del fichero no
    # es una cabecera.
    return MARCA in texto[:1500]


def procesar(verificar: bool):
    puestas, ya, sin_marcar = 0, 0, []
    for ruta, rel in _ficheros():
        ext = os.path.splitext(ruta)[1]
        with open(ruta, encoding="utf-8") as f:
            texto = f.read()
        if _ya_tiene(texto):
            ya += 1
            continue
        if verificar:
            sin_marcar.append(rel)
            continue
        corte = _punto_de_insercion(texto, ext)
        nuevo = texto[:corte] + _cabecera(ext) + texto[corte:]
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(nuevo)
        puestas += 1

    if verificar:
        if sin_marcar:
            print(f"✗ {len(sin_marcar)} fichero(s) SIN aviso de copyright:")
            for r in sin_marcar[:30]:
                print(f"    {r}")
            if len(sin_marcar) > 30:
                print(f"    … y {len(sin_marcar) - 30} más")
            print("\n  Se arregla con: python3 herramientas/cabeceras_copyright.py")
            return 1
        print(f"✓ los {ya} ficheros propios llevan el aviso de copyright")
        return 0

    print(f"✓ aviso puesto en {puestas} fichero(s); {ya} ya lo tenían")
    print(f"  (excluido el código de terceros: {', '.join(EXCLUIDOS)})")
    return 0


def comprobar_sintaxis_python():
    """Un aviso mal puesto rompe el fichero: se comprueba antes de dar por bueno."""
    malos = []
    for ruta, rel in _ficheros():
        if not ruta.endswith(".py"):
            continue
        try:
            import ast
            with open(ruta, encoding="utf-8") as f:
                ast.parse(f.read())
        except SyntaxError as e:
            malos.append(f"{rel}: {e}")
    if malos:
        print("✗ ficheros Python rotos tras poner la cabecera:")
        for m in malos:
            print("   ", m)
        return 1
    return 0


if __name__ == "__main__":
    verificar = "--verificar" in sys.argv
    codigo = procesar(verificar)
    if not verificar and codigo == 0:
        codigo = comprobar_sintaxis_python()
    sys.exit(codigo)
