# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de los candados: QUE SE PUEDAN ABRIR EN UNA TABLET.

EL FALLO
--------
El coste y el margen viven detras de un candado que se abria con Shift+clic. La
idea es buena: no se abre por un roce, y no se abre delante de un cliente sin
querer. Pero tiene un agujero que desde un ordenador no se ve:

    UNA TABLET NO TIENE TECLA SHIFT.

Asi que en tablet y en movil el margen no estaba protegido: estaba INALCANZABLE.
El boton se veia, se podia tocar y no pasaba nada — que es la peor forma de
esconder algo, porque parece que esta roto. Y el master trabaja en tablet.

Eran tres sitios, no uno: la relacion de muebles, el panel de Rentabilidad MV y
el candado de Cocina Desmontada que abre ese panel.

LO QUE SE PROTEGE
-----------------
1. NINGUN CANDADO SE ABRE SOLO CON SHIFT. Si aparece uno nuevo que solo mira
   `shiftKey`, esta prueba se pone roja: en tablet no serviria.

2. EL GESTO ES UNO SOLO Y ESTA ESCRITO EN UN SITIO. Tres formas distintas de
   abrir el mismo candado en tres pantallas es peor que ninguna.

3. LA PULSACION LARGA NO SE COME EL CLIC DE DESPUES. Al soltar el dedo el
   navegador manda TAMBIEN un clic: sin `consumir()`, la pulsacion abre el
   candado y el clic lo cierra en el mismo gesto — un parpadeo y nada mas.

4. SIGUE SIENDO UN GESTO DELIBERADO. Mantener pulsado no pasa por accidente. Si
   alguien lo baja a un toque suelto, el coste se enseniaria solo.
"""
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
HOOK = os.path.join(SRC, "utils", "pulsacionLarga.js")

# Los tres sitios donde hay un candado de dinero. Escritos a mano: aniadir uno
# nuevo tiene que ser una decision, no un descuido.
CON_CANDADO = {
    "components/RelacionReview.jsx": "coste y margen de la relacion de muebles",
    "components/RentabilidadMV.jsx": "coste y margen de la tarifa MV",
    "components/Cascos.jsx": "abre el panel de Rentabilidad",
}

# Los que se quedan SOLO con Shift, y por que. Escribirlo aqui es la unica forma
# de distinguir una decision de un olvido.
SOLO_CON_SHIFT_A_PROPOSITO = {
    "components/settings/BackupManagementTab.jsx": (
        "RESTAURAR una copia sobrescribe la base entera: es la accion mas "
        "destructiva del ERP. Aqui exigir un TECLADO no es un fallo de "
        "accesibilidad, es la guarda — y bajarla a mantener pulsado en una "
        "tablet la haria mas facil, no mas segura. Esto no esconde dinero: "
        "impide un desastre. Si algun dia hace falta restaurar desde tablet, "
        "la guarda buena es escribir el nombre de la copia a mano, no un gesto."
    ),
}


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ─── 1. Ningun candado se abre solo con Shift ───────────────────────────────

@pytest.mark.parametrize("fichero", sorted(CON_CANDADO))
def test_el_candado_se_puede_abrir_sin_teclado(fichero):
    """CANDADO PRINCIPAL. Con Shift a secas, en tablet no hay forma de entrar."""
    src = _leer(os.path.join(SRC, fichero))
    assert "shiftKey" in src, f"{fichero} ya no es un candado; quita el fichero de la lista"
    assert "usePulsacionLarga" in src, (
        f"{fichero} vuelve a abrirse solo con Shift+clic. En una tablet no hay "
        "tecla Shift: el margen no quedaria protegido, quedaria inalcanzable.")


def test_no_aparece_ningun_candado_nuevo_solo_con_shift():
    """Barre TODAS las pantallas, no solo las tres conocidas."""
    malos = []
    for raiz, _, ficheros in os.walk(os.path.join(SRC, "components")):
        for f in ficheros:
            if not f.endswith(".jsx"):
                continue
            ruta = os.path.join(raiz, f)
            src = _leer(ruta)
            if "shiftKey" not in src:
                continue
            rel = os.path.relpath(ruta, SRC).replace(os.sep, "/")
            if rel in SOLO_CON_SHIFT_A_PROPOSITO:
                continue
            # Shift dentro de un atajo de teclado (Ctrl+Shift+Z) no es un
            # candado: ahi el teclado existe por definicion.
            solo_atajos = re.search(r"(ctrlKey|metaKey)[^\n]*shiftKey|shiftKey[^\n]*(ctrlKey|metaKey)", src)
            if solo_atajos and "usePulsacionLarga" not in src:
                continue
            if "usePulsacionLarga" not in src:
                malos.append(rel)
    assert not malos, (
        "estas pantallas esconden algo detras de Shift+clic y no ofrecen otra "
        "forma de abrirlo: " + ", ".join(malos)
        + ". En tablet no se puede abrir. Usa `usePulsacionLarga`.")


# ─── 2. El gesto esta escrito en un solo sitio ──────────────────────────────

def test_el_gesto_vive_en_un_unico_fichero():
    assert os.path.exists(HOOK), (
        "falta utils/pulsacionLarga.js: sin el, cada pantalla se inventaria su "
        "propia forma de abrir el candado")
    src = _leer(HOOK)
    assert "onPointerDown" in src and "onPointerUp" in src, (
        "el gesto tiene que funcionar con dedo y con raton: eventos de puntero")


def test_el_texto_de_ayuda_tambien_es_uno_solo():
    """Tres explicaciones distintas del mismo gesto acaban contradiciendose."""
    src = _leer(HOOK)
    assert "AYUDA_CANDADO" in src
    for fichero in CON_CANDADO:
        assert "AYUDA_CANDADO" in _leer(os.path.join(SRC, fichero)), (
            f"{fichero} explica el gesto con sus propias palabras en vez de usar "
            "el texto comun: el dia que cambie el gesto, ahi seguira el viejo")


# ─── 3. La pulsacion larga no se come el clic de despues ────────────────────

@pytest.mark.parametrize("fichero", sorted(CON_CANDADO))
def test_el_clic_del_final_no_deshace_la_pulsacion(fichero):
    """CANDADO. Al soltar el dedo llega un clic ademas de la pulsacion. Sin
    `consumir()`, un gesto abre y cierra: se ve un parpadeo y nada mas."""
    src = _leer(os.path.join(SRC, fichero))
    assert ".consumir()" in src, (
        f"{fichero} no descarta el clic que el navegador manda al soltar: la "
        "pulsacion larga abriria el candado y ese clic lo cerraria al instante")


# ─── 4. Sigue siendo un gesto deliberado ────────────────────────────────────

def test_mantener_pulsado_no_es_un_toque_suelto():
    """Si el tiempo baja demasiado, el candado se abre con un toque normal — y
    entonces el coste se ensenia solo, que es justo lo que no puede pasar."""
    src = _leer(HOOK)
    m = re.search(r"MS_PULSACION_LARGA\s*=\s*(\d+)", src)
    assert m, "no se encuentra el tiempo de la pulsacion larga"
    ms = int(m.group(1))
    assert ms >= 400, (
        f"{ms} ms es un toque normal: el candado se abriria sin querer, delante "
        "de quien sea")
    assert ms <= 1200, (
        f"{ms} ms es tanto que nadie lo descubre y el margen sigue sin poder verse")


def test_las_excepciones_estan_razonadas():
    """Un candado que se queda sin salida en tablet y sin motivo escrito al lado
    es indistinguible de un descuido, y a los seis meses nadie lo toca."""
    for fichero, motivo in SOLO_CON_SHIFT_A_PROPOSITO.items():
        assert os.path.exists(os.path.join(SRC, fichero)), f"{fichero} ya no existe"
        assert len(motivo.strip()) > 80, (
            f"{fichero} esta fuera del barrido con una excusa de una linea: "
            "escribe POR QUE exigir teclado es aqui la guarda buena")


def test_el_gesto_no_saca_el_menu_de_copiar_del_movil():
    """Mantener pulsado en una pantalla tactil selecciona texto y saca el menu
    del sistema. Con eso encima, el candado no se ve abrirse."""
    src = _leer(HOOK)
    assert "onContextMenu" in src and "userSelect" in src
