import streamlit as st
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from backend.pharmacist_llm_service import pharmacist_llm_service
from backend.finance_service import finance_service
from backend.ocr_service import ocr_service
from backend.report_service import report_service
from backend.db_connection import DatabaseConnection
import pandas as pd
import uuid
import logging


logger = logging.getLogger(__name__)



def render_pharmacist_dashboard():
    """Display pharmacist dashboard with chat interface"""
    
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
        .stDataFrame {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session
    initialize_session()
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"## 💊 Pharmacist Dashboard - Welcome, {st.session_state.user.get('full_name', 'Pharmacist')}!")
    with col2:
        if st.button("Logout", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Check for timeout (30 minutes)
    if datetime.now() - st.session_state.last_activity > timedelta(minutes=30):
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
                    <strong>🤖 Pharmacy Assistant</strong><br>
                    Hello! I can help you with Smart Data Entry, Inventory Management, and Reports. What would you like to do today?
                    <div class="timestamp">{datetime.now().strftime('%H:%M')}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Display chat history
        for idx, msg in enumerate(st.session_state.chat_messages):
            if msg['role'] == 'assistant':
                st.markdown(f"""
                    <div class="bot-message">
                        <strong>🤖 Assistant</strong><br>
                        {msg['content']}
                        <div class="timestamp">{msg['timestamp']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display editable table if present
                if 'editable_table' in msg:
                    st.markdown("#### 📊 Extracted Data (Click cells to edit)")
                    
                    # Use data_editor for editable table
                    edited_df = st.data_editor(
                        msg['editable_table'],
                        width="stretch",
                        num_rows="dynamic",
                        key=msg.get('table_key', f"table_{idx}"),
                        column_config=msg.get('column_config', {})
                    )
                    
                    # Update the pending data with edited dataframe
                    if st.session_state.pending_data and st.session_state.pending_data.get('table_key') == msg.get('table_key'):
                        st.session_state.pending_data['edited_dataframe'] = edited_df
                
                # Display regular table if present (non-editable)
                elif 'table' in msg:
                    st.dataframe(msg['table'], width="stretch")
                
                # Display download button if present
                if 'download' in msg:
                    st.download_button(
                        label=msg['download']['label'],
                        data=msg['download']['data'],
                        file_name=msg['download']['filename'],
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key=msg['download']['key']
                    )
            
            else:
                st.markdown(f"""
                    <div class="user-message">
                        <strong>You</strong><br>
                        {msg['content']}
                        <div class="timestamp">{msg['timestamp']}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Show main menu buttons
    if st.session_state.show_main_menu:
        st.markdown("### Choose an option:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Smart Data Entry", key="opt_data_entry"):
                handle_main_menu_selection("data_entry")
                st.rerun()
        
        with col2:
            if st.button("📦 Inventory Management", key="opt_inventory"):
                handle_main_menu_selection("inventory")
                st.rerun()
        
        with col3:
            if st.button("📊 Dashboard & Reports", key="opt_dashboard"):
                handle_main_menu_selection("dashboard")
                st.rerun()
    
    # Show report selection buttons (NEW - DASHBOARD MODE)
    if st.session_state.show_report_menu:
        st.markdown("### Select Report Type:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📅 Appointments Report", key="rep_appointments"):
                handle_report_selection("appointments")
                st.rerun()
            
            if st.button("💰 Bank Statement Report", key="rep_bank"):
                handle_report_selection("bank")
                st.rerun()
        
        with col2:
            if st.button("📦 Supplier Invoice Report", key="rep_supplier"):
                handle_report_selection("supplier")
                st.rerun()
            
            if st.button("🧾 POS Sales Report", key="rep_pos"):
                handle_report_selection("pos")
                st.rerun()
        
        with col3:
            if st.button("💊 Medicines Inventory Report", key="rep_inventory"):
                handle_report_selection("inventory")
                st.rerun()
        
        st.markdown("---")
        if st.button("🏠 Back to Main Menu", key="back_main"):
            reset_conversation()
            st.rerun()
    
    # Date range selector for reports (NEW - DASHBOARD MODE)
    if st.session_state.awaiting_date_range:
        st.markdown("### 📅 Select Date Range:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.today() - timedelta(days=30),
                key="start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today(),
                key="end_date"
            )
        
        if st.button("📊 Generate Report", key="gen_report"):
            if start_date > end_date:
                st.error("❌ Start date must be before end date")
            else:
                generate_report_with_dates(
                    st.session_state.selected_report,
                    start_date,
                    end_date
                )
                st.rerun()
        
        if st.button("🏠 Back to Reports", key="back_reports"):
            st.session_state.awaiting_date_range = False
            st.session_state.selected_report = None
            st.rerun()
    
    # File upload area
    if st.session_state.current_mode in ['data_entry', 'inventory']:
        uploaded_file = st.file_uploader(
            "📎 Upload Image (Bank Statement, POS Receipt, Supplier Invoice, or Prescription)",
            type=['jpg', 'jpeg', 'png'],
            key=f"file_upload_{st.session_state.session_id}"
        )
        
        if uploaded_file is not None:
            # Check if file already processed
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            
            if st.session_state.last_uploaded_file != file_id:
                st.session_state.last_uploaded_file = file_id
                handle_file_upload(uploaded_file)
                st.rerun()
    
    # Chat input
    chat_placeholder = "Type your message..." if st.session_state.chat_enabled else "Select an option above to start..."
    
    user_input = st.chat_input(
        chat_placeholder,
        disabled=not st.session_state.chat_enabled
    )
    
    if user_input:
        st.session_state.last_activity = datetime.now()
        process_user_input(user_input)
        st.rerun()



def initialize_session():
    """Initialize session state"""
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = 'initial'
    if 'show_main_menu' not in st.session_state:
        st.session_state.show_main_menu = True
    if 'show_report_menu' not in st.session_state:
        st.session_state.show_report_menu = False
    if 'awaiting_date_range' not in st.session_state:
        st.session_state.awaiting_date_range = False
    if 'selected_report' not in st.session_state:
        st.session_state.selected_report = None
    if 'chat_enabled' not in st.session_state:
        st.session_state.chat_enabled = False
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'pending_data' not in st.session_state:
        st.session_state.pending_data = None
    if 'data_type' not in st.session_state:
        st.session_state.data_type = None



def reset_conversation():
    """Reset conversation state"""
    st.session_state.chat_messages = []
    st.session_state.current_mode = 'initial'
    st.session_state.show_main_menu = True
    st.session_state.show_report_menu = False
    st.session_state.awaiting_date_range = False
    st.session_state.selected_report = None
    st.session_state.chat_enabled = False
    st.session_state.last_activity = datetime.now()
    st.session_state.last_uploaded_file = None
    st.session_state.conversation_history = []
    st.session_state.pending_data = None
    st.session_state.data_type = None



def add_message(role: str, content: str, **kwargs):
    """Add message to chat"""
    timestamp = datetime.now().strftime('%H:%M')
    message = {
        'role': role,
        'content': content,
        'timestamp': timestamp,
        **kwargs
    }
    st.session_state.chat_messages.append(message)
    
    # Update conversation history for LLM
    if role == 'user':
        st.session_state.conversation_history.append({
            "role": "user",
            "content": content
        })
    elif role == 'assistant':
        st.session_state.conversation_history.append({
            "role": "assistant",
            "content": content
        })



def handle_main_menu_selection(option: str):
    """Handle main menu button clicks"""
    if option == "data_entry":
        add_message('user', 'Smart Data Entry')
        add_message('assistant', 
            "I can help you with Smart Data Entry. Please upload an image of:\n\n"
            "• **Bank Statement** - Transaction records\n"
            "• **POS Receipt** - Sales receipts\n"
            "• **Supplier Invoice** - Purchase invoices\n\n"
            "Upload using the button below, and I'll automatically detect the document type and extract the information for you.")
        
        st.session_state.current_mode = 'data_entry'
        st.session_state.show_main_menu = False
        st.session_state.chat_enabled = True
    
    elif option == "inventory":
        add_message('user', 'Inventory Management')
        add_message('assistant',
            "I can help you with Inventory Management. You can:\n\n"
            "• **Upload Prescription** - Check medicine availability, stock, and expiry\n"
            "• Check individual medicine stock (e.g., 'Check Paracetamol stock')\n"
            "• Update stock quantities\n"
            "• Add new medicines to inventory\n\n"
            "📎 **Upload a prescription image** using the button below, or type your request.")
        
        st.session_state.current_mode = 'inventory'
        st.session_state.show_main_menu = False
        st.session_state.chat_enabled = True
    
    elif option == "dashboard":
        add_message('user', 'Dashboard & Reports')
        add_message('assistant',
            "📊 **Select the report you want to generate:**\n\n"
            "Choose from the buttons below:")
        
        st.session_state.current_mode = 'dashboard'
        st.session_state.show_main_menu = False
        st.session_state.show_report_menu = True



def handle_report_selection(report_type: str):
    """Handle report selection (NEW - DASHBOARD MODE)"""
    add_message('user', f'{report_type.title()} Report')
    
    if report_type == 'inventory':
        # Generate inventory report immediately (no date range needed)
        generate_inventory_report()
    else:
        # Ask for date range
        add_message('assistant', f"📅 Please select date range for **{report_type.title()} Report**")
        st.session_state.awaiting_date_range = True
        st.session_state.selected_report = report_type
        st.session_state.show_report_menu = False



def generate_report_with_dates(report_type: str, start_date: date, end_date: date):
    """Generate report with date range (NEW - DASHBOARD MODE)"""
    
    add_message('assistant', f"⏳ Generating {report_type.title()} Report from {start_date} to {end_date}...")
    
    try:
        if report_type == 'appointments':
            df = fetch_appointments_report(start_date, end_date)
            report_name = "Appointments"
        elif report_type == 'bank':
            df = fetch_bank_report(start_date, end_date)
            report_name = "Bank Statement"
        elif report_type == 'supplier':
            df = fetch_supplier_report(start_date, end_date)
            report_name = "Supplier Invoice"
        elif report_type == 'pos':
            df = fetch_pos_report(start_date, end_date)
            report_name = "POS Sales"
        else:
            add_message('assistant', "❌ Invalid report type")
            return
        
        if df is not None and not df.empty:
            add_message('assistant',
                f"✅ **{report_name} Report Generated**\n\n"
                f"Found {len(df)} record(s)",
                table=df)
            
            # Add download button
            excel_data = report_service.dataframe_to_excel(df)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_report_{timestamp}.xlsx"
            
            st.session_state.chat_messages[-1]['download'] = {
                'label': f"📥 Download {report_name} Report",
                'data': excel_data,
                'filename': filename,
                'key': f"download_{st.session_state.session_id}_{len(st.session_state.chat_messages)}"
            }
        else:
            add_message('assistant', f"📭 No records found for the selected date range")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        add_message('assistant', f"❌ Error generating report: {str(e)}")
    
    finally:
        st.session_state.awaiting_date_range = False
        st.session_state.show_report_menu = True



def generate_inventory_report():
    """Generate full inventory report (NEW - DASHBOARD MODE)"""
    
    add_message('assistant', "⏳ Generating Medicines Inventory Report...")
    
    try:
        df = fetch_inventory_report()
        
        if df is not None and not df.empty:
            add_message('assistant',
                f"✅ **Medicines Inventory Report Generated**\n\n"
                f"Total medicines: {len(df)}",
                table=df)
            
            # Add download button
            excel_data = report_service.dataframe_to_excel(df)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"inventory_report_{timestamp}.xlsx"
            
            st.session_state.chat_messages[-1]['download'] = {
                'label': "📥 Download Inventory Report",
                'data': excel_data,
                'filename': filename,
                'key': f"download_{st.session_state.session_id}_{len(st.session_state.chat_messages)}"
            }
        else:
            add_message('assistant', "📭 No medicines found in inventory")
    
    except Exception as e:
        logger.error(f"Error generating inventory report: {e}", exc_info=True)
        add_message('assistant', f"❌ Error generating report: {str(e)}")
    
    finally:
        st.session_state.show_report_menu = True



def fetch_appointments_report(start_date: date, end_date: date) -> Optional[pd.DataFrame]:
    """Fetch appointments from database (NEW - DASHBOARD MODE)"""
    try:
        with DatabaseConnection.get_connection() as conn:
            query = """
                SELECT 
                    appointment_id,
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    status
                FROM appointments
                WHERE DATE(appointment_date) BETWEEN %s AND %s
                ORDER BY appointment_date DESC, appointment_time DESC
            """
            df = pd.read_sql(query, conn, params=(start_date, end_date))
            return df
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}", exc_info=True)
        return None



def fetch_bank_report(start_date: date, end_date: date) -> Optional[pd.DataFrame]:
    """Fetch bank transactions from database (NEW - DASHBOARD MODE)"""
    try:
        with DatabaseConnection.get_connection() as conn:
            query = """
                SELECT 
                    tran_id,
                    txn_date,
                    cr_dr,
                    amount,
                    balance,
                    description,
                    created_at
                FROM bank_transactions
                WHERE DATE(txn_date) BETWEEN %s AND %s
                ORDER BY txn_date DESC
            """
            df = pd.read_sql(query, conn, params=(start_date, end_date))
            return df
    except Exception as e:
        logger.error(f"Error fetching bank transactions: {e}", exc_info=True)
        return None



def fetch_supplier_report(start_date: date, end_date: date) -> Optional[pd.DataFrame]:
    """Fetch supplier invoices from database (NEW - DASHBOARD MODE)"""
    try:
        with DatabaseConnection.get_connection() as conn:
            query = """
                SELECT 
                    invoice_id,
                    invoice_number,
                    invoice_date,
                    supplier_name,
                    supplier_gstin,
                    po_reference,
                    subtotal,
                    cgst_amount,
                    sgst_amount,
                    total_amount,
                    delivery_date,
                    vehicle_number,
                    created_at
                FROM supplier_invoices
                WHERE DATE(invoice_date) BETWEEN %s AND %s
                ORDER BY invoice_date DESC
            """
            df = pd.read_sql(query, conn, params=(start_date, end_date))
            return df
    except Exception as e:
        logger.error(f"Error fetching supplier invoices: {e}", exc_info=True)
        return None



def fetch_pos_report(start_date: date, end_date: date) -> Optional[pd.DataFrame]:
    """Fetch POS sales from database"""
    try:
        with DatabaseConnection.get_connection() as conn:
            query = """
                SELECT 
                    sale_id,
                    receipt_number,
                    sale_date,
                    pharmacist_name,
                    payment_mode,
                    subtotal,
                    cgst_amount,
                    sgst_amount,
                    total_amount,
                    created_at
                FROM pos_sales
                WHERE DATE(sale_date) BETWEEN %s AND %s
                ORDER BY sale_date DESC
            """
            df = pd.read_sql(query, conn, params=(start_date, end_date))
            return df
    except Exception as e:
        logger.error(f"Error fetching POS sales: {e}", exc_info=True)
        return None



def fetch_inventory_report() -> Optional[pd.DataFrame]:
    """Fetch all medicines from inventory (NEW - DASHBOARD MODE)"""
    try:
        with DatabaseConnection.get_connection() as conn:
            query = """
                SELECT 
                    stock_id,
                    medicine_name,
                    batch_number,
                    manufacturer,
                    expiry_date,
                    current_quantity,
                    reorder_level,
                    cost_price,
                    selling_price,
                    location
                FROM inventory_stock
                ORDER BY medicine_name ASC
            """
            df = pd.read_sql(query, conn)
            return df
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}", exc_info=True)
        return None



def process_user_input(user_input: str):
    """Process user input with LLM"""
    
    # Check for home/reset
    if user_input.lower() in ['home', 'menu', 'back', 'reset']:
        add_message('assistant', "Returning to main menu...")
        reset_conversation()
        return
    
    # Add user message
    add_message('user', user_input)
    
    # Handle confirmation responses for pending data
    if st.session_state.pending_data:
        handle_data_confirmation(user_input)
        return
    
    # Check if out of scope
    if pharmacist_llm_service.check_out_of_scope(user_input):
        add_message('assistant',
            "I'm sorry, but I can only assist with Smart Data Entry, Inventory Management, and Reports. "
            "Please ask me something related to these pharmacy functions, or type 'home' to return to the main menu.")
        return
    
    # Prepare messages for LLM
    system_message = {
        "role": "system",
        "content": """You are a pharmacy assistant AI with function calling capabilities. You MUST use the provided functions when users request actions.

Your available functions:
- check_medicine_stock: Check stock for a medicine
- check_prescription_availability: Check multiple medicines from prescription
- update_medicine_stock: Update stock quantity (USE THIS when user says "update quantity")
- add_new_medicine: Add new medicine to inventory

When user says "update paracetamol 500mg to 500 quantity", you MUST call update_medicine_stock function with:
- medicine_name: "Paracetamol 500mg"
- quantity: 500

NEVER respond with text commands like "UpdateStock()". ALWAYS use function calls.

Be concise, professional, and helpful.
Current mode: """ + st.session_state.current_mode
    }
    
    messages = [system_message] + st.session_state.conversation_history
    
    # Get LLM response with function calling
    with st.spinner("🤔 Processing..."):
        response = pharmacist_llm_service.chat(messages)
    
    if response['type'] == 'function_call':
        handle_function_call(response)
    elif response['type'] == 'message':
        add_message('assistant', response['content'])
    else:
        add_message('assistant', "I encountered an error. Please try again or type 'home' to restart.")



def handle_function_call(response: Dict):
    """Handle function call from LLM"""
    function_name = response['function_name']
    function_result = response['result']
    
    # Generate natural language response
    natural_response = pharmacist_llm_service.generate_response_from_function_result(
        messages=[{"role": "system", "content": "You are a helpful pharmacy assistant"}] + st.session_state.conversation_history,
        function_name=function_name,
        function_result=function_result,
        tool_call_id=response['tool_call_id']
    )
    
    # Handle inventory check
    if function_name == 'check_medicine_stock':
        if function_result['success']:
            data = function_result['data']
            formatted_response = f"{natural_response}\n\n"
            formatted_response += f"**Medicine Details:**\n"
            formatted_response += f"• **Name:** {data['medicine_name']}\n"
            formatted_response += f"• **Stock:** {data['stock_quantity']} units\n"
            formatted_response += f"• **Status:** {'✅ In Stock' if data['stock_quantity'] > 0 else '❌ Out of Stock'}\n"
            formatted_response += f"• **Expiry:** {data['expiry_date'] if data['expiry_date'] else 'N/A'}\n"
            formatted_response += f"• **Manufacturer:** {data['manufacturer'] if data['manufacturer'] else 'N/A'}\n"
            formatted_response += f"• **Price:** ₹{data['unit_price'] if data['unit_price'] else 'N/A'}\n"
            
            add_message('assistant', formatted_response)
        else:
            add_message('assistant', natural_response)
    
    # Handle prescription availability check
    elif function_name == 'check_prescription_availability':
        results = function_result.get('data', [])
        
        formatted_response = f"{natural_response}\n\n**Availability Status:**\n\n"
        
        for result in results:
            status = "✅ Available" if result['in_stock'] else "❌ Out of Stock"
            formatted_response += f"• **{result['searched_name']}**: {status}"
            
            if result['found']:
                formatted_response += f" ({result['stock_quantity']} units)"
            
            formatted_response += "\n"
        
        add_message('assistant', formatted_response)
    
    # Default
    else:
        add_message('assistant', natural_response)



def handle_file_upload(uploaded_file):
    """Handle file upload with unified extraction"""
    
    add_message('user', f"[Uploaded: {uploaded_file.name}]")
    
    mode = st.session_state.current_mode
    
    # Read file bytes
    file_bytes = uploaded_file.read()
    
    if mode == 'data_entry':
        add_message('assistant', "📄 Analyzing document...")
        
        with st.spinner("🔍 Classifying and extracting data..."):
            success, message, doc_type, extracted_data = finance_service.extract_document(file_bytes)
        
        if not success:
            add_message('assistant',
                f"❌ {message}\n\n"
                "Please ensure:\n"
                "• Image is clear and well-lit\n"
                "• Text is readable\n"
                "• File format is JPG or PNG\n\n"
                "Would you like to:\n"
                "1. Upload another image\n"
                "2. Type 'manual entry' for manual data entry")
            return
        
        # Route to appropriate handler
        if doc_type == 'bank':
            handle_bank_statement_display(extracted_data)
        elif doc_type == 'pos':
            handle_pos_statement_display(extracted_data)
        elif doc_type == 'supplier':
            handle_supplier_invoice_display(extracted_data)
        else:
            add_message('assistant', f"❌ Unsupported document type: {doc_type}")
    
    elif mode == 'inventory':
        handle_prescription_extraction(file_bytes)



def handle_bank_statement_display(transactions: List[Dict]):
    """Display bank statement data in editable table"""
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    
    # ONLY fields that exist in DB schema
    expected_columns = ['tran_id', 'txn_date', 'cr_dr', 'amount', 'balance', 'description']
    
    # Add missing columns
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None
    
    # Reorder
    df = df[expected_columns]
    
    # Convert txn_date to datetime
    df['txn_date'] = pd.to_datetime(df['txn_date'], errors='coerce')
    
    # Column configuration
    column_config = {
        "tran_id": st.column_config.TextColumn("Transaction ID", width="small", required=True),
        "txn_date": st.column_config.DateColumn("Date", width="small", required=True),
        "cr_dr": st.column_config.SelectboxColumn("CR/DR", options=["CR", "DR"], width="small", required=True),
        "amount": st.column_config.NumberColumn("Amount", format="%.2f", width="medium", required=True),
        "balance": st.column_config.NumberColumn("Balance", format="%.2f", width="medium"),
        "description": st.column_config.TextColumn("Description", width="large")
    }
    
    table_key = f"bank_table_{st.session_state.session_id}_{len(st.session_state.chat_messages)}"
    
    add_message('assistant',
        f"✅ **Bank Statement Detected!**\n\n"
        f"Extracted {len(transactions)} transaction(s).\n\n"
        "**Please review the data below.** You can edit any cell directly by clicking on it.",
        editable_table=df,
        table_key=table_key,
        column_config=column_config)
    
    add_message('assistant',
        "After reviewing:\n"
        "• Type **'confirm'** to save to database\n"
        "• Type **'cancel'** to discard\n"
        "• Edit the table cells above if needed")
    
    # Store pending data
    st.session_state.pending_data = {
        'type': 'bank',
        'transactions': transactions,
        'dataframe': df,
        'table_key': table_key
    }



def handle_pos_statement_display(transaction: Dict):
    """Display POS statement data"""
    
    formatted = f"✅ **POS Receipt Detected!**\n\n**Transaction Details:**\n"
    formatted += f"• **Receipt No:** {transaction['receipt_number']}\n"
    formatted += f"• **Date:** {transaction['sale_date']}\n"
    formatted += f"• **Pharmacist:** {transaction.get('pharmacist_name', 'N/A')}\n"
    formatted += f"• **Payment:** {transaction.get('payment_mode', 'cash')}\n"
    formatted += f"• **Subtotal:** ₹{transaction.get('subtotal', 0.0):.2f}\n"
    formatted += f"• **CGST:** ₹{transaction.get('cgst_amount', 0.0):.2f}\n"
    formatted += f"• **SGST:** ₹{transaction.get('sgst_amount', 0.0):.2f}\n"
    formatted += f"• **Total Amount:** ₹{transaction['total_amount']:.2f}\n\n"
    
    if transaction['items']:
        items_df = pd.DataFrame(transaction['items'])
        
        column_config = {
            "medicine_name": st.column_config.TextColumn("Medicine", width="large", required=True),
            "batch_number": st.column_config.TextColumn("Batch", width="medium"),
            "quantity": st.column_config.NumberColumn("Qty", width="small", required=True),
            "unit_price": st.column_config.NumberColumn("Unit Price", format="%.2f", width="small", required=True),
            "total_price": st.column_config.NumberColumn("Total", format="%.2f", width="small", required=True)
        }
        
        table_key = f"pos_table_{st.session_state.session_id}_{len(st.session_state.chat_messages)}"
        
        add_message('assistant', formatted + "**Items:**",
            editable_table=items_df,
            table_key=table_key,
            column_config=column_config)
    else:
        add_message('assistant', formatted)
    
    add_message('assistant',
        "Is this information **correct**?\n"
        "• Type 'yes' or 'confirm' to save to database\n"
        "• Type 'no' or 'cancel' to discard\n"
        "• Edit the table cells above if needed")
    
    st.session_state.pending_data = {
        'type': 'pos',
        'transaction': transaction,
        'table_key': f"pos_table_{st.session_state.session_id}_{len(st.session_state.chat_messages) - 1}"
    }



def handle_supplier_invoice_display(invoice: Dict):
    """Display supplier invoice data"""
    
    formatted = f"✅ **Supplier Invoice Detected!**\n\n**Invoice Details:**\n"
    formatted += f"• **Invoice No:** {invoice['invoice_number']}\n"
    formatted += f"• **Date:** {invoice['invoice_date']}\n"
    formatted += f"• **Supplier:** {invoice['supplier_name']}\n"
    formatted += f"• **GSTIN:** {invoice.get('supplier_gstin', 'N/A')}\n"
    formatted += f"• **PO Reference:** {invoice.get('po_reference', 'N/A')}\n"
    formatted += f"• **Delivery Date:** {invoice.get('delivery_date', 'N/A')}\n"
    formatted += f"• **Vehicle:** {invoice.get('vehicle_number', 'N/A')}\n"
    formatted += f"• **Subtotal:** ₹{invoice.get('subtotal', 0.0):.2f}\n"
    formatted += f"• **CGST:** ₹{invoice.get('cgst_amount', 0.0):.2f}\n"
    formatted += f"• **SGST:** ₹{invoice.get('sgst_amount', 0.0):.2f}\n"
    formatted += f"• **Total Amount:** ₹{invoice['total_amount']:.2f}\n\n"
    
    if invoice['items']:
        items_df = pd.DataFrame(invoice['items'])
        
        # Convert expiry_date to datetime
        if 'expiry_date' in items_df.columns:
            items_df['expiry_date'] = pd.to_datetime(items_df['expiry_date'], errors='coerce')
        
        column_config = {
            "medicine_name": st.column_config.TextColumn("Medicine", width="large", required=True),
            "batch_number": st.column_config.TextColumn("Batch", width="medium"),
            "manufacturer": st.column_config.TextColumn("Manufacturer", width="medium"),
            "expiry_date": st.column_config.DateColumn("Expiry", width="small"),
            "quantity": st.column_config.NumberColumn("Qty", width="small", required=True),
            "unit_price": st.column_config.NumberColumn("Unit Price", format="%.2f", width="small", required=True),
            "total_price": st.column_config.NumberColumn("Total", format="%.2f", width="small", required=True)
        }
        
        table_key = f"supplier_table_{st.session_state.session_id}_{len(st.session_state.chat_messages)}"
        
        add_message('assistant', formatted + "**Items:**",
            editable_table=items_df,
            table_key=table_key,
            column_config=column_config)
    else:
        add_message('assistant', formatted)
    
    add_message('assistant',
        "Is this information **correct**?\n"
        "• Type 'yes' or 'confirm' to save to database\n"
        "• Type 'no' or 'cancel' to discard\n"
        "• Edit the table cells above if needed")
    
    st.session_state.pending_data = {
        'type': 'supplier',
        'invoice': invoice,
        'table_key': f"supplier_table_{st.session_state.session_id}_{len(st.session_state.chat_messages) - 1}"
    }



def handle_prescription_extraction(image_bytes: bytes):
    """Extract medicines from prescription and check availability with detailed info"""
    
    with st.spinner("💊 Extracting medicines from prescription..."):
        extracted_text = ocr_service.extract_text_from_image(image_bytes)
        
        if not extracted_text:
            add_message('assistant',
                "❌ Failed to extract text from prescription. Please upload a clearer image.")
            return
        
        medicine_items = ocr_service.extract_prescription_items(extracted_text)
        
        if not medicine_items:
            add_message('assistant',
                "❌ No medicines found in the prescription. Please check the image quality.")
            return
    
    add_message('assistant', f"✅ Found {len(medicine_items)} medicine(s) in prescription.\n\nChecking inventory...")
    
    # Check availability with detailed info
    with st.spinner("🔍 Checking inventory..."):
        availability_results = check_prescription_medicines_detailed(medicine_items)
    
    # Display results in table format
    if availability_results:
        results_df = pd.DataFrame(availability_results)
        
        # Format expiry date
        if 'expiry_date' in results_df.columns:
            results_df['expiry_date'] = pd.to_datetime(results_df['expiry_date'], errors='coerce')
        
        # Add status column
        results_df['status'] = results_df['available'].apply(lambda x: '✅ Available' if x else '❌ Out of Stock')
        
        # Reorder columns for display
        display_columns = ['medicine_name', 'status', 'stock_quantity', 'expiry_date', 'batch_number', 'manufacturer', 'unit_price']
        available_columns = [col for col in display_columns if col in results_df.columns]
        results_df = results_df[available_columns]
        
        add_message('assistant',
            "📋 **Prescription Inventory Check Results:**\n\n"
            f"Total medicines checked: {len(medicine_items)}",
            table=results_df)
        
        # Summary
        available_count = sum(1 for r in availability_results if r['available'])
        unavailable_count = len(availability_results) - available_count

        summary = f"**Summary:**\n"
        summary += f"• ✅ Available: {available_count}\n"
        summary += f"• ❌ Out of Stock: {unavailable_count}"

        # Highlight low stock or expiring soon
        low_stock = [r for r in availability_results if r['available'] and r.get('stock_quantity', 0) < 10]
        if low_stock:
            summary += f"\n\n⚠️ **Low Stock Warning:** {len(low_stock)} medicine(s) have less than 10 units"

        add_message('assistant', summary)
    else:
        add_message('assistant', "❌ No results found.")



def check_prescription_medicines_detailed(medicine_list: List[str]) -> List[Dict]:
    """Check prescription medicines against inventory with detailed information"""
    try:
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            
            results = []
            
            for medicine_name in medicine_list:
                # Extract base medicine name
                base_name = medicine_name.split()[0].strip()
                
                # Search in inventory_stock table
                cursor.execute("""
                    SELECT 
                        medicine_name,
                        batch_number,
                        manufacturer,
                        expiry_date,
                        current_quantity as stock_quantity,
                        selling_price as unit_price,
                        location
                    FROM inventory_stock
                    WHERE LOWER(medicine_name) LIKE LOWER(%s)
                    AND current_quantity > 0
                    ORDER BY expiry_date ASC
                """, (f"%{base_name}%",))
                
                rows = cursor.fetchall()
                
                if rows:
                    for row in rows:
                        results.append({
                            'medicine_name': f"{row[0]} (for: {medicine_name})",
                            'batch_number': row[1],
                            'manufacturer': row[2],
                            'expiry_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                            'stock_quantity': row[4],
                            'unit_price': float(row[5]) if row[5] else 0.0,
                            'location': row[6],
                            'available': True
                        })
                else:
                    results.append({
                        'medicine_name': medicine_name,
                        'batch_number': None,
                        'manufacturer': None,
                        'expiry_date': None,
                        'stock_quantity': 0,
                        'unit_price': 0.0,
                        'location': None,
                        'available': False
                    })
            
            cursor.close()
            return results
        
    except Exception as e:
        logger.error(f"Error checking prescription medicines: {e}", exc_info=True)
        return []



def handle_data_confirmation(user_input: str):
    """Handle user confirmation"""
    
    user_lower = user_input.lower().strip()
    pending = st.session_state.pending_data
    
    if user_lower in ['yes', 'confirm', 'correct', 'save']:
        
        if pending['type'] == 'bank':
            edited_df = pending.get('edited_dataframe', pending.get('dataframe'))
            
            with st.spinner("💾 Saving bank transactions..."):
                transactions = edited_df.to_dict('records')
                
                # Clean NaN and NaT
                for trans in transactions:
                    for key, value in trans.items():
                        if pd.isna(value):
                            trans[key] = None
                        elif isinstance(value, pd.Timestamp):
                            trans[key] = value.strftime('%Y-%m-%d')
                
                success, message, count = finance_service.save_bank_transactions(
                    transactions,
                    approved_by=st.session_state.user.get('user_id')
                )
            
            if success:
                add_message('assistant', 
                    f"✅ **Success!** {count} transaction(s) saved.\n\n"
                    f"• Total: {count}\n"
                    f"• Approved by: {st.session_state.user.get('full_name')}\n"
                    f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "Type 'home' to return or upload another document.")
            else:
                add_message('assistant', f"❌ Error: {message}")
            
            st.session_state.pending_data = None
        
        elif pending['type'] == 'pos':
            edited_items_df = pending.get('edited_dataframe')
            
            if edited_items_df is not None:
                items = edited_items_df.to_dict('records')
                for item in items:
                    for key, value in item.items():
                        if pd.isna(value):
                            item[key] = None
                pending['transaction']['items'] = items
            
            with st.spinner("💾 Saving POS transaction..."):
                success, message, sale_id = finance_service.save_pos_transaction(
                    pending['transaction'],
                    approved_by=st.session_state.user.get('user_id')
                )
            
            if success:
                add_message('assistant', 
                    f"✅ **Success!** POS transaction saved.\n\n"
                    f"Sale ID: {sale_id}\n\n"
                    "Type 'home' to return.")
            else:
                add_message('assistant', f"❌ Error: {message}")
            
            st.session_state.pending_data = None
        
        elif pending['type'] == 'supplier':
            edited_items_df = pending.get('edited_dataframe')
            
            if edited_items_df is not None:
                items = edited_items_df.to_dict('records')
                for item in items:
                    for key, value in item.items():
                        if pd.isna(value):
                            item[key] = None
                        elif isinstance(value, pd.Timestamp):
                            item[key] = value.strftime('%Y-%m-%d')
                pending['invoice']['items'] = items
            
            with st.spinner("💾 Saving supplier invoice..."):
                success, message, invoice_id = finance_service.save_supplier_invoice(
                    pending['invoice'],
                    approved_by=st.session_state.user.get('user_id')
                )
            
            if success:
                add_message('assistant', 
                    f"✅ **Success!** Supplier invoice saved.\n\n"
                    f"Invoice ID: {invoice_id}\n\n"
                    "Type 'home' to return.")
            else:
                add_message('assistant', f"❌ Error: {message}")
            
            st.session_state.pending_data = None
    
    elif user_lower in ['no', 'cancel', 'discard']:
        add_message('assistant', "❌ Data discarded. Upload new image or type 'home'.")
        st.session_state.pending_data = None
    
    else:
        add_message('assistant',
            "💡 Click table cells to edit.\n\n"
            "Then type:\n"
            "• **'confirm'** to save\n"
            "• **'cancel'** to discard")
