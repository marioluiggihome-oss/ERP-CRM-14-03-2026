# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LAS CUENTAS EN LAS QUE COBRA LA CASA.

El master, 09/09/2026: «mete este número de cuenta y pon delante JA... en el
resumen de totales JA CAJA RURAL, las otras dos pon PBL».

POR QUÉ ESTO LLEVA CANDADO Y NO ES UNA LISTA MÁS. Un IBAN aquí no es un dato de
pantalla: se imprime en el presupuesto que se le entrega al cliente y es por
donde hace la transferencia. Una cifra mal copiada no da ningún error en ningún
sitio — el dinero simplemente no llega, o llega a otro. Y no se descubre al
programar: se descubre semanas después, buscando un cobro.

EL IBAN SE COMPRUEBA SOLO, y por eso se comprueba aquí: los dos dígitos que van
detrás de «ES» son un `mod 97` de todo lo demás, inventado exactamente para
cazar un número mal tecleado o dos cifras cambiadas de sitio. Si alguien toca un
dígito, esta prueba se pone roja.

Y LA ENTIDAD TIENE QUE CUADRAR CON EL NOMBRE. Las cuatro cifras que siguen al
control son el código del banco: 0049 Santander, 0182 BBVA, 3016 Caja Rural. Un
IBAN válido pero pegado en la cuenta que no es sería igual de malo, y el dígito
de control no lo vería: sería un número perfectamente correcto de otro banco.

EL PREFIJO DICE DE QUIÉN ES. Va DELANTE porque es lo primero que se lee en el
desplegable, y es lo que evita elegir la cuenta de la otra sociedad. **PBL es
PUBLIOFERTA S.L. y JA es Estudio de Cocina José Ángel** — son dos titulares
distintos, y por eso el titular de una no puede copiarse de la otra por estar
justo encima en la lista.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESUMEN = os.path.join(RAIZ, "frontend", "src", "components", "ResumenCocinas.jsx")


def _cuentas():
    """Las cuentas TAL CUAL están escritas en la pantalla."""
    with open(RESUMEN, "r", encoding="utf-8") as f:
        src = f.read()
    i = src.index("const BANCOS = [")
    bloque = src[i:src.index("];", i)]
    fuera = []
    for linea in bloque.split("\n"):
        if "iban:" not in linea:
            continue
        campos = dict(re.findall(r"(\w+): '([^']*)'", linea))
        fuera.append(campos)
    return fuera


def _iban_valido(iban):
    """El `mod 97` del propio IBAN: lo que existe para cazar una cifra mal
    copiada o dos cambiadas de sitio."""
    s = iban.replace(" ", "").upper()
    if not re.fullmatch(r"ES\d{22}", s):
        return False
    reordenado = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in reordenado)) % 97 == 1


# Lo que el master ha dicho que hay, con su entidad. La entidad se escribe aquí
# a mano a propósito: es la comprobación de que el IBAN está en la cuenta que le
# toca, y un IBAN válido del banco equivocado el dígito de control no lo caza.
ESPERADAS = {
    "santander": ("PBL Banco Santander", "0049", "PUBLIOFERTA S.L."),
    "bbva": ("PBL BBVA", "0182", "PUBLIOFERTA S.L."),
    "cajarural": ("JA CAJA RURAL", "3016", "Estudio de Cocina José Ángel"),
}


def test_ESTAN_LAS_TRES_CUENTAS():
    ids = {c["id"] for c in _cuentas()}
    assert ids == set(ESPERADAS), (
        f"las cuentas del presupuesto han cambiado: {sorted(ids)}. Si es a "
        "propósito, dilo aquí — esto se imprime en el papel con el que paga el "
        "cliente")


def test_TODOS_LOS_IBAN_PASAN_SU_DIGITO_DE_CONTROL():
    """Una cifra mal copiada no da ningún error en ninguna parte: el dinero
    simplemente no llega."""
    malos = [(c["id"], c["iban"]) for c in _cuentas() if not _iban_valido(c["iban"])]
    assert not malos, (
        f"estos IBAN no cuadran con su propio dígito de control, o sea que hay "
        f"al menos una cifra mal: {malos}")


def test_EL_IBAN_ES_DEL_BANCO_QUE_DICE_SER():
    """Un IBAN válido pegado en la cuenta que no es sería igual de malo, y el
    dígito de control no lo vería: es un número correcto de otro banco."""
    for c in _cuentas():
        nombre, entidad, _ = ESPERADAS[c["id"]]
        real = c["iban"].replace(" ", "")[4:8]
        assert real == entidad, (
            f"«{c['id']}» dice ser {nombre} y su IBAN es de la entidad {real}, "
            f"no de la {entidad}")


def test_EL_PREFIJO_DICE_DE_QUIEN_ES_LA_CUENTA():
    """Va delante porque es lo primero que se lee en el desplegable, y es lo que
    evita elegir la de la otra sociedad."""
    for c in _cuentas():
        nombre, _, _ = ESPERADAS[c["id"]]
        assert c["nombre"] == nombre, (
            f"«{c['id']}» se llama «{c['nombre']}» y tiene que llamarse «{nombre}»")
    assert all(c["nombre"].split()[0] in ("PBL", "JA") for c in _cuentas()), (
        "alguna cuenta ha perdido el prefijo que dice de quién es")


def test_EL_NUMERO_QUE_DIO_EL_MASTER_ESTA_TAL_CUAL():
    """El de Caja Rural, dígito a dígito."""
    ja = [c for c in _cuentas() if c["id"] == "cajarural"][0]
    assert ja["iban"] == "ES26 3016 0618 6122 3373 2128"


def test_SIN_TITULAR_NO_SE_IMPRIME_UN_TITULAR_VACIO():
    """El master dio el número y el nombre de la cuenta, no la razón social.
    Poner una inventada es meterle al cliente un dato falso en el documento con
    el que hace la transferencia (regla 7); dejar «Titular:» en blanco es un
    presupuesto con pinta de roto. Ninguna de las dos: no se escribe."""
    with open(RESUMEN, "r", encoding="utf-8") as f:
        src = f.read()
    assert "banco.titular ? `${banco.nombre} — Titular: ${banco.titular}`" in src, (
        "el PDF vuelve a escribir «Titular:» aunque no se sepa quién es")
    assert "b.titular ? `${b.titular} · ` : ''" in src, (
        "la pantalla vuelve a pintar un titular vacío")


def test_CADA_CUENTA_VA_A_NOMBRE_DE_QUIEN_ES():
    """El titular se imprime en el presupuesto, debajo del nombre del banco, y
    es lo que el cliente ve al hacer la transferencia. Las PBL son de
    PUBLIOFERTA; la JA es de José Ángel (master, 09/09/2026)."""
    for c in _cuentas():
        _, _, titular = ESPERADAS[c["id"]]
        assert c["titular"] == titular, (
            f"«{c['nombre']}» sale a nombre de «{c['titular']}» y es de "
            f"«{titular}»")


def test_LA_CUENTA_DE_JA_NO_SE_PONE_A_NOMBRE_DE_PUBLIOFERTA():
    """El prefijo es lo que distingue a las dos sociedades: PBL es PUBLIOFERTA y
    JA es otra. Rellenar el titular de la de Caja Rural copiando el de las otras
    dos —que es lo cómodo, porque están justo encima— pondría en el papel del
    cliente una razón social que no es la dueña de esa cuenta.

    Se comprueba lo que SÍ se sabe: que no es PUBLIOFERTA. El día que el master
    diga de quién es, se escribe y esta prueba lo sigue permitiendo — lo único
    que no permite es heredarlo de la cuenta de al lado.
    """
    ja = [c for c in _cuentas() if c["id"] == "cajarural"][0]
    otras = {c["titular"] for c in _cuentas() if c["id"] != "cajarural"}
    assert ja["titular"] not in otras or not ja["titular"], (
        f"la cuenta «{ja['nombre']}» ha salido a nombre de «{ja['titular']}», que "
        "es el titular de las cuentas PBL. El prefijo dice que son sociedades "
        "distintas: si de verdad es esa, quítale el prefijo JA")


def test_NINGUNA_CUENTA_SE_QUEDA_SIN_IBAN():
    """Una cuenta en el desplegable sin número es un presupuesto que se manda
    sin decir dónde pagar."""
    for c in _cuentas():
        assert c.get("iban"), f"«{c['id']}» no tiene IBAN"
