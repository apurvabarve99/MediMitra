import streamlit as st
from backend.auth_service import AuthService
from utils.validators import validate_password, validate_password_match
from config.settings import settings

def render_reset_password_page():
    """Render the password reset page"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 20px;'>
                <h1 style='color: #1E88E5;'>Reset Password</h1>
                <p style='color: #666;'>Answer your security question to reset your password</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Step 1: Verify identity
        if 'reset_verified' not in st.session_state:
            st.session_state.reset_verified = False
            st.session_state.reset_username = None
        
        if not st.session_state.reset_verified:
            with st.form("verify_identity_form"):
                st.markdown("### Step 1: Verify Your Identity")
                
                username = st.text_input("Username", placeholder="Enter your username")
                
                security_question = st.selectbox(
                    "Select your security question:",
                    options=settings.SECURITY_QUESTIONS
                )
                
                security_answer = st.text_input(
                    "Answer",
                    placeholder="Enter your security answer"
                )
                
                verify_button = st.form_submit_button("Verify", use_container_width=True)
                
                if verify_button:
                    if not username or not security_answer:
                        st.error("Please fill in all fields")
                    else:
                        success, message = AuthService.verify_security_answer(
                            username, security_question, security_answer
                        )
                        
                        if success:
                            st.session_state.reset_verified = True
                            st.session_state.reset_username = username
                            st.success("Identity verified! Please set your new password.")
                            st.rerun()
                        else:
                            st.error(message)
        
        # Step 2: Reset password
        else:
            with st.form("reset_password_form"):
                st.markdown(f"### Step 2: Set New Password")
                st.info(f"Resetting password for: **{st.session_state.reset_username}**")
                
                new_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter your new password"
                )
                
                if 'password_error' in st.session_state:
                    st.error(st.session_state.password_error)
                
                confirm_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Re-enter your new password"
                )
                
                if 'confirm_error' in st.session_state:
                    st.error(st.session_state.confirm_error)
                
                reset_button = st.form_submit_button("Reset Password", use_container_width=True)
                
                if reset_button:
                    # Clear previous errors
                    if 'password_error' in st.session_state:
                        del st.session_state.password_error
                    if 'confirm_error' in st.session_state:
                        del st.session_state.confirm_error
                    
                    # Validate password
                    is_valid, error_msg = validate_password(new_password)
                    if not is_valid:
                        st.session_state.password_error = error_msg
                        st.rerun()
                    
                    # Validate password match
                    is_valid, error_msg = validate_password_match(new_password, confirm_password)
                    if not is_valid:
                        st.session_state.confirm_error = error_msg
                        st.rerun()
                    
                    # Reset password
                    success, message = AuthService.reset_password(
                        st.session_state.reset_username,
                        new_password
                    )
                    
                    if success:
                        st.success("Password reset successful! Redirecting to login...")
                        # Clean up session
                        st.session_state.reset_verified = False
                        st.session_state.reset_username = None
                        import time
                        time.sleep(2)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(message)
        
        # Back to login
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.reset_verified = False
            st.session_state.reset_username = None
            st.session_state.page = "login"
            st.rerun()
