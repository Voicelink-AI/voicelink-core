"""
ElevenLabs ASR integration for Voicelink - Simplified for better results
"""
import os
import requests
import tempfile
import wave
import numpy as np
import time
from typing import List, Dict, Any

class ElevenLabsASR:
    """ElevenLabs ASR adapter for real voice transcription - Simplified"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1/speech-to-text"
        if not self.api_key:
            print("⚠️  ElevenLabs API key not found. Set ELEVENLABS_API_KEY environment variable.")
        else:
            print("🎙️  ElevenLabs ASR initialized (full-audio transcription)")
    
    def transcribe_segments(self, audio_data, voice_segments, speaker_segments=None) -> List[Dict[str, Any]]:
        """Transcribe using full audio instead of problematic segments"""
        transcripts = []
        
        print("🎙️  Using full audio transcription strategy for better accuracy...")
        
        # Transcribe the entire audio file - this works well!
        result = self._transcribe_with_elevenlabs(
            audio_data.samples,
            audio_data.sample_rate,
            audio_data.num_channels,
            enable_diarization=True,
            improve_accuracy=True
        )
        
        if result and result.get("text", "").strip():
            full_text = result["text"].strip()
            confidence = result.get("language_probability", 0.9)
            
            # Create a single transcript for the entire audio
            transcript = {
                "segment_id": 0,
                "start_sample": 0,
                "end_sample": len(audio_data.samples),
                "start_time": 0.0,
                "end_time": len(audio_data.samples) / audio_data.sample_rate,
                "speaker_id": 0,
                "text": full_text,
                "confidence": confidence,
                "language_code": result.get("language_code", "en"),
                "words": result.get("words", []),
                "transcription_method": "full_audio"
            }
            transcripts.append(transcript)
            print(f"✅ ElevenLabs transcribed full audio: '{full_text}'")
            
            # If we have word-level timestamps, create word-based segments
            words = result.get("words", [])
            if words and len(words) > 1:
                print(f"🔤 Creating {len(words)} word-level segments...")
                
                # Group words into meaningful phrases (every 3-5 words)
                phrase_segments = self._create_phrase_segments(words, audio_data.sample_rate, full_text)
                transcripts.extend(phrase_segments)
        
        print(f"✅ ElevenLabs generated {len(transcripts)} transcripts")
        return transcripts
    
    def _create_phrase_segments(self, words: List[Dict], sample_rate: int, full_text: str) -> List[Dict[str, Any]]:
        """Create phrase-level segments from word timestamps"""
        phrase_segments = []
        current_phrase = []
        phrase_start_time = None
        
        for i, word in enumerate(words):
            if word.get("type") == "word":  # Skip spacing tokens
                if phrase_start_time is None:
                    phrase_start_time = word.get("start", 0)
                
                current_phrase.append(word.get("text", ""))
                
                # End phrase every 4-6 words or at the end
                if len(current_phrase) >= 4 or i == len(words) - 1:
                    phrase_end_time = word.get("end", phrase_start_time + 1)
                    phrase_text = "".join(current_phrase).strip()
                    
                    if phrase_text:
                        segment = {
                            "segment_id": len(phrase_segments) + 1,
                            "start_sample": int(phrase_start_time * sample_rate),
                            "end_sample": int(phrase_end_time * sample_rate),
                            "start_time": phrase_start_time,
                            "end_time": phrase_end_time,
                            "speaker_id": 0,
                            "text": phrase_text,
                            "confidence": 0.9,
                            "transcription_method": "word_grouped"
                        }
                        phrase_segments.append(segment)
                        print(f"  📝 Phrase {len(phrase_segments)}: '{phrase_text}'")
                    
                    # Reset for next phrase
                    current_phrase = []
                    phrase_start_time = None
        
        return phrase_segments
    
    def _transcribe_with_elevenlabs(self, samples: List[int], sample_rate: int, num_channels: int, 
                                   enable_diarization: bool = True, improve_accuracy: bool = True) -> Dict[str, Any]:
        """Transcribe audio using ElevenLabs API with optimized parameters"""
        if not self.api_key:
            print("❌ ElevenLabs API key not found")
            return {}
        
        temp_dir = None
        temp_path = None
        
        try:
            # Create temporary WAV file
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, f"full_audio_{int(time.time() * 1000)}.wav")
            
            # Convert and enhance audio
            enhanced_samples = self._enhance_audio_quality(samples, sample_rate)
            
            # Write enhanced WAV file
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(enhanced_samples.tobytes())
            
            # Verify file was created
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                print(f"❌ Failed to create valid temporary file: {temp_path}")
                return {}
            
            print(f"📁 Created enhanced audio file: {temp_path} ({os.path.getsize(temp_path)} bytes)")
            
            # Prepare optimized API request
            headers = {
                "xi-api-key": self.api_key
            }
            
            # Optimized parameters for full audio transcription
            data = {
                "model_id": "scribe_v1",
                "language_code": "en",
                "tag_audio_events": "true",
                "timestamps_granularity": "word",  # Get word-level timestamps
                "diarize": "true" if enable_diarization else "false",
                "enable_logging": "false",
                "temperature": "0.0"  # Most deterministic results
            }
            
            # Make API request
            with open(temp_path, 'rb') as audio_file:
                files = {"file": audio_file}
                
                print(f"🌐 Calling ElevenLabs API for full audio transcription...")
                response = requests.post(
                    self.base_url, 
                    headers=headers, 
                    data=data,
                    files=files,
                    timeout=60  # Longer timeout for full audio
                )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                print(f"✅ ElevenLabs API success: '{text}'")
                return result
            else:
                print(f"❌ ElevenLabs API error {response.status_code}: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ ElevenLabs transcription error: {e}")
            return {}
        finally:
            # Cleanup temporary files
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
    
    def _enhance_audio_quality(self, samples: List[int], sample_rate: int) -> np.ndarray:
        """Enhance audio quality for better transcription"""
        # Convert to numpy array
        if isinstance(samples, list):
            samples = np.array(samples, dtype=np.int16)
        elif not isinstance(samples, np.ndarray):
            samples = np.array(samples, dtype=np.int16)
        
        # Ensure samples are in valid range
        samples = np.clip(samples, -32768, 32767)
        
        # Simple normalization
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            # Normalize to use 90% of dynamic range
            samples = samples * (29491 / max_val)  # 90% of 32768
            samples = np.clip(samples, -32768, 32767).astype(np.int16)
        
        return samples

# Global instance
elevenlabs_asr = ElevenLabsASR()

def transcribe_audio_elevenlabs(audio_data, voice_segments, speaker_segments=None):
    """ElevenLabs transcription function - simplified for accuracy"""
    return elevenlabs_asr.transcribe_segments(audio_data, voice_segments, speaker_segments)
