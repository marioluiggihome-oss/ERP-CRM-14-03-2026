# -*- coding: utf-8 -*-
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""LA PUBLIOFERTA DE ELECTROSTOCK → `backend/data/electrostock_publioferta.json`.

El master, 07/09/2026: «vuelca estas ofertas a la sección electros y mete una
línea en presupuestador de cocina montada... un artículo para que metiendo el
modelo meta el precio, descripción y precio».

QUÉ ES ESTE PAPEL, Y POR QUÉ IMPORTA LEERLO BIEN
────────────────────────────────────────────────
Es una TARIFA DE CESIÓN: lo que Electrostock le cobra a la casa, no lo que la
casa le cobra al cliente. Su propio pie lo dice:

    «IVA y Transporte no incluido. Precios válidos para el mes de Tarifa o fin
     de existencias» · «Portes de envío a consultar»

O sea que la cifra de la columna «€ CESIÓN» es COSTE, y coste INCOMPLETO —
faltan portes—. Tres consecuencias que van escritas en el JSON para que nadie
tenga que acordarse:

  1. Es dinero del proveedor, así que se trata como la tarifa MV: el catálogo
     (modelo, descripción, marca) es de todos; la CESIÓN es del master
     (CLAUDE.md, regla 8b).
  2. NO es un PVP. Vender a precio de cesión es vender a coste. El PVP lo pone
     el master al volcarlo a Electros, y queda escrito de dónde sale
     (`pvpOrigen`), para que nadie lo confunda con un precio que venga en el
     papel.
  3. CADUCA. Es la oferta de un mes concreto («1 de Septiembre de 2026») y
     además se acaba con las existencias. Un presupuesto sacado en diciembre
     con la tarifa de septiembre es dinero perdido sin ningún error por medio,
     así que la vigencia viaja con cada artículo y la pantalla la enseña.

POR QUÉ SE GENERA Y NO SE TECLEA
────────────────────────────────
Son 169 artículos con su precio. Copiados a mano, una cifra mal tecleada da un
presupuesto plausible y equivocado. Aquí se LEE EL PDF, que además queda
guardado en el repo (`backend/data/Electrostock_PubliOferta_2026-09-01.pdf`),
así que el candado puede regenerar y comparar byte a byte: si alguien edita el
JSON a mano, el CI se pone rojo. Es la misma regla que las tarifas de ACB.

CÓMO SE LEE LA TABLA, Y DÓNDE ESTÁ LA TRAMPA
────────────────────────────────────────────
El PDF tiene cuatro columnas —MODELO · CARACTERÍSTICAS · MARCA · € CESIÓN— y
`extraction_mode='layout'` las respeta con espacios. Pero hay una quinta cosa
sin columna propia: el RECLAMO comercial («OFERTA», «OPORTUNIDAD», «ÚLTIMAS
UDS»…), que unas veces cae pegado al final de las características y otras
suelto entre columnas.

Eso rompe lo que parece natural —partir por el primer hueco ancho—, porque las
descripciones llevan huecos anchos dentro («20 litros 800 W,   grill 1000W»):
con esa lectura, media descripción se iba al campo de la marca. Se lee AL
REVÉS, desde el precio hacia atrás: la marca es el último bloque antes del
importe, y se comprueba contra una lista CERRADA de 16 marcas. Una marca que no
esté en la lista no se adivina: se para el generador.

El reclamo se separa de la descripción a propósito. Pegado, la descripción del
artículo diría «Placa 3EB715LR 3 Fuegos grande doble biselada OFERTA», y eso es
lo que acabaría impreso en el presupuesto de un cliente.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(RAIZ, "backend", "data",
                   "Electrostock_PubliOferta_2026-09-01.pdf")
SALIDA = os.path.join(RAIZ, "backend", "data", "electrostock_publioferta.json")

# La cabecera del papel, transcrita tal cual. La VIGENCIA es lo que hace que un
# presupuesto de dentro de tres meses no se saque con estos precios.
PROVEEDOR = "ELECTROSTOCK"
TARIFA = "PubliOferta"
FECHA = "2026-09-01"
VIGENCIA = "2026-09"          # «válidos para el mes de Tarifa»
PIE = ("IVA y Transporte no incluido. Precios válidos para el mes de Tarifa o "
       "fin de existencias. Portes de envío a consultar.")

# LISTA CERRADA. No sale de leer el PDF —eso sería darse la razón a uno mismo—:
# se escribe aquí y se comprueba. Si Electrostock mete una marca nueva, el
# generador PARA y alguien la mira, en vez de colar en el catálogo un trozo de
# descripción convertido en marca.
MARCAS = frozenset({
    "AEG", "ARTICA", "BALAY", "BOSCH", "CANDY", "CATA", "EDESA", "ELECTROLUX",
    "FRANKE", "GORENJE", "JOHNSON", "MEPAMSA", "NOVAMIX", "OKA", "SIEMENS",
    "TEKA",
})

# Los reclamos comerciales del papel. No son características del aparato: son
# el gancho de la oferta, y no pueden acabar impresos en el presupuesto de un
# cliente como si describieran el producto.
RECLAMOS = re.compile(
    r"(?:[\s(]*\b(?:MUY\s+INTERESANTE|INTERESANTE|OPORTUNIDAD|OFERTA|"
    r"[ÚU]LTIMAS\s+UDS|POCAS\s+UDS|NOVEDAD)\b\)?)+\s*$")

# Se lee desde la derecha: precio, marca, y lo que quede por delante es la
# descripción. Ver el docstring: partir por la izquierda parte las
# descripciones que llevan huecos anchos dentro.
LINEA = re.compile(
    r"^\s*(?P<modelo>\S.*?)\s{2,}(?P<resto>.*)\s{2,}"
    r"(?P<marca>[A-ZÑÁÉÍÓÚ]+)\s{2,}(?P<eur>[\d.]+,\d{2})\s*€\s*$")

# Lo que no es ni artículo ni epígrafe: cabecera de columnas y pie de página.
IGNORAR = ("MODELO", "TARIFA CESIÓN", "IVA Y TRANSPORTE", "PORTES DE ENVÍO")

# Cuántos tiene el papel. Es un CANARIO: si el PDF cambia y salen 150 o 200, el
# generador para en vez de emitir medio catálogo con la misma pinta de bueno.
N_ARTICULOS = 169
N_EPIGRAFES = 28


def _normalizar(modelo: str) -> str:
    """La clave con la que se busca un modelo tecleado.

    En el papel conviven «TD 3002 BK», «EFT-1711 WH» y «3EB715LR»: quien lo
    teclea no va a poner los espacios ni los guiones en el mismo sitio que
    Electrostock. Se comparan sin ellos y en mayúsculas, que es lo único que no
    depende de cómo lo escriba cada uno.
    """
    return re.sub(r"[^A-Z0-9]", "", (modelo or "").upper())


def leer_pdf(ruta: str = PDF) -> list:
    from pypdf import PdfReader                      # pypdf, nunca fitz (AGPL)

    epigrafe = None
    articulos = []
    for pagina in PdfReader(ruta).pages:
        for linea in pagina.extract_text(extraction_mode="layout").split("\n"):
            if not linea.strip():
                continue
            m = LINEA.match(linea)
            if not m or m.group("marca") not in MARCAS:
                texto = " ".join(linea.split())
                if any(texto.upper().startswith(x) for x in IGNORAR):
                    continue
                # Un epígrafe va en MAYÚSCULAS y no lleva precio. Lo demás es
                # pie de página y no arrastra artículos.
                if texto == texto.upper() and len(texto) > 3 and "€" not in texto:
                    epigrafe = texto
                continue
            descripcion = " ".join(m.group("resto").split())
            reclamo = ""
            corte = RECLAMOS.search(descripcion)
            if corte:
                reclamo = corte.group(0).strip()
                descripcion = descripcion[:corte.start()].strip()
            articulos.append({
                "modelo": " ".join(m.group("modelo").split()),
                "modeloNorm": _normalizar(m.group("modelo")),
                "descripcion": descripcion,
                "marca": m.group("marca"),
                "categoria": epigrafe or "",
                "reclamo": reclamo,
                # € CESIÓN: lo que le cuesta a la casa, SIN IVA y SIN portes.
                "cesion": float(m.group("eur").replace(".", "").replace(",", ".")),
            })
    return articulos


def validar(articulos: list) -> None:
    """Se comprueba ANTES de emitir. Un catálogo a medias no se nota mirándolo:
    tiene la misma pinta que uno entero."""
    fallos = []
    if len(articulos) != N_ARTICULOS:
        fallos.append(f"salen {len(articulos)} artículos y el papel tiene {N_ARTICULOS}")
    epigrafes = {a["categoria"] for a in articulos}
    if len(epigrafes) != N_EPIGRAFES:
        fallos.append(f"salen {len(epigrafes)} epígrafes y el papel tiene {N_EPIGRAFES}")
    vistos = {}
    for a in articulos:
        etq = a["modelo"]
        if not a["modeloNorm"]:
            fallos.append(f"«{etq}»: modelo vacío")
        if a["modeloNorm"] in vistos:
            fallos.append(f"«{etq}»: modelo repetido")
        vistos[a["modeloNorm"]] = True
        if not a["descripcion"]:
            fallos.append(f"«{etq}»: sin descripción")
        if not a["categoria"]:
            fallos.append(f"«{etq}»: sin epígrafe (¿se perdió una cabecera?)")
        if a["marca"] not in MARCAS:
            fallos.append(f"«{etq}»: marca «{a['marca']}» desconocida")
        # Un electrodoméstico de 0 € o de 20.000 € es una cifra mal leída, no
        # una oferta. El más barato del papel es un sifón de 26 € y el más caro
        # una campana de isla de 2.198 €.
        if not (10.0 <= a["cesion"] <= 5000.0):
            fallos.append(f"«{etq}»: cesión de {a['cesion']} € fuera de rango")
        # El reclamo NO puede quedarse dentro de la descripción: es lo que se
        # imprimiría en el presupuesto del cliente.
        if RECLAMOS.search(a["descripcion"]):
            fallos.append(f"«{etq}»: la descripción acaba en un reclamo comercial")
    if fallos:
        raise SystemExit("TARIFA ELECTROSTOCK NO VÁLIDA:\n  - " + "\n  - ".join(fallos))


def generar(salida: str = SALIDA) -> dict:
    articulos = leer_pdf()
    validar(articulos)
    doc = {
        "_aviso": ("GENERADO por herramientas/tarifa_electrostock.py desde el PDF "
                   "del proveedor. No editar a mano: hay un candado que lo "
                   "regenera y compara."),
        "proveedor": PROVEEDOR,
        "tarifa": TARIFA,
        "fecha": FECHA,
        "vigencia": VIGENCIA,
        "ivaIncluido": False,
        "transporteIncluido": False,
        "pie": PIE,
        "articulos": articulos,
    }
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")
    return doc


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else SALIDA
    d = generar(destino)
    print(f"{len(d['articulos'])} artículos · "
          f"{len({a['categoria'] for a in d['articulos']})} epígrafes · "
          f"{len({a['marca'] for a in d['articulos']})} marcas → {destino}")
