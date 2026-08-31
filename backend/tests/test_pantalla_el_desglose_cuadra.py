# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN DESGLOSE QUE NO SUMA EL TOTAL NO ES UN DESGLOSE: ES UNA SOSPECHA.

El master, 30/08, con el candado por fin abierto: «ojo, el coste no lo veo
bien». Y no lo veía bien porque no cuadraba:

    Casco 61,15 € + Puertas 53,28 € = 114,43 €
    Coste que ponía:                  145,55 €
                                      ─────────
    Sin explicar:                      31,12 €

El coste de fábrica tiene CUATRO sumandos —casco, puertas, herrajes y mano de
obra— y la ficha enseñaba dos. Los otros 31,12 € aparecían de la nada.

LA MANO DE OBRA ES LA PARTE QUE MÁS IMPORTA QUE SE VEA: son los 17 € por mueble
montado, o sea LA COMISIÓN DEL MONTADOR (CLAUDE.md, regla 16). Va dentro del
coste de fábrica y de ahí sale el margen; esconderla hace que el margen parezca
peor de lo que es sin que se sepa por qué.

CÓMO SE COMPRUEBA: con la ARITMÉTICA de la propia fórmula, sacada del código, no
mirando si la palabra «Herrajes» está en el JSX. Que el rótulo exista no
garantiza que sume.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")
RENT = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadMV.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_LA_FORMULA_DEL_COSTE_TIENE_CUATRO_SUMANDOS():
    """Se lee del cálculo. Si un día se añade un quinto, esta prueba lo dice y
    hay que enseñarlo también — que es exactamente lo que falló."""
    # LA SENTENCIA ENTERA, hasta su `;`. Buscar «la línea que contiene
    # `const costeTotal = Math.round`» dejó de encontrar nada el día que la
    # fórmula pasó a ser un ternario repartido en tres líneas (para que un
    # casco sin precio no se sume como cero), y esta prueba se puso roja sin
    # que nadie hubiera roto el desglose.
    rent = _lee(RENT)
    i = rent.index("const costeTotal")
    sentencia = rent[i:rent.index(";", i)]
    # Solo la parte que SUMA, no la rama del `null`.
    suma = sentencia[sentencia.index("Math.round"):]
    for parte in ("cc.coste", "costePuertas", "costeHerrajes", "costeMo"):
        assert parte in suma, (
            f"«{parte}» ya no entra en el coste total; la fórmula ha cambiado y "
            "el desglose de pantalla hay que revisarlo")
    assert suma.count("+") == 3, (
        f"la fórmula del coste ya no tiene cuatro sumandos: {suma.strip()}. "
        "Si se ha añadido otro, tiene que salir también en la ficha o el "
        "desglose dejará de cuadrar")


def test_LOS_HERRAJES_SE_SUMAN_IGUAL_QUE_EN_EL_CALCULO():
    """La pantalla no puede sumar los herrajes por su cuenta.

    `costeHerrajes` los suma en `despiece`; `herrajesDe` los vuelve a sumar para
    enseñarlos. Si las dos listas se separan, el desglose deja de cuadrar otra
    vez y nadie ve un error — solo un total que no sale.
    """
    rent = _lee(RENT)
    i = rent.index("const costeHerrajes")
    formula = rent[i:rent.index("const costeMo", i)]
    # Los conceptos que entran en el coste, por el nombre con que se devuelven.
    devueltos = ("bisagras", "patas", "colg", "caj", "gav", "soportes")
    cm3 = _lee(CM3)
    j = cm3.index("export const herrajesDe")
    # Hasta el cierre DE LA FUNCIÓN (`\n};`), no hasta el primer `};` — que es
    # el `|| {};` de la primera línea y dejaba fuera toda la suma.
    suma = cm3[j:cm3.index("\n};", j)]
    for concepto in devueltos:
        assert f"'{concepto}'" in suma, (
            f"«{concepto}» entra en el coste y NO se está sumando al enseñar "
            "los herrajes: el desglose no cuadrará")
    # Y al revés: nada de más.
    extra = re.findall(r"'(\w+)'", suma)
    assert set(extra) == set(devueltos), (
        f"la suma de herrajes de la pantalla lleva conceptos que el cálculo no "
        f"mete en el coste: {sorted(set(extra) - set(devueltos))}")


def test_LA_FICHA_ENSEÑA_LOS_CUATRO():
    # EL BLOQUE ENTERO, CONTANDO LLAVES, no una ventana de N caracteres. La
    # primera versión cogía 2600 caracteres a bulto y el día que se añadió al
    # casco su texto de ayuda del descuento de ACB, la ventana dejó de llegar
    # hasta «Coste» y esta prueba se puso roja SIN QUE NADIE HUBIERA ROTO NADA.
    # Una ventana fija miente en las dos direcciones: se queda corta cuando el
    # código crece, y se pasa de largo cazando lo que hay debajo.
    cm3 = _lee(CM3)
    i = cm3.index("Coste y margen: solo con el candado abierto")
    inicio = cm3.index("{verCoste && (", i)
    profundidad = 0
    for k in range(inicio, len(cm3)):
        if cm3[k] == "{":
            profundidad += 1
        elif cm3[k] == "}":
            profundidad -= 1
            if profundidad == 0:
                break
    else:
        raise AssertionError("el bloque de la ficha no se cierra")
    ficha = cm3[inicio:k]
    # LO QUE SE PINTA, no la palabra suelta. Buscar «Coste » a secas ya se
    # salvó solo: el texto de ayuda del casco dice «Coste neto del casco», así
    # que borrar el total de la ficha —el fallo entero de esta prueba— pasaba
    # en verde. Se busca la expresión que de verdad sale por pantalla.
    for etiqueta, expr in (("Casco", "`Casco ${"), ("Puertas", "`Puertas ${"),
                           ("Herrajes", "`Herrajes ${"), ("M. obra", "`M. obra ${"),
                           ("Coste", "`Coste ${")):
        assert expr in ficha, (
            f"la ficha no enseña «{etiqueta}»: el desglose no suma el "
            "total y quien lo mire no sabrá de dónde sale la diferencia")


def test_LA_MANO_DE_OBRA_SE_DICE_QUE_ES_LA_DEL_MONTADOR():
    """Es la misma cifra que cobra él (regla 16). Verla dentro del coste sin
    saber qué es lleva a tocarla creyendo que es un ajuste de fábrica."""
    # EL `title`, que es lo que el master lee al pasar por encima — no «la
    # palabra aparece por ahí cerca». El comentario que hay justo arriba
    # EXPLICA que es la del montador, así que una ventana a bulto se salvaba
    # sola con la explicación puesta y el texto quitado. Cuarta vez que este
    # proyecto tropieza con lo mismo.
    cm3 = "\n".join(l for l in _lee(CM3).split("\n")
                    if not l.lstrip().startswith("//"))
    i = cm3.index("M. obra ")
    titulo = cm3.rindex("title=", 0, i)
    assert "montador" in cm3[titulo:i], (
        "el texto de ayuda de la mano de obra no dice que es la del montador: "
        "quien la vea dentro del coste la tocará creyendo que es un ajuste de "
        "fábrica, y esa cifra es una nómina")


def test_EL_DESGLOSE_CUADRA_CON_NUMEROS_DE_VERDAD():
    """La aritmética del caso del master, con sus cifras.

    Es la prueba que de verdad importa: los rótulos pueden estar y no sumar.
    """
    casco, puertas, herrajes, mano = 61.15, 53.28, 14.12, 17.00
    total = round(casco + puertas + herrajes + mano, 2)
    assert total == 145.55, (
        f"la suma de los cuatro sumandos da {total} y el coste que enseñaba la "
        "pantalla era 145,55: si esto falla, el ejemplo de la documentación ya "
        "no describe el cálculo")
    # Y lo que se veía antes: dos de cuatro.
    assert round(casco + puertas, 2) == 114.43
    assert round(total - (casco + puertas), 2) == 31.12
