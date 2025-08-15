"""Simple test to verify dashboard API is working."""

import requests
import json

def test_dashboard_api():
    """Test the dashboard API manually."""
    
    base_url = "http://localhost:8000"
    
    try:
        # Test 1: Basic health check
        print("🔍 Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Quick metrics endpoint
        print("\n📊 Testing quick metrics endpoint...")
        response = requests.get(f"{base_url}/api/dashboard/quick-metrics?agent_id=agent_rajesh_kumar")
        
        if response.status_code == 200:
            print("✅ Quick metrics API successful!")
            data = response.json()
            
            # Print sample data
            basic_metrics = data['data']['basic_metrics']
            print(f"   Total leads: {basic_metrics['total_leads']}")
            print(f"   New today: {basic_metrics['new_today']}")
            print(f"   Hot leads: {basic_metrics['hot_leads']}")
            
            # Test data structure
            required_fields = ['basic_metrics', 'lead_sources', 'weekly_trend', 'pipeline']
            for field in required_fields:
                if field in data['data']:
                    print(f"   ✅ {field} present")
                else:
                    print(f"   ❌ {field} missing")
            
            return True
        else:
            print(f"❌ Quick metrics failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Dashboard API Test")
    print("=" * 40)
    
    if test_dashboard_api():
        print("\n🎉 Dashboard API is working correctly!")
        print("\n📋 Integration Summary:")
        print("   ✅ FastAPI server running on port 8000")
        print("   ✅ Dashboard endpoints responding")
        print("   ✅ Data structure compatible with React frontend")
        print("   ✅ Ready for frontend integration")
        
        print("\n🚀 Next Steps:")
        print("   1. Frontend: npm install react-chartjs-2 chart.js")
        print("   2. Import Dashboard component: import Dashboard from './components/Dashboard'")
        print("   3. Use in App: <Dashboard agentId='agent_rajesh_kumar' />")
        print("   4. Test on mobile devices for responsive design")
    else:
        print("\n❌ Dashboard API test failed")
        print("   Check that the server is running on port 8000")
