import re
import phonenumbers
from typing import Tuple

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format and return (is_valid, error_message)"""
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    if not email:
        return False, "Email is required"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""

def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate phone number (Indian format primarily)"""
    if not phone:
        return False, "Phone number is required"
    try:
        # Try parsing as Indian number first
        parsed = phonenumbers.parse(phone, "IN")
        if not phonenumbers.is_valid_number(parsed):
            return False, "Invalid phone number"
        return True, ""
    except:
        return False, "Invalid phone number format"

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, ""

def validate_password_match(password: str, confirm_password: str) -> Tuple[bool, str]:
    """Check if passwords match"""
    if password != confirm_password:
        return False, "Passwords do not match"
    return True, ""
