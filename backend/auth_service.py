import bcrypt
from typing import Optional, Tuple, Dict
from backend.db_connection import DatabaseConnection
from utils.validators import (
    validate_username, validate_email, 
    validate_phone, validate_password
)
import logging


logger = logging.getLogger(__name__)


class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def check_username_availability(username: str) -> bool:
        """Check if username is available"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE username = %s",
                    (username,)
                )
                return cursor.fetchone() is None
        except Exception as e:
            logger.error(f"Error checking username availability: {e}")
            return False
    
    @staticmethod
    def check_email_availability(email: str) -> bool:
        """Check if email is available"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE email = %s",
                    (email,)
                )
                return cursor.fetchone() is None
        except Exception as e:
            logger.error(f"Error checking email availability: {e}")
            return False
    
    @staticmethod
    def register_user(
        username: str,
        email: str,
        phone: str,
        password: str,
        user_type: str,
        security_question: str,
        security_answer: str,
        full_name: str = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Register a new user
        Returns: (success, message, user_id)
        """
        try:
            # Validate inputs before proceeding
            is_valid, msg = validate_username(username)
            if not is_valid:
                return False, msg, None
            
            is_valid, msg = validate_email(email)
            if not is_valid:
                return False, msg, None
            
            is_valid, msg = validate_phone(phone)
            if not is_valid:
                return False, msg, None
            
            is_valid, msg = validate_password(password)
            if not is_valid:
                return False, msg, None
            
            # Hash password and security answer
            password_hash = AuthService.hash_password(password)
            answer_hash = AuthService.hash_password(security_answer.lower().strip())
            
            with DatabaseConnection.get_cursor() as cursor:
                # Insert user with full_name field
                cursor.execute(
                    """
                    INSERT INTO users (username, full_name, password_hash, email, phone, 
                                     user_type, security_question, security_answer_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING user_id
                    """,
                    (username, full_name, password_hash, email, phone, user_type, 
                     security_question, answer_hash)
                )
                user_id = cursor.fetchone()['user_id']
                
                # If patient, create patient profile (if you have a separate patients table)
                if user_type == 'patient' and full_name:
                    try:
                        cursor.execute(
                            """
                            INSERT INTO patients (user_id, full_name, phone)
                            VALUES (%s, %s, %s)
                            """,
                            (user_id, full_name, phone)
                        )
                    except Exception as e:
                        # Log but don't fail registration if patients table doesn't exist
                        logger.warning(f"Could not create patient profile: {e}")
                
                return True, "Registration successful", user_id
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, f"Registration failed: {str(e)}", None
    
    @staticmethod
    def login_user(username: str, password: str, user_type: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user
        Returns: (success, message, user_data)
        """
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username, full_name, password_hash, email, phone, user_type
                    FROM users
                    WHERE username = %s AND user_type = %s
                    """,
                    (username, user_type)
                )
                user = cursor.fetchone()
                
                if not user:
                    return False, "Invalid username or user type", None
                
                if not AuthService.verify_password(password, user['password_hash']):
                    return False, "Invalid password", None
                
                # Get additional info for patients (if you have a separate patients table)
                if user_type == 'patient':
                    try:
                        cursor.execute(
                            """
                            SELECT patient_id, full_name
                            FROM patients
                            WHERE user_id = %s
                            """,
                            (user['user_id'],)
                        )
                        patient_info = cursor.fetchone()
                        if patient_info:
                            user.update(patient_info)
                    except Exception as e:
                        # Log but continue if patients table doesn't exist
                        logger.warning(f"Could not fetch patient info: {e}")
                
                # Remove sensitive data before returning
                user_data = dict(user)
                user_data.pop('password_hash', None)
                
                return True, "Login successful", user_data
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, "Login failed", None
    
    @staticmethod
    def get_security_question(username: str) -> Tuple[bool, str, Optional[str]]:
        """Get security question for a username"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT security_question
                    FROM users
                    WHERE username = %s
                    """,
                    (username,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False, "Username not found", None
                
                return True, "Security question retrieved", result['security_question']
                
        except Exception as e:
            logger.error(f"Error retrieving security question: {e}")
            return False, "Failed to retrieve security question", None
    
    @staticmethod
    def verify_security_answer(username: str, question: str, answer: str) -> Tuple[bool, str]:
        """Verify security question answer for password reset"""
        try:
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT security_answer_hash
                    FROM users
                    WHERE username = %s AND security_question = %s
                    """,
                    (username, question)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False, "Invalid username or security question"
                
                if AuthService.verify_password(answer.lower().strip(), result['security_answer_hash']):
                    return True, "Security answer verified"
                else:
                    return False, "Incorrect security answer"
                    
        except Exception as e:
            logger.error(f"Security verification error: {e}")
            return False, "Verification failed"
    
    @staticmethod
    def reset_password(username: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password"""
        try:
            # Validate new password
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                return False, msg
            
            password_hash = AuthService.hash_password(new_password)
            
            with DatabaseConnection.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE username = %s
                    """,
                    (password_hash, username)
                )
                
                if cursor.rowcount > 0:
                    return True, "Password reset successful"
                else:
                    return False, "User not found"
                    
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return False, "Password reset failed"
