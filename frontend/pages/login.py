import streamlit as st
from backend.auth_service import AuthService

def render_login_page():
    """Render the login page"""
    
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header
        st.markdown("""
            <div style='text-align: center; padding: 20px;'>
                <h1 style='color: #1E88E5; margin-bottom: 10px;'>🏥 MediMitra</h1>
                <p style='color: #666; font-size: 18px;'>Hi! I am MediMitra. Allow me to assist you by logging in.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            user_type = st.radio(
                "I am a:",
                options=["Patient", "Pharmacist"],
                horizontal=True
            )
            
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, message, user_data = AuthService.login_user(
                        username, 
                        password, 
                        user_type.lower()
                    )
                    
                    if success:
                        # Store user data in session
                        st.session_state.logged_in = True
                        st.session_state.user = user_data
                        st.session_state.user_type = user_type.lower()
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Links
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔑 Forgot Password?", use_container_width=True):
                st.session_state.page = "reset_password"
                st.rerun()
        
        with col_b:
            if st.button("📝 Register", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
