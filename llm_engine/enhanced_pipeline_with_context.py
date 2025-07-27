"""
Enhanced pipeline with code context analysis
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the correct audio bridge location
from audio_engine.python.audio_bridge import load_audio, detect_voice_segments, diarize_speakers, get_audio_info
from llm_engine.modules.asr_smart import transcribe_audio_smart as transcribe_audio
from code_context.python.simple_context_engine import initialize_simple_context_engine, analyze_transcript_simple

class VoicelinkCodeAwarePipeline:
    """Complete audio processing pipeline with code context analysis"""
    
    def __init__(self, repo_path: Optional[str] = None):
        print("🎵 Initializing Voicelink Code-Aware Pipeline...")
        
        # Initialize code context engine
        self.repo_path = repo_path or str(Path(__file__).parent.parent)
        try:
            initialize_simple_context_engine(self.repo_path)
            print(f"📚 Code context initialized for: {self.repo_path}")
        except Exception as e:
            print(f"⚠️  Warning: Code context initialization failed: {e}")
            print("📚 Continuing without code context analysis")
    
    def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Complete processing pipeline: Audio → VAD → Diarization → ASR → Code Context → Results
        
        Args:
            file_path: Path to audio file (WAV/MP3)
            
        Returns:
            Complete analysis results with code context
        """
        print(f"🎧 Processing audio file: {file_path}")
        
        if not Path(file_path).exists():
            return {
                "status": "error",
                "error": f"Audio file not found: {file_path}",
                "file_path": file_path
            }
        
        try:
            # Step 1: Load audio
            print("📥 Step 1: Loading audio...")
            audio_data = load_audio(file_path)
            if not audio_data:
                raise Exception("Failed to load audio data")
            
            audio_info = get_audio_info(audio_data)
            print(f"📊 Audio loaded: {audio_info}")
            
            # Step 2: Voice Activity Detection
            print("🗣️  Step 2: Voice Activity Detection...")
            voice_segments = detect_voice_segments(audio_data)
            print(f"🗣️  Detected {len(voice_segments)} voice segments")
            
            # Step 3: Speaker Diarization
            print("👥 Step 3: Speaker Diarization...")
            speaker_segments = diarize_speakers(audio_data)
            print(f"👥 Detected {len(speaker_segments)} speaker segments")
            
            # Step 4: Speech-to-Text Transcription
            print("📝 Step 4: Speech-to-Text Transcription...")
            try:
                transcripts = transcribe_audio(audio_data, voice_segments, speaker_segments)
                print(f"📝 Generated {len(transcripts)} transcripts")
            except Exception as e:
                print(f"⚠️  ASR error: {e}, using fallback")
                transcripts = self._create_fallback_transcripts(voice_segments, speaker_segments)
            
            # Step 5: Code Context Analysis
            print("🔍 Step 5: Code Context Analysis...")
            code_context = self._analyze_code_context(transcripts)
            print(f"🔍 Code context analysis completed")
            
            # Step 6: Compile results
            print("📋 Step 6: Compiling results...")
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
                    "speakers_detected": len(set(getattr(s, 'speaker_id', 0) for s in speaker_segments)),
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
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path,
                "traceback": traceback.format_exc()
            }
    
    def _create_fallback_transcripts(self, voice_segments: List[Any], speaker_segments: List[Any]) -> List[Dict[str, Any]]:
        """Create fallback transcripts when ASR fails"""
        transcripts = []
        for i, segment in enumerate(voice_segments):
            # Find corresponding speaker
            speaker_id = 0
            for spk in speaker_segments:
                if (hasattr(spk, 'start_sample') and hasattr(segment, 'start_sample') and
                    spk.start_sample <= segment.start_sample < spk.end_sample):
                    speaker_id = getattr(spk, 'speaker_id', 0)
                    break
            
            transcripts.append({
                "text": f"[Audio segment {i+1} - transcription unavailable]",
                "speaker_id": speaker_id,
                "start_time": getattr(segment, 'start_sample', 0) / 44100,
                "end_time": getattr(segment, 'end_sample', 44100) / 44100,
                "confidence": 0.0
            })
        return transcripts
    
    def _analyze_code_context(self, transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all transcripts for code context"""
        combined_context = {
            "code_references": [],
            "github_references": [],
            "technical_terms": set(),
            "api_mentions": set(),
            "file_mentions": set()
        }
        
        try:
            # Analyze each transcript
            for transcript in transcripts:
                text = transcript.get("text", "")
                if text and not text.startswith("[Audio segment"):  # Skip fallback transcripts
                    context = analyze_transcript_simple(text)
                    
                    # Merge results
                    combined_context["code_references"].extend(context.get("code_references", []))
                    combined_context["github_references"].extend(context.get("github_references", []))
                    combined_context["technical_terms"].update(context.get("technical_terms", []))
                    combined_context["api_mentions"].update(context.get("api_mentions", []))
                    combined_context["file_mentions"].update(context.get("file_mentions", []))
        except Exception as e:
            print(f"⚠️  Code context analysis error: {e}")
        
        # Convert sets back to lists and remove duplicates
        combined_context["technical_terms"] = list(combined_context["technical_terms"])
        combined_context["api_mentions"] = list(combined_context["api_mentions"])
        combined_context["file_mentions"] = list(combined_context["file_mentions"])
        
        return combined_context
    
    def _serialize_segments(self, segments: List[Any]) -> List[Dict[str, Any]]:
        """Convert C++ segments to serializable format"""
        serialized = []
        for seg in segments:
            try:
                # Get sample rate from segment or use default
                sample_rate = getattr(seg, 'sample_rate', 44100)
                start_sample = getattr(seg, 'start_sample', 0)
                end_sample = getattr(seg, 'end_sample', sample_rate)
                
                serialized.append({
                    "start_sample": start_sample,
                    "end_sample": end_sample,
                    "start_time": start_sample / sample_rate,
                    "end_time": end_sample / sample_rate
                })
            except Exception as e:
                print(f"⚠️  Error serializing segment: {e}")
                # Add a fallback segment
                serialized.append({
                    "start_sample": 0,
                    "end_sample": 44100,
                    "start_time": 0.0,
                    "end_time": 1.0
                })
        return serialized
    
    def _serialize_speakers(self, speakers: List[Any]) -> List[Dict[str, Any]]:
        """Convert C++ speaker segments to serializable format"""
        serialized = []
        for spk in speakers:
            try:
                # Get sample rate from speaker or use default
                sample_rate = getattr(spk, 'sample_rate', 44100)
                start_sample = getattr(spk, 'start_sample', 0)
                end_sample = getattr(spk, 'end_sample', sample_rate)
                speaker_id = getattr(spk, 'speaker_id', 0)
                
                serialized.append({
                    "start_sample": start_sample,
                    "end_sample": end_sample,
                    "speaker_id": speaker_id,
                    "start_time": start_sample / sample_rate,
                    "end_time": end_sample / sample_rate
                })
            except Exception as e:
                print(f"⚠️  Error serializing speaker: {e}")
                # Add a fallback speaker
                serialized.append({
                    "start_sample": 0,
                    "end_sample": 44100,
                    "speaker_id": 0,
                    "start_time": 0.0,
                    "end_time": 1.0
                })
        return serialized

# Global pipeline instance
code_aware_pipeline = VoicelinkCodeAwarePipeline()

def process_audio_with_context(file_path: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for processing audio files with code context"""
    try:
        if repo_path:
            pipeline = VoicelinkCodeAwarePipeline(repo_path)
            return pipeline.process_audio_file(file_path)
        else:
            return code_aware_pipeline.process_audio_file(file_path)
    except Exception as e:
        print(f"❌ Error in process_audio_with_context: {e}")
        return {
            "status": "error",
            "error": str(e),
            "file_path": file_path
        }
