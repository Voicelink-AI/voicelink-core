from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # App configuration
    BUILD_ID = os.getenv("BUILD_ID", "VCLNK-9")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    
    # API Keys
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    
    # Cloud configuration
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Local LLM configuration
    LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434")
    LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama2")
    
    # Model configuration
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH")
    
    # Audio processing
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "100"))
    SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
    
    # LLM settings
    DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    
    @classmethod
    def get_llm_config(cls) -> dict:
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
        
        config["local_llm"] = {
            "endpoint": cls.LOCAL_LLM_ENDPOINT,
            "model_name": cls.LOCAL_LLM_MODEL
        }
        
        return config