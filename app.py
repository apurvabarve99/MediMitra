import streamlit as st

st.set_page_config(
    page_title="MediMitra - Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== LOADING SPINNER FOR INITIAL APP LOAD =====
if 'app_fully_loaded' not in st.session_state:
    # Show loading screen
    loading_container = st.empty()
    
    with loading_container.container():
        st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh;">
                <h1>🏥 MediMitra</h1>
                <p style="font-size: 18px; color: #666;">Healthcare Assistant</p>
            </div>
        """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Import heavy modules with progress updates
        status_text.text("⏳ Loading authentication services...")
        progress_bar.progress(10)
        from frontend.pages.login import render_login_page
        from frontend.pages.register import render_register_page
        from frontend.pages.reset_password import render_reset_password_page
        
        status_text.text("⏳ Loading dashboard modules...")
        progress_bar.progress(30)
        from frontend.pages.patient_dashboard import render_patient_dashboard
        from frontend.pages.pharmacist_dashboard import render_pharmacist_dashboard
        
        status_text.text("⏳ Initializing OCR service...")
        progress_bar.progress(50)
        from backend.ocr_service import ocr_service
        
        status_text.text("⏳ Loading medical AI models (this may take 20-30 seconds)...")
        progress_bar.progress(60)
        from backend.rag_service import rag_service
        
        progress_bar.progress(80)
        from backend.llm_service import llm_service
        
        status_text.text("⏳ Finalizing setup...")
        progress_bar.progress(95)
        
        # Mark as loaded
        st.session_state.app_fully_loaded = True
        
        status_text.text("✅ MediMitra is ready!")
        progress_bar.progress(100)
    
    # Clear loading screen and rerun
    loading_container.empty()
    st.rerun()

else:
    # App already loaded - import directly
    from frontend.pages.login import render_login_page
    from frontend.pages.register import render_register_page
    from frontend.pages.reset_password import render_reset_password_page
    from frontend.pages.patient_dashboard import render_patient_dashboard
    from frontend.pages.pharmacist_dashboard import render_pharmacist_dashboard
    from backend.ocr_service import ocr_service


# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'login'

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


# === SMART BACKGROUND OCR LOADING ===
# Start OCR loading when user is on login/register page
if not st.session_state.logged_in and st.session_state.page in ['login', 'register']:
    if 'ocr_loading_started' not in st.session_state:
        st.session_state.ocr_loading_started = True


# Routing
def main():
    if st.session_state.logged_in:
        # User is logged in - show appropriate dashboard
        if st.session_state.user_type == 'patient':
            render_patient_dashboard()
        elif st.session_state.user_type == 'pharmacist':
            render_pharmacist_dashboard()
    else:
        # User not logged in - show auth pages
        page = st.session_state.page
        
        if page == 'login':
            render_login_page()
        elif page == 'register':
            render_register_page()
        elif page == 'reset_password':
            render_reset_password_page()


if __name__ == "__main__":
    main()
