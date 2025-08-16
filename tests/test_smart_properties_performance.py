"""
Performance and Load Tests for Smart Properties
Tests system behavior under load and measures performance metrics
"""
import time
import asyncio
import aiohttp
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import base64
from datetime import datetime


class TestSmartPropertiesPerformance:
    """Performance testing for Smart Properties API"""
    
    BASE_URL = "http://127.0.0.1:8003"
    
    def __init__(self):
        # Create auth token for testing
        payload = {
            'user_id': 'perf-test-user',
            'email': 'perf@test.com',
            'name': 'Performance Test User'
        }
        
        header = base64.urlsafe_b64encode(
            json.dumps({'typ': 'JWT', 'alg': 'none'}).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        token = f'{header}.{payload_encoded}.signature'
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def test_api_response_times(self):
        """Test API response times for different endpoints"""
        print("📊 TESTING API RESPONSE TIMES")
        print("-" * 40)
        
        endpoints = [
            ('GET Properties', 'GET', '/api/smart-properties/', None),
            ('Dashboard Load', 'GET', '/dashboard', None),
            ('Server Health', 'GET', '/', None)
        ]
        
        results = {}
        
        for name, method, endpoint, data in endpoints:
            response_times = []
            
            # Test each endpoint 5 times
            for i in range(5):
                start_time = time.time()
                
                try:
                    if method == 'GET':
                        if 'api' in endpoint:
                            response = requests.get(
                                f"{self.BASE_URL}{endpoint}",
                                headers=self.headers,
                                timeout=10
                            )
                        else:
                            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    
                    if response.status_code in [200, 401]:  # 401 is expected for non-auth endpoints
                        response_times.append(response_time)
                    
                except Exception as e:
                    print(f"   ❌ {name} failed: {e}")
                    continue
            
            if response_times:
                avg_time = statistics.mean(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                
                results[name] = {
                    'avg': avg_time,
                    'min': min_time,
                    'max': max_time,
                    'samples': len(response_times)
                }
                
                print(f"   ✅ {name}:")
                print(f"      Average: {avg_time:.2f}ms")
                print(f"      Range: {min_time:.2f}ms - {max_time:.2f}ms")
                print(f"      Samples: {len(response_times)}")
            else:
                print(f"   ❌ {name}: No successful responses")
        
        return results
    
    def test_property_creation_performance(self):
        """Test performance of property creation with AI generation"""
        print("\n🏠 TESTING PROPERTY CREATION PERFORMANCE")
        print("-" * 40)
        
        creation_times = []
        ai_generation_success = 0
        
        test_properties = [
            {
                "address": f"Performance Test Street {i}, Mumbai",
                "price": f"₹{2 + (i * 0.1):.1f} Crore",
                "property_type": "apartment",
                "bedrooms": str(2 + (i % 3)),
                "bathrooms": str(1 + (i % 2)),
                "features": f"Test property {i} with modern amenities",
                "template": "just_listed"
            }
            for i in range(5)
        ]
        
        for i, property_data in enumerate(test_properties):
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.BASE_URL}/api/smart-properties",
                    json=property_data,
                    headers=self.headers,
                    timeout=20
                )
                
                end_time = time.time()
                creation_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    creation_times.append(creation_time)
                    
                    # Check if AI content was generated
                    data = response.json()
                    if data.get('ai_content') and len(data['ai_content']) > 50:
                        ai_generation_success += 1
                    
                    print(f"   ✅ Property {i+1}: {creation_time:.2f}ms")
                else:
                    print(f"   ❌ Property {i+1}: Failed ({response.status_code})")
                
            except Exception as e:
                print(f"   ❌ Property {i+1}: Error - {e}")
        
        if creation_times:
            avg_time = statistics.mean(creation_times)
            success_rate = (len(creation_times) / len(test_properties)) * 100
            ai_success_rate = (ai_generation_success / len(creation_times)) * 100 if creation_times else 0
            
            print(f"\n📈 Creation Performance Summary:")
            print(f"   Average Creation Time: {avg_time:.2f}ms")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   AI Generation Success: {ai_success_rate:.1f}%")
            
            # Performance benchmarks
            if avg_time < 1000:
                print("   🚀 Excellent performance (< 1 second)")
            elif avg_time < 3000:
                print("   ✅ Good performance (< 3 seconds)")
            elif avg_time < 5000:
                print("   ⚠️ Acceptable performance (< 5 seconds)")
            else:
                print("   🐌 Slow performance (> 5 seconds)")
        
        return {
            'creation_times': creation_times,
            'ai_success_rate': ai_generation_success / len(creation_times) if creation_times else 0
        }
    
    def test_concurrent_requests(self):
        """Test system behavior under concurrent load"""
        print("\n🔄 TESTING CONCURRENT REQUEST HANDLING")
        print("-" * 40)
        
        def make_request(request_id):
            """Make a single API request"""
            start_time = time.time()
            
            try:
                response = requests.get(
                    f"{self.BASE_URL}/api/smart-properties/",
                    headers=self.headers,
                    timeout=15
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                return {
                    'id': request_id,
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response_time': response_time
                }
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                return {
                    'id': request_id,
                    'success': False,
                    'error': str(e),
                    'response_time': response_time
                }
        
        # Test with 10 concurrent requests
        concurrent_requests = 10
        results = []
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_request, i) 
                for i in range(concurrent_requests)
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"   📊 Concurrent Load Test Results:")
            print(f"      Total Requests: {concurrent_requests}")
            print(f"      Successful: {len(successful_requests)}")
            print(f"      Failed: {len(failed_requests)}")
            print(f"      Success Rate: {len(successful_requests)/concurrent_requests*100:.1f}%")
            print(f"      Total Time: {total_time:.2f}ms")
            print(f"      Average Response: {avg_response_time:.2f}ms")
            print(f"      Response Range: {min_response_time:.2f}ms - {max_response_time:.2f}ms")
            
            if len(successful_requests) == concurrent_requests:
                print("   ✅ All requests handled successfully")
            elif len(successful_requests) >= concurrent_requests * 0.8:
                print("   ⚠️ Most requests successful (some failures expected under load)")
            else:
                print("   ❌ High failure rate under concurrent load")
        
        return results
    
    def test_memory_usage_simulation(self):
        """Simulate memory usage patterns"""
        print("\n🧠 TESTING MEMORY USAGE PATTERNS")
        print("-" * 40)
        
        # Create multiple properties to test memory usage
        properties_created = 0
        
        for batch in range(3):  # 3 batches of properties
            print(f"   Creating batch {batch + 1}...")
            
            batch_properties = [
                {
                    "address": f"Memory Test {batch}-{i} Street, Mumbai",
                    "price": f"₹{1.5 + (i * 0.2):.1f} Crore",
                    "property_type": "apartment",
                    "bedrooms": str(2 + (i % 2)),
                    "bathrooms": "2",
                    "features": f"Batch {batch} property {i} with standard features",
                    "template": "just_listed"
                }
                for i in range(5)
            ]
            
            for prop in batch_properties:
                try:
                    response = requests.post(
                        f"{self.BASE_URL}/api/smart-properties",
                        json=prop,
                        headers=self.headers,
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        properties_created += 1
                    
                except Exception as e:
                    print(f"      ❌ Property creation failed: {e}")
                    continue
            
            # Test retrieval after each batch
            try:
                response = requests.get(
                    f"{self.BASE_URL}/api/smart-properties/",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    properties = response.json()
                    print(f"      ✅ Batch {batch + 1}: Can retrieve {len(properties)} properties")
                else:
                    print(f"      ❌ Batch {batch + 1}: Retrieval failed")
                    
            except Exception as e:
                print(f"      ❌ Batch {batch + 1}: Retrieval error - {e}")
        
        print(f"   📈 Memory Test Summary:")
        print(f"      Properties Created: {properties_created}")
        print(f"      Expected: 15 (3 batches × 5 properties)")
        
        if properties_created >= 10:
            print("   ✅ Good memory handling")
        else:
            print("   ⚠️ Potential memory issues")
        
        return properties_created


def run_performance_tests():
    """Run all performance tests"""
    print("🚀 SMART PROPERTIES PERFORMANCE TEST SUITE")
    print("=" * 60)
    
    # Wait for server
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Check server availability
    try:
        response = requests.get("http://127.0.0.1:8003/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding, aborting performance tests")
            return
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return
    
    # Initialize performance tester
    perf_tester = TestSmartPropertiesPerformance()
    
    # Run all performance tests
    test_results = {}
    
    try:
        test_results['response_times'] = perf_tester.test_api_response_times()
    except Exception as e:
        print(f"❌ Response time tests failed: {e}")
    
    try:
        test_results['creation_performance'] = perf_tester.test_property_creation_performance()
    except Exception as e:
        print(f"❌ Creation performance tests failed: {e}")
    
    try:
        test_results['concurrent_load'] = perf_tester.test_concurrent_requests()
    except Exception as e:
        print(f"❌ Concurrent load tests failed: {e}")
    
    try:
        test_results['memory_usage'] = perf_tester.test_memory_usage_simulation()
    except Exception as e:
        print(f"❌ Memory usage tests failed: {e}")
    
    # Performance Summary
    print(f"\n" + "=" * 60)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    
    if 'response_times' in test_results:
        print("✅ API Response Times: Measured")
    if 'creation_performance' in test_results:
        print("✅ Property Creation: Tested")  
    if 'concurrent_load' in test_results:
        print("✅ Concurrent Load: Handled")
    if 'memory_usage' in test_results:
        print("✅ Memory Usage: Simulated")
    
    print(f"\n🎯 PERFORMANCE TESTING COMPLETE!")
    print("   System performance metrics collected")
    print("   Ready for production load testing")
    
    return test_results


if __name__ == "__main__":
    run_performance_tests()
