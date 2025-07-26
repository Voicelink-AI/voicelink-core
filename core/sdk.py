"""
Voicelink SDK for easy integration with other repositories
"""
from typing import Dict, Any, Optional
import requests
from pathlib import Path

class VoicelinkSDK:
    """SDK for integrating with Voicelink Core"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def process_meeting_file(self, audio_file: Path) -> Dict[str, Any]:
        """Process a meeting audio file"""
        with open(audio_file, 'rb') as f:
            files = {'audio_file': f}
            response = requests.post(f"{self.base_url}/process-meeting", files=files)
        return response.json()
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question about processed meetings"""
        data = {'question': question}
        response = requests.post(f"{self.base_url}/ask-question", json=data)
        return response.json()
    
    def get_health(self) -> Dict[str, Any]:
        """Check system health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities"""
        response = requests.get(f"{self.base_url}/capabilities")
        return response.json()

# Global instance for easy importing
voicelink = VoicelinkSDK()

# Convenience functions
def process_meeting(audio_file: Path) -> Dict[str, Any]:
    return voicelink.process_meeting_file(audio_file)

def ask_meeting_question(question: str) -> Dict[str, Any]:
    return voicelink.ask_question(question)
