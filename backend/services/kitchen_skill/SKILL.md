---
name: kitchen-3d-render
description: Generación de renders 3D fotorrealistas de cocinas a partir de bocetos, dictados de distribución y especificaciones de materiales. Úsalo para transformar ideas de diseño en imágenes visuales de alta calidad.
---

# Kitchen 3D Render Skill

Esta habilidad permite a Manus actuar como un diseñador de interiores especializado en cocinas, capaz de interpretar entradas multimodales y convertirlas en visualizaciones profesionales.

## Flujo de Trabajo

1.  **Análisis de Entrada**:
    *   Si el usuario envía un **boceto**, utiliza la visión para identificar la ubicación de muebles, electrodomésticos y ventanas.
    *   Si el usuario envía un **dictado o texto**, extrae las medidas y la distribución (ej. cocina en L, isla central).
    *   Si el usuario envía fotos de **puertas o materiales**, identifica el estilo (ej. minimalista, rústico) y la textura.

2.  **Consolidación de Datos**:
    Organiza la información en tres categorías: Distribución, Materiales y Estilo de Puerta. Consulta `/home/ubuntu/skills/kitchen-3d-render/references/materials_guide.md` para usar terminología técnica precisa.

3.  **Generación de Prompt**:
    Utiliza el script `/home/ubuntu/skills/kitchen-3d-render/scripts/generate_kitchen_prompt.py` para crear un prompt técnico. Pasa los datos recolectados como argumentos.

4.  **Renderizado**:
    Usa herramientas de generación de imágenes (como `generate_image`) con el prompt generado para producir el render final.

## Recursos Disponibles

- **Guía de Materiales**: `/home/ubuntu/skills/kitchen-3d-render/references/materials_guide.md` - Referencia para descripciones precisas de acabados.
- **Generador de Prompts**: `/home/ubuntu/skills/kitchen-3d-render/scripts/generate_kitchen_prompt.py` - Script para estandarizar la creación de prompts de renderizado.

## Ejemplo de Uso

> "Tengo un boceto de una cocina en U con una isla. Quiero muebles de madera de roble con encimera de mármol blanco. Te adjunto la foto de la puerta que me gusta."

1.  Analizar el boceto y la foto de la puerta.
2.  Consultar la guía de materiales para describir el roble y el mármol.
3.  Ejecutar el script generador de prompts.
4.  Generar y entregar la imagen al usuario.
