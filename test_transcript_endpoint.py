#!/usr/bin/env python3
"""
Test script to verify the transcript endpoint functionality
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def test_transcript_endpoint():
    """Test the meeting transcript endpoint"""
    print("🧪 Testing Transcript Endpoint Functionality")
    print("=" * 50)
    
    # Step 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        return
    
    # Step 2: Create a test audio file (dummy data)
    test_audio_content = b"dummy audio content for testing"
    
    # Step 3: Upload and process the audio file
    print("\n📤 Uploading test audio file...")
    files = {
        'file': ('test_meeting.wav', test_audio_content, 'audio/wav')
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process-meeting", files=files)
        if response.status_code == 200:
            data = response.json()
            meeting_id = data.get('meeting_id')
            print(f"✅ Audio processed successfully. Meeting ID: {meeting_id}")
            
            # Show the transcript from the processing response
            transcript = data.get('transcript', {})
            print(f"📝 Transcript from processing: {transcript.get('full_text', '')[:100]}...")
            
            # Step 4: Test the transcript endpoint
            print(f"\n🔍 Testing transcript endpoint for meeting {meeting_id}")
            transcript_response = requests.get(f"{BASE_URL}/meetings/{meeting_id}/transcript")
            
            if transcript_response.status_code == 200:
                transcript_data = transcript_response.json()
                print("✅ Transcript endpoint works!")
                print(f"📝 Meeting Title: {transcript_data.get('title', 'N/A')}")
                
                transcript_info = transcript_data.get('transcript', {})
                if isinstance(transcript_info, dict) and 'full_text' in transcript_info:
                    print(f"📄 Transcript Text: {transcript_info['full_text'][:100]}...")
                    print(f"📊 Transcript has {len(transcript_info.get('segments', []))} segments")
                elif isinstance(transcript_info, dict):
                    print(f"📄 Structured Transcript: {json.dumps(transcript_info, indent=2)[:200]}...")
                else:
                    print(f"📄 Transcript: {str(transcript_info)[:100]}...")
                
                # Check for speakers data
                speakers = transcript_data.get('speakers', [])
                if speakers:
                    print(f"🎤 Found {len(speakers)} speakers")
                    for speaker in speakers:
                        speaker_id = speaker.get('speaker_id', 'Unknown')
                        speaking_time = speaker.get('total_speaking_time', 0)
                        print(f"   - {speaker_id}: {speaking_time}s speaking time")
                
            else:
                print(f"❌ Transcript endpoint failed: {transcript_response.status_code}")
                print(f"Error: {transcript_response.text}")
            
            # Step 5: Test getting meeting details
            print(f"\n🔍 Testing meeting details endpoint")
            meeting_response = requests.get(f"{BASE_URL}/meetings/{meeting_id}")
            
            if meeting_response.status_code == 200:
                meeting_data = meeting_response.json()
                print("✅ Meeting details endpoint works!")
                print(f"📋 Meeting Status: {meeting_data.get('status', 'N/A')}")
                print(f"📝 Has Transcript: {'Yes' if meeting_data.get('transcript') else 'No'}")
            else:
                print(f"❌ Meeting details endpoint failed: {meeting_response.status_code}")
            
        else:
            print(f"❌ Audio processing failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_transcript_endpoint()
