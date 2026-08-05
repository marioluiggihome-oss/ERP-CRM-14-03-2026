# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
CRM models - Contacts, Opportunities, Activities, Calendar Events
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class ContactModel(BaseModel):
    """CRM Contact model"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"contact-{uuid.uuid4().hex[:8]}")
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    position: str = ""
    address: str = ""
    notes: str = ""
    tags: List[str] = []
    source: str = ""
    status: str = "active"
    segment: str = ""
    prescriptorId: str = ""
    prescriptorName: str = ""
    assignedTo: str = ""
    totalValue: float = 0
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    createdBy: str = ""
    linkedProjectIds: List[str] = []
    convertedToClientId: Optional[str] = None
    businessTypes: List[str] = []
    # Custom pricing values
    customCarcassMaterialId: Optional[str] = None
    customWidthIncrement: Optional[float] = None
    customHeightIncrement: Optional[float] = None
    customDepthIncrement: Optional[float] = None
    customVigaCutIncrement: Optional[float] = None
    customPointValueMontada: Optional[float] = None
    customPointValueDespiece: Optional[float] = None


class ContactCreate(BaseModel):
    """Contact creation model"""
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    position: str = ""
    address: str = ""
    notes: str = ""
    tags: List[str] = []
    source: str = ""
    status: str = "lead"
    segment: str = ""
    prescriptorId: str = ""
    prescriptorName: str = ""
    assignedTo: str = ""


class ContactUpdate(BaseModel):
    """Contact update model"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    status: Optional[str] = None
    segment: Optional[str] = None
    prescriptorId: Optional[str] = None
    prescriptorName: Optional[str] = None
    assignedTo: Optional[str] = None
    totalValue: Optional[float] = None
    linkedProjectIds: Optional[List[str]] = None
    customCarcassMaterialId: Optional[str] = None
    customWidthIncrement: Optional[float] = None
    customHeightIncrement: Optional[float] = None
    customDepthIncrement: Optional[float] = None
    customVigaCutIncrement: Optional[float] = None
    customPointValueMontada: Optional[float] = None
    customPointValueDespiece: Optional[float] = None


class OpportunityModel(BaseModel):
    """CRM Opportunity model"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"opp-{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    contactId: str
    contactName: str = ""
    company: str = ""
    value: float = 0
    probability: int = 20
    stage: str = "lead"
    expectedCloseDate: Optional[str] = None
    notes: str = ""
    tags: List[str] = []
    assignedTo: str = ""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closedAt: Optional[datetime] = None
    createdBy: str = ""
    linkedProjectId: Optional[str] = None
    linkedProjectNumber: Optional[str] = None
    businessType: str = "cocina"
    moduleType: str = ""


class OpportunityCreate(BaseModel):
    """Opportunity creation model"""
    title: str
    description: str = ""
    contactId: str
    contactName: str = ""
    company: str = ""
    value: float = 0
    probability: int = 20
    stage: str = "lead"
    expectedCloseDate: Optional[str] = None
    notes: str = ""
    tags: List[str] = []
    assignedTo: str = ""
    linkedProjectId: Optional[str] = None
    linkedProjectNumber: Optional[str] = None
    businessType: str = "cocina"
    moduleType: str = ""


class OpportunityUpdate(BaseModel):
    """Opportunity update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    company: Optional[str] = None
    value: Optional[float] = None
    probability: Optional[int] = None
    stage: Optional[str] = None
    expectedCloseDate: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assignedTo: Optional[str] = None
    linkedProjectId: Optional[str] = None
    linkedProjectNumber: Optional[str] = None


class CalendarEventModel(BaseModel):
    """CRM Calendar Event model"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    eventType: str = "cita"
    startDate: str
    endDate: str
    allDay: bool = False
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    assignedTo: str
    assignedToName: str = ""
    createdBy: str
    createdByName: str = ""
    completed: bool = False
    completedAt: Optional[str] = None
    reminder: Optional[int] = None
    color: Optional[str] = None
    location: Optional[str] = None
    notes: str = ""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CalendarEventCreate(BaseModel):
    """Calendar event creation model"""
    title: str
    description: str = ""
    eventType: str = "cita"
    startDate: str
    endDate: str
    allDay: bool = False
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    assignedTo: str
    assignedToName: str = ""
    reminder: Optional[int] = None
    color: Optional[str] = None
    location: Optional[str] = None
    notes: str = ""


class CalendarEventUpdate(BaseModel):
    """Calendar event update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    eventType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    allDay: Optional[bool] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    assignedTo: Optional[str] = None
    assignedToName: Optional[str] = None
    completed: Optional[bool] = None
    reminder: Optional[int] = None
    color: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class ActivityModel(BaseModel):
    """CRM Activity model"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}")
    type: str  # call, visit, meeting, video, email, note
    title: str = ""
    subject: str = ""  # Asunto principal
    description: str = ""
    notes: str = ""  # Notas detalladas
    outcome: str = ""  # Resultado/seguimiento
    contactId: Optional[str] = None
    contactName: str = ""
    opportunityId: Optional[str] = None
    opportunityTitle: str = ""
    date: Optional[str] = None  # Fecha de la actividad (YYYY-MM-DD)
    time: Optional[str] = None  # Hora (HH:MM)
    duration: int = 15  # Duración en minutos
    dueDate: Optional[str] = None  # Mantener para retrocompatibilidad
    dueTime: Optional[str] = None
    completed: bool = False
    completedAt: Optional[datetime] = None
    priority: str = "medium"
    assignedTo: str = ""
    userId: str = ""  # Usuario que registró la actividad
    userName: str = ""  # Nombre del usuario
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    createdBy: str = ""


class ActivityCreate(BaseModel):
    """Activity creation model"""
    type: str
    title: str = ""
    subject: str = ""
    description: str = ""
    notes: str = ""
    outcome: str = ""
    contactId: Optional[str] = None
    contactName: str = ""
    opportunityId: Optional[str] = None
    opportunityTitle: str = ""
    date: Optional[str] = None
    time: Optional[str] = None
    duration: int = 15
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    priority: str = "medium"
    assignedTo: str = ""
    userId: str = ""
    userName: str = ""


class ActivityUpdate(BaseModel):
    """Activity update model"""
    type: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[int] = None
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    assignedTo: Optional[str] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
