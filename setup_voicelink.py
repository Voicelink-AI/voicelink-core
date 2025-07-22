"""
VoiceLink Setup Script

Quick setup script for the VoiceLink development environment.
"""

import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ is required")
        sys.exit(1)
    logger.info(f"Python version OK: {sys.version}")


def install_requirements():
    """Install Python requirements"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        logger.error("Requirements file not found")
        return False
    
    try:
        logger.info("Installing Python dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        logger.info("Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        return False


def create_env_file():
    """Create .env file from example"""
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"
    
    if env_file.exists():
        logger.info(".env file already exists")
        return
    
    env_content = """# VoiceLink Environment Variables

# API Configuration
APP_VERSION=1.0.0
BUILD_ID=VCLNK-DEV
DEBUG=true

# LLM Provider Configuration
LLM_PROVIDER=mock
# Options: mock, openai, vertexai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4

# Google Cloud / VertexAI Configuration (if using VertexAI)
GCP_PROJECT_ID=your_gcp_project_id
GCP_LOCATION=us-central1
VERTEXAI_MODEL=text-bison@001
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# ElevenLabs Configuration (Optional - for voice synthesis)
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Audio Processing Configuration
MAX_AUDIO_SIZE_MB=100
SUPPORTED_AUDIO_FORMATS=wav,mp3,m4a,flac
WHISPER_MODEL=base
VOSK_MODEL_PATH=models/vosk-model

# Database Configuration (Optional - uses mock storage by default)
DATABASE_URL=sqlite:///voicelink.db

# Integration APIs (Optional)
DISCORD_BOT_TOKEN=your_discord_token
GITHUB_TOKEN=your_github_token  
NOTION_API_KEY=your_notion_key
SLACK_BOT_TOKEN=your_slack_token

# Blockchain/Web3 Configuration (Optional)
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/your_key_here
PRIVATE_KEY=your_private_key_here
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    logger.info(".env file created. Please update with your API keys.")


def main():
    """Main setup function"""
    logger.info("Starting VoiceLink setup...")
    
    check_python_version()
    
    if install_requirements():
        logger.info("✅ Python dependencies installed")
    else:
        logger.error("❌ Failed to install dependencies")
        return
    
    create_env_file()
    logger.info("✅ Environment file created")
    
    logger.info("""
🎉 VoiceLink setup complete!

Next steps:
1. Update .env file with your API keys (optional for basic functionality)
2. Start the API server: uvicorn api.main:app --reload
3. Visit http://localhost:8000/docs for API documentation
4. Test with: python orchestrate_voicelink.py

For C++ components (audio engine, code context):
- Install CMake and build tools
- Run: cd audio_engine && mkdir build && cd build && cmake .. && make
- Run: cd code_context && mkdir build && cd build && cmake .. && make

Enjoy building with VoiceLink! 🚀
    """)


if __name__ == "__main__":
    main()
