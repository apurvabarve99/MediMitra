import streamlit as st
import re
from backend.auth_service import AuthService
from config.settings import settings


def validate_email_format(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_indian_phone_number(phone):
    """Validate Indian phone number - only digits allowed"""
    # Remove any non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it's a valid Indian number
    if cleaned.startswith('+91'):
        digits = cleaned[3:]
        if len(digits) == 10 and digits[0] in '6789':
            return True
    elif len(cleaned) == 10 and cleaned[0] in '6789':
        return True
    
    return False


def get_password_strength(password):
    """Calculate password strength"""
    strength = 0
    feedback = []
    
    if len(password) >= 8:
        strength += 1
    else:
        feedback.append("At least 8 characters")
    
    if re.search(r'[A-Z]', password):
        strength += 1
    else:
        feedback.append("One uppercase letter")
    
    if re.search(r'[a-z]', password):
        strength += 1
    else:
        feedback.append("One lowercase letter")
    
    if re.search(r'\d', password):
        strength += 1
    else:
        feedback.append("One number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        strength += 1
    
    levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
    colors = ["#ff0000", "#ff6600", "#ffcc00", "#99cc00", "#00cc00"]
    
    level = levels[min(strength, 4)]
    color = colors[min(strength, 4)]
    
    return level, color, feedback


def render_register_page():
    """Render the registration page with real-time validation"""
    
    # Center content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 20px;'>
                <h1 style='color: #1E88E5;'>Create Account</h1>
                <p style='color: #666;'>Register to access MediMitra services</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Initialize validation states
        if 'reg_email_valid' not in st.session_state:
            st.session_state.reg_email_valid = True
        if 'reg_phone_valid' not in st.session_state:
            st.session_state.reg_phone_valid = True
        if 'reg_pwd_match' not in st.session_state:
            st.session_state.reg_pwd_match = True
        if 'reg_username_valid' not in st.session_state:
            st.session_state.reg_username_valid = True
        
        # User type selection
        user_type = st.radio(
            "I am registering as:",
            options=["Patient", "Pharmacist"],
            horizontal=True,
            key="reg_user_type"
        )
        
        # Full name (required for both patients and pharmacists)
        full_name = st.text_input(
            "Full Name*", 
            placeholder="Enter your full name", 
            key="reg_full_name"
)

        
        # Username with availability check - inline validation
        col_user_input, col_user_msg = st.columns([3, 1])
        with col_user_input:
            username = st.text_input(
                "Username*", 
                placeholder="Choose a username (min 3 characters)", 
                key="reg_username"
            )
        with col_user_msg:
            if username:
                if len(username) < 3:
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">❌ Username Too Short</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_username_valid = False
                elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">❌ Invalid characters</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_username_valid = False
                elif not AuthService.check_username_availability(username):
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">❌ Username Already Taken</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_username_valid = False
                else:
                    st.markdown(
                        '<p style="color: green; font-size: 12px; margin-top: 30px;">✓ Username Available</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_username_valid = True
        
        # Email with real-time validation - inline
        col_email_input, col_email_msg = st.columns([3, 1])
        with col_email_input:
            email = st.text_input(
                "Email*", 
                placeholder="Enter your email address", 
                key="reg_email"
            )
        with col_email_msg:
            if email:
                if not validate_email_format(email):
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">Enter A Valid Email</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_email_valid = False
                elif not AuthService.check_email_availability(email):
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">❌ Email Already Registered</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_email_valid = False
                else:
                    st.markdown(
                        '<p style="color: green; font-size: 12px; margin-top: 30px;">✓ Email Valid</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_email_valid = True
        
        # Phone number - numeric only with real-time validation - inline
        col_phone_input, col_phone_msg = st.columns([3, 1])
        with col_phone_input:
            phone = st.text_input(
                "Phone Number*", 
                placeholder="+91XXXXXXXXXX or 10-digit number",
                max_chars=13,
                key="reg_phone"
            )
        
        if phone:
            # Filter out non-numeric characters (except + at start)
            cleaned_phone = ""
            for i, char in enumerate(phone):
                if char.isdigit():
                    cleaned_phone += char
                elif char == '+' and i == 0:
                    cleaned_phone += char
            
            # Update if user entered non-numeric characters
            if cleaned_phone != phone:
                st.session_state.reg_phone = cleaned_phone
                st.rerun()
        
        with col_phone_msg:
            if phone:
                if not validate_indian_phone_number(phone):
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">Enter A Valid Phone Number!</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_phone_valid = False
                else:
                    st.markdown(
                        '<p style="color: green; font-size: 12px; margin-top: 30px;">✓ Valid Phone Number</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_phone_valid = True
        
        # Password with strength indicator - inline
        col_pwd_input, col_pwd_msg = st.columns([3, 1])
        with col_pwd_input:
            password = st.text_input(
                "Password*", 
                placeholder="Create a strong password", 
                type="password", 
                key="reg_password"
            )
        with col_pwd_msg:
            if password:
                level, color, feedback = get_password_strength(password)
                st.markdown(
                    f'<p style="color: {color}; font-size: 12px; margin-top: 30px;"><strong>{level}</strong></p>', 
                    unsafe_allow_html=True
                )
        
        # Show password feedback below if needed
        if password:
            level, color, feedback = get_password_strength(password)
            if feedback:
                st.markdown(
                    f'<p style="color: orange; font-size: 11px; margin-top: -10px;">Missing: {", ".join(feedback)}</p>', 
                    unsafe_allow_html=True
                )
        
        # Confirm password with match indicator - inline
        col_cpwd_input, col_cpwd_msg = st.columns([3, 1])
        with col_cpwd_input:
            confirm_password = st.text_input(
                "Confirm Password*", 
                placeholder="Re-enter your password", 
                type="password", 
                key="reg_confirm_password"
            )
        with col_cpwd_msg:
            if confirm_password:
                if password == confirm_password:
                    st.markdown(
                        '<p style="color: green; font-size: 12px; margin-top: 30px;">✓ Passwords Match</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_pwd_match = True
                else:
                    st.markdown(
                        '<p style="color: red; font-size: 12px; margin-top: 30px;">❌ Entered Passwords Do NOT match</p>', 
                        unsafe_allow_html=True
                    )
                    st.session_state.reg_pwd_match = False
        
        # Security Question
        st.markdown("**Security Question** (for password recovery)")
        security_question = st.selectbox(
            "Select a security question*",
            options=settings.SECURITY_QUESTIONS,
            key="reg_security_question"
        )
        security_answer = st.text_input(
            "Answer*", 
            placeholder="Enter your answer",
            key="reg_security_answer"
        )
        
        st.markdown("---")
        
        # Buttons
        col_submit, col_back = st.columns(2)
        
        with col_submit:
            submit_button = st.button("Register", use_container_width=True, type="primary")
        
        with col_back:
            back_button = st.button("Back to Login", use_container_width=True)
        
        if submit_button:
            # Final validation
            errors = []
            
            if not full_name:
                errors.append("Full name is required")
            
            if not username or not st.session_state.reg_username_valid:
                errors.append("Please enter a valid and available username")
            
            if not email or not st.session_state.reg_email_valid:
                errors.append("Please enter a valid and available email")
            
            if not phone or not st.session_state.reg_phone_valid:
                errors.append("Please enter a valid Indian phone number")
            
            if not password:
                errors.append("Password is required")
            elif get_password_strength(password)[0] in ["Very Weak", "Weak"]:
                errors.append("Password is too weak")
            
            if not st.session_state.reg_pwd_match or password != confirm_password:
                errors.append("Passwords do not match")
            
            if not security_answer:
                errors.append("Security answer is required")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Register user
                success, message, user_id = AuthService.register_user(
                    username=username,
                    email=email,
                    phone=phone,
                    password=password,
                    user_type=user_type.lower(),
                    security_question=security_question,
                    security_answer=security_answer,
                    full_name=full_name
                )
                
                if success:
                    st.balloons()
                    st.toast('Welcome to MediMitra!', icon='🏥')
                    st.toast('Registration successful!', icon='✅')
                    st.success("Redirecting to login page...")
                    import time
                    time.sleep(2)
                    st.session_state.page = "login"
                    # Clear validation states
                    st.session_state.reg_email_valid = True
                    st.session_state.reg_phone_valid = True
                    st.session_state.reg_pwd_match = True
                    st.session_state.reg_username_valid = True
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        if back_button:
            st.session_state.page = "login"
            # Clear validation states
            st.session_state.reg_email_valid = True
            st.session_state.reg_phone_valid = True
            st.session_state.reg_pwd_match = True
            st.session_state.reg_username_valid = True
            st.rerun()
