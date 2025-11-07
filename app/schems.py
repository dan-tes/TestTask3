from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional


class IncidentStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IncidentSource(str, Enum):
    operator = "operator"
    monitoring = "monitoring"
    partner = "partner"


class IncidentBase(BaseModel):
    description: str
    source: IncidentSource


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdateStatus(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    id: int
    description: str
    status: IncidentStatus
    source: IncidentSource
    created_at: datetime

    class Config:
        orm_mode = True
