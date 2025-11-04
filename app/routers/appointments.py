# app/routers/appointments.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from typing import List
from datetime import datetime
from app.routers.auth import get_current_user
from app.firebase_client import FirebaseClient
from app.services.notification_service import NotificationService
import logging

router = APIRouter()
firebase_client = FirebaseClient()
notification_service = NotificationService()

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(current_user = Depends(get_current_user)):
    """Get all appointments for the current user"""
    try:
        appointments = firebase_client.get_appointments(current_user['id'])
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointments: {str(e)}"
        )

@router.get("/upcoming", response_model=List[AppointmentResponse])
async def get_upcoming_appointments(current_user = Depends(get_current_user)):
    """Get upcoming appointments for the current user"""
    try:
        appointments = firebase_client.get_upcoming_appointments(current_user['id'])
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve upcoming appointments: {str(e)}"
        )

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentCreate, 
    current_user = Depends(get_current_user)
):
    """Create a new appointment for the current user"""
    try:
        appointment_data = appointment.dict()  # Use .dict() instead of .model_dump()

        # Set reminder_time to None initially
        appointment_data['reminder_time'] = appointment_data.get('reminder_time', None)

        # Log the incoming appointment data for debugging
        logging.info(f"Appointment data: {appointment_data}")

        if appointment_data['appointment_date'] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment date is required and cannot be None"
            )
        
        appointment_id = firebase_client.add_appointment(current_user['id'], appointment_data)
        
        # # Schedule notification for this appointment
        # notification_service.schedule_appointment_reminder(
        #     user_id=current_user['id'],
        #     appointment_id=appointment_id,
        #     appointment_title=appointment_data['title'],
        #     reminder_time=appointment_data.get('reminder_time')
        # )
        
        # Return the created appointment
        created_appointment = firebase_client.get_appointments(current_user['id'])
        for app in created_appointment:
            if app.get('id') == appointment_id:
                return app
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Appointment created but could not be retrieved"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}"
        )

@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    appointment: AppointmentUpdate,
    current_user = Depends(get_current_user)
):
    """Update an appointment for the current user"""
    try:
        appointment_data = {k: v for k, v in appointment.dict().items() if v is not None}
        
        # Update the appointment
        firebase_client.update_appointment(current_user['id'], appointment_id, appointment_data)
        
        if 'reminder_time' in appointment_data:
            # Get the updated appointment to get the new reminder_time
            appointments = firebase_client.get_appointments(current_user['id'])
            updated_app = next((a for a in appointments if a.get('id') == appointment_id), None)
            
            # if updated_app and 'reminder_time' in updated_app:
            #     notification_service.schedule_appointment_reminder(
            #         user_id=current_user['id'],
            #         appointment_id=appointment_id,
            #         appointment_title=updated_app.get('title'),
            #         reminder_time=updated_app.get('reminder_time')
            #     )
        
        appointments = firebase_client.get_appointments(current_user['id'])
        for app in appointments:
            if app.get('id') == appointment_id:
                return app
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found after update"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment: {str(e)}"
        )

@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    current_user = Depends(get_current_user)
):
    """Delete an appointment for the current user"""
    try:
        appointments = firebase_client.get_appointments(current_user['id'])
        appointment = next((a for a in appointments if a.get('id') == appointment_id), None)
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        result = firebase_client.db.collection('users').document(current_user['id']).collection('appointments').document(appointment_id).delete()
        
        notification_service.cancel_appointment_reminder(current_user['id'], appointment_id)
        
        return {"message": "Appointment deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete appointment: {str(e)}"
        )

@router.post("/{appointment_id}/reminder")
async def mark_appointment_as_reminded(
    appointment_id: str,
    current_user = Depends(get_current_user)
):
    """Mark an appointment as reminded"""
    try:
        appointments = firebase_client.get_appointments(current_user['id'])
        appointment = next((a for a in appointments if a.get('id') == appointment_id), None)
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        now = datetime.now()
        appointment_data = {
            'reminder_time': now
        }
        
        firebase_client.update_appointment(current_user['id'], appointment_id, appointment_data)
        
        appointments = firebase_client.get_appointments(current_user['id'])
        for app in appointments:
            if app.get('id') == appointment_id:
                return app
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found after update"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark appointment as reminded: {str(e)}"
        )
