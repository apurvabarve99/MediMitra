from huggingface_hub import InferenceClient
from config.settings import settings
import logging
from typing import Optional, Dict, List, Any
import time
import json
from backend.inventory_service import inventory_service
from backend.finance_service import finance_service
from backend.report_service import report_service
from backend.db_connection import DatabaseConnection



logger = logging.getLogger(__name__)




class PharmacistLLMService:
    """LLM service for pharmacist dashboard with function calling"""
    
    def __init__(self):
        self.hf_token = settings.HF_TOKEN
        
        # Primary model (Mistral-7B-Instruct)
        try:
            self.client = InferenceClient(
                model=settings.MEDICAL_MODEL,
                token=self.hf_token,
                timeout=90
            )
            logger.info(f"✅ Pharmacist LLM initialized: {settings.MEDICAL_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize pharmacist LLM: {e}")
            self.client = None
        
        # Define available tools/functions
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict]:
        """Define function calling tools for the LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_medicine_stock",
                    "description": "Check stock availability, quantity, expiry date, and supplier for a specific medicine",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "medicine_name": {
                                "type": "string",
                                "description": "Name of the medicine to check"
                            }
                        },
                        "required": ["medicine_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_prescription_availability",
                    "description": "Check availability of multiple medicines from a prescription",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "medicine_list": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of medicine names from prescription"
                            }
                        },
                        "required": ["medicine_list"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_medicine_stock",
                    "description": "REQUIRED: Use this function when user wants to update, change, or modify stock quantity. Example: 'update paracetamol to 500', 'change quantity of aspirin to 100'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "medicine_name": {
                                "type": "string",
                                "description": "Name of the medicine to update (e.g., 'Paracetamol 500mg')"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "New quantity to set"
                            },
                            "batch_number": {
                                "type": "string",
                                "description": "Batch number (optional)"
                            }
                        },
                        "required": ["medicine_name", "quantity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_new_medicine",
                    "description": "Add a new medicine to inventory with all details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "medicine_name": {
                                "type": "string",
                                "description": "Name of the medicine"
                            },
                            "batch_number": {
                                "type": "string",
                                "description": "Batch number"
                            },
                            "manufacturer": {
                                "type": "string",
                                "description": "Manufacturer name"
                            },
                            "expiry_date": {
                                "type": "string",
                                "description": "Expiry date in YYYY-MM-DD format"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Initial stock quantity"
                            },
                            "unit_price": {
                                "type": "number",
                                "description": "Unit purchase price"
                            },
                            "selling_price": {
                                "type": "number",
                                "description": "Selling price per unit"
                            },
                            "location": {
                                "type": "string",
                                "description": "Storage location (e.g., Shelf A1)"
                            }
                        },
                        "required": ["medicine_name", "batch_number", "manufacturer", "expiry_date", "quantity", "unit_price", "selling_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_appointments_report",
                    "description": "Generate appointments report with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format (optional)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format (optional)"
                            },
                            "doctor_id": {
                                "type": "integer",
                                "description": "Filter by doctor ID (optional)"
                            },
                            "specialization": {
                                "type": "string",
                                "description": "Filter by specialization (optional)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_inventory_report",
                    "description": "Generate inventory report with filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter_type": {
                                "type": "string",
                                "enum": ["low_stock", "expiring", "full"],
                                "description": "Type of inventory report: low_stock (below reorder level), expiring (expiring within 30 days), or full (complete inventory)"
                            }
                        },
                        "required": ["filter_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_bank_report",
                    "description": "Generate bank statement transactions report",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format (optional)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format (optional)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_pos_report",
                    "description": "Generate POS (Point of Sale) report",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format (optional)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format (optional)"
                            },
                            "report_type": {
                                "type": "string",
                                "enum": ["summary", "details"],
                                "description": "Type of report: summary (aggregated) or details (transaction list)"
                            }
                        },
                        "required": ["report_type"]
                    }
                }
            }
        ]
    
    def execute_function(self, function_name: str, arguments: Dict) -> Dict[str, Any]:
        """Execute a function based on LLM's request"""
        try:
            logger.info(f"Executing function: {function_name} with args: {arguments}")
            
            # Inventory functions
            if function_name == "check_medicine_stock":
                success, message, data = inventory_service.check_medicine_stock(
                    arguments.get('medicine_name')
                )
                return {
                    "success": success,
                    "message": message,
                    "data": data
                }
            
            elif function_name == "check_prescription_availability":
                results = inventory_service.check_prescription_availability(
                    arguments.get('medicine_list', [])
                )
                return {
                    "success": True,
                    "message": f"Checked {len(results)} medicine(s)",
                    "data": results
                }
            
            elif function_name == "update_medicine_stock":
                return self.update_medicine_stock(
                    medicine_name=arguments.get('medicine_name'),
                    quantity=arguments.get('quantity'),
                    batch_number=arguments.get('batch_number')
                )
            
            elif function_name == "add_new_medicine":
                return self.add_new_medicine(
                    medicine_name=arguments.get('medicine_name'),
                    batch_number=arguments.get('batch_number'),
                    manufacturer=arguments.get('manufacturer'),
                    expiry_date=arguments.get('expiry_date'),
                    quantity=arguments.get('quantity'),
                    unit_price=arguments.get('unit_price'),
                    selling_price=arguments.get('selling_price'),
                    location=arguments.get('location')
                )
            
            # Report functions
            elif function_name == "generate_appointments_report":
                df = report_service.generate_appointments_report(
                    start_date=arguments.get('start_date'),
                    end_date=arguments.get('end_date'),
                    doctor_id=arguments.get('doctor_id'),
                    specialization=arguments.get('specialization')
                )
                return {
                    "success": not df.empty,
                    "message": f"Generated report with {len(df)} appointments" if not df.empty else "No appointments found",
                    "data": df,
                    "report_type": "appointments"
                }
            
            elif function_name == "generate_inventory_report":
                df = report_service.generate_inventory_report(
                    filter_type=arguments.get('filter_type', 'full')
                )
                return {
                    "success": not df.empty,
                    "message": f"Generated inventory report with {len(df)} items" if not df.empty else "No items found",
                    "data": df,
                    "report_type": "inventory"
                }
            
            elif function_name == "generate_bank_report":
                df = report_service.generate_bank_report(
                    start_date=arguments.get('start_date'),
                    end_date=arguments.get('end_date')
                )
                return {
                    "success": not df.empty,
                    "message": f"Generated bank report with {len(df)} transactions" if not df.empty else "No transactions found",
                    "data": df,
                    "report_type": "bank"
                }
            
            elif function_name == "generate_pos_report":
                df = report_service.generate_pos_report(
                    start_date=arguments.get('start_date'),
                    end_date=arguments.get('end_date'),
                    report_type=arguments.get('report_type', 'summary')
                )
                return {
                    "success": not df.empty,
                    "message": f"Generated POS report with {len(df)} entries" if not df.empty else "No data found",
                    "data": df,
                    "report_type": "pos"
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown function: {function_name}"
                }
        
        except Exception as e:
            logger.error(f"Function execution error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error executing {function_name}: {str(e)}"
            }
    
    def update_medicine_stock(self, medicine_name: str, quantity: int, batch_number: Optional[str] = None) -> Dict:
        """Update medicine stock quantity"""
        try:            
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Extract base medicine name
                base_name = medicine_name.split()[0].strip()
                
                # Find medicine
                if batch_number:
                    cursor.execute("""
                        SELECT stock_id, medicine_name, current_quantity 
                        FROM inventory_stock 
                        WHERE LOWER(medicine_name) LIKE LOWER(%s) AND batch_number = %s
                        LIMIT 1
                    """, (f"%{base_name}%", batch_number))
                else:
                    cursor.execute("""
                        SELECT stock_id, medicine_name, current_quantity 
                        FROM inventory_stock 
                        WHERE LOWER(medicine_name) LIKE LOWER(%s)
                        ORDER BY expiry_date ASC
                        LIMIT 1
                    """, (f"%{base_name}%",))
                
                result = cursor.fetchone()
                
                if not result:
                    cursor.close()
                    return {
                        'success': False,
                        'message': f"Medicine '{medicine_name}' not found in inventory"
                    }
                
                stock_id = result[0]
                db_medicine_name = result[1]
                old_quantity = result[2]
                
                # Update quantity using stock_id
                cursor.execute("""
                    UPDATE inventory_stock 
                    SET current_quantity = %s, updated_at = NOW()
                    WHERE stock_id = %s
                """, (quantity, stock_id))
                
                affected_rows = cursor.rowcount
                cursor.close()
                
                if affected_rows == 0:
                    return {
                        'success': False,
                        'message': f"Failed to update {db_medicine_name}"
                    }
                
                return {
                    'success': True,
                    'message': f"Updated {db_medicine_name} stock from {old_quantity} to {quantity} units",
                    'data': {
                        'medicine_name': db_medicine_name,
                        'old_quantity': old_quantity,
                        'new_quantity': quantity
                    }
                }
            
        except Exception as e:
            logger.error(f"Error updating medicine stock: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Database error: {str(e)}"
            }


    def add_new_medicine(self, medicine_name: str, batch_number: str, manufacturer: str,
                        expiry_date: str, quantity: int, unit_price: float, 
                        selling_price: float, location: Optional[str] = None) -> Dict:
        """Add new medicine to inventory"""
        try:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if already exists
                cursor.execute("""
                    SELECT medicine_name FROM inventory_stock 
                    WHERE LOWER(medicine_name) = LOWER(%s) AND batch_number = %s
                """, (medicine_name, batch_number))
                
                if cursor.fetchone():
                    cursor.close()
                    return {
                        'success': False,
                        'message': f"Medicine '{medicine_name}' with batch '{batch_number}' already exists. Use update instead."
                    }
                
                # Insert new medicine
                cursor.execute("""
                    INSERT INTO inventory_stock 
                    (medicine_name, batch_number, manufacturer, expiry_date, 
                    current_quantity, unit_price, selling_price, location, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING stock_id
                """, (medicine_name, batch_number, manufacturer, expiry_date, 
                    quantity, unit_price, selling_price, location))
                
                stock_id = cursor.fetchone()[0]
                cursor.close()
                
                return {
                    'success': True,
                    'message': f"Successfully added {medicine_name} to inventory",
                    'data': {
                        'stock_id': stock_id,
                        'medicine_name': medicine_name,
                        'batch_number': batch_number,
                        'quantity': quantity
                    }
                }
            
        except Exception as e:
            logger.error(f"Error adding new medicine: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Database error: {str(e)}"
            }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        if not self.client:
            return {"type": "error", "content": "LLM service not available"}
        
        try:
            # 1. Initial call to LLM to detect function needs
            response = self.client.chat_completion(
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            if not response or not response.choices:
                return {"type": "error", "content": "No response from LLM"}
            
            message = response.choices[0].message
            
            # 2. Check for tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except:
                    arguments = {}
                
                # 3. EXECUTE THE ACTUAL DATABASE FUNCTION
                function_result = self.execute_function(function_name, arguments)
                
                # 4. GENERATE THE FINAL NATURAL LANGUAGE RESPONSE
                # This makes the LLM say "I've updated it" instead of just showing code
                final_content = self.generate_response_from_function_result(
                    messages=messages,
                    function_name=function_name,
                    function_result=function_result,
                    tool_call_id=tool_call.id
                )

                return {
                    "type": "message",
                    "content": final_content,
                    "function_executed": function_name, # Optional: for UI feedback
                    "success": function_result.get('success', False)
                }
            
            # Regular text response
            else:
                return {
                    "type": "message",
                    "content": message.content.strip()
                }
        
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {"type": "error", "content": f"Error: {str(e)}"}
    
    def generate_response_from_function_result(
        self,
        messages: List[Dict[str, str]],
        function_name: str,
        function_result: Dict,
        tool_call_id: str
    ) -> str:
        """
        Generate natural language response after function execution
        
        Args:
            messages: Conversation history
            function_name: Name of executed function
            function_result: Result from function
            tool_call_id: ID of the tool call
        
        Returns:
            Natural language response
        """
        try:
            # Add function result to messages
            messages_with_result = messages + [
                {
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_result),
                    "tool_call_id": tool_call_id
                }
            ]
            
            # Get LLM to generate natural response
            response = self.client.chat_completion(
                messages=messages_with_result,
                max_tokens=300,
                temperature=0.5,
                stream=False
            )
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "Function executed successfully."
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return function_result.get('message', 'Operation completed.')
    
    def check_out_of_scope(self, user_message: str) -> bool:
        """
        Check if user query is out of scope (not related to pharmacy functions)
        Uses keyword matching (no LLM needed for efficiency)
        """
        user_lower = user_message.lower()
        
        # In-scope keywords
        in_scope_keywords = [
            # Inventory
            'stock', 'medicine', 'inventory', 'available', 'check', 'expiry', 'expire',
            'quantity', 'update', 'add', 'supplier', 'manufacturer',
            
            # Data entry
            'upload', 'statement', 'bank', 'pos', 'receipt', 'transaction',
            'entry', 'data', 'save', 'invoice',
            
            # Reports
            'report', 'dashboard', 'appointment', 'sales', 'summary',
            'download', 'export', 'excel'
        ]
        
        # Check if any in-scope keyword is present
        if any(keyword in user_lower for keyword in in_scope_keywords):
            return False  # In scope
        
        # Out-of-scope indicators
        out_of_scope_keywords = [
            'weather', 'news', 'joke', 'story', 'game', 'recipe',
            'movie', 'song', 'sport', 'politics', 'celebrity',
            'hypothetical', 'what if', 'pretend', 'imagine',
            'role play', 'act as', 'you are a'
        ]
        
        if any(keyword in user_lower for keyword in out_of_scope_keywords):
            return True  # Out of scope
        
        # If message is very short and generic (likely out of scope)
        if len(user_message.strip()) < 5:
            return True
        
        # Default: assume in scope if unclear
        return False




# Global instance
pharmacist_llm_service = PharmacistLLMService()
