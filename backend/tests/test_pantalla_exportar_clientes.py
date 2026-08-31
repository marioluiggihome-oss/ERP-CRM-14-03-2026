# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL LISTADO DE CLIENTES, PARA ABRIRLO EN EXCEL.

El master, 31/08: «pásame un listado de todos estos clientes en Excel». La lista
de «Clientes importados» solo se podía MIRAR: para llevársela había que copiarla
a mano de la pantalla.

LAS TRES COSAS QUE HACEN QUE UN CSV SE ABRA BIEN EN UN EXCEL ESPAÑOL, y que si
faltan convierten «exportar a Excel» en un fichero que hay que arreglar a mano:

1. EL SEPARADOR ES `;`, NO `,`. En un Excel en español el separador de lista es
   el punto y coma. Con comas —que es lo que hacen las demás exportaciones de
   este repo— el fichero se abre con TODO metido en la primera columna. La
   primera línea `sep=;` es lo que lee Excel para no preguntar.

2. EL BOM. Sin `\\uFEFF`, Excel no reconoce el UTF-8 y «Enríquez» sale
   «EnrÃ­quez». Un listado de clientes con los apellidos rotos no se puede usar.

3. TODAS LAS CELDAS ENTRECOMILLADAS, no solo «las que tengan una coma». En una
   dirección hay puntos y comas y en unas notas hay saltos de línea: UNA sola
   celda sin escapar desplaza el resto de la fila una columna, y a partir de ahí
   el teléfono de un cliente aparece en la casilla del CIF de otro. No da ningún
   error: da un listado que parece bien y no lo está.

Y el nombre de un cliente puede llevar comillas dobles (un alias, un «S.L.
"Los Robles"»). En CSV una comilla dentro de una celda se escribe DOBLE; si no,
cierra la celda antes de tiempo y parte la fila.
"""
import json
import os
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadLineas.jsx")


def _lee():
    with open(JSX, "r", encoding="utf-8") as f:
        return f.read()


def test_LA_LISTA_DE_CLIENTES_SE_PUEDE_EXPORTAR():
    """Que exista la función Y el botón que la llama: una exportación sin botón
    no existe, que es el fallo que ya tuvo el modal de descuentos."""
    cuerpo = sin_comentarios(_lee())
    assert "exportarClientesExcel" in cuerpo, "no hay forma de exportar los clientes"
    assert 'data-testid="clientes-exportar-excel"' in cuerpo, (
        "la exportación no tiene botón: está escrita y no se puede llamar")
    i = cuerpo.index('data-testid="clientes-exportar-excel"')
    boton = cuerpo[cuerpo.rindex("<button", 0, i):i]
    assert "onClick={exportarClientesExcel}" in boton, (
        "el botón de exportar no llama a la exportación")


def test_NO_SE_DESCARGA_UN_FICHERO_VACIO():
    """Con la lista vacía el botón no puede dar un CSV con solo cabeceras: quien
    lo abra creerá que no tiene clientes."""
    cuerpo = sin_comentarios(_lee())
    i = cuerpo.index("const exportarClientesExcel")
    cuerpo_fn = cuerpo[i:i + 700]
    assert "if (!filas.length) return;" in cuerpo_fn, (
        "se exporta aunque no haya ni un cliente")
    j = cuerpo.index('data-testid="clientes-exportar-excel"')
    boton = cuerpo[cuerpo.rindex("<button", 0, j):j]
    assert "disabled=" in boton, "el botón se puede pulsar con la lista vacía"


# ── EJECUTANDO LA FUNCIÓN DE VERDAD ──────────────────────────────────────────
#
# El escapado de un CSV no se comprueba mirando si la palabra «replace» está en
# el fichero: se comprueba metiéndole un cliente con un punto y coma en la
# dirección y viendo cuántas columnas salen.

def _exporta(clientes):
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar la exportación de verdad")
    cuerpo = _lee()
    i = cuerpo.index("const exportarClientesExcel")
    fin = cuerpo.index("\n  };", i) + len("\n  };")
    fuente = cuerpo[i:fin]
    # Se sustituye solo la descarga (no hay navegador aquí); el armado del
    # contenido —que es lo que se vigila— se ejecuta tal cual está escrito.
    corte = fuente.index("const blob = new Blob")
    fuente = fuente[:corte] + "return contenido;\n  };"
    js = """
const clients = %s;
%s
console.log(JSON.stringify(exportarClientesExcel() || ''));
""" % (json.dumps(clientes), fuente.replace("const exportarClientesExcel", "var exportarClientesExcel"))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"la exportación no se ejecuta: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_EXCEL_ESPAÑOL_lo_abre_en_COLUMNAS():
    csv = _exporta([{"codigo": "49237", "nombre": "GORKA ENRIQUEZ"}])
    assert csv.startswith("sep=;"), (
        "falta la línea `sep=;`: un Excel español abriría el fichero con todo "
        "metido en la primera columna")
    cabecera = csv.split("\r\n")[1]
    assert cabecera.count(";") >= 8 and "," not in cabecera.replace('"', ""), (
        f"las columnas no van separadas por punto y coma: {cabecera[:80]}")


def test_LOS_ACENTOS_NO_SE_ROMPEN():
    cuerpo = sin_comentarios(_lee())
    i = cuerpo.index("const exportarClientesExcel")
    assert "\\uFEFF" in cuerpo[i:i + 2600], (
        "falta el BOM: Excel no reconocerá el UTF-8 y «Enríquez» saldrá "
        "«EnrÃ­quez» en todo el listado")


def test_UN_PUNTO_Y_COMA_EN_UNA_DIRECCION_NO_PARTE_LA_FILA():
    """El caso que rompe un listado sin que nadie vea un error: a partir de la
    celda mal escapada, cada dato aparece en la casilla del siguiente."""
    csv = _exporta([
        {"codigo": "49237", "nombre": "GORKA ENRIQUEZ",
         "direccion": "C/ Mayor 3; 2º B", "localidad": "Bilbao"},
    ])
    fila = csv.split("\r\n")[2]
    # Se cuentan los separadores DE VERDAD: los que caen fuera de las comillas.
    fuera, dentro = 0, False
    for ch in fila:
        if ch == '"':
            dentro = not dentro
        elif ch == ";" and not dentro:
            fuera += 1
    cabecera = csv.split("\r\n")[1]
    esperados = sum(1 for k, ch in enumerate(cabecera) if ch == ";")
    assert fuera == esperados, (
        f"la fila tiene {fuera} separadores y la cabecera {esperados}: el punto "
        "y coma de la dirección ha partido la fila y los datos se han corrido "
        "de columna")
    assert "C/ Mayor 3; 2º B" in csv


def test_UNA_COMILLA_EN_EL_NOMBRE_NO_PARTE_LA_CELDA():
    csv = _exporta([{"codigo": "1", "nombre": 'MUEBLES "LOS ROBLES" SL'}])
    assert 'MUEBLES ""LOS ROBLES"" SL' in csv, (
        "una comilla dentro del nombre no se está doblando: cierra la celda "
        "antes de tiempo y parte la fila")


def test_UN_CLIENTE_SIN_DATOS_SALE_VACIO_Y_NO_ROMPE():
    """La ficha de un cliente viejo puede no tener ni teléfono ni CIF. Eso es
    una celda vacía, no un `undefined` escrito en el listado."""
    csv = _exporta([{"nombre": "SIN DATOS"}])
    assert "undefined" not in csv and "null" not in csv, (
        f"se están escribiendo `undefined`/`null` en el listado: {csv[:160]}")


def test_SALEN_LAS_COLUMNAS_QUE_SIRVEN_PARA_TRABAJAR():
    csv = _exporta([{"codigo": "49237", "nombre": "GORKA ENRIQUEZ"}])
    cabecera = csv.split("\r\n")[1]
    for col in ("Código", "Nombre", "CIF / NIF", "Email", "Teléfono",
                "Localidad", "Provincia"):
        assert col in cabecera, f"falta la columna «{col}» en el listado"


def test_SE_LEEN_LOS_DOS_JUEGOS_DE_NOMBRES_DE_CAMPO():
    """La colección guarda los campos en ESPAÑOL (`codigo`, `nombre`, `cif`,
    `localidad`) porque así los normaliza `POST /clients`, pero el modelo
    Pydantic los declara en inglés y por ahí han entrado fichas con `code` y
    `name`. Leer solo uno de los dos dejaría media lista en blanco."""
    es = _exporta([{"codigo": "1", "nombre": "EN ESPAÑOL", "cif": "B111"}])
    en = _exporta([{"code": "2", "name": "IN ENGLISH", "taxId": "B222"}])
    assert "EN ESPAÑOL" in es and "B111" in es
    assert "IN ENGLISH" in en and "B222" in en, (
        "una ficha guardada con los nombres en inglés sale vacía en el listado")
