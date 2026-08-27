# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
import sys

def generate_prompt(layout, materials, style):
    """
    Genera un prompt optimizado para renderizado de cocinas.
    Incluye instrucciones específicas de distribución y materiales
    para que el motor de IA respete fielmente el diseño.
    """

    # Mapeo de estilos a descriptores visuales
    style_map = {
        "nórdico": "Scandinavian design with light wood tones, white surfaces, minimal hardware, organic textures, hygge atmosphere",
        "nordico": "Scandinavian design with light wood tones, white surfaces, minimal hardware, organic textures, hygge atmosphere",
        "industrial": "Industrial style with exposed metal, dark matte finishes, concrete textures, Edison bulbs, raw materials",
        "clásico": "Classic traditional style with raised panel doors, crown molding, marble countertops, warm wood tones",
        "clasico": "Classic traditional style with raised panel doors, crown molding, marble countertops, warm wood tones",
        "lacado blanco": "All-white lacquered cabinets, handleless push-to-open, ultra-clean minimalist, high gloss or matte finish",
        "madera natural": "Natural solid wood cabinets, visible grain, warm earth tones, artisan craftsmanship, oil-finished surfaces",
        "contemporáneo": "Contemporary design with mixed materials, geometric patterns, bold accent colors, integrated lighting",
        "contemporaneo": "Contemporary design with mixed materials, geometric patterns, bold accent colors, integrated lighting",
        "moderno": "Modern minimalist with flat-panel doors, integrated handles, neutral palette, clean geometric lines",
    }

    style_desc = style_map.get(style.lower().strip(), f"Kitchen style: {style}")

    base_prompt = (
        f"Photorealistic 3D architectural render of a kitchen interior. "
        f"Professional interior photography quality, 8K resolution. "
        f"\n\nLAYOUT AND DISTRIBUTION (MUST FOLLOW EXACTLY): {layout}. "
        f"\n\nMATERIALS AND FINISHES: {materials}. "
        f"\n\nDESIGN STYLE: {style_desc}. "
        f"\n\nTECHNICAL RENDER SETTINGS: "
        f"Natural daylight entering from window, supplemented by warm under-cabinet LED strips. "
        f"Camera at eye level (~160cm height), slight wide-angle perspective (24-35mm equivalent). "
        f"Shallow depth of field for cinematic feel. Ray-traced reflections on countertops and appliances. "
        f"Hyper-detailed material textures: wood grain, stone veining, brushed metal. "
        f"Interior design magazine quality (Architectural Digest, Elle Decor level)."
    )

    return base_prompt


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 generate_kitchen_prompt.py '<layout>' '<materials>' '<style>'")
    else:
        print(generate_prompt(sys.argv[1], sys.argv[2], sys.argv[3]))
