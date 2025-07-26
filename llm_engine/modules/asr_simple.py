"""
Simple ASR adapter that works without any external dependencies
"""
import numpy as np
from typing import List, Dict, Any

class SimpleASRAdapter:
    """Simple ASR adapter with mock transcription for testing"""
    
    def __init__(self):
        print("🎙️  Simple ASR initialized (mock transcription)")
    
    def transcribe_segments(self, audio_data, voice_segments, speaker_segments=None) -> List[Dict[str, Any]]:
        """Generate mock transcripts for voice segments"""
        transcripts = []
        
        for i, segment in enumerate(voice_segments):
            start_sample = segment.start_sample
            end_sample = segment.end_sample
            duration = (end_sample - start_sample) / audio_data.sample_rate
            
            # Skip very short segments
            if duration < 0.5:
                print(f"⏭️  Skipping short segment {i} ({duration:.2f}s)")
                continue
            
            # Find speaker for this segment
            speaker_id = self._find_speaker_for_segment(start_sample, end_sample, speaker_segments)
            
            # Generate mock transcript based on segment characteristics
            text = self._generate_mock_transcript(duration, i)
            
            transcript = {
                "segment_id": i,
                "start_sample": start_sample,
                "end_sample": end_sample,
                "start_time": start_sample / audio_data.sample_rate,
                "end_time": end_sample / audio_data.sample_rate,
                "speaker_id": speaker_id,
                "text": text,
                "confidence": 0.85
            }
            transcripts.append(transcript)
            print(f"✅ Generated transcript for segment {i}: '{text}'")
        
        print(f"✅ Generated {len(transcripts)} mock transcripts")
        return transcripts
    
    def _generate_mock_transcript(self, duration: float, segment_id: int) -> str:
        """Generate realistic mock transcript based on segment duration"""
        mock_phrases = [
            "Hello everyone, welcome to our meeting today.",
            "Let's discuss the technical architecture for this project.", 
            "I think we should implement this feature using Python.",
            "The audio processing pipeline is working correctly.",
            "We need to integrate the voice recognition system.",
            "This segment contains important technical information.",
            "Let's review the code changes and documentation.",
            "The real-time processing is functioning as expected."
        ]
        
        # Select phrase based on segment characteristics
        phrase_index = segment_id % len(mock_phrases)
        base_phrase = mock_phrases[phrase_index]
        
        # Adjust phrase length based on duration
        if duration < 1.0:
            words = base_phrase.split()[:3]
            return " ".join(words) + "."
        elif duration > 2.0:
            return base_phrase + " This is additional content for longer segments."
        else:
            return base_phrase
    
    def _find_speaker_for_segment(self, start_sample: int, end_sample: int, speaker_segments) -> int:
        """Find which speaker corresponds to a voice segment"""
        if not speaker_segments:
            return 0
        
        for speaker in speaker_segments:
            if (start_sample >= speaker.start_sample and start_sample < speaker.end_sample) or \
               (end_sample > speaker.start_sample and end_sample <= speaker.end_sample):
                return speaker.speaker_id
        
        return 0

# Global instance
simple_asr = SimpleASRAdapter()

def transcribe_audio_simple(audio_data, voice_segments, speaker_segments=None):
    """Simple transcription function"""
    return simple_asr.transcribe_segments(audio_data, voice_segments, speaker_segments)
