# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL LIMPIADOR DE COMENTARIOS QUE SE COMÍA EL CÓDIGO.

Nueve candados de este repo necesitan leer un JSX SIN sus comentarios, porque
los ficheros de este proyecto explican los fallos citándolos: si no se quitan,
el candado se aprueba —o se acusa— con su propia documentación. Ya había pasado
cinco veces.

Todos escribían la misma línea:

    re.sub(r"/\\*.*?\\*/", " ", cuerpo, flags=re.S)

Y esa línea SE COME CÓDIGO. Se descubrió persiguiendo un falso positivo en
`RentabilidadLineas.jsx`, donde hay esto, que es de lo más corriente:

    accept="image/*,application/pdf"

Ese `/*` de dentro de una cadena abre un comentario que no existe, y el `.*?` lo
cierra en el siguiente `*/` de verdad — un comentario JSX diez líneas más abajo.
Por el camino se tragaba el botón `setShowTotals(s => !s)`.

POR QUÉ IMPORTA TANTO: un candado que lee un fichero mutilado MIENTE EN LAS DOS
DIRECCIONES. Si busca algo que tiene que estar, dirá que falta y se pondrá rojo
sin que nadie haya roto nada. Si busca algo prohibido, dirá que no está y dejará
pasar justo lo que vigila. Y no da ningún error: devuelve un texto perfectamente
válido, solo que con agujeros.

ESTE CANDADO COMPRUEBA LAS DOS MITADES, que es lo que de verdad hay que
sostener: que los comentarios SE VAN, y que el código NO.
"""
import glob
import os

from jsx_limpio import sin_comentarios, cortes_de_comentario

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")


def test_EL_CASO_QUE_LO_DESTAPO_un_accept_de_imagen():
    """`image/*` dentro de una cadena no abre ningún comentario."""
    jsx = '''
      <input accept="image/*,application/pdf" onChange={subir} />
      {/* esto sí es un comentario */}
      <button onClick={() => setShowTotals(s => !s)}>Totales</button>
    '''
    limpio = sin_comentarios(jsx)
    assert "setShowTotals(s => !s)" in limpio, (
        "el limpiador se ha comido el botón: un `/*` dentro de una cadena le "
        "abre un comentario que no existe")
    assert 'accept="image/*,application/pdf"' in limpio
    assert "esto sí es un comentario" not in limpio


def test_UNA_URL_NO_SE_COME_EL_RESTO_DE_LA_LINEA():
    """`https://...` lleva `//` dentro. Tratarlo como comentario de línea
    borraría lo que venga detrás en esa misma línea."""
    jsx = '<a href="https://erp.luiggihome.es/coop" data-testid="ir-a-coop">COOP</a>'
    limpio = sin_comentarios(jsx)
    assert 'data-testid="ir-a-coop"' in limpio, (
        "las dos barras de una URL se han tomado por un comentario de línea")
    assert ">COOP<" in limpio


def test_LOS_COMENTARIOS_DE_VERDAD_SE_VAN():
    """La mitad para la que se escribió la función. Sin esto no sirve de nada."""
    jsx = """
      // el motor viejo era manus
      const motor = 'gemini';
      /* y antes de eso
         se llamaba directo a la API */
      const otro = 1;
    """
    limpio = sin_comentarios(jsx)
    assert "manus" not in limpio, "no se quitan los comentarios de línea"
    assert "se llamaba directo" not in limpio, "no se quitan los bloques"
    assert "const motor = 'gemini';" in limpio and "const otro = 1;" in limpio


def test_LOS_NUMEROS_DE_LINEA_SIGUEN_CUADRANDO():
    """Un candado que informe de «línea 412» tiene que acertar, así que un
    comentario se sustituye por sus saltos de línea, no por nada."""
    jsx = "const a = 1;\n/* uno\n   dos\n   tres */\nconst b = 2;\n"
    assert sin_comentarios(jsx).count("\n") == jsx.count("\n")


def test_UNA_COMILLA_SUELTA_EN_UN_TEXTO_NO_ENMASCARA_MEDIO_FICHERO():
    """En castellano y en catalán hay apóstrofos dentro de textos. Si una
    comilla suelta abriera una cadena hasta la siguiente, el enmascarado se
    llevaría por delante todo lo que hubiera en medio."""
    jsx = """
      <p>No s'ha pogut desar</p>
      {/* este comentario va DESPUES del apostrofo */}
      <button data-testid="reintentar">Reintentar</button>
    """
    limpio = sin_comentarios(jsx)
    assert 'data-testid="reintentar"' in limpio, (
        "un apóstrofo dentro de un texto ha enmascarado el resto del fichero")
    # EL DAÑO DE VERDAD ES POR DEFECTO, NO POR EXCESO: si el apóstrofo abre una
    # cadena que no se cierra nunca, todo lo que venga detrás queda enmascarado
    # y los comentarios que haya ahí YA NO SE QUITAN. El candado vuelve
    # entonces a creerse la explicación del fichero, que es de lo que se trataba
    # protegerse. Sin esta línea, romper el corte por salto de línea pasaba en
    # verde: se comprobó rompiéndolo.
    assert "este comentario va DESPUES" not in limpio, (
        "un apóstrofo suelto ha enmascarado el resto del fichero y los "
        "comentarios de después ya no se quitan")


def test_TODO_LO_QUE_SE_RECORTA_ES_UN_COMENTARIO_EN_LAS_92_PANTALLAS():
    """LA PROPIEDAD EXACTA, sobre el ERP entero: cada trozo que desaparece
    tiene que EMPEZAR por `//` o por `/*`.

    Así se caza el fallo de verdad —comerse código— sin tener que escribir un
    analizador de JavaScript. Con el limpiador viejo, el trozo que empezaba en
    el `/*` de `image/*` arrancaba por `*,application/pdf" className=...`, que
    no es un comentario, y esta prueba lo dice señalando el fichero y la línea.
    """
    malos = []
    for ruta in sorted(glob.glob(os.path.join(SRC, "**", "*.jsx"), recursive=True)):
        if os.sep + "ui" + os.sep in ruta:
            continue  # shadcn/ui, código de terceros
        cuerpo = open(ruta, encoding="utf-8").read()
        for a, b in cortes_de_comentario(cuerpo):
            trozo = cuerpo[a:b]
            if not (trozo.startswith("//") or trozo.startswith("/*")):
                linea = cuerpo[:a].count("\n") + 1
                malos.append((os.path.basename(ruta), linea, trozo[:50]))
    assert not malos, (
        f"el limpiador está recortando trozos que NO son comentarios "
        f"({len(malos)}): {malos[:4]}. Eso es código que desaparece, y un "
        "candado que lea el fichero mutilado miente en las dos direcciones")


def test_NINGUN_CANDADO_SE_ESCRIBE_SU_PROPIO_LIMPIADOR_DE_JSX():
    """Nueve copias de la misma línea rota. La que se arregla es la de aquí, y
    si mañana alguien vuelve a escribirla a mano el fallo vuelve solo — con la
    diferencia de que ya sabemos que existe."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    culpables = []
    for ruta in sorted(glob.glob(os.path.join(aqui, "test_*.py"))):
        cuerpo = open(ruta, encoding="utf-8").read()
        if 'r"/\\*.*?\\*/"' in cuerpo or 'r"/\\*[\\s\\S]*?\\*/"' in cuerpo:
            culpables.append(os.path.basename(ruta))
    assert not culpables, (
        f"estos candados vuelven a quitar los comentarios a mano, con la "
        f"expresión que se come el código: {culpables}. Se usa "
        "`jsx_limpio.sin_comentarios`, que ya sabe que `image/*` no abre "
        "ningún comentario")
