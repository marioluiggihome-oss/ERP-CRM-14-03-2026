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
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

logger = logging.getLogger("estudio_cocinas")

# ─── Auth ─────────────────────────────────────────────────────────────────────
try:
    from services.jwt_service import require_auth
    _DEPS = [Depends(require_auth)]
except Exception:
    _DEPS = []

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
    """Parsea texto libre de medidas → dict con ancho, alto, isla_w, isla_h en cm."""
    nums = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:cm|m)?', (texto or "").lower())
    vals = [float(n.replace(',', '.')) for n in nums if float(n.replace(',', '.')) > 0]
    vals_cm = [int(v * 100) if v < 20 else int(v) for v in vals]
    return {
        "ancho":  vals_cm[0] if len(vals_cm) > 0 else 400,
        "alto":   vals_cm[1] if len(vals_cm) > 1 else 350,
        "isla_w": vals_cm[2] if len(vals_cm) > 2 else 200,
        "isla_h": vals_cm[3] if len(vals_cm) > 3 else 100,
    }

# ─── Modelos ──────────────────────────────────────────────────────────────────

class RenderInput(BaseModel):
    descripcion: str = Field(..., description="Descripción libre de la cocina")
    estilo: Optional[str] = Field(default="Moderno", description="Estilo de diseño")
    materiales: Optional[str] = Field(default="", description="Materiales específicos")
    distribucion: Optional[str] = Field(default="", description="Distribución (L, U, isla...)")
    croquis_b64: Optional[str] = Field(default=None, description="Croquis en base64 (opcional)")
    modo_async: Optional[bool] = Field(default=False, description="Si True devuelve task_id sin esperar")

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
    distribucion = payload.distribucion or payload.descripcion
    materiales = payload.materiales or "encimera de silestone, muebles lacados en mate"
    estilo = payload.estilo or "Moderno"

    prompt_tecnico = _generate_render_prompt(
        layout=distribucion,
        materials=materiales,
        style=estilo,
        extra=payload.descripcion if payload.distribucion else "",
    )

    # Instrucción completa para Manus
    instruccion = (
        f"Genera un render fotorrealista de alta gama de una cocina.\n\n"
        f"DESCRIPCIÓN DEL PROYECTO:\n{payload.descripcion}\n\n"
        f"PROMPT TÉCNICO DE RENDER:\n{prompt_tecnico}\n\n"
        f"REQUISITOS:\n"
        f"- Render fotorrealista 8K, iluminación cinematográfica\n"
        f"- Perspectiva angular desde esquina, formato 16:9\n"
        f"- Calidad de revista de interiorismo de lujo\n"
        f"- Texturas hiper-detalladas con ray tracing\n"
        f"- Devuelve SOLO la imagen generada, sin texto adicional"
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

    # Crear tarea en Manus API
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
    if not engine or engine.get_status().get("status") != "active":
        raise HTTPException(status_code=503, detail="Motor de IA no disponible.")

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
    No requiere motor de IA — generación local instantánea.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        m = _parse_medidas(payload.medidas)
        ancho, alto, isla_w, isla_h = m["ancho"], m["alto"], m["isla_w"], m["isla_h"]

        C_BG = "#F8F6F2"; C_SUELO = "#EDE8E0"; C_PARED = "#2C2C2C"
        C_MUEBLE = "#D4C5A9"; C_BORDE = "#8B7355"; C_ENCIM = "#C8B89A"
        C_ISLA = "#E8DDD0"; C_COTA = "#555555"; C_ACENTO = "#8B7355"
        C_GRID = "#D8D0C4"

        fig, ax = plt.subplots(figsize=(16, 11))
        fig.patch.set_facecolor(C_BG)
        ax.set_facecolor(C_BG)

        scale = min(560 / ancho, 420 / alto)
        W, H = ancho * scale, alto * scale
        ox, oy = 80, 70

        ax.set_xlim(0, W + 160); ax.set_ylim(0, H + 130)
        ax.set_aspect("equal"); ax.axis("off")

        # Suelo + grid
        ax.add_patch(patches.Rectangle((ox, oy), W, H,
            linewidth=2, edgecolor=C_PARED, facecolor=C_SUELO, zorder=1))
        paso = max(30, int(min(ancho, alto) / 10)) * scale / 100 * 100
        for x in range(int(ox), int(ox + W + 1), max(1, int(paso))):
            ax.plot([x, x], [oy, oy + H], color=C_GRID, linewidth=0.3, zorder=1)
        for y in range(int(oy), int(oy + H + 1), max(1, int(paso))):
            ax.plot([ox, ox + W], [y, y], color=C_GRID, linewidth=0.3, zorder=1)

        # Paredes
        pw = max(6, int(0.015 * min(W, H)))
        for rect in [(ox, oy + H - pw, W, pw), (ox, oy, W, pw),
                     (ox, oy, pw, H), (ox + W - pw, oy, pw, H)]:
            ax.add_patch(patches.Rectangle(
                (rect[0], rect[1]), rect[2], rect[3],
                linewidth=0, facecolor=C_PARED, zorder=2))

        # Módulos norte
        mod = 55 * scale / 100
        x = ox + pw
        while x + mod <= ox + W - pw:
            ax.add_patch(patches.Rectangle((x, oy + H - pw - mod), mod, mod,
                linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
            x += mod
        ax.add_patch(patches.Rectangle(
            (ox + pw, oy + H - pw - mod), W - 2 * pw, 3,
            linewidth=0, facecolor=C_ENCIM, alpha=0.7, zorder=4))

        # Módulos oeste
        y = oy + pw
        while y + mod <= oy + H - pw - mod:
            ax.add_patch(patches.Rectangle((ox + pw, y), mod, mod,
                linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
            y += mod
        ax.add_patch(patches.Rectangle(
            (ox + pw + mod, oy + pw), 3, H - 2 * pw - mod,
            linewidth=0, facecolor=C_ENCIM, alpha=0.7, zorder=4))

        # Isla
        iw = isla_w * scale / 100; ih = isla_h * scale / 100
        ix = ox + (W - iw) / 2; iy = oy + (H - ih) / 2 - 15
        ax.add_patch(patches.Rectangle((ix, iy), iw, ih,
            linewidth=2, edgecolor=C_BORDE, facecolor=C_ISLA, zorder=3))
        ax.text(ix + iw / 2, iy + ih / 2, f"ISLA\n{isla_w}×{isla_h} cm",
            ha="center", va="center", fontsize=7.5, fontweight="bold",
            color="#1A1A1A", zorder=5)

        # Fregadero
        fx = ox + pw + mod / 2; fy = oy + H - pw - mod / 2
        ax.add_patch(patches.FancyBboxPatch(
            (fx - 18 * scale / 100, fy - 12 * scale / 100),
            36 * scale / 100, 24 * scale / 100,
            boxstyle="round,pad=2", linewidth=1,
            edgecolor="#555", facecolor="#B8D4E0", zorder=5))
        ax.text(fx, fy, "≈", ha="center", va="center", fontsize=8, color="#555", zorder=6)

        # Etiquetas paredes
        for label, x_, y_, rot in [
            ("PARED NORTE", ox + W / 2, oy + H + 8, 0),
            ("PARED SUR",   ox + W / 2, oy - 8, 0),
            ("PARED OESTE", ox - 8, oy + H / 2, 90),
            ("PARED ESTE",  ox + W + 8, oy + H / 2, 90),
        ]:
            ax.text(x_, y_, label, ha="center", va="center",
                fontsize=5.5, color="#888", rotation=rot, zorder=6)

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
        cota_h(ox, ox + W, oy - 22, f"{ancho} cm")
        cota_v(ox - 22, oy, oy + H, f"{alto} cm")
        cota_h(ix, ix + iw, iy - 12, f"{isla_w} cm")
        cota_v(ix + iw + 10, iy, iy + ih, f"{isla_h} cm")

        # Leyenda
        lx = ox + W + 20; ly = oy + H - 10
        items = [(C_MUEBLE, C_BORDE, "Módulo bajo"), (C_ENCIM, C_BORDE, "Encimera"),
                 (C_ISLA, C_BORDE, "Isla central"), ("#B8D4E0", "#555", "Fregadero")]
        ax.text(lx, ly + 15, "LEYENDA", fontsize=7, fontweight="bold", color=C_ACENTO)
        for i, (fc, ec, lbl) in enumerate(items):
            yy = ly - i * 18
            ax.add_patch(patches.Rectangle((lx, yy - 6), 12, 10,
                linewidth=0.8, edgecolor=ec, facecolor=fc))
            ax.text(lx + 16, yy, lbl, fontsize=6.5, va="center", color=C_COTA)

        # Cajetín
        ax.add_patch(patches.Rectangle((ox, 0), W, 52,
            linewidth=1.2, edgecolor=C_ACENTO, facecolor="#F0EBE3", zorder=10))
        ax.plot([ox, ox + W], [30, 30], color=C_ACENTO, linewidth=0.7, zorder=11)
        ax.text(ox + W / 2, 42,
            f"PLANO DE DISTRIBUCIÓN — {(payload.nombre_cliente or 'CLIENTE').upper()} · {(payload.estilo or 'MODERNO').upper()}",
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="#1A1A1A", zorder=12)
        ax.text(ox + 10, 18, f"MEDIDAS: {ancho}×{alto} cm",
            ha="left", va="center", fontsize=6.5, color=C_COTA, zorder=12)
        ax.text(ox + W / 2, 18, "ESCALA 1:20",
            ha="center", va="center", fontsize=6.5, color=C_COTA, zorder=12)
        ax.text(ox + W - 10, 18, "3D ESTUDIO",
            ha="right", va="center", fontsize=6.5, color=C_ACENTO,
            fontweight="bold", zorder=12)

        buf = io.BytesIO()
        plt.tight_layout(pad=0)
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"planoBase64": f"data:image/png;base64,{b64}", "medidas_parseadas": m}

    except Exception as e:
        logger.error(f"plano-2d error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo generar el plano: {e}")


@router.post("/ficha-tecnica")
async def generar_ficha_tecnica(payload: ProyectoBase):
    """Genera ficha técnica en Markdown. Generación local instantánea."""
    fecha = datetime.date.today().strftime("%d/%m/%Y")
    mes_anio = datetime.date.today().strftime("%B %Y")
    ref = f"COC-{datetime.date.today().strftime('%Y%m%d')}-{abs(hash(payload.nombre_cliente or '')) % 1000:03d}"
    m = _parse_medidas(payload.medidas)

    md = f"""# Ficha Técnica — Cocina {payload.estilo or 'Moderna'} · {payload.nombre_cliente or 'Cliente'}

| | |
|:--|:--|
| **Referencia** | `{ref}` |
| **Fecha** | {fecha} |
| **Cliente** | {payload.nombre_cliente or '—'} |
| **Estilo** | {payload.estilo or 'Moderno'} |
| **Medidas** | {m['ancho']}×{m['alto']} cm (isla: {m['isla_w']}×{m['isla_h']} cm) |
| **Presupuesto** | {payload.presupuesto or 'A consultar'} |

---

## Descripción del Proyecto

{payload.descripcion or f"Proyecto de diseño de cocina estilo {payload.estilo or 'moderno'} para {payload.nombre_cliente or 'el cliente'}."}

{f"> **Notas del cliente:** {payload.notas}" if payload.notas else ""}

---

## Materiales y Acabados Propuestos

| Elemento | Material / Acabado | Referencia | Garantía |
|:--|:--|:--|:--|
| **Frentes bajos** | Laca seda anti-huellas | LACA-BL-01 | 10 años |
| **Frentes altos** | Chapa de roble natural | ROBLE-NAT-05 | 10 años |
| **Encimera** | Silestone Calacatta Gold 20 mm | SIL-CAL-GOLD | 25 años |
| **Tiradores** | Sistema Gola integrado | GOLA-ALU-BL | 10 años |
| **Zócalos** | Aluminio lacado 10 cm | ZOC-ALU-10 | 10 años |
| **Suelo** | Porcelánico gran formato 120×60 | PORC-GF-GR | — |

---

## Electrodomésticos Propuestos

- **Frigorífico:** Combi integrable 90 cm — Liebherr / Miele
- **Horno:** Multifunción pirolítico 60 cm — Siemens iQ700
- **Placa:** Inducción con extractor integrado 80 cm — Bora / Neff
- **Lavavajillas:** Totalmente integrable 60 cm — Bosch Serie 8
- **Fregadero:** Bajo encimera, grifería latón cepillado — Blanco / Franke

---

## Instalaciones

| Elemento | Especificación |
|:--|:--|
| **Enchufes encimera** | 1 cada 120 cm a 110 cm del suelo (línea dedicada 16A) |
| **Toma de agua** | Fría + caliente + desagüe bajo fregadero |
| **Extractor** | Salida de humos ∅150 mm o recirculación |
| **Iluminación** | LED 3.000K bajo muebles + colgante isla |

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
    """Genera presentación HTML para cliente. Generación local instantánea."""
    fecha = datetime.date.today().strftime("%d/%m/%Y")
    estilo = payload.estilo or "Moderno"
    cliente = payload.nombre_cliente or "Cliente"
    m = _parse_medidas(payload.medidas)
    medidas_str = f"{m['ancho']}×{m['alto']} cm"
    presupuesto = payload.presupuesto or "A consultar"
    descripcion = payload.descripcion or f"Una cocina de diseño {estilo.lower()} pensada para adaptarse perfectamente a su espacio y estilo de vida."
    notas = payload.notas or ""

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
    <div class="card"><h3>Distribución</h3><p>Optimizada para el flujo de trabajo con isla central y módulos en L</p></div>
    <div class="card"><h3>Materiales</h3><p>Primera calidad con garantía de 10 años en todos los elementos fabricados</p></div>
    <div class="card"><h3>Electrodomésticos</h3><p>Alta gama totalmente integrados, selección personalizada según uso y presupuesto</p></div>
    <div class="card"><h3>Iluminación</h3><p>3 niveles: funcional bajo muebles, ambiental y decorativa sobre isla</p></div>
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


@router.post("/instalaciones")
async def generar_instalaciones(payload: InstalacionesInput):
    """
    Genera el plan de instalaciones (eléctrica, fontanería, gas) para la cocina.
    Generación local instantánea basada en las medidas y descripción.
    """
    m = _parse_medidas(payload.medidas)
    ancho = m["ancho"]
    alto = m["alto"]
    tiene_isla = m["isla_w"] > 0 and m["isla_h"] > 0
    desc_lower = (payload.descripcion or "").lower()
    tiene_gas = any(w in desc_lower for w in ["gas", "placa gas", "cocina gas"])
    tiene_vapor = any(w in desc_lower for w in ["vapor", "horno vapor"])
    tiene_cafe = any(w in desc_lower for w in ["café", "cafe", "cafetera"])

    # ── Puntos eléctricos ──
    puntos_elec = [
        {"tipo": "Enchufe encimera", "ubicacion": "Pared norte, cada 120 cm a 110 cm del suelo", "potencia": "16A"},
        {"tipo": "Circuito horno", "ubicacion": "Columna de hornos, línea dedicada", "potencia": "20A"},
        {"tipo": "Circuito lavavajillas", "ubicacion": "Bajo fregadero, línea dedicada", "potencia": "16A"},
        {"tipo": "Circuito frigorífico", "ubicacion": "Columna frigorífico, línea dedicada", "potencia": "16A"},
        {"tipo": "Circuito extractor/campana", "ubicacion": "Sobre placa, línea dedicada", "potencia": "10A"},
        {"tipo": "Iluminación LED bajo muebles", "ubicacion": "Bajo muebles superiores, toda la longitud", "potencia": "5A"},
        {"tipo": "Iluminación zona isla", "ubicacion": "Techo sobre isla central", "potencia": "5A"} if tiene_isla else None,
        {"tipo": "Circuito placa inducción", "ubicacion": "Encimera, línea trifásica dedicada", "potencia": "32A"},
    ]
    if tiene_vapor:
        puntos_elec.append({"tipo": "Circuito horno vapor", "ubicacion": "Columna hornos, línea dedicada", "potencia": "20A"})
    if tiene_cafe:
        puntos_elec.append({"tipo": "Circuito cafetera integrada", "ubicacion": "Columna hornos o mueble dedicado", "potencia": "16A"})

    puntos_elec = [p for p in puntos_elec if p is not None]

    circuitos_str = (
        f"Se recomienda cuadro de distribución con {len(puntos_elec)} circuitos independientes. "
        f"Potencia total estimada: {sum(int(p['potencia'].replace('A','')) for p in puntos_elec)} A. "
        "Todos los circuitos con protección diferencial 30 mA."
    )

    # ── Fontanería ──
    puntos_agua = [
        {"tipo": "Toma de agua fría", "ubicacion": "Bajo fregadero, válvula de corte individual"},
        {"tipo": "Toma de agua caliente", "ubicacion": "Bajo fregadero, válvula de corte individual"},
        {"tipo": "Desagüe fregadero", "ubicacion": "Bajo fregadero, sifón con tapa de registro, ∅40 mm"},
        {"tipo": "Desagüe lavavajillas", "ubicacion": "Junto al fregadero, conexión al sifón"},
    ]
    if tiene_isla:
        puntos_agua.append({"tipo": "Toma de agua isla (opcional)", "ubicacion": "Bajo isla central, requiere paso por suelo"})
    if tiene_vapor:
        puntos_agua.append({"tipo": "Toma de agua horno vapor", "ubicacion": "Columna hornos, toma directa con filtro"})

    # ── Gas ──
    puntos_gas = []
    if tiene_gas:
        puntos_gas = [
            {"tipo": "Toma de gas placa", "ubicacion": "Encimera, llave de corte individual bajo mueble"},
            {"tipo": "Llave de paso general", "ubicacion": "Accesible, exterior al mueble de placa"},
        ]

    notas = (
        f"Cocina de {ancho}×{alto} cm, estilo {payload.estilo or 'Moderno'}. "
        "Todas las instalaciones deben ser realizadas por instaladores certificados. "
        "Se recomienda dejar rozas en paredes antes del alicatado. "
        "Verificar normativa local vigente (REBT para eléctrica, RITE para fontanería)."
    )

    return {
        "electrica": {
            "puntos": puntos_elec,
            "circuitos": circuitos_str,
        },
        "fontaneria": {
            "puntos": puntos_agua,
        },
        "gas": {
            "puntos": puntos_gas,
        } if tiene_gas else None,
        "notas": notas,
        "medidas_parseadas": m,
        "cliente": payload.nombre_cliente,
        "fecha": datetime.date.today().strftime("%d/%m/%Y"),
    }


# ─── Galería de renders ────────────────────────────────────────────────────────

from motor.motor_asyncio import AsyncIOMotorClient as _MotorClient
from bson import ObjectId as _ObjectId

_MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
_DB_NAME   = os.environ.get("DB_NAME", "luiggi_home")
_mongo_client = _MotorClient(_MONGO_URL)
_galeria_db   = _mongo_client[_DB_NAME]["renders_galeria"]


class GaleriaGuardarPayload(BaseModel):
    image_url: str
    cliente: str = ""
    descripcion: str = ""
    estilo: str = ""
    medidas: str = ""
    presupuesto: str = ""


@router.post("/galeria/guardar")
async def galeria_guardar(payload: GaleriaGuardarPayload):
    """Guarda un render generado en la galería MongoDB."""
    doc = {
        "image_url": payload.image_url,
        "cliente": payload.cliente,
        "descripcion": payload.descripcion,
        "estilo": payload.estilo,
        "medidas": payload.medidas,
        "presupuesto": payload.presupuesto,
        "fecha": datetime.datetime.utcnow(),
        "favorito": False,
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
