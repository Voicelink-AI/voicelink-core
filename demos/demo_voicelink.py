"""
VoiceLink Pipeline Demo

Demonstrates the complete VoiceLink processing pipeline with sample data.
"""

import asyncio
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_voicelink_pipeline():
    """Demonstrate the complete VoiceLink pipeline"""
    
    print("🎯 VoiceLink Pipeline Demo Starting...")
    print("=" * 50)
    
    try:
        # Import VoiceLink components
        from api.config import Config
        from orchestrate_voicelink import VoiceLinkOrchestrator
        from persistence.database_service import get_database_service
        
        # Initialize system
        config = Config()
        orchestrator = VoiceLinkOrchestrator(config)
        db_service = get_database_service()
        
        print("✅ System initialized successfully")
        
        # 1. Database Health Check
        print("\n📊 DATABASE HEALTH CHECK")
        print("-" * 30)
        db_healthy = db_service.health_check()
        stats = db_service.get_statistics()
        
        print(f"Database Status: {'✅ Healthy' if db_healthy else '❌ Unhealthy'}")
        print(f"Total Meetings: {stats.get('total_meetings', 0)}")
        print(f"Completed Meetings: {stats.get('completed_meetings', 0)}")
        print(f"Database URL: {stats.get('database_url', 'Unknown')}")
        
        # 2. Create Sample Meeting
        print("\n🎤 CREATING SAMPLE MEETING")
        print("-" * 30)
        
        meeting_data = {
            'title': 'VoiceLink Demo Meeting',
            'description': 'Demonstration of the complete AI-powered documentation pipeline',
            'participants': ['Alice Johnson', 'Bob Smith', 'Charlie Davis', 'Diana Wilson'],
            'metadata': {
                'meeting_type': 'technical_discussion',
                'duration_minutes': 45,
                'location': 'Conference Room A',
                'demo_mode': True
            },
            'audio_file_path': 'demo_meeting_audio.wav'
        }
        
        meeting_id = db_service.create_meeting(meeting_data)
        print(f"Created Meeting ID: {meeting_id}")
        print(f"Meeting Title: {meeting_data['title']}")
        print(f"Participants: {', '.join(meeting_data['participants'])}")
        
        # 3. Simulate Transcript Data
        print("\n📝 ADDING SAMPLE TRANSCRIPTS")
        print("-" * 30)
        
        sample_transcripts = [
            {
                'speaker': 'Alice Johnson',
                'text': 'Good morning everyone. Today we\'re going to discuss our API redesign and the new authentication system.',
                'confidence': 0.95,
                'start_time': 0.0,
                'end_time': 5.2,
                'speaker_id': 'speaker_001',
                'processing_method': 'whisper'
            },
            {
                'speaker': 'Bob Smith',
                'text': 'Thanks Alice. I\'ve been working on the database optimization. We need to review the indexing strategy.',
                'confidence': 0.92,
                'start_time': 5.5,
                'end_time': 10.8,
                'speaker_id': 'speaker_002',
                'processing_method': 'whisper'
            },
            {
                'speaker': 'Charlie Davis',
                'text': 'I agree with Bob. Also, we should implement proper error handling in the authentication middleware.',
                'confidence': 0.88,
                'start_time': 11.0,
                'end_time': 16.3,
                'speaker_id': 'speaker_003',
                'processing_method': 'whisper'
            },
            {
                'speaker': 'Diana Wilson',
                'text': 'Excellent points. Let me create action items for database indexing and middleware improvements.',
                'confidence': 0.94,
                'start_time': 16.5,
                'end_time': 21.0,
                'speaker_id': 'speaker_004',
                'processing_method': 'whisper'
            }
        ]
        
        transcript_ids = db_service.save_transcripts(meeting_id, sample_transcripts)
        print(f"Saved {len(transcript_ids)} transcript segments")
        
        for i, transcript in enumerate(sample_transcripts):
            print(f"  [{transcript['start_time']:.1f}s] {transcript['speaker']}: {transcript['text'][:50]}...")
        
        # 4. LLM Processing Demo
        print("\n🧠 LLM PROCESSING PIPELINE")
        print("-" * 30)
        
        # Simulate LLM processing
        from llm_engine.pipeline import LLMPipeline
        llm_pipeline = LLMPipeline(config)
        
        # Process transcripts through LLM
        llm_results = await llm_pipeline.process_meeting(
            transcripts=sample_transcripts,
            code_context={},
            participants=meeting_data['participants'],
            metadata=meeting_data['metadata']
        )
        
        print(f"LLM Provider: {llm_results.get('provider', 'mock')}")
        print(f"Processing Time: {llm_results.get('processing_time', 'N/A')}")
        
        # Display results
        summary = llm_results.get('meeting_summary', {})
        print(f"\n📋 Executive Summary:")
        print(f"  {summary.get('executive_summary', 'No summary available')}")
        
        topics = summary.get('main_topics', [])
        if topics:
            print(f"\n🎯 Main Topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
        
        action_items = llm_results.get('action_items', [])
        if action_items:
            print(f"\n✅ Action Items:")
            for i, item in enumerate(action_items, 1):
                assignee = item.get('assignee', 'Unassigned')
                priority = item.get('priority', 'medium')
                description = item.get('description', item.get('task', 'No description'))
                print(f"  {i}. [{priority.upper()}] {description} - {assignee}")
        
        key_points = llm_results.get('key_points', [])
        if key_points:
            print(f"\n💡 Key Points:")
            for i, point in enumerate(key_points, 1):
                print(f"  {i}. {point}")
        
        # 5. Save Analysis to Database
        analysis_id = db_service.save_meeting_analysis(meeting_id, llm_results)
        print(f"\n💾 Analysis saved to database: {analysis_id}")
        
        # 6. Integration Simulation
        print("\n🔗 INTEGRATION PROCESSING")
        print("-" * 30)
        
        from integrations.manager import IntegrationManager
        integration_manager = IntegrationManager(config)
        
        # Simulate integration triggers
        integration_results = await integration_manager.trigger_integrations(
            meeting_id=meeting_id,
            meeting_data=meeting_data,
            analysis_results=llm_results
        )
        
        print(f"Integration Results: {len(integration_results)} integrations processed")
        for integration in integration_results:
            platform = integration.get('platform', 'unknown')
            status = integration.get('status', 'unknown')
            print(f"  📱 {platform.title()}: {status}")
        
        # 7. Final Database Status
        print("\n📊 FINAL DATABASE STATUS")
        print("-" * 30)
        
        # Update meeting status
        db_service.update_meeting_status(meeting_id, 'completed')
        
        # Get updated statistics
        final_stats = db_service.get_statistics()
        print(f"Total Meetings: {final_stats.get('total_meetings', 0)}")
        print(f"Completed Meetings: {final_stats.get('completed_meetings', 0)}")
        print(f"Total Transcripts: {final_stats.get('total_transcripts', 0)}")
        print(f"Total Analyses: {final_stats.get('total_analyses', 0)}")
        
        # 8. Retrieve and Display Meeting
        print("\n📖 MEETING RETRIEVAL DEMO")
        print("-" * 30)
        
        retrieved_meeting = db_service.get_meeting(meeting_id)
        retrieved_transcripts = db_service.get_meeting_transcripts(meeting_id)
        retrieved_analysis = db_service.get_meeting_analysis(meeting_id)
        
        print(f"Retrieved Meeting: {retrieved_meeting['title']}")
        print(f"Status: {retrieved_meeting['status']}")
        print(f"Transcript Segments: {len(retrieved_transcripts)}")
        print(f"Analysis Available: {'Yes' if retrieved_analysis else 'No'}")
        
        print("\n" + "=" * 50)
        print("🎉 VoiceLink Pipeline Demo Complete!")
        print("\n✨ Summary of Demonstrated Features:")
        print("  ✅ Database operations (create, read, update)")
        print("  ✅ Meeting processing pipeline")
        print("  ✅ Transcript management")
        print("  ✅ LLM analysis and summarization")
        print("  ✅ Integration framework")
        print("  ✅ Complete data persistence")
        print("  ✅ System health monitoring")
        
        return meeting_id
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(demo_voicelink_pipeline())
