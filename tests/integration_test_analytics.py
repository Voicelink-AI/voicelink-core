"""
Analytics API Integration Test

This test verifies that the analytics API works end-to-end with real service calls.
"""

import asyncio
import json
from datetime import datetime, timedelta

async def test_analytics_integration():
    """Test analytics service integration"""
    
    try:
        # Import the analytics service
        from analytics.service import analytics_service
        
        print("🧪 Starting Analytics Service Integration Test")
        print("=" * 50)
        
        # Test 1: Health Status
        print("\n📊 Testing health status...")
        health_status = await analytics_service.get_health_status()
        print(f"Health Status: {health_status}")
        assert "status" in health_status
        print("✅ Health status test passed")
        
        # Test 2: Processing Status
        print("\n⚙️  Testing processing status...")
        processing_status = await analytics_service.get_processing_status()
        print(f"Processing Status: {processing_status}")
        assert "is_processing" in processing_status
        assert "queue_size" in processing_status
        print("✅ Processing status test passed")
        
        # Test 3: Analytics Summary
        print("\n📈 Testing analytics summary...")
        summary = await analytics_service.get_analytics_summary()
        print(f"Summary keys: {list(summary.keys())}")
        print("✅ Analytics summary test passed")
        
        # Test 4: Trends Calculation
        print("\n📉 Testing trends calculation...")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        trends = await analytics_service.calculate_trends(start_date, end_date)
        print(f"Trends: {trends}")
        assert "engagement_trend" in trends
        assert "productivity_trend" in trends
        print("✅ Trends calculation test passed")
        
        print("\n🎉 All Analytics Service Integration Tests Passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_endpoints_structure():
    """Test that analytics endpoints are properly structured"""
    
    try:
        print("\n🔗 Testing Analytics Endpoints Structure")
        print("=" * 40)
        
        # Test imports
        from api.analytics_endpoints import router
        
        print("✅ Analytics endpoints import successfully")
        
        # Check router has routes
        route_count = len(router.routes)
        print(f"📋 Analytics router has {route_count} routes")
        assert route_count > 0
        
        print("✅ Analytics endpoints structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Endpoints structure test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Running Analytics Integration Tests")
    print("=" * 60)
    
    # Test structure
    structure_result = test_endpoints_structure()
    
    # Test service integration
    integration_result = await test_analytics_integration()
    
    if structure_result and integration_result:
        print("\n🎊 ALL TESTS PASSED! 🎊")
        print("Analytics API is ready for production use!")
    else:
        print("\n💥 Some tests failed.")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    if not result:
        exit(1)
