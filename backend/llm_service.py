from huggingface_hub import InferenceClient
from config.settings import settings
import logging
from typing import Optional, Dict, List
import time
import re


logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Hugging Face models using chat_completion API"""
    
    def __init__(self):
        self.hf_token = settings.HF_TOKEN
        
        # Primary medical model (Mistral-7B-Instruct)
        try:
            self.medical_client = InferenceClient(
                model=settings.MEDICAL_MODEL,
                token=self.hf_token,
                timeout=90
            )
            logger.info(f"✅ Primary medical model initialized: {settings.MEDICAL_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize primary medical model: {e}")
            self.medical_client = None
        
        # Fallback medical model (Zephyr-7B-Beta)
        try:
            self.fallback_medical_client = InferenceClient(
                model=settings.FALLBACK_MEDICAL_MODEL,
                token=self.hf_token,
                timeout=90
            )
            logger.info(f"✅ Fallback medical model initialized: {settings.FALLBACK_MEDICAL_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize fallback medical model: {e}")
            self.fallback_medical_client = None
        
        # Orchestration model (same as primary for simplicity)
        try:
            self.orchestration_client = InferenceClient(
                model=settings.ORCHESTRATION_MODEL,
                token=self.hf_token,
                timeout=90
            )
            logger.info(f"✅ Orchestration model initialized: {settings.ORCHESTRATION_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize orchestration model: {e}")
            self.orchestration_client = None
    
    def get_medical_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 512,
        temperature: float = 0.3,
        retries: int = 2
    ) -> Optional[str]:
        """
        Get response from medical models with fallback using chat_completion
        Tries primary model (Mistral) first, then fallback (Zephyr)
        
        Args:
            messages: List of chat messages [{"role": "system"|"user"|"assistant", "content": "..."}]
        """
        # Try primary model first
        if self.medical_client:
            logger.info(f"Trying primary medical model: {settings.MEDICAL_MODEL}")
            response = self._call_chat_model(
                client=self.medical_client,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                retries=retries,
                model_name=settings.MEDICAL_MODEL
            )
            
            if response:
                logger.info("✅ Primary medical model succeeded")
                return response
            else:
                logger.warning("Primary medical model failed after retries")
        
        # Try fallback model
        if self.fallback_medical_client:
            logger.info(f"Trying fallback medical model: {settings.FALLBACK_MEDICAL_MODEL}")
            response = self._call_chat_model(
                client=self.fallback_medical_client,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                retries=retries,
                model_name=settings.FALLBACK_MEDICAL_MODEL
            )
            
            if response:
                logger.info("✅ Fallback medical model succeeded")
                return response
            else:
                logger.warning("Fallback medical model also failed")
        
        logger.error("All medical models failed")
        return None
    
    def _call_chat_model(
        self,
        client: InferenceClient,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        retries: int,
        model_name: str
    ) -> Optional[str]:
        """
        Call a specific model using chat_completion API with retry logic
        """
        for attempt in range(retries + 1):
            try:
                logger.info(f"Calling {model_name} via chat_completion (attempt {attempt + 1}/{retries + 1})...")
                
                response = client.chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )
                
                # Extract content from response
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    
                    if content and len(content.strip()) > 10:
                        logger.info(f"✅ {model_name} response received ({len(content)} chars)")
                        return content.strip()
                    else:
                        logger.warning(f"{model_name} returned short/empty response: '{content}'")
                else:
                    logger.warning(f"{model_name} returned no choices")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"{model_name} error (attempt {attempt + 1}/{retries + 1}): {error_msg}")
                logger.error(f"Error type: {type(e).__name__}")
                
                if attempt < retries:
                    wait_time = 3 * (attempt + 1)  # Progressive backoff: 3s, 6s
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        return None
    
    def get_orchestration_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 256,
        temperature: float = 0.7,
        retries: int = 1
    ) -> Optional[str]:
        """
        Get response from orchestration model using chat_completion
        """
        if not self.orchestration_client:
            logger.error("Orchestration client not initialized")
            return None
        
        for attempt in range(retries + 1):
            try:
                response = self.orchestration_client.chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )
                
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        return content.strip()
                    
            except Exception as e:
                logger.error(f"Orchestration model error (attempt {attempt + 1}/{retries + 1}): {e}")
                if attempt < retries:
                    time.sleep(2)
        
        return None
    
    def extract_medicine_instructions(self, prescription_items: List[str]) -> Optional[str]:
        """
        Extract dosage instructions from prescription items
        Uses LLM first (with fallback), then intelligent natural language generation
        """
        if not prescription_items:
            return None
        
        logger.info(f"Processing {len(prescription_items)} prescription items")
        
        # Try LLM first (tries both primary and fallback models)
        try:
            items_text = "\n".join(prescription_items)
            
            # Chat messages format - UPDATED FOR CONCISENESS
            messages = [
                {
                    "role": "system",
                    "content": "You are a pharmacist providing medicine instructions. Be formal, precise, and concise. Use bullet points."
                },
                {
                    "role": "user",
                    "content": f"""Provide concise instructions for these medicines:

    {items_text}

    For EACH medicine, provide in this EXACT format:
    **[Medicine Name]**
    • Dosage: [amount and form]
    • Frequency: [times per day in simple terms]
    • Timing: [when to take - before/after food]
    • Duration: [how many days]
    • Note: [one-line warning if needed]

    Be brief and professional. No conversational text."""
                }
            ]
            
            logger.info("Attempting LLM generation (trying both models)...")
            response = self.get_medical_response(messages, max_tokens=500, temperature=0.2, retries=2)
            
            if response and len(response) > 50:
                logger.info("✅ LLM generated instructions successfully")
                return response
            else:
                logger.warning("All LLMs failed, using intelligent fallback")
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
        
        # Use intelligent natural language fallback
        logger.info("Generating natural language instructions...")
        return self._generate_natural_instructions(prescription_items)
    
    def _generate_natural_instructions(self, prescription_items: List[str]) -> str:
        """
        Generate natural, pharmacist-like instructions from prescription items
        This mimics how a pharmacist would explain medicines to a patient
        """
        logger.info("Generating natural language instructions")
        
        instructions = []
        
        for idx, item in enumerate(prescription_items, 1):
            item_lower = item.lower()
            
            # Parse medicine name and dosage
            medicine_name = self._extract_medicine_name(item)
            dosage = self._extract_dosage(item)
            frequency = self._parse_frequency(item_lower)
            timing = self._parse_timing(item_lower)
            duration = self._parse_duration(item_lower)
            
            # Build natural instruction
            instruction_parts = []
            
            # Header with medicine name
            instruction_parts.append(f"**{idx}. {medicine_name}**")
            
            # Dosage and frequency in natural language
            if dosage and frequency:
                instruction_parts.append(f"\n💊 **How to take:** Take {dosage} {frequency['text']}\n")
            elif dosage:
                instruction_parts.append(f"\n💊 **How to take:** Take {dosage} as prescribed\n")
            
            # Timing
            if timing:
                instruction_parts.append(f"\n🕐 **When:** {timing}\n")
            
            # Duration
            if duration:
                instruction_parts.append(f"\n📅 **For how long:** {duration}")
            
            # Special notes based on medicine type
            special_note = self._get_special_instructions(medicine_name, item_lower)
            if special_note:
                instruction_parts.append(f"\n⚠️ **Note:** {special_note}")
            
            instructions.append("".join(instruction_parts))
        
        # Combine all instructions
        result = "\n\n".join(instructions)
        
        # Add general advice
        result += "\n\n---\n\n**General Reminders:**\n"
        result += "• Set reminders on your phone so you don't miss doses\n"
        result += "• Complete the full course even if you feel better\n"
        result += "• Store medicines in a cool, dry place away from children\n"
        result += "• If you experience any side effects, contact your doctor immediately"
        
        return result
    def _generate_natural_instructions(self, prescription_items: List[str]) -> str:
        """
        Generate concise, formal instructions (UPDATED FOR BREVITY)
        """
        logger.info("Generating natural language instructions")
        
        instructions = []
        
        for idx, item in enumerate(prescription_items, 1):
            item_lower = item.lower()
            
            # Parse medicine name and dosage
            medicine_name = self._extract_medicine_name(item)
            dosage = self._extract_dosage(item)
            frequency = self._parse_frequency(item_lower)
            timing = self._parse_timing(item_lower)
            duration = self._parse_duration(item_lower)
            
            # Build concise instruction
            instruction_parts = [f"**{idx}. {medicine_name}**"]
            
            # Dosage and frequency
            if dosage and frequency:
                instruction_parts.append(f"• **Dosage:** {dosage} {frequency['text']}")
            elif dosage:
                instruction_parts.append(f"• **Dosage:** {dosage} as prescribed")
            
            # Timing (shortened)
            if timing:
                instruction_parts.append(f"• **Timing:** {timing}")
            
            # Duration (shortened)
            if duration:
                instruction_parts.append(f"• **Duration:** {duration}")
            
            # Special notes (one-liner)
            special_note = self._get_special_instructions(medicine_name, item_lower)
            if special_note:
                instruction_parts.append(f"• **Note:** {special_note}")
            
            instructions.append("\n".join(instruction_parts))
        
        # Combine all instructions
        result = "\n\n".join(instructions)
        
        # Shorter general advice
        result += "\n\n**⚠️ Important:**\n"
        result += "• Complete full course even if symptoms improve\n"
        result += "• Take at same time daily for best results\n"
        result += "• Contact your doctor if side effects occur"
        
        return result

    def _extract_medicine_name(self, item: str) -> str:
        """Extract clean medicine name"""
        # Remove dosage information
        name = re.sub(r'\d+\s*(mg|ml|g|mcg|%|tablet|cap|capsule|syrup)', '', item, flags=re.IGNORECASE)
        # Remove frequency patterns
        name = re.sub(r'(take|tablet|capsule|OD|BD|TDS|QID|\d+\s*times)', '', name, flags=re.IGNORECASE)
        # Remove dashes and extra spaces
        name = re.sub(r'\s*[-–—]\s*', ' ', name)
        return name.strip()
    
    def _extract_dosage(self, item: str) -> Optional[str]:
        """Extract dosage in natural language"""
        # Look for dosage patterns
        patterns = [
            (r'(\d+)\s*mg', lambda m: f"{m.group(1)}mg"),
            (r'(\d+)\s*ml', lambda m: f"{m.group(1)}ml"),
            (r'(\d+)\s*g\b', lambda m: f"{m.group(1)}g"),
            (r'(\d+)\s*mcg', lambda m: f"{m.group(1)}mcg"),
            (r'(\d+)\s*%', lambda m: f"{m.group(1)}%"),
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, item, re.IGNORECASE)
            if match:
                dosage_value = formatter(match)
                
                # Check if it mentions tablets/capsules
                if re.search(r'(\d+)\s*(tablet|cap|capsule)', item, re.IGNORECASE):
                    tab_match = re.search(r'(\d+)\s*(tablet|cap|capsule)', item, re.IGNORECASE)
                    return f"{tab_match.group(1)} {tab_match.group(2)} of {dosage_value}"
                else:
                    return f"one dose of {dosage_value}"
        
        # Fallback: just mention tablet/capsule if found
        if re.search(r'(\d+)\s*(tablet|cap|capsule)', item, re.IGNORECASE):
            match = re.search(r'(\d+)\s*(tablet|cap|capsule)', item, re.IGNORECASE)
            return f"{match.group(1)} {match.group(2)}"
        
        return None
    
    def _parse_frequency(self, item_lower: str) -> Optional[Dict]:
        """Parse frequency into natural language"""
        frequency_map = {
            'qid': {'text': 'four times daily', 'times': 4},
            'four times': {'text': 'four times daily', 'times': 4},
            'tds': {'text': 'three times daily (morning, afternoon, and night)', 'times': 3},
            'three times': {'text': 'three times daily', 'times': 3},
            'thrice': {'text': 'three times daily', 'times': 3},
            'bd': {'text': 'twice daily (morning and night)', 'times': 2},
            'twice': {'text': 'twice daily', 'times': 2},
            'od': {'text': 'once daily', 'times': 1},
            'once': {'text': 'once daily', 'times': 1},
            'daily': {'text': 'once daily', 'times': 1},
        }
        
        for key, value in frequency_map.items():
            if key in item_lower:
                return value
        
        return None
    
    def _parse_timing(self, item_lower: str) -> Optional[str]:
        """Parse timing into SHORT natural language"""
        if 'before food' in item_lower or 'empty stomach' in item_lower or 'before meal' in item_lower:
            return "30 min before meals (empty stomach)"
        elif 'after food' in item_lower or 'after meal' in item_lower:
            return "After meals"
        elif 'with food' in item_lower or 'with meal' in item_lower:
            return "With meals"
        elif 'morning' in item_lower and 'night' in item_lower:
            return "Morning and bedtime"
        elif 'morning' in item_lower:
            return "Morning"
        elif 'night' in item_lower or 'bedtime' in item_lower:
            return "Bedtime"
        elif 'evening' in item_lower:
            return "Evening"
        else:
            return "As directed"
    
    def _parse_duration(self, item_lower: str) -> Optional[str]:
        """Parse duration into SHORT natural language"""
        duration_patterns = [
            (r'(\d+)\s*day', lambda m: f"{m.group(1)} days"),
            (r'(\d+)\s*week', lambda m: f"{m.group(1)} weeks"),
            (r'(\d+)\s*month', lambda m: f"{m.group(1)} months"),
        ]
        
        for pattern, formatter in duration_patterns:
            match = re.search(pattern, item_lower)
            if match:
                return formatter(match)
        
        return "As prescribed"
    
    def _get_special_instructions(self, medicine_name: str, item_lower: str) -> Optional[str]:
        """Generate SHORT special instructions"""
        medicine_lower = medicine_name.lower()
        
        # Shortened medicine-specific advice
        if 'paracetamol' in medicine_lower or 'acetaminophen' in medicine_lower:
            return "Max 4 doses/day"
        elif 'amoxicillin' in medicine_lower or 'antibiotic' in item_lower:
            return "Complete full course, don't skip"
        elif 'cetirizine' in medicine_lower or 'allergy' in item_lower:
            return "May cause drowsiness"
        elif 'omeprazole' in medicine_lower or 'pantoprazole' in medicine_lower:
            return "Take on empty stomach"
        elif 'metformin' in medicine_lower:
            return "Take with food"
        elif 'aspirin' in medicine_lower or 'ibuprofen' in medicine_lower:
            return "Take with food to avoid stomach upset"
        
        return None
    
    def extract_intent(self, user_message: str, context: Dict) -> str:
        """Use orchestration model to understand user intent"""
        messages = [
            {
                "role": "system",
                "content": "You are a healthcare assistant intent classifier. Respond with ONLY the intent category, nothing else."
            },
            {
                "role": "user",
                "content": f"""Current conversation state: {context.get('current_state', 'initial')}
User message: "{user_message}"

Classify the user's intent into ONE of these categories:
- book_appointment
- get_instructions
- manage_profile
- go_home
- provide_info (providing requested information)

Respond with ONLY the intent category."""
            }
        ]
        
        response = self.get_orchestration_response(messages, max_tokens=50, temperature=0.2, retries=1)
        return response.lower().strip() if response else "provide_info"
    
    def generate_conversational_response(
    self, 
    user_message: str, 
    context: Dict,
    instruction: str = None
) -> str:
        """Generate natural conversational response (UPDATED FOR BETTER DIAGNOSIS HANDLING)"""
        state = context.get('current_state', 'initial')
        history = context.get('history', [])
        
        # Check if user is asking for diagnosis/medical advice - IMPROVED RESPONSE
        diagnosis_keywords = ['what disease', 'do i have', 'am i sick', 'diagnose', 
                            'what\'s wrong with', 'is it serious', 'symptoms mean',
                            'what condition', 'medical advice','prescibe','treatment for',
                            'what illness','what to do about','should i do if','how to cure',
                            'is it dangerous','is it normal','should i worry about',
                            'could it be','what could be causing','why do i need medication']
        
        if any(keyword in user_message.lower() for keyword in diagnosis_keywords):
            return ("I cannot provide medical diagnosis or interpret symptoms. "
                "For accurate medical advice, I recommend booking an appointment with a doctor at our hospital. "
                "Would you like me to help you book an appointment?")
        
        # Build conversation history
        history_text = "\n".join([
            f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}"
            for i, msg in enumerate(history[-6:])
        ])
        
        base_instruction = instruction or "Continue the conversation naturally."
        
        messages = [
            {
                "role": "system",
                "content": """You are MediMitra, a healthcare assistant for a hospital. You can ONLY:
    1. Help book appointments at THIS hospital
    2. Provide medicine/test instructions from prescriptions
    3. Answer questions about test preparation

    STRICT RULES:
    - NEVER diagnose or provide medical advice
    - If asked about symptoms/diagnosis, ask to book an appointment instead
    - If user says "book appointment", acknowledge and say you'll help them book
    - Keep responses SHORT (1-2 sentences max)
    - Be professional and helpful"""
            },
            {
                "role": "user",
                "content": f"""Conversation history:
    {history_text}

    Current state: {state}
    User's latest message: "{user_message}"

    Task: {base_instruction}"""
            }
        ]
        
        response = self.get_orchestration_response(messages, max_tokens=100, temperature=0.7, retries=1)
        
        if not response:
            return "I'm having trouble processing that right now. Could you please rephrase or type 'home' to return to the main menu?"
        
        return response


# Global instance
llm_service = LLMService()
