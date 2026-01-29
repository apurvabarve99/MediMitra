import streamlit as st
from datetime import datetime, timedelta
from backend.appointment_service import appointment_service
from backend.rag_service import rag_service
from backend.llm_service import llm_service
from backend.date_parser import DateTimeParser
from backend.ocr_service import ocr_service
from utils.qr_generator import generate_qr_code
import uuid
import logging


logger = logging.getLogger(__name__)


def render_patient_dashboard():
    """Display patient dashboard with inline chat interface"""
    
    # Custom CSS
    st.markdown("""
        <style>
        .chat-container {
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .bot-message {
            background-color: #e3f2fd;
            padding: 12px 16px;
            border-radius: 15px 15px 15px 0;
            margin: 10px 0;
            max-width: 80%;
            float: left;
            clear: both;
        }
        .user-message {
            background-color: #c8e6c9;
            padding: 12px 16px;
            border-radius: 15px 15px 0 15px;
            margin: 10px 0;
            max-width: 80%;
            float: right;
            clear: both;
        }
        .timestamp {
            font-size: 10px;
            color: #757575;
            margin-top: 5px;
        }
        div.stButton > button {
            background-color: transparent !important;
            border: 2px solid #1f77b4 !important;
            color: #1f77b4 !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button:hover {
            background-color: #1f77b4 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session
    initialize_session()
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"## 🏥 Welcome, {st.session_state.user.get('full_name', 'Patient')}!")
    with col2:
        if st.button("Logout", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Check for timeout (10 minutes)
    if datetime.now() - st.session_state.last_activity > timedelta(minutes=10):
        st.warning("⏱️ Session expired due to inactivity. Please refresh to start over.")
        if st.button("Start New Session"):
            reset_conversation()
            st.rerun()
        return
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        # Initial greeting
        if len(st.session_state.chat_messages) == 0:
            st.markdown(f"""
                <div class="bot-message">
                    <strong>🤖 MediMitra</strong><br>
                    Hello! I'm MediMitra, your healthcare assistant. How can I help you today?
                    <div class="timestamp">{datetime.now().strftime('%H:%M')}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Display chat history
        for msg in st.session_state.chat_messages:
            if msg['role'] == 'assistant':
                st.markdown(f"""
                    <div class="bot-message">
                        <strong>🤖 MediMitra</strong><br>
                        {msg['content']}
                        <div class="timestamp">{msg['timestamp']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display QR code if present
                if 'qr_code' in msg:
                    st.markdown(f"<img src='{msg['qr_code']}' width='250'>", unsafe_allow_html=True)
                
                # Display prescription upload if needed
                if msg.get('show_upload'):
                    # Check if OCR is ready
                    if not ocr_service.is_ready():
                        st.warning("⏳ OCR service is still loading. Please wait...")
                        if st.button("🔄 Refresh", key=f"refresh_ocr_{msg['timestamp']}"):
                            st.rerun()
                    else:
                        # Create unique key using timestamp to prevent duplicate processing
                        file_key = f"upload_{msg['timestamp']}"
                        
                        uploaded_file = st.file_uploader(
                            "Upload Prescription", 
                            type=['jpg', 'jpeg', 'png'],
                            key=file_key
                        )
                        
                        # Only process if file is new and not already processed
                        if uploaded_file is not None:
                            # Create file identifier
                            file_id = f"{uploaded_file.name}_{uploaded_file.size}_{msg['timestamp']}"
                            
                            # Check if this file was already processed
                            if st.session_state.last_uploaded_file != file_id:
                                st.session_state.last_uploaded_file = file_id
                                st.session_state.upload_processed = False
                            
                            # Process only once
                            if not st.session_state.upload_processed:
                                st.session_state.upload_processed = True
                                handle_prescription_upload(uploaded_file)
            else:
                st.markdown(f"""
                    <div class="user-message">
                        <strong>You</strong><br>
                        {msg['content']}
                        <div class="timestamp">{msg['timestamp']}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Show initial options
    if st.session_state.show_main_menu:
        st.markdown("### Choose an option:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📅 Book Appointment", key="opt_book", use_container_width=True):
                handle_main_menu_selection("book_appointment")
        
        with col2:
            if st.button("📋 Get Instructions", key="opt_instructions", use_container_width=True):
                handle_main_menu_selection("get_instructions")
        
        with col3:
            if st.button("👤 Manage Profile", key="opt_profile", use_container_width=True):
                handle_main_menu_selection("manage_profile")
    
    # Show specialist buttons
    if st.session_state.show_specialist_buttons:
        st.markdown("### Select your preferred specialization:")
        specialists = st.session_state.booking_data.get('specialists', [])
        
        cols = st.columns(min(len(specialists), 4))
        for idx, spec in enumerate(specialists):
            col_idx = idx % 4
            with cols[col_idx]:
                if st.button(spec, key=f"spec_{spec}", use_container_width=True):
                    handle_specialist_selection(spec)
    
    # Chat input
    if st.session_state.booking_complete:
        chat_placeholder = "Need anything else? (Type 'home' to return to menu)"
    elif not st.session_state.chat_enabled:
        chat_placeholder = "Select an option above to start..."
    else:
        chat_placeholder = "Type your message..."
    
    user_input = st.chat_input(
        chat_placeholder, 
        disabled=not st.session_state.chat_enabled and not st.session_state.booking_complete
    )
    
    if user_input:
        st.session_state.last_activity = datetime.now()
        timestamp = datetime.now().strftime('%H:%M')
        
        # Add user message instantly
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': timestamp
        })
        
        # Process input
        process_user_input(user_input)


def initialize_session():
    """Initialize session state"""
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'current_flow' not in st.session_state:
        st.session_state.current_flow = 'initial'
    if 'booking_data' not in st.session_state:
        st.session_state.booking_data = {}
    if 'show_main_menu' not in st.session_state:
        st.session_state.show_main_menu = True
    if 'chat_enabled' not in st.session_state:
        st.session_state.chat_enabled = False
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
    if 'booking_complete' not in st.session_state:
        st.session_state.booking_complete = False
    if 'show_specialist_buttons' not in st.session_state:
        st.session_state.show_specialist_buttons = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'upload_processed' not in st.session_state:
        st.session_state.upload_processed = False
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None


def add_message(role: str, content: str, **kwargs):
    """Add message to chat"""
    st.session_state.chat_messages.append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().strftime('%H:%M'),
        **kwargs
    })


def reset_conversation():
    """Reset all chat session variables"""
    st.session_state.chat_messages = []
    st.session_state.current_flow = 'initial'
    st.session_state.booking_data = {}
    st.session_state.show_main_menu = True
    st.session_state.chat_enabled = False
    st.session_state.last_activity = datetime.now()
    st.session_state.booking_complete = False
    st.session_state.show_specialist_buttons = False
    st.session_state.upload_processed = False
    st.session_state.last_uploaded_file = None


def handle_main_menu_selection(option):
    """Handle main menu button clicks"""
       
    if option == "book_appointment":
        add_message('user', 'Book an Appointment')
        add_message('assistant', 
            "Great! Let's book an appointment. Please describe patient's symptoms or health concerns.")
        
        st.session_state.current_flow = 'awaiting_symptoms'
        st.session_state.show_main_menu = False
        st.session_state.chat_enabled = True
        st.rerun()
    
    elif option == "get_instructions":
        add_message('user', 'Get Patient Instructions')
        add_message('assistant', 
            "Please upload your prescription image, and I'll provide detailed instructions for your medicines.",
            show_upload=True)
        
        st.session_state.current_flow = 'awaiting_prescription'
        st.session_state.show_main_menu = False
        st.session_state.chat_enabled = False
        st.session_state.upload_processed = False  # Reset upload flag
        st.session_state.last_uploaded_file = None
        st.rerun()
    
    elif option == "manage_profile":
        add_message('user', 'Manage Profile')
        user = st.session_state.user
        profile_info = f"""**Your Profile:**

👤 **Name:** {user.get('full_name', 'N/A')}
📧 **Email:** {user.get('email', 'N/A')}
📱 **Phone:** {user.get('phone', 'N/A')}
🩸 **Blood Group:** {user.get('blood_group', 'N/A')}

To update your profile, please contact support.
Type 'home' to return to the main menu."""
        
        add_message('assistant', profile_info)
        st.session_state.current_flow = 'profile_view'
        st.session_state.show_main_menu = False
        st.session_state.chat_enabled = True
        st.rerun()


def process_user_input(user_input: str):
    """Process user input based on current flow (UPDATED WITH INTENT DETECTION)"""
    
    # Check for home/reset intent
    if user_input.lower() in ['home', 'menu', 'back', 'start over', 'reset']:
        add_message('assistant', "Returning to main menu...")
        reset_conversation()
        st.rerun()
        return
    
    # CHECK FOR BOOKING INTENT DURING GENERAL CONVERSATION
    booking_keywords = ['book appointment', 'schedule appointment', 'make appointment', 
                       'book an appointment', 'i want to book', 'need appointment',
                       'want appointment']
    
    if any(keyword in user_input.lower() for keyword in booking_keywords):
        # Check if not already in booking flow
        if st.session_state.current_flow not in ['awaiting_symptoms', 'awaiting_date', 
                                                   'awaiting_time', 'awaiting_doctor_confirmation',
                                                   'awaiting_doctor_selection', 'awaiting_final_confirmation',
                                                   'awaiting_patient_name', 'awaiting_patient_contact']:
            # Trigger booking flow
            add_message('assistant', 
                "Great! Let's book an appointment for you. Please describe the patient's symptoms or health concerns.")
            
            st.session_state.current_flow = 'awaiting_symptoms'
            st.session_state.show_main_menu = False
            st.session_state.chat_enabled = True
            st.rerun()
            return
    
    flow = st.session_state.current_flow
    data = st.session_state.booking_data
    
    # Appointment booking flow
    if flow == 'awaiting_symptoms':
        handle_symptoms_input(user_input)
    
    elif flow == 'awaiting_alternative_specialist':
        handle_alternative_specialist(user_input)
    
    elif flow == 'awaiting_date':
        handle_date_input(user_input)
    
    elif flow == 'awaiting_time':
        handle_time_input(user_input)
    
    elif flow == 'awaiting_doctor_confirmation':
        handle_doctor_confirmation(user_input)
    
    elif flow == 'awaiting_doctor_selection':
        handle_doctor_selection(user_input)
    
    elif flow == 'awaiting_final_confirmation':
        handle_final_confirmation(user_input)
    
    elif flow == 'awaiting_patient_name':
        data['patient_name'] = user_input
        add_message('assistant', "Please provide contact number for appointment.")
        st.session_state.current_flow = 'awaiting_patient_contact'
        st.rerun()
    
    elif flow == 'awaiting_patient_contact':
        data['patient_contact'] = user_input
        finalize_booking()
    
    else:
        # General conversation with guardrails
        response = llm_service.generate_conversational_response(
            user_input,
            {'current_state': flow, 'history': [m['content'] for m in st.session_state.chat_messages[-6:]]}
        )
        if response:
            add_message('assistant', response)
        st.rerun()


def handle_symptoms_input(symptoms: str):
    """Handle symptom analysis using RAG"""
    data = st.session_state.booking_data
    data['symptoms'] = symptoms
    
    with st.spinner("🔍 Analyzing your symptoms with AI..."):
        # RAG: Retrieve specialists based on symptoms
        specialists = rag_service.get_specialists_for_symptoms(symptoms)
    
    data['specialists'] = specialists
    
    # If no specialists found, default to General Medicine
    if not specialists or len(specialists) == 0:
        specialists = ['General Medicine']
        data['specialists'] = specialists
    
    bot_response = "Based on your symptoms, we have provided options for specialists.\n\n"
    bot_response += "Please select your preferred specialization doctor from below:"
    
    add_message('assistant', bot_response)
    
    st.session_state.show_specialist_buttons = True
    st.session_state.chat_enabled = False
    st.rerun()


def handle_specialist_selection(specialization: str):
    """Handle specialist selection"""
    data = st.session_state.booking_data
    
    # Add user selection to chat
    add_message('user', specialization)
    data['selected_specialist'] = specialization
    
    # Hide specialist buttons
    st.session_state.show_specialist_buttons = False
    
    # Get doctors for specialty
    doctors = appointment_service.get_doctors_by_specialization(specialization)
    
    if doctors and len(doctors) > 0:
        # Store all doctors but DON'T assign yet
        data['all_doctors'] = doctors
        
        bot_response = f"Great! We have **{len(doctors)} {specialization}** doctor(s) available.\n\n"
        bot_response += "When would you like to schedule your appointment? (e.g., tomorrow, Jan 26, next Monday)"
        
        add_message('assistant', bot_response)
        st.session_state.current_flow = 'awaiting_date'
        st.session_state.chat_enabled = True
    else:
        # No doctors found
        add_message('assistant', 
            f"⚠️ Unfortunately, no **{specialization}** doctors are available in our system right now.\n\n"
            f"Would you like to:\n"
            f"1. Consult a **General Medicine** doctor instead? (They can provide initial assessment)\n"
            f"2. Return to main menu? (Type 'home')\n\n"
            f"Please type 'general medicine' or 'home'.")
        
        st.session_state.current_flow = 'awaiting_alternative_specialist'
        st.session_state.chat_enabled = True
    
    st.rerun()


def handle_alternative_specialist(user_input: str):
    """Handle when user needs alternative after no doctors found"""
    user_choice = user_input.lower().strip()
    
    if 'general' in user_choice or 'gp' in user_choice:
        # User chose General Medicine as alternative
        data = st.session_state.booking_data
        data['selected_specialist'] = 'General Medicine'
        
        # Get General Medicine doctors
        doctors = appointment_service.get_doctors_by_specialization('General Medicine')
        
        if doctors and len(doctors) > 0:
            data['doctor'] = doctors[0]
            data['all_doctors'] = doctors
            
            bot_response = f"Perfect! I've assigned you to **{data['doctor']['full_name']}** (General Medicine).\n\n"
            bot_response += "When would you like to schedule your appointment? (e.g., tomorrow, Jan 26, next Monday)"
            
            add_message('assistant', bot_response)
            st.session_state.current_flow = 'awaiting_date'
            st.session_state.chat_enabled = True
        else:
            add_message('assistant', "❌ System error: No doctors available. Please contact support.")
            reset_conversation()
    
    elif 'home' in user_choice or 'menu' in user_choice:
        add_message('assistant', "Returning to main menu...")
        reset_conversation()
    
    else:
        add_message('assistant', "Please type 'general medicine' to consult a GP, or 'home' to return to menu.")
    
    st.rerun()


def handle_date_input(user_input: str):
    """Handle date selection"""
    parsed_date = DateTimeParser.parse_date(user_input)
    
    if not parsed_date:
        add_message('assistant', 
            "I couldn't understand that date. Please provide a date like:\n"
            "- 'tomorrow'\n- 'Jan 26' or 'January 26'\n- 'next Monday'\n- '26-01-2026'")
        st.rerun()
        return
    
    if parsed_date < datetime.now().date():
        add_message('assistant', "That date has already passed. Please choose a future date.")
        st.rerun()
        return
    
    st.session_state.booking_data['appointment_date'] = parsed_date
    
    # Format: "Wednesday, 29th January 2026" instead of just "Wednesday"
    bot_response = f"Perfect! {parsed_date.strftime('%A, %d %B %Y')} it is.\n\n"
    bot_response += "Regular consultation timings are from 9 AM to 9 PM. "
    bot_response += "What time would work best for you? (e.g., '10:30 AM', 'five thirty pm', '2:00 PM')"
    
    add_message('assistant', bot_response)
    st.session_state.current_flow = 'awaiting_time'
    st.rerun()


def handle_time_input(user_input: str):
    """Handle time selection"""
    parsed_time = DateTimeParser.parse_time(user_input)
    
    if not parsed_time:
        add_message('assistant', 
            "I couldn't understand that time. Please provide time like:\n"
            "- '10:30', '2:00 PM'\n- 'five thirty pm'\n- '14:00'")
        st.rerun()
        return
    
    if not appointment_service.is_valid_appointment_time(parsed_time):
        add_message('assistant', 
            "Sorry, appointments are only available between 9:00 AM and 9:00 PM. Please choose another time.")
        st.rerun()
        return
    
    data = st.session_state.booking_data
    data['appointment_time'] = parsed_time
    
    # NOW assign the first available doctor
    data['doctor'] = data['all_doctors'][0]
    
    # Show appointment summary with doctor details
    bot_response = f"""Perfect! Here's your appointment summary:

👨‍⚕️ **Doctor:** {data['doctor']['full_name']}
🎓 **Qualification:** {data['doctor'].get('qualification', 'N/A')}
🏥 **Specialization:** {data['selected_specialist']}
📅 **Date:** {data['appointment_date'].strftime('%A, %d %B %Y')}
🕐 **Time:** {DateTimeParser.format_time_friendly(parsed_time)}
💰 **Consultation Fee:** ₹{data['doctor']['consultation_fee']}

Type **'confirm'** to proceed with booking or **'change doctor'** to view other doctors."""
    
    add_message('assistant', bot_response)
    st.session_state.current_flow = 'awaiting_doctor_confirmation'
    st.rerun()


def handle_doctor_confirmation(user_input: str):
    """Handle doctor confirmation or change request"""
    user_choice = user_input.lower().strip()
    data = st.session_state.booking_data
    
    if 'confirm' in user_choice or user_choice in ['yes', 'ok', 'proceed']:
        # User confirmed the doctor - ask for patient name
        add_message('assistant', "Great! Please provide the patient's full name to confirm the booking.")
        st.session_state.current_flow = 'awaiting_patient_name'
        st.rerun()
    
    elif 'change' in user_choice or 'other' in user_choice or 'different' in user_choice:
        # User wants to see other doctors
        doctors = data['all_doctors']
        
        if len(doctors) <= 1:
            add_message('assistant', 
                f"Sorry, only one **{data['selected_specialist']}** doctor is available at the moment.\n\n"
                "Type 'confirm' to proceed with this doctor or 'home' to return to main menu.")
            st.rerun()
            return
        
        # Show all available doctors
        doctors_list = f"**Available {data['selected_specialist']} Doctors:**\n\n"
        
        for idx, doc in enumerate(doctors, 1):
            doctors_list += f"{idx}. **{doc['full_name']}**\n"
            doctors_list += f"   🎓 {doc.get('qualification', 'N/A')}\n"
            doctors_list += f"   💰 ₹{doc['consultation_fee']}\n"
            doctors_list += f"   📅 Available: {doc.get('available_days', 'All days')}\n\n"
        
        doctors_list += "Please type the **number** of your preferred doctor (e.g., '1', '2', '3')"
        
        add_message('assistant', doctors_list)
        st.session_state.current_flow = 'awaiting_doctor_selection'
        st.rerun()
    
    else:
        add_message('assistant', "Please type 'confirm' to proceed or 'change doctor' to view other options.")
        st.rerun()


def handle_doctor_selection(user_input: str):
    """Handle doctor selection from numbered list"""
    data = st.session_state.booking_data
    doctors = data['all_doctors']
    
    try:
        # Try to parse the number
        selection = int(user_input.strip())
        
        if 1 <= selection <= len(doctors):
            # Valid selection
            selected_doctor = doctors[selection - 1]
            data['doctor'] = selected_doctor
            
            # Show updated appointment summary
            bot_response = f"""Perfect! You've selected:

👨‍⚕️ **Doctor:** {selected_doctor['full_name']}
🎓 **Qualification:** {selected_doctor.get('qualification', 'N/A')}
🏥 **Specialization:** {data['selected_specialist']}
📅 **Date:** {data['appointment_date'].strftime('%A, %d %B %Y')}
🕐 **Time:** {DateTimeParser.format_time_friendly(data['appointment_time'])}
💰 **Consultation Fee:** ₹{selected_doctor['consultation_fee']}

Type **'confirm'** to proceed with booking."""
            
            add_message('assistant', bot_response)
            st.session_state.current_flow = 'awaiting_final_confirmation'
            st.rerun()
        else:
            add_message('assistant', 
                f"Invalid selection. Please choose a number between 1 and {len(doctors)}.")
            st.rerun()
    
    except ValueError:
        add_message('assistant', 
            "Please enter a valid number (e.g., '1', '2', '3') to select a doctor.")
        st.rerun()


def handle_final_confirmation(user_input: str):
    """Handle final confirmation after doctor selection"""
    user_choice = user_input.lower().strip()
    
    if user_choice in ['confirm', 'yes', 'ok', 'proceed']:
        add_message('assistant', "Great! Please provide the patient's full name to confirm the booking.")
        st.session_state.current_flow = 'awaiting_patient_name'
        st.rerun()
    else:
        add_message('assistant', "Please type 'confirm' to proceed with booking or 'home' to return to main menu.")
        st.rerun()


def finalize_booking():
    """Finalize and create appointment"""
    data = st.session_state.booking_data
    
    with st.spinner("📝 Booking your appointment..."):
        success, message, appt_id = appointment_service.create_appointment(
            patient_id=st.session_state.user.get('patient_id', 1),
            doctor_id=data['doctor']['doctor_id'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            symptoms=data['symptoms'],
            patient_name=data.get('patient_name', st.session_state.user.get('full_name')),
            patient_contact=data.get('patient_contact', st.session_state.user.get('phone'))
        )
    
    if success:
        # Generate QR code
        qr_data = f"Appointment ID: {appt_id}\nPatient: {data.get('patient_name')}\n" \
                 f"Doctor: {data['doctor']['full_name']}\n" \
                 f"Date: {data['appointment_date']}\nTime: {data['appointment_time']}"
        qr_code = generate_qr_code(qr_data)
        
        bot_response = f"""🎉 **Appointment Booked Successfully!**

**Appointment ID:** {appt_id}
**Patient Name:** {data.get('patient_name', st.session_state.user.get('full_name'))}
**Doctor:** {data['doctor']['full_name']}
**Date:** {data['appointment_date'].strftime('%A, %d %B %Y')}
**Time:** {DateTimeParser.format_time_friendly(data['appointment_time'])}
**Fee:** ₹{data['doctor']['consultation_fee']}

📧 A confirmation SMS will be sent to your registered number.

Please show this QR code at the hospital reception:"""
        
        add_message('assistant', bot_response, qr_code=qr_code)
        add_message('assistant', "Is there anything else I can help you with? (Type 'home' for menu)")
        
        st.session_state.booking_complete = True
        st.session_state.chat_enabled = True
        st.session_state.current_flow = 'complete'
    else:
        add_message('assistant', f"❌ Booking failed: {message}. Please try again.")
        reset_conversation()
    
    st.rerun()


def handle_prescription_upload(uploaded_file):
    """Handle prescription image upload"""
    
    # Add user message
    add_message('user', "[Uploaded prescription image]")
    
    # Extract text
    with st.spinner("🔍 Extracting text from prescription..."):
        try:
            image_bytes = uploaded_file.read()
            extracted_text = ocr_service.extract_text_from_image(image_bytes)
        except Exception as e:
            logger.error(f"Upload processing error: {e}")
            extracted_text = None
    
    # Handle extraction failure
    if not extracted_text:
        error_msg = """❌ Could not extract text from the image.

**Possible reasons:**
• Image quality is too low
• Text is blurry or too small
• Unsupported format

**What to do:**
• Upload a clearer image
• Ensure good lighting
• Type 'home' to return to menu"""
        
        add_message('assistant', error_msg)
        st.session_state.chat_enabled = True
        st.session_state.current_flow = 'initial'
        return
    
    # Extract medicine items (returns list of strings)
    prescription_items = ocr_service.extract_prescription_items(extracted_text)
    
    if not prescription_items:
        error_msg = """❌ No medicines found in prescription.

**Please ensure:**
• Prescription contains medicine names
• Text includes dosages (mg, ml, tablet)
• Image is right-side up

Type 'home' for menu or upload another image."""
        
        add_message('assistant', error_msg)
        st.session_state.chat_enabled = True
        st.session_state.current_flow = 'initial'
        return
    
    # Success - show extracted items
    extracted_list = "\n".join([f"• {item}" for item in prescription_items])
    add_message('assistant', f"✅ Found {len(prescription_items)} medicine(s) in prescription:\n\n{extracted_list}")
    
    # Get instructions from LLM
    with st.spinner("📋 Generating instructions with AI..."):
        try:
            # Pass list of strings to LLM
            instructions = llm_service.extract_medicine_instructions(prescription_items)
        except Exception as e:
            logger.error(f"LLM instruction error: {e}", exc_info=True)
            instructions = None
    
    if instructions:
        formatted_msg = f"""**📋 Medicine Instructions**

{instructions}

---

💡 **Important Reminders:**
- Take medicines at prescribed times
- Complete the full course
- Store properly as directed
- Contact doctor if side effects occur

Type 'home' to return to menu."""
        
        add_message('assistant', formatted_msg)
    else:
        fallback_msg = """⚠️ Extracted medicines but couldn't generate detailed instructions.

**Next steps:**
• Consult your pharmacist for dosage details
• Follow doctor's verbal instructions
• Read medicine package inserts

Type 'home' for main menu."""
        
        add_message('assistant', fallback_msg)
    
    # Enable chat for next interaction
    st.session_state.chat_enabled = True
    st.session_state.current_flow = 'instruction_complete'

