"""
Interactive VoiceLink Tester

Run this script to test VoiceLink functionality interactively.
Usage: python interactive_test.py
"""

import requests
import json
import asyncio
from datetime import datetime

class VoiceLinkTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self):
        """Test system health"""
        print("🏥 TESTING SYSTEM HEALTH")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ System is healthy!")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_statistics(self):
        """Get database statistics"""
        print("\n📊 DATABASE STATISTICS")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/meetings/stats/overview")
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {})
                print(f"Total Meetings: {stats.get('total_meetings', 0)}")
                print(f"Completed Meetings: {stats.get('completed_meetings', 0)}")
                print(f"Processing Meetings: {stats.get('processing_meetings', 0)}")
                print(f"Total Transcripts: {stats.get('total_transcripts', 0)}")
                print(f"Total Analyses: {stats.get('total_analyses', 0)}")
                print(f"Database Healthy: {stats.get('database_healthy', False)}")
                return stats
            else:
                print(f"❌ Failed to get stats: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def list_meetings(self):
        """List all meetings"""
        print("\n📋 ALL MEETINGS")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/meetings/")
            if response.status_code == 200:
                data = response.json()
                meetings = data.get('data', {}).get('meetings', [])
                
                if meetings:
                    for i, meeting in enumerate(meetings, 1):
                        print(f"{i}. {meeting.get('title', 'Untitled')}")
                        print(f"   ID: {meeting.get('id', 'N/A')}")
                        print(f"   Status: {meeting.get('status', 'Unknown')}")
                        print(f"   Participants: {len(meeting.get('participants', []))}")
                        print()
                else:
                    print("No meetings found.")
                
                return meetings
            else:
                print(f"❌ Failed to list meetings: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def get_meeting_details(self, meeting_id):
        """Get detailed meeting information"""
        print(f"\n🔍 MEETING DETAILS: {meeting_id[:8]}...")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/meetings/{meeting_id}")
            if response.status_code == 200:
                data = response.json()
                meeting = data.get('data', {})
                
                print(f"Title: {meeting.get('title', 'N/A')}")
                print(f"Description: {meeting.get('description', 'N/A')}")
                print(f"Status: {meeting.get('status', 'N/A')}")
                print(f"Participants: {', '.join(meeting.get('participants', []))}")
                print(f"Start Time: {meeting.get('start_time', 'N/A')}")
                print(f"Audio File: {meeting.get('audio_file_path', 'N/A')}")
                
                return meeting
            else:
                print(f"❌ Meeting not found: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_transcripts(self, meeting_id):
        """Get meeting transcripts"""
        print(f"\n📝 TRANSCRIPTS: {meeting_id[:8]}...")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/meetings/{meeting_id}/transcripts")
            if response.status_code == 200:
                data = response.json()
                transcripts = data.get('data', {}).get('transcripts', [])
                
                if transcripts:
                    for i, transcript in enumerate(transcripts, 1):
                        speaker = transcript.get('speaker', 'Unknown')
                        text = transcript.get('text', 'No text')
                        start_time = transcript.get('start_time', 0)
                        confidence = transcript.get('confidence', 0)
                        
                        print(f"{i}. [{start_time:.1f}s] {speaker} (conf: {confidence:.2f})")
                        print(f"   {text}")
                        print()
                else:
                    print("No transcripts found.")
                
                return transcripts
            else:
                print(f"❌ Transcripts not found: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def get_analysis(self, meeting_id):
        """Get meeting analysis"""
        print(f"\n🧠 ANALYSIS: {meeting_id[:8]}...")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/meetings/{meeting_id}/analysis")
            if response.status_code == 200:
                data = response.json()
                analysis = data.get('data', {})
                
                # Summary
                summary = analysis.get('summary', {})
                print(f"Executive Summary:")
                print(f"  {summary.get('executive_summary', 'N/A')}")
                
                # Topics
                topics = summary.get('main_topics', [])
                if topics:
                    print(f"\nMain Topics:")
                    for i, topic in enumerate(topics, 1):
                        print(f"  {i}. {topic}")
                
                # Action Items
                action_items = analysis.get('action_items', [])
                if action_items:
                    print(f"\nAction Items:")
                    for i, item in enumerate(action_items, 1):
                        assignee = item.get('assignee', 'Unassigned')
                        priority = item.get('priority', 'medium')
                        description = item.get('description', item.get('task', 'No description'))
                        print(f"  {i}. [{priority.upper()}] {description} - {assignee}")
                
                # Key Points
                key_points = analysis.get('key_points', [])
                if key_points:
                    print(f"\nKey Points:")
                    for i, point in enumerate(key_points, 1):
                        print(f"  {i}. {point}")
                
                print(f"\nProvider: {analysis.get('llm_provider', 'Unknown')}")
                return analysis
            else:
                print(f"❌ Analysis not found: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def interactive_test(self):
        """Run interactive test session"""
        print("🎯 VOICELINK INTERACTIVE TESTER")
        print("=" * 50)
        
        # Test health first
        if not self.test_health():
            print("❌ Cannot continue - system is not healthy")
            return
        
        # Get statistics
        self.get_statistics()
        
        # List meetings
        meetings = self.list_meetings()
        
        if not meetings:
            print("\n💡 No meetings found. Run 'python final_demo.py' to create test data.")
            return
        
        # Interactive meeting selection
        print("\n🔍 SELECT A MEETING TO EXPLORE:")
        print("-" * 40)
        
        for i, meeting in enumerate(meetings, 1):
            print(f"{i}. {meeting.get('title', 'Untitled')} ({meeting.get('status', 'Unknown')})")
        
        try:
            choice = input(f"\nEnter meeting number (1-{len(meetings)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                return
            
            choice = int(choice)
            if 1 <= choice <= len(meetings):
                selected_meeting = meetings[choice - 1]
                meeting_id = selected_meeting['id']
                
                # Show full details for selected meeting
                self.get_meeting_details(meeting_id)
                self.get_transcripts(meeting_id)
                self.get_analysis(meeting_id)
                
                print("\n🎉 Test completed successfully!")
            else:
                print("❌ Invalid choice")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Test interrupted by user")

def main():
    """Main test function"""
    tester = VoiceLinkTester()
    tester.interactive_test()

if __name__ == "__main__":
    main()
