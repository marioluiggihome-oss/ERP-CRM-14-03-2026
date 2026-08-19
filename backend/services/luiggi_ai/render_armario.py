# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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
    acabados = (
        f"FINISHES (this is the ONLY thing the text decides — the geometry comes 100% from the "
        f"drawing): {brief}\n\n" if (brief or "").strip() else
        "Use restrained real materials (matt lacquer, natural oak veneer); the geometry still "
        "comes 100% from the drawing.\n\n")

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
