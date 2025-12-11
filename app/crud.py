import random
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from sqlalchemy.orm import selectinload

async def get_or_create_lead(db: AsyncSession, lead_in: schemas.LeadIn) -> models.Lead:
    # try external_id, then phone, then email
    q = select(models.Lead)
    if lead_in.external_id:
        q = q.where(models.Lead.external_id == lead_in.external_id)
        res = await db.execute(q)
        lead = res.scalar_one_or_none()
        if lead:
            return lead
    # phone
    if lead_in.phone:
        res = await db.execute(select(models.Lead).where(models.Lead.phone == lead_in.phone))
        lead = res.scalar_one_or_none()
        if lead:
            return lead
    # email
    if lead_in.email:
        res = await db.execute(select(models.Lead).where(models.Lead.email == lead_in.email))
        lead = res.scalar_one_or_none()
        if lead:
            return lead
    # create new
    new = models.Lead(
        external_id=lead_in.external_id,
        phone=lead_in.phone,
        email=lead_in.email
    )
    db.add(new)
    await db.flush()
    await db.refresh(new)
    await db.commit()
    return new

# Operator CRUD
async def create_operator(db: AsyncSession, op_in: schemas.OperatorCreate) -> models.Operator:
    op = models.Operator(name=op_in.name, active=op_in.active, capacity=op_in.capacity)
    db.add(op)
    await db.flush()
    await db.commit()

    await db.refresh(op)
    return op

async def list_operators(db: AsyncSession) -> List[models.Operator]:
    res = await db.execute(select(models.Operator))
    await db.commit()

    return res.scalars().all()

async def get_operator(db: AsyncSession, operator_id: int) -> Optional[models.Operator]:
    res = await db.execute(select(models.Operator).where(models.Operator.id == operator_id))
    return res.scalar_one_or_none()

async def update_operator(db: AsyncSession, operator: models.Operator, update: dict):
    for k, v in update.items():
        if hasattr(operator, k) and v is not None:
            setattr(operator, k, v)
    db.add(operator)
    await db.flush()
    await db.refresh(operator)
    await db.commit()

    return operator

# Source CRUD and operator weight config
async def create_source(db: AsyncSession, src_in: schemas.SourceCreate, operator_weights: List[schemas.OperatorWeight] = None) -> models.Source:
    src = models.Source(code=src_in.code, title=src_in.title)
    db.add(src)
    await db.flush()
    if operator_weights:
        for ow in operator_weights:
            link = models.OperatorSource(operator_id=ow.operator_id, source_id=src.id, weight=ow.weight)
            db.add(link)
    await db.flush()
    await db.refresh(src)
    await db.commit()
    return src

async def set_source_weights(db: AsyncSession, source_id: int, operator_weights: List[schemas.OperatorWeight]):
    # remove existing links
    await db.execute(models.OperatorSource.__table__.delete().where(models.OperatorSource.source_id == source_id))
    await db.flush()
    for ow in operator_weights:
        db.add(models.OperatorSource(operator_id=ow.operator_id, source_id=source_id, weight=ow.weight))
    await db.flush()
    # return source
    res = await db.execute(select(models.Source).where(models.Source.id == source_id))
    await db.commit()

    return res.scalar_one_or_none()

async def get_source_by_code(db: AsyncSession, code: str) -> Optional[models.Source]:
    res = await db.execute(select(models.Source).where(models.Source.code == code).options(selectinload(models.Source.operator_links)))
    return res.scalar_one_or_none()

# compute current load for operator: count of contacts assigned to operator with status in active_statuses
ACTIVE_STATUSES = ("open", "in_progress")

async def get_operator_current_load(db: AsyncSession, operator_id: int) -> int:
    res = await db.execute(
        select(func.count(models.Contact.id)).where(
            models.Contact.operator_id == operator_id,
            models.Contact.status.in_(ACTIVE_STATUSES)
        )
    )
    await db.commit()

    return res.scalar_one() or 0

async def choose_operator_random_weighted(db: AsyncSession, source: models.Source) -> Optional[models.Operator]:
    # gather operator links with operator objects loaded
    links = await db.execute(
        select(models.OperatorSource).where(models.OperatorSource.source_id == source.id).options(selectinload(models.OperatorSource.operator))
    )
    links = links.scalars().all()
    # filter active and capacity
    candidates = []
    for link in links:
        op = link.operator
        if not op or not op.active:
            continue
        cur_load = await get_operator_current_load(db, op.id)
        if cur_load >= op.capacity:
            continue
        if link.weight <= 0:
            continue
        candidates.append((op, link.weight))
    if not candidates:
        return None
    total = sum(w for _, w in candidates)
    # pick random weighted
    r = random.uniform(0, total)
    upto = 0.0
    for op, w in candidates:
        if upto + w >= r:
            return op
        upto += w
    # fallback
    return candidates[-1][0]

# create contact (register incoming)
async def create_contact(db: AsyncSession, contact_in: schemas.ContactCreate):
    lead = await get_or_create_lead(db, contact_in.lead)
    source = await get_source_by_code(db, contact_in.source_code)
    if not source:
        raise ValueError(f"Unknown source code: {contact_in.source_code}")

    operator = await choose_operator_random_weighted(db, source)
    contact = models.Contact(
        lead_id=lead.id,
        source_id=source.id,
        operator_id=operator.id if operator else None,
        message=contact_in.message,
        status="open"
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    await db.commit()
    return contact, operator

# reporting helpers
async def list_leads_with_contacts(db: AsyncSession):
    res = await db.execute(select(models.Lead).options(selectinload(models.Lead.contacts)))
    await db.commit()
    return res.scalars().all()

async def distribution_by_operator(db: AsyncSession):
    res = await db.execute(
        select(models.Operator.id, models.Operator.name, func.count(models.Contact.id)).join(models.Contact, isouter=True).group_by(models.Operator.id)
    )
    await db.commit()
    return res.all()
