"""
Universal audio bridge for the Voicelink Python backend - VAD Optimized
"""
import sys
import os
from pathlib import Path

try:
    from audio_engine.python import audio_engine_py
    AUDIO_ENGINE_AVAILABLE = True
    print("✅ Real C++ audio engine loaded successfully")
except ImportError:
    AUDIO_ENGINE_AVAILABLE = False
    print("⚠️  C++ audio engine not available, using mock mode")

class VoicelinkAudioEngine:
    """
    Universal audio engine interface for Voicelink backend
    Automatically uses real C++ engine if available, otherwise falls back to mock
    """
    
    def __init__(self):
        if AUDIO_ENGINE_AVAILABLE:
            self.engine = audio_engine_py.AudioEngine()
            self.mode = "real"
        else:
            self.engine = None
            self.mode = "mock"
        
        print(f"🎵 Audio Engine initialized in {self.mode} mode")
    
    def load_audio(self, file_path):
        """Load audio file (WAV or MP3)"""
        if self.mode == "real":
            if file_path.lower().endswith('.mp3'):
                return self.engine.load_mp3(file_path)
            else:
                return self.engine.load_wav(file_path)
        else:
            return self._mock_audio_data(file_path)
    
    def detect_voice_segments(self, audio_data, frame_ms=30, threshold=400):
        """Detect voice activity segments - tuned for better capture"""
        if self.mode == "real":
            # Try both methods and pick the best result
            
            # Method 1: Fixed threshold (good for consistent audio)
            fixed_segments = self.engine.detect_voice_segments(audio_data, frame_ms, threshold)
            
            # Method 2: Adaptive threshold (good for varying audio levels)
            adaptive_segments = self.engine.detect_voice_segments_adaptive(audio_data, frame_ms, sensitivity=1.0)
            
            # Pick the method that gives more reasonable segments
            if len(fixed_segments) > 0 and len(adaptive_segments) > 0:
                # Calculate average duration for each method
                fixed_avg_duration = sum((s.end_sample - s.start_sample) / audio_data.sample_rate for s in fixed_segments) / len(fixed_segments)
                adaptive_avg_duration = sum((s.end_sample - s.start_sample) / audio_data.sample_rate for s in adaptive_segments) / len(adaptive_segments)
                
                # Prefer method with longer average segments (more natural speech)
                if fixed_avg_duration > adaptive_avg_duration and fixed_avg_duration > 0.5:
                    print(f"🎙️  Using fixed VAD: {len(fixed_segments)} segments, avg {fixed_avg_duration:.2f}s")
                    return fixed_segments
                else:
                    print(f"🎙️  Using adaptive VAD: {len(adaptive_segments)} segments, avg {adaptive_avg_duration:.2f}s")
                    return adaptive_segments
            elif len(fixed_segments) > 0:
                return fixed_segments
            elif len(adaptive_segments) > 0:
                return adaptive_segments
            else:
                # Fallback: create one segment for the whole audio if no VAD works
                print("⚠️  VAD found no segments, using full audio")
                class FallbackSegment:
                    def __init__(self, start, end):
                        self.start_sample = start
                        self.end_sample = end
                return [FallbackSegment(0, len(audio_data.samples))]
        else:
            return self._mock_voice_segments(audio_data)
    
    def detect_voice_segments_adaptive(self, audio_data, frame_ms=30, sensitivity=1.0):
        """Detect voice segments with adaptive threshold"""
        if self.mode == "real":
            return self.engine.detect_voice_segments_adaptive(audio_data, frame_ms, sensitivity)
        else:
            return self._mock_voice_segments(audio_data)
    
    def diarize_speakers(self, audio_data):
        """Perform speaker diarization"""
        if self.mode == "real":
            return self.engine.diarize(audio_data)
        else:
            return self._mock_speaker_segments(audio_data)
    
    def get_audio_info(self, audio_data):
        """Get audio metadata"""
        if hasattr(audio_data, 'sample_rate'):
            return {
                'sample_rate': audio_data.sample_rate,
                'num_channels': audio_data.num_channels,
                'samples': len(audio_data.samples),
                'duration_seconds': len(audio_data.samples) / audio_data.sample_rate
            }
        else:
            return {'error': 'Invalid audio data'}
    
    def _mock_audio_data(self, file_path):
        """Mock audio data for fallback"""
        class MockAudioData:
            def __init__(self):
                self.sample_rate = 44100
                self.num_channels = 1
                self.samples = [0] * 44100  # 1 second of silence
        
        return MockAudioData()
    
    def _mock_voice_segments(self, audio_data):
        """Mock voice segments for fallback"""
        class MockSegment:
            def __init__(self, start, end):
                self.start_sample = start
                self.end_sample = end
        
        return [MockSegment(0, len(audio_data.samples))]
    
    def _mock_speaker_segments(self, audio_data):
        """Mock speaker segments for fallback"""
        class MockSpeaker:
            def __init__(self, start, end, speaker_id):
                self.start_sample = start
                self.end_sample = end
                self.speaker_id = speaker_id
        
        return [MockSpeaker(0, len(audio_data.samples), 0)]

# Global instance for easy importing
audio_engine = VoicelinkAudioEngine()

# Convenience functions
def load_audio(file_path):
    return audio_engine.load_audio(file_path)

def detect_voice_segments(audio_data, **kwargs):
    return audio_engine.detect_voice_segments(audio_data, **kwargs)

def diarize_speakers(audio_data):
    return audio_engine.diarize_speakers(audio_data)

def get_audio_info(audio_data):
    return audio_engine.get_audio_info(audio_data)
