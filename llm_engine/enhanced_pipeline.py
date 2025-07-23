"""
Enhanced pipeline that combines C++ audio processing with ASR transcription
"""
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_bridge import load_audio, detect_voice_segments, diarize_speakers, get_audio_info

# Use smart ASR selector for best available option
from llm_engine.modules.asr_smart import transcribe_audio_smart as transcribe_audio

class VoicelinkAudioPipeline:
    """Complete audio processing pipeline for Voicelink"""
    
    def __init__(self):
        print("🎵 Initializing Voicelink Audio Pipeline...")
    
    def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Complete processing pipeline: Audio → VAD → Diarization → ASR → Results
        
        Args:
            file_path: Path to audio file (WAV/MP3)
            
        Returns:
            Complete analysis results
        """
        print(f"🎧 Processing audio file: {file_path}")
        
        try:
            # Step 1: Load audio
            audio_data = load_audio(file_path)
            audio_info = get_audio_info(audio_data)
            print(f"📊 Audio loaded: {audio_info}")
            
            # Step 2: Voice Activity Detection
            voice_segments = detect_voice_segments(audio_data)
            print(f"🗣️  Detected {len(voice_segments)} voice segments")
            
            # Step 3: Speaker Diarization
            speaker_segments = diarize_speakers(audio_data)
            print(f"👥 Detected {len(speaker_segments)} speaker segments")
            
            # Step 4: Speech-to-Text Transcription
            transcripts = transcribe_audio(audio_data, voice_segments, speaker_segments)
            print(f"📝 Generated {len(transcripts)} transcripts")
            
            # Step 5: Compile results
            results = {
                "status": "success",
                "audio_info": audio_info,
                "voice_segments": self._serialize_segments(voice_segments),
                "speaker_segments": self._serialize_speakers(speaker_segments), 
                "transcripts": transcripts,
                "summary": {
                    "total_duration": audio_info.get("duration_seconds", 0),
                    "speech_segments": len(voice_segments),
                    "speakers_detected": len(set(s.speaker_id for s in speaker_segments)),
                    "transcribed_segments": len(transcripts)
                }
            }
            
            print("✅ Audio processing pipeline completed successfully")
            return results
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path
            }
    
    def _serialize_segments(self, segments) -> List[Dict[str, Any]]:
        """Convert C++ segments to serializable format"""
        return [
            {
                "start_sample": seg.start_sample,
                "end_sample": seg.end_sample,
                "start_time": seg.start_sample / 44100,  # TODO: Use actual sample rate
                "end_time": seg.end_sample / 44100
            }
            for seg in segments
        ]
    
    def _serialize_speakers(self, speakers) -> List[Dict[str, Any]]:
        """Convert C++ speaker segments to serializable format"""
        return [
            {
                "start_sample": spk.start_sample,
                "end_sample": spk.end_sample,
                "speaker_id": spk.speaker_id,
                "start_time": spk.start_sample / 44100,  # TODO: Use actual sample rate
                "end_time": spk.end_sample / 44100
            }
            for spk in speakers
        ]

# Global pipeline instance
pipeline = VoicelinkAudioPipeline()

def process_audio(file_path: str) -> Dict[str, Any]:
    """Convenience function for processing audio files"""
    return pipeline.process_audio_file(file_path)
