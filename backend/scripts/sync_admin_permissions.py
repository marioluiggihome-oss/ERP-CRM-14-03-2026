# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Sincroniza el usuario admin principal con TODOS los permisos posibles.
El usuario admin es el que se loguea con mario@luiggihome.es / Mario2025*
"""
import asyncio
from pymongo import MongoClient
from datetime import datetime, timezone


MONGO_URL = "mongodb+srv://marioluiggihome_db_user:Mario2025Mario2025@luiggi-cluster.frtehmc.mongodb.net/luiggi_home?retryWrites=true&w=majority"
DB_NAME = "luiggi_home"


# Conjunto completo de permisos para super-admin
SUPER_ADMIN_PERMS = {
    # Roles
    "isAdmin": True,
    "isPrimaryAdmin": True,
    "isGerente": True,
    "isDirectorComercial": True,
    "isResponsableDelegacion": True,
    "isDirectorFabrica": True,
    "isRepresentative": False,
    "isComercial": False,
    "isPrescriptor": False,
    "isTienda": False,
    "isFabrica": False,
    "isMontador": False,
    # Permisos generales
    "canAccessCRM": True,
    "canAccessFabrica": True,
    "canAccessArmarios": True,
    "canAccessMontajes": True,
    "canAccessBackups": True,
    "canAccessDashboard": True,
    "canAccessMaintenance": True,
    "canAccessReports": True,
    "canAccessTelemetry": True,
    "canAccessMV": True,
    "canAccessZC": True,
    # Permisos de gestión
    "canManageUsers": True,
    "canManageSettings": True,
    "canManageArticles": True,
    "canManageClients": True,
    "canManageProducts": True,
    "canManageOrders": True,
    "canDeleteOrders": True,
    "canEditAllOrders": True,
    "canViewAllOrders": True,
    "canSetDeliveryDates": True,
    "canViewTechnicalDespiece": True,
    "canSeeCost": True,
    "canSeeRetail": True,
    "canViewMetrics": True,
    "canExportData": True,
    "canAuthorizePermissions": True,
    "canChangeLogo": True,
    "useCustomBranding": True,
    # IA / Digitalizador
    "canUseAIAnalysis": True,
    "canUseDigitalizador": True,
    # Bibliotecas y módulos
    "allowedLibraries": ["ZC", "MV"],
    "allowedModules": ["montada", "despiece", "armarios"],
    "allowedCatalogIds": ["cat-m-base", "cat-d-base"],
    "defaultLibrary": "ZC",
    # Activo
    "isActive": True,
    # Metadata
    "updatedAt": datetime.now(timezone.utc).isoformat(),
}


def main():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=8000)
    db = client[DB_NAME]

    # 1) Actualizar usuario admin principal (mario@luiggihome.es / id=admin)
    result = db.users.update_one(
        {"id": "admin"},
        {"$set": SUPER_ADMIN_PERMS}
    )
    print(f"Actualizado mario@luiggihome.es (id=admin): modified={result.modified_count}")

    # 2) Verificar que MARIO (user-master-mario) tambien tenga todo
    result2 = db.users.update_one(
        {"id": "user-master-mario"},
        {"$set": SUPER_ADMIN_PERMS}
    )
    print(f"Actualizado MARIO (id=user-master-mario): modified={result2.modified_count}")

    # 3) Listar usuarios duplicados de MARIO (para revisarlos)
    print("\n=== Usuarios con 'mario' en username ===")
    for u in db.users.find({"username": {"$regex": "mario", "$options": "i"}}, {"_id": 0, "password": 0, "logo": 0}):
        print(f"  id={u.get('id'):25s} username={u.get('username')}")

    # 4) Eliminar los duplicados sospechosos (mantener solo admin + MARIO)
    duplicates = ["user-efdd19b6", "user-a2716ce2"]
    for dup_id in duplicates:
        result_del = db.users.delete_one({"id": dup_id})
        print(f"Eliminado duplicado {dup_id}: deleted={result_del.deleted_count}")

    # 5) Verificación final - mario@luiggihome.es
    user = db.users.find_one({"id": "admin"}, {"_id": 0, "password": 0, "logo": 0})
    print("\n=== Estado final mario@luiggihome.es ===")
    perm_keys = sorted(k for k in user.keys() if k.startswith(("is", "can", "allowed", "default")))
    for k in perm_keys:
        v = user.get(k)
        emoji = "✅" if v in (True, ["ZC", "MV"], ["montada", "despiece", "armarios"], "ZC") or (isinstance(v, list) and len(v) > 0) else ("❌" if v is False else "  ")
        print(f"  {emoji} {k}: {v}")

    print(f"\nTotal usuarios en DB: {db.users.count_documents({})}")
    print(f"Comerciales (isRepresentative=True): {db.users.count_documents({'isRepresentative': True})}")


if __name__ == "__main__":
    main()
