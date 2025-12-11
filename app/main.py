# app/main.py
import logging

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, models
from app.db import engine, Base
from app.deps import get_db
from typing import List

app = FastAPI(title="Leads router")
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@app.on_event("startup")
async def on_startup():
    log.info("Starting up")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/operators/", response_model=schemas.OperatorOut)
async def create_operator(op_in: schemas.OperatorCreate, db: AsyncSession = Depends(get_db)):
    op = await crud.create_operator(db, op_in)
    return op

@app.get("/operators/", response_model=List[schemas.OperatorOut])
async def list_operators(db: AsyncSession = Depends(get_db)):
    ops = await crud.list_operators(db)
    return ops

@app.patch("/operators/{operator_id}", response_model=schemas.OperatorOut)
async def update_operator(operator_id: int, op_upd: schemas.OperatorUpdate, db: AsyncSession = Depends(get_db)):
    op = await crud.get_operator(db, operator_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    op = await crud.update_operator(db, op, op_upd.dict())
    return op

@app.post("/sources/", response_model=schemas.SourceOut)
async def create_source(src_in: schemas.SourceCreate, weights: List[schemas.OperatorWeight] = None, db: AsyncSession = Depends(get_db)):
    src = await crud.create_source(db, src_in, weights)
    # shape operator_weights for response
    out = schemas.SourceOut.from_orm(src)
    out.operator_weights = [schemas.OperatorWeight(operator_id=l.operator_id, weight=l.weight) for l in src.operator_links]
    return out

@app.put("/sources/{source_id}/weights", response_model=schemas.SourceOut)
async def set_weights(source_id: int, weights: List[schemas.OperatorWeight], db: AsyncSession = Depends(get_db)):
    src = await crud.set_source_weights(db, source_id, weights)
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    out = schemas.SourceOut.from_orm(src)
    out.operator_weights = [schemas.OperatorWeight(operator_id=l.operator_id, weight=l.weight) for l in src.operator_links]
    return out

@app.post("/contacts/", response_model=schemas.ContactOut)
async def register_contact(contact_in: schemas.ContactCreate, db: AsyncSession = Depends(get_db)):
    try:
        contact, operator = await crud.create_contact(db, contact_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return contact

@app.get("/leads/")
async def get_leads(db: AsyncSession = Depends(get_db)):
    leads = await crud.list_leads_with_contacts(db)
    # simple serialization
    return [
        {
            "id": l.id,
            "external_id": l.external_id,
            "phone": l.phone,
            "email": l.email,
            "contacts": [{"id": c.id, "source_id": c.source_id, "operator_id": c.operator_id, "status": c.status, "created_at": c.created_at} for c in l.contacts]
        }
        for l in leads
    ]

@app.get("/stats/distribution")
async def distribution(db: AsyncSession = Depends(get_db)):
    rows = await crud.distribution_by_operator(db)
    return [{"operator_id": r[0], "operator_name": r[1], "count": int(r[2] or 0)} for r in rows]


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)