"""
LLM-powered documentation generator for Voicelink
"""
import os
import json
from typing import Dict, Any, List
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class DocumentGenerator:
    """Generate structured documentation from meeting transcripts"""
    
    def __init__(self):
        self.client = None
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("📝 Document Generator initialized with OpenAI")
        else:
            print("📝 Document Generator initialized (mock mode)")
    
    def generate_meeting_summary(self, voicelink_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive meeting summary"""
        
        # Extract key information
        transcripts = voicelink_results.get("transcripts", [])
        code_context = voicelink_results.get("code_context", {})
        audio_info = voicelink_results.get("audio_info", {})
        
        # Combine all transcript text
        full_transcript = " ".join([t.get("text", "") for t in transcripts])
        
        if self.client:
            return self._generate_with_openai(full_transcript, code_context, audio_info, transcripts)
        else:
            return self._generate_mock_summary(full_transcript, code_context, audio_info)
    
    def _generate_with_openai(self, transcript: str, code_context: Dict, audio_info: Dict, transcripts: List) -> Dict[str, Any]:
        """Generate documentation using OpenAI"""
        
        # Prepare context for the LLM
        context_info = []
        if code_context.get("github_references"):
            context_info.append(f"GitHub References: {code_context['github_references']}")
        if code_context.get("technical_terms"):
            context_info.append(f"Technical Terms: {', '.join(code_context['technical_terms'])}")
        if code_context.get("file_mentions"):
            context_info.append(f"Files Mentioned: {', '.join(code_context['file_mentions'])}")
        
        context_str = "\n".join(context_info) if context_info else "No technical context found."
        
        # Calculate speakers count
        speakers_count = len(set(t.get('speaker_id', 0) for t in transcripts if 'speaker_id' in t))
        
        prompt = f"""
You are an AI assistant that generates structured documentation from developer meeting transcripts.

MEETING TRANSCRIPT:
"{transcript}"

TECHNICAL CONTEXT:
{context_str}

AUDIO INFO:
Duration: {audio_info.get('duration_seconds', 0):.1f} seconds
Speakers: {speakers_count}

Please generate a structured meeting summary in the following JSON format:
{{
    "meeting_title": "Brief descriptive title",
    "summary": "2-3 sentence overview",
    "participants": ["List of participants mentioned"],
    "key_topics": ["Main topics discussed"],
    "action_items": ["Specific action items and tasks"],
    "technical_decisions": ["Technical decisions made"],
    "github_items": ["GitHub issues/PRs mentioned"],
    "next_steps": ["Next steps and follow-ups"],
    "meeting_type": "Type of meeting (standup, planning, review, etc.)"
}}

Respond only with valid JSON.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates structured meeting documentation from transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                doc_json = json.loads(result)
                doc_json["generated_with"] = "openai"
                doc_json["generated_at"] = datetime.now().isoformat()
                return doc_json
            except json.JSONDecodeError:
                print("⚠️  Failed to parse OpenAI response as JSON")
                return self._generate_mock_summary(transcript, code_context, audio_info)
                
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return self._generate_mock_summary(transcript, code_context, audio_info)
    
    def _generate_mock_summary(self, transcript: str, code_context: Dict, audio_info: Dict) -> Dict[str, Any]:
        """Generate a mock summary for demonstration"""
        
        # Extract participants (basic name detection)
        participants = []
        if "alice" in transcript.lower():
            participants.append("Alice (Product Manager)")
        
        # Extract key topics from technical terms
        key_topics = []
        tech_terms = code_context.get("technical_terms", [])
        if tech_terms:
            key_topics.extend([f"Discussion of {term}" for term in tech_terms[:3]])
        
        # Generate action items from GitHub references
        action_items = []
        github_refs = code_context.get("github_references", [])
        for ref in github_refs:
            action_items.append(f"Review {ref['type']} #{ref['value']}")
        
        if not action_items:
            action_items = ["Follow up on discussed topics"]
        
        return {
            "meeting_title": "Team Meeting - Product Introduction",
            "summary": f"Brief meeting introducing Alice as the new product manager. Duration: {audio_info.get('duration_seconds', 0):.1f} seconds.",
            "participants": participants or ["Alice"],
            "key_topics": key_topics or ["Team introductions", "Role clarification"],
            "action_items": action_items,
            "technical_decisions": [],
            "github_items": [f"{ref['type']} #{ref['value']}"],
            "next_steps": ["Continue onboarding process", "Schedule follow-up meetings"],
            "meeting_type": "introduction",
            "generated_with": "mock",
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_markdown_doc(self, summary: Dict[str, Any]) -> str:
        """Generate a markdown document from the summary"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"""# {summary.get('meeting_title', 'Meeting Summary')}

**Date:** {timestamp}  
**Generated by:** Voicelink AI  

## Summary
{summary.get('summary', 'No summary available')}

## Participants
{self._format_list(summary.get('participants', []))}

## Key Topics Discussed
{self._format_list(summary.get('key_topics', []))}

## Action Items
{self._format_list(summary.get('action_items', []))}

## Technical Decisions
{self._format_list(summary.get('technical_decisions', []) or ['No technical decisions recorded'])}

## GitHub Items Referenced
{self._format_list(summary.get('github_items', []) or ['No GitHub items referenced'])}

## Next Steps
{self._format_list(summary.get('next_steps', []))}

---
*Generated by Voicelink on {timestamp}*
"""
        return markdown
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list as markdown"""
        if not items:
            return "- None\n"
        return "\n".join([f"- {item}" for item in items]) + "\n"

# Global instance
doc_generator = DocumentGenerator()

def generate_meeting_documentation(voicelink_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate meeting documentation from Voicelink results"""
    summary = doc_generator.generate_meeting_summary(voicelink_results)
    markdown = doc_generator.generate_markdown_doc(summary)
    
    return {
        "summary": summary,
        "markdown": markdown,
        "generated_at": datetime.now().isoformat()
    }
