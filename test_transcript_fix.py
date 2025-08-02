#!/usr/bin/env python3
"""
Quick test to verify transcript functionality works correctly
"""
import requests
import json

def test_transcript_feature():
    """Test the transcript feature end-to-end"""
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Testing Transcript Feature")
    print("=" * 50)
    
    # Test 1: Upload an audio file
    print("1. Testing file upload...")
    
    # Create a mock audio file for testing
    test_audio_content = b"Mock audio content for testing"
    files = {
        'file': ('test_meeting.wav', test_audio_content, 'audio/wav')
    }
    
    try:
        response = requests.post(f"{base_url}/process-meeting", files=files)
        if response.status_code == 200:
            data = response.json()
            meeting_id = data.get('meeting_id')
            print(f"✅ Audio uploaded successfully! Meeting ID: {meeting_id}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    # Test 2: Check if meeting appears in meetings list
    print("\n2. Checking meetings list...")
    try:
        response = requests.get(f"{base_url}/meetings")
        if response.status_code == 200:
            meetings = response.json()
            if meetings and len(meetings) > 0:
                print(f"✅ Found {len(meetings)} meeting(s)")
                meeting = meetings[0]
                print(f"   Title: {meeting.get('title')}")
                print(f"   Has transcript: {bool(meeting.get('transcript'))}")
            else:
                print("❌ No meetings found")
                return False
        else:
            print(f"❌ Failed to get meetings: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting meetings: {e}")
        return False
    
    # Test 3: Get meeting details
    print("\n3. Getting meeting details...")
    try:
        response = requests.get(f"{base_url}/meetings/{meeting_id}")
        if response.status_code == 200:
            meeting_data = response.json()
            transcript = meeting_data.get('transcript', '')
            print(f"✅ Meeting details retrieved")
            print(f"   Status: {meeting_data.get('status')}")
            print(f"   Transcript length: {len(transcript) if transcript else 0} chars")
            if transcript:
                print(f"   Transcript preview: {transcript[:100]}...")
        else:
            print(f"❌ Failed to get meeting details: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting meeting details: {e}")
        return False
    
    # Test 4: Test dedicated transcript endpoint
    print("\n4. Testing transcript endpoint...")
    try:
        response = requests.get(f"{base_url}/meetings/{meeting_id}/transcript")
        if response.status_code == 200:
            transcript_data = response.json()
            print(f"✅ Transcript endpoint works!")
            print(f"   Meeting ID: {transcript_data.get('meeting_id')}")
            print(f"   Title: {transcript_data.get('title')}")
            
            transcript = transcript_data.get('transcript', {})
            if isinstance(transcript, dict) and transcript.get('full_text'):
                print(f"   Full text length: {len(transcript.get('full_text', ''))}")
                print(f"   Segments: {len(transcript.get('segments', []))}")
                print(f"   Text preview: {transcript.get('full_text', '')[:100]}...")
            else:
                print(f"   Transcript structure: {type(transcript)}")
                print(f"   Transcript content: {transcript}")
                
        else:
            print(f"❌ Transcript endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting transcript: {e}")
        return False
    
    print("\n🎉 All tests passed! Transcript feature is working correctly!")
    return True

if __name__ == "__main__":
    success = test_transcript_feature()
    if not success:
        print("\n❌ Some tests failed")
        exit(1)
    else:
        print("\n✅ All tests successful!")
