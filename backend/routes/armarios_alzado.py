# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
armarios_alzado.py — ALZADO VECTORIAL ACOTADO DE ARMARIO / VESTIDOR.

El único motor de alzado del ERP vivía en `estudio_cocinas.py` y sólo servía
para cocina. En un proyecto de armario, «Alzado + planta + medidas» se saltaba
el dibujo vectorial y devolvía una lámina de IA sin una sola cota. Esto lo
arregla.

QUIÉN PONE LOS NÚMEROS
----------------------
Los pone `services/armario_geometry.py`, que es cálculo puro y está probado.
Aquí sólo se dibuja. Un modelo de IMAGEN nunca escribe cotas (regla de oro de
CLAUDE.md): las inventa, y en un plano acotado eso es madera cortada mal.

LO QUE NO SE DIBUJA
-------------------
Lo que no se sabe. Sin ancho, alto, fondo o módulos sale un 422 diciendo qué
falta, no un armario "por defecto". Y si un módulo no cabe, ese módulo sale
marcado y los demás se dibujan: un plano parcial con el fallo señalado sirve
más que un error en blanco.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from services import armario_geometry as geo

logger = logging.getLogger(__name__)

try:
    from services.jwt_service import require_auth
    _DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover - entorno sin auth (pruebas)
    _DEPS = []

router = APIRouter(tags=["armarios"], dependencies=_DEPS)


class AlzadoArmarioRequest(BaseModel):
    config: Dict[str, Any] = Field(..., description="wardrobeConfig: width/height/depth/modules/numDoors (mm)")
    moduleConfigs: Optional[List[Dict[str, Any]]] = Field(default=None)
    nombre_cliente: Optional[str] = ""
    referencia: Optional[str] = ""
    con_cotas: bool = True
    monocromo: bool = True


@router.post("/armarios/alzado")
async def generar_alzado_armario(payload: AlzadoArmarioRequest):
    """Alzado del frente + alzado interior + planta, acotados y vectoriales."""
    import io
    import base64
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig = None
    try:
        # LÍNEA RECTA, SIEMPRE. Un alzado de armario es un plano de taller:
        # con él se corta. El trazo temblado lo afea y encima hace dudar de si
        # esa balda está donde parece. El lápiz se queda para el boceto en
        # perspectiva, que es un dibujo para enseñar.
        #
        # Se pone a None de ENTRADA y no solo en el `finally`: `path.sketch` es
        # global del proceso, y una petición anterior que lo dejara puesto haría
        # salir este temblado sin que nadie lo pidiera y sin dar ningún error.
        matplotlib.rcParams["path.sketch"] = None

        g = geo.montar(payload.config, payload.moduleConfigs)
        if not g.get("ok"):
            # 422 con instrucciones, no "error de validación". El que lo lee
            # tiene que saber qué tocar.
            raise HTTPException(status_code=422, detail=g.get("motivo")
                                or "No hay medidas suficientes para acotar el alzado.")

        if payload.monocromo:
            C_LINE = "#000000"; C_COTA = "#000000"; C_BG = "#FFFFFF"
            C_GRID = "#D9D9D9"; C_INT = "#000000"; C_HERRAJE = "#000000"
            C_AVISO = "#000000"
        else:
            C_LINE = "#2C2C2C"; C_COTA = "#B03A2E"; C_BG = "#FFFFFF"
            C_GRID = "#E6E2DA"; C_INT = "#8A6D3B"; C_HERRAJE = "#3F3F3F"
            C_AVISO = "#B03A2E"

        ancho, alto, fondo = g["ancho"], g["alto"], g["fondo"]
        P = geo.GRUESO_PANEL

        fig, axes = plt.subplots(1, 3, figsize=(19, 7.4),
                                 gridspec_kw={"width_ratios": [1.0, 1.0, 0.42]})
        fig.patch.set_facecolor(C_BG)
        ax_frente, ax_int, ax_planta = axes

        def wire(ax, x, y, w, h, lw=1.4, dash=False, color=None):
            ax.add_patch(patches.Rectangle(
                (x, y), w, h, fill=False, edgecolor=color or C_LINE, linewidth=lw,
                linestyle="--" if dash else "-", zorder=3))

        def cota_h(ax, x0, x1, y, txt):
            if not payload.con_cotas:
                return
            ax.annotate("", xy=(x0, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="<->", color=C_COTA, lw=0.9))
            ax.text((x0 + x1) / 2, y + alto * 0.012, txt, ha="center", va="bottom",
                    fontsize=7.5, color=C_COTA)

        def cota_v(ax, x, y0, y1, txt):
            if not payload.con_cotas:
                return
            ax.annotate("", xy=(x, y0), xytext=(x, y1),
                        arrowprops=dict(arrowstyle="<->", color=C_COTA, lw=0.9))
            ax.text(x - ancho * 0.012, (y0 + y1) / 2, txt, ha="right", va="center",
                    fontsize=7.5, color=C_COTA, rotation=90)

        def marco(ax, titulo):
            ax.set_facecolor(C_BG)
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_title(titulo, fontsize=10, fontweight="bold", color=C_LINE, pad=12)

        # ── 1. ALZADO DEL FRENTE (puertas cerradas) ─────────────────────────
        marco(ax_frente, "ALZADO FRENTE")
        ax_frente.set_xlim(-ancho * 0.16, ancho * 1.10)
        ax_frente.set_ylim(-alto * 0.16, alto * 1.10)
        wire(ax_frente, 0, 0, ancho, alto, lw=2.2)

        for p in g["puertas"]:
            wire(ax_frente, p["x"], 0, p["ancho"], alto, lw=1.0)
            # Tirador: herraje visible, por dentro del canto de la puerta.
            hx = p["x"] + p["ancho"] * 0.88
            ax_frente.plot([hx, hx], [alto * 0.42, alto * 0.55],
                           color=C_HERRAJE, lw=2.6, zorder=6, solid_capstyle="round")
            if p["ancho"] >= ancho * 0.12:
                cota_h(ax_frente, p["x"], p["x"] + p["ancho"], -alto * 0.055,
                       f"{int(round(p['ancho']))}")

        cota_h(ax_frente, 0, ancho, -alto * 0.125, f"ANCHO TOTAL  {int(round(ancho))} mm")
        cota_v(ax_frente, -ancho * 0.055, 0, alto, f"ALTO  {int(round(alto))} mm")
        ax_frente.text(ancho / 2, alto * 1.045,
                       f"{len(g['puertas'])} puerta(s)", ha="center", va="bottom",
                       fontsize=8, color=C_LINE)

        # ── 2. ALZADO INTERIOR (puertas abiertas) ───────────────────────────
        marco(ax_int, "ALZADO INTERIOR (puertas abiertas)")
        ax_int.set_xlim(-ancho * 0.16, ancho * 1.10)
        ax_int.set_ylim(-alto * 0.16, alto * 1.10)
        wire(ax_int, 0, 0, ancho, alto, lw=2.2)
        # Tapas y laterales: el interior arranca DENTRO de ellos, no en el 0.
        for gy in (P, alto - P):
            ax_int.plot([0, ancho], [gy, gy], color=C_GRID, lw=0.8, zorder=1)

        for col in g["modulos"]:
            x0 = col["x"]
            # Divisor entre módulos (no hay divisor antes del primero).
            if col["indice"] > 0:
                ax_int.add_patch(patches.Rectangle(
                    (x0 - P / 2, P), P, alto - 2 * P, facecolor=C_GRID,
                    edgecolor=C_LINE, linewidth=0.8, zorder=2))

            hueco_x0 = x0 + (P / 2 if col["indice"] > 0 else P)
            hueco_w = col["hueco"]

            if col["error"]:
                # El módulo que no cabe NO se dibuja a medias: se marca. Un
                # interior apretado en pantalla es lo que llega al taller sin
                # que nadie sepa que estaba mal.
                ax_int.add_patch(patches.Rectangle(
                    (hueco_x0, P), hueco_w, alto - 2 * P, facecolor="#F2F2F2",
                    edgecolor=C_AVISO, linewidth=1.2, hatch="//", zorder=2))
                # Con fondo opaco: sobre el rayado el aviso no se leía, y un
                # aviso que no se lee es un módulo que baja al taller igual.
                ax_int.text(hueco_x0 + hueco_w / 2, alto / 2,
                            f"MÓDULO {col['indice'] + 1}\nNO CABE\n(ver aviso al pie)",
                            ha="center", va="center", fontsize=7.5,
                            fontweight="bold", color=C_AVISO, zorder=7,
                            bbox=dict(facecolor=C_BG, edgecolor=C_AVISO,
                                      linewidth=0.8, boxstyle="round,pad=0.5"))
            else:
                for el in col["elementos"]:
                    t = el["tipo"]
                    y = P + el["y"]
                    if t == "barra":
                        ax_int.plot([hueco_x0 + hueco_w * 0.06, hueco_x0 + hueco_w * 0.94],
                                    [y, y], color=C_HERRAJE, lw=3.0, zorder=5,
                                    solid_capstyle="round")
                        ax_int.text(hueco_x0 + hueco_w / 2, y + alto * 0.008, "barra",
                                    ha="center", va="bottom", fontsize=5.8, color=C_HERRAJE)
                    elif t == "balda":
                        ax_int.add_patch(patches.Rectangle(
                            (hueco_x0, y), hueco_w, el["alto"], facecolor=C_GRID,
                            edgecolor=C_LINE, linewidth=0.8, zorder=4))
                    else:
                        # Cajón, maletero, zapatero, pantalonero: volumen con frente.
                        wire(ax_int, hueco_x0, y, hueco_w, el["alto"], lw=0.9, color=C_INT)
                        # El rótulo va en el tercio bajo y el tirador en el
                        # alto: centrados los dos, el tirador tachaba el texto y
                        # "Cajón 2" se leía como si estuviera anulado.
                        alto_txt = (y + el["alto"] * 0.30 if t == "cajon"
                                    else y + el["alto"] / 2)
                        if el["alto"] >= alto * 0.045 and hueco_w >= ancho * 0.09:
                            ax_int.text(hueco_x0 + hueco_w / 2, alto_txt,
                                        el["etiqueta"], ha="center", va="center",
                                        fontsize=5.8, color=C_INT)
                        if t == "cajon":
                            cx = hueco_x0 + hueco_w / 2
                            ax_int.plot([cx - hueco_w * 0.16, cx + hueco_w * 0.16],
                                        [y + el["alto"] * 0.72] * 2, color=C_HERRAJE,
                                        lw=2.0, zorder=6, solid_capstyle="round")

            cota_h(ax_int, hueco_x0, hueco_x0 + hueco_w, -alto * 0.055,
                   f"{int(round(hueco_w))}")
            ax_int.text(hueco_x0 + hueco_w / 2, alto * 1.02, f"M{col['indice'] + 1}",
                        ha="center", va="bottom", fontsize=8, fontweight="bold",
                        color=C_LINE)

        cota_h(ax_int, 0, ancho, -alto * 0.125,
               f"{len(g['modulos'])} módulo(s) · paso {int(round(g['modulos'][0]['paso']))} mm")
        cota_v(ax_int, -ancho * 0.055, P, alto - P,
               f"INTERIOR  {int(round(g['altoInterior']))} mm")

        # ── 3. PLANTA ───────────────────────────────────────────────────────
        marco(ax_planta, "PLANTA")
        ax_planta.set_xlim(-ancho * 0.16, ancho * 1.10)
        ax_planta.set_ylim(-fondo * 1.30, fondo * 2.10)
        wire(ax_planta, 0, 0, ancho, fondo, lw=2.2)
        for col in g["modulos"]:
            if col["indice"] > 0:
                ax_planta.add_patch(patches.Rectangle(
                    (col["x"] - P / 2, 0), P, fondo, facecolor=C_GRID,
                    edgecolor=C_LINE, linewidth=0.8, zorder=2))
        # Trasera, con su grosor propio (8 mm, no 18).
        ax_planta.add_patch(patches.Rectangle(
            (0, fondo - geo.GRUESO_TRASERA), ancho, geo.GRUESO_TRASERA,
            facecolor=C_GRID, edgecolor=C_LINE, linewidth=0.8, zorder=2))
        cota_h(ax_planta, 0, ancho, -fondo * 0.42, f"{int(round(ancho))} mm")
        cota_v(ax_planta, -ancho * 0.045, 0, fondo, f"FONDO {int(round(fondo))}")

        # ── Pie: piezas de corte y avisos ───────────────────────────────────
        pz = g["piezas"]
        def _mm(t):
            return " × ".join(str(int(round(v))) for v in t)
        pie = (f"PIEZAS (mm)   lateral {_mm(pz['lateral'])} ×2   ·   tapa {_mm(pz['tapa'])} ×2   ·   "
               f"trasera {_mm(pz['trasera'])}   ·   divisor {_mm(pz['divisor'])} ×{pz['divisores_uds']}   ·   "
               f"balda {_mm(pz['balda'])}   ·   cajón {_mm(pz['cajon'])}")
        fig.text(0.5, 0.055, pie, ha="center", va="bottom", fontsize=7.2, color=C_LINE)

        cab = " · ".join(x for x in [(payload.nombre_cliente or "").strip(),
                                     (payload.referencia or "").strip()] if x)
        if cab:
            # A la izquierda, como el cajetín de un plano: centrada se montaba
            # encima del título «ALZADO INTERIOR», que va justo en el medio.
            fig.text(0.012, 0.985, cab, ha="left", va="top", fontsize=9,
                     fontweight="bold", color=C_LINE)

        # Los problemas y las medidas derivadas van IMPRESAS EN EL PLANO, no
        # sólo en la respuesta: el plano se imprime y se baja al taller, y allí
        # nadie ve el JSON.
        notas = ([f"⚠ Módulo {p['modulo']}: {p['motivo']}" for p in g["problemas"]]
                 + [f"· {a}" for a in g["avisos"]]
                 + [f"· {d}" for d in g["derivados"]])
        if notas:
            fig.text(0.5, 0.012, "\n".join(notas[:4]), ha="center", va="bottom",
                     fontsize=6.6, color=C_AVISO, linespacing=1.5)

        buf = io.BytesIO()
        plt.tight_layout(pad=1.2, rect=(0, 0.08, 1, 0.96))
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=C_BG)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")

        return {
            "success": True,
            "alzadoBase64": f"data:image/png;base64,{b64}",
            "modulos": len(g["modulos"]),
            "puertas": len(g["puertas"]),
            "piezas": {k: (list(v) if isinstance(v, tuple) else v) for k, v in pz.items()},
            # Se devuelven aparte para que la pantalla pueda enseñarlos como
            # aviso. NO se registran en un log y se sigue: eso es justo lo que
            # hace que el fallo reaparezca disfrazado mucho más lejos.
            "problemas": g["problemas"],
            "avisos": g["avisos"],
            "derivados": g["derivados"],
        }

    except HTTPException:
        # Un 422 con instrucciones no puede acabar convertido en un 500
        # genérico: HTTPException hereda de Exception y el `except` de abajo se
        # lo tragaría, dejando al usuario leyendo "no se pudo generar".
        raise
    except Exception as e:
        logger.error("alzado de armario: %s", e, exc_info=True)
        raise HTTPException(status_code=500,
                            detail=f"No se pudo generar el alzado del armario: {e}")
    finally:
        matplotlib.rcParams["path.sketch"] = None
        if fig is not None:
            plt.close(fig)
