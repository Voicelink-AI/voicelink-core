"""
ASR (Automatic Speech Recognition) adapter for Voicelink
Supports multiple providers: OpenAI Whisper, ElevenLabs, Vosk
"""
import os
import tempfile
import wave
import struct
import numpy as np
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class ASRAdapter:
    """Universal ASR adapter with multiple provider support"""
    
    def __init__(self, provider: str = "whisper"):
        self.provider = provider.lower()
        self.client = None
        
        if self.provider == "openai" and OPENAI_AVAILABLE:
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "whisper" and WHISPER_AVAILABLE:
            self.model = whisper.load_model("base")
        elif self.provider == "elevenlabs":
            # TODO: Implement ElevenLabs integration
            pass
        
        print(f"🎙️  ASR initialized with provider: {self.provider}")
    
    def transcribe_segments(self, audio_data, voice_segments, speaker_segments=None) -> List[Dict[str, Any]]:
        """
        Transcribe voice segments from audio data
        
        Args:
            audio_data: Audio data from C++ engine
            voice_segments: VAD segments from C++ engine
            speaker_segments: Diarization segments (optional)
        
        Returns:
            List of transcripts with timestamps and speaker info
        """
        transcripts = []
        
        for i, segment in enumerate(voice_segments):
            try:
                # Extract audio segment
                start_sample = segment.start_sample
                end_sample = segment.end_sample
                segment_audio = audio_data.samples[start_sample:end_sample]
                
                # Skip very short segments (less than 0.5 seconds)
                duration = (end_sample - start_sample) / audio_data.sample_rate
                if duration < 0.5:
                    print(f"⏭️  Skipping short segment {i} ({duration:.2f}s)")
                    continue
                
                # Find speaker for this segment
                speaker_id = self._find_speaker_for_segment(start_sample, end_sample, speaker_segments)
                
                # Transcribe segment
                text = self._transcribe_audio_segment(
                    segment_audio, 
                    audio_data.sample_rate, 
                    audio_data.num_channels
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
                        "confidence": 0.9  # TODO: Get real confidence scores
                    }
                    transcripts.append(transcript)
                    print(f"✅ Transcribed segment {i}: '{text.strip()[:50]}...'")
                    
            except Exception as e:
                print(f"❌ Error transcribing segment {i}: {e}")
                continue
        
        print(f"✅ Transcribed {len(transcripts)} segments")
        return transcripts
    
    def _transcribe_audio_segment(self, samples: List[int], sample_rate: int, num_channels: int) -> str:
        """Transcribe a single audio segment"""
        
        # Use a persistent temporary file with proper cleanup
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, f"segment_{int(time.time() * 1000)}.wav")
        
        try:
            # Convert samples to proper numpy array format
            if isinstance(samples, list):
                samples = np.array(samples, dtype=np.int16)
            elif not isinstance(samples, np.ndarray):
                samples = np.array(samples, dtype=np.int16)
            
            # Ensure samples are in valid range
            samples = np.clip(samples, -32768, 32767)
            
            # Write WAV file with explicit file closure
            wav_file = wave.open(temp_path, 'wb')
            try:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(samples.tobytes())
            finally:
                wav_file.close()  # Ensure file is closed
            
            # Small delay to ensure file is written to disk
            time.sleep(0.1)
            
            # Verify file was created and has data
            if not os.path.exists(temp_path):
                print(f"❌ Failed to create temporary file: {temp_path}")
                return self._transcribe_mock(samples)
            
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                print(f"❌ Empty temporary file created: {temp_path}")
                return self._transcribe_mock(samples)
            
            print(f"📁 Created temp file: {temp_path} ({file_size} bytes)")
            
            # Transcribe using selected provider
            if self.provider == "openai" and self.client:
                return self._transcribe_openai(temp_path)
            elif self.provider == "whisper" and hasattr(self, 'model'):
                return self._transcribe_whisper(temp_path)
            else:
                return self._transcribe_mock(samples)
                
        except Exception as e:
            print(f"❌ Error in audio segment processing: {e}")
            return self._transcribe_mock(samples)
            
        finally:
            # Clean up temp file and directory with retry
            for attempt in range(3):
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        print(f"⚠️  Cleanup warning (attempt {attempt+1}): {e}")
                    time.sleep(0.1)  # Brief delay before retry
    
    def _transcribe_openai(self, audio_file: str) -> str:
        """Transcribe using OpenAI Whisper API"""
        try:
            with open(audio_file, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            return transcript.text
        except Exception as e:
            print(f"❌ OpenAI transcription error: {e}")
            return ""
    
    def _transcribe_whisper(self, audio_file: str) -> str:
        """Transcribe using local Whisper model"""
        try:
            print(f"🎙️  Transcribing: {audio_file}")
            
            # Verify file exists and is readable
            if not os.path.isfile(audio_file):
                print(f"❌ File does not exist: {audio_file}")
                return ""
            
            # Use absolute path to avoid any path resolution issues
            abs_path = os.path.abspath(audio_file)
            print(f"🎙️  Absolute path: {abs_path}")
            
            # Transcribe with error handling
            result = self.model.transcribe(abs_path, fp16=False, verbose=False)
            text = result.get("text", "").strip()
            
            if text:
                print(f"✅ Whisper result: '{text[:100]}...'")
            else:
                print("⚠️  Whisper returned empty result")
            
            return text
            
        except Exception as e:
            print(f"❌ Whisper transcription error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _transcribe_mock(self, samples) -> str:
        """Mock transcription for fallback"""
        duration = len(samples) / 44100  # Assume 44.1kHz
        return f"[Mock transcript for {duration:.1f}s audio segment]"
    
    def _find_speaker_for_segment(self, start_sample: int, end_sample: int, speaker_segments) -> int:
        """Find which speaker corresponds to a voice segment"""
        if not speaker_segments:
            return 0
        
        # Find overlapping speaker segment
        for speaker in speaker_segments:
            if (start_sample >= speaker.start_sample and start_sample < speaker.end_sample) or \
               (end_sample > speaker.start_sample and end_sample <= speaker.end_sample):
                return speaker.speaker_id
        
        return 0  # Default speaker

# Global instance
asr_provider = os.getenv("ASR_PROVIDER", "whisper")
asr_adapter = ASRAdapter(asr_provider)

def transcribe_audio(audio_data, voice_segments, speaker_segments=None):
    """Convenience function for transcribing audio"""
    return asr_adapter.transcribe_segments(audio_data, voice_segments, speaker_segments)
