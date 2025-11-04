# app/models/medication.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MedicationBase(BaseModel):
    name: str
    dosage: str
    frequency: int  # in hours
    start_date: datetime
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    notes: Optional[str] = None
    preferred_time: str  # Format: "HH:MM" (e.g. "08:00" or "19:30")

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    notes: Optional[str] = None
    last_taken: Optional[datetime] = None

class MedicationResponse(MedicationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_taken: Optional[datetime] = None
    next_dose: Optional[datetime] = None
    preferred_time: Optional[str]
