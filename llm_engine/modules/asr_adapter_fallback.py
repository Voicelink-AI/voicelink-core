"""
Fallback ASR adapter that works without FFmpeg
Uses direct numpy arrays instead of file-based transcription
"""
import os
import numpy as np
from typing import List, Dict, Any
import librosa
import soundfile as sf

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class FallbackASRAdapter:
    """ASR adapter that works without FFmpeg dependencies"""
    
    def __init__(self, provider: str = "whisper"):
        self.provider = provider.lower()
        
        if self.provider == "whisper" and WHISPER_AVAILABLE:
            self.model = whisper.load_model("base")
        
        print(f"🎙️  Fallback ASR initialized with provider: {self.provider}")
    
    def transcribe_segments(self, audio_data, voice_segments, speaker_segments=None) -> List[Dict[str, Any]]:
        """Transcribe voice segments from audio data"""
        transcripts = []
        
        for i, segment in enumerate(voice_segments):
            try:
                # Extract audio segment
                start_sample = segment.start_sample
                end_sample = segment.end_sample
                segment_audio = audio_data.samples[start_sample:end_sample]
                
                # Skip very short segments
                duration = (end_sample - start_sample) / audio_data.sample_rate
                if duration < 0.5:
                    print(f"⏭️  Skipping short segment {i} ({duration:.2f}s)")
                    continue
                
                # Find speaker for this segment
                speaker_id = self._find_speaker_for_segment(start_sample, end_sample, speaker_segments)
                
                # Transcribe segment using numpy array directly
                text = self._transcribe_numpy_audio(
                    segment_audio, 
                    audio_data.sample_rate
                )
                
                if text and text.strip():
                    transcript = {
                        "segment_id": i,
                        "start_sample": start_sample,
                        "end_sample": end_sample,
                        "start_time": start_sample / audio_data.sample_rate,
                        "end_time": end_sample / audio_data.sample_rate,
                        "speaker_id": speaker_id,
                        "text": text.strip(),
                        "confidence": 0.9
                    }
                    transcripts.append(transcript)
                    print(f"✅ Transcribed segment {i}: '{text.strip()[:50]}...'")
                    
            except Exception as e:
                print(f"❌ Error transcribing segment {i}: {e}")
                continue
        
        print(f"✅ Transcribed {len(transcripts)} segments")
        return transcripts
    
    def _transcribe_numpy_audio(self, samples: List[int], sample_rate: int) -> str:
        """Transcribe audio from numpy array without file I/O"""
        try:
            # Convert to float32 array normalized to [-1, 1]
            if isinstance(samples, list):
                samples = np.array(samples, dtype=np.int16)
            
            # Convert from int16 to float32 and normalize
            audio_float = samples.astype(np.float32) / 32768.0
            
            # Resample to 16kHz if needed (Whisper expects 16kHz)
            if sample_rate != 16000:
                # Simple resampling (you might want to use librosa.resample for better quality)
                target_length = int(len(audio_float) * 16000 / sample_rate)
                audio_float = np.interp(
                    np.linspace(0, len(audio_float), target_length),
                    np.arange(len(audio_float)),
                    audio_float
                )
            
            print(f"🎙️  Transcribing numpy array: {len(audio_float)} samples at 16kHz")
            
            # Use Whisper directly with the audio array
            if self.provider == "whisper" and hasattr(self, 'model'):
                result = self.model.transcribe(audio_float, fp16=False, verbose=False)
                text = result.get("text", "").strip()
                
                if text:
                    print(f"✅ Whisper result: '{text[:100]}...'")
                else:
                    print("⚠️  Whisper returned empty result")
                
                return text
            else:
                return self._transcribe_mock(samples)
                
        except Exception as e:
            print(f"❌ Numpy transcription error: {e}")
            return self._transcribe_mock(samples)
    
    def _transcribe_mock(self, samples) -> str:
        """Mock transcription for fallback"""
        duration = len(samples) / 44100
        return f"[Mock transcript for {duration:.1f}s audio segment]"
    
    def _find_speaker_for_segment(self, start_sample: int, end_sample: int, speaker_segments) -> int:
        """Find which speaker corresponds to a voice segment"""
        if not speaker_segments:
            return 0
        
        for speaker in speaker_segments:
            if (start_sample >= speaker.start_sample and start_sample < speaker.end_sample) or \
               (end_sample > speaker.start_sample and end_sample <= speaker.end_sample):
                return speaker.speaker_id
        
        return 0

# Global instance for fallback ASR
fallback_asr = FallbackASRAdapter()

def transcribe_audio_fallback(audio_data, voice_segments, speaker_segments=None):
    """Fallback transcription function"""
    return fallback_asr.transcribe_segments(audio_data, voice_segments, speaker_segments)
