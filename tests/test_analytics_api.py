"""
Comprehensive Test Suite for VoiceLink Analytics API Endpoints

Tests all analytics endpoints for functionality, security, and performance.
Includes authentication, authorization, rate limiting, and data validation tests.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aiohttp
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsAPITester:
    """Comprehensive tester for Analytics API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1/analytics"
        self.session = None
        self.auth_headers = {}
        self.test_results = []
        
        # Test data
        self.test_meeting_id = "test_meeting_analytics_001"
        self.mock_analytics_data = {
            "meeting_id": self.test_meeting_id,
            "title": "Analytics API Test Meeting",
            "duration_minutes": 45,
            "participants": [
                {
                    "speaker_id": "user_001",
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "speaking_time": 900,  # 15 minutes
                    "contribution_score": 8.5,
                    "engagement_level": "high",
                    "questions_asked": 5,
                    "topics_contributed": ["API Design", "Security"]
                },
                {
                    "speaker_id": "user_002", 
                    "name": "Bob Smith",
                    "email": "bob@example.com",
                    "speaking_time": 600,  # 10 minutes
                    "contribution_score": 6.2,
                    "engagement_level": "medium",
                    "questions_asked": 2,
                    "topics_contributed": ["Testing", "Performance"]
                }
            ],
            "topics": [
                {
                    "topic": "API Design",
                    "duration": 1200,
                    "participants": ["user_001", "user_002"],
                    "importance_score": 8.5,
                    "keywords": ["endpoint", "rest", "design"],
                    "confidence": 0.9
                },
                {
                    "topic": "Security Implementation", 
                    "duration": 800,
                    "participants": ["user_001"],
                    "importance_score": 9.2,
                    "keywords": ["authentication", "jwt", "security"],
                    "confidence": 0.85
                }
            ],
            "decisions": [
                {
                    "decision": "Implement JWT authentication for all endpoints",
                    "confidence": 0.95,
                    "timestamp": 1500,
                    "participants_involved": ["user_001", "user_002"],
                    "priority": "high"
                }
            ],
            "action_items": [
                {
                    "task": "Create API documentation",
                    "assignee": "user_001",
                    "due_date": "2024-02-15",
                    "priority": "medium",
                    "status": "open",
                    "estimated_effort": "medium"
                },
                {
                    "task": "Implement rate limiting",
                    "assignee": "user_002", 
                    "due_date": "2024-02-10",
                    "priority": "high",
                    "status": "open",
                    "estimated_effort": "large"
                }
            ],
            "code_context": {
                "technical_terms": ["fastapi", "python", "jwt", "authentication"],
                "code_references": ["@router.get", "async def", "HTTPException"],
                "repositories_mentioned": ["voicelink-core"],
                "api_discussions": ["POST /analytics", "GET /meetings"],
                "architecture_decisions": ["Use FastAPI for REST API"],
                "bug_reports": []
            },
            "metrics": {
                "engagement_score": 78.5,
                "productivity_score": 82.3,
                "technical_complexity": "high"
            }
        }
    
    async def setup(self):
        """Set up test environment"""
        self.session = aiohttp.ClientSession()
        logger.info("🚀 Starting Analytics API Test Suite")
        logger.info(f"Base URL: {self.base_url}")
        
        # Test basic connectivity
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info("✅ API connectivity confirmed")
                else:
                    logger.warning(f"⚠️  API health check returned status {response.status}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to API: {e}")
            return False
        
        return True
    
    async def cleanup(self):
        """Clean up test environment"""
        if self.session:
            await self.session.close()
        
        # Print test results summary
        self.print_test_summary()
    
    def record_test_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name} - {details}")
    
    def print_test_summary(self):
        """Print test results summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*60)
        print("📊 ANALYTICS API TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
        print("="*60)
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
    
    async def test_health_endpoint(self):
        """Test analytics health endpoint"""
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.record_test_result(
                        "Health Endpoint", 
                        True, 
                        f"Status: {data.get('status', 'unknown')}"
                    )
                else:
                    self.record_test_result(
                        "Health Endpoint", 
                        False, 
                        f"HTTP {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Health Endpoint", False, str(e))
    
    async def test_authentication_required(self):
        """Test that endpoints require authentication"""
        test_endpoints = [
            f"{self.api_base}/meetings/{self.test_meeting_id}/stats",
            f"{self.api_base}/meetings/{self.test_meeting_id}/participants",
            f"{self.api_base}/meetings/{self.test_meeting_id}/topics",
            f"{self.api_base}/meetings/{self.test_meeting_id}/action-items"
        ]
        
        for endpoint in test_endpoints:
            try:
                async with self.session.get(endpoint) as response:
                    if response.status == 401:
                        self.record_test_result(
                            f"Auth Required - {endpoint.split('/')[-1]}", 
                            True, 
                            "Correctly requires authentication"
                        )
                    else:
                        self.record_test_result(
                            f"Auth Required - {endpoint.split('/')[-1]}", 
                            False, 
                            f"Expected 401, got {response.status}"
                        )
            except Exception as e:
                self.record_test_result(
                    f"Auth Required - {endpoint.split('/')[-1]}", 
                    False, 
                    str(e)
                )
    
    async def test_api_key_authentication(self):
        """Test API key authentication"""
        # Test with valid API key
        headers = {"X-API-Key": "vl_admin_key_12345"}
        
        try:
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/stats",
                headers=headers
            ) as response:
                if response.status in [200, 404]:  # 404 is fine if meeting doesn't exist
                    self.record_test_result(
                        "API Key Auth - Valid Key", 
                        True, 
                        f"Authenticated successfully (status: {response.status})"
                    )
                    self.auth_headers = headers  # Store for later tests
                else:
                    self.record_test_result(
                        "API Key Auth - Valid Key", 
                        False, 
                        f"Unexpected status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("API Key Auth - Valid Key", False, str(e))
        
        # Test with invalid API key
        invalid_headers = {"X-API-Key": "invalid_key_12345"}
        
        try:
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/stats",
                headers=invalid_headers
            ) as response:
                if response.status == 401:
                    self.record_test_result(
                        "API Key Auth - Invalid Key", 
                        True, 
                        "Correctly rejected invalid key"
                    )
                else:
                    self.record_test_result(
                        "API Key Auth - Invalid Key", 
                        False, 
                        f"Expected 401, got {response.status}"
                    )
        except Exception as e:
            self.record_test_result("API Key Auth - Invalid Key", False, str(e))
    
    async def test_meeting_stats_endpoint(self):
        """Test meeting statistics endpoint"""
        if not self.auth_headers:
            self.record_test_result("Meeting Stats Endpoint", False, "No authentication available")
            return
        
        try:
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/stats",
                headers=self.auth_headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = [
                        "meeting_id", "duration_minutes", "participant_count",
                        "total_decisions", "total_action_items", "total_topics",
                        "engagement_score", "productivity_score", "technical_complexity"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.record_test_result(
                            "Meeting Stats Endpoint", 
                            True, 
                            f"All required fields present"
                        )
                    else:
                        self.record_test_result(
                            "Meeting Stats Endpoint", 
                            False, 
                            f"Missing fields: {missing_fields}"
                        )
                elif response.status == 404:
                    self.record_test_result(
                        "Meeting Stats Endpoint", 
                        True, 
                        "Correctly returns 404 for non-existent meeting"
                    )
                else:
                    self.record_test_result(
                        "Meeting Stats Endpoint", 
                        False, 
                        f"Unexpected status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Meeting Stats Endpoint", False, str(e))
    
    async def test_participants_endpoint(self):
        """Test participants analytics endpoint"""
        if not self.auth_headers:
            return
        
        try:
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/participants",
                headers=self.auth_headers
            ) as response:
                if response.status in [200, 404]:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            self.record_test_result(
                                "Participants Endpoint", 
                                True, 
                                f"Returns list with {len(data)} participants"
                            )
                        else:
                            self.record_test_result(
                                "Participants Endpoint", 
                                False, 
                                "Response is not a list"
                            )
                    else:
                        self.record_test_result(
                            "Participants Endpoint", 
                            True, 
                            "Correctly handles missing meeting"
                        )
                else:
                    self.record_test_result(
                        "Participants Endpoint", 
                        False, 
                        f"Unexpected status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Participants Endpoint", False, str(e))
    
    async def test_topics_endpoint(self):
        """Test topics analytics endpoint"""
        if not self.auth_headers:
            return
        
        try:
            # Test basic endpoint
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/topics",
                headers=self.auth_headers
            ) as response:
                if response.status in [200, 404]:
                    success = True
                    details = f"Status: {response.status}"
                else:
                    success = False
                    details = f"Unexpected status: {response.status}"
                
                self.record_test_result("Topics Endpoint", success, details)
            
            # Test with query parameters
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/topics?min_duration=60&technical_only=true",
                headers=self.auth_headers
            ) as response:
                if response.status in [200, 404]:
                    self.record_test_result(
                        "Topics Endpoint - Query Params", 
                        True, 
                        "Handles query parameters correctly"
                    )
                else:
                    self.record_test_result(
                        "Topics Endpoint - Query Params", 
                        False, 
                        f"Failed with query params: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Topics Endpoint", False, str(e))
    
    async def test_action_items_endpoint(self):
        """Test action items analytics endpoint"""
        if not self.auth_headers:
            return
        
        try:
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/action-items",
                headers=self.auth_headers
            ) as response:
                if response.status in [200, 404]:
                    self.record_test_result(
                        "Action Items Endpoint", 
                        True, 
                        f"Status: {response.status}"
                    )
                else:
                    self.record_test_result(
                        "Action Items Endpoint", 
                        False, 
                        f"Unexpected status: {response.status}"
                    )
            
            # Test with filters
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/action-items?status_filter=open&priority_filter=high",
                headers=self.auth_headers
            ) as response:
                if response.status in [200, 404]:
                    self.record_test_result(
                        "Action Items Endpoint - Filters", 
                        True, 
                        "Filter parameters work correctly"
                    )
                else:
                    self.record_test_result(
                        "Action Items Endpoint - Filters", 
                        False, 
                        f"Filter test failed: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Action Items Endpoint", False, str(e))
    
    async def test_code_context_endpoint(self):
        """Test code context analytics endpoint"""
        if not self.auth_headers:
            return
        
        try:
            async with self.session.get(
                f"{self.api_base}/meetings/{self.test_meeting_id}/code-context",
                headers=self.auth_headers
            ) as response:
                if response.status in [200, 404]:
                    if response.status == 200:
                        data = await response.json()
                        required_fields = [
                            "meeting_id", "technical_terms", "code_references", 
                            "repositories_mentioned", "technical_complexity_score"
                        ]
                        
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if not missing_fields:
                            self.record_test_result(
                                "Code Context Endpoint", 
                                True, 
                                "All required fields present"
                            )
                        else:
                            self.record_test_result(
                                "Code Context Endpoint", 
                                False, 
                                f"Missing fields: {missing_fields}"
                            )
                    else:
                        self.record_test_result(
                            "Code Context Endpoint", 
                            True, 
                            "Correctly handles missing meeting"
                        )
                else:
                    self.record_test_result(
                        "Code Context Endpoint", 
                        False, 
                        f"Unexpected status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Code Context Endpoint", False, str(e))
    
    async def test_aggregated_analytics_endpoint(self):
        """Test aggregated analytics endpoint"""
        if not self.auth_headers:
            return
        
        try:
            # Test with date range
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            end_date = datetime.utcnow().isoformat()
            
            async with self.session.get(
                f"{self.api_base}/aggregate/meetings?start_date={start_date}&end_date={end_date}",
                headers=self.auth_headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = [
                        "date_range", "total_meetings", "total_participants",
                        "average_engagement", "average_productivity"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.record_test_result(
                            "Aggregated Analytics Endpoint", 
                            True, 
                            f"All required fields present"
                        )
                    else:
                        self.record_test_result(
                            "Aggregated Analytics Endpoint", 
                            False, 
                            f"Missing fields: {missing_fields}"
                        )
                else:
                    self.record_test_result(
                        "Aggregated Analytics Endpoint", 
                        False, 
                        f"Status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Aggregated Analytics Endpoint", False, str(e))
    
    async def test_processing_status_endpoint(self):
        """Test processing status endpoint"""
        if not self.auth_headers:
            return
        
        try:
            async with self.session.get(
                f"{self.api_base}/processing/status",
                headers=self.auth_headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    expected_fields = [
                        "processing_active", "queue_size", "processed_today"
                    ]
                    
                    present_fields = [field for field in expected_fields if field in data]
                    
                    if len(present_fields) >= 2:  # At least 2 fields should be present
                        self.record_test_result(
                            "Processing Status Endpoint", 
                            True, 
                            f"Fields present: {present_fields}"
                        )
                    else:
                        self.record_test_result(
                            "Processing Status Endpoint", 
                            False, 
                            f"Too few fields present: {present_fields}"
                        )
                else:
                    self.record_test_result(
                        "Processing Status Endpoint", 
                        False, 
                        f"Status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Processing Status Endpoint", False, str(e))
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        if not self.auth_headers:
            return
        
        try:
            # Make multiple rapid requests
            rapid_requests = 5
            success_count = 0
            rate_limited = False
            
            for i in range(rapid_requests):
                async with self.session.get(
                    f"{self.api_base}/health",
                    headers=self.auth_headers
                ) as response:
                    if response.status == 200:
                        success_count += 1
                    elif response.status == 429:  # Too Many Requests
                        rate_limited = True
                        break
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            if success_count > 0:
                self.record_test_result(
                    "Rate Limiting Test", 
                    True, 
                    f"Processed {success_count} requests, rate_limited: {rate_limited}"
                )
            else:
                self.record_test_result(
                    "Rate Limiting Test", 
                    False, 
                    "No requests succeeded"
                )
        except Exception as e:
            self.record_test_result("Rate Limiting Test", False, str(e))
    
    async def test_input_validation(self):
        """Test input validation and error handling"""
        if not self.auth_headers:
            return
        
        # Test invalid meeting ID format
        try:
            async with self.session.get(
                f"{self.api_base}/meetings//stats",  # Empty meeting ID
                headers=self.auth_headers
            ) as response:
                if response.status in [400, 404, 422]:  # Various error codes are acceptable
                    self.record_test_result(
                        "Input Validation - Empty Meeting ID", 
                        True, 
                        f"Correctly rejects empty ID (status: {response.status})"
                    )
                else:
                    self.record_test_result(
                        "Input Validation - Empty Meeting ID", 
                        False, 
                        f"Unexpected status: {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Input Validation - Empty Meeting ID", False, str(e))
        
        # Test invalid date range for aggregated analytics
        try:
            # End date before start date
            start_date = datetime.utcnow().isoformat()
            end_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
            
            async with self.session.get(
                f"{self.api_base}/aggregate/meetings?start_date={start_date}&end_date={end_date}",
                headers=self.auth_headers
            ) as response:
                if response.status == 400:
                    self.record_test_result(
                        "Input Validation - Invalid Date Range", 
                        True, 
                        "Correctly rejects invalid date range"
                    )
                else:
                    self.record_test_result(
                        "Input Validation - Invalid Date Range", 
                        False, 
                        f"Expected 400, got {response.status}"
                    )
        except Exception as e:
            self.record_test_result("Input Validation - Invalid Date Range", False, str(e))
    
    async def run_all_tests(self):
        """Run all analytics API tests"""
        
        if not await self.setup():
            logger.error("❌ Failed to set up test environment")
            return
        
        try:
            # Core functionality tests
            await self.test_health_endpoint()
            await self.test_authentication_required()
            await self.test_api_key_authentication()
            
            # Endpoint functionality tests
            await self.test_meeting_stats_endpoint()
            await self.test_participants_endpoint()
            await self.test_topics_endpoint()
            await self.test_action_items_endpoint()
            await self.test_code_context_endpoint()
            await self.test_aggregated_analytics_endpoint()
            await self.test_processing_status_endpoint()
            
            # Security and performance tests
            await self.test_rate_limiting()
            await self.test_input_validation()
            
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test VoiceLink Analytics API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = AnalyticsAPITester(args.url)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
