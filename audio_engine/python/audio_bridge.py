"""
Bridge module to integrate C++ audio engine with Python backend
"""
import os
import sys

# Add the build directory to Python path
build_path = os.path.join(os.path.dirname(__file__), '..', 'build', 'bindings', 'Release')
sys.path.insert(0, build_path)

try:
    import audio_engine_py
    AUDIO_ENGINE_AVAILABLE = True
except ImportError:
    AUDIO_ENGINE_AVAILABLE = False
    print("Warning: C++ audio engine not available, using mock mode")

class AudioProcessor:
    """Unified interface for audio processing"""
    
    def __init__(self):
        if AUDIO_ENGINE_AVAILABLE:
            self.engine = audio_engine_py.AudioEngine()
            self.use_real_engine = True
        else:
            self.engine = None
            self.use_real_engine = False
    
    def load_audio(self, file_path):
        """Load audio file (WAV or MP3)"""
        if not self.use_real_engine:
            return self._mock_load_audio(file_path)
        
        if file_path.lower().endswith('.mp3'):
            return self.engine.load_mp3(file_path)
        else:
            return self.engine.load_wav(file_path)
    
    def detect_voice_segments(self, audio_data):
        """Detect voice activity segments"""
        if not self.use_real_engine:
            return self._mock_voice_segments(audio_data)
        
        return self.engine.detect_voice_segments(audio_data)
    
    def diarize_speakers(self, audio_data):
        """Perform speaker diarization"""
        if not self.use_real_engine:
            return self._mock_diarization(audio_data)
        
        return self.engine.diarize(audio_data)
    
    def _mock_load_audio(self, file_path):
        """Mock audio loading for fallback"""
        print(f"Mock: Loading {file_path}")
        # Return mock audio data structure
        return type('MockAudioData', (), {
            'sample_rate': 44100,
            'num_channels': 1,
            'samples': [0] * 44100  # 1 second of silence
        })()
    
    def _mock_voice_segments(self, audio_data):
        """Mock voice activity detection"""
        print("Mock: Detecting voice segments")
        return [type('MockSegment', (), {
            'start_sample': 0,
            'end_sample': len(audio_data.samples)
        })()]
    
    def _mock_diarization(self, audio_data):
        """Mock speaker diarization"""
        print("Mock: Performing diarization")
        return [type('MockSpeaker', (), {
            'start_sample': 0,
            'end_sample': len(audio_data.samples),
            'speaker_id': 0
        })()]

# Global instance
audio_processor = AudioProcessor()
