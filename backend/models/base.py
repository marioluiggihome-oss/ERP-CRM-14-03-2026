"""
Base models and common configurations
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
