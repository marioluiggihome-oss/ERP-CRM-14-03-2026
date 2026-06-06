"""
Rentabilidad por proyecto (cocina): cruza VENTAS (presupuestos/proyectos) con
COSTES (facturas/gastos de proveedor) para obtener la cuenta de resultados por
cocina: Venta - Coste = Margen (EUR y %).

Modelo de datos:
- Ventas: se leen de la coleccion `projects` (presupuestos), campo totalPvp y
  budgetNumber/clientCode/customerName.
- Costes: coleccion nueva `project_costs`, un documento por gasto:
    { id, projectRef, proveedor, concepto, categoria, importe, fecha,
      createdAt, source }  (source: 'manual' | 'ia' | 'factura')
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rentabilidad"])

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ----------------------------- COSTES POR PROYECTO -----------------------------

@router.post("/project-costs")
async def add_project_cost(cost: dict):
    """Registrar un coste/gasto asociado a un proyecto (por su referencia)."""
    try:
        ref = (cost.get("projectRef") or "").strip()
        if not ref:
            raise HTTPException(status_code=400, detail="Falta projectRef")
        doc = {
            "id": f"cost-{uuid.uuid4().hex[:8]}",
            "projectRef": ref,
            "proveedor": cost.get("proveedor", ""),
            "concepto": cost.get("concepto", ""),
            "categoria": cost.get("categoria", "OTROS"),
            "importe": float(cost.get("importe", 0) or 0),
            "fecha": cost.get("fecha", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "source": cost.get("source", "manual"),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        await db.project_costs.insert_one(doc)
        doc.pop("_id", None)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add project cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-costs")
async def list_project_costs(projectRef: Optional[str] = None):
    """Listar costes; si se pasa projectRef, solo los de ese proyecto."""
    try:
        query = {"projectRef": projectRef} if projectRef else {}
        costs = await db.project_costs.find(query, {"_id": 0}).sort("fecha", -1).to_list(2000)
        return costs
    except Exception as e:
        logger.error(f"List project costs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/project-costs/{cost_id}")
async def delete_project_cost(cost_id: str):
    try:
        res = await db.project_costs.delete_one({"id": cost_id})
        return {"success": True, "deleted": res.deleted_count}
    except Exception as e:
        logger.error(f"Delete project cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- RENTABILIDAD -----------------------------

@router.get("/rentabilidad")
async def get_rentabilidad(userId: Optional[str] = None):
    """Cuenta de resultados por proyecto: Venta (presupuesto) - Coste = Margen.

    Une cada proyecto con sus costes (por budgetNumber == projectRef).
    """
    try:
        query = {}
        if userId:
            query["userId"] = userId
        projects = await db.projects.find(
            query,
            {"_id": 0, "id": 1, "budgetNumber": 1, "customerName": 1, "clientCode": 1,
             "totalPvp": 1, "totalConIVA": 1, "createdAt": 1, "userId": 1, "status": 1}
        ).sort("createdAt", -1).to_list(3000)

        # Agregar costes por projectRef (== budgetNumber)
        costs_agg = {}
        async for c in db.project_costs.find({}, {"_id": 0, "projectRef": 1, "importe": 1}):
            ref = c.get("projectRef")
            costs_agg[ref] = costs_agg.get(ref, 0) + float(c.get("importe", 0) or 0)

        rows = []
        tot_venta = tot_coste = 0.0
        for p in projects:
            ref = p.get("budgetNumber") or ""
            venta = float(p.get("totalPvp", 0) or 0)
            coste = float(costs_agg.get(ref, 0))
            margen = venta - coste
            margen_pct = (margen / venta * 100) if venta > 0 else 0
            tot_venta += venta
            tot_coste += coste
            rows.append({
                "projectId": p.get("id"),
                "ref": ref,
                "cliente": p.get("customerName", ""),
                "clientCode": p.get("clientCode", ""),
                "fecha": p.get("createdAt", ""),
                "status": p.get("status", ""),
                "venta": round(venta, 2),
                "coste": round(coste, 2),
                "margen": round(margen, 2),
                "margenPct": round(margen_pct, 1),
            })

        tot_margen = tot_venta - tot_coste
        return {
            "rows": rows,
            "totales": {
                "venta": round(tot_venta, 2),
                "coste": round(tot_coste, 2),
                "margen": round(tot_margen, 2),
                "margenPct": round((tot_margen / tot_venta * 100) if tot_venta > 0 else 0, 1),
                "proyectos": len(rows),
            },
        }
    except Exception as e:
        logger.error(f"Get rentabilidad error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
