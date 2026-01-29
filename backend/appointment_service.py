from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
from backend.db_connection import DatabaseConnection
from config.settings import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class AppointmentService:
    
    @staticmethod
    def generate_appointment_id() -> str:
        """Generate unique appointment ID"""
        return f"APT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def get_available_time_slots(appointment_date: date) -> List[str]:
        """
        Get available 30-minute time slots from 9 AM to 9 PM
        """
        slots = []
        current_time = time(settings.APPOINTMENT_START_HOUR, 0)
        end_time = time(settings.APPOINTMENT_END_HOUR, 0)
        
        while current_time < end_time:
            slots.append(current_time.strftime("%I:%M %p"))
            # Add 30 minutes
            current_datetime = datetime.combine(date.today(), current_time)
            current_datetime += timedelta(minutes=settings.APPOINTMENT_SLOT_MINUTES)
            current_time = current_datetime.time()
        
        return slots
    
    @staticmethod
    def is_valid_appointment_time(appointment_time: time) -> bool:
        """Check if time is within valid appointment hours"""
        start_time = time(settings.APPOINTMENT_START_HOUR, 0)
        end_time = time(settings.APPOINTMENT_END_HOUR, 0)
        return start_time <= appointment_time < end_time
    
    @staticmethod
    def is_future_datetime(appointment_date: date, appointment_time: time) -> bool:
        """Check if appointment is in the future"""
        now = datetime.now()
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        return appointment_datetime > now
    
    @staticmethod
    def get_doctors_by_specialization(specialization: str) -> List[Dict]:
        """Get list of doctors for a specialization"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT doctor_id, full_name, specialization, qualification, 
                           consultation_fee
                    FROM doctors
                    WHERE LOWER(specialization) = LOWER(%s) AND is_active = TRUE
                    ORDER BY full_name
                    """,
                    (specialization,)
                )
                doctors = cursor.fetchall()
                return [dict(doc) for doc in doctors]
        except Exception as e:
            logger.error(f"Error fetching doctors: {e}")
            return []
    
    @staticmethod
    def get_doctors_available_on_date(
        specialization: str, 
        appointment_date: date
    ) -> List[Dict]:
        """
        Get doctors available on a specific date
        (Simplified - checks if doctor has that weekday in available_days)
        """
        try:
            weekday_name = appointment_date.strftime("%A")
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT doctor_id, full_name, specialization, qualification, 
                           consultation_fee, available_days
                    FROM doctors
                    WHERE LOWER(specialization) = LOWER(%s) 
                    AND is_active = TRUE
                    AND (available_days ILIKE %s OR available_days IS NULL)
                    ORDER BY full_name
                    """,
                    (specialization, f"%{weekday_name}%")
                )
                doctors = cursor.fetchall()
                return [dict(doc) for doc in doctors]
        except Exception as e:
            logger.error(f"Error fetching available doctors: {e}")
            return []
    
    @staticmethod
    def check_doctor_availability(
        doctor_id: int, 
        appointment_date: date, 
        appointment_time: time
    ) -> bool:
        """Check if doctor has a conflicting appointment"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM appointments
                    WHERE doctor_id = %s 
                    AND appointment_date = %s
                    AND appointment_time = %s
                    AND status != 'cancelled'
                    """,
                    (doctor_id, appointment_date, appointment_time)
                )
                result = cursor.fetchone()
                return result['count'] == 0
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False
    
    @staticmethod
    def create_appointment(
        patient_id: int,
        doctor_id: int,
        appointment_date: date,
        appointment_time: time,
        symptoms: str,
        patient_name: str,
        patient_contact: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new appointment
        Returns: (success, message, appointment_id)
        """
        try:
            # Validate date and time
            if not AppointmentService.is_future_datetime(appointment_date, appointment_time):
                return False, "Appointment must be in the future", None
            
            if not AppointmentService.is_valid_appointment_time(appointment_time):
                return False, f"Appointments available from {settings.APPOINTMENT_START_HOUR}:00 AM to {settings.APPOINTMENT_END_HOUR}:00 PM", None
            
            # Check doctor availability
            if not AppointmentService.check_doctor_availability(doctor_id, appointment_date, appointment_time):
                return False, "Doctor not available at this time", None
            
            # Generate appointment ID
            appointment_id = AppointmentService.generate_appointment_id()
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO appointments 
                    (appointment_id, patient_id, doctor_id, appointment_date, 
                     appointment_time, symptoms, patient_name, patient_contact, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'scheduled')
                    """,
                    (appointment_id, patient_id, doctor_id, appointment_date, 
                     appointment_time, symptoms, patient_name, patient_contact)
                )
            
            return True, "Appointment booked successfully", appointment_id
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return False, "Failed to create appointment", None
    
    @staticmethod
    def get_appointment_details(appointment_id: str) -> Optional[Dict]:
        """Get full appointment details"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT a.*, d.full_name as doctor_name, d.specialization,
                           d.qualification, d.consultation_fee
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    WHERE a.appointment_id = %s
                    """,
                    (appointment_id,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error fetching appointment: {e}")
            return None

# Global instance
appointment_service = AppointmentService()
