from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from .db import Base

class Operator(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    capacity = Column(Integer, default=5)
    # отношения
    weights = relationship("SourceOperatorWeight", back_populates="operator")

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True)
    contacts = relationship("Contact", back_populates="lead")

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    weights = relationship("SourceOperatorWeight", back_populates="source")

class SourceOperatorWeight(Base):
    __tablename__ = "source_operator_weights"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    operator_id = Column(Integer, ForeignKey("operators.id"))
    weight = Column(Float, default=1.0)
    source = relationship("Source", back_populates="weights")
    operator = relationship("Operator", back_populates="weights")

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True)
    lead = relationship("Lead", back_populates="contacts")
