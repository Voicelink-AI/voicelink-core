"""
Audio Engine Integration for Voicelink Core
"""

import base64
import sys
import os

# Ensure the engine directory is in the Python path
engine_dir = os.path.join(os.path.dirname(__file__), "python")
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

try:
    import audio_engine_py  # This should be your .pyd/.so module in audio_engine/python/
except ImportError:
    audio_engine_py = None

def is_available():
    return audio_engine_py is not None

def transcribe_audio_file(file_bytes: bytes, format: str = "wav"):
    if not is_available():
        raise RuntimeError("Audio engine not available")
    # Call your C++ engine's transcription method
    # Example: result = audio_engine_py.transcribe(file_bytes, format)
    # For now, mock result:
    result = {
        "transcript": "Speaker 1: Let's discuss the API architecture for user auth.",
        "speakers": [
            {
                "speaker_id": "Speaker 1",
                "segments": [
                    {
                        "text": "Let's discuss the API architecture for user auth",
                        "timestamp": "00:02:15",
                        "confidence": 0.95,
                        "code_references": ["auth.py", "UserController"]
                    }
                ]
            }
        ],
        "full_transcript": "Complete meeting transcript...",
        "speaker_separation": True,
        "technical_terms_detected": ["API", "authentication", "JWT tokens"]
    }
    return result
