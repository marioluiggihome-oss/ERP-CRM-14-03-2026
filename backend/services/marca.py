# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL NOMBRE COMERCIAL DEL ERP. UNO SOLO, Y VACÍO POR DEFECTO.

El master, 25/08/2026: «revisa todos los PDFs y quita el texto de Luiggi Home
por todos los lados, y en el ERP también». El ERP se licencia a terceros, y un
cliente no puede encontrarse la marca de otro impresa en su presupuesto.

EL AJUSTE YA EXISTÍA. `SettingsModel` tiene `companyName`, `logo` y hasta un
`marcaBlanca`. Lo que fallaba era otra cosa:

  · Los PDFs no lo usaban: escribían «LUIGGI HOME» a mano en la cabecera y en
    el pie.
  · Y donde sí lo usaban, el valor por defecto volvía a meter la marca:
    `settings.get("companyName", "LUIGGI HOME")`. Un ajuste cuyo defecto es la
    marca no despersonaliza nada — solo tapa el problema hasta que alguien
    deja el campo vacío.

POR ESO EL DEFECTO DE AQUÍ ES CADENA VACÍA. Si nadie ha configurado una marca,
no se imprime ninguna. Un documento sin membrete es correcto; un documento con
el membrete de otra empresa, no.

Se puede fijar por entorno (`MARCA_COMERCIAL`) para un despliegue entero, o por
ajustes para cada instalación. Manda el ajuste, porque es el que puede tocar el
cliente sin volver a desplegar.
"""
from __future__ import annotations

import os
from typing import Optional

# Nunca una marca. Ver la nota de arriba.
POR_DEFECTO = ""


def nombre_comercial(settings: Optional[dict] = None) -> str:
    """La marca a imprimir, o cadena vacía si no hay ninguna configurada."""
    if settings:
        v = (settings.get("companyName") or "").strip()
        if v:
            return v
    return (os.environ.get("MARCA_COMERCIAL") or POR_DEFECTO).strip()


def con_marca(texto: str, settings: Optional[dict] = None,
              separador: str = " · ") -> str:
    """«CATÁLOGO TÉCNICO» + marca -> «CATÁLOGO TÉCNICO · ACME».

    Sin marca devuelve el texto tal cual, SIN el separador colgando. Ese detalle
    es la mitad del trabajo: concatenar a pelo deja pies de página como
    «Documento generado el 25/08/2025 - » con el guion al aire, y eso en un
    presupuesto que ve un cliente canta más que la propia marca.
    """
    m = nombre_comercial(settings)
    if not m:
        return texto
    if not texto:
        return m
    return f"{texto}{separador}{m}"
