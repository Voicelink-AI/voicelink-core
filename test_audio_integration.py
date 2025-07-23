#!/usr/bin/env python3
"""
Quick test to validate C++ audio engine integration
"""

import sys
from pathlib import Path

def test_audio_engine():
    print("🧪 VoiceLink Audio Engine Integration Test")
    print("=" * 50)
    
    try:
        # Try to import the C++ binding
        print("1. Testing C++ audio engine import...")
        try:
            import audio_engine_py
            print("✅ C++ audio engine binding available!")
            
            # Test basic functionality
            engine = audio_engine_py.AudioEngine()
            print("✅ AudioEngine instance created")
            
            return True
            
        except ImportError as e:
            print(f"❌ C++ binding not available: {e}")
            print("   Need to compile with: cmake --build build/")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    print("\n🔧 Audio Engine Status: Mock mode (need to compile C++)")
    return False

def test_python_wrapper():
    print("\n2. Testing Python audio processor wrapper...")
    try:
        from audio_engine.python.audio_processor import AudioProcessor
        processor = AudioProcessor()
        print("✅ Python AudioProcessor initialized")
        
        # Test mock audio processing
        fake_audio_data = processor.load_audio(Path("demo.wav"))
        print(f"✅ Mock audio loaded: {len(fake_audio_data)} samples")
        
        return True
        
    except Exception as e:
        print(f"❌ Python wrapper failed: {e}")
        return False

if __name__ == "__main__":
    print("🎵 VoiceLink Audio Engine Status Check")
    
    cpp_works = test_audio_engine()
    python_works = test_python_wrapper()
    
    print("\n" + "=" * 50)
    if cpp_works and python_works:
        print("🎉 Audio engine fully functional!")
        print("✨ Ready for real audio processing")
    elif python_works:
        print("🟡 Python wrapper works, C++ needs compilation")
        print("📝 Run: cd audio_engine && cmake --build build/")
    else:
        print("❌ Audio engine needs setup")
        
    print("\n🎯 Next Step: Implement ElevenLabs voice integration")
