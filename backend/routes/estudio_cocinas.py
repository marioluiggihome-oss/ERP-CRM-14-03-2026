"""
Estudio de Cocinas — Router Maestro Unificado
==============================================
Consolida y orquesta todos los módulos de diseño de cocinas del ERP:
  · cocinasai.py         → render desde planos (Gemini)
  · ai_engine.py         → motor LuiggiAI (render por texto/voz, transcripción)
  · kitchen_projects.py  → CRUD proyectos, medidas, muebles, aprobación

Nuevas capacidades exclusivas de este módulo:
  POST /estudio-cocinas/plano-2d          → Plano técnico 2D (matplotlib, base64 PNG)
  POST /estudio-cocinas/ficha-tecnica     → Ficha técnica en Markdown
  POST /estudio-cocinas/presentacion      → Presentación HTML para cliente
  POST /estudio-cocinas/transcribir-audio → Transcripción de audio a texto (voz → descripción)
  POST /estudio-cocinas/render-rapido     → Render rápido sin proyecto (texto libre)
  GET  /estudio-cocinas/estado            → Estado del módulo y capacidades disponibles

Todos los endpoints requieren JWT. El módulo no duplica lógica existente:
reutiliza los servicios ya disponibles (llm_vision, luiggi_ai, kitchen_projects).
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
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
    tags=["Estudio de Cocinas"],
    dependencies=_DEPS,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _strip_b64(b64: str) -> str:
    if isinstance(b64, str) and b64.startswith("data:"):
        return b64.split(",", 1)[1]
    return b64


def _parse_medidas(texto: str) -> dict:
    """
    Parsea texto libre de medidas y devuelve un dict con ancho, alto, isla_w, isla_h.
    Soporta: "3x4m", "300x400cm", "Pared A: 3m, Pared B: 4m", etc.
    """
    nums = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:cm|m)?', (texto or "").lower())
    vals = [float(n.replace(',', '.')) for n in nums if float(n.replace(',', '.')) > 0]
    # Convertir a cm si parecen metros (< 20)
    vals_cm = [int(v * 100) if v < 20 else int(v) for v in vals]
    return {
        "ancho": vals_cm[0] if len(vals_cm) > 0 else 400,
        "alto":  vals_cm[1] if len(vals_cm) > 1 else 350,
        "isla_w": vals_cm[2] if len(vals_cm) > 2 else 200,
        "isla_h": vals_cm[3] if len(vals_cm) > 3 else 100,
    }


# ─── Modelos ──────────────────────────────────────────────────────────────────

class ProyectoBase(BaseModel):
    nombre_cliente: Optional[str] = Field(default="Cliente", description="Nombre del cliente")
    descripcion: Optional[str] = Field(default="", description="Descripción libre del proyecto")
    estilo: Optional[str] = Field(default="Moderno", description="Estilo de diseño")
    notas: Optional[str] = Field(default="", description="Notas adicionales del cliente")
    medidas: Optional[str] = Field(default="", description="Medidas en texto libre: '4x3m isla 2x1m'")
    presupuesto: Optional[str] = Field(default="", description="Rango de presupuesto")
    croquis_b64: Optional[str] = Field(default=None, description="Croquis en base64 (opcional)")


class EditarRenderInput(BaseModel):
    render_b64: str = Field(..., description="Render previo en base64")
    instruccion: str = Field(..., description="Instrucción de edición en lenguaje natural")


class RenderRapidoInput(BaseModel):
    descripcion: str = Field(..., description="Descripción en lenguaje natural")
    estilo: Optional[str] = Field(default="Moderno")
    croquis_b64: Optional[str] = Field(default=None)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/estado")
async def estado_modulo():
    """
    Devuelve el estado del módulo y qué capacidades están disponibles
    según las variables de entorno configuradas.
    """
    from services.llm_vision import get_gemini_key, GOOGLE_GENAI_AVAILABLE
    gemini_ok = bool(get_gemini_key() and GOOGLE_GENAI_AVAILABLE)

    manus_key = os.environ.get("MANUS_API_KEY", "")
    manus_ok = bool(manus_key)

    return {
        "modulo": "Estudio de Cocinas",
        "version": "2.0.0",
        "capacidades": {
            "render_ia": gemini_ok or manus_ok,
            "render_gemini": gemini_ok,
            "render_luiggi_ai": manus_ok,
            "plano_2d": True,
            "ficha_tecnica": True,
            "presentacion_html": True,
            "transcripcion_audio": manus_ok,
        },
        "motores_disponibles": (
            ["Gemini"] if gemini_ok else []
        ) + (
            ["LuiggiAI"] if manus_ok else []
        ),
    }


@router.post("/render-rapido")
async def render_rapido(payload: RenderRapidoInput):
    """
    Genera un render fotorrealista de cocina a partir de descripción en texto libre.
    Usa el motor disponible: LuiggiAI (Manus) si está configurado, Gemini como fallback.
    Devuelve: { imageUrl, motor_usado, timestamp }
    """
    # Intentar primero con LuiggiAI (motor principal del ERP)
    manus_key = os.environ.get("MANUS_API_KEY", "")
    if manus_key:
        try:
            from services.luiggi_ai import get_render_service
            render_svc = get_render_service()
            result = await render_svc.generate_render(
                description=payload.descripcion,
                style=payload.estilo or "photorealistic",
                reference_image_base64=_strip_b64(payload.croquis_b64) if payload.croquis_b64 else None,
            )
            if result and result.get("images"):
                return {
                    "imageUrl": result["images"][0],
                    "motor_usado": "LuiggiAI",
                    "timestamp": int(time.time()),
                }
        except Exception as e:
            logger.warning(f"LuiggiAI render falló, intentando Gemini: {e}")

    # Fallback: Gemini
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(
                status_code=503,
                detail="Ningún motor de IA disponible. Configura MANUS_API_KEY o GEMINI_API_KEY."
            )
        prompt = (
            f"Render fotorrealista de alta gama de una cocina estilo '{payload.estilo}'. "
            f"Descripción: {payload.descripcion}. "
            "Estilo Octane/Corona Renderer, iluminación natural, texturas premium, "
            "perspectiva angular desde esquina, formato 16:9."
        )
        refs = None
        if payload.croquis_b64:
            refs = [{"data": _strip_b64(payload.croquis_b64), "mime": "image/png"}]
        data_url = await generate_image_with_gemini(prompt=prompt, reference_images=refs)
        if not data_url:
            raise HTTPException(status_code=502, detail="La IA no devolvió imagen.")
        return {"imageUrl": data_url, "motor_usado": "Gemini", "timestamp": int(time.time())}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"render_rapido error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo generar el render: {e}")


@router.post("/render/editar")
async def editar_render(payload: EditarRenderInput):
    """
    Edita un render existente en lenguaje natural.
    Ej: "Cambia los muebles a color antracita" o "Añade una ventana en la pared norte"
    """
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible.")
        prompt = (
            f"Revisión técnica de proyecto de cocina. Modifica este render siguiendo: \"{payload.instruccion}\". "
            "Mantén la distribución, muros, ventanas y puertas inalterados salvo que se indique explícitamente. "
            "Conserva la iluminación fotorrealista y la calidad de los materiales. Formato 16:9."
        )
        data_url = await generate_image_with_gemini(
            prompt=prompt,
            reference_image_base64=_strip_b64(payload.render_b64),
            reference_mime="image/png",
        )
        if not data_url:
            raise HTTPException(status_code=502, detail="La IA no devolvió imagen.")
        return {"imageUrl": data_url, "timestamp": int(time.time())}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"render/editar error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo editar el render: {e}")


@router.post("/transcribir-audio")
async def transcribir_audio(audio: UploadFile = File(...)):
    """
    Transcribe un archivo de audio (voz del diseñador o del cliente) a texto.
    Soporta: mp3, wav, m4a, webm, ogg.
    Devuelve: { texto, duracion_estimada }
    """
    try:
        from services.luiggi_ai import get_engine
        engine = get_engine()
        audio_bytes = await audio.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        result = await engine.transcribe_audio(
            audio_base64=audio_b64,
            mime_type=audio.content_type or "audio/mpeg",
        )
        return {
            "texto": result.get("text", ""),
            "idioma": result.get("language", "es"),
            "duracion_estimada": result.get("duration_seconds"),
        }
    except Exception as e:
        logger.error(f"transcribir_audio error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo transcribir el audio: {e}")


@router.post("/plano-2d")
async def generar_plano_2d(payload: ProyectoBase):
    """
    Genera un plano 2D técnico acotado de la cocina usando matplotlib.
    Parsea las medidas del texto libre del payload.
    Devuelve: { planoBase64, medidas_parseadas }
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.patches import FancyArrowPatch

        m = _parse_medidas(payload.medidas)
        ancho, alto, isla_w, isla_h = m["ancho"], m["alto"], m["isla_w"], m["isla_h"]

        # ── Constantes de estilo ───────────────────────────────────────────
        C_BG      = "#F8F6F2"
        C_SUELO   = "#EDE8E0"
        C_PARED   = "#2C2C2C"
        C_MUEBLE  = "#D4C5A9"
        C_BORDE   = "#8B7355"
        C_ENCIM   = "#C8B89A"
        C_ISLA    = "#E8DDD0"
        C_COTA    = "#555555"
        C_ACENTO  = "#8B7355"
        C_GRID    = "#D8D0C4"

        # ── Canvas ────────────────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(16, 11))
        fig.patch.set_facecolor(C_BG)
        ax.set_facecolor(C_BG)

        scale = min(560 / ancho, 420 / alto)
        W, H = ancho * scale, alto * scale
        ox, oy = 80, 70

        ax.set_xlim(0, W + 160)
        ax.set_ylim(0, H + 130)
        ax.set_aspect("equal")
        ax.axis("off")

        # ── Suelo ─────────────────────────────────────────────────────────
        ax.add_patch(patches.Rectangle((ox, oy), W, H,
            linewidth=2, edgecolor=C_PARED, facecolor=C_SUELO, zorder=1))
        paso = max(30, int(min(ancho, alto) / 10)) * scale / 100 * 100
        for x in range(int(ox), int(ox + W + 1), int(paso)):
            ax.plot([x, x], [oy, oy + H], color=C_GRID, linewidth=0.3, zorder=1)
        for y in range(int(oy), int(oy + H + 1), int(paso)):
            ax.plot([ox, ox + W], [y, y], color=C_GRID, linewidth=0.3, zorder=1)

        # ── Paredes ───────────────────────────────────────────────────────
        pw = max(6, int(0.015 * min(W, H)))
        for rect in [
            (ox, oy + H - pw, W, pw),   # Norte
            (ox, oy, W, pw),             # Sur
            (ox, oy, pw, H),             # Oeste
            (ox + W - pw, oy, pw, H),    # Este
        ]:
            ax.add_patch(patches.Rectangle(
                (rect[0], rect[1]), rect[2], rect[3],
                linewidth=0, facecolor=C_PARED, zorder=2))

        # ── Módulos norte ─────────────────────────────────────────────────
        mod = 55 * scale / 100
        x = ox + pw
        while x + mod <= ox + W - pw:
            ax.add_patch(patches.Rectangle((x, oy + H - pw - mod), mod, mod,
                linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
            x += mod
        ax.add_patch(patches.Rectangle(
            (ox + pw, oy + H - pw - mod), W - 2 * pw, 3,
            linewidth=0, facecolor=C_ENCIM, alpha=0.7, zorder=4))

        # ── Módulos oeste ─────────────────────────────────────────────────
        y = oy + pw
        while y + mod <= oy + H - pw - mod:
            ax.add_patch(patches.Rectangle((ox + pw, y), mod, mod,
                linewidth=0.8, edgecolor=C_BORDE, facecolor=C_MUEBLE, zorder=3))
            y += mod
        ax.add_patch(patches.Rectangle(
            (ox + pw + mod, oy + pw), 3, H - 2 * pw - mod,
            linewidth=0, facecolor=C_ENCIM, alpha=0.7, zorder=4))

        # ── Isla central ──────────────────────────────────────────────────
        iw = isla_w * scale / 100
        ih = isla_h * scale / 100
        ix = ox + (W - iw) / 2
        iy = oy + (H - ih) / 2 - 15
        ax.add_patch(patches.Rectangle((ix, iy), iw, ih,
            linewidth=2, edgecolor=C_BORDE, facecolor=C_ISLA, zorder=3))
        ax.text(ix + iw / 2, iy + ih / 2,
            f"ISLA\n{isla_w}×{isla_h} cm",
            ha="center", va="center", fontsize=7.5, fontweight="bold",
            color="#1A1A1A", zorder=5)

        # ── Fregadero (símbolo) ───────────────────────────────────────────
        fx = ox + pw + mod / 2
        fy = oy + H - pw - mod / 2
        ax.add_patch(patches.FancyBboxPatch(
            (fx - 18 * scale / 100, fy - 12 * scale / 100),
            36 * scale / 100, 24 * scale / 100,
            boxstyle="round,pad=2", linewidth=1,
            edgecolor="#555", facecolor="#B8D4E0", zorder=5))
        ax.text(fx, fy, "≈", ha="center", va="center",
            fontsize=8, color="#555", zorder=6)

        # ── Etiquetas de paredes ──────────────────────────────────────────
        for label, x_, y_, rot in [
            ("PARED NORTE", ox + W / 2, oy + H + 8, 0),
            ("PARED SUR",   ox + W / 2, oy - 8, 0),
            ("PARED OESTE", ox - 8, oy + H / 2, 90),
            ("PARED ESTE",  ox + W + 8, oy + H / 2, 90),
        ]:
            ax.text(x_, y_, label, ha="center", va="center",
                fontsize=5.5, color="#888", rotation=rot, zorder=6)

        # ── Cotas ─────────────────────────────────────────────────────────
        arrow_kw = dict(arrowstyle="<->", color=C_COTA, lw=0.9)

        def cota_h(x1, x2, y, label):
            ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=arrow_kw)
            ax.text((x1 + x2) / 2, y + 6, label,
                ha="center", va="bottom", fontsize=6.5, color=C_COTA)

        def cota_v(x, y1, y2, label):
            ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=arrow_kw)
            ax.text(x - 6, (y1 + y2) / 2, label,
                ha="right", va="center", fontsize=6.5, color=C_COTA, rotation=90)

        cota_h(ox, ox + W, oy - 22, f"{ancho} cm")
        cota_v(ox - 22, oy, oy + H, f"{alto} cm")
        cota_h(ix, ix + iw, iy - 12, f"{isla_w} cm")
        cota_v(ix + iw + 10, iy, iy + ih, f"{isla_h} cm")

        # ── Leyenda ───────────────────────────────────────────────────────
        leyenda_x = ox + W + 20
        leyenda_y = oy + H - 10
        items = [
            (C_MUEBLE, C_BORDE, "Módulo bajo"),
            (C_ENCIM,  C_BORDE, "Encimera"),
            (C_ISLA,   C_BORDE, "Isla central"),
            ("#B8D4E0", "#555",  "Fregadero"),
        ]
        ax.text(leyenda_x, leyenda_y + 15, "LEYENDA",
            fontsize=7, fontweight="bold", color=C_ACENTO)
        for i, (fc, ec, lbl) in enumerate(items):
            yy = leyenda_y - i * 18
            ax.add_patch(patches.Rectangle(
                (leyenda_x, yy - 6), 12, 10,
                linewidth=0.8, edgecolor=ec, facecolor=fc))
            ax.text(leyenda_x + 16, yy, lbl,
                fontsize=6.5, va="center", color=C_COTA)

        # ── Cajetín del título ────────────────────────────────────────────
        ax.add_patch(patches.Rectangle(
            (ox, 0), W, 52,
            linewidth=1.2, edgecolor=C_ACENTO, facecolor="#F0EBE3", zorder=10))
        ax.plot([ox, ox + W], [30, 30], color=C_ACENTO, linewidth=0.7, zorder=11)
        ax.text(ox + W / 2, 42,
            f"PLANO DE DISTRIBUCIÓN — {payload.nombre_cliente.upper()} · {(payload.estilo or 'MODERNO').upper()}",
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="#1A1A1A", zorder=12)
        ax.text(ox + 10, 18, f"MEDIDAS: {ancho}×{alto} cm",
            ha="left", va="center", fontsize=6.5, color=C_COTA, zorder=12)
        ax.text(ox + W / 2, 18, "ESCALA 1:20",
            ha="center", va="center", fontsize=6.5, color=C_COTA, zorder=12)
        ax.text(ox + W - 10, 18, "ESTUDIO DE COCINAS",
            ha="right", va="center", fontsize=6.5, color=C_ACENTO,
            fontweight="bold", zorder=12)

        # ── Exportar ──────────────────────────────────────────────────────
        buf = io.BytesIO()
        plt.tight_layout(pad=0)
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {
            "planoBase64": f"data:image/png;base64,{b64}",
            "medidas_parseadas": m,
        }

    except Exception as e:
        logger.error(f"plano-2d error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo generar el plano: {e}")


@router.post("/ficha-tecnica")
async def generar_ficha_tecnica(payload: ProyectoBase):
    """
    Genera una ficha técnica completa en Markdown.
    Devuelve: { fichaMarkdown, referencia, fecha }
    """
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

*Ficha generada automáticamente · Estudio de Cocinas · {mes_anio}*
"""
    return {"fichaMarkdown": md, "referencia": ref, "fecha": fecha}


@router.post("/presentacion")
async def generar_presentacion(payload: ProyectoBase):
    """
    Genera una presentación HTML completa lista para mostrar al cliente.
    Incluye: portada, descripción, materiales, plazos y contacto.
    Devuelve: { presentacionHtml, cliente, fecha }
    """
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
  ul{{list-style:none;max-width:700px}}
  li{{padding:14px 0;border-bottom:1px solid rgba(200,169,110,.12);font-size:.95rem;padding-left:28px;position:relative;color:#C0B090}}
  li::before{{content:'';position:absolute;left:0;top:22px;width:8px;height:8px;background:#C8A96E;border-radius:50%}}
  .badge{{display:inline-block;background:rgba(200,169,110,.12);color:#C8A96E;font-size:.7rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;padding:6px 18px;margin-bottom:28px;border:1px solid rgba(200,169,110,.3)}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:40px;max-width:960px;margin-top:16px}}
  .card{{background:rgba(200,169,110,.06);border:1px solid rgba(200,169,110,.15);padding:28px;}}
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
  <p style="margin-top:48px;color:#666;font-size:.9rem">Referencia · Estudio de Cocinas · {fecha}</p>
</section>

<section>
  <div class="line"></div>
  <h2>Su nueva cocina</h2>
  <p>{descripcion}</p>
  {f'<p><strong class="accent">Medidas:</strong> {medidas_str}</p>'}
  {f'<p><strong class="accent">Notas:</strong> {notas}</p>' if notas else ''}
  <div class="grid2" style="margin-top:40px">
    <div class="card"><h3>Distribución</h3><p>Optimizada para el flujo de trabajo en cocina con isla central y módulos en L</p></div>
    <div class="card"><h3>Materiales</h3><p>Primera calidad con garantía de 10 años en todos los elementos fabricados</p></div>
    <div class="card"><h3>Electrodomésticos</h3><p>Alta gama totalmente integrados, selección personalizada según uso y presupuesto</p></div>
    <div class="card"><h3>Iluminación</h3><p>3 niveles: funcional bajo muebles, ambiental y decorativa sobre isla</p></div>
  </div>
</section>

<section>
  <div class="line"></div>
  <h2>Materiales y acabados</h2>
  <p>Cada superficie ha sido seleccionada por su resistencia, facilidad de mantenimiento y valor estético a largo plazo.</p>
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
  <p class="brand">Estudio de Cocinas</p>
  <p>info@estudiococinas.es &nbsp;·&nbsp; +34 900 000 000</p>
  <p style="margin-top:24px;font-size:.75rem;color:#333">Visita de medición gratuita · Propuesta en 48h · Garantía 2 años instalación</p>
</footer>

</body>
</html>"""

    return {"presentacionHtml": html, "cliente": cliente, "fecha": fecha}
