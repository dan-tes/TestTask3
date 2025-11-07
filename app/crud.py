from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from app.database import Base
import enum


class IncidentStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSource(str, enum.Enum):
    OPERATOR = "operator"
    MONITORING = "monitoring"
    PARTNER = "partner"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.NEW)
    source = Column(Enum(IncidentSource), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def create_incident(db: AsyncSession, description: str, source: str):
    incident = Incident(description=description, source=source)
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


async def get_incidents(db: AsyncSession, status: str | None = None):
    query = select(Incident)
    if status:
        query = query.where(Incident.status == status)
    result = await db.execute(query)
    return result.scalars().all()


async def update_incident_status(db: AsyncSession, incident_id: int, status: str):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        return None

    incident.status = status
    await db.commit()
    await db.refresh(incident)
    return incident
