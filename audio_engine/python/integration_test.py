"""
Test script to verify C++ audio engine integration with Python backend
"""
import sys
import os

# Add the build directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build', 'bindings', 'Release'))

def test_integration():
    """Test the C++ audio engine integration"""
    try:
        import audio_engine_py
        
        print("Testing C++ Audio Engine Integration...")
        
        # Initialize engine
        engine = audio_engine_py.AudioEngine()
        
        # Test with a sample audio file - try multiple locations
        test_files = [
            "sample.wav",
            "../build/sample.wav", 
            "../../sample.wav",
            "../sample.wav"
        ]
        
        data = None
        for file_path in test_files:
            if os.path.exists(file_path):
                try:
                    print(f"Trying to load: {file_path}")
                    if file_path.endswith('.mp3'):
                        data = engine.load_mp3(file_path)
                    else:
                        data = engine.load_wav(file_path)
                    print(f"✅ Successfully loaded: {file_path}")
                    break
                except Exception as e:
                    print(f"❌ Failed to load {file_path}: {e}")
                    continue
        
        if data is None:
            print("❌ No valid audio file found. Please place a sample.wav file in one of these locations:")
            for file_path in test_files:
                print(f"  - {os.path.abspath(file_path)}")
            return False
            
        print(f"Loaded audio: {data.sample_rate}Hz, {data.num_channels} channels, {len(data.samples)} samples")
        
        # Test VAD - explicitly pass parameters
        segments = engine.detect_voice_segments(data, 30, 500)  # frame_ms=30, threshold=500
        print(f"Detected {len(segments)} voice segments")
        for i, seg in enumerate(segments[:5]):  # Show first 5 segments
            print(f"  Segment {i+1}: {seg.start_sample} - {seg.end_sample}")
        
        # Test adaptive VAD
        adaptive_segments = engine.detect_voice_segments_adaptive(data, 30, 2.0)  # frame_ms=30, sensitivity=2.0
        print(f"Detected {len(adaptive_segments)} adaptive voice segments")
        
        # Test diarization
        speakers = engine.diarize(data)
        print(f"Detected {len(speakers)} speaker segments")
        for i, speaker in enumerate(speakers):
            print(f"  Speaker {speaker.speaker_id}: {speaker.start_sample} - {speaker.end_sample}")
        
        print("✅ Integration test passed!")
        return True
            
    except ImportError as e:
        print(f"❌ Failed to import audio_engine_py: {e}")
        print("Make sure the C++ module is compiled and accessible")
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
