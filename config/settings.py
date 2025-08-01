"""
Configuration settings for VoiceLink Core
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_STORAGE_PATH = str(DATA_DIR / "audio")
LOG_DIR = DATA_DIR / "logs"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/voicelink.db")

# Audio Processing Configuration
MAX_AUDIO_FILE_SIZE = int(os.getenv("MAX_AUDIO_FILE_SIZE", "100")) * 1024 * 1024  # 100MB default
SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")

# Audio Engine Configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
PYANNOTE_TOKEN = os.getenv("PYANNOTE_TOKEN")  # For speaker diarization

# Blockchain Configuration
WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# Redis Configuration (for caching)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def ensure_directories():
    """Ensure all required directories exist"""
    try:
        # Create data directories
        DATA_DIR.mkdir(exist_ok=True)
        (DATA_DIR / "audio").mkdir(exist_ok=True)
        (DATA_DIR / "meetings").mkdir(exist_ok=True)
        (DATA_DIR / "transcripts").mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)
        
        # Create audio storage subdirectories
        audio_path = Path(AUDIO_STORAGE_PATH)
        audio_path.mkdir(parents=True, exist_ok=True)
        (audio_path / "temp").mkdir(exist_ok=True)
        (audio_path / "processed").mkdir(exist_ok=True)
        
        print(f"Directories ensured: {DATA_DIR}")
        
    except Exception as e:
        print(f"Failed to create directories: {e}")
        raise

def get_config():
    """Get configuration dictionary"""
    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "audio_storage_path": AUDIO_STORAGE_PATH,
        "api_host": API_HOST,
        "api_port": API_PORT,
        "debug": DEBUG,
        "database_url": DATABASE_URL,
        "max_audio_file_size": MAX_AUDIO_FILE_SIZE,
        "supported_formats": SUPPORTED_AUDIO_FORMATS,
        "log_level": LOG_LEVEL
    }

# Initialize directories on import
if __name__ != "__main__":
    ensure_directories()
