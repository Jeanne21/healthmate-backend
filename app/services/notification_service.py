# app/services/notification_service.py
import firebase_admin
from firebase_admin import messaging
from datetime import datetime, timedelta
import json
import logging
from app.config import Settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling push notifications"""
    
    def __init__(self):
        self.settings = Settings()
        self.enabled = self.settings.ENABLE_NOTIFICATIONS
    
    def schedule_medication_reminder(self, user_id, medication_id, medication_name, next_dose):
        """Schedule a medication reminder notification"""
        if not self.enabled:
            logger.info("Notifications are disabled. Skipping medication reminder scheduling.")
            return
        
        try:
            # Get the user's FCM token
            from app.firebase_client import FirebaseClient
            firebase_client = FirebaseClient()
            
            user_data = firebase_client.get_user(user_id)
            if not user_data or 'fcm_token' not in user_data:
                logger.warning(f"User {user_id} has no FCM token. Cannot schedule medication reminder.")
                return
            
            fcm_token = user_data['fcm_token']
            
            # Calculate when to send the notification
            now = datetime.now()
            if isinstance(next_dose, str):
                next_dose = datetime.fromisoformat(next_dose.replace('Z', '+00:00'))
            
            # Send a notification 15 minutes before the dose is due
            notification_time = next_dose - timedelta(minutes=15)
            
            # If the notification time is in the past, don't send it
            if notification_time < now:
                logger.info(f"Notification time for medication {medication_id} is in the past. Skipping.")
                return
            
            # Create the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Medication Reminder",
                    body=f"Time to take your {medication_name}"
                ),
                data={
                    "type": "medication_reminder",
                    "medication_id": medication_id,
                    "medication_name": medication_name
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    ttl=timedelta(minutes=60),
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='notification_icon',
                        color='#f45342'
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            badge=1,
                            sound='default',
                            content_available=True
                        )
                    )
                )
            )
            
            # Store the scheduled notification in Firebase
            notification_data = {
                'user_id': user_id,
                'type': 'medication_reminder',
                'medication_id': medication_id,
                'scheduled_time': notification_time,
                'status': 'scheduled',
                'created_at': datetime.now()
            }
            
            firebase_client.db.collection('notifications').document().set(notification_data)
            
            logger.info(f"Scheduled medication reminder for {medication_name}, user {user_id} at {notification_time}")
            return True
        # Note: In a real application, you would use a task scheduler like Celery
            # to schedule the notification to be sent at the specified time.
            # For this example, we're just storing the notification data in Firebase.
            # A separate process or cloud function would need to check for pending
            # notifications and send them when their scheduled time arrives.
            
        except Exception as e:
            logger.error(f"Error scheduling medication reminder: {str(e)}")
            return False
    
    def cancel_medication_reminder(self, user_id, medication_id):
        """Cancel scheduled medication reminders for a specific medication"""
        if not self.enabled:
            logger.info("Notifications are disabled. Skipping reminder cancellation.")
            return
        
        try:
            from app.firebase_client import FirebaseClient
            firebase_client = FirebaseClient()
            
            # Find all scheduled notifications for this medication
            notifications_ref = firebase_client.db.collection('notifications')
            query = notifications_ref.where('user_id', '==', user_id).where('medication_id', '==', medication_id).where('status', '==', 'scheduled')
            
            scheduled_notifications = query.get()
            
            for notification in scheduled_notifications:
                # Mark the notification as cancelled
                notification.reference.update({'status': 'cancelled'})
            
            logger.info(f"Cancelled {len(scheduled_notifications)} reminders for medication {medication_id}, user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling medication reminders: {str(e)}")
            return False
    
    def send_appointment_reminder(self, user_id, appointment_id, appointment_data):
        """Send appointment reminder notification"""
        if not self.enabled:
            logger.info("Notifications are disabled. Skipping appointment reminder.")
            return
        
        try:
            # Get the user's FCM token
            from app.firebase_client import FirebaseClient
            firebase_client = FirebaseClient()
            
            user_data = firebase_client.get_user(user_id)
            if not user_data or 'fcm_token' not in user_data:
                logger.warning(f"User {user_id} has no FCM token. Cannot send appointment reminder.")
                return
            
            fcm_token = user_data['fcm_token']
            
            # Create the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Appointment Reminder",
                    body=f"You have an appointment with {appointment_data.get('doctor_name', 'your doctor')} at {appointment_data.get('time')}"
                ),
                data={
                    "type": "appointment_reminder",
                    "appointment_id": appointment_id
                },
                token=fcm_token
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent appointment reminder: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {str(e)}")
            return False