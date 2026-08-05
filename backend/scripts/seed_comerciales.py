# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Script para recrear los 9 comerciales en la BD Atlas si no existen.
Idempotente: si el usuario ya existe (por username), se actualizan sus permisos.
"""
import asyncio
import os
import sys
import uuid
import bcrypt
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']


# Lista de los 9 comerciales originales con sus credenciales y permisos
COMERCIALES = [
    {"username": "MIGUEL", "password": "Miguel2026*", "clientName": "MIGUEL"},
    {"username": "JOSEMANUEL", "password": "Josemanuel2026*", "clientName": "JOSE MANUEL"},
    {"username": "JENARO", "password": "Jenaro2026*", "clientName": "JENARO"},
    {"username": "BENITO", "password": "Benito2026*", "clientName": "BENITO"},
    {"username": "CARLOSBEJAR", "password": "Carlosbejar2026*", "clientName": "CARLOS BEJAR"},
    {"username": "CARLOSRODRIGUEZ", "password": "Carlosrodriguez2026*", "clientName": "CARLOS RODRIGUEZ"},
    {"username": "JOSEANTONIO", "password": "Joseantonio2026*", "clientName": "JOSE ANTONIO"},
    {"username": "NAVA", "password": "Nava2026*", "clientName": "NAVA"},
    {"username": "ROBERTO", "password": "Roberto2026*", "clientName": "ROBERTO"},
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def build_user_doc(c):
    """Construye el documento del usuario con permisos de Comercial standard."""
    return {
        "id": f"user-{uuid.uuid4().hex[:8]}",
        "username": c["username"],
        "clientName": c["clientName"],
        "password": hash_password(c["password"]),
        "isActive": True,
        # Roles
        "isAdmin": False,
        "isGerente": False,
        "isDirectorComercial": False,
        "isResponsableDelegacion": False,
        "isRepresentative": True,   # <-- Es comercial
        "isComercial": True,        # alias compatible
        "isPrescriptor": False,
        "isTienda": False,
        "isFabrica": False,
        "isMontador": False,
        "isDirectorFabrica": False,
        "isPrimaryAdmin": False,
        "linkedRepresentativeId": "",
        "linkedClientId": "",
        # Permisos
        "canAccessCRM": True,
        "canUseAIAnalysis": False,
        "canUseDigitalizador": False,
        "canAccessArmarios": False,
        "canAccessFabrica": False,
        "canAccessMontajes": False,
        "canManageArticles": False,
        "canManageOrders": False,
        "canSetDeliveryDates": False,
        "canViewTechnicalDespiece": False,
        "canSeeCost": False,
        "canSeeRetail": True,
        "canAuthorizePermissions": False,
        "canChangeLogo": False,
        "useCustomBranding": False,
        # Comercial / Módulos
        "allowedModules": ["montada", "despiece"],
        "allowedLibraries": ["ZC", "MV"],
        "allowedCatalogIds": ["cat-m-base", "cat-d-base"],
        "commercialDiscount": 0.0,
        "discountMontada": 0.0,
        "discountDespiece": 0.0,
        "provinciaCode": "",
        "factoryId": "",
        "accessExpirationDate": "",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


async def main():
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000, maxPoolSize=5)
    db = client[DB_NAME]

    print(f"Conectado a DB: {DB_NAME}")
    print(f"Comerciales a procesar: {len(COMERCIALES)}")
    print("-" * 50)

    created = 0
    updated = 0
    for c in COMERCIALES:
        existing = await db.users.find_one(
            {"username": {"$regex": f"^{c['username']}$", "$options": "i"}}
        )
        if existing:
            # Actualizar permisos sin tocar id ni password (a menos que falte)
            update_doc = {k: v for k, v in build_user_doc(c).items()
                          if k not in ("id", "createdAt", "password")}
            # Solo resetear password si NO había una válida
            if not existing.get("password"):
                update_doc["password"] = hash_password(c["password"])
            await db.users.update_one(
                {"id": existing["id"]},
                {"$set": update_doc}
            )
            updated += 1
            print(f"  ↻ Actualizado: {c['username']}")
        else:
            doc = build_user_doc(c)
            await db.users.insert_one(doc)
            created += 1
            print(f"  ✓ Creado: {c['username']} (pwd: {c['password']})")

    print("-" * 50)
    print(f"Total creados: {created}")
    print(f"Total actualizados: {updated}")

    # Verificación final
    total_comerciales = await db.users.count_documents({
        "isRepresentative": True,
        "isAdmin": {"$ne": True}
    })
    print(f"\nComerciales (isRepresentative=true, no admin) en DB: {total_comerciales}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
