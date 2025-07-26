"""
Quick test script to verify backend endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoints():
    """Test all main endpoints"""
    
    print("🧪 Testing VoiceLink Core API Endpoints...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BASE_URL}/../health")
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 2: Get meetings (should work now)
    try:
        response = requests.get(f"{BASE_URL}/meetings?limit=10")
        print(f"✅ GET /meetings: {response.status_code} - {len(response.json())} meetings")
    except Exception as e:
        print(f"❌ GET /meetings failed: {e}")
    
    # Test 3: Upload audio
    try:
        # Create a dummy file
        files = {'file': ('test.wav', b'dummy audio data', 'audio/wav')}
        response = requests.post(f"{BASE_URL}/upload-audio", files=files)
        
        if response.status_code == 200:
            file_data = response.json()
            file_id = file_data['file_id']
            print(f"✅ Upload audio: {response.status_code} - File ID: {file_id}")
            
            # Test 4: Create meeting from file (JSON)
            try:
                meeting_data = {"file_id": file_id, "title": "Test Meeting"}
                response = requests.post(
                    f"{BASE_URL}/create-meeting-from-file-json",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(meeting_data)
                )
                print(f"✅ Create meeting from file: {response.status_code}")
                
                if response.status_code == 200:
                    meeting = response.json()
                    print(f"   Meeting ID: {meeting['meeting_id']}")
                    
                    # Test 5: Get meetings again (should have 1 now)
                    response = requests.get(f"{BASE_URL}/meetings?limit=10")
                    meetings = response.json()
                    print(f"✅ GET /meetings after creation: {response.status_code} - {len(meetings)} meetings")
                    
            except Exception as e:
                print(f"❌ Create meeting from file failed: {e}")
                
        else:
            print(f"❌ Upload audio failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Upload audio failed: {e}")
    
    # Test 6: System status
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"✅ System status: {response.status_code}")
    except Exception as e:
        print(f"❌ System status failed: {e}")
    
    print("\n🏁 Endpoint testing complete!")

if __name__ == "__main__":
    test_endpoints()
