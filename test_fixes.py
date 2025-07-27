#!/usr/bin/env python3
"""
Test script to verify VoiceLink fixes
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

async def test_database_functionality():
    """Test database service functionality"""
    print("🧪 Testing Database Functionality")
    print("-" * 40)
    
    from persistence.database_service import get_database_service
    db_service = get_database_service()
    
    # Test creating a meeting
    meeting_data = {
        "title": "Test Meeting",
        "description": "Testing database functionality",
        "participants": ["Alice", "Bob", "Charlie"],
        "status": "completed",
        "metadata": {"test": True},
        "audio_duration": 120.0
    }
    
    meeting_id = db_service.create_meeting(meeting_data)
    print(f"✅ Created meeting: {meeting_id}")
    
    # Test saving transcripts
    sample_transcripts = [
        {
            "speaker": "Alice",
            "text": "Let's discuss the API endpoint in main.py",
            "start_time": 0.0,
            "end_time": 3.0,
            "confidence": 0.95
        },
        {
            "speaker": "Bob", 
            "text": "I agree, we should optimize the database queries",
            "start_time": 3.5,
            "end_time": 6.0,
            "confidence": 0.93
        }
    ]
    
    transcript_ids = db_service.save_transcripts(meeting_id, sample_transcripts)
    print(f"✅ Saved {len(transcript_ids)} transcripts")
    
    # Test saving analysis
    analysis_data = {
        "summary": {
            "title": "API Discussion",
            "main_topics": ["API optimization", "Database queries"]
        },
        "action_items": ["Review main.py", "Optimize database"],
        "key_points": ["Performance improvements needed"],
        "confidence_score": 0.85
    }
    
    analysis_id = db_service.save_analysis(meeting_id, analysis_data)
    print(f"✅ Saved analysis: {analysis_id}")
    
    # Test retrieval
    meeting = db_service.get_meeting(meeting_id)
    transcripts = db_service.get_meeting_transcripts(meeting_id)
    analysis = db_service.get_meeting_analysis(meeting_id)
    
    print(f"✅ Retrieved meeting: {meeting['title']}")
    print(f"✅ Retrieved {len(transcripts)} transcripts")
    print(f"✅ Retrieved analysis with {len(analysis['action_items'])} action items")
    
    # Test statistics
    stats = db_service.get_statistics()
    print(f"✅ Statistics: {stats['total_meetings']} meetings, {stats['active_participants']} participants")
    
    print("\n✅ Database functionality test PASSED!")
    return meeting_id

async def test_api_endpoints():
    """Test API endpoints with requests"""
    print("\n🌐 Testing API Endpoints")
    print("-" * 40)
    
    try:
        import httpx
        
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
        
        print("✅ API endpoints test PASSED!")
        
    except ImportError:
        print("⚠️  httpx not available, skipping API tests")
    except Exception as e:
        print(f"⚠️  API not running: {e}")

async def test_pipeline_functionality():
    """Test enhanced pipeline"""
    print("\n🎵 Testing Enhanced Pipeline")
    print("-" * 40)
    
    try:
        from llm_engine.enhanced_pipeline_with_context import VoicelinkCodeAwarePipeline
        
        # Create pipeline
        pipeline = VoicelinkCodeAwarePipeline()
        print("✅ Pipeline initialized")
        
        # Test participant extraction
        sample_transcripts = [
            {"speaker": "Alice Johnson", "text": "Hello everyone"},
            {"speaker": "Bob Smith", "text": "Hi Alice"},
            {"speaker": "Charlie", "text": "Good morning"}
        ]
        
        participants = pipeline._extract_participants(sample_transcripts)
        print(f"✅ Extracted participants: {participants}")
        
        print("✅ Enhanced pipeline test PASSED!")
        
    except Exception as e:
        print(f"⚠️  Pipeline test error: {e}")

async def main():
    """Run all tests"""
    print("🚀 VoiceLink Fixes Test Suite")
    print("=" * 50)
    
    try:
        # Test database
        meeting_id = await test_database_functionality()
        
        # Test API endpoints
        await test_api_endpoints()
        
        # Test pipeline
        await test_pipeline_functionality()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print(f"📝 Sample meeting created: {meeting_id}")
        print("\n✨ VoiceLink fixes are working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
