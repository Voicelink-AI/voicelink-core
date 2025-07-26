"""
Voicelink Core Module

Main entry point for Voicelink core functionality.
"""

from .audio_bridge import VoicelinkAudioEngine, load_audio, detect_voice_segments
from .orchestrator import VoiceLinkOrchestrator
from .sdk import VoicelinkSDK

__version__ = "1.0.0"
__all__ = [
    "VoicelinkAudioEngine",
    "VoiceLinkOrchestrator", 
    "VoicelinkSDK",
    "load_audio",
    "detect_voice_segments"
]
