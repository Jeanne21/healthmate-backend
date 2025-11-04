# app/firebase_client.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

# Load environment variables from .env file
load_dotenv()

class FirebaseClient:
    """Firebase client for health tracker application"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)

            # Initialize Firebase only once
            if not firebase_admin._apps:
                try:
                    # First, check for credentials JSON in environment (for deployment)
                    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
                    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

                    if cred_json:
                        logging.info("Initializing Firebase using JSON credentials from environment.")
                        cred_dict = json.loads(cred_json)
                        cred = credentials.Certificate(cred_dict)
                    elif cred_path:
                        logging.info(f"Initializing Firebase using local credentials file: {cred_path}")
                        
                        # Use absolute path if needed
                        if not os.path.isabs(cred_path):
                            cred_path = os.path.join(os.path.dirname(__file__), cred_path)
                        
                        if not os.path.exists(cred_path):
                            raise ValueError(f"Invalid Firebase credentials path: {cred_path}")
                        
                        cred = credentials.Certificate(cred_path)
                    else:
                        raise ValueError("Firebase credentials not found. Set FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH.")
                    
                    firebase_admin.initialize_app(cred)
                    cls._instance.db = firestore.client()
                    logging.info("Firebase initialized successfully.")
                
                except Exception as e:
                    logging.error(f"Error initializing Firebase: {e}")
                    raise e

        return cls._instance
    
    #Get user
    def get_user(self, user_id):
        """Get user data by ID"""
        user_ref = self.db.collection('users').document(user_id)
        user = user_ref.get()
        if user.exists:
            return user.to_dict()
        return None
    
    #Create user
    def create_user(self, user_data):
        """Create a new user in Firebase Authentication and Firestore"""
        try:
            # Create user in Firebase Authentication
            user = auth.create_user(
                email=user_data.get('email'),
                password=user_data.get('password'),
                display_name=user_data.get('name')
            )
        
            # Store additional user data in Firestore
            user_ref = self.db.collection('users').document(user.uid)
            user_data_to_store = {
                'id': user.uid,
                'name': user_data.get('name'),
                'email': user_data.get('email'),
                'phone': user_data.get('phone', ''),
                'gender': user_data.get('gender', ''),
                'date_of_birth': user_data.get('date_of_birth', ''),
                'blood_type': user_data.get('blood_type', ''),
                'height': user_data.get('height', 0),
                'weight': user_data.get('weight', 0),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            user_ref.set(user_data_to_store)
        
            return user.uid
        except Exception as e:
            raise e
    
    #Update user
    def update_user(self, user_id, user_data):
        """Update user data"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_data['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.update(user_data)
            return True
        except Exception as e:
            raise e
    
    #Get medications
    def get_medications(self, user_id):
        """Get all medications for a user"""
        medications_ref = self.db.collection('users').document(user_id).collection('medications')
        medications = medications_ref.get()
        return [doc.to_dict() for doc in medications]
    
    #Get upcoming medications
    def get_upcoming_medications(self, user_id, limit=5):
        """Get upcoming medications for a user"""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        medications_ref = (self.db.collection('users').document(user_id)
                          .collection('medications')
                          .where('next_dose', '>=', now)
                          .where('next_dose', '<=', tomorrow)
                          .order_by('next_dose')
                          .limit(limit))
        
        medications = medications_ref.get()
        return [doc.to_dict() for doc in medications]
    
    #Add medication
    def add_medication(self, user_id, medication_data):
        """Add a new medication for a user"""
        try:
            medications_ref = self.db.collection('users').document(user_id).collection('medications')
            medication_data['created_at'] = firestore.SERVER_TIMESTAMP
            medication_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Calculate next dose time
            if 'frequency' in medication_data and 'last_taken' in medication_data and medication_data['last_taken']:
                last_taken = medication_data['last_taken']
                frequency_hours = medication_data['frequency']
                if isinstance(last_taken, str):
                    last_taken = datetime.fromisoformat(last_taken.replace('Z', '+00:00'))
                next_dose = last_taken + timedelta(hours=frequency_hours)
                medication_data['next_dose'] = next_dose

            logging.info(f"Saving medication data: {medication_data}")

            doc_ref = medications_ref.document()
            medication_data['id'] = doc_ref.id
            doc_ref.set(medication_data)

            logging.info(f"Medication document created with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            raise e
    
    #Update medication
    def update_medication(self, user_id, medication_id, medication_data):
        """Update a medication for a user"""
        try:
            medication_ref = (self.db.collection('users').document(user_id)
                             .collection('medications').document(medication_id))
            
            medication_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Recalculate next dose if necessary
            if 'frequency' in medication_data and 'last_taken' in medication_data:
                last_taken = medication_data['last_taken']
                frequency_hours = medication_data['frequency']
                if isinstance(last_taken, str):
                    last_taken = datetime.fromisoformat(last_taken.replace('Z', '+00:00'))
                next_dose = last_taken + timedelta(hours=frequency_hours)
                medication_data['next_dose'] = next_dose
            
            medication_ref.update(medication_data)
            return True
        except Exception as e:
            raise e
    
    #Get appointments
    def get_appointments(self, user_id):
        """Get all appointments for a user"""
        appointments_ref = self.db.collection('users').document(user_id).collection('appointments')
        appointments = appointments_ref.get()
        return [doc.to_dict() for doc in appointments]
    
    #Get upcoming appointments
    def get_upcoming_appointments(self, user_id, limit=5):
        """Get upcoming appointments for a user"""
        now = datetime.now()
        appointments_ref = (self.db.collection('users').document(user_id)
                           .collection('appointments')
                           .where('date', '>=', now)
                           .order_by('date')
                           .limit(limit))
        
        appointments = appointments_ref.get()
        return [doc.to_dict() for doc in appointments]
    
    #Add appointment
    def add_appointment(self, user_id, appointment_data):
        """Add a new appointment for a user"""
        try:
            appointments_ref = self.db.collection('users').document(user_id).collection('appointments')
            appointment_data['created_at'] = firestore.SERVER_TIMESTAMP
            appointment_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = appointments_ref.document()
            appointment_data['id'] = doc_ref.id
            doc_ref.set(appointment_data)
            return doc_ref.id
        except Exception as e:
            raise e
    
    #Get measurements
    def get_measurements(self, user_id, measurement_type=None, limit=10):
        """Get health measurements for a user"""
        measurements_ref = self.db.collection('users').document(user_id).collection('measurements')
        
        if measurement_type:
            query = measurements_ref.where('type', '==', measurement_type).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        else:
            query = measurements_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        measurements = query.get()
        return [doc.to_dict() for doc in measurements]
    
    #Add measurement
    def add_measurement(self, user_id, measurement_data):
        """Add a new health measurement for a user"""
        try:
            measurements_ref = self.db.collection('users').document(user_id).collection('measurements')
            measurement_data['created_at'] = firestore.SERVER_TIMESTAMP
            measurement_data['timestamp'] = measurement_data.get('timestamp', firestore.SERVER_TIMESTAMP)

            # Optional safety check
            if "status" not in measurement_data:
                measurement_data["status"] = "unknown"  # fallback

            doc_ref = measurements_ref.document()
            measurement_data['id'] = doc_ref.id
            doc_ref.set(measurement_data)
            return doc_ref.id
        except Exception as e:
            raise e
        

    def verify_id_token(self, token):
        """
        Verify Firebase ID token and return user information
    
        Args:
            token (str): Firebase ID token
        
        Returns:
            dict: User information
        
        Raises:
            Exception: If token verification fails
        """
        try:
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(token)
        
            # Get additional user information from Firestore
            user_id = decoded_token['uid']
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
        
            if not user_doc.exists:
                # User exists in Authentication but not in Firestore
                return {
                    'uid': user_id,
                    'email': decoded_token.get('email', ''),
                    'name': decoded_token.get('name', '')
                }
        
            # Combine token data with Firestore data
            user_data = user_doc.to_dict()
            user_data['uid'] = user_id
        
            return user_data
        except Exception as e:
            logging.error(f"Token verification error: {str(e)}")
            raise e
        
    # Add dependents for a user
    def add_dependent(self, user_id, dependent_data):
        try:
            dependents_ref = self.db.collection('users').document(user_id).collection('dependents')
            dependent_data['created_at'] = firestore.SERVER_TIMESTAMP
            dependent_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
            doc_ref = dependents_ref.document()
            dependent_data['id'] = doc_ref.id
            doc_ref.set(dependent_data)
            return doc_ref.id
        except Exception as e:
            raise e

    # Get dependents for a user
    def get_dependents(self, user_id):
        try:
            dependents_ref = self.db.collection('users').document(user_id).collection('dependents')
            dependents = dependents_ref.get()
            return [doc.to_dict() for doc in dependents]
        except Exception as e:
            raise e

    # Update a dependent
    def update_dependent(self, user_id, dependent_id, dependent_data):
        try:
            dependent_ref = (self.db.collection('users')
                            .document(user_id)
                            .collection('dependents')
                            .document(dependent_id))
        
            dependent_data['updated_at'] = firestore.SERVER_TIMESTAMP
            dependent_ref.update(dependent_data)
            return True
        except Exception as e:
            raise e

                