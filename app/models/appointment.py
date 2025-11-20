# app/models/appointment.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AppointmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    doctor_name: Optional[str] = None  # New field added
    appointment_date: datetime
    reminder_time: Optional[datetime] = None
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    doctor_name: Optional[str] = None  # New field added
    appointment_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: str
    created_at: datetime
    updated_at: datetime