"""
Bridge module to integrate C++ audio engine with Python backend
"""
import os
import sys
import traceback
from typing import Dict, Any, List, Optional

# Add the build directory to Python path
build_paths = [
    os.path.join(os.path.dirname(__file__), '..', 'build', 'bindings', 'Release'),
    os.path.join(os.path.dirname(__file__), '..', 'build', 'bindings', 'Debug'),
    os.path.join(os.path.dirname(__file__), '..', 'build', 'bindings'),
    os.path.join(os.path.dirname(__file__), '..', 'build')
]

for build_path in build_paths:
    if os.path.exists(build_path):
        sys.path.insert(0, build_path)

try:
    import audio_engine_py  # type: ignore                              
    AUDIO_ENGINE_AVAILABLE = True
    print("✅ C++ audio engine loaded successfully")
except ImportError as e:
    AUDIO_ENGINE_AVAILABLE = False
    print(f"⚠️  Warning: C++ audio engine not available ({e})")
    print("📝 Using mock mode for audio processing")
    print("💡 To enable C++ engine, build the project with: cmake --build build --config Release")

class AudioProcessor:
    """Unified interface for audio processing"""
    
    def __init__(self):
        if AUDIO_ENGINE_AVAILABLE:
            self.engine = audio_engine_py.AudioEngine()
            self.use_real_engine = True
        else:
            self.engine = None
            self.use_real_engine = False
    
    def load_audio(self, file_path: str) -> Optional[Any]:
        """Load audio file (WAV or MP3)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        if not self.use_real_engine:
            return self._mock_load_audio(file_path)
        
        try:
            if file_path.lower().endswith('.mp3'):
                return self.engine.load_mp3(file_path)
            else:
                return self.engine.load_wav(file_path)
        except Exception as e:
            print(f"Error loading audio with C++ engine: {e}")
            print("Falling back to mock mode")
            return self._mock_load_audio(file_path)
    
    def detect_voice_segments(self, audio_data: Any) -> List[Any]:
        """Detect voice activity segments"""
        if not self.use_real_engine:
            return self._mock_voice_segments(audio_data)
        
        try:
            return self.engine.detect_voice_segments(audio_data)
        except Exception as e:
            print(f"Error detecting voice segments: {e}")
            return self._mock_voice_segments(audio_data)
    
    def diarize_speakers(self, audio_data: Any) -> List[Any]:
        """Perform speaker diarization"""
        if not self.use_real_engine:
            return self._mock_diarization(audio_data)
        
        try:
            return self.engine.diarize(audio_data)
        except Exception as e:
            print(f"Error performing diarization: {e}")
            return self._mock_diarization(audio_data)
    
    def get_audio_info(self, audio_data: Any) -> Dict[str, Any]:
        """Get audio information"""
        if hasattr(audio_data, 'sample_rate'):
            duration = len(audio_data.samples) / audio_data.sample_rate if hasattr(audio_data, 'samples') else 0
            return {
                "sample_rate": audio_data.sample_rate,
                "num_channels": getattr(audio_data, 'num_channels', 1),
                "duration_seconds": duration,
                "total_samples": len(audio_data.samples) if hasattr(audio_data, 'samples') else 0
            }
        return {
            "sample_rate": 44100,
            "num_channels": 1,
            "duration_seconds": 1.0,
            "total_samples": 44100
        }
    
    def _mock_load_audio(self, file_path: str) -> Any:
        """Mock audio loading for fallback"""
        print(f"Mock: Loading {file_path}")
        
        # Simulate real file reading
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Return mock audio data structure
        return type('MockAudioData', (), {
            'sample_rate': 44100,
            'num_channels': 1,
            'samples': [0] * 44100,  # 1 second of silence
            'file_path': file_path
        })()
    
    def _mock_voice_segments(self, audio_data: Any) -> List[Any]:
        """Mock voice activity detection"""
        print("Mock: Detecting voice segments")
        duration = len(audio_data.samples) if hasattr(audio_data, 'samples') else 44100
        
        # Create realistic voice segments (3 segments with gaps)
        segments = []
        segment_length = duration // 4
        
        for i in range(3):
            start = i * segment_length + (i * 1000)  # Add small gaps
            end = start + segment_length
            if end <= duration:
                segments.append(type('MockSegment', (), {
                    'start_sample': start,
                    'end_sample': end
                })())
        
        return segments
    
    def _mock_diarization(self, audio_data: Any) -> List[Any]:
        """Mock speaker diarization"""
        print("Mock: Performing diarization")
        duration = len(audio_data.samples) if hasattr(audio_data, 'samples') else 44100
        
        # Create realistic speaker segments (2 speakers alternating)
        speakers = []
        segment_length = duration // 6
        
        for i in range(6):
            start = i * segment_length
            end = start + segment_length
            speaker_id = i % 2  # Alternate between speaker 0 and 1
            
            if end <= duration:
                speakers.append(type('MockSpeaker', (), {
                    'start_sample': start,
                    'end_sample': end,
                    'speaker_id': speaker_id
                })())
        
        return speakers

# Convenience functions for backward compatibility
def load_audio(file_path: str) -> Optional[Any]:
    """Load audio file using the global processor"""
    return audio_processor.load_audio(file_path)

def detect_voice_segments(audio_data: Any) -> List[Any]:
    """Detect voice segments using the global processor"""
    return audio_processor.detect_voice_segments(audio_data)

def diarize_speakers(audio_data: Any) -> List[Any]:
    """Perform speaker diarization using the global processor"""
    return audio_processor.diarize_speakers(audio_data)

def get_audio_info(audio_data: Any) -> Dict[str, Any]:
    """Get audio information using the global processor"""
    return audio_processor.get_audio_info(audio_data)

# Global instance
audio_processor = AudioProcessor()
