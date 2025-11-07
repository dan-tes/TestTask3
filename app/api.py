from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud
import app.schems as schemas

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/", response_model=schemas.IncidentResponse)
async def create_incident(incident: schemas.IncidentCreate, db: AsyncSession = Depends(get_db)):
    new_incident = await crud.create_incident(db, incident.description, incident.source)
    return new_incident


@router.get("/", response_model=list[schemas.IncidentResponse])
async def get_incidents(status: str | None = None, db: AsyncSession = Depends(get_db)):
    return await crud.get_incidents(db, status)


@router.put("/{incident_id}", response_model=schemas.IncidentResponse)
async def update_incident_status(incident_id: int, update: schemas.IncidentUpdateStatus, db: AsyncSession = Depends(get_db)):
    updated = await crud.update_incident_status(db, incident_id, update.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    return updated
