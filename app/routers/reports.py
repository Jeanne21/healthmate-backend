# app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from enum import Enum
from typing import Optional
import logging
from firebase_client import FirebaseClient
from routers.auth import get_current_user
import traceback

# Import our PDF report generator 
from report_generator import ReportGenerator

router = APIRouter()
logger = logging.getLogger(__name__)
firebase_client = FirebaseClient()

# Create an enum for report types
class ReportType(str, Enum):
    medications = "medications"
    measurements = "measurements"
    combined = "combined"

@router.get("/export/pdf", 
           summary="Export user data as PDF", 
           description="Generate a PDF report of user's health data with options for medications, measurements, or both.")
async def export_pdf(
    report_type: ReportType = Query(
        ReportType.combined, 
        description="Type of report to generate"
    ),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a PDF export of user data based on the requested report type.
    
    - **report_type**: Type of report to generate (medications, measurements, or combined)
    
    Returns a downloadable PDF file.
    """
    try:
        # Get user ID from authenticated user
        logger.debug(f"Current user object: {current_user}")
        user_id = current_user.get("id") or current_user.get("user_id")  # ✅ fallback if needed
        
        # Generate the PDF
        report_generator = ReportGenerator()
        pdf_buffer = report_generator.generate_pdf_report(user_id, report_type.value)
        
        # Determine filename based on report type
        filename = f"{report_type.value}_report_{user_id}.pdf"
        
        # Return the PDF as a downloadable file
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(
            pdf_buffer, 
            media_type='application/pdf',
            headers=headers
        )
    
    except ValueError as e:
        logger.error(f"Value error in PDF export: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        traceback.print_exc()  # This will show the full traceback in the console
        raise HTTPException(status_code=500, detail="Failed to generate report. Please try again later.")
