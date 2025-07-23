"""
Enhanced pipeline with code context analysis
"""
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_bridge import load_audio, detect_voice_segments, diarize_speakers, get_audio_info
from llm_engine.modules.asr_smart import transcribe_audio_smart as transcribe_audio
from code_context.python.simple_context_engine import initialize_simple_context_engine, analyze_transcript_simple

class VoicelinkCodeAwarePipeline:
    """Complete audio processing pipeline with code context analysis"""
    
    def __init__(self, repo_path: str = None):
        print("🎵 Initializing Voicelink Code-Aware Pipeline...")
        
        # Initialize code context engine
        self.repo_path = repo_path or str(Path(__file__).parent.parent)
        initialize_simple_context_engine(self.repo_path)
        print(f"📚 Code context initialized for: {self.repo_path}")
    
    def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Complete processing pipeline: Audio → VAD → Diarization → ASR → Code Context → Results
        
        Args:
            file_path: Path to audio file (WAV/MP3)
            
        Returns:
            Complete analysis results with code context
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
            
            # Step 5: Code Context Analysis
            code_context = self._analyze_code_context(transcripts)
            print(f"🔍 Code context analysis completed")
            
            # Step 6: Compile results
            results = {
                "status": "success",
                "audio_info": audio_info,
                "voice_segments": self._serialize_segments(voice_segments),
                "speaker_segments": self._serialize_speakers(speaker_segments), 
                "transcripts": transcripts,
                "code_context": code_context,
                "summary": {
                    "total_duration": audio_info.get("duration_seconds", 0),
                    "speech_segments": len(voice_segments),
                    "speakers_detected": len(set(s.speaker_id for s in speaker_segments)),
                    "transcribed_segments": len(transcripts),
                    "code_references_found": len(code_context.get("code_references", [])),
                    "github_references_found": len(code_context.get("github_references", [])),
                    "technical_terms_found": len(code_context.get("technical_terms", []))
                }
            }
            
            print("✅ Code-aware audio processing pipeline completed successfully")
            return results
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path
            }
    
    def _analyze_code_context(self, transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all transcripts for code context"""
        combined_context = {
            "code_references": [],
            "github_references": [],
            "technical_terms": set(),
            "api_mentions": set(),
            "file_mentions": set()
        }
        
        # Analyze each transcript
        for transcript in transcripts:
            text = transcript.get("text", "")
            if text:
                context = analyze_transcript_simple(text)
                
                # Merge results
                combined_context["code_references"].extend(context["code_references"])
                combined_context["github_references"].extend(context["github_references"])
                combined_context["technical_terms"].update(context["technical_terms"])
                combined_context["api_mentions"].update(context["api_mentions"])
                combined_context["file_mentions"].update(context["file_mentions"])
        
        # Convert sets back to lists and remove duplicates
        combined_context["technical_terms"] = list(combined_context["technical_terms"])
        combined_context["api_mentions"] = list(combined_context["api_mentions"])
        combined_context["file_mentions"] = list(combined_context["file_mentions"])
        
        return combined_context
    
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
code_aware_pipeline = VoicelinkCodeAwarePipeline()

def process_audio_with_context(file_path: str, repo_path: str = None) -> Dict[str, Any]:
    """Convenience function for processing audio files with code context"""
    if repo_path:
        pipeline = VoicelinkCodeAwarePipeline(repo_path)
        return pipeline.process_audio_file(file_path)
    else:
        return code_aware_pipeline.process_audio_file(file_path)
