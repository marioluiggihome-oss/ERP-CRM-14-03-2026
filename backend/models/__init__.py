# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Models package
"""
from .user import UserModelInternal, UserResponse, UserCreate, UserUpdate, user_to_response
from .product import ProductModel, ProductCreate, ZonePoints, MaterialModel, MaterialCreate
from .project import ProjectModel, ProjectCreate, ProjectUpdate, SettingsModel, SettingsUpdate, BudgetItemModel
from .client import ClientModel, ClientCreate, ClientUpdate, CLIENT_SEGMENTS
from .crm import (
    ContactModel, ContactCreate, ContactUpdate,
    OpportunityModel, OpportunityCreate, OpportunityUpdate,
    CalendarEventModel, CalendarEventCreate, CalendarEventUpdate,
    ActivityModel, ActivityCreate, ActivityUpdate
)
