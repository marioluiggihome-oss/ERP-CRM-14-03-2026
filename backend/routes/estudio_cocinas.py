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
import os
import re
import sys
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

logger = logging.getLogger("estudio_cocinas")

# ─── Auth ─────────────────────────────────────────────────────────────────────
try:
    from services.jwt_service import require_auth, get_current_user, ADMIN_ROLE_FLAGS
    _DEPS = [Depends(require_auth)]
except Exception:
    _DEPS = []
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]

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
            "REPRODUCE EXACTAMENTE del croquis:\n"
            "- La forma de la habitación y la DISTRIBUCIÓN (paredes, esquinas; en L / U / lineal tal cual).\n"
            "- La POSICIÓN, el ORDEN de izquierda a derecha y el TAMAÑO RELATIVO de cada módulo (bajos, altos, columnas).\n"
            "- La UBICACIÓN EXACTA de la columna de horno/microondas, del frigorífico, del fregadero, de la placa y de la campana, donde aparecen en el dibujo.\n"
            "- Las VENTANAS y PUERTAS en la MISMA pared y posición del croquis (no las muevas ni inventes ventanas nuevas).\n"
            "- Las medidas/proporciones anotadas: un módulo ancho debe verse ancho.\n\n"
            "PROHIBIDO: añadir, quitar, mover o redistribuir cualquier elemento que no esté en el croquis; "
            "inventar isla, ventana central o electrodomésticos extra; cambiar la distribución por otra que te parezca más bonita.\n\n"
            "IMPORTANTE: del texto de estilo de abajo usa SOLO colores, materiales y acabados. "
            "Si menciona isla, ventanas, campana, distribución o cualquier elemento que NO aparezca en el croquis, "
            "IGNÓRALO por completo — el CROQUIS manda sobre el texto.\n\n"
            f"Acabado/estilo a aplicar (SOLO materiales y colores) — Estilo: {estilo}; Materiales: {materiales}; "
            f"{payload.descripcion or ''}.\n\n"
            "Resultado: fotografía de interiorismo fotorrealista, iluminación natural realista, materiales PBR con textura real, "
            "perspectiva desde una esquina a la altura de los ojos (~160 cm) que muestre TODA la cocina, formato 16:9. "
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
        f"Edita este render de cocina siguiendo exactamente esta instrucción: \"{payload.instruccion}\"\n\n"
        f"REQUISITOS:\n"
        f"- Mantén la distribución, estructura y dimensiones inalteradas salvo que se indique explícitamente\n"
        f"- Conserva la iluminación fotorrealista y calidad de los materiales\n"
        f"- El resultado debe ser un render 8K de calidad de revista de interiorismo\n"
        f"- Devuelve SOLO la imagen editada"
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
    """
    Genera un plano 2D técnico acotado con matplotlib.
    Usa la distribución estructurada si está disponible.
    No requiere motor de IA — generación local instantánea.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        # Colores profesionales
        C_BG = "#F8F6F2"; C_SUELO = "#EDE8E0"; C_PARED = "#2C2C2C"
        C_MUEBLE = "#D4C5A9"; C_BORDE = "#8B7355"; C_ENCIM = "#C8B89A"
        C_ISLA = "#E8DDD0"; C_COTA = "#555555"; C_ACENTO = "#8B7355"
        C_GRID = "#D8D0C4"
        C_ELEM = {"fregadero": "#B8D4E0", "placa": "#E8B4B4", "horno": "#D4A574",
                  "frigorifico": "#A8C8D8", "lavavajillas": "#B8D0B8", "campana": "#D0D0D0",
                  "microondas": "#D4A574", "columna_hornos": "#C8A882"}
        ELEM_SYMBOLS = {"fregadero": "≈", "placa": "○○", "horno": "□", "frigorifico": "❄",
                        "lavavajillas": "≡", "campana": "▽", "microondas": "□", "columna_hornos": "┃"}

        # Obtener distribución
        dist = payload.distribucion_estructurada
        if dist and dist.tipo:
            tipo = dist.tipo
            paredes_data = dist.paredes or [{'nombre': 'Pared principal', 'ancho': 400, 'alto': 240}]
            isla_data = dist.isla or {'ancho': 0, 'largo': 0}
            elementos = dist.elementos or []
        else:
            # Fallback al parser de texto
            m = _medidas_para_dibujo(payload.medidas)
            tipo = 'l'  # default legacy
            paredes_data = [{'nombre': 'Pared norte', 'ancho': m['ancho'], 'alto': 240},
                           {'nombre': 'Pared oeste', 'ancho': m['alto'], 'alto': 240}]
            isla_data = {'ancho': m['isla_w'], 'largo': m['isla_h']}
            elementos = []

        # Calcular dimensiones del espacio
        if tipo == 'lineal':
            room_w = paredes_data[0].get('ancho', 400)
            room_h = max(250, int(room_w * 0.6))
        elif tipo in ('l', 'g'):
            room_w = max(p.get('ancho', 300) for p in paredes_data)
            room_h = max(250, paredes_data[1].get('ancho', 250) if len(paredes_data) > 1 else 300)
        elif tipo == 'u':
            room_w = paredes_data[1].get('ancho', 400) if len(paredes_data) > 1 else 400
            room_h = max(paredes_data[0].get('ancho', 250), paredes_data[2].get('ancho', 250) if len(paredes_data) > 2 else 250)
        elif tipo == 'paralela':
            room_w = max(p.get('ancho', 400) for p in paredes_data)
            room_h = max(300, int(room_w * 0.7))
        elif tipo == 'isla':
            room_w = paredes_data[0].get('ancho', 400)
            room_h = max(350, int(room_w * 0.8))
        else:
            room_w = 400; room_h = 350

        # Evitar dimensiones 0 o negativas (una pared con ancho 0 provocaría
        # una división por cero al calcular la escala).
        room_w = room_w if room_w and room_w > 0 else 400
        room_h = room_h if room_h and room_h > 0 else 350

        # Setup figure
        fig, ax = plt.subplots(figsize=(16, 11))
        fig.patch.set_facecolor(C_BG)
        ax.set_facecolor(C_BG)

        scale = min(560 / room_w, 420 / room_h)
        W, H = room_w * scale, room_h * scale
        ox, oy = 80, 70

        ax.set_xlim(0, W + 180); ax.set_ylim(-20, H + 130)
        ax.set_aspect("equal"); ax.axis("off")

        # Suelo + grid
        ax.add_patch(patches.Rectangle((ox, oy), W, H,
            linewidth=2, edgecolor=C_PARED, facecolor=C_SUELO, zorder=1))
        paso = max(30, int(min(room_w, room_h) / 10)) * scale / 100 * 100
        for gx in range(int(ox), int(ox + W + 1), max(1, int(paso))):
            ax.plot([gx, gx], [oy, oy + H], color=C_GRID, linewidth=0.3, zorder=1)
        for gy in range(int(oy), int(oy + H + 1), max(1, int(paso))):
            ax.plot([ox, ox + W], [gy, gy], color=C_GRID, linewidth=0.3, zorder=1)

        # Paredes (contorno)
        pw = max(6, int(0.015 * min(W, H)))
        for rect in [(ox, oy + H - pw, W, pw), (ox, oy, W, pw),
                     (ox, oy, pw, H), (ox + W - pw, oy, pw, H)]:
            ax.add_patch(patches.Rectangle(
                (rect[0], rect[1]), rect[2], rect[3],
                linewidth=0, facecolor=C_PARED, zorder=2))

        # Dibujar módulos según distribución
        mod_depth = 60 * scale / 100  # 60cm profundidad estándar

        def draw_modules_on_wall(start_x, start_y, length_cm, direction, pared_idx):
            """Dibuja módulos a lo largo de una pared."""
            length_px = length_cm * scale
            mod_w = 55 * scale / 100  # 55cm ancho módulo
            # Obtener elementos asignados a esta pared
            pared_elems = [e for e in elementos if e.get('pared_idx', 0) == pared_idx]
            
            if direction == 'north':  # Módulos en pared norte (arriba)
                x = start_x
                while x + mod_w <= start_x + length_px:
                    ax.add_patch(patches.Rectangle((x, start_y - mod_depth), mod_w, mod_depth,
                        linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
                    x += mod_w
                # Encimera
                ax.add_patch(patches.Rectangle(
                    (start_x, start_y - mod_depth - 3), length_px, 3,
                    linewidth=0, facecolor=C_ENCIM, alpha=0.8, zorder=4))
                # Elementos
                elem_x = start_x + mod_w * 0.5
                for el in pared_elems:
                    ew = el.get('ancho', 60) * scale / 100
                    color = C_ELEM.get(el.get('id', ''), '#B8D4E0')
                    symbol = ELEM_SYMBOLS.get(el.get('id', ''), '?')
                    ax.add_patch(patches.FancyBboxPatch(
                        (elem_x - ew/2, start_y - mod_depth/2 - ew*0.3),
                        ew, ew*0.6, boxstyle="round,pad=2", linewidth=1,
                        edgecolor="#555", facecolor=color, zorder=5))
                    ax.text(elem_x, start_y - mod_depth/2, symbol,
                        ha="center", va="center", fontsize=7, color="#333", zorder=6)
                    ax.text(elem_x, start_y - mod_depth - 10, el.get('label', ''),
                        ha="center", va="top", fontsize=5, color="#666", zorder=6)
                    elem_x += ew + 10

            elif direction == 'south':  # Módulos en pared sur (abajo)
                x = start_x
                while x + mod_w <= start_x + length_px:
                    ax.add_patch(patches.Rectangle((x, start_y), mod_w, mod_depth,
                        linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
                    x += mod_w
                ax.add_patch(patches.Rectangle(
                    (start_x, start_y + mod_depth), length_px, 3,
                    linewidth=0, facecolor=C_ENCIM, alpha=0.8, zorder=4))

            elif direction == 'west':  # Módulos en pared oeste (izquierda)
                y = start_y
                while y + mod_w <= start_y + length_px:
                    ax.add_patch(patches.Rectangle((start_x, y), mod_depth, mod_w,
                        linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
                    y += mod_w
                ax.add_patch(patches.Rectangle(
                    (start_x + mod_depth, start_y), 3, length_px,
                    linewidth=0, facecolor=C_ENCIM, alpha=0.8, zorder=4))

            elif direction == 'east':  # Módulos en pared este (derecha)
                y = start_y
                while y + mod_w <= start_y + length_px:
                    ax.add_patch(patches.Rectangle((start_x - mod_depth, y), mod_depth, mod_w,
                        linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
                    y += mod_w
                ax.add_patch(patches.Rectangle(
                    (start_x - mod_depth - 3, start_y), 3, length_px,
                    linewidth=0, facecolor=C_ENCIM, alpha=0.8, zorder=4))

        # Dibujar según tipo de distribución
        if tipo == 'lineal':
            pared_w = paredes_data[0].get('ancho', 400)
            draw_modules_on_wall(ox + pw, oy + H - pw, pared_w, 'north', 0)
        elif tipo == 'l':
            pared_w = paredes_data[0].get('ancho', 400)
            pared_h = paredes_data[1].get('ancho', 250) if len(paredes_data) > 1 else 250
            draw_modules_on_wall(ox + pw, oy + H - pw, pared_w, 'north', 0)
            draw_modules_on_wall(ox + pw, oy + pw, pared_h, 'west', 1)
        elif tipo == 'u':
            pared_izq = paredes_data[0].get('ancho', 250)
            pared_fondo = paredes_data[1].get('ancho', 400) if len(paredes_data) > 1 else 400
            pared_der = paredes_data[2].get('ancho', 250) if len(paredes_data) > 2 else 250
            draw_modules_on_wall(ox + pw, oy + H - pw, pared_fondo, 'north', 1)
            draw_modules_on_wall(ox + pw, oy + pw, pared_izq, 'west', 0)
            draw_modules_on_wall(ox + W - pw, oy + pw, pared_der, 'east', 2)
        elif tipo == 'paralela':
            pared_n = paredes_data[0].get('ancho', 400)
            pared_s = paredes_data[1].get('ancho', 400) if len(paredes_data) > 1 else 400
            draw_modules_on_wall(ox + pw, oy + H - pw, pared_n, 'north', 0)
            draw_modules_on_wall(ox + pw, oy + pw, pared_s, 'south', 1)
        elif tipo == 'isla':
            pared_w_val = paredes_data[0].get('ancho', 400)
            draw_modules_on_wall(ox + pw, oy + H - pw, pared_w_val, 'north', 0)
            # Isla central
            iw = isla_data.get('ancho', 120) * scale / 100
            ih = isla_data.get('largo', 200) * scale / 100
            ix = ox + (W - iw) / 2; iy = oy + (H - ih) / 2 - 15
            ax.add_patch(patches.Rectangle((ix, iy), iw, ih,
                linewidth=2, edgecolor=C_BORDE, facecolor=C_ISLA, zorder=3))
            ax.text(ix + iw / 2, iy + ih / 2,
                f"ISLA\n{isla_data.get('ancho', 120)}×{isla_data.get('largo', 200)} cm",
                ha="center", va="center", fontsize=7.5, fontweight="bold",
                color="#1A1A1A", zorder=5)
        elif tipo == 'g':
            pared_izq = paredes_data[0].get('ancho', 250)
            pared_fondo = paredes_data[1].get('ancho', 400) if len(paredes_data) > 1 else 400
            pared_der = paredes_data[2].get('ancho', 200) if len(paredes_data) > 2 else 200
            draw_modules_on_wall(ox + pw, oy + H - pw, pared_fondo, 'north', 1)
            draw_modules_on_wall(ox + pw, oy + pw, pared_izq, 'west', 0)
            draw_modules_on_wall(ox + W - pw, oy + pw, pared_der, 'east', 2)
            # Península
            pen_w = 120 * scale / 100; pen_h = mod_depth
            px = ox + W - pw - pen_w; py = oy + pw + pared_der * scale / 100
            ax.add_patch(patches.Rectangle((px, py), pen_w, pen_h,
                linewidth=1.5, edgecolor=C_BORDE, facecolor=C_ISLA, zorder=3))
            ax.text(px + pen_w / 2, py + pen_h / 2, "PENÍNSULA",
                ha="center", va="center", fontsize=6, fontweight="bold", color="#1A1A1A", zorder=5)

        # Cotas
        arrow_kw = dict(arrowstyle="<->", color=C_COTA, lw=0.9)
        def cota_h(x1, x2, y, label):
            ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=arrow_kw)
            ax.text((x1 + x2) / 2, y + 6, label, ha="center", va="bottom",
                fontsize=6.5, color=C_COTA)
        def cota_v(x, y1, y2, label):
            ax.annotate("", xy=(x, y2), xytext=(x, y1), arrowprops=arrow_kw)
            ax.text(x - 6, (y1 + y2) / 2, label, ha="right", va="center",
                fontsize=6.5, color=C_COTA, rotation=90)
        cota_h(ox, ox + W, oy - 22, f"{room_w} cm")
        cota_v(ox - 22, oy, oy + H, f"{room_h} cm")
        # Cotas por pared
        for i, p in enumerate(paredes_data):
            ancho_p = p.get('ancho', 0)
            if ancho_p > 0:
                ax.text(ox + W + 20, oy + H - 20 - i * 16,
                    f"{p.get('nombre', f'Pared {i+1}')}: {ancho_p}cm",
                    fontsize=6, color=C_COTA, va="center", zorder=6)

        # Leyenda
        lx = ox + W + 20; ly = oy + H - 20 - len(paredes_data) * 16 - 20
        items = [(C_MUEBLE, C_BORDE, "Módulo bajo"), (C_ENCIM, C_BORDE, "Encimera")]
        if tipo == 'isla' or (isla_data.get('ancho', 0) > 0):
            items.append((C_ISLA, C_BORDE, "Isla central"))
        if tipo == 'g':
            items.append((C_ISLA, C_BORDE, "Península"))
        if elementos:
            for el in elementos[:4]:
                color = C_ELEM.get(el.get('id', ''), '#B8D4E0')
                items.append((color, "#555", el.get('label', '')))
        ax.text(lx, ly + 15, "LEYENDA", fontsize=7, fontweight="bold", color=C_ACENTO)
        for i, (fc, ec, lbl) in enumerate(items):
            yy = ly - i * 16
            ax.add_patch(patches.Rectangle((lx, yy - 5), 10, 8,
                linewidth=0.8, edgecolor=ec, facecolor=fc))
            ax.text(lx + 14, yy, lbl, fontsize=5.5, va="center", color=C_COTA)

        # Título distribución
        dist_labels = {'lineal': 'LINEAL', 'l': 'EN L', 'u': 'EN U',
                       'paralela': 'PARALELA', 'isla': 'CON ISLA', 'g': 'EN G'}
        tipo_label = dist_labels.get(tipo, tipo.upper())

        # Cajetín
        ax.add_patch(patches.Rectangle((ox, -10), W, 52,
            linewidth=1.2, edgecolor=C_ACENTO, facecolor="#F0EBE3", zorder=10))
        ax.plot([ox, ox + W], [20, 20], color=C_ACENTO, linewidth=0.7, zorder=11)
        ax.text(ox + W / 2, 32,
            f"PLANO DE DISTRIBUCIÓN {tipo_label} — {(payload.nombre_cliente or 'CLIENTE').upper()} · {(payload.estilo or 'MODERNO').upper()}",
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="#1A1A1A", zorder=12)
        medidas_txt = ' | '.join([f"{p.get('nombre','')}: {p.get('ancho',0)}cm" for p in paredes_data])
        ax.text(ox + 10, 8, f"MEDIDAS: {medidas_txt}",
            ha="left", va="center", fontsize=5.5, color=C_COTA, zorder=12)
        ax.text(ox + W / 2, 8, "ESCALA 1:20",
            ha="center", va="center", fontsize=6.5, color=C_COTA, zorder=12)
        ax.text(ox + W - 10, 8, "3D ESTUDIO",
            ha="right", va="center", fontsize=6.5, color=C_ACENTO,
            fontweight="bold", zorder=12)

        buf = io.BytesIO()
        plt.tight_layout(pad=0)
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"planoBase64": f"data:image/png;base64,{b64}", "tipo_distribucion": tipo}

    except Exception as e:
        logger.error(f"plano-2d error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo generar el plano: {e}")


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
                    "cocina y sus medidas, o pulsa «Detectar distribución» sobre un "
                    "render) y vuelve a intentarlo."))

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
                       "«Detectar distribución» sobre un render para deducirlas.")
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
            ax.text(cx, cy, t if len(t) <= cabe else t[:max(1, cabe - 1)] + "…",
                    ha="center", va="center", fontsize=6.5, rotation=90,
                    color=color or C_LINE)

        def _texto_modulo(ax, x, w, cy, txt):
            """Etiqueta dentro del módulo, ajustada a lo ancho que sea.

            Con módulos estrechos el texto horizontal se salía por los lados y se
            pisaba con el del vecino: en el alzado del 05/08 se leía
            "Mueble fregadeMueble altoMueble bajMueble alto". Por debajo de 45 cm
            se gira 90º, que es como se rotula un módulo estrecho en un plano.
            """
            if w >= 45:
                cabe = max(4, int(w * 0.92 / _cm_por_caracter(ax, 6.5)))
                lineas = [l if len(l) <= cabe else l[:max(1, cabe - 1)] + "…"
                          for l in txt.split("\n")]
                ax.text(x + w / 2, cy, "\n".join(lineas), ha="center", va="center", fontsize=6.5)
            elif w >= 22:
                _texto_vertical(ax, x + w / 2, cy, txt, ENC_Y - ZOC_Y)
            # Por debajo de 22 cm no cabe ni girado: lo dice la cota, no la etiqueta.

        herr = {"puertas": 0, "cajones": 0}  # recuento de herraje para el resumen
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
            cotas = []
            hob_zones = []   # (x, w) de las placas → la campana va justo encima
            bajos_xy = []    # (x, w) de los bajos REALES → los altos se alinean con ellos
            altos_xy = []    # (x, w) de los altos que vienen DADOS (no derivados)
            cotas_altos = [] # cotas de la fila colgada, que van sobre los altos
            for e in elems:
                w = int(e.get("ancho") or 60)
                tipo = str(e.get("id") or e.get("tipo") or "").lower()
                fila = str(e.get("fila") or "bajo").lower()
                if tipo == "campana":
                    continue  # se dibuja al final, centrada sobre la placa
                label = str(e.get("label") or tipo or "módulo")[:18]
                x = int(e.get("posicion_cm") or pos)
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
                    _ta = f"{label}\n{w}×{ALTOS_Y1 - ALTOS_Y0}" if _con_cotas else label
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
                        if _con_cotas and w >= 40:
                            ax.text(x + w / 2, yy + fh / 2, f"{fh:g}", ha="center", va="center",
                                    fontsize=6, color=C_FRENTE)
                        # Tirador horizontal centrado, junto al canto superior del frente.
                        tirador_h(ax, x + w / 2, yy + fh - 3, length=min(16, w * 0.5))
                        herr["cajones"] += 1
                    # Dentro del módulo, no debajo: ahí abajo están las cotas y se
                    # pisaban ("Módulo bajo cajone…" encima del 10 del zócalo).
                    _texto_vertical(ax, x + w / 2, (ZOC_Y + ENC_Y) / 2, label,
                                    ENC_Y - ZOC_Y, color=C_LINE)
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
                if fila == "alto" or tipo in ALTOS:
                    cotas_altos.append((x, x + w, f"{w}"))
                else:
                    cotas.append((x, x + w, f"{w}"))
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
                    herr["puertas"] += 1
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

        # Resumen de herraje (recuento aproximado a partir de puertas y cajones).
        puertas = herr["puertas"]; cajones = herr["cajones"]
        bisagras = puertas * 2                 # 2 bisagras por puerta (estándar)
        guias = cajones                        # 1 juego de guías por frente de cajón
        tiradores = puertas + cajones          # 1 tirador por puerta y por frente
        resumen = (f"HERRAJE (aprox.):  {puertas} puertas · {cajones} cajones/gavetas   |   "
                   f"{bisagras} bisagras · {guias} juegos de guías · {tiradores} tiradores")
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
            "Eres proyectista de cocinas. Analiza esta imagen (render o croquis de cocina) y deduce su "
            "DISTRIBUCIÓN. Identifica el tipo (lineal, l, u, paralela, isla, g), las PAREDES con muebles y, "
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
            + escala_nota +
            "Devuelve SOLO un JSON con esta forma exacta:\n"
            "{\"tipo\":\"l\",\"paredes\":[{\"nombre\":\"Pared principal\",\"ancho\":370,\"alto\":240,"
            "\"ancho_escrito\":false}],"
            "\"elementos\":[{\"id\":\"frigorifico\",\"label\":\"Frigorífico\",\"pared_idx\":0,"
            "\"posicion_cm\":0,\"ancho\":60,\"medida_escrita\":false}]}. "
            "'posicion_cm' es la distancia desde el inicio de la pared. "
            "id usa palabras clave: frigorifico, congelador, columna_hornos, horno, microondas, lavavajillas, "
            "fregadero, placa, campana, mueble, cajonera, despensa, vinoteca. "
            "Distingue CAJONERA (frentes de cajón apilados) de mueble de PUERTA: son cosas distintas y el "
            "herraje no es el mismo."
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
            try:
                anc = int(round(float(e.get("ancho") or 60)))
                pos = int(round(float(e.get("posicion_cm") or 0)))
                pidx = int(e.get("pared_idx") or 0)
            except (TypeError, ValueError):
                continue
            elementos.append({
                "id": str(e.get("id") or "mueble").lower().strip().replace(" ", "_"),
                "label": str(e.get("label") or e.get("id") or "Módulo")[:24],
                "pared_idx": max(0, pidx), "posicion_cm": max(0, pos), "ancho": max(10, anc),
                "medida_escrita": bool(e.get("medida_escrita")),
            })
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


def _sanea_distribucion(data: dict, ancho_real: int, alto_real: int) -> dict:
    """Sanea + normaliza una distribución {paredes, elementos} (mismo criterio que
    detect-distribucion): reescala módulos a estándar y los recoloca contiguos."""
    paredes = []
    for p in (data.get("paredes") or [])[:4]:
        try:
            anc = int(round(float(p.get("ancho") or 0)))
            alt = int(round(float(p.get("alto") or 240)))
        except (TypeError, ValueError):
            continue
        if anc > 0:
            paredes.append({"nombre": str(p.get("nombre") or f"Pared {len(paredes)+1}"), "ancho": anc, "alto": alt or 240})
    elementos = []
    for e in (data.get("elementos") or [])[:40]:
        try:
            anc = int(round(float(e.get("ancho") or 60)))
            pos = int(round(float(e.get("posicion_cm") or 0)))
            pidx = int(e.get("pared_idx") or 0)
        except (TypeError, ValueError):
            continue
        elementos.append({
            "id": str(e.get("id") or "mueble").lower().strip().replace(" ", "_"),
            "label": str(e.get("label") or e.get("id") or "Módulo")[:24],
            "pared_idx": max(0, pidx), "posicion_cm": max(0, pos), "ancho": max(10, anc),
        })
    if not paredes:
        paredes = [{"nombre": "Pared principal", "ancho": ancho_real or 400, "alto": alto_real or 240}]
    STD = [15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120]
    _snap = lambda w: min(STD, key=lambda s: abs(s - w))
    if ancho_real and paredes:
        paredes[0]["ancho"] = ancho_real
        if alto_real:
            paredes[0]["alto"] = alto_real
    norm = []
    for pidx, pared in enumerate(paredes):
        grupo = sorted([e for e in elementos if e["pared_idx"] == pidx], key=lambda e: e["posicion_cm"])
        if not grupo:
            continue
        suma = sum(e["ancho"] for e in grupo) or 1
        factor = pared["ancho"] / suma
        for e in grupo:
            e["ancho"] = max(15, _snap(e["ancho"] * factor))
        desfase = pared["ancho"] - sum(e["ancho"] for e in grupo)
        if desfase and grupo:
            i = max(range(len(grupo)), key=lambda i: grupo[i]["ancho"])
            grupo[i]["ancho"] = max(15, grupo[i]["ancho"] + desfase)
        x = 0
        for e in grupo:
            e["posicion_cm"] = x; x += e["ancho"]
        norm.extend(grupo)
    return {"tipo": str(data.get("tipo") or "lineal"), "paredes": paredes, "elementos": norm or elementos, "isla": {}, "medidasReales": bool(ancho_real)}


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
