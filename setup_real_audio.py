"""
Setup script for real audio processing capabilities
"""
import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages for real audio processing"""
    print("Installing real audio processing requirements...")
    
    requirements = [
        "openai-whisper",
        "pyannote.audio", 
        "librosa",
        "soundfile",
        "openai",
        "torch",
        "torchaudio"
    ]
    
    for req in requirements:
        print(f"Installing {req}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
            print(f"✅ {req} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {req}: {e}")

def test_imports():
    """Test if all required libraries can be imported"""
    print("\nTesting imports...")
    
    try:
        import whisper
        print("✅ Whisper imported successfully")
    except ImportError as e:
        print(f"❌ Whisper import failed: {e}")
    
    try:
        from pyannote.audio import Pipeline
        print("✅ pyannote.audio imported successfully")
    except ImportError as e:
        print(f"❌ pyannote.audio import failed: {e}")
    
    try:
        import librosa
        print("✅ librosa imported successfully")
    except ImportError as e:
        print(f"❌ librosa import failed: {e}")
    
    try:
        import soundfile
        print("✅ soundfile imported successfully")
    except ImportError as e:
        print(f"❌ soundfile import failed: {e}")
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ openai import failed: {e}")

def setup_environment():
    """Setup environment variables"""
    print("\nSetting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Copying .env.example to .env...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ .env file created")
        print("📝 Please edit .env file and add your API keys:")
        print("   - HUGGINGFACE_TOKEN (from https://huggingface.co/pyannote/speaker-diarization)")
        print("   - OPENAI_API_KEY (from https://platform.openai.com/api-keys)")
    else:
        print("✅ .env file already exists")

def test_whisper():
    """Test Whisper model loading"""
    print("\nTesting Whisper model loading...")
    try:
        import whisper
        model = whisper.load_model("base")
        print("✅ Whisper base model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Whisper model loading failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🎙️  VoiceLink Real Audio Processing Setup")
    print("=" * 50)
    
    # Install requirements
    install_requirements()
    
    # Test imports
    test_imports()
    
    # Setup environment
    setup_environment()
    
    # Test Whisper
    whisper_ok = test_whisper()
    
    print("\n" + "=" * 50)
    print("Setup Summary:")
    print("✅ Requirements installation attempted")
    print("✅ Environment setup completed")
    
    if whisper_ok:
        print("✅ Whisper model test passed")
    else:
        print("❌ Whisper model test failed")
    
    print("\nNext Steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python main_enhanced.py")
    print("3. Upload an audio file to test real processing")
    
    print("\nAPI Keys needed:")
    print("- HUGGINGFACE_TOKEN: https://huggingface.co/pyannote/speaker-diarization")
    print("- OPENAI_API_KEY: https://platform.openai.com/api-keys")

if __name__ == "__main__":
    main()
