"""
Create Your Own Meeting Test

This script lets you create a custom meeting with your own data
and see the complete VoiceLink pipeline in action.
"""

import asyncio
from datetime import datetime

async def create_custom_meeting():
    """Create a custom meeting for testing"""
    
    print("🎯 CREATE YOUR CUSTOM MEETING TEST")
    print("=" * 50)
    
    # Get user input
    print("\n📝 Enter your meeting details:")
    title = input("Meeting Title: ").strip() or "Custom Test Meeting"
    description = input("Description (optional): ").strip()
    
    print("\nParticipants (press Enter after each, empty line to finish):")
    participants = []
    while True:
        participant = input(f"Participant {len(participants) + 1}: ").strip()
        if not participant:
            break
        participants.append(participant)
    
    if not participants:
        participants = ["You", "Test User"]
    
    print(f"\n🎤 Create transcript segments:")
    print("Enter dialogue (format: 'Speaker: What they said')")
    print("Press Enter twice when done")
    
    transcripts = []
    current_time = 0.0
    
    while True:
        line = input(f"[{current_time:.1f}s] ").strip()
        if not line:
            break
        
        if ':' in line:
            speaker, text = line.split(':', 1)
            speaker = speaker.strip()
            text = text.strip()
        else:
            speaker = "Unknown"
            text = line
        
        # Estimate duration (rough: 150 words per minute)
        words = len(text.split())
        duration = max(2.0, words * 0.4)  # At least 2 seconds
        
        transcript = {
            'speaker': speaker,
            'text': text,
            'confidence': 0.95,
            'start_time': current_time,
            'end_time': current_time + duration,
            'speaker_id': f"speaker_{len(transcripts) + 1:03d}",
            'processing_method': 'custom'
        }
        
        transcripts.append(transcript)
        current_time += duration + 0.5  # Add small gap
        
        print(f"   Added: [{transcript['start_time']:.1f}s-{transcript['end_time']:.1f}s] {speaker}: {text[:50]}...")
    
    if not transcripts:
        # Default transcript
        transcripts = [
            {
                'speaker': participants[0] if participants else 'You',
                'text': 'This is a test of the VoiceLink system. Let me see how it processes this meeting.',
                'confidence': 0.95,
                'start_time': 0.0,
                'end_time': 5.0,
                'speaker_id': 'speaker_001',
                'processing_method': 'custom'
            }
        ]
    
    # Import VoiceLink components
    try:
        from api.config import Config
        from orchestrate_voicelink import VoiceLinkOrchestrator
        from persistence.database_service import get_database_service
        
        config = Config()
        orchestrator = VoiceLinkOrchestrator(config)
        db_service = get_database_service()
        
        print(f"\n⚙️ PROCESSING YOUR MEETING")
        print("-" * 40)
        
        # Create meeting record
        meeting_data = {
            'title': title,
            'description': description,
            'participants': participants,
            'metadata': {
                'custom_test': True,
                'created_by': 'interactive_test',
                'timestamp': datetime.now().isoformat()
            },
            'audio_file_path': 'custom_test.wav',
            'audio_duration': transcripts[-1]['end_time'] if transcripts else 30.0
        }
        
        meeting_id = db_service.create_meeting(meeting_data)
        print(f"✅ Meeting created: {meeting_id}")
        
        # Save transcripts
        transcript_ids = db_service.save_transcripts(meeting_id, transcripts)
        print(f"✅ Transcripts saved: {len(transcript_ids)} segments")
        
        # Process through LLM pipeline
        from llm_engine.pipeline import LLMPipeline
        llm_pipeline = LLMPipeline(config)
        
        print(f"🧠 Processing through LLM pipeline...")
        llm_results = await llm_pipeline.process_meeting(
            transcripts=transcripts,
            code_context={},
            participants=participants,
            metadata=meeting_data['metadata']
        )
        
        # Save analysis
        analysis_id = db_service.save_meeting_analysis(meeting_id, llm_results)
        print(f"✅ Analysis saved: {analysis_id}")
        
        # Complete meeting
        db_service.update_meeting_status(meeting_id, 'completed')
        
        # Show results
        print(f"\n🎉 YOUR MEETING ANALYSIS")
        print("=" * 50)
        
        print(f"📋 Meeting: {title}")
        print(f"🔗 Meeting ID: {meeting_id}")
        print(f"👥 Participants: {', '.join(participants)}")
        print(f"📝 Transcript Segments: {len(transcripts)}")
        
        # Display analysis
        summary = llm_results.get('meeting_summary', {})
        print(f"\n📊 Executive Summary:")
        print(f"   {summary.get('executive_summary', 'No summary available')}")
        
        topics = summary.get('main_topics', [])
        if topics:
            print(f"\n🎯 Main Topics:")
            for i, topic in enumerate(topics, 1):
                print(f"   {i}. {topic}")
        
        action_items = llm_results.get('action_items', [])
        if action_items:
            print(f"\n✅ Action Items:")
            for i, item in enumerate(action_items, 1):
                assignee = item.get('assignee', 'Unassigned')
                description = item.get('description', item.get('task', 'No description'))
                print(f"   {i}. {description} - {assignee}")
        
        print(f"\n🌐 Test your meeting in the web interface:")
        print(f"   http://localhost:8000/meetings/{meeting_id}")
        print(f"   http://localhost:8000/docs")
        
        return meeting_id
        
    except Exception as e:
        print(f"❌ Error processing meeting: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    asyncio.run(create_custom_meeting())

if __name__ == "__main__":
    main()
