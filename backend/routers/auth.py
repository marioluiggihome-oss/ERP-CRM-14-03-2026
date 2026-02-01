"""
Authentication and Users router
"""
from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from models.user import UserCreate, UserUpdate, UserResponse, user_to_response
from services.database import db
from services.auth_service import hash_password, verify_password

router = APIRouter(prefix="/api", tags=["auth", "users"])


# ============================================
# AUTHENTICATION
# ============================================

@router.post("/auth/login")
async def login(credentials: dict):
    """Login with hashed password verification"""
    username = credentials.get("username", "").upper().strip()
    password = credentials.get("password", "").strip()
    
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not verify_password(password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not user.get("isActive", True):
        raise HTTPException(status_code=401, detail="Cuenta desactivada")
    
    return {"success": True, "user": user_to_response(user)}


# ============================================
# USERS
# ============================================

@router.get("/users", response_model=List[UserResponse])
async def get_users():
    """Get all users (without passwords)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a user by ID (without password)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user with hashed password"""
    existing = await db.users.find_one({"username": user.username.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    user_data = user.model_dump()
    user_data["id"] = f"user-{uuid.uuid4().hex[:8]}"
    user_data["username"] = user_data["username"].upper()
    user_data["password"] = hash_password(user_data["password"])
    
    await db.users.insert_one(user_data)
    return user_to_response(user_data)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate):
    """Update a user"""
    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {k: v for k, v in user.model_dump().items() if v is not None}
    if "username" in update_data:
        update_data["username"] = update_data["username"].upper()
    
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return updated


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user"""
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado"}
