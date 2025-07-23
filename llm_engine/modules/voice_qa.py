"""
Voice-powered Q&A system for Voicelink
"""
import os
from typing import Dict, Any, List
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class VoiceQAEngine:
    """Interactive voice Q&A for meeting transcripts"""
    
    def __init__(self):
        self.client = None
        self.meeting_history = []
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("🗣️  Voice Q&A Engine initialized with OpenAI")
        else:
            print("🗣️  Voice Q&A Engine initialized (mock mode)")
    
    def add_meeting(self, voicelink_results: Dict[str, Any]):
        """Add a processed meeting to the knowledge base"""
        meeting_data = {
            "timestamp": datetime.now().isoformat(),
            "transcripts": voicelink_results.get("transcripts", []),
            "code_context": voicelink_results.get("code_context", {}),
            "duration": voicelink_results.get("audio_info", {}).get("duration_seconds", 0),
            "participants": self._extract_participants(voicelink_results)
        }
        self.meeting_history.append(meeting_data)
        print(f"📚 Added meeting to knowledge base ({len(self.meeting_history)} total meetings)")
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Answer a question about the meeting history"""
        if not self.meeting_history:
            return {
                "answer": "No meetings in knowledge base yet.",
                "confidence": 0.0,
                "sources": []
            }
        
        if self.client:
            return self._answer_with_openai(question)
        else:
            return self._answer_mock(question)
    
    def _answer_with_openai(self, question: str) -> Dict[str, Any]:
        """Generate answer using OpenAI"""
        # Prepare context from meeting history
        context_parts = []
        
        for i, meeting in enumerate(self.meeting_history):
            transcript_text = " ".join([t.get("text", "") for t in meeting["transcripts"]])
            context_parts.append(f"Meeting {i+1} ({meeting['timestamp'][:10]}):\n{transcript_text}")
            
            # Add code context if available
            code_context = meeting.get("code_context", {})
            if code_context.get("github_references"):
                context_parts.append(f"GitHub items: {code_context['github_references']}")
            if code_context.get("technical_terms"):
                context_parts.append(f"Technical terms: {', '.join(code_context['technical_terms'])}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""
You are Voicelink AI, an assistant that answers questions about developer meetings and technical discussions.

MEETING CONTEXT:
{context}

QUESTION: {question}

Please provide a helpful answer based on the meeting transcripts. If the information isn't available in the meetings, say so clearly.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Voicelink AI, a helpful assistant for developer meeting analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "confidence": 0.9,
                "sources": [f"Meeting {i+1}" for i in range(len(self.meeting_history))],
                "generated_with": "openai"
            }
            
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return self._answer_mock(question)
    
    def _answer_mock(self, question: str) -> Dict[str, Any]:
        """Generate mock answer for demo"""
        question_lower = question.lower()
        
        # Simple keyword matching for demo
        if "alice" in question_lower:
            return {
                "answer": "Alice introduced herself as the new product manager in the most recent meeting.",
                "confidence": 0.8,
                "sources": ["Meeting 1"],
                "generated_with": "mock"
            }
        elif "who" in question_lower and ("said" in question_lower or "mentioned" in question_lower):
            return {
                "answer": "Alice was the primary speaker in the recorded meeting, introducing herself as the new product manager.",
                "confidence": 0.7,
                "sources": ["Meeting 1"],
                "generated_with": "mock"
            }
        elif "what" in question_lower and "discuss" in question_lower:
            return {
                "answer": "The meeting focused on team introductions, specifically Alice's role as the new product manager.",
                "confidence": 0.7,
                "sources": ["Meeting 1"],
                "generated_with": "mock"
            }
        else:
            return {
                "answer": f"I found {len(self.meeting_history)} meeting(s) in the knowledge base, but I need more specific information to answer '{question}'. Try asking about participants, topics discussed, or technical decisions.",
                "confidence": 0.5,
                "sources": [f"Meeting {i+1}" for i in range(len(self.meeting_history))],
                "generated_with": "mock"
            }
    
    def _extract_participants(self, voicelink_results: Dict[str, Any]) -> List[str]:
        """Extract participant names from meeting"""
        participants = []
        
        # Look for names in transcripts
        transcripts = voicelink_results.get("transcripts", [])
        for transcript in transcripts:
            text = transcript.get("text", "").lower()
            if "alice" in text:
                participants.append("Alice")
        
        return list(set(participants))  # Remove duplicates

# Global instance
voice_qa_engine = VoiceQAEngine()

def add_meeting_to_qa(voicelink_results: Dict[str, Any]):
    """Add meeting to Q&A knowledge base"""
    voice_qa_engine.add_meeting(voicelink_results)

def ask_voice_question(question: str) -> Dict[str, Any]:
    """Ask a question about the meetings"""
    return voice_qa_engine.ask_question(question)
