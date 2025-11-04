# app/routers/medications.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.medication import MedicationCreate, MedicationUpdate, MedicationResponse
from typing import List
from datetime import datetime, timedelta
from app.routers.auth import get_current_user
from app.firebase_client import FirebaseClient
from app.services.notification_service import NotificationService
import logging
import traceback

router = APIRouter()
firebase_client = FirebaseClient()
notification_service = NotificationService()

#Get medications
@router.get("/", response_model=List[MedicationResponse])
async def get_medications(current_user = Depends(get_current_user)):
    """Get all medications for the current user"""
    try:
        print(f"Fetching medications for user: {current_user['id']}")
        medications = firebase_client.get_medications(current_user['id'])
        print(f"Retrieved {len(medications)} medications")
        return medications
    except Exception as e:
        print(f"Error details: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve medications: {str(e)}"
        )

#Get upcoming medications
@router.get("/upcoming", response_model=List[MedicationResponse])
async def get_upcoming_medications(current_user = Depends(get_current_user)):
    """Get upcoming medications for the current user"""
    try:
        medications = firebase_client.get_upcoming_medications(current_user['id'])
        return medications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve upcoming medications: {str(e)}"
        )

#Create medication
@router.post("/", response_model=MedicationResponse)
async def create_medication(
    medication: MedicationCreate, 
    current_user = Depends(get_current_user)
):
    """Create a new medication for the current user"""
    try:
        logging.info(f"Received medication: {medication}")
        medication_data = medication.dict(exclude_unset=False)  # Use .dict() instead of .model_dump()
        logging.info(f"Medication data (before processing): {medication_data}")

        # Set last_taken to None initially
        medication_data['last_taken'] = None

        # Ensure preferred_time is stored
        if medication.preferred_time:
            preferred_hour, preferred_minute = map(int, medication.preferred_time.split(":"))
            start_date_with_time = medication_data['start_date'].replace(
                hour=preferred_hour,
                minute=preferred_minute,
                second=0,
                microsecond=0
            )
            medication_data['next_dose'] = start_date_with_time
            logging.info(f"Calculated next dose (preferred time): {start_date_with_time}")
        else:
            medication_data['next_dose'] = medication_data['start_date'] + timedelta(hours=medication_data['frequency'])
            logging.info(f"Calculated next dose (default): {medication_data['next_dose']}")
            
        # Log the incoming medication data for debugging
        logging.info(f"Medication data: {medication_data}")

        logging.info(f"Start date type: {type(medication_data['start_date'])}")
        logging.info(f"Frequency type: {type(medication_data['frequency'])}")

        if medication_data['start_date'] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date is required and cannot be None"
            )
        if medication_data['frequency'] is None or medication_data['frequency'] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Frequency must be a positive integer"
            )

        medication_id = firebase_client.add_medication(current_user['id'], medication_data)
        logging.info(f"Medication ID returned: {medication_id}")
        
        # # Schedule notification for this medication
        # notification_service.schedule_medication_reminder(
        #     user_id=current_user['id'],
        #     medication_id=medication_id,
        #     medication_name=medication_data['name'],
        #     next_dose=medication_data['next_dose']
        # )
        
        # Return the created medication
        created_medication = firebase_client.get_medications(current_user['id'])
        for med in created_medication:
            if med.get('id') == medication_id:
                return med
        
        logging.info(f"Created medication response: {created_medication}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Medication created but could not be retrieved"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medication: {str(e)}"
        )

#Update medication
@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: str,
    medication: MedicationUpdate,
    current_user = Depends(get_current_user)
):
    """Update a medication for the current user"""
    try:
        medication_data = {k: v for k, v in medication.dict().items() if v is not None}
        
        # Update the medication
        firebase_client.update_medication(current_user['id'], medication_id, medication_data)
        
        if 'last_taken' in medication_data:
            # Get the updated medication to get the new next_dose
            medications = firebase_client.get_medications(current_user['id'])
            updated_med = next((m for m in medications if m.get('id') == medication_id), None)
            
            if updated_med and 'next_dose' in updated_med:
                notification_service.schedule_medication_reminder(
                    user_id=current_user['id'],
                    medication_id=medication_id,
                    medication_name=updated_med.get('name'),
                    next_dose=updated_med.get('next_dose')
                )
        
        medications = firebase_client.get_medications(current_user['id'])
        for med in medications:
            if med.get('id') == medication_id:
                return med
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found after update"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medication: {str(e)}"
        )

#Delete medication
@router.delete("/{medication_id}")
async def delete_medication(
    medication_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a medication for the current user"""
    try:
        medications = firebase_client.get_medications(current_user['id'])
        medication = next((m for m in medications if m.get('id') == medication_id), None)
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        result = firebase_client.db.collection('users').document(current_user['id']).collection('medications').document(medication_id).delete()
        
        notification_service.cancel_medication_reminder(current_user['id'], medication_id)
        
        return {"message": "Medication deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medication: {str(e)}"
        )

#Taken medicine
@router.post("/{medication_id}/take")
async def mark_medication_as_taken(
    medication_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a medication as taken"""
    try:
        medications = firebase_client.get_medications(current_user['id'])
        medication = next((m for m in medications if m.get('id') == medication_id), None)
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        now = datetime.now()
        medication_data = {
            'last_taken': now
        }
        
        firebase_client.update_medication(current_user['id'], medication_id, medication_data)
        
        medications = firebase_client.get_medications(current_user['id'])
        for med in medications:
            if med.get('id') == medication_id:
                return med
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found after update"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark medication as taken: {str(e)}"
        )
