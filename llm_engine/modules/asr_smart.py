"""
Smart ASR adapter that tries multiple providers in order of preference
"""
import os
from typing import List, Dict, Any

# Try to load from .env file with better parsing
def load_env_file():
    try:
        from pathlib import Path
        env_file = Path(__file__).parent.parent.parent / ".env"
        print(f"🔍 Looking for .env file at: {env_file}")
        
        if env_file.exists():
            print(f"✅ Found .env file")
            with open(env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        # Split only on first =
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        os.environ[key] = value
                        print(f"  Loaded: {key}={value[:8]}...")
        else:
            print(f"⚠️  .env file not found")
    except Exception as e:
        print(f"⚠️  Error loading .env file: {e}")

# Load environment variables
load_env_file()

def get_best_asr_adapter():
    """Get the best available ASR adapter"""
    
    # Debug: Print what we find
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"🔍 Environment check:")
    print(f"  ELEVENLABS_API_KEY: {'✅ Found' if elevenlabs_key else '❌ Not found'}")
    print(f"  OPENAI_API_KEY: {'✅ Found' if openai_key else '❌ Not found'}")
    
    # Try ElevenLabs first (aligns with your plan and has good diarization)
    if elevenlabs_key:
        try:
            from llm_engine.modules.asr_elevenlabs import transcribe_audio_elevenlabs
            print("🎙️  Using ElevenLabs ASR (API with diarization)")
            return transcribe_audio_elevenlabs
        except Exception as e:
            print(f"⚠️  ElevenLabs failed: {e}")
    
    # Try OpenAI Whisper API
    if openai_key:
        try:
            from llm_engine.modules.asr_adapter import transcribe_audio
            os.environ["ASR_PROVIDER"] = "openai"
            print("🎙️  Using OpenAI Whisper API")
            return transcribe_audio
        except Exception as e:
            print(f"⚠️  OpenAI failed: {e}")
    
    # Fallback to mock
    print("🎙️  No API keys found - using mock ASR for development")
    print("💡 To get real transcription, set ELEVENLABS_API_KEY or OPENAI_API_KEY")
    
    from llm_engine.modules.asr_simple import transcribe_audio_simple
    return transcribe_audio_simple

# Get the best available transcription function
transcribe_audio_smart = get_best_asr_adapter()
