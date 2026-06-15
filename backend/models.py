"""
SQLAlchemy ORM models for Stelos AI.
Tables: logbook_entries, spare_parts, feedback_entries
"""
from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.types import JSON
from database import Base


class LogbookEntry(Base):
    __tablename__ = "logbook_entries"

    id                  = Column(Integer, primary_key=True, index=True)
    timestamp           = Column(String, nullable=False)
    equipment_id        = Column(String, nullable=False, index=True)
    location            = Column(String, default="")
    alert_level         = Column(String, default="NORMAL")
    diagnosis           = Column(Text, default="")
    root_cause          = Column(Text, default="")
    health_score        = Column(Float, default=0.0)
    rul_days            = Column(Float, default=0.0)
    failure_probability = Column(Float, default=0.0)
    maintenance_priority = Column(String, default="P3")
    recommended_actions = Column(JSON, default=list)
    confidence_score    = Column(Float, default=0.0)
    work_order_id       = Column(String, unique=True, index=True)
    approved            = Column(Boolean, default=False)
    approval_engineer   = Column(String, nullable=True)
    approval_timestamp  = Column(String, nullable=True)
    approval_notes      = Column(String, nullable=True)
    engineer_notes      = Column(JSON, default=list)
    business_impact     = Column(JSON, nullable=True)
    session_id          = Column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "timestamp":            self.timestamp,
            "equipment_id":         self.equipment_id,
            "location":             self.location or "",
            "alert_level":          self.alert_level or "NORMAL",
            "diagnosis":            self.diagnosis or "",
            "root_cause":           self.root_cause or "",
            "health_score":         self.health_score,
            "rul_days":             self.rul_days,
            "failure_probability":  self.failure_probability,
            "maintenance_priority": self.maintenance_priority or "P3",
            "recommended_actions":  self.recommended_actions or [],
            "confidence_score":     self.confidence_score,
            "work_order_id":        self.work_order_id,
            "approved":             self.approved,
            "approval_engineer":    self.approval_engineer,
            "approval_timestamp":   self.approval_timestamp,
            "approval_notes":       self.approval_notes,
            "engineer_notes":       self.engineer_notes or [],
            "business_impact":      self.business_impact,
            "session_id":           self.session_id,
        }


class SparePart(Base):
    __tablename__ = "spare_parts"

    id              = Column(Integer, primary_key=True)
    part_id         = Column(String, unique=True, index=True, nullable=False)
    part_name       = Column(String, nullable=False)
    equipment_ids   = Column(JSON, default=list)
    type            = Column(String, default="")
    qty             = Column(Integer, default=0)
    unit            = Column(String, default="pcs")
    status          = Column(String, default="In Stock")
    supplier        = Column(String, default="")
    lead_time_days  = Column(Integer, default=0)
    cost_inr        = Column(Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "part_id":        self.part_id,
            "part_name":      self.part_name,
            "equipment_ids":  self.equipment_ids or [],
            "type":           self.type,
            "qty":            self.qty,
            "unit":           self.unit,
            "status":         self.status,
            "supplier":       self.supplier,
            "lead_time_days": self.lead_time_days,
            "cost_inr":       self.cost_inr,
        }


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id                  = Column(Integer, primary_key=True)
    equipment_id        = Column(String, nullable=False, index=True)
    diagnosis_correct   = Column(Boolean, nullable=False)
    root_cause_correct  = Column(Boolean, nullable=True)
    actions_useful      = Column(Boolean, nullable=True)
    notes               = Column(Text, nullable=True)
    confidence_rating   = Column(Integer, nullable=True)
    timestamp           = Column(String, nullable=False)

    def to_dict(self) -> dict:
        return {
            "equipment_id":       self.equipment_id,
            "diagnosis_correct":  self.diagnosis_correct,
            "root_cause_correct": self.root_cause_correct,
            "actions_useful":     self.actions_useful,
            "notes":              self.notes,
            "confidence_rating":  self.confidence_rating,
            "timestamp":          self.timestamp,
        }
