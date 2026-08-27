# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
render_armario.py — EL ENCARGO DEL RENDER CUANDO EL CROQUIS ES UN ARMARIO.

Hasta ahora el croquis de un armario se renderizaba con el encargo de cocina:
mil palabras sobre el hueco de la campana encima de la placa, la encimera que
muere contra la columna, el diccionario de Frigo / Combi / Lavavajillas / Bajo
Fregadero, la regla de la L y la de la isla. Y una línea suelta al principio
diciendo «esto es un armario».

Órdenes contradictorias, y el modelo hace lo razonable: se queda con las mil
palabras. Por eso un armario de dos cuerpos con altillo y una cajonera abajo a
la izquierda volvía convertido en un frente de seis módulos con la cajonera en
el centro — que es, exactamente, la composición de una cocina.

Este fichero es el mismo trabajo pero con las reglas de un armario. Lo que se
comparte con la cocina (esto es una FOTO, no un dibujo; el dibujo manda la
geometría y el texto solo los acabados; nada de inventar módulos) se repite
aquí a propósito, porque un encargo tiene que poder leerse entero de una vez.
"""
from __future__ import annotations

from typing import Optional


def prompt_croquis_armario(transcripcion: str = "", brief: str = "") -> str:
    """El encargo completo para realizar EN FOTO el armario dibujado."""
    bloque = (f"\nWARDROBE SPECIFICATION EXTRACTED DIRECTLY FROM THE DRAWING:\n{transcripcion}\n"
              if transcripcion else "")
    # QUÉ HACE EL TEXTO. Decía «FINISHES: esto es lo ÚNICO que decide el texto»,
    # y bajo ese epígrafe se metía la descripción entera del master. La suya
    # decía «altillo de una sola puerta que abarca todo el ancho», «dividido en
    # dos módulos asimétricos», «el de la izquierda de mayor anchura y 3
    # cajones». Eso no son acabados: es la misma geometría del dibujo, escrita
    # por quien lo dibujó. Archivarla como acabado era tirarla.
    #
    # El dibujo sigue mandando —la regla existe porque la pantalla mandaba sus
    # valores por defecto («En L», «Cuarzo Blanco») contradiciendo el croquis—.
    # Lo que cambia es que cuando el texto CONFIRMA lo leído, se dice que
    # confirma, en vez de degradarlo a decoración.
    acabados = (
        "WHAT THE WRITTEN TEXT IS FOR:\n"
        "- The GEOMETRY comes 100% from the drawing. The text never overrides it.\n"
        "- But this text was written by the SAME person who made the drawing, and it has already "
        "been used to read it. Where it names a count — how many cuerpos, how many drawers, how "
        "many doors in the altillo, which side is wider — it CONFIRMS the specification above. "
        "Those numbers agree from two independent sources: treat them as certain, not as "
        "suggestions.\n"
        "- FINISHES, MATERIALS, COLOURS and the HANDLE SYSTEM come from this text.\n"
        f"- The text: {brief}\n\n" if (brief or "").strip() else
        "No text was written: use restrained real materials (matt lacquer, natural oak veneer). "
        "The geometry comes 100% from the drawing.\n\n")

    return (
        "You are given a TECHNICAL 2D DRAWING of ONE specific fitted wardrobe / built-in closet: "
        "a front elevation. It may be hand-drawn on a phone with a finger, and the lines may be "
        "wobbly — a wobbly line is a straight piece of furniture.\n"
        "ONLY THE DRAWING COUNTS. The image may be a PHONE SCREENSHOT OF A WHOLE PAGE: drawing-app "
        "toolbars, colour swatches, icons, a title, prices, and the phone's own status and "
        "navigation bars can surround the drawing. All of that is packaging — never render it, and "
        "never treat a toolbar or an icon as part of the furniture. Find the drawing inside the "
        "page and work from it alone.\n"
        + bloque +
        "Produce a single photorealistic interior photograph of THAT SAME wardrobe, built exactly "
        "as drawn. This is a FAITHFUL 3D realisation of the drawing, NOT a new design — do not "
        "'improve' it and do not substitute a nicer, fuller or more symmetrical layout.\n\n"

        "COUNT THE BAYS FIRST — THIS IS THE RULE THAT OVERRIDES THE OTHERS:\n"
        "- A wardrobe is a row of CUERPOS (vertical bays). Every full-height vertical line inside "
        "the outline separates one bay from the next. ONE vertical line means TWO bays. TWO lines "
        "mean THREE bays.\n"
        "- Render EXACTLY that many bays. Not more. A drawing of two wide bays must NOT come back "
        "as five or six narrow modules: that is a different piece of furniture, and it is the "
        "single most common way this goes wrong.\n"
        "- Keep the RELATIVE WIDTHS as drawn. A bay drawn wider than its neighbour is wider in the "
        "photograph. Never even them out into equal modules.\n"
        "- The wardrobe ends where the drawing ends. Do not add a bay on either side to 'fill the "
        "wall', and do not extend it to the corner of the room.\n\n"

        "THE ALTILLO IS A BAND, NOT A BAY:\n"
        "- A horizontal line crossing the WHOLE width near the top is the altillo (top boxes / "
        "maletero): a continuous horizontal band sitting ABOVE every bay, usually closing against "
        "the ceiling. Render it as one band with the number of sections drawn.\n"
        "- If NO such line is drawn, there is no altillo. Do not add one.\n"
        "- A horizontal line that stops at a vertical division is NOT an altillo: it is a shelf of "
        "that one bay.\n\n"

        "WHAT IS INSIDE EACH BAY STAYS IN THAT BAY:\n"
        "- Reproduce, bay by bay, exactly what the drawing puts inside it, in the same order top to "
        "bottom and at roughly the same heights. A bank of drawers drawn at the BOTTOM LEFT is at "
        "the bottom left in the photograph — never moved to the centre, never duplicated, never "
        "swapped with the neighbouring bay.\n"
        "- Several close parallel horizontal lines are a BANK OF DRAWERS: render that exact number "
        "of drawer fronts, with a continuous reveal across the full width of the bay.\n"
        "- Horizontal lines spaced well apart are SHELVES: render exactly that many, at those "
        "heights, spanning only their own bay.\n"
        "- A tall empty space, with or without a single shelf over it, is HANGING SPACE: render a "
        "hanging rail with clothes on it. An empty bay drawn empty stays open and mostly empty.\n"
        "- NEVER ADD INTERIOR THAT IS NOT DRAWN. No extra column of shelves, no extra drawer bank, "
        "no shoe rack, no jewellery tray, no wine-rack, no invented dividers. If it is not drawn, "
        "IT DOES NOT EXIST.\n\n"

        "DOORS: ONLY IF THEY ARE DRAWN:\n"
        "- If the drawing shows the INTERIOR — shelves, rails, drawer fronts visible — it is an "
        "OPEN elevation. Photograph the wardrobe OPEN, with the whole interior visible and NO door "
        "leaves in front of it. Do not close bays behind blank panels 'because a wardrobe has "
        "doors': hiding what is drawn is the same mistake as inventing what is not.\n"
        "- Only render doors when door leaves are actually drawn, and then exactly as many as "
        "drawn, of the type stated in the text (batiente / hinged, corredera / sliding).\n\n"

        "THE DRAWING GIVES GEOMETRY. IT NEVER GIVES STYLE:\n"
        "- The output is a PHOTOGRAPH of real furniture in a real room. It is never a drawing, "
        "illustration, cartoon, flat vector, cel-shaded image or 'render of a drawing'.\n"
        "- Copy from the reference ONLY: how many bays, their widths, and what goes inside each "
        "one. Copy NOTHING of how it is drawn — no outlines or contour lines around objects, no "
        "flat fills, no paper texture, no sketchy edges, no pastel illustration palette, no "
        "uniform lighting.\n"
        "- The colours of the drawing are NOT the materials. A wardrobe drawn in bare pencil on "
        "white paper, or filled in flat pale blue, is a wardrobe whose finish comes from the brief "
        "text; if the brief says nothing, use restrained real materials (matt lacquer, natural oak "
        "veneer).\n"
        "- Everything drawn inside becomes the REAL object photographed: garments in real fabric "
        "with real folds, real leather shoes, real fabric or cardboard boxes, real metal rails and "
        "hangers. Never a drawing of a shirt — an actual shirt.\n"
        "- Props are styling, never structure: a few folded garments or a box on a shelf are fine; "
        "an extra shelf to put them on is not.\n"
        "- Real photography: physically based materials, visible wood grain and textile weave, "
        "contact shadows under every object, soft directional daylight.\n\n"

        "CAMERA — A WARDROBE IS PHOTOGRAPHED STRAIGHT ON:\n"
        "- A fitted wardrobe stands flat against ONE single wall. Photograph it straight-on or very "
        "slightly off-axis, at mid height, so every bay reads at its true width from end to end.\n"
        "- A steep three-quarter angle is WRONG here: it foreshortens the far bays until they "
        "cannot be counted.\n"
        "- FRAME THE SHOT SO NOTHING IS CUT OFF: the complete wardrobe, floor line and top, inside "
        "the frame with a margin of room on both sides. Never crop a bay at the edge of the image.\n\n"

        + acabados +
        "Masterpiece ultra-sharp 8K architectural interior photograph, pin-sharp tack focus across "
        "the entire depth of field, maximum clarity on every edge, seam, joint and material "
        "texture. Extreme micro-detail PBR surfaces: razor-sharp wood grain, crisp textile weave, "
        "clean shadow gaps and handle profiles. Balanced natural architectural daylight, realistic "
        "soft shadows, 16:9 aspect ratio. Zero blur, no noise, no cartoon or CGI plastic look. "
        "No text, dimension lines, watermarks, logos or people."
    )


def reglas_del_plano_esquematico() -> str:
    """Lo que es MUEBLE y lo que es ANOTACIÓN en el plano de referencia.

    El master pidió el armario CERRADO y en la foto salió, pintada encima, una
    línea roja discontinua con el rótulo «Puerta 2» en rojo y una «M2» arriba:
    las anotaciones del plano esquemático que se le manda como referencia,
    copiadas literalmente dentro de la fotografía.

    Y era razonable. Al modelo se le da un dibujo técnico y se le dice
    «reprodúcelo EXACTAMENTE en forma fotorrealista». Nadie le había dicho qué
    partes de ese dibujo son el mueble y cuáles son el lápiz del delineante.

    El dibujo ya se ha limpiado de rótulos y de rojo (ver
    `generateBlueprintDataUrl`), pero esta regla se queda igualmente: el
    cliente puede subir su propio plano acotado, y ese sí viene lleno de cotas,
    flechas y números.
    """
    return (
        "\nTHE REFERENCE DRAWING: WHAT IS FURNITURE AND WHAT IS PENCIL:\n"
        "- A technical drawing has two layers. One is the FURNITURE: the outline, the door "
        "joints, the shelves, the drawer fronts, the rails. The other is NOTATION — the "
        "draughtsman's pencil: dimension lines and their arrows, the millimetre figures, module "
        "or door labels (M1, M2, 'Puerta 1'), dashed construction lines, captions, colour "
        "coding, and the white paper itself.\n"
        "- READ the notation. NEVER RENDER IT. The finished photograph contains no text, no "
        "digits, no arrows, no dashed lines and no labels of any colour — a red dashed line or "
        "the word 'Puerta' painted across the furniture makes the image WRONG, no matter how "
        "good the rest looks.\n"
        "- The drawing's colours are notation too: reds, ambers, greys and the white background "
        "are drawing conventions, never the finishes of the wardrobe. The finishes are the ones "
        "named in the COLORS section below.\n"
        "- The output is a PHOTOGRAPH of a real wardrobe in a real room, not a drawing and not a "
        "drawing with photographic texture on top.\n"
    )


def reglas_de_puertas_y_cuerpos(n_puertas: int, n_cuerpos: int,
                                tipo_puerta: str, ancho_mm,
                                todas_cerradas: bool = False) -> str:
    """Las dos reglas que faltaban en el render del configurador de Armarios.

    El master encargó DOS PUERTAS ABATIBLES en un armario de 1000 mm y volvió
    esto: una puerta abatible abierta a la izquierda, un panel cerrado en el
    centro que además parecía corredera, y un tercio del armario a la derecha
    CON ESTANTERÍA A LA VISTA Y SIN PUERTA NINGUNA. Por dentro, cuatro o cinco
    columnas de baldas donde había dos módulos.

    Y era razonable: el encargo decía «EXACTLY 2 doors» y describía el interior,
    pero en ninguna parte decía que esas dos puertas son TODO el frente. Sin esa
    frase, «dos puertas» se puede cumplir poniendo dos puertas donde sea y
    dejando el resto abierto — que es lo que hizo.

    Se pone aparte del `routes/armarios.py` porque es una regla, no una ruta, y
    así se puede probar sin levantar la aplicación.
    """
    tipo = (tipo_puerta or "").strip().lower()
    contrario = {
        "hinged": "sliding panels or bi-fold leaves",
        "sliding": "hinged doors on visible hinges or bi-fold leaves",
        "folding": "plain hinged doors or sliding panels",
    }.get(tipo, "doors of any other type")
    divisores = max(0, int(n_cuerpos) - 1)

    # CON TODO CERRADO NO SE VE NADA DEL INTERIOR. El plano de referencia ya se
    # dibuja con las puertas cerradas cuando se piden cerradas, pero se repite
    # por escrito: el interior sigue descrito más abajo en el encargo, y
    # describirlo es media invitación a enseñarlo.
    cerradas = (
        f"- IN THIS PHOTOGRAPH ALL {n_puertas} DOORS ARE CLOSED. The interior described below "
        "exists, but here it is exactly what must be HIDDEN. The front is one continuous run of "
        f"{n_puertas} closed door panels from the left edge to the right edge — no open bay, no "
        "gap, not one shelf, rail, drawer or garment visible anywhere.\n"
        if todas_cerradas else "")

    # CON UNA PUERTA ABIERTA, LAS DEMÁS SE PUEDEN CONTAR. «Las otras se quedan
    # cerradas» no es comprobable; «tienen que verse 2 paneles cerrados» sí, y
    # es lo único que el modelo puede repasar antes de dar la imagen por buena.
    # El master pidió la puerta 1 de tres abierta y volvieron DOS huecos de tres
    # de par en par.
    abiertas = (
        f"- COUNT THE CLOSED PANELS: exactly ONE door is open, so the photograph must show "
        f"exactly {int(n_puertas) - 1} CLOSED door panel(s) covering the rest of the front. If "
        "you can count fewer closed panels than that, or more than one section showing its "
        "interior, the image is WRONG.\n"
        if (not todas_cerradas and int(n_puertas) > 1) else "")

    return (
        cerradas + abiertas +
        "\nFRONT COVERAGE — THIS RULE OVERRIDES THE OTHERS:\n"
        f"- The {n_puertas} doors ARE the entire front of the wardrobe. Side by side they span "
        f"the full {ancho_mm}mm from the left edge to the right edge, with no gap between them "
        "and NO part of the front left uncovered.\n"
        "- An OPEN door reveals what is behind THAT door. It does not delete the door, and it "
        "does not turn its section into a permanently open shelving unit. Every part of the "
        "front that is not the open door is a CLOSED door panel.\n"
        "- NEVER render an open, doorless shelving bay beside the doors. If interior is visible "
        "anywhere other than behind the door that is open, the image is WRONG.\n"
        f"- All {n_puertas} doors are the SAME TYPE. This wardrobe has {tipo_puerta} doors: do "
        f"NOT mix in {contrario}.\n"
        "\nINTERIOR BAY COUNT:\n"
        f"- Inside, the wardrobe is divided into EXACTLY {n_cuerpos} vertical bay(s) by "
        f"{divisores} full-height vertical divider(s). Count them before you finish: "
        f"{n_cuerpos}, not more.\n"
        "- Never subdivide a bay into extra columns of shelves to fill the space, and never add "
        "a bay that is not in the specification.\n"
    )


def es_armario(project_type: Optional[str], space_type: Optional[str]) -> bool:
    """¿Este croquis es de un armario?

    Se mira lo que ELIGIÓ el usuario en la pantalla y, si no eligió, lo que se
    dedujo del texto. Acertar aquí es lo que decide si al modelo se le pide un
    armario o una cocina, así que se acepta también «vestidor»: un vestidor se
    dibuja igual y se lee igual.
    """
    pt = (project_type or "").strip().lower()
    if pt in ("armario", "vestidor", "closet", "wardrobe"):
        return True
    st = (space_type or "").lower()
    return "wardrobe" in st or "closet" in st or "walk-in" in st
