# app/utils/ocr_processor.py
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import re
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    """Processes images to extract health measurements using OCR"""
    
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        print('Tesseract path set.')
        pass
    
    def process_image(self, image_data: bytes, measurement_type: str) -> Dict[str, Any]:
        """
        Process image data to extract health measurement values
        
        Args:
            image_data: Raw image bytes
            measurement_type: Type of measurement ("blood_pressure" or "blood_sugar")
            
        Returns:
            Dictionary with extracted values
        """
        try:
            # Convert bytes to opencv image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Preprocess image
            preprocessed_img = self._preprocess_image(img)
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(preprocessed_img)
            logger.info(f"OCR extracted text: {extracted_text}")
            
            # Process based on measurement type
            if measurement_type == "blood_pressure":
                return self._extract_blood_pressure(extracted_text)
            elif measurement_type == "blood_sugar":
                return self._extract_blood_sugar(extracted_text)
            else:
                raise ValueError(f"Unsupported measurement type: {measurement_type}")
                
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            raise
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            img: OpenCV image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise removal using morphological operations
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Additional contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return enhanced
    
    def _extract_blood_pressure(self, text: str) -> Dict[str, Any]:
        """
        Extract blood pressure values from OCR text
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with systolic, diastolic, and optionally pulse values
        """
        logger.info(f"Extracting blood pressure from text: {text}")
        
        # Common formats: "120/80", "SYS 120 DIA 80 PULSE 72"
        systolic = None
        diastolic = None
        pulse = None
        
        # Try to find systolic/diastolic in format like "120/80"
        bp_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', text)
        if bp_match:
            systolic = int(bp_match.group(1))
            diastolic = int(bp_match.group(2))
        
        # Look for labeled values
        sys_match = re.search(r'(?:SYS|SYSTOLIC)[:\s]+(\d{2,3})', text, re.IGNORECASE)
        dia_match = re.search(r'(?:DIA|DIASTOLIC)[:\s]+(\d{2,3})', text, re.IGNORECASE)
        pulse_match = re.search(r'(?:PUL|PULSE)[:\s]+(\d{2,3})', text, re.IGNORECASE)
        
        if sys_match:
            systolic = int(sys_match.group(1))
        if dia_match:
            diastolic = int(dia_match.group(1))
        if pulse_match:
            pulse = int(pulse_match.group(1))
        
        # Last resort: look for any two numbers that could be systolic/diastolic
        if systolic is None or diastolic is None:
            numbers = re.findall(r'\b(\d{2,3})\b', text)
            if len(numbers) >= 2:
                # Usually the first larger number is systolic, the second smaller number is diastolic
                potential_values = [int(num) for num in numbers]
                potential_values.sort(reverse=True)  # Sort in descending order
                
                if systolic is None and len(potential_values) > 0:
                    systolic = potential_values[0]
                
                if diastolic is None and len(potential_values) > 1:
                    diastolic = potential_values[1]
        
        # Validate and return results
        if systolic is None or diastolic is None:
            raise ValueError("Could not extract blood pressure values from image")
        
        # Sanity check for blood pressure values
        if systolic < diastolic:
            # Swap if systolic is less than diastolic (common OCR error)
            systolic, diastolic = diastolic, systolic
            
        if systolic < 60 or systolic > 250 or diastolic < 30 or diastolic > 150:
            raise ValueError(f"Extracted blood pressure values are outside reasonable range: {systolic}/{diastolic}")
        
        result = {
            "systolic": systolic,
            "diastolic": diastolic
        }
        
        if pulse is not None:
            if 30 <= pulse <= 220:  # Sanity check for pulse
                result["pulse"] = pulse
            
        return result
    
    def _extract_blood_sugar(self, text: str) -> Dict[str, Any]:
        """
        Extract blood sugar value and unit from OCR text
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with blood sugar value and unit
        """
        logger.info(f"Extracting blood sugar from text: {text}")
        
        # Look for patterns like "Blood Glucose: 120 mg/dL"
        value_match = None
        
        # General numeric pattern with optional decimal
        numeric_patterns = [
            r'(\d+\.?\d*)\s*(mg/dL|mmol/L|mg|mmol)',  # Value with unit
            r'(?:glucose|sugar|reading|glucose reading)[:\s]+(\d+\.?\d*)',  # Labeled value
            r'(\d+\.?\d*)\s*(?:mg|mmol)'  # Value with partial unit
        ]
        
        for pattern in numeric_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_match = match
                break
        
        # Last resort: look for any number that could be blood sugar
        if not value_match:
            # Look for numbers in a typical blood sugar range (40-600 mg/dL or 2.2-33.3 mmol/L)
            numbers = re.findall(r'\b(\d+\.?\d*)\b', text)
            if numbers:
                for num in numbers:
                    value = float(num)
                    # Determine if it's in a reasonable blood sugar range
                    if 40 <= value <= 600:  # mg/dL range
                        value_match = re.search(num, text)
                        break
                    elif 2.0 <= value <= 33.3:  # mmol/L range
                        value_match = re.search(num, text)
                        break
        
        if value_match:
            try:
                value = float(value_match.group(1))
                
                # Try to determine unit
                unit = "mg/dL"  # Default
                if "mmol" in text.lower():
                    unit = "mmol/L"
                
                # Sanity checks for blood sugar values
                if unit == "mg/dL" and (value < 20 or value > 800):
                    raise ValueError(f"Blood sugar value {value} {unit} is outside reasonable range")
                elif unit == "mmol/L" and (value < 1.1 or value > 44.4):
                    raise ValueError(f"Blood sugar value {value} {unit} is outside reasonable range")
                
                return {
                    "value": value,
                    "unit": unit
                }
            except ValueError as e:
                logger.error(f"Error parsing blood sugar value: {str(e)}")
                raise ValueError("Could not extract valid blood sugar value from image")
        else:
            raise ValueError("Could not extract blood sugar value from image")