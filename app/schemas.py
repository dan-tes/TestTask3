from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class OperatorBase(BaseModel):
    name: str
    active: Optional[bool] = True
    capacity: Optional[int] = 10

class OperatorCreate(OperatorBase):
    pass

class OperatorUpdate(BaseModel):
    active: Optional[bool]
    capacity: Optional[int]

class OperatorOut(OperatorBase):
    id: int
    class Config:
        orm_mode = True

class SourceBase(BaseModel):
    code: str
    title: Optional[str] = None

class SourceCreate(SourceBase):
    pass

class OperatorWeight(BaseModel):
    operator_id: int
    weight: int = Field(..., ge=0)

class SourceOut(SourceBase):
    id: int
    operator_weights: List[OperatorWeight] = []
    class Config:
        orm_mode = True

class LeadIn(BaseModel):
    external_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ContactCreate(BaseModel):
    lead: LeadIn
    source_code: str
    message: Optional[str] = None

class ContactOut(BaseModel):
    id: int
    lead_id: int
    source_id: Optional[int]
    operator_id: Optional[int]
    status: str
    created_at: datetime
    message: Optional[str]
    class Config:
        orm_mode = True
