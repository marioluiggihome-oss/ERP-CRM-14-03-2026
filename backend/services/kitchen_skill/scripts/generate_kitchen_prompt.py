import sys

def generate_prompt(layout, materials, style):
    """
    Genera un prompt optimizado para renderizado de cocinas.
    """
    base_prompt = "Fotorrealistic 3D render of a modern kitchen, architectural photography, 8k resolution, cinematic lighting. "
    
    layout_desc = f"Layout: {layout}. "
    materials_desc = f"Materials and textures: {materials}. "
    style_desc = f"Cabinet style: {style}. "
    
    technical_specs = "Soft natural light from a window, high-end appliances, interior design magazine style, hyper-detailed textures, ray tracing."
    
    full_prompt = f"{base_prompt}{layout_desc}{materials_desc}{style_desc}{technical_specs}"
    return full_prompt

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 generate_kitchen_prompt.py '<layout>' '<materials>' '<style>'")
    else:
        print(generate_prompt(sys.argv[1], sys.argv[2], sys.argv[3]))
