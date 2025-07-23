"""
Configuration for Voicelink API
"""
from dotenv import load_dotenv
import os
from typing import Dict, Any

load_dotenv()

class Config:
    # App info
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    BUILD_ID = os.getenv("BUILD_ID", "VCLNK-9")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Blockchain
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///voicelink.db")
    
    # Audio processing
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "100"))
    SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
    
    # Models
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH")
    
    # LLM settings
    DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    
    # Local LLM (if using)
    LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT")
    LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama2")
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration for the engine"""
        config = {}
        
        if cls.OPENAI_API_KEY:
            config["openai"] = {
                "api_key": cls.OPENAI_API_KEY
            }
        
        if cls.GOOGLE_CLOUD_PROJECT:
            config["vertex_ai"] = {
                "project_id": cls.GOOGLE_CLOUD_PROJECT,
                "location": cls.GOOGLE_CLOUD_LOCATION,
                "credentials_path": cls.GOOGLE_APPLICATION_CREDENTIALS
            }
        
        if cls.LOCAL_LLM_ENDPOINT:
            config["local_llm"] = {
                "endpoint": cls.LOCAL_LLM_ENDPOINT,
                "model_name": cls.LOCAL_LLM_MODEL
            }
        
        return config
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration"""
        required_keys = []
        
        # Check if we have at least one LLM provider
        if not any([cls.OPENAI_API_KEY, cls.GOOGLE_CLOUD_PROJECT, cls.LOCAL_LLM_ENDPOINT]):
            required_keys.append("At least one LLM provider (OpenAI, Google Cloud, or Local)")
        
        if required_keys:
            raise ValueError(f"Missing required configuration: {', '.join(required_keys)}")
        
        return True