# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
3D Estudio — Router Maestro
============================
Módulo unificado de diseño de cocinas para el ERP.
Todas las capacidades de IA pasan exclusivamente por el motor LuiggiAI
(capa white-label sobre Manus API), usando la skill kitchen-3d-render
para construir prompts de render de calidad profesional.

Endpoints:
  GET  /estudio-cocinas/estado
  POST /estudio-cocinas/render          → Render fotorrealista (texto + croquis opcional)
  POST /estudio-cocinas/render/editar   → Editar render existente en lenguaje natural
  POST /estudio-cocinas/transcribir     → Transcribir audio/voz a texto
  POST /estudio-cocinas/plano-2d        → Plano técnico acotado (matplotlib)
  POST /estudio-cocinas/ficha-tecnica   → Ficha técnica en Markdown
  POST /estudio-cocinas/presentacion    → Presentación HTML para cliente
  GET  /estudio-cocinas/tarea/{id}      → Consultar estado de tarea asíncrona
  GET  /estudio-cocinas/tarea/{id}/resultado → Obtener resultado de tarea completada
"""
from __future__ import annotations

import asyncio
import base64
import datetime
import io
import logging
import math
import os
import re
import sys
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

logger = logging.getLogger("estudio_cocinas")

# ─── Auth ─────────────────────────────────────────────────────────────────────
# SI FALLA ESTE IMPORT, EL ERP NO ARRANCA. Y ES LO QUE QUEREMOS.
#
# Aquí había un `try/except` que, ante cualquier error importando `require_auth`
# —una dependencia que no se instala en un despliegue, un cambio de nombre—,
# dejaba `_DEPS = []` y seguía como si nada. O sea que TODOS los endpoints del
# Estudio 3D se quedaban abiertos: render, planos, relación MV, volcado... sin
# contraseña y sin una sola línea en el registro que lo dijera.
#
# Un ERP que no arranca se arregla en cinco minutos porque se ve enseguida. Uno
# que arranca con la puerta abierta no se nota hasta que es tarde. Así que el
# fallo se deja subir: mejor ruidoso que silencioso.
from services.jwt_service import require_auth, get_current_user, ADMIN_ROLE_FLAGS

_DEPS = [Depends(require_auth)]

router = APIRouter(
    prefix="/estudio-cocinas",
    tags=["3D Estudio"],
    dependencies=_DEPS,
)

# ─── Motor LuiggiAI (Manus API white-label) ───────────────────────────────────
def _get_engine():
    """Obtiene la instancia del motor LuiggiAI."""
    try:
        from services.luiggi_ai.engine_core import LuiggiAICore
        return LuiggiAICore()
    except Exception as e:
        logger.error(f"No se pudo inicializar LuiggiAI: {e}")
        return None

# ─── Skill: generador de prompts de cocinas ───────────────────────────────────
_SKILL_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "kitchen_skill")

def _load_materials_guide() -> str:
    """Carga la guía de materiales de la skill kitchen-3d-render."""
    path = os.path.join(_SKILL_DIR, "references", "materials_guide.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _generate_render_prompt(layout: str, materials: str, style: str,
                             extra: str = "") -> str:
    """
    Genera un prompt técnico de alta calidad usando el script de la skill.
    Fallback manual si el script no está disponible.
    """
    try:
        script_path = os.path.join(_SKILL_DIR, "scripts", "generate_kitchen_prompt.py")
        spec = __import__("importlib.util", fromlist=["util"]).util.spec_from_file_location(
            "gen_prompt", script_path)
        mod = __import__("importlib.util", fromlist=["util"]).util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        base = mod.generate_prompt(layout, materials, style)
    except Exception:
        base = (
            f"Fotorealistic 3D render of a kitchen, architectural photography, "
            f"8k resolution, cinematic lighting. Layout: {layout}. "
            f"Materials: {materials}. Cabinet style: {style}. "
            "Soft natural light from a window, high-end appliances, "
            "interior design magazine style, hyper-detailed textures, ray tracing."
        )
    if extra:
        base += f" Additional details: {extra}"
    return base


def _parse_medidas(texto: str) -> dict:
    """Parsea texto libre de medidas → dict con ancho, alto, isla_w, isla_h en cm.

    NUNCA inventa (ver CLAUDE.md): lo que no venga en el texto sale como None y se
    lista en `faltan`. Antes rellenaba en silencio 400×350 (isla 200×100), y esos
    números ficticios acababan impresos como si fueran medidas reales.
    """
    nums = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:cm|m)?', (texto or "").lower())
    vals = [float(n.replace(',', '.')) for n in nums if float(n.replace(',', '.')) > 0]
    vals_cm = [int(v * 100) if v < 20 else int(v) for v in vals]
    out = {
        "ancho":  vals_cm[0] if len(vals_cm) > 0 else None,
        "alto":   vals_cm[1] if len(vals_cm) > 1 else None,
        "isla_w": vals_cm[2] if len(vals_cm) > 2 else 0,
        "isla_h": vals_cm[3] if len(vals_cm) > 3 else 0,
    }
    out["faltan"] = [k for k in ("ancho", "alto") if not out[k]]
    return out


def _medidas_para_dibujo(texto: str) -> dict:
    """Medidas para algo que se va a DIBUJAR o calcular numéricamente. Sin medidas
    reales no se dibuja: se rechaza con un motivo claro (jamás se aproxima)."""
    m = _parse_medidas(texto)
    if m["faltan"]:
        raise HTTPException(
            status_code=422,
            detail=("Faltan medidas reales (" + ", ".join(m["faltan"]) +
                    "). Indícalas para poder acotar: sin ellas las cotas no serían medidas reales."))
    return m


def _fmt_medida(v) -> str:
    """Formatea una medida para un documento: si no se conoce, se dice."""
    return f"{v}" if v else "por definir"

# ─── Modelos ──────────────────────────────────────────────────────────────────

class DistribucionEstructurada(BaseModel):
    tipo: Optional[str] = Field(default="lineal", description="Tipo: lineal, l, u, paralela, isla, g")
    paredes: Optional[list] = Field(default=[], description="Lista de paredes [{nombre, ancho, alto}]")
    isla: Optional[dict] = Field(default={}, description="{ancho, largo} de la isla si existe")
    elementos: Optional[list] = Field(default=[], description="Lista de elementos [{id, label, pared_idx, ancho}]")

class RenderInput(BaseModel):
    descripcion: str = Field(..., description="Descripción libre de la cocina")
    estilo: Optional[str] = Field(default="Moderno", description="Estilo de diseño")
    materiales: Optional[str] = Field(default="", description="Materiales específicos")
    distribucion: Optional[str] = Field(default="", description="Distribución (L, U, isla...)")
    distribucion_estructurada: Optional[DistribucionEstructurada] = Field(default=None, description="Distribución estructurada con paredes y elementos")
    croquis_b64: Optional[str] = Field(default=None, description="Croquis en base64 (opcional)")
    modo_async: Optional[bool] = Field(default=False, description="Si True devuelve task_id sin esperar")
    free_design: Optional[bool] = Field(default=False, description="Si True, la IA diseña libremente sin respetar el croquis")
    provider: Optional[str] = Field(default=None, description="Motor: gemini (por defecto, más fiel) | manus")

class EditarRenderInput(BaseModel):
    render_url: Optional[str] = Field(default=None, description="URL del render previo")
    render_b64: Optional[str] = Field(default=None, description="Render previo en base64")
    instruccion: str = Field(..., description="Instrucción de edición en lenguaje natural")
    modo_async: Optional[bool] = Field(default=False)

class ProyectoBase(BaseModel):
    nombre_cliente: Optional[str] = Field(default="Cliente")
    descripcion: Optional[str] = Field(default="")
    estilo: Optional[str] = Field(default="Moderno")
    notas: Optional[str] = Field(default="")
    medidas: Optional[str] = Field(default="")
    presupuesto: Optional[str] = Field(default="")
    distribucion_estructurada: Optional[DistribucionEstructurada] = Field(default=None, description="Distribución estructurada")
    con_cotas: Optional[bool] = Field(default=True, description="Dibujar las cotas en el alzado")
    monocromo: Optional[bool] = Field(default=False, description="Vista alámbrica en blanco y negro (estilo CAD)")
    # Solo lo usa el BOCETO EN PERSPECTIVA. El alzado y la planta se dibujan
    # siempre a línea recta: son planos de taller, y el temblor los afea y hace
    # dudar de dónde está cada cosa.
    boceto: Optional[bool] = Field(default=False, description="Trazo a mano alzada. Solo en el boceto en perspectiva")

# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/estado")
async def estado_modulo():
    """Estado del módulo y disponibilidad del motor."""
    engine = _get_engine()
    if engine:
        status = engine.get_status()
        activo = status.get("status") == "active"
    else:
        activo = False

    return {
        "modulo": "3D Estudio",
        "version": "3.0.0",
        "motor": "LuiggiAI (Manus API)",
        "motor_activo": activo,
        "skill_render": os.path.exists(os.path.join(_SKILL_DIR, "SKILL.md")),
        "capacidades": {
            "render_fotorrealista": activo,
            "edicion_render": activo,
            "transcripcion_audio": activo,
            "plano_2d": True,
            "ficha_tecnica": True,
            "presentacion_html": True,
        },
    }


@router.post("/render")
async def generar_render(payload: RenderInput):
    """
    Genera un render fotorrealista de cocina usando Manus API (LuiggiAI).
    Combina la descripción del usuario con la skill kitchen-3d-render
    para construir un prompt técnico de alta calidad.

    Si modo_async=True devuelve {task_id} inmediatamente.
    Si modo_async=False (por defecto) espera el resultado (máx. 5 min).
    """
    engine = _get_engine()
    if not engine or engine.get_status().get("status") != "active":
        raise HTTPException(
            status_code=503,
            detail="Motor de IA no disponible. Verifica que MANUS_API_KEY esté configurada en Railway."
        )

    # Construir prompt técnico usando la skill
    materiales = payload.materiales or "encimera de silestone, muebles lacados en mate"
    estilo = payload.estilo or "Moderno"

    # ═══════════════════════════════════════════════════════════════════════════
    # PROMPT POSICIONAL ULTRA-DETALLADO
    # Describe la cocina módulo a módulo, de izquierda a derecha, con restricciones
    # negativas explícitas para que la IA respete la distribución exacta.
    # ═══════════════════════════════════════════════════════════════════════════
    dist_struct = payload.distribucion_estructurada
    es_libre = getattr(payload, 'free_design', False)
    tiene_croquis = bool(payload.croquis_b64)

    # --- Construir descripción posicional detallada ---
    if dist_struct and dist_struct.tipo and not es_libre:
        tipo = dist_struct.tipo
        paredes = dist_struct.paredes or []
        isla_data = dist_struct.isla or {}
        elementos = dist_struct.elementos or []
        tiene_isla = tipo == 'isla' or (isla_data.get('ancho', 0) > 0)

        dist_labels = {
            'lineal': 'LINEAL (todos los módulos en una sola pared recta)',
            'l': 'EN L (dos paredes formando esquina de 90°)',
            'u': 'EN U (tres paredes formando U)',
            'paralela': 'PARALELA (dos paredes enfrentadas con pasillo central)',
            'isla': 'CON ISLA CENTRAL (pared de módulos + isla exenta en el centro)',
            'g': 'EN G (tres paredes + península que cierra parcialmente)'
        }

        # Restricciones negativas según tipo
        restricciones_negativas = []
        if tipo != 'isla' and not tiene_isla:
            restricciones_negativas.append("NO hay isla central — NO dibujes ninguna isla ni mueble exento en el centro")
        if tipo == 'lineal':
            restricciones_negativas.append("NO hay muebles en más de una pared — TODO está en una sola pared recta")
            restricciones_negativas.append("NO hay esquinas de cocina — es una línea recta")
        if tipo == 'paralela':
            restricciones_negativas.append("NO hay esquinas — son dos líneas rectas paralelas enfrentadas")
        if tipo in ('lineal', 'l', 'paralela'):
            restricciones_negativas.append("NO hay península")

        # Siempre añadir restricciones sobre ventanas/puertas inventadas
        restricciones_negativas.append("NO inventes ventanas grandes centrales si no se mencionan")
        restricciones_negativas.append("NO añadas puertas, arcos ni aberturas que no se describan")
        restricciones_negativas.append("NO cambies la distribución por una que te parezca más bonita")

        # Descripción posicional módulo a módulo
        posicional_desc = f"DISTRIBUCIÓN EXACTA: {dist_labels.get(tipo, tipo.upper())}\n\n"

        # Describir cada pared con sus elementos de izquierda a derecha
        for i, pared in enumerate(paredes):
            nombre_p = pared.get('nombre', f'Pared {i+1}')
            ancho_p = pared.get('ancho', 0)
            alto_p = pared.get('alto', 240)
            posicional_desc += f"PARED {i+1} — {nombre_p} ({ancho_p}cm de ancho × {alto_p}cm de alto):\n"

            # Obtener elementos de esta pared en orden
            elems_pared = sorted(
                [e for e in elementos if e.get('pared_idx', 0) == i],
                key=lambda e: e.get('posicion_cm', 0)
            )

            if elems_pared:
                posicional_desc += "  Secuencia de módulos DE IZQUIERDA A DERECHA:\n"
                pos_acum = 0
                for j, el in enumerate(elems_pared):
                    label = el.get('label', el.get('id', '?'))
                    ancho_el = el.get('ancho', 60)
                    posicional_desc += f"    {j+1}. {label} — {ancho_el}cm de ancho (posición: {pos_acum}cm a {pos_acum + ancho_el}cm)\n"
                    pos_acum += ancho_el
                espacio_libre = ancho_p - pos_acum
                if espacio_libre > 0:
                    posicional_desc += f"    → Espacio libre restante: {espacio_libre}cm (módulos de almacenaje estándar)\n"
            else:
                posicional_desc += f"  Módulos de almacenaje estándar a lo largo de toda la pared ({ancho_p}cm)\n"
            posicional_desc += "\n"

        # Isla si existe
        if tiene_isla:
            iw = isla_data.get('ancho', 120)
            il = isla_data.get('largo', 200)
            posicional_desc += f"ISLA CENTRAL (exenta en el centro de la habitación):\n"
            posicional_desc += f"  Dimensiones: {iw}cm × {il}cm\n"
            posicional_desc += f"  Separada de la pared principal por al menos 90cm de pasillo\n\n"

        # Restricciones negativas
        posicional_desc += "RESTRICCIONES OBLIGATORIAS (NO VIOLAR NINGUNA):\n"
        for r in restricciones_negativas:
            posicional_desc += f"  ✗ {r}\n"

        distribucion = posicional_desc
    elif dist_struct and dist_struct.tipo and es_libre:
        # Modo libre: solo dar dimensiones como referencia
        paredes = dist_struct.paredes or []
        dims = ' + '.join([f"{p.get('nombre','Pared')}: {p.get('ancho',0)}cm" for p in paredes])
        distribucion = f"Espacio disponible: {dims}. LIBERTAD CREATIVA TOTAL para proponer tu propio diseño."
    else:
        distribucion = payload.distribucion or payload.descripcion

    # --- Prompt técnico de render ---
    prompt_tecnico = _generate_render_prompt(
        layout=distribucion,
        materials=materiales,
        style=estilo,
        extra=payload.descripcion if payload.distribucion else "",
    )

    # --- Instrucciones sobre croquis adjunto ---
    instrucciones_croquis = ""
    if tiene_croquis and not es_libre:
        instrucciones_croquis = (
            "\n\n═══ CROQUIS/PLANO ADJUNTO — REFERENCIA OBLIGATORIA ═══\n"
            "Se adjunta un croquis/plano técnico de la cocina. DEBES respetar ESTRICTAMENTE:\n"
            "1. La DISTRIBUCIÓN EXACTA visible en el plano (lineal, en L, en U, etc.)\n"
            "2. La POSICIÓN RELATIVA de cada electrodoméstico y módulo\n"
            "3. Las PROPORCIONES entre módulos (un módulo de 80cm debe verse más ancho que uno de 60cm)\n"
            "4. El NÚMERO EXACTO de muebles altos y bajos\n"
            "5. La AUSENCIA de elementos: si no hay isla en el plano, NO la añadas\n"
            "6. Si no hay ventana central en el plano, NO la inventes\n"
            "7. Respeta la FORMA de la habitación tal como aparece en el croquis\n"
            "\nEl croquis es la VERDAD ABSOLUTA de la distribución. Tu trabajo es SOLO\n"
            "aplicar el estilo visual y los materiales, NO rediseñar la distribución.\n"
        )
    elif tiene_croquis and es_libre:
        instrucciones_croquis = (
            "\n\nNOTA: Se adjunta un croquis como REFERENCIA del espacio disponible.\n"
            "Tienes LIBERTAD CREATIVA total para proponer tu propio diseño.\n"
            "Usa el croquis solo para entender las dimensiones del espacio.\n"
        )

    # --- Instrucción final completa ---
    instruccion = (
        f"Genera un render fotorrealista de alta gama de una cocina.\n\n"
        f"══════════════════════════════════════════════════\n"
        f"DISTRIBUCIÓN Y POSICIÓN DE MÓDULOS (RESPETAR AL 100%):\n"
        f"══════════════════════════════════════════════════\n"
        f"{distribucion}\n\n"
        f"══════════════════════════════════════════════════\n"
        f"ESTILO Y MATERIALES:\n"
        f"══════════════════════════════════════════════════\n"
        f"Estilo: {estilo}\n"
        f"Materiales: {materiales}\n"
        f"Descripción adicional: {payload.descripcion}\n\n"
        f"══════════════════════════════════════════════════\n"
        f"REQUISITOS TÉCNICOS DEL RENDER:\n"
        f"══════════════════════════════════════════════════\n"
        f"- Render fotorrealista 8K, iluminación natural cinematográfica\n"
        f"- Perspectiva angular desde esquina a altura de ojos (~160cm), formato 16:9\n"
        f"- Calidad de revista de interiorismo de lujo (Architectural Digest, Elle Decor)\n"
        f"- Texturas hiper-detalladas: vetas de madera, brillos de encimera, reflejos metálicos\n"
        f"- Profundidad de campo sutil, sin distorsión de lente\n"
        f"- Devuelve SOLO la imagen generada, sin texto adicional\n"
        f"\n══════════════════════════════════════════════════\n"
        f"PROMPT TÉCNICO:\n"
        f"══════════════════════════════════════════════════\n"
        f"{prompt_tecnico}"
        f"{instrucciones_croquis}"
    )

    # Con CROQUIS adjunto (y sin diseño libre): un prompt CORTO y 100% FIEL al dibujo
    # funciona mucho mejor que la dirección de arte larga (que hace que el modelo
    # invente una cocina genérica que no se parece al croquis). Es un re-render fiel
    # del croquis; solo se aplican acabado/estilo, sin cambiar la distribución.
    if tiene_croquis and not es_libre:
        instruccion = (
            "Tienes adjunto un CROQUIS/plano dibujado a mano de UNA cocina concreta. "
            "Conviértelo en una FOTOGRAFÍA fotorrealista de ESA MISMA cocina, 100% FIEL al dibujo. "
            "Es un RE-RENDER del croquis, NO un diseño nuevo: copia lo que muestra el croquis.\n\n"
            "REPRODUCE EXACTAMENTE DEL CROQUIS:\n"
            "- La FORMA REAL del espacio (si hay dos paredes en ángulo formando una ESQUINA EN L, RENDERIZA UNA COCINA EN L. NUNCA la interpretes como una cocina lineal de una sola pared recta).\n"
            "- La POSICIÓN, el ORDEN de izquierda a derecha y el TAMAÑO RELATIVO de cada módulo (bajos, altos, columnas, lavadoras, hornos, microondas y pilar).\n"
            "- La UBICACIÓN EXACTA de la columna de horno/microondas, del frigorífico, del fregadero, de la placa, de la campana y del lavavajillas/lavadora en sus respectivas paredes y esquinas.\n"
            "- Las VENTANAS y PUERTAS en la MISMA pared y posición del croquis (no las muevas ni inventes ventanas nuevas).\n"
            "- Las medidas/proporciones anotadas: un módulo ancho debe verse ancho.\n\n"
            "ATENCIÓN CRÍTICA SI ES UNA COCINA EN L:\n"
            "Si el croquis muestra elementos en dos paredes en esquina (por ejemplo, placa/fregadero en el frente principal y columna/horno/micro/lavadora/pilar en la pared lateral en ángulo de 90°), DEBES RENDERIZAR AMBAS PAREDES FORMANDO ESQUINA EN L. Queda estrictamente prohibido colocar todo en una sola línea recta.\n\n"
            "PROHIBIDO: añadir, quitar, mover o redistribuir cualquier elemento que no esté en el croquis; "
            "inventar isla, ventana central o electrodomésticos extra; cambiar la distribución por otra que te parezca más bonita.\n\n"
            "IMPORTANTE: del texto de estilo de abajo usa SOLO colores, materiales y acabados. "
            "Si menciona isla, ventanas, campana, distribución o cualquier elemento que NO aparezca en el croquis, "
            "IGNÓRALO por completo — el CROQUIS manda sobre el texto.\n\n"
            f"Acabado/estilo a aplicar (SOLO materiales y colores) — Estilo: {estilo}; Materiales: {materiales}; "
            f"{payload.descripcion or ''}.\n\n"
            "Resultado: fotografía de interiorismo fotorrealista, iluminación natural realista, materiales PBR con textura real, "
            "perspectiva desde una esquina a la altura de los ojos (~160 cm) que muestre AMBAS PAREDES Y LA ESQUINA DE LA COCINA EN L, formato 16:9. "
            "Sin texto, marcas de agua ni logotipos."
        )

    # Adjuntar croquis si se proporcionó
    files = []
    if payload.croquis_b64:
        try:
            b64_data = payload.croquis_b64
            if b64_data.startswith("data:"):
                b64_data = b64_data.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_data)
            upload = await engine.upload_file(img_bytes, "croquis_cocina.png")
            if upload.get("success") and upload.get("file_id"):
                files.append({"file_id": upload["file_id"]})
        except Exception as e:
            logger.warning(f"No se pudo adjuntar croquis: {e}")

    # Motor GEMINI por defecto (mucho más fiel al croquis y devuelve la imagen
    # incrustada, sin proxy ni polling). Manus solo si se pide expresamente.
    _provider = (payload.provider or "gemini").lower()
    if _provider != "manus":
        try:
            from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
            if get_gemini_key() and GOOGLE_GENAI_AVAILABLE:
                ref_b64 = None
                if payload.croquis_b64:
                    ref_b64 = payload.croquis_b64.split(",", 1)[1] if payload.croquis_b64.startswith("data:") else payload.croquis_b64
                data_url = await generate_image_with_gemini(
                    prompt=instruccion,
                    reference_image_base64=ref_b64,
                    reference_mime="image/png",
                )
                if data_url:
                    return {
                        "imageUrl": data_url,
                        "images": [data_url],
                        "status": "completed",
                        "motor": "LuiggiAI",
                        "timestamp": int(time.time()),
                    }
                logger.warning("Gemini no devolvió imagen; se intenta con Manus.")
        except Exception as e:
            logger.warning(f"Render con Gemini falló ({e}); se intenta con Manus.")

    # Crear tarea en Manus API (respaldo o IA 2)
    task = await engine.create_task(
        prompt=instruccion,
        files=files if files else None,
    )

    if not task.get("success"):
        raise HTTPException(status_code=502, detail=task.get("error", "Error al crear tarea"))

    task_id = task["task_id"]

    if payload.modo_async:
        return {"task_id": task_id, "status": "running", "motor": task.get("engine")}

    # Esperar resultado (polling)
    resultado = await engine.wait_for_completion(task_id, timeout=300, poll_interval=4)

    if not resultado.get("success"):
        raise HTTPException(
            status_code=502,
            detail=resultado.get("error", "La tarea no se completó correctamente")
        )

    images = resultado.get("result", {}).get("images", [])
    return {
        "imageUrl": images[0] if images else None,
        "images": images,
        "task_id": task_id,
        "motor": resultado.get("engine"),
        "duracion_segundos": resultado.get("duration_seconds"),
        "timestamp": int(time.time()),
    }


@router.post("/render/editar")
async def editar_render(payload: EditarRenderInput):
    """
    Edita un render existente en lenguaje natural usando Manus API.
    Acepta la URL del render anterior o su base64.
    """
    engine = _get_engine()

    instruccion = (
        f"Edita este render de cocina siguiendo exactamente esta instrucción del proyectista: \"{payload.instruccion}\"\n\n"
        f"REQUISITOS OBLIGATORIOS:\n"
        f"- Mantén la distribución (en L / lineal / U), paredes y estructura del mueble inalteradas salvo lo solicitado\n"
        f"- Si se pide añadir una cafetera en la esquina, pequeño electrodoméstico o detalle de encimera, AÑÁDELO EN ESA POSICIÓN EXACTA\n"
        f"- Conserva la iluminación fotorrealista 8K y la calidad de los acabados\n"
        f"- Devuelve SOLO la imagen editada fotorrealista"
    )

    files = []

    # Subir imagen de referencia si viene en base64
    if payload.render_b64:
        try:
            b64_data = payload.render_b64
            if b64_data.startswith("data:"):
                b64_data = b64_data.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_data)
            upload = await engine.upload_file(img_bytes, "render_original.png")
            if upload.get("success") and upload.get("file_id"):
                files.append({"file_id": upload["file_id"]})
        except Exception as e:
            logger.warning(f"No se pudo subir render base64: {e}")

    # Motor GEMINI por defecto: edita "viendo" el render anterior (render_b64).
    _provider = (getattr(payload, "provider", None) or "gemini").lower()
    if _provider != "manus" and payload.render_b64:
        try:
            from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
            if get_gemini_key() and GOOGLE_GENAI_AVAILABLE:
                ref = payload.render_b64.split(",", 1)[1] if payload.render_b64.startswith("data:") else payload.render_b64
                data_url = await generate_image_with_gemini(
                    prompt=instruccion, reference_image_base64=ref, reference_mime="image/png",
                )
                if data_url:
                    return {"imageUrl": data_url, "images": [data_url], "status": "completed", "timestamp": int(time.time())}
        except Exception as e:
            logger.warning(f"Edición con Gemini falló ({e}); se intenta con Manus.")

    # Respaldo/IA 2: Manus (requiere motor activo)
    if not engine or engine.get_status().get("status") != "active":
        raise HTTPException(status_code=503, detail="Motor de IA no disponible.")

    # Si viene como URL, incluirla en el prompt
    if payload.render_url and not files:
        instruccion = f"Render de referencia: {payload.render_url}\n\n" + instruccion

    task = await engine.create_task(
        prompt=instruccion,
        files=files if files else None,
    )

    if not task.get("success"):
        raise HTTPException(status_code=502, detail=task.get("error"))

    task_id = task["task_id"]

    if payload.modo_async:
        return {"task_id": task_id, "status": "running"}

    resultado = await engine.wait_for_completion(task_id, timeout=300, poll_interval=4)
    if not resultado.get("success"):
        raise HTTPException(status_code=502, detail=resultado.get("error"))

    images = resultado.get("result", {}).get("images", [])
    return {
        "imageUrl": images[0] if images else None,
        "images": images,
        "task_id": task_id,
        "timestamp": int(time.time()),
    }


@router.post("/transcribir")
async def transcribir_audio(audio: UploadFile = File(...)):
    """
    Transcribe un audio (nota de voz del diseñador o del cliente) a texto
    usando Manus API. Soporta mp3, wav, m4a, webm, ogg.
    """
    engine = _get_engine()
    if not engine or engine.get_status().get("status") != "active":
        raise HTTPException(status_code=503, detail="Motor de IA no disponible.")

    audio_bytes = await audio.read()

    # Subir el audio a Manus
    upload = await engine.upload_file(audio_bytes, audio.filename or "audio.mp3")
    if not upload.get("success"):
        raise HTTPException(status_code=502, detail="No se pudo subir el audio.")

    instruccion = (
        "Transcribe exactamente el audio adjunto. "
        "Devuelve SOLO el texto transcrito, sin comentarios ni explicaciones adicionales. "
        "Si el audio describe medidas, distribución o materiales de una cocina, "
        "extráelos también en un formato estructurado al final."
    )

    task = await engine.create_task(
        prompt=instruccion,
        files=[{"file_id": upload["file_id"]}],
    )

    if not task.get("success"):
        raise HTTPException(status_code=502, detail=task.get("error"))

    resultado = await engine.wait_for_completion(task["task_id"], timeout=120, poll_interval=3)
    if not resultado.get("success"):
        raise HTTPException(status_code=502, detail=resultado.get("error"))

    # Extraer el texto del resultado
    mensajes = resultado.get("result", {}).get("messages", [])
    texto = ""
    for msg in mensajes:
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            contenido = msg.get("content", "")
            if isinstance(contenido, str):
                texto += contenido
            elif isinstance(contenido, list):
                for bloque in contenido:
                    if isinstance(bloque, dict) and bloque.get("type") == "text":
                        texto += bloque.get("text", "")

    return {"texto": texto.strip(), "task_id": task["task_id"]}


@router.get("/tarea/{task_id}")
async def consultar_tarea(task_id: str):
    """Consulta el estado de una tarea asíncrona."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Motor no disponible.")
    status = await engine.get_task_status(task_id)
    return status


@router.get("/tarea/{task_id}/resultado")
async def obtener_resultado(task_id: str):
    """Obtiene el resultado completo de una tarea completada."""
    engine = _get_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Motor no disponible.")
    messages = await engine.get_task_messages(task_id)
    images = messages.get("images", [])
    return {
        "task_id": task_id,
        "imageUrl": images[0] if images else None,
        "images": images,
        "messages": messages.get("messages", []),
    }


@router.post("/plano-2d")
async def generar_plano_2d(payload: ProyectoBase):
    """LA PLANTA: la cocina vista DESDE ARRIBA, acotada.

    Lo dijo el master: «donde pone planta, no está bien, lo que dibuja es un
    alzado; el alzado es visto de frente y la planta vista desde arriba, con
    cotas y medidas». Tenía razón, y la de antes fallaba por dos sitios:

    1. NO USABA LOS ANCHOS REALES. Pintaba módulos genéricos de 55 cm en un
       bucle y luego colocaba los elementos aparte, con un espaciado propio.
       Los rectángulos eran decoración y las etiquetas se amontonaban.
    2. SE INVENTABA EL FONDO DE LA ESTANCIA (`max(250, ancho*0,6)`), y lo
       rotulaba en un plano que pone «ESCALA 1:20».

    Los números los pone `services/planta_cocina.py`, que es cálculo puro y
    está probado. Aquí sólo se dibuja.
    """
    try:
        import io, base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        from services import planta_cocina as pc
        from services.kitchen_geometry import validar_distribucion, fondo_modulo, es_alto

        # LÍNEA RECTA, SIEMPRE. La planta es un plano de taller: se mide con
        # ella. El trazo temblado la deja «muy distorsionada y muy fea» —
        # palabras del master— y encima hace dudar de si esa pared está donde
        # parece. El lápiz se queda para el boceto en perspectiva, que es un
        # dibujo para enseñar, no para cortar.
        #
        # Se pone a None de ENTRADA y no solo en el `finally`: `path.sketch` es
        # un ajuste global del proceso, así que una petición anterior que lo
        # dejara puesto haría salir esta temblada sin que nadie lo pidiera y
        # sin dar ningún error. Se vio: un alzado con el boceto apagado salió
        # a lápiz.
        matplotlib.rcParams["path.sketch"] = None

        dist = payload.distribucion_estructurada
        if not dist or not dist.paredes:
            raise HTTPException(
                status_code=422,
                detail=("No puedo dibujar la planta sin las medidas de las "
                        "paredes. Elige la distribución (lineal, L, U…) y "
                        "escribe el ancho real de cada pared, o pulsa "
                        "«Detectar distribución» en el Estudio 3D."))

        _val = validar_distribucion({
            "tipo": getattr(dist, "tipo", "lineal") or "lineal",
            "paredes": dist.paredes or [],
            "elementos": dist.elementos or [],
        })
        if not _val.get("ok"):
            detalle = ("No puedo dibujar la planta con esas medidas de pared.")
            causa = " ".join(x for x in [(_val.get("motivo") or "").strip(),
                                         *(_val.get("avisos") or [])] if x).strip()
            raise HTTPException(status_code=422,
                                detail=f"{detalle} ({causa})" if causa else detalle)

        tipo = _val.get("tipo") or "lineal"
        g = pc.montar({"tipo": tipo, "paredes": _val["paredes"],
                       "elementos": _val["elementos"]},
                      fondo_modulo=fondo_modulo, es_alto=es_alto)
        if not g["muros"]:
            raise HTTPException(status_code=422,
                                detail="Ninguna pared trae ancho: no hay planta que dibujar.")

        C_LINE = "#2C2C2C"; C_BAJO = "#D4C5A9"; C_BORDE = "#8B7355"
        C_ALTO = "#8B7355"; C_COTA = "#B03A2E"; C_BG = "#F8F6F2"
        C_MURO = "#2C2C2C"; C_GRID = "#E6E2DA"
        _con_cotas = bool(getattr(payload, "con_cotas", True))

        fig, ax = plt.subplots(figsize=(15, 10))
        fig.patch.set_facecolor(C_BG); ax.set_facecolor(C_BG)
        ax.set_aspect("equal"); ax.axis("off")

        GRUESO_MURO = 8.0   # cm de pared dibujada (representación, no medida)

        def cota(p0, p1, sep, txt, lado=1):
            """Cota entre dos puntos, desplazada `sep` cm perpendicularmente."""
            if not _con_cotas:
                return
            (x0, y0), (x1, y1) = p0, p1
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n * sep * lado, dx / n * sep * lado
            ax.annotate("", xy=(x0 + nx, y0 + ny), xytext=(x1 + nx, y1 + ny),
                        arrowprops=dict(arrowstyle="<->", color=C_COTA, lw=0.9))
            ax.text((x0 + x1) / 2 + nx * 1.28, (y0 + y1) / 2 + ny * 1.28, txt,
                    ha="center", va="center", fontsize=7.5, color=C_COTA,
                    rotation=(0 if abs(dx) >= abs(dy) else 90))

        # ── Muros ───────────────────────────────────────────────────────────
        for muro in g["muros"]:
            (x0, y0), (x1, y1) = muro["desde"], muro["hasta"]
            nx, ny = muro["normal"]
            # El muro se dibuja HACIA FUERA de la estancia (al revés que los
            # muebles), que es como se representa en una planta.
            ax.add_patch(patches.Polygon(
                [(x0, y0), (x1, y1),
                 (x1 - nx * GRUESO_MURO, y1 - ny * GRUESO_MURO),
                 (x0 - nx * GRUESO_MURO, y0 - ny * GRUESO_MURO)],
                closed=True, facecolor=C_MURO, edgecolor=C_MURO, zorder=2))

        # ── Módulos, cada uno con SU ancho y SU fondo ────────────────────────
        for m in g["modulos"]:
            esq = m["esquinas"]
            if m["alto"]:
                # Los altos, a trazos y por encima: es como se marcan en planta.
                ax.add_patch(patches.Polygon(
                    esq, closed=True, fill=False, edgecolor=C_ALTO,
                    linewidth=1.0, linestyle="--", zorder=5))
            else:
                ax.add_patch(patches.Polygon(
                    esq, closed=True, facecolor=C_BAJO, edgecolor=C_BORDE,
                    linewidth=1.0, zorder=3))
                cx = sum(p[0] for p in esq) / 4
                cy = sum(p[1] for p in esq) / 4
                # El rótulo sólo si cabe: por debajo de 40 cm de ancho se lee
                # la cota, no la etiqueta. Antes se pintaban todos y salía un
                # borrón de texto encima de texto.
                if m["ancho"] >= 55:
                    dx, dy = m["direccion"]
                    ax.text(cx, cy, str(m["label"])[:14],
                            ha="center", va="center", fontsize=6,
                            color="#4A3F2F", zorder=6,
                            rotation=(0 if abs(dx) >= abs(dy) else 90))

        # ── Cotas: cada módulo y el total de la pared ────────────────────────
        for cad in g["cotas"]:
            muro = next(m for m in g["muros"] if m["indice"] == cad["pared"])
            (ox, oy) = muro["desde"]
            dx, dy = muro["direccion"]
            fondo_ref = max((m["fondo"] for m in g["modulos"]
                             if m["pared"] == cad["pared"] and not m["alto"]), default=60.0)
            # La PRIMERA pared se acota hacia dentro (por encima de sus
            # muebles); las demás, hacia FUERA. Si todas fueran hacia dentro,
            # en una L las dos cadenas se cruzan por el medio del dibujo y no
            # hay quien lea ninguna de las dos.
            lado = 1 if cad["pared"] == 0 else -1
            sep = (fondo_ref + 22) if lado == 1 else 22
            for t in cad["tramos"]:
                cota((ox + dx * t["desde"], oy + dy * t["desde"]),
                     (ox + dx * t["hasta"], oy + dy * t["hasta"]),
                     sep, f"{int(round(t['medida']))}", lado)
            cota((ox, oy), (ox + dx * cad["total"], oy + dy * cad["total"]),
                 sep + 30, f"{cad['nombre']}  {int(round(cad['total']))} cm", lado)

        # ── Encuadre ────────────────────────────────────────────────────────
        pts = [p for m in g["modulos"] for p in m["esquinas"]]
        pts += [muro["desde"] for muro in g["muros"]] + [muro["hasta"] for muro in g["muros"]]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        mx = max(max(xs) - min(xs), 1.0); my = max(max(ys) - min(ys), 1.0)
        # Margen ajustado: con 0,30 el dibujo quedaba perdido en medio de
        # una hoja casi vacia. Lo justo para que quepan las cadenas de cota.
        margen = max(mx, my) * 0.13
        ax.set_xlim(min(xs) - margen, max(xs) + margen)
        ax.set_ylim(min(ys) - margen, max(ys) + margen)

        # ── Rótulos y avisos ────────────────────────────────────────────────
        cab = (payload.nombre_cliente or "").strip()
        ax.set_title(f"PLANTA{' · ' + cab if cab else ''} — vista desde arriba · cotas en cm",
                     fontsize=11, fontweight="bold", color=C_LINE, pad=14)

        pie = []
        r = g.get("rincon")
        if r:
            pie.append(f"Rincón {int(round(r['ancho']))} × {int(round(r['fondo']))} cm")
        else:
            # NO se cierra la habitación por detrás: de una lineal sólo se
            # conoce el ancho de SU pared. Y se dice, para que nadie lea el
            # dibujo como si la estancia acabara ahí.
            pie.append("Fondo de la estancia no medido: la planta se dibuja alrededor de los muebles.")
        for d in pc.descuadres(g["cotas"]):
            pie.append(f"⚠ {d['nombre']}: {d['motivo']}")
        if g["omitidos"]:
            faltan = ", ".join(str(o.get("label") or o.get("id") or "?") for o in g["omitidos"][:4])
            pie.append(f"⚠ Sin dibujar por falta de datos: {faltan}")
        if pie:
            fig.text(0.5, 0.02, "\n".join(pie[:4]), ha="center", va="bottom",
                     fontsize=7.5, color=C_COTA, linespacing=1.6)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=C_BG)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"planoBase64": f"data:image/png;base64,{b64}",
                "tipo_distribucion": tipo,
                "modulos": len(g["modulos"]),
                "omitidos": g["omitidos"],
                "descuadres": pc.descuadres(g["cotas"]),
                "avisos": _val.get("avisos") or []}

    except HTTPException:
        # Un 422 con instrucciones NO puede acabar saliendo como un 500.
        raise
    except Exception as e:
        logger.error(f"plano-2d error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"No se pudo generar el plano: {e}")
    finally:
        # Si se queda puesto, la SIGUIENTE planta sale temblada sin que nadie
        # lo haya pedido, y eso no da error en ninguna parte: solo sale mal.
        try:
            import matplotlib as _mpl
            _mpl.rcParams["path.sketch"] = None
        except Exception:
            pass

@router.post("/ficha-tecnica")
async def generar_ficha_tecnica(payload: ProyectoBase):
    """Genera ficha técnica en Markdown usando datos reales del proyecto."""
    fecha = datetime.date.today().strftime("%d/%m/%Y")
    mes_anio = datetime.date.today().strftime("%B %Y")
    ref = f"COC-{datetime.date.today().strftime('%Y%m%d')}-{abs(hash(payload.nombre_cliente or '')) % 1000:03d}"

    # Obtener distribución estructurada
    dist = payload.distribucion_estructurada
    if dist and dist.tipo:
        dist_labels = {'lineal': 'Lineal', 'l': 'En L', 'u': 'En U',
                       'paralela': 'Paralela', 'isla': 'Con isla central', 'g': 'En G'}
        tipo_label = dist_labels.get(dist.tipo, dist.tipo.upper())
        paredes = dist.paredes or []
        isla = dist.isla or {}
        elementos = dist.elementos or []

        # Calcular metros lineales totales
        ml_total = sum(p.get('ancho', 0) for p in paredes) / 100
        if isla.get('ancho', 0) > 0:
            ml_total += (isla['ancho'] * 2 + isla.get('largo', 0) * 2) / 100

        medidas_section = f"| **Distribución** | {tipo_label} |"
        for i, p in enumerate(paredes):
            medidas_section += f"\n| **{p.get('nombre', f'Pared {i+1}')}** | {p.get('ancho', 0)} cm (ancho) × {p.get('alto', 240)} cm (alto) |"
        if isla.get('ancho', 0) > 0:
            medidas_section += f"\n| **Isla central** | {isla['ancho']} × {isla.get('largo', 0)} cm |"
        medidas_section += f"\n| **Metros lineales totales** | {ml_total:.1f} m.l. |"
    else:
        m = _parse_medidas(payload.medidas)
        tipo_label = 'Personalizada'
        medidas_section = f"| **Medidas** | {_fmt_medida(m['ancho'])}×{_fmt_medida(m['alto'])} cm |"
        if m['isla_w'] > 0:
            medidas_section += f"\n| **Isla** | {m['isla_w']}×{m['isla_h']} cm |"
        elementos = []
        paredes = []
        ml_total = (m['ancho'] + m['alto']) / 100

    # Parsear materiales del campo notas/descripción
    materiales_raw = payload.notas or payload.descripcion or ""
    mat_lines = [l.strip() for l in materiales_raw.replace('. ', '.\n').split('\n') if l.strip()]

    # Generar tabla de materiales dinámica
    mat_table = ""
    mat_keywords = {
        'frente': 'Frentes', 'lacado': 'Frentes', 'puerta': 'Frentes',
        'encimera': 'Encimera', 'silestone': 'Encimera', 'dekton': 'Encimera', 'granito': 'Encimera', 'cuarzo': 'Encimera',
        'tirador': 'Tiradores', 'gola': 'Tiradores', 'push': 'Tiradores',
        'suelo': 'Suelo', 'porcelánico': 'Suelo', 'tarima': 'Suelo',
        'zócalo': 'Zócalos',
    }
    materiales_detectados = {}
    for line in mat_lines:
        for kw, cat in mat_keywords.items():
            if kw in line.lower():
                materiales_detectados[cat] = line
                break

    if materiales_detectados:
        mat_table = "| Elemento | Material / Acabado |\n|:--|:--|\n"
        for cat, desc in materiales_detectados.items():
            mat_table += f"| **{cat}** | {desc} |\n"
    else:
        mat_table = """| Elemento | Material / Acabado |
|:--|:--|
| **Frentes** | Según selección del cliente |
| **Encimera** | Según selección del cliente |
| **Tiradores** | Según selección del cliente |
| **Suelo** | Existente / a definir |
"""

    # Generar sección de electrodomésticos basada en elementos reales
    electro_section = ""
    elem_labels = {e.get('id', ''): e.get('label', '') for e in elementos}
    if elementos:
        electro_section = "## Electrodomésticos Incluidos\n\n"
        for el in elementos:
            eid = el.get('id', '')
            label = el.get('label', eid)
            ancho = el.get('ancho', 60)
            pared_idx = el.get('pared_idx', 0)
            pared_nombre = paredes[pared_idx].get('nombre', f'Pared {pared_idx+1}') if pared_idx < len(paredes) else 'Pared principal'
            electro_section += f"- **{label}** ({ancho} cm) — ubicado en {pared_nombre}\n"
    else:
        electro_section = """## Electrodomésticos

*A definir según necesidades del cliente.*
"""

    # Generar instalaciones basadas en elementos
    inst_section = "## Instalaciones Necesarias\n\n| Elemento | Especificación |\n|:--|:--|\n"
    if 'fregadero' in elem_labels or not elementos:
        inst_section += "| **Toma de agua** | Fría + caliente + desagüe bajo fregadero |\n"
    if 'placa' in elem_labels or 'horno' in elem_labels or not elementos:
        inst_section += "| **Ventilación** | Salida de humos ∅150 mm o recirculación |\n"
    if 'lavavajillas' in elem_labels:
        inst_section += "| **Lavavajillas** | Toma de agua + desagüe + enchufe dedicado |\n"
    inst_section += f"| **Enchufes** | 1 cada 120 cm a 110 cm del suelo (línea 16A) |\n"
    inst_section += f"| **Iluminación** | LED 3.000K bajo muebles altos |\n"

    md = f"""# Ficha Técnica — Cocina {payload.estilo or 'Moderna'} · {payload.nombre_cliente or 'Cliente'}

| | |
|:--|:--|
| **Referencia** | `{ref}` |
| **Fecha** | {fecha} |
| **Cliente** | {payload.nombre_cliente or '—'} |
| **Estilo** | {payload.estilo or 'Moderno'} |
{medidas_section}
| **Presupuesto** | {payload.presupuesto or 'A consultar'} |

---

## Descripción del Proyecto

{payload.descripcion or f"Proyecto de diseño de cocina estilo {payload.estilo or 'moderno'} para {payload.nombre_cliente or 'el cliente'}."}

{f"> **Notas del cliente:** {payload.notas}" if payload.notas else ""}

---

## Materiales y Acabados

{mat_table}

---

{electro_section}

---

{inst_section}

---

## Proceso y Plazos

| Fase | Descripción | Plazo estimado |
|:--|:--|:--|
| **Diseño y aprobación** | Renders, planos y selección de materiales | Semana 1–2 |
| **Fabricación** | Producción de muebles a medida | Semana 2–5 |
| **Instalación** | Montaje y conexión de electrodomésticos | Semana 6–7 |
| **Entrega** | Revisión final y documentación | Semana 8 |

---

*Ficha generada automáticamente · 3D Estudio · {mes_anio}*
"""
    return {"fichaMarkdown": md, "referencia": ref, "fecha": fecha}


@router.post("/presentacion")
async def generar_presentacion(payload: ProyectoBase):
    """Genera presentación HTML para cliente usando datos reales del proyecto."""
    fecha = datetime.date.today().strftime("%d/%m/%Y")
    estilo = payload.estilo or "Moderno"
    cliente = payload.nombre_cliente or "Cliente"
    presupuesto = payload.presupuesto or "A consultar"
    descripcion = payload.descripcion or f"Una cocina de diseño {estilo.lower()} pensada para adaptarse perfectamente a su espacio y estilo de vida."
    notas = payload.notas or ""

    # Obtener distribución estructurada
    dist = payload.distribucion_estructurada
    if dist and dist.tipo:
        dist_labels = {'lineal': 'Lineal', 'l': 'En L', 'u': 'En U',
                       'paralela': 'Paralela', 'isla': 'Con isla central', 'g': 'En G'}
        tipo_label = dist_labels.get(dist.tipo, dist.tipo.upper())
        paredes = dist.paredes or []
        elementos = dist.elementos or []
        medidas_str = ' + '.join([f"{p.get('nombre','')}: {p.get('ancho',0)}cm" for p in paredes])
        dist_card = f"Distribución {tipo_label} con {len(paredes)} pared{'es' if len(paredes) > 1 else ''}"
        electro_card = f"{len(elementos)} electrodoméstico{'s' if len(elementos) != 1 else ''} integrado{'s' if len(elementos) != 1 else ''}: " + ', '.join([e.get('label','') for e in elementos[:3]]) if elementos else 'A definir según necesidades'
    else:
        m = _parse_medidas(payload.medidas)
        medidas_str = f"{_fmt_medida(m['ancho'])}×{_fmt_medida(m['alto'])} cm"
        tipo_label = 'Personalizada'
        dist_card = 'Optimizada para el flujo de trabajo'
        electro_card = 'Alta gama totalmente integrados'
        elementos = []
        paredes = []

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Propuesta Cocina — {cliente}</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Montserrat',sans-serif;background:#111;color:#D4C5A9;scroll-behavior:smooth}}
  section{{width:100%;min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:80px 10%;border-bottom:1px solid #222}}
  section:nth-child(even){{background:#0D0D0D}}
  .accent{{color:#C8A96E}}
  .line{{width:60px;height:3px;background:#C8A96E;margin-bottom:24px}}
  h1{{color:#fff;font-size:clamp(2rem,5vw,3.5rem);font-weight:900;line-height:1.1;margin-bottom:16px}}
  h2{{color:#fff;font-size:clamp(1.4rem,3vw,2rem);font-weight:700;margin-bottom:32px;text-transform:uppercase;letter-spacing:2px}}
  p{{font-size:1.05rem;line-height:1.9;margin-bottom:16px;max-width:800px;color:#C0B090}}
  table{{width:100%;border-collapse:collapse;margin-top:24px;max-width:960px}}
  th{{color:#C8A96E;font-size:.8rem;text-transform:uppercase;letter-spacing:2px;padding-bottom:16px;border-bottom:2px solid #C8A96E;text-align:left;padding-right:16px}}
  td{{padding:16px 16px 16px 0;border-bottom:1px solid rgba(200,169,110,.15);font-size:.95rem;color:#C0B090;vertical-align:top}}
  td:first-child{{color:#fff;font-weight:600;width:28%}}
  .badge{{display:inline-block;background:rgba(200,169,110,.12);color:#C8A96E;font-size:.7rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;padding:6px 18px;margin-bottom:28px;border:1px solid rgba(200,169,110,.3)}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:40px;max-width:960px;margin-top:16px}}
  .card{{background:rgba(200,169,110,.06);border:1px solid rgba(200,169,110,.15);padding:28px}}
  .card h3{{color:#C8A96E;font-size:.85rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px}}
  .card p{{font-size:.9rem;color:#A09070;margin:0}}
  footer{{text-align:center;padding:80px 10%;background:#080808}}
  footer p{{color:#555;font-size:.85rem;margin:6px 0}}
  footer .brand{{color:#fff;font-size:1.3rem;font-weight:700;margin-bottom:16px}}
</style>
</head>
<body>
<section style="background:linear-gradient(135deg,#111 50%,#1A1508 100%)">
  <div class="badge">Propuesta de Diseño · {fecha}</div>
  <div class="line"></div>
  <h1>Cocina <span class="accent">{estilo}</span></h1>
  <h1 style="font-size:clamp(1.2rem,3vw,2rem);font-weight:300;color:#888">{cliente}</h1>
  <p style="margin-top:48px;color:#666;font-size:.9rem">3D Estudio · {fecha}</p>
</section>
<section>
  <div class="line"></div>
  <h2>Su nueva cocina</h2>
  <p>{descripcion}</p>
  <p><strong class="accent">Medidas:</strong> {medidas_str}</p>
  {f'<p><strong class="accent">Notas:</strong> {notas}</p>' if notas else ''}
  <div class="grid2" style="margin-top:40px">
    <div class="card"><h3>Distribución</h3><p>{dist_card}</p></div>
    <div class="card"><h3>Materiales</h3><p>Primera calidad con garantía de 10 años en todos los elementos fabricados</p></div>
    <div class="card"><h3>Electrodomésticos</h3><p>{electro_card}</p></div>
    <div class="card"><h3>Iluminación</h3><p>LED funcional bajo muebles + ambiental decorativa</p></div>
  </div>
</section>
<section>
  <div class="line"></div>
  <h2>Materiales y acabados</h2>
  <table>
    <thead><tr><th>Elemento</th><th>Material / Acabado</th><th>Característica clave</th></tr></thead>
    <tbody>
      <tr><td>Frentes bajos</td><td>Laca seda anti-huellas</td><td>Resistente a arañazos y humedad</td></tr>
      <tr><td>Frentes altos</td><td>Chapa de roble natural</td><td>Calidez y textura real, sostenible</td></tr>
      <tr><td>Encimera</td><td>Silestone Calacatta Gold 20 mm</td><td>Antibacteriano, sin sellado periódico</td></tr>
      <tr><td>Tiradores</td><td>Sistema Gola integrado</td><td>Sin interrupciones visuales</td></tr>
      <tr><td>Suelo</td><td>Porcelánico gran formato 120×60</td><td>Fácil limpieza, alta durabilidad</td></tr>
    </tbody>
  </table>
</section>
<section>
  <div class="line"></div>
  <h2>Proceso y plazos</h2>
  <p>Precio cerrado, sin sorpresas. Duración estimada: <strong class="accent">6 a 8 semanas</strong> desde la firma del contrato.</p>
  <table>
    <thead><tr><th>Fase</th><th>Descripción</th><th>Plazo</th></tr></thead>
    <tbody>
      <tr><td>Diseño</td><td>Renders definitivos, planos y selección de materiales</td><td>Semana 1–2</td></tr>
      <tr><td>Fabricación</td><td>Producción de muebles a medida en fábrica propia</td><td>Semana 2–5</td></tr>
      <tr><td>Instalación</td><td>Montaje, conexión de electrodomésticos y acabados</td><td>Semana 6–7</td></tr>
      <tr><td>Entrega</td><td>Revisión final con el cliente y entrega de documentación</td><td>Semana 8</td></tr>
    </tbody>
  </table>
  {f'<p style="margin-top:32px"><strong class="accent">Inversión estimada:</strong> {presupuesto}</p>' if presupuesto != "A consultar" else ""}
</section>
<footer>
  <div class="line" style="margin:0 auto 24px"></div>
  <p class="brand">3D Estudio</p>
  <p>Visita de medición gratuita · Propuesta en 48h · Garantía 2 años instalación</p>
</footer>
</body>
</html>"""

    return {"presentacionHtml": html, "cliente": cliente, "fecha": fecha}


# ─── Modelo para instalaciones ────────────────────────────────────────────────
class InstalacionesInput(BaseModel):
    medidas: Optional[str] = Field(default="400x350cm")
    descripcion: Optional[str] = Field(default="")
    estilo: Optional[str] = Field(default="Moderno")
    nombre_cliente: Optional[str] = Field(default="Cliente")
    distribucion_estructurada: Optional[DistribucionEstructurada] = Field(
        default=None, description="Distribución real: de ella salen los puntos")


@router.post("/instalaciones")
async def generar_instalaciones(payload: InstalacionesInput):
    """Plan de instalaciones (eléctrica, fontanería, gas) DERIVADO de la cocina.

    Este papel lo usa el instalador para hacer rozas antes de alicatar, así que
    cada punto sale de un módulo que EXISTE y lleva su posición en cm desde el
    inicio de la pared. Antes era una plantilla fija: listaba circuito de
    lavavajillas y de frigorífico hubiera o no, y colocaba los enchufes "cada
    120 cm en la pared norte" sin saber qué había delante.
    """
    from services.instalaciones_cocina import (
        NORMATIVA, plan_electrico, plan_fontaneria, plan_gas)
    from services.kitchen_geometry import validar_distribucion

    m = _medidas_para_dibujo(payload.medidas)
    dist = payload.distribucion_estructurada
    elementos, paredes, avisos = [], [], []
    if dist and (dist.paredes or dist.elementos):
        val = validar_distribucion({
            "tipo": getattr(dist, "tipo", "lineal") or "lineal",
            "paredes": dist.paredes or [],
            "elementos": dist.elementos or [],
        })
        elementos = val.get("elementos") or []
        paredes = val.get("paredes") or []
        avisos = val.get("avisos") or []

    if not elementos:
        # Sin distribución NO se inventa una cocina para colgar de ella los
        # puntos: se dice qué falta. Un plano de instalaciones equivocado se
        # paga picando pared.
        raise HTTPException(
            status_code=422,
            detail=("No puedo hacer el plano de instalaciones sin saber qué muebles "
                    "hay y dónde. Genera antes la distribución (elige el tipo de "
                    "cocina y sus medidas, o pulsa «Detectar distribución» en el "
                    "Estudio 3D) y vuelve a intentarlo."))

    ancho_pared = int(paredes[0]["ancho"]) if paredes else int(m["ancho"])
    con_isla = bool(m["isla_w"] > 0 and m["isla_h"] > 0) or \
        str(getattr(dist, "tipo", "") or "").lower() == "isla"

    electrica = plan_electrico(elementos, ancho_pared, con_isla)
    fontaneria = plan_fontaneria(elementos, con_isla)
    gas = plan_gas(elementos, payload.descripcion or "")

    notas = (
        f"Pared de {ancho_pared} cm. Cotas horizontales medidas desde el inicio de "
        f"la pared (izquierda); alturas desde el suelo acabado. "
        f"Encimera a {int(94)} cm. Dejar rozas antes de alicatar. " + NORMATIVA
    )
    return {
        "electrica": electrica,
        "fontaneria": fontaneria,
        "gas": gas,
        "notas": notas,
        "avisos": avisos,
        "pared_cm": ancho_pared,
        "medidas_parseadas": m,
        "cliente": payload.nombre_cliente,
        "fecha": datetime.date.today().strftime("%d/%m/%Y"),
    }


# ─── Galería de renders ────────────────────────────────────────────────────────

from bson import ObjectId as _ObjectId
from services.db_client import get_db as _get_db

_galeria_db = _get_db()["renders_galeria"]  # colección compartida (singleton)


class GaleriaGuardarPayload(BaseModel):
    image_url: str
    cliente: str = ""
    descripcion: str = ""
    estilo: str = ""
    medidas: str = ""
    presupuesto: str = ""


@router.post("/galeria/guardar")
async def galeria_guardar(payload: GaleriaGuardarPayload, current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda un render generado en la galería MongoDB."""
    user_id = (current_user or {}).get("id")
    doc = {
        "image_url": payload.image_url,
        "cliente": payload.cliente,
        "descripcion": payload.descripcion,
        "estilo": payload.estilo,
        "medidas": payload.medidas,
        "presupuesto": payload.presupuesto,
        "fecha": datetime.datetime.utcnow(),
        "favorito": False,
        "userId": user_id,
    }
    result = await _galeria_db.insert_one(doc)
    return {"ok": True, "id": str(result.inserted_id)}


@router.get("/galeria")
async def galeria_listar(
    cliente: str = "",
    estilo: str = "",
    page: int = 1,
    limit: int = 20,
):
    """Lista los renders guardados en la galería con paginación."""
    query: dict = {}
    if cliente:
        query["cliente"] = {"$regex": cliente, "$options": "i"}
    if estilo:
        query["estilo"] = estilo
    skip = (page - 1) * limit
    cursor = _galeria_db.find(query).sort("fecha", -1).skip(skip).limit(limit)
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("fecha"), datetime.datetime):
            doc["fecha"] = doc["fecha"].strftime("%d/%m/%Y %H:%M")
        docs.append(doc)
    total = await _galeria_db.count_documents(query)
    return {
        "renders": docs,
        "total": total,
        "page": page,
        "pages": max(1, -(-total // limit)),
    }


@router.delete("/galeria/{render_id}")
async def galeria_eliminar(render_id: str):
    """Elimina un render de la galería."""
    try:
        oid = _ObjectId(render_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")
    result = await _galeria_db.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Render no encontrado")
    return {"ok": True}


@router.patch("/galeria/{render_id}/favorito")
async def galeria_favorito(render_id: str):
    """Alterna el estado de favorito de un render."""
    try:
        oid = _ObjectId(render_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")
    doc = await _galeria_db.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Render no encontrado")
    nuevo_fav = not doc.get("favorito", False)
    await _galeria_db.update_one({"_id": oid}, {"$set": {"favorito": nuevo_fav}})
    return {"ok": True, "favorito": nuevo_fav}


# ─────────────────────────────────────────────────────────────────────────────
# AGENTES DISEÑADORES EN PARALELO
# Permite lanzar 2-7 proyectos de diseño simultáneos, cada uno con su propio
# agente Manus que genera render + ficha técnica + presupuesto estimado.
# ─────────────────────────────────────────────────────────────────────────────

class AgenteProyectoInput(BaseModel):
    """Datos de un proyecto individual para el agente diseñador."""
    nombre_cliente: str = Field(..., description="Nombre del cliente")
    medidas: Optional[str] = Field(default="400x350cm", description="Medidas de la cocina")
    estilo: Optional[str] = Field(default="Moderno", description="Estilo de diseño")
    descripcion: Optional[str] = Field(default="", description="Descripción adicional")
    presupuesto: Optional[str] = Field(default="", description="Presupuesto orientativo")
    notas: Optional[str] = Field(default="", description="Materiales y notas")


class AgentesLoteInput(BaseModel):
    """Lote de proyectos para lanzar en paralelo."""
    proyectos: List[AgenteProyectoInput] = Field(..., description="Lista de proyectos (2-7)")
    provider: Optional[str] = Field(default=None, description="Motor: manus (por defecto) | gemini")


class AgenteEstado(BaseModel):
    """Estado de un agente en ejecución."""
    task_id: str
    nombre_cliente: str
    status: str  # pending | running | completed | error
    imageUrl: Optional[str] = None
    error: Optional[str] = None
    duracion_segundos: Optional[float] = None


def _build_agente_prompt(proyecto: AgenteProyectoInput) -> str:
    """Construye el prompt completo para el agente diseñador."""
    presupuesto_txt = f"\nPRESUPUESTO ORIENTATIVO: {proyecto.presupuesto}" if proyecto.presupuesto else ""
    notas_txt = f"\nMATERIALES Y NOTAS: {proyecto.notas}" if proyecto.notas else ""
    return (
        f"Eres un diseñador de cocinas de lujo. Genera un render fotorrealista de alta gama para el siguiente proyecto:\n\n"
        f"CLIENTE: {proyecto.nombre_cliente}\n"
        f"MEDIDAS: {proyecto.medidas}\n"
        f"ESTILO: {proyecto.estilo}\n"
        f"DESCRIPCIÓN: {proyecto.descripcion or 'Cocina moderna de alta gama'}"
        f"{presupuesto_txt}"
        f"{notas_txt}\n\n"
        f"REQUISITOS DEL RENDER:\n"
        f"- Render fotorrealista 8K, iluminación cinematográfica natural\n"
        f"- Perspectiva angular desde esquina, formato 16:9\n"
        f"- Calidad de revista de interiorismo de lujo (AD, Elle Decoration)\n"
        f"- Texturas hiper-detalladas, materiales con profundidad y reflexión\n"
        f"- Electrodomésticos integrados visibles\n"
        f"- Devuelve SOLO la imagen generada, sin texto adicional"
    )


async def _lanzar_gemini(proyecto, idx: int) -> dict:
    """Genera el render con el motor alternativo (Gemini) de forma síncrona y
    devuelve el agente ya 'completado' con la imagen incrustada (sin polling)."""
    base = {"task_id": f"gem-{int(time.time())}-{idx}", "nombre_cliente": proyecto.nombre_cliente,
            "estilo": proyecto.estilo, "medidas": proyecto.medidas}
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            return {**base, "status": "error", "error": "Motor alternativo no disponible."}
        prompt = _build_agente_prompt(proyecto)
        data_url = await asyncio.wait_for(generate_image_with_gemini(prompt), timeout=180)
        if data_url:
            return {**base, "status": "completed", "imageUrl": data_url}
        return {**base, "status": "error", "error": "El motor no devolvió imagen."}
    except asyncio.TimeoutError:
        return {**base, "status": "error", "error": "El motor tardó demasiado."}
    except Exception as e:
        logger.error(f"agente gemini error: {e}")
        return {**base, "status": "error", "error": "No se pudo generar el render."}


async def _lanzar_manus(engine, proyecto) -> dict:
    """Crea la tarea en Manus con tiempo límite y devuelve el agente en 'running'."""
    base = {"task_id": None, "nombre_cliente": proyecto.nombre_cliente,
            "estilo": proyecto.estilo, "medidas": proyecto.medidas}
    try:
        prompt = _build_agente_prompt(proyecto)
        task = await asyncio.wait_for(engine.create_task(prompt=prompt), timeout=30)
    except asyncio.TimeoutError:
        return {**base, "status": "error", "error": "El motor tardó demasiado en iniciar. Reinténtalo."}
    except Exception as e:
        logger.error(f"agente manus error: {e}")
        return {**base, "status": "error", "error": "No se pudo iniciar el render."}
    if task.get("success"):
        return {**base, "task_id": task["task_id"], "status": "running"}
    return {**base, "status": "error", "error": task.get("error", "Error al crear tarea")}


@router.post("/agentes/lanzar")
async def lanzar_agentes(payload: AgentesLoteInput):
    """
    Lanza múltiples agentes diseñadores en paralelo (1-7 proyectos).
    Crea las tareas de forma CONCURRENTE y con tiempo límite para responder rápido
    (evita que una llamada lenta al motor deje la petición colgada → NetworkError).
    """
    if len(payload.proyectos) < 1 or len(payload.proyectos) > 7:
        raise HTTPException(status_code=400, detail="Se permiten entre 1 y 7 proyectos simultáneos.")

    provider = (payload.provider or "manus").lower()

    if provider == "gemini":
        agentes = await asyncio.gather(*[
            _lanzar_gemini(p, i) for i, p in enumerate(payload.proyectos)
        ])
    else:
        engine = _get_engine()
        if not engine or engine.get_status().get("status") != "active":
            raise HTTPException(status_code=503, detail="Motor de IA no disponible.")
        agentes = await asyncio.gather(*[
            _lanzar_manus(engine, p) for p in payload.proyectos
        ])

    return {
        "ok": True,
        "total": len(agentes),
        "agentes": list(agentes),
        "timestamp": int(time.time()),
    }


@router.get("/agentes/{task_id}/estado")
async def estado_agente(task_id: str):
    """
    Consulta el estado de un agente diseñador individual.
    Devuelve status + imageUrl si está completado.
    """
    engine = _get_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Motor no disponible.")

    status_resp = await engine.get_task_status(task_id)
    task_status = status_resp.get("status", "unknown")

    if task_status == "stopped":
        messages = await engine.get_task_messages(task_id)
        images = messages.get("images", [])
        return {
            "task_id": task_id,
            "status": "completed",
            "imageUrl": images[0] if images else None,
            "images": images,
        }
    elif task_status == "error":
        return {
            "task_id": task_id,
            "status": "error",
            "error": status_resp.get("error", "La tarea falló."),
        }
    else:
        return {
            "task_id": task_id,
            "status": "running",
            "manus_status": task_status,
        }


@router.post("/agentes/lote-estado")
async def estado_lote_agentes(body: dict):
    """
    Consulta el estado de múltiples agentes a la vez.
    Recibe {"task_ids": ["id1", "id2", ...]} y devuelve el estado de cada uno.
    """
    task_ids = body.get("task_ids", [])
    if not task_ids:
        return {"agentes": []}

    engine = _get_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Motor no disponible.")

    resultados = []
    for task_id in task_ids:
        status_resp = await engine.get_task_status(task_id)
        task_status = status_resp.get("status", "unknown")

        if task_status == "stopped":
            messages = await engine.get_task_messages(task_id)
            images = messages.get("images", [])
            resultados.append({
                "task_id": task_id,
                "status": "completed",
                "imageUrl": images[0] if images else None,
            })
        elif task_status == "error":
            resultados.append({
                "task_id": task_id,
                "status": "error",
                "error": status_resp.get("error", "Error"),
            })
        else:
            resultados.append({
                "task_id": task_id,
                "status": "running",
            })

    return {"agentes": resultados, "timestamp": int(time.time())}


@router.post("/alzado")
async def generar_alzado(payload: ProyectoBase):
    """Vista ALÁMBRICA acotada (alzado por pared) para el dossier técnico:
    bajos/altos/columnas en wireframe con cotas de anchos por módulo, alturas
    estándar (zócalo 10, encimera 90, altos 140–210) y etiquetas de elementos.
    Generación local con matplotlib (sin IA)."""
    try:
        import io, base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        # ── BOCETO A MANO ALZADA ────────────────────────────────────────────
        # El dibujo es EXACTAMENTE EL MISMO: los mismos módulos, los mismos
        # anchos y las mismas cotas. Lo único que cambia es el trazo, que pasa
        # a temblar como el de un lápiz.
        #
        # Por qué así y no pidiéndole a una IA que "dibuje a mano" el render:
        # una IA redibuja, y al redibujar mueve cosas. Un boceto se lee como
        # "esto lo ha dibujado el diseñador", así que un módulo desplazado ahí
        # tiene MÁS autoridad que en un render, no menos. Aquí no hay nada que
        # inventar: sale de la misma distribución validada que el alzado
        # técnico, así que cuadra por construcción.
        #
        # Se usa `path.sketch` (ondulado del trazo) y NO `plt.xkcd()`, que
        # además cambia la tipografía y depende de una fuente que puede no
        # estar instalada en el servidor: las cotas tienen que leerse siempre.
        # LÍNEA RECTA, SIEMPRE. Ver la nota de la planta: el alzado es un
        # plano de taller y el temblor lo afea y lo hace dudoso. Se pone a None
        # de ENTRADA, no solo en el `finally`, porque el ajuste es global del
        # proceso y una petición anterior podría haberlo dejado puesto.
        matplotlib.rcParams["path.sketch"] = None

        # Vista alámbrica: paleta CAD en blanco y negro puro (estilo TeoWin) cuando
        # se pide `monocromo`; si no, la paleta de color habitual.
        _mono = bool(getattr(payload, "monocromo", False))
        if _mono:
            C_LINE = "#000000"; C_COTA = "#000000"; C_BG = "#FFFFFF"; C_GRID = "#D9D9D9"
            C_FRENTE = "#000000"; C_ENCH = "#000000"; C_HERRAJE = "#000000"
        else:
            C_LINE = "#2C2C2C"; C_COTA = "#B03A2E"; C_BG = "#FFFFFF"; C_GRID = "#E6E2DA"
            C_FRENTE = "#8A6D3B"; C_ENCH = "#1F6FB2"; C_HERRAJE = "#3F3F3F"
        _con_cotas = bool(getattr(payload, "con_cotas", True))
        # Geometría REAL de fabricación (una sola fuente de verdad: kitchen_geometry).
        # Antes estas constantes no cuadraban con sus propios rótulos (la línea a 86
        # se rotulaba "90" y una cota de 76 cm decía "80"). Ahora todo se DERIVA:
        from services.kitchen_geometry import (
            CASCO_BAJO_ALTO, ALTOS_ALTURAS, COLUMNA_ALTURAS,
            ZOCALO_ALTO_MIN, ENCIMERA_GRUESO_MAX, SEPARACION_ENCIMERA_ALTOS_MIN,
            cota_de_ancho,
        )
        ZOC_Y = ZOCALO_ALTO_MIN                      # 10  · cara superior del zócalo
        ENC_Y = ZOC_Y + CASCO_BAJO_ALTO              # 90  · cara superior del casco bajo
        ENC_TOP = ENC_Y + ENCIMERA_GRUESO_MAX        # 94  · cara superior de la encimera
        ALTOS_Y1 = COLUMNA_ALTURAS[1]                # 220 · los altos rasan con la columna
        ALTOS_Y0 = ALTOS_Y1 - ALTOS_ALTURAS[0]       # 150 · alto de 70 cm
        COL_Y = COLUMNA_ALTURAS[1]                   # 220
        _SEP_ALTOS = ALTOS_Y0 - ENC_TOP              # separación encimera→altos (56 cm)
        # Autocomprobación: si alguien cambia una constante y la geometría deja de ser
        # fabricable, se ve aquí en vez de salir un plano incoherente.
        if not (SEPARACION_ENCIMERA_ALTOS_MIN - 1 <= _SEP_ALTOS <= 65):
            logger.warning("alzado: separación encimera→altos fuera de norma (%s cm)", _SEP_ALTOS)
        COLS = {"frigorifico", "columna_hornos", "despensa", "congelador"}
        ALTOS = {"microondas"}  # la campana se dibuja SIEMPRE sobre la placa (abajo)
        HOB = {"placa", "cocina", "vitroceramica", "vitro", "induccion", "placa_induccion", "coccion", "vitroceramicamica"}
        DRAWERS = {"cajonera", "cajones", "gavetas", "cajon", "gaveta", "cacerolero", "cubertero"}
        SINK = {"fregadero", "seno", "lavabo"}

        def _frentes_gavetas(body_h, label_tipo):
            """Alturas (cm) de los frentes de una cajonera, de arriba abajo.

            Enteras y sumando EXACTAMENTE el cuerpo. Antes salían 15,2 y 32,4:
            un frente no se corta a décimas de centímetro, y encima la suma no
            cerraba el módulo. El cajón superior va más bajo (es el de cubiertos)
            y el sobrante de la división entera se reparte por arriba.
            """
            t = (label_tipo or "").lower()
            n = 3
            for k in ("4", "cuatro"):
                if k in t: n = 4
            for k in ("2", "dos"):
                if k in t and "cajon" in t: n = 3  # 2 gavetas + 1 cajon
            body = int(round(body_h))
            top = max(12, int(round(body * 0.19)))   # cajón superior ~19%
            resto = (body - top) // (n - 1)
            fondos = [resto] * (n - 1)
            top += body - top - sum(fondos)          # el descuadre, al de arriba
            return [top] + fondos

        dist = payload.distribucion_estructurada
        # NUNCA inventar una pared por defecto (antes caía a 400x240 en silencio, lo
        # que producía cotas falsas). Sin medidas válidas NO se dibuja: se avisa.
        from services.kitchen_geometry import validar_distribucion
        _val = validar_distribucion({
            "tipo": getattr(dist, "tipo", "lineal") if dist else "lineal",
            "paredes": (dist.paredes if dist and dist.paredes else []) or [],
            "elementos": (dist.elementos if dist else []) or [],
        })
        if not _val.get("ok"):
            # Sin paredes NO se dibuja (regla de oro: no se inventa una cota). Pero
            # el aviso tiene que decir QUÉ HACER: antes solo decía que no había
            # medidas válidas y el usuario se quedaba mirando un error sin salida.
            detalle = ("No se puede dibujar el alzado sin las medidas de las paredes. "
                       "Elige la distribución (lineal, L, U…) en el panel de la "
                       "izquierda y escribe el ancho real de cada pared; o pulsa "
                       "«Detectar distribución» en el Estudio 3D para deducirlas.")
            causa = " ".join(x for x in [(_val.get("motivo") or "").strip(),
                                         *(_val.get("avisos") or [])] if x).strip()
            if causa:
                detalle += f" ({causa})"
            raise HTTPException(status_code=422, detail=detalle)
        paredes = _val["paredes"]
        elementos = _val["elementos"]
        _avisos_geom = _val.get("avisos") or []

        n = len(paredes)
        fig, axes = plt.subplots(n, 1, figsize=(14, 4.6 * n))
        if n == 1:
            axes = [axes]
        fig.patch.set_facecolor(C_BG)

        def wire(ax, x, y, w, h, dash=False, lw=1.4):
            ax.add_patch(patches.Rectangle((x, y), w, h, fill=False, edgecolor=C_LINE,
                                           linewidth=lw, linestyle="--" if dash else "-", zorder=3))

        def puerta_x(ax, x, y, w, h):
            ax.plot([x, x + w], [y, y + h], color=C_LINE, lw=0.5, ls=":", zorder=3)
            ax.plot([x, x + w], [y + h, y], color=C_LINE, lw=0.5, ls=":", zorder=3)

        # Tiradores (herraje visible por FUERA del mueble).
        def tirador_h(ax, cx, y, length=13):   # tirador horizontal (frentes de cajón)
            ax.plot([cx - length / 2, cx + length / 2], [y, y], color=C_HERRAJE,
                    lw=2.4, zorder=6, solid_capstyle="round")
        def tirador_v(ax, x, cy, length=15):    # tirador vertical (puertas)
            ax.plot([x, x], [cy - length / 2, cy + length / 2], color=C_HERRAJE,
                    lw=2.4, zorder=6, solid_capstyle="round")

        def cota_h(ax, x0, x1, y, txt):
            ax.annotate("", xy=(x0, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="<->", color=C_COTA, lw=0.9))
            ax.text((x0 + x1) / 2, y + 4, txt, ha="center", va="bottom", fontsize=7.5, color=C_COTA)

        def _cm_por_caracter(ax, fontsize):
            """Cuántos cm de dibujo ocupa un carácter en este eje.

            No se puede estimar a ojo: el eje va con `aspect="equal"`, así que la
            escala real la impone el lado que más aprieta (aquí el alto, no el
            ancho). Suponer "unos 2,6 cm por letra" es lo que hacía que
            "Placa vitrocerámica" se saliera de un módulo de 60 cm. Esto se
            deriva de la figura, que es la única que sabe cuánto mide un punto.
            """
            fig = ax.figure
            ancho_in, alto_in = fig.get_size_inches()
            caja = ax.get_position()
            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()
            pulg_por_cm = min((ancho_in * caja.width) / max(x1 - x0, 1e-6),
                              (alto_in * caja.height) / max(y1 - y0, 1e-6))
            # Un carácter de una fuente proporcional ocupa ~0,6 × su cuerpo.
            return (fontsize * 0.6 / 72.0) / max(pulg_por_cm, 1e-9)

        def _texto_vertical(ax, cx, cy, txt, largo_disponible, color=None):
            """Rótulo girado 90º, recortado a lo que mide el módulo A LO ALTO.

            Girado, el hueco no es el ancho del mueble sino su altura. Sin este
            recorte, "Columna horno y microondas" en una columna se salía por
            arriba y por abajo y se metía en las cotas.
            """
            cabe = max(4, int(largo_disponible * 0.92 / _cm_por_caracter(ax, 6.5)))
            t = str(txt).replace("\n", " · ")
            # Fondo opaco detrás del rótulo. Girado, el texto cruza la línea de
            # encimera, las diagonales de las puertas y los frentes de los
            # cajones: sin taparlas, «Mueble bajo» se leía encima del «16» de la
            # altura del cajón y no se entendía ninguno de los dos.
            ax.text(cx, cy, t if len(t) <= cabe else t[:max(1, cabe - 1)] + "…",
                    ha="center", va="center", fontsize=6.5, rotation=90,
                    color=color or C_LINE, zorder=6,
                    bbox=dict(facecolor=C_BG, edgecolor="none", pad=1.2))

        def _texto_modulo(ax, x, w, cy, txt):
            """Etiqueta dentro del módulo, ajustada a lo ancho que sea.

            Con módulos estrechos el texto horizontal se salía por los lados y se
            pisaba con el del vecino: en el alzado del 05/08 se leía
            "Mueble fregadeMueble altoMueble bajMueble alto". Por debajo de 45 cm
            se gira 90º, que es como se rotula un módulo estrecho en un plano.
            """
            if w >= 45:
                cabe = max(4, int(w * 0.92 / _cm_por_caracter(ax, 6.5)))
                # PARTIR POR PALABRAS ANTES DE CORTAR. Se recortaba a lo bruto y
                # el plano salía lleno de «Bajo frega…», «Lavavaji…», «Mueble
                # alto 2…»: al taller media palabra no le sirve, y a lo alto del
                # módulo sobra sitio para una segunda línea.
                lineas = []
                for parte in str(txt).split("\n"):
                    if len(parte) <= cabe:
                        lineas.append(parte)
                        continue
                    actual = ""
                    for palabra in parte.split(" "):
                        if not actual:
                            actual = palabra
                        elif len(actual) + 1 + len(palabra) <= cabe:
                            actual += " " + palabra
                        else:
                            lineas.append(actual)
                            actual = palabra
                    if actual:
                        lineas.append(actual)
                # Una palabra suelta más larga que el módulo sí hay que cortarla.
                lineas = [l if len(l) <= cabe else l[:max(1, cabe - 1)] + "…" for l in lineas]
                # Con fondo, por lo mismo que el rótulo girado: dentro de una
                # cajonera el texto cae encima de las líneas de los frentes.
                ax.text(x + w / 2, cy, "\n".join(lineas), ha="center", va="center",
                        fontsize=6.5, zorder=6,
                        bbox=dict(facecolor=C_BG, edgecolor="none", pad=1.2))
            elif w >= 22:
                _texto_vertical(ax, x + w / 2, cy, txt, ENC_Y - ZOC_Y)
            # Por debajo de 22 cm no cabe ni girado: lo dice la cota, no la etiqueta.

        herr = {"puertas": 0, "cajones": 0}  # recuento de herraje para el resumen
        propuestos = 0   # altos DERIVADOS: se dibujan, pero no se piden
        for idx, (ax, pared) in enumerate(zip(axes, paredes)):
            ancho = int(pared.get("ancho") or 400)
            alto = int(pared.get("alto") or 240)
            ax.set_facecolor(C_BG); ax.set_aspect("equal"); ax.axis("off")
            ax.set_xlim(-70, ancho + 78); ax.set_ylim(-58, alto + 40)
            # contorno de pared y líneas guía
            wire(ax, 0, 0, ancho, alto, lw=2)
            for gy in (ZOC_Y, ENC_Y, ALTOS_Y0, ALTOS_Y1):
                ax.plot([0, ancho], [gy, gy], color=C_GRID, lw=0.6, zorder=1)

            elems = sorted([e for e in elementos if e.get("pared_idx", 0) == idx],
                           key=lambda e: e.get("posicion_cm", 0) or 0)
            # La campana se sitúa ANTES de dibujar nada: va sobre la placa por
            # física, y ahí no puede haber un mueble alto. Calcularla al final
            # hacía que se pintara ENCIMA de un alto ya dibujado.
            zonas_campana = [(int(e.get("posicion_cm") or 0), int(e.get("ancho") or 60))
                             for e in elems
                             if str(e.get("id") or "").lower() in HOB]
            pos = 0
            # UN CONTADOR POR FILA. `pos` solo avanzaba con los BAJOS (está
            # dentro de su rama), así que un ALTO sin `posicion_cm` cogía ese
            # `pos` y NO lo movía: dos altos seguidos se dibujaban EXACTAMENTE
            # uno encima del otro, con sus rótulos y sus cotas pisándose
            # («Muebl€Mueble a…» y «60 60» amontonados). Es el mismo fallo que
            # tenían la perspectiva y la planta: altos y bajos son dos filas y
            # cada una corre por su cuenta.
            pos_alto = 0
            cotas = []
            hob_zones = []   # (x, w) de las placas → la campana va justo encima
            bajos_xy = []    # (x, w) de los bajos REALES → los altos se alinean con ellos
            altos_xy = []    # (x, w) de los altos que vienen DADOS (no derivados)
            cotas_altos = [] # cotas de la fila colgada, que van sobre los altos
            hay_estimadas = False  # ¿alguna cota de esta pared es una estimación?
            hay_sin_medir = False  # ¿alguna no se sabe siquiera estimar?
            for e in elems:
                # DE DÓNDE SALE CADA COTA: escrita («60»), estimada («~60»)
                # o desconocida («?»). Quién lo decide vive en
                # `kitchen_geometry.cota_de_ancho`, que es donde está escrita la
                # regla de la casa y donde se puede probar de verdad. Hasta el
                # 23/08 el tercer caso se rotulaba «~60» con un 60 que no había
                # medido ni deducido nadie: era el respaldo del código pasando
                # por estimación del dibujo.
                w, cota_w, _origen = cota_de_ancho(e)
                hay_estimadas = hay_estimadas or _origen == "estimada"
                hay_sin_medir = hay_sin_medir or _origen == "sin_dato"
                tipo = str(e.get("id") or e.get("tipo") or "").lower()
                fila = str(e.get("fila") or "bajo").lower()
                if tipo == "campana":
                    continue  # se dibuja al final, centrada sobre la placa
                label = str(e.get("label") or tipo or "módulo")[:18]
                # Cada fila arranca donde acabó el anterior DE SU FILA. Si la
                # detección trae una posición concreta, manda esa.
                _es_fila_alta = (fila == "alto" or tipo in ALTOS)
                x = int(e.get("posicion_cm") or (pos_alto if _es_fila_alta else pos))
                if tipo in COLS:
                    wire(ax, x, ZOC_Y, w, COL_Y - ZOC_Y); puerta_x(ax, x, ZOC_Y, w, COL_Y - ZOC_Y)
                    _texto_vertical(ax, x + w / 2, (ZOC_Y + COL_Y) / 2, label, COL_Y - ZOC_Y)
                    # Tiradores verticales de la columna (puerta superior e inferior).
                    tirador_v(ax, x + w - 5, ZOC_Y + (COL_Y - ZOC_Y) * 0.30, length=18)
                    tirador_v(ax, x + w - 5, ZOC_Y + (COL_Y - ZOC_Y) * 0.72, length=18)
                    herr["puertas"] += 2
                elif (fila == "alto" or tipo in ALTOS) and any(
                        min(cx + cw, x + w) - max(cx, x) > w * 0.5
                        for (cx, cw) in zonas_campana):
                    # La campana se come más de medio módulo: ahí no cabe el alto.
                    # (Rozarla no basta: un alto de 60 no desaparece porque le
                    # pisen 10 cm; en obra se estrecha, no se quita.)
                    continue
                elif fila == "alto" or tipo in ALTOS:
                    # Fila COLGADA. Antes un "Mueble alto" caía en el `else` y se
                    # dibujaba a ras de suelo, rotulado "30×80": un alto no mide
                    # 80 de alto (son 70 o 90) ni se apoya en el zócalo.
                    wire(ax, x, ALTOS_Y0, w, ALTOS_Y1 - ALTOS_Y0)
                    _ta = f"{label}\n{cota_w}×{ALTOS_Y1 - ALTOS_Y0}" if _con_cotas else label
                    _texto_modulo(ax, x, w, (ALTOS_Y0 + ALTOS_Y1) / 2, _ta)
                    tirador_v(ax, x + w - 5, ALTOS_Y0 + 12, length=16)
                    herr["puertas"] += 1
                    altos_xy.append((x, w))
                elif tipo in DRAWERS:
                    body_h_cm = ENC_Y - ZOC_Y  # altura útil del cuerpo (cm de dibujo)
                    wire(ax, x, ZOC_Y, w, body_h_cm)
                    fronts = _frentes_gavetas(body_h_cm, label)
                    yy = ENC_Y
                    for fh in fronts:
                        yy -= fh
                        ax.plot([x, x + w], [yy, yy], color=C_FRENTE, lw=0.8, zorder=3)
                        # La cota del frente va PEGADA AL CANTO IZQUIERDO, no en
                        # el centro: en el centro es donde va el nombre del
                        # módulo, y los dos se pisaban («16» encima de «Mueble
                        # bajo», y ninguno se leía).
                        if _con_cotas and w >= 40:
                            ax.text(x + 4, yy + fh / 2, f"{fh:g}", ha="left", va="center",
                                    fontsize=6, color=C_FRENTE)
                        # Tirador horizontal centrado, junto al canto superior del frente.
                        tirador_h(ax, x + w / 2, yy + fh - 3, length=min(16, w * 0.5))
                        herr["cajones"] += 1
                    # Dentro del módulo, no debajo: ahí abajo están las cotas y se
                    # pisaban ("Módulo bajo cajone…" encima del 10 del zócalo).
                    # Y en horizontal si el módulo es ancho: girar el rótulo de
                    # una cajonera de 90 cm no lo hacía más legible, lo hacía
                    # menos. `_texto_modulo` ya decide gira/no gira por el ancho.
                    _texto_modulo(ax, x, w, (ZOC_Y + ENC_Y) / 2, label)
                else:
                    wire(ax, x, ZOC_Y, w, ENC_Y - ZOC_Y); puerta_x(ax, x, ZOC_Y, w, ENC_Y - ZOC_Y)
                    _txt = f"{label}\n{w}×{ENC_Y - ZOC_Y}" if _con_cotas else label
                    _texto_modulo(ax, x, w, (ZOC_Y + ENC_Y) / 2, _txt)
                    # Tirador vertical de la puerta del bajo (salvo bajo placa/cocción).
                    if tipo not in HOB:
                        tirador_v(ax, x + w - 5, ENC_Y - 14, length=16)
                        herr["puertas"] += 1
                    if tipo in HOB:
                        hob_zones.append((x, w))
                        # marca de zona de cocción sobre la encimera
                        ax.plot([x + 6, x + w - 6], [ENC_Y - 2, ENC_Y - 2], color=C_LINE, lw=1.0)
                if _es_fila_alta:
                    cotas_altos.append((x, x + w, cota_w))
                    pos_alto = max(pos_alto, x + w)
                else:
                    cotas.append((x, x + w, cota_w))
                    if tipo not in COLS:
                        bajos_xy.append((x, w))  # para alinear los altos con los bajos
                    pos = max(pos, x + w)

            # CAMPANA: siempre centrada JUSTO ENCIMA de cada placa, con su mismo ancho.
            for (hx, hw) in hob_zones:
                wire(ax, hx, ALTOS_Y0, hw, ALTOS_Y1 - ALTOS_Y0, lw=1.6)
                # boca de campana (línea inferior más marcada)
                ax.plot([hx + 4, hx + hw - 4], [ALTOS_Y0 + 4, ALTOS_Y0 + 4], color=C_LINE, lw=1.4)
                ax.text(hx + hw / 2, (ALTOS_Y0 + ALTOS_Y1) / 2, "Campana", ha="center", va="center", fontsize=7)

            # NO se inventan módulos: el validador de geometría garantiza que los
            # módulos suman el ancho de pared (si falta hueco, llega como "relleno"
            # explícito). Antes aquí se rellenaba con módulos de 60 cm inventados y
            # se les ponía cota como si fueran reales.
            # ALTOS: se alinean con los BAJOS reales (misma anchura y posición),
            # saltando columnas y la zona de campana sobre la placa.
            # ...pero SOLO si la distribución no traía altos propios. Si el
            # análisis ya dijo qué altos hay y dónde, añadir otros "supuestos"
            # es inventarse muebles que nadie ha pedido (CLAUDE.md: no se
            # inventa nada). Los derivados son la ayuda para cuando no hay
            # ningún alto declarado, no un extra permanente.
            for (bx, bw) in (bajos_xy if not altos_xy else []):
                ocupado_col = any(str(t.get("id") or "").lower() in COLS
                                  and (t.get("posicion_cm") or 0) < bx + bw
                                  and (t.get("posicion_cm") or 0) + (t.get("ancho") or 0) > bx
                                  for t in elems)
                ocupado_camp = any(hx < bx + bw and hx + hw > bx for (hx, hw) in hob_zones)
                # Si en ese tramo ya hay un alto REAL, no se dibuja otro encima.
                ocupado_alto = any(ax0 < bx + bw and ax0 + aw > bx for (ax0, aw) in altos_xy)
                if not (ocupado_col or ocupado_camp or ocupado_alto):
                    wire(ax, bx, ALTOS_Y0, bw, ALTOS_Y1 - ALTOS_Y0, dash=True)
                    tirador_v(ax, bx + bw - 5, ALTOS_Y0 + 12, length=16)
                    # DICE QUE ES UNA PROPUESTA. Se dibujaban en discontinuo y
                    # sin rótulo: una fila de cajas vacías encima de los bajos,
                    # que en el papel se lee como «aquí van altos» aunque nadie
                    # los haya pedido. Con la palabra puesta, se sabe qué es.
                    _texto_modulo(ax, bx, bw, (ALTOS_Y0 + ALTOS_Y1) / 2, "Alto\n(propuesto)")
                    # Y NO se cuentan en el herraje: ese recuento se usa para
                    # pedir bisagras y tiradores, y estos muebles puede que no
                    # existan. Un pedido de más se paga.
                    propuestos += 1
            # encimera y zócalo
            ax.plot([0, ancho], [ENC_Y, ENC_Y], color=C_LINE, lw=2.2, zorder=4)
            ax.plot([0, ancho], [ZOC_Y, ZOC_Y], color=C_LINE, lw=1.2, zorder=4)
            # COTAS: solo si se piden (la vista alámbrica "limpia" va sin ellas).
            if _con_cotas:
                def _cadena_de_cotas(lista, y_base, sentido=1):
                    """Dibuja una cadena de cotas escalonando las que no caben.

                    Dos módulos estrechos y contiguos escribían sus números
                    pegados y se leía "2060" en vez de "20" y "60". Cuando el
                    número no cabe en su tramo, baja (o sube) un escalón.
                    """
                    ancho_num = _cm_por_caracter(ax, 7.5)
                    ultimo_alto = -1e9
                    for (x0, x1, t) in lista:
                        estrecho = (x1 - x0) < len(t) * ancho_num * 1.6
                        # Solo se escalona si el anterior no estaba ya escalonado,
                        # para no hacer una escalera infinita.
                        escalon = 1 if (estrecho and x0 > ultimo_alto) else 0
                        if escalon:
                            ultimo_alto = x1
                        cota_h(ax, x0, x1, y_base - sentido * escalon * 9, t)

                _cadena_de_cotas(cotas, -12, sentido=1)
                cota_h(ax, 0, ancho, -40, f"{ancho} cm")
                # Las cotas de la fila colgada van SOBRE los altos: mezclarlas con
                # las de suelo daba una tira que no sumaba el ancho de la pared.
                _cadena_de_cotas(cotas_altos, ALTOS_Y1 + 5, sentido=-1)
                for gy, t in ((ZOC_Y, str(ZOC_Y)), (ENC_TOP, str(ENC_TOP)), (ALTOS_Y0, str(ALTOS_Y0)),
                              (ALTOS_Y1, str(ALTOS_Y1)), (alto, str(alto))):
                    ax.text(-10, gy, t, ha="right", va="center", fontsize=7, color=C_COTA)
                    ax.plot([-6, 0], [gy, gy], color=C_COTA, lw=0.8)
                # cota VERTICAL de alturas (lado derecho): zócalo / bajo / alto
                xc = ancho + 14

                def cota_v(y0, y1, txt, carril=0):
                    """Cota vertical. `carril` la separa de las demás.

                    Las cuatro compartían la misma vertical y sus textos se
                    escribían unos encima de otros: en el alzado del 05/08 se leía
                    "246", que era el 240 de la pared pisando el 56 de la
                    separación. Ahora van escalonadas, como una cadena de cotas.
                    """
                    xx = xc + carril * 15
                    ax.annotate("", xy=(xx, y0), xytext=(xx, y1),
                                arrowprops=dict(arrowstyle="<->", color=C_COTA, lw=0.9))
                    ax.text(xx + 3.5, (y0 + y1) / 2, txt, ha="left", va="center", fontsize=7,
                            color=C_COTA, rotation=90)
                for yy in (ZOC_Y, ENC_Y, ALTOS_Y0, ALTOS_Y1):
                    ax.plot([ancho, xc + 2], [yy, yy], color=C_COTA, lw=0.4, ls=":")
                # El TEXTO se calcula del propio dibujo: nunca puede mentir.
                cota_v(ZOC_Y, ENC_Y, f"{ENC_Y - ZOC_Y}", 0)              # cuerpo del bajo (80)
                cota_v(ENC_TOP, ALTOS_Y0, f"{_SEP_ALTOS}", 0)            # encimera → altos (56)
                cota_v(ALTOS_Y0, ALTOS_Y1, f"{ALTOS_Y1 - ALTOS_Y0}", 0)  # alto (70)
                cota_v(0, alto, f"{alto}", 1)                            # altura total pared
            # ENCHUFES sobre la encimera (franja salpicadero), evitando zona de placa
            ench_y = (ENC_Y + ALTOS_Y0) / 2
            ex = 45
            while ex < ancho - 20:
                sobre_hob = any(hx - 5 <= ex <= hx + hw + 5 for (hx, hw) in hob_zones)
                sobre_col = any(str(t.get("id") or "").lower() in COLS
                                and (t.get("posicion_cm") or 0) <= ex <= (t.get("posicion_cm") or 0) + (t.get("ancho") or 60)
                                for t in elems)
                if not (sobre_hob or sobre_col):
                    ax.add_patch(patches.Rectangle((ex - 4, ench_y - 4), 8, 8, fill=False,
                                                   edgecolor=C_ENCH, linewidth=1.1, zorder=5))
                    ax.plot([ex - 1.6, ex - 1.6], [ench_y - 1.6, ench_y + 1.6], color=C_ENCH, lw=1.0, zorder=5)
                    ax.plot([ex + 1.6, ex + 1.6], [ench_y - 1.6, ench_y + 1.6], color=C_ENCH, lw=1.0, zorder=5)
                ex += 90
            ax.text(0, alto + 12, f"ALZADO S{idx + 1} — {pared.get('nombre') or f'Pared {idx + 1}'} · escala orientativa · cotas en cm",
                    fontsize=9, fontweight="bold", color=C_LINE)
            # LA LEYENDA DE LA TILDE. Una marca que nadie sabe leer no protege
            # a nadie: quien recibe el papel tiene que saber, sin preguntar, que
            # Dos marcas que explicar: «~60» es una cota deducida del dibujo y
            # hay que confirmarla antes de cortar; «?» es un módulo cuyo ancho
            # no se ha podido leer y hay que ir a medirlo. La leyenda solo se
            # escribe si hay alguna de las dos, para no ensuciar un alzado
            # enteramente acotado — una advertencia que sobra deja de leerse.
            if _con_cotas and (hay_estimadas or hay_sin_medir):
                _avisos = []
                if hay_estimadas:
                    _avisos.append("Las cotas con ~ son ESTIMADAS del dibujo, no medidas escritas")
                if hay_sin_medir:
                    _avisos.append("las marcadas ? NO SE HAN PODIDO LEER y hay que medirlas")
                ax.text(0, alto + 5,
                        " · ".join(_avisos) + ": confírmalas antes de cortar.",
                        fontsize=6.8, color=C_COTA)

        # Resumen de herraje (recuento aproximado a partir de puertas y cajones).
        puertas = herr["puertas"]; cajones = herr["cajones"]
        bisagras = puertas * 2                 # 2 bisagras por puerta (estándar)
        guias = cajones                        # 1 juego de guías por frente de cajón
        tiradores = puertas + cajones          # 1 tirador por puerta y por frente
        resumen = (f"HERRAJE (aprox.):  {puertas} puertas · {cajones} cajones/gavetas   |   "
                   f"{bisagras} bisagras · {guias} juegos de guías · {tiradores} tiradores")
        # Los altos propuestos NO entran en el recuento —con este papel se pide
        # el herraje— pero se dice cuántos hay, para que se confirmen o se
        # quiten a propósito y no pasen inadvertidos.
        if propuestos:
            resumen += (f"   |   + {propuestos} alto(s) PROPUESTO(S) sin confirmar "
                        f"(no incluidos en el herraje)")
        fig.text(0.5, 0.005, resumen, ha="center", va="bottom", fontsize=8.5,
                 color=C_HERRAJE, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#F3F1EC", ec=C_HERRAJE, lw=0.8))

        buf = io.BytesIO()
        plt.tight_layout(pad=1.2, rect=(0, 0.03, 1, 1))
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=C_BG)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"alzadoBase64": f"data:image/png;base64,{b64}", "paredes": len(paredes),
                "avisos": _avisos_geom,
                "herraje": {"puertas": puertas, "cajones": cajones, "bisagras": bisagras,
                            "guias": guias, "tiradores": tiradores}}
    except HTTPException:
        # Un 422 con instrucciones ("elige la distribución") NO puede acabar
        # convertido en un 500 genérico: HTTPException hereda de Exception, así
        # que sin esto el `except` de abajo se lo tragaba y el usuario leía
        # "no se pudo generar" con un "422:" incrustado dentro.
        raise
    except Exception as e:
        logger.error(f"alzado error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"No se pudo generar la vista alámbrica: {e}")
    finally:
        # `path.sketch` es global: si se queda puesto, el SIGUIENTE alzado sale
        # temblando sin que nadie lo haya pedido.
        try:
            import matplotlib as _mpl
            _mpl.rcParams["path.sketch"] = None
        except Exception:
            pass


@router.post("/perspectiva")
async def generar_perspectiva(payload: ProyectoBase):
    """BOCETO EN PERSPECTIVA a lápiz, dibujado desde los datos.

    Lo que el master pidió enseñando sus referencias: un dibujo de interior con
    profundidad y punto de fuga, no el alzado plano.

    Cada arista sale de un ancho o una altura REALES (`services/perspectiva.py`,
    que es cálculo puro y está probado). NO se le pide a una IA que lo dibuje:
    una IA redibuja, y al redibujar mueve cosas — y en un boceto eso es peor
    que en un render, porque un dibujo a lápiz se lee como «esto lo ha hecho el
    diseñador» y un módulo desplazado ahí tiene MÁS autoridad, no menos.

    Sin cotas, y a propósito: es un boceto de presentación. Las medidas van en
    el alzado acotado, que es el que baja al taller.
    """
    try:
        import io, base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from services import perspectiva as pe
        from services.kitchen_geometry import (
            validar_distribucion, altura_modulo, fondo_modulo, es_alto,
        )

        _boceto = bool(getattr(payload, "boceto", True))
        # El trazo tiembla más que en el alzado: aquí no hay cotas que leer, y
        # las referencias del master son dibujos a mano, no planos temblados.
        matplotlib.rcParams["path.sketch"] = (2.6, 100.0, 18.0) if _boceto else None

        dist = payload.distribucion_estructurada
        _val = validar_distribucion({
            "tipo": getattr(dist, "tipo", "lineal") if dist else "lineal",
            "paredes": (dist.paredes if dist and dist.paredes else []) or [],
            "elementos": (dist.elementos if dist else []) or [],
        })
        if not _val.get("ok"):
            # Mismo criterio que el alzado: sin paredes NO se dibuja, y el
            # aviso dice QUÉ HACER, no solo que no salió.
            detalle = ("No se puede dibujar la perspectiva sin las medidas de "
                       "las paredes. Elige la distribución (lineal, L, U…) y "
                       "escribe el ancho real de cada pared; o pulsa «Detectar "
                       "distribución» en el Estudio 3D para deducirlas.")
            causa = " ".join(x for x in [(_val.get("motivo") or "").strip(),
                                         *(_val.get("avisos") or [])] if x).strip()
            if causa:
                detalle += f" ({causa})"
            raise HTTPException(status_code=422, detail=detalle)

        escena = {"tipo": _val.get("tipo") or "lineal",
                  "paredes": _val["paredes"], "elementos": _val["elementos"]}

        cajas, omitidos = pe.montar_escena(
            escena, altura_modulo=altura_modulo, fondo_modulo=fondo_modulo,
            es_alto=es_alto)
        # ENCIMERA Y ZÓCALO. Sin ellos el dibujo son cajas apiladas: una cocina
        # sin encimera no existe, y unos bajos que arrancan del suelo se leen
        # como muebles apoyados en el aire.
        cajas = cajas + pe.encimera_y_zocalo(cajas)
        if not cajas:
            raise HTTPException(
                status_code=422,
                detail="Ningún módulo tiene ancho, así que no hay nada que "
                       "dibujar. Revisa la distribución: un boceto con muebles "
                       "de ancho inventado sería peor que no tenerlo.")

        cam = pe.camara_para(escena)
        cascaron = pe.suelo_y_paredes(escena)

        C_LAPIZ = "#2B2B2B"; C_SUAVE = "#9A9A9A"; C_BG = "#FCFBF7"
        fig, ax = plt.subplots(figsize=(13, 8.4))
        fig.patch.set_facecolor(C_BG)
        ax.set_facecolor(C_BG)
        ax.set_aspect("equal"); ax.axis("off")

        def proy(p):
            return pe.proyectar(p, cam)

        def linea(a, b, color, lw, alpha=1.0, z=3):
            pa, pb = proy(a), proy(b)
            # Un punto detrás de la cámara NO se acerca: la arista no se dibuja.
            # Proyectarlo daría una figura del revés, que es como se cuelan los
            # dibujos imposibles.
            if pa is None or pb is None:
                return
            ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color=color, lw=lw,
                    alpha=alpha, zorder=z, solid_capstyle="round")

        # 1. El suelo: las líneas que van al punto de fuga. Van primero y flojas.
        for a, b in cascaron["suelo"]:
            linea(a, b, C_SUAVE, 0.5, alpha=0.45, z=1)

        # 2. Las paredes REALES (las que tienen ancho y alto de verdad).
        for muro in cascaron["paredes"]:
            e = muro["esquinas"]
            for i in range(4):
                linea(e[i], e[(i + 1) % 4], C_SUAVE, 0.9, alpha=0.75, z=2)

        # 3. Los muebles, de lejos a cerca: lo cercano tapa a lo lejano. Sin
        #    este orden el fondo se pinta encima y el dibujo se lee al revés.
        ARISTAS = ((0, 1), (1, 2), (2, 3), (3, 0),        # cara contra la pared
                   (4, 5), (5, 6), (6, 7), (7, 4),        # cara vista
                   (0, 4), (1, 5), (2, 6), (3, 7))        # fondo
        # CADA MUEBLE EN SU PROPIA CAPA.
        #
        # Estaba ordenado por profundidad y NO SERVÍA DE NADA: los zorder eran
        # fijos para todos (relleno 3, aristas 4, tirador 5), y matplotlib pinta
        # por zorder, no por orden de bucle. O sea que el relleno de un mueble
        # CERCANO quedaba debajo de las aristas de uno LEJANO. De ahí que la
        # cocina se viera transparente —se leía el interior de cada mueble— y
        # que los tiradores cruzaran de un mueble a otro.
        #
        # Con una capa por mueble, el orden de profundidad manda de verdad.
        ATRAS = ((0, 1), (1, 2), (2, 3), (3, 0))          # cara contra la pared
        FRENTE = ((4, 5), (5, 6), (6, 7), (7, 4))         # cara vista
        # LAS ARISTAS DE FONDO VAN POR DEBAJO DE TODOS LOS RELLENOS.
        #
        # Son las que dan la profundidad, pero entre dos muebles contiguos no se
        # ven: las tapa el mueble de al lado. Dibujadas por encima asomaban como
        # diagonales sueltas en cada esquina, y el dibujo parecía roto.
        #
        # Poniéndolas debajo de todo, el relleno del vecino las tapa solo y
        # quedan únicamente las de los extremos del tramo — que es exactamente
        # lo que se ve en una cocina de verdad. Sin detectar vecinos ni resolver
        # esquinas: lo hace el propio orden de pintado.
        FONDO = ((0, 4), (1, 5), (2, 6), (3, 7))
        Z_FONDO = 2.5
        for _n, c in enumerate(pe.ordenar_por_profundidad(cajas, cam)):
            e = c["esquinas"]
            z0 = 3 + _n * 4
            # Las aristas de ATRÁS van DEBAJO del relleno, y por eso el mueble
            # se ve cerrado. Dibujadas encima, como estaban, se veía el interior
            # y cada mueble parecía una vitrina.
            # UNA ENCIMERA ES CONTINUA. Se dibuja por tramos (uno por mueble),
            # así que sus aristas VERTICALES son juntas que en obra no existen:
            # se saltan y los tramos se leen como una sola losa. Igual el
            # zócalo, que corre de punta a punta.
            continua = bool(c.get("sin_tirador"))
            atras = ((0, 1), (2, 3)) if continua else ATRAS
            frente = ((4, 5), (6, 7)) if continua else FRENTE
            for i, j in atras:
                linea(e[i], e[j], C_LAPIZ, 1.25, z=z0)
            cara = [proy(e[i]) for i in (4, 5, 6, 7)]
            if all(p is not None for p in cara):
                ax.fill([p[0] for p in cara], [p[1] for p in cara],
                        facecolor=C_BG, edgecolor="none", zorder=z0 + 1)
            for i, j in frente:
                linea(e[i], e[j], C_LAPIZ, 1.25, z=z0 + 2)
            for i, j in FONDO:
                linea(e[i], e[j], C_LAPIZ, 1.25, z=Z_FONDO)
            # Tirador: una raya. Es lo que hace que se lea como un mueble y no
            # como una caja.
            p0, p1 = proy(e[4]), proy(e[5])
            p3 = proy(e[7])
            # Una encimera y un zócalo no llevan tirador.
            if c.get("sin_tirador"):
                p0 = None
            if p0 and p1 and p3:
                t = 0.72 if c["base"] < 100 else 0.28   # bajos abajo, altos arriba
                ax.plot([p0[0] + (p1[0] - p0[0]) * 0.12, p0[0] + (p1[0] - p0[0]) * 0.88],
                        [p0[1] + (p3[1] - p0[1]) * t, p1[1] + (p3[1] - p1[1]) * t],
                        color=C_LAPIZ, lw=1.6, zorder=z0 + 3, solid_capstyle="round")

        # ENCUADRE. Lo manda la COCINA, nunca el suelo: las líneas de suelo
        # llegan casi hasta el ojo y ahí la proyección se dispara, así que si
        # se las deja opinar sobre los límites del eje la cocina acaba del
        # tamaño de un sello en una esquina. Se enmarca por muebles y paredes,
        # y el suelo se recorta solo (matplotlib recorta al eje).
        interes = []
        for c in cajas:
            interes += [proy(p) for p in c["esquinas"]]
        for muro in cascaron["paredes"]:
            interes += [proy(p) for p in muro["esquinas"]]
        interes = [p for p in interes if p is not None]
        if interes:
            xs = [p[0] for p in interes]; ys = [p[1] for p in interes]
            mx, my = (max(xs) - min(xs)) or 1.0, (max(ys) - min(ys)) or 1.0
            # Margen generoso por abajo: es donde entra el suelo, que es lo que
            # da la profundidad. Por arriba basta con no rozar el techo.
            ax.set_xlim(min(xs) - mx * 0.10, max(xs) + mx * 0.10)
            # El suelo daba profundidad, sí, pero con 0.55 se comía MEDIA
            # LÁMINA y la cocina quedaba arrinconada arriba. Con 0.20 sigue
            # habiendo suelo y la cocina es la protagonista, que es lo que se
            # está enseñando.
            ax.set_ylim(min(ys) - my * 0.20, max(ys) + my * 0.12)

        cab = (payload.nombre_cliente or "").strip()
        titulo = f"{cab} · boceto" if cab else "Boceto en perspectiva"
        fig.text(0.5, 0.955, titulo, ha="center", va="top", fontsize=11,
                 color=C_LAPIZ, fontweight="bold")
        fig.text(0.5, 0.035, "Boceto de presentación · sin cotas · "
                 "las medidas van en el alzado acotado",
                 ha="center", va="bottom", fontsize=7.5, color=C_SUAVE)

        # Lo que NO se ha podido dibujar va IMPRESO en el boceto. Si se quedara
        # en un log, el master vería una cocina a la que le faltan muebles y no
        # tendría forma de saber por qué.
        if omitidos:
            faltan = ", ".join(str(o.get("label") or o.get("id") or "?")
                               for o in omitidos[:4])
            fig.text(0.5, 0.005,
                     f"⚠ Sin dibujar por falta de datos: {faltan}"
                     + ("…" if len(omitidos) > 4 else ""),
                     ha="center", va="bottom", fontsize=7.5, color="#B03A2E")

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=C_BG)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"success": True,
                "perspectivaBase64": f"data:image/png;base64,{b64}",
                "modulos": len(cajas),
                "omitidos": omitidos,
                "avisos": _val.get("avisos") or []}

    except HTTPException:
        # Un 422 con instrucciones no puede salir como un 500 genérico.
        raise
    except Exception as e:
        logger.error(f"perspectiva error: {e}", exc_info=True)
        raise HTTPException(status_code=500,
                            detail=f"No se pudo generar el boceto en perspectiva: {e}")
    finally:
        try:
            import matplotlib as _mpl
            _mpl.rcParams["path.sketch"] = None
        except Exception:
            pass


@router.post("/detect-distribucion")
async def detect_distribucion(payload: dict):
    """Analiza un render de cocina con IA y deduce la DISTRIBUCIÓN ESTRUCTURADA
    (tipo, paredes con ancho/alto y elementos con posición y ancho en cm) para
    poder dibujar planta y alzado deterministas con cotas."""
    import json as _json, re as _re
    img = (payload or {}).get("imageBase64") or (payload or {}).get("image") or ""
    if not img:
        raise HTTPException(status_code=400, detail="Falta la imagen del render.")
    # Medidas REALES que ha introducido el usuario (ancla de escala). Sin esto, la IA
    # solo puede estimar por proporción visual y las medidas salen imprecisas.
    medidas = (payload or {}).get("medidas") or {}
    def _num(v):
        try:
            n = float(str(v).replace(",", "."));  return n if n > 0 else 0
        except (TypeError, ValueError):
            return 0
    ancho_real = int(round(_num(medidas.get("ancho"))))    # ancho total de la estancia (cm)
    alto_real = int(round(_num(medidas.get("altura")))) or 240
    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="IA no configurada. Falta la clave del motor de IA (contacta con el administrador).")
        escala_nota = (
            f"\nDATO REAL (úsalo como ESCALA): el ancho total de la estancia es {ancho_real} cm"
            + (f" y la altura de techo {alto_real} cm" if alto_real else "")
            + ". La SUMA de los anchos de los módulos de la pared principal debe COINCIDIR con ese ancho real. "
            "Distribuye los módulos para que cuadren exactamente con esa medida.\n"
            if ancho_real else "\n"
        )
        prompt = (
            "Eres proyectista de cocinas experto. Analiza esta imagen (render o croquis de cocina) y deduce su "
            "DISTRIBUCIÓN REAL. Identifica el tipo (lineal, l, u, paralela, isla, g), las PAREDES con muebles y, "
            "en cada pared, la secuencia de MÓDULOS de izquierda a derecha con su nombre y ancho en cm "
            "(anchos de fabricación: 15,20,30,40,45,50,60,70,80,90,100,120). Electrodomésticos visibles "
            "cuentan como módulos (frigorífico, columna horno/microondas, lavavajillas, fregadero, "
            "placa/cocina, campana...).\n"
            "\nREGLA MÁS IMPORTANTE — LAS MEDIDAS ESCRITAS MANDAN:\n"
            "Si en la imagen hay NÚMEROS ESCRITOS (un croquis acotado a mano, cotas sobre un render), esos "
            "números son la VERDAD. Cópialos literalmente y marca `\"medida_escrita\": true` en ese módulo. "
            "NO los redondees, NO los ajustes y NO los sustituyas por tu estimación visual. "
            "Si solo puedes estimar el ancho mirando la proporción, marca `\"medida_escrita\": false`.\n"
            "El ancho de la pared: si está escrito en la imagen, cópialo y pon `\"ancho_escrito\": true`. "
            "Si NO está escrito pero los módulos sí lo están, pon `\"ancho_escrito\": false` y deja que el "
            "ancho sea la SUMA de los módulos escritos: nunca inventes un ancho de pared menor que esa suma.\n"
            "\nLA COMPOSICIÓN ESTÁ CERRADA:\n"
            "Devuelve EXACTAMENTE los módulos que estén dibujados o escritos en la imagen, ni uno más. "
            "No añadas un módulo porque a una cocina «le suele ir» ahí (un combi, una despensa, un "
            "escobero, un mueble para rellenar el hueco): si no está dibujado ni escrito, NO EXISTE. "
            "Si a la derecha del último módulo solo hay un costado o un lateral, eso es un costado: no "
            "lo conviertas en un mueble. "
            "Un hueco sin mueble se queda como hueco; ya se rellenará con un relleno a medida.\n"
            "\nREGLA DE FORMA — ESQUINAS Y FORMA EN L / U / LINEAL:\n"
            "- Si el croquis o render muestra elementos en DOS paredes formando una esquina de 90° (por ejemplo, placa/fregadero en un frente y columna/horno/micro/lavadora/pilar en la pared lateral), EL TIPO ES OBLIGATORIAMENTE \"l\" Y DEBES DEVOLVER 2 PAREDES (Pared 1 y Pared 2). NUNCA devuelvas \"lineal\" si ves muebles dispuestos en dos paredes en esquina.\n"
            "- Si ves 3 paredes con muebles, el tipo es \"u\". Si solo hay muebles a lo largo de una única línea recta de pared, el tipo es \"lineal\".\n"
            + escala_nota +
            "Devuelve SOLO un JSON con esta forma exacta:\n"
            "{\"tipo\":\"l\",\"paredes\":[{\"nombre\":\"Pared 1 (Frente Placa/Fregadero)\",\"ancho\":370,\"alto\":240,\"ancho_escrito\":false},{\"nombre\":\"Pared 2 (Frente Columnas/Lavadora)\",\"ancho\":210,\"alto\":240,\"ancho_escrito\":false}],"
            "\"elementos\":[{\"id\":\"placa\",\"label\":\"Placa\",\"pared_idx\":0,\"posicion_cm\":0,\"ancho\":90,\"medida_escrita\":true},{\"id\":\"columna_hornos\",\"label\":\"Columna Horno/Micro\",\"pared_idx\":1,\"posicion_cm\":0,\"ancho\":60,\"medida_escrita\":true}]}. "
            "'posicion_cm' es la distancia desde el inicio de esa pared. "
            "id usa palabras clave: frigorifico, congelador, columna_hornos, horno, microondas, lavavajillas, "
            "fregadero, placa, campana, mueble, cajonera, despensa, vinoteca, lavadora. "
            "Distingue CAJONERA de mueble de PUERTA."
        )
        text = await analyze_image_with_gemini(image_base64=img, prompt=prompt, model="gemini-2.5-pro")
        m = _re.search(r"\{[\s\S]*\}", text or "")
        data = {}
        if m:
            try:
                data = _json.loads(m.group())
            except Exception:
                data = {}
        # Sanear
        paredes = []
        for p in (data.get("paredes") or [])[:4]:
            try:
                anc = int(round(float(p.get("ancho") or 0)))
                alt = int(round(float(p.get("alto") or 240)))
            except (TypeError, ValueError):
                continue
            if anc > 0:
                paredes.append({"nombre": str(p.get("nombre") or f"Pared {len(paredes)+1}"),
                                "ancho": anc, "alto": alt or 240,
                                "ancho_escrito": bool(p.get("ancho_escrito"))})
        elementos = []
        for e in (data.get("elementos") or [])[:40]:
            # UN MÓDULO SIN ANCHO LLEGA SIN ANCHO. Aquí había un `or 60` que
            # rellenaba el hueco antes de validar nada, y con eso se cargaba —sin
            # querer— el arreglo del 23/08: `cota_de_ancho` distingue tres casos
            # (escrita / estimada / sin dato) y el tercero rotula «?», pero como
            # el módulo ya venía con un 60 puesto, nunca podía darse. Por el
            # camino principal se imprimía «~60» de módulos que no había medido
            # nadie, y la virgulilla le daba credibilidad a un número que era el
            # valor de respaldo del código. Eso es inventarse una cota
            # (CLAUDE.md, regla 7).
            try:
                bruto = e.get("ancho")
                anc = int(round(float(bruto))) if bruto not in (None, "") else None
                pos = int(round(float(e.get("posicion_cm") or 0)))
                pidx = int(e.get("pared_idx") or 0)
            except (TypeError, ValueError):
                continue
            elem = {
                "id": str(e.get("id") or "mueble").lower().strip().replace(" ", "_"),
                "label": str(e.get("label") or e.get("id") or "Módulo")[:24],
                "pared_idx": max(0, pidx), "posicion_cm": max(0, pos),
                "medida_escrita": bool(e.get("medida_escrita")),
            }
            # La clave `ancho` solo se pone si de verdad hay un ancho. Si se
            # pusiera a 0 o a None tampoco valdría: el validador lo tomaría por
            # un ancho imposible y lo «corregiría» a 15, que es otra cifra que
            # no ha medido nadie.
            if anc is not None:
                elem["ancho"] = max(10, anc)
            elementos.append(elem)
        if not paredes:
            raise HTTPException(status_code=422, detail="No se pudo deducir la distribución del render.")

        # Las medidas las cuadra kitchen_geometry, que es la única fuente de
        # verdad. Aquí había una segunda normalización que reescalaba TODOS los
        # módulos contra el ancho de pared estimado: eso aplastaba las medidas
        # ESCRITAS del croquis contra un ancho que la IA se había inventado
        # (400 cm de módulos acotados a mano metidos en una pared de 280).
        if ancho_real and paredes:
            paredes[0]["ancho"] = ancho_real
            paredes[0]["ancho_escrito"] = True
            if alto_real:
                paredes[0]["alto"] = alto_real
        # VALIDACIÓN DE GEOMETRÍA REAL (obligatoria, ver CLAUDE.md): ninguna medida
        # imposible llega al dibujo; los electrodomésticos no se reescalan.
        from services.kitchen_geometry import validar_distribucion
        val = validar_distribucion(
            {"tipo": str(data.get("tipo") or "lineal"), "paredes": paredes, "elementos": elementos},
            ancho_real=ancho_real, alto_real=alto_real)
        if not val.get("ok"):
            raise HTTPException(status_code=422,
                                detail=f"{val.get('motivo')} " + " ".join(val.get('avisos') or []))
        return {"success": True, "distribucion": val, "avisos": val.get("avisos") or []}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"detect-distribucion error: {e}")
        raise HTTPException(status_code=500, detail="No se pudo analizar la distribución.")


@router.post("/validar-distribucion")
async def validar_distribucion_corregida(payload: dict):
    """Revalida una distribución CORREGIDA A MANO en el panel del Estudio 3D.

    Aquí no interviene ninguna IA: entra lo que ha tecleado el usuario y sale
    pasado por el validador de geometría, que es el único que decide si una
    medida es fabricable y el que cuadra la suma de cada pared con su ancho
    (CLAUDE.md). O sea que corregir a mano NO es saltarse la validación: es
    entrar por la puerta buena, con un dato real en vez de una estimación.

    `ancho_real` no se pasa a propósito. El ancho de pared que llega ya es el
    bueno: o el que se aplicó al detectar (que salió de «Medidas de la
    estancia») o el que el usuario acaba de corregir en el panel. Volver a
    imponer el de la estancia pisaría su corrección.
    """
    dist = payload.get("distribucion") or {}
    if not dist.get("paredes"):
        raise HTTPException(status_code=422,
                            detail="No hay ninguna pared que validar.")

    # EL ANCHO DE PARED SE CLAVA. Es el fallo que tuvo esto al escribirse, y se
    # vio probandolo: al corregir un bajo fregadero de 60 a 90, la PARED crecia
    # sola de 300 a 330; y al quitar el lavavajillas, encogia a 270. Una pared
    # no crece porque cambies un mueble ni encoge porque quites un
    # electrodomestico — lo que te queda es un hueco de 60 cm.
    #
    # Venia de que `validar_distribucion`, cuando la pared no esta marcada como
    # medida firme, deduce su ancho de la SUMA de los modulos con medida
    # escrita. Ahi eso es correcto (se esta leyendo un croquis acotado). Aqui no:
    # aqui la pared ya esta decidida —la tecleo el usuario en «Medidas de la
    # estancia», estaba escrita en el plano, o la acaba de corregir en el panel—
    # y lo que se esta tocando son los MUEBLES.
    #
    # Es el mismo agujero contra el que avisa CLAUDE.md: si la pared se estira
    # hasta los muebles, cualquier composicion "cabe" y el validador deja de
    # validar nada.
    for pared in dist.get("paredes") or []:
        pared["ancho_escrito"] = True

    from services.kitchen_geometry import validar_distribucion
    try:
        val = validar_distribucion(dist)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"validar-distribucion error: {e}")
        raise HTTPException(status_code=500, detail="No se pudo validar la distribución.")
    if not val.get("ok"):
        raise HTTPException(
            status_code=422,
            detail=f"{val.get('motivo') or 'La distribución no es válida.'} "
                   + " ".join(val.get("avisos") or []))
    return {"success": True, "distribucion": val, "avisos": val.get("avisos") or []}


# ─── Volcar la relación MV al presupuesto ────────────────────────────────────
# Permiso PROPIO, no el de la tarifa. Son dos cosas distintas: ver lo que cuesta
# un mueble (master) y poder meter muebles en un presupuesto (quien monta
# pedidos). Un jefe de obra puede necesitar lo segundo sin tener lo primero, y
# de hecho es el caso normal.
PERMISO_VOLCAR_MV = "canVolcarMV"


async def _puede_volcar_mv(user) -> bool:
    """¿Puede volcar la relación MV al presupuesto?

    Se mira el permiso EN VIVO en la base de datos, no en el token: el JWT no
    lleva los `can*`, así que fiándose del token este permiso no se cumpliría
    nunca para un usuario al que se le acaba de dar (es la misma razón por la
    que `require_module_access` lo hace así).
    """
    if not user:
        return False
    from routes.cascos import _es_master
    if _es_master(user):
        return True
    uid = user.get("id")
    if not uid:
        return False
    try:
        from services.jwt_service import _users_collection
        fila = await _users_collection().find_one({"id": uid}, {"_id": 0, PERMISO_VOLCAR_MV: 1})
        return bool(fila and fila.get(PERMISO_VOLCAR_MV))
    except Exception as e:                       # pragma: no cover
        # Si no se puede comprobar, NO se concede. Un permiso que se abre cuando
        # falla la base de datos no es un permiso.
        logger.error("no se pudo comprobar %s: %s", PERMISO_VOLCAR_MV, e)
        return False


@router.post("/relacion-mv")
async def relacion_mv(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """La distribución del Estudio 3D, traducida a MUEBLES MV con su precio.

    Cierra el circuito: lo que se ha detectado (y corregido a mano) en el panel
    se convierte en códigos de catálogo con puntos y PVP, listos para revisar y
    volcar al presupuesto.

    No hay aquí ni una tarifa nueva. El puente (`distribucion_a_mv`) solo decide
    QUÉ mueble es cada módulo y con qué ancho y altura; de ponerle precio se
    encarga `mv_relacion`, que lee el catálogo oficial y ya estaba probado. Dos
    caminos hasta el precio serían dos sitios donde equivocarse.

    Dos formas de llamarlo:
      · con `distribucion`: traduce y tarifa (primera vez).
      · con `lineas`: vuelve a tarifar unas líneas ya revisadas por el usuario
        (ha cambiado una mano, o ha pasado un mueble a dos puertas).

    LOS MUEBLES SÍ, EL DINERO NO. Los códigos MV los ve cualquiera —son el
    nombre del mueble, no lo que cuesta—; los puntos y el PVP solo el master
    (24/08/2026, a petición suya).
    """
    from routes.cascos import _ve_precios_mv, sin_precios
    con_precios = _ve_precios_mv(current_user)
    puede_volcar = await _puede_volcar_mv(current_user)
    from services.distribucion_a_mv import distribucion_a_relacion, notacion_de
    from services.mv_relacion import parse_relacion_text

    tarifa = str((payload or {}).get("tarifa") or "T1")
    lineas_dadas = (payload or {}).get("lineas")
    if lineas_dadas:
        lineas = [dict(x) for x in lineas_dadas]
        sin_codigo = (payload or {}).get("sin_codigo") or []
    else:
        dist = (payload or {}).get("distribucion") or {}
        if not dist.get("elementos"):
            raise HTTPException(
                status_code=422,
                detail=("No hay módulos que traducir. Pulsa «Detectar distribución» "
                        "antes de pedir los muebles MV."))
        try:
            r = distribucion_a_relacion(
                dist, tarifa=tarifa,
                alto_altos=int((payload or {}).get("alto_altos") or 70),
                alto_columnas=int((payload or {}).get("alto_columnas") or 200))
        except Exception as e:
            logger.error(f"relacion-mv: {e}")
            raise HTTPException(status_code=500, detail="No se pudo traducir la distribución a muebles MV.")
        lineas, sin_codigo = r["lineas"], r["sin_codigo"]

    notacion = notacion_de(lineas)
    tarifadas = parse_relacion_text(notacion, tarifa) if lineas else []

    # Se emparejan por ORDEN: `notacion_de` escribe un mueble por línea y el
    # parser devuelve uno por línea, en el mismo orden. Si algún día dejaran de
    # coincidir, se dice — no se reparten precios a ojo, que es como se cuela un
    # PVP en el mueble equivocado.
    if len(tarifadas) != len(lineas):
        logger.error("relacion-mv: %d líneas y %d tarifadas", len(lineas), len(tarifadas))
        raise HTTPException(
            status_code=500,
            detail=("No se han podido tarifar todos los muebles "
                    f"({len(tarifadas)} de {len(lineas)}). No se dan precios a medias."))

    for linea, t in zip(lineas, tarifadas):
        # La MANO decidida viaja en el código canónico. Un código que acaba en
        # «D/I» es una puerta SIN mano decidida, y si sale así hacia el taller la
        # decide el taller: acierta la mitad de las veces y la otra mitad es un
        # frente desmontado y taladrado otra vez en casa del cliente. Aquí ya
        # sabemos la mano (propuesta o elegida), así que se escribe.
        if linea.get("mano") and t.get("cod", "").endswith("D/I"):
            t["cod"] = t["cod"][:-3] + linea["mano"]
            t["mano"] = linea["mano"]
        t["manoPropuesta"] = bool(linea.get("mano_propuesta"))
        linea["codigo_mv"] = t.get("cod")
        linea["familia_mv"] = t.get("familia")
        linea["puntos"] = t.get("pts")
        linea["pvp"] = t.get("pvp")
        linea["fondo"] = t.get("fondo")

    total = round(sum((x.get("pvp") or 0) for x in lineas), 2)
    # OJO AL ORDEN: `sinPrecio` se calcula ANTES de esconder nada. Si se mirara
    # después, con el master fuera saldrían TODAS las líneas como «sin precio» y
    # el aviso diría que la tarifa está rota cuando lo que pasa es que no se
    # tienen permisos para verla.
    sin_precio = [x["codigo"] for x in lineas if not x.get("pvp")]
    # LOS MUEBLES LISTOS PARA VOLCAR solo se entregan a quien puede volcar. El
    # candado va aquí y no en el botón: esconder un botón no cierra una API.
    # Es la misma lista que devuelve el tarificador, que es lo que espera la
    # pantalla de revisión de la relación — no se inventa un formato nuevo para
    # que luego los dos caminos se separen con el tiempo.
    muebles = None
    if puede_volcar:
        muebles = tarifadas if con_precios else sin_precios(tarifadas)

    return {"success": True, "tarifa": tarifa,
            "lineas": lineas if con_precios else sin_precios(lineas),
            "muebles": muebles,
            "puedeVolcar": puede_volcar,
            "sin_codigo": sin_codigo, "notacion": notacion,
            "totalPvp": total if con_precios else None,
            "sinPrecio": sin_precio,
            "preciosOcultos": not con_precios}


@router.post("/relacion-mv-pdf")
async def relacion_mv_pdf(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """La relación de muebles MV en PDF RELLENABLE.

    Para tres cosas que pidió el master: llevárselo en papel, enseñárselo a un
    cliente, y —sobre todo— corregirlo fuera del ERP y volver a subirlo para un
    pegado masivo. Por eso NO es un PDF cerrado: los campos son AcroForm y se
    releen de forma determinista, sin IA de por medio. Y trae seis renglones en
    blanco al final para apuntar a mano lo que falte.

    SIN PRECIOS, y no por el candado de la tarifa: es que este papel puede
    acabar delante de un cliente. Lo que lleva es qué muebles son y cuánto
    miden. (Regla 5: los descuentos y el coste no salen en nada que vea un
    cliente.)

    LAS MEDIDAS SE PASAN A MILÍMETROS. El PDF es en mm y `_cota` no convierte:
    escribe el número que le den. Mandándole los centímetros de la tarifa MV, un
    bajo de 60 cm saldría impreso como «60», que en ese papel significa 60 mm.
    """
    from fastapi.responses import Response as _Response
    from services.relacion_pdf import build_relacion_pdf

    lineas = (payload or {}).get("lineas") or []
    if not isinstance(lineas, list) or not lineas:
        raise HTTPException(
            status_code=400,
            detail="No hay muebles que listar. Saca antes la relación de muebles MV.")

    def _mm(valor_cm):
        try:
            return int(round(float(valor_cm) * 10))
        except (TypeError, ValueError):
            return ""                      # sin dato se deja EN BLANCO, no a cero

    filas = []
    for ln in lineas[:400]:
        avisos = []
        if ln.get("mano_propuesta"):
            avisos.append("mano propuesta: confirmar D/I")
        if ln.get("confirmar_familia"):
            avisos.append("familia a confirmar")
        filas.append({
            "cantidad": "1",
            "codigo": str(ln.get("codigo") or ""),
            "descripcion": str(ln.get("familia") or ln.get("label") or ""),
            "ancho": _mm(ln.get("ancho")),
            "alto": _mm(ln.get("alto")),
            "fondo": _mm(ln.get("fondo")),
            "observaciones": " · ".join(avisos),
        })

    try:
        pdf = build_relacion_pdf(
            filas,
            titulo=str((payload or {}).get("titulo") or "Relación de muebles"),
            cliente=str((payload or {}).get("cliente") or ""),
            observaciones=str((payload or {}).get("observaciones") or ""),
        )
    except Exception as e:
        logger.error("relacion-mv-pdf: %s", e)
        raise HTTPException(status_code=500, detail=f"No se pudo generar el PDF: {e}")

    return _Response(content=pdf, media_type="application/pdf",
                     headers={"Content-Disposition": 'attachment; filename="relacion-muebles.pdf"'})


@router.post("/exportar-dxf")
async def exportar_dxf(payload: dict):
    """
    Exporta la distribución validada de la cocina a un archivo DXF (AutoCAD R12/2000 ASCII)
    listo para enviar a taller, fábrica de cascos o marmolista.
    """
    distribucion = payload.get("distribucion") or {}
    cliente = str(payload.get("cliente") or "Cliente")
    if not distribucion or not distribucion.get("paredes"):
        raise HTTPException(status_code=400, detail="Falta la distribución para exportar a DXF.")

    try:
        from services.dxf_exporter import generar_dxf_cocina
        dxf_txt = generar_dxf_cocina(distribucion, cliente=cliente)
        filename = f"plano_cad_{cliente.lower().replace(' ', '_')}.dxf"
        return {
            "success": True,
            "dxfContent": dxf_txt,
            "filename": filename,
        }
    except Exception as e:
        logger.error(f"exportar-dxf error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando archivo DXF: {e}")


# `_sanea_distribucion` SE BORRO el 25/08/2026 y no se echa de menos.
#
# No la llamaba nadie —cero usos en todo el repositorio— y estaba escrita para
# hacer justo lo que prohibe la regla de oro: se inventaba medidas y se saltaba
# el validador entero. Ejecutandola salian un bajo de 180 cm y otro de 127 cm
# (ninguno de los dos existe) y, sin datos, una pared de 400 cm de la nada.
# Repartia el sobrante al modulo mas ancho sin volver a ajustarlo al catalogo,
# que es de donde salian esas cifras.
#
# Quien necesite sanear una distribucion llama a `validar_distribucion`, que con
# esos mismos 127 cm ajusta a 120 y anade el relleno de 7 — la solucion de
# carpinteria correcta. Dos caminos hasta la misma medida son dos sitios donde
# equivocarse, y uno de los dos no miraba.


@router.post("/distribucion-desde-texto")
async def distribucion_desde_texto(payload: dict):
    """Deduce la DISTRIBUCIÓN ESTRUCTURADA a partir de la DESCRIPCIÓN de texto del
    diseño (la que el usuario escribe para el render), no de la imagen. Así el
    alzado técnico refleja EXACTAMENTE lo pedido (recuentos de cajones/gavetas por
    módulo), aunque el render fotorrealista no lo respete. Devuelve {success, distribucion}."""
    import json as _json, re as _re
    desc = ((payload or {}).get("descripcion") or (payload or {}).get("description") or "").strip()
    if not desc:
        raise HTTPException(status_code=400, detail="Falta la descripción del diseño.")
    medidas = (payload or {}).get("medidas") or {}
    def _num(v):
        try:
            n = float(str(v).replace(",", ".")); return n if n > 0 else 0
        except (TypeError, ValueError):
            return 0
    ancho_real = int(round(_num(medidas.get("ancho"))))
    alto_real = int(round(_num(medidas.get("altura")))) or 240
    try:
        from services.llm_vision import generate_text_with_gemini
    except Exception:
        raise HTTPException(status_code=503, detail="IA de texto no disponible.")
    escala = (f"\nEl ancho total de la pared principal es {ancho_real} cm: la suma de anchos de sus módulos debe coincidir.\n" if ancho_real else "\n")
    prompt = (
        "Eres proyectista de cocinas. A partir de esta DESCRIPCIÓN de un diseño, deduce su DISTRIBUCIÓN "
        "estructurada, RESPETANDO LITERALMENTE lo que se pide por cada módulo (nº de puertas, cajones y "
        "gavetas, y su orden de izquierda a derecha). Anchos típicos en cm: 15,20,30,40,45,50,60,80,90,100,120.\n"
        + escala +
        "Devuelve SOLO un JSON con esta forma exacta:\n"
        "{\"tipo\":\"lineal\",\"paredes\":[{\"nombre\":\"Pared principal\",\"ancho\":370,\"alto\":240}],"
        "\"elementos\":[{\"id\":\"cajonera\",\"label\":\"1 cajón + 2 gavetas\",\"pared_idx\":0,\"posicion_cm\":0,\"ancho\":60}]}.\n"
        "REGLAS del campo 'id' (palabras clave que entiende el dibujo): frigorifico, congelador, "
        "columna_hornos, horno, microondas, lavavajillas, fregadero, placa, campana, despensa, vinoteca, "
        "cajonera (para módulos con cajones/gavetas), mueble (bajo/alto de puerta normal). "
        "Para un módulo con cajones/gavetas usa id='cajonera' y en 'label' escribe el recuento EXACTO "
        "(p. ej. '1 cajón + 2 gavetas') para que se dibujen los frentes correctos.\n"
        f"DESCRIPCIÓN:\n{desc}\n\n"
        "Devuelve SOLO el JSON."
    )
    try:
        text = await generate_text_with_gemini(prompt, model="gemini-2.5-pro")
    except Exception as e:
        logger.error(f"distribucion-desde-texto IA: {e}")
        raise HTTPException(status_code=500, detail="No se pudo interpretar la descripción.")
    m = _re.search(r"\{[\s\S]*\}", text or "")
    data = {}
    if m:
        try:
            data = _json.loads(m.group())
        except Exception:
            data = {}
    from services.kitchen_geometry import validar_distribucion
    dist = validar_distribucion(data, ancho_real=ancho_real, alto_real=alto_real)
    if not dist.get("ok"):
        raise HTTPException(status_code=422,
                            detail=f"{dist.get('motivo')} " + " ".join(dist.get('avisos') or []))
    return {"success": True, "distribucion": dist, "avisos": dist.get("avisos") or []}
