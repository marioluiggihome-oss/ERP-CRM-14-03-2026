# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
NINGÚN HOOK DESPUÉS DE UN `return`. PANTALLA EN NEGRO, ERP ENTERO CAÍDO.

El 29/08, el master: «cuando entro en máster sale este error», con la pantalla
completamente en negro en el móvil.

Era esto. En `SettingsModal.jsx` —el panel Master— se había añadido un
`useEffect` que carga las fichas de la agenda de montajes, y se coló DEBAJO del
`if (!isOpen) return null` que ese componente tiene a media altura. Con el panel
cerrado React ejecutaba 87 hooks; al abrirlo, 88. Eso es

    «Rendered more hooks than during the previous render»

y no es un fallo de esa pantalla: React tira el árbol entero, así que el ERP
completo se va a negro y solo se recupera recargando. No lo avisa el build, no
lo avisa ESLint con esta configuración, y no lo ve ninguna prueba de cálculo:
todos los demás candados miran lo que el ERP CALCULA, no si la pantalla se
llega a pintar.

QUÉ VIGILA. Que dentro de un mismo componente no haya una llamada a un hook
(`useState`, `useEffect`, `useMemo`, `useCallback`, `useRef`…) por debajo de un
`return` del cuerpo del componente. Es la regla de React de toda la vida: los
hooks van todos antes del primer `return`, sin excepción; lo que se condiciona
es lo que hacen DENTRO.

CÓMO. Se lee el JSX como texto, por líneas, y se mira la indentación: el cuerpo
de un componente va a dos espacios. Un `return` a dos espacios es una salida del
componente; un hook a dos espacios por debajo de esa salida es el fallo. Se
reinicia al empezar otra función de primer nivel, para no confundir el `return`
de una función auxiliar de arriba con la salida del componente.

No hace falta un analizador de JavaScript de verdad: hoy da CERO en las 92
pantallas del ERP, y con eso ya sujeta lo que tiene que sujetar. Si algún día
diera un falso positivo, se arregla el reconocedor — no se borra el candado.
"""
import os
import re

RAIZ = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "src")

# Empieza otra función de primer nivel: lo de antes ya no cuenta.
RE_NUEVA_FUNC = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s"
    r"|^(?:export\s+)?const\s+[A-Za-z_$][\w$]*\s*=\s*"
    r"(?:React\.)?(?:memo\(|forwardRef\(|\(|async\s*\(|function)")
# Cierre de una función de primer nivel.
RE_CIERRE = re.compile(r"^[}\)];?\s*$")
# Una salida del cuerpo del componente (dos espacios de indentación).
RE_SALIDA = re.compile(r"^  (?:if \(.*\)\s*)?return\b")
# Una llamada a un hook en el cuerpo del componente.
RE_HOOK = re.compile(
    r"^  (?:const .*=\s*)?use(?:State|Effect|Memo|Callback|Ref|Reducer|Context"
    r"|LayoutEffect)\s*\(")


def hooks_despues_del_return(texto):
    """Los hooks que quedan por debajo de una salida del mismo componente."""
    salida, malos = None, []
    for numero, linea in enumerate(texto.split("\n"), 1):
        if RE_NUEVA_FUNC.match(linea) or RE_CIERRE.match(linea):
            salida = None
        elif salida is None and RE_SALIDA.match(linea):
            salida = (numero, linea.strip())
        elif salida and RE_HOOK.match(linea):
            malos.append((numero, linea.strip(), salida[0], salida[1]))
            salida = None
    return malos


def pantallas():
    for carpeta, _, ficheros in os.walk(RAIZ):
        # `components/ui` es shadcn/ui (código de terceros, MIT): no se toca.
        if "components/ui" in carpeta.replace("\\", "/"):
            continue
        for f in sorted(ficheros):
            if f.endswith((".jsx", ".js")):
                yield os.path.join(carpeta, f)


def test_NINGUNA_PANTALLA_llama_a_un_hook_por_debajo_de_un_return():
    fallos = []
    for ruta in pantallas():
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        for numero, hook, n_salida, salida in hooks_despues_del_return(texto):
            fallos.append(
                f"{os.path.relpath(ruta, RAIZ)}:{numero}\n"
                f"      hook   : {hook[:90]}\n"
                f"      debajo : línea {n_salida} · {salida[:90]}")
    assert not fallos, (
        "hay hooks por debajo de un `return` del componente. Al abrir esa "
        "pantalla React ejecuta más hooks que antes, tira el árbol entero y el "
        "ERP se queda EN NEGRO — no solo esa pantalla. Súbelos por encima del "
        "primer `return` y condiciona lo que hacen dentro:\n\n" + "\n".join(fallos))


def test_el_PANEL_MASTER_carga_las_fichas_antes_de_su_return():
    """El caso concreto que tumbó el ERP el 29/08, para que se lea aquí.

    `SettingsModal.jsx` tiene un `if (!isOpen) return null` a media altura, así
    que es la pantalla donde este fallo es más fácil de cometer: parece natural
    poner el `useEffect` al lado del código que lo usa, y ese código está abajo.
    """
    ruta = os.path.join(RAIZ, "components", "SettingsModal.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.read().split("\n")

    cierra = next(i for i, l in enumerate(lineas, 1)
                  if l.strip() == "if (!isOpen) return null;")
    montadores = next(i for i, l in enumerate(lineas, 1) if "api/montadores" in l)
    assert montadores < cierra, (
        f"la carga de fichas de montador (línea {montadores}) ha vuelto a caer "
        f"por debajo del `if (!isOpen) return null` (línea {cierra}). Abrir el "
        "panel Master deja el ERP en negro.")


def test_el_RECONOCEDOR_encuentra_el_fallo_cuando_lo_hay():
    """Un candado que no se ha visto fallar no protege nada.

    Aquí se le da el patrón exacto que tumbó el ERP —un `useEffect` debajo del
    `return null`— y tiene que señalarlo. Sin esto, un reconocedor que no
    reconociera NADA daría cero fallos y el CI en verde para siempre.
    """
    roto = (
        "export default function Panel({ isOpen }) {\n"
        "  const [a, setA] = useState(null);\n"
        "  if (!isOpen) return null;\n"
        "  useEffect(() => { setA(1); }, []);\n"
        "  return <div />;\n"
        "}\n")
    encontrados = hooks_despues_del_return(roto)
    assert len(encontrados) == 1 and encontrados[0][0] == 4, encontrados

    bueno = (
        "export default function Panel({ isOpen }) {\n"
        "  const [a, setA] = useState(null);\n"
        "  useEffect(() => { if (!isOpen) return; setA(1); }, [isOpen]);\n"
        "  if (!isOpen) return null;\n"
        "  return <div />;\n"
        "}\n")
    assert hooks_despues_del_return(bueno) == [], (
        "el reconocedor señala como fallo un componente correcto")
