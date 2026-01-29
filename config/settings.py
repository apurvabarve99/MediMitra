import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # Hugging Face
    HF_TOKEN = os.getenv("HF_TOKEN")
    MEDICAL_MODEL = os.getenv("MEDICAL_MODEL")
    FALLBACK_MEDICAL_MODEL = os.getenv("FALLBACK_MEDICAL_MODEL")
    ORCHESTRATION_MODEL = os.getenv("ORCHESTRATION_MODEL")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    EMBEDDING_MODEL_SEED = os.getenv("EMBEDDING_MODEL_SEED")
      
    # App
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))
    
    # Business Rules
    APPOINTMENT_START_HOUR = 9
    APPOINTMENT_END_HOUR = 21
    APPOINTMENT_SLOT_MINUTES = 30
    
    # Security Questions
    SECURITY_QUESTIONS = [
        "What is your mother's maiden name?",
        "What was the name of your first pet?",
        "What city were you born in?",
        "What is your favorite book?",
        "What was your childhood nickname?"
    ]
    
    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
settings = Settings()
