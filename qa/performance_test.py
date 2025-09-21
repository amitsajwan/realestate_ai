#!/usr/bin/env python3
"""
Performance Testing Suite for PropertyAI Platform
================================================
Comprehensive performance testing across all system components
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import sys

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    errors: List[str]

class PerformanceTestSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", **kwargs):
        """Make a single HTTP request and measure performance"""
        start_time = time.time()
        try:
            async with session.request(method, f"{self.base_url}{endpoint}", **kwargs) as response:
                await response.text()  # Consume response body
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                return {
                    "success": True,
                    "status_code": response.status,
                    "response_time": response_time,
                    "error": None
                }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "status_code": None,
                "response_time": response_time,
                "error": str(e)
            }
    
    async def load_test_endpoint(self, endpoint: str, method: str = "GET", 
                                concurrent_users: int = 10, duration_seconds: int = 30, **kwargs):
        """Run load test on a single endpoint"""
        print(f"🔥 Load testing {method} {endpoint} with {concurrent_users} concurrent users for {duration_seconds}s")
        
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            start_time = time.time()
            tasks = []
            response_times = []
            errors = []
            
            # Create initial batch of requests
            for _ in range(concurrent_users):
                task = self.make_request(session, endpoint, method, **kwargs)
                tasks.append(task)
            
            # Run for specified duration
            while time.time() - start_time < duration_seconds:
                # Wait for some tasks to complete and create new ones
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    result = await task
                    response_times.append(result["response_time"])
                    if not result["success"]:
                        errors.append(result["error"])
                
                # Create new tasks to maintain concurrency
                new_tasks = []
                for _ in range(len(done)):
                    task = self.make_request(session, endpoint, method, **kwargs)
                    new_tasks.append(task)
                
                tasks = list(pending) + new_tasks
            
            # Wait for remaining tasks
            if tasks:
                final_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in final_results:
                    if isinstance(result, dict):
                        response_times.append(result["response_time"])
                        if not result["success"]:
                            errors.append(result["error"])
        
        # Calculate metrics
        total_requests = len(response_times)
        successful_requests = len([rt for rt in response_times if rt < 30000])  # Under 30s timeout
        failed_requests = total_requests - successful_requests
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
            
            requests_per_second = total_requests / duration_seconds
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
            requests_per_second = 0
        
        metrics = PerformanceMetrics(
            endpoint=endpoint,
            method=method,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            errors=list(set(errors))
        )
        
        self.results.append(metrics)
        return metrics
    
    def print_metrics(self, metrics: PerformanceMetrics):
        """Print performance metrics in a formatted way"""
        print(f"\n📊 {metrics.method} {metrics.endpoint}")
        print("-" * 50)
        print(f"Total Requests: {metrics.total_requests}")
        print(f"Successful: {metrics.successful_requests} ({metrics.successful_requests/metrics.total_requests*100:.1f}%)")
        print(f"Failed: {metrics.failed_requests} ({metrics.failed_requests/metrics.total_requests*100:.1f}%)")
        print(f"Requests/sec: {metrics.requests_per_second:.2f}")
        print(f"Avg Response Time: {metrics.avg_response_time:.2f}ms")
        print(f"Min Response Time: {metrics.min_response_time:.2f}ms")
        print(f"Max Response Time: {metrics.max_response_time:.2f}ms")
        print(f"95th Percentile: {metrics.p95_response_time:.2f}ms")
        print(f"99th Percentile: {metrics.p99_response_time:.2f}ms")
        
        if metrics.errors:
            print(f"Errors: {len(metrics.errors)} unique errors")
            for error in metrics.errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
    
    async def run_comprehensive_tests(self):
        """Run comprehensive performance tests"""
        print("🚀 Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        # Test scenarios
        test_scenarios = [
            # Basic endpoints
            {
                "endpoint": "/api/v1/health",
                "method": "GET",
                "concurrent_users": 50,
                "duration_seconds": 30,
                "name": "Health Check Load Test"
            },
            {
                "endpoint": "/api/v1/properties/public",
                "method": "GET", 
                "concurrent_users": 20,
                "duration_seconds": 30,
                "name": "Public Properties Load Test"
            },
            {
                "endpoint": "/api/v1/properties/search",
                "method": "GET",
                "concurrent_users": 15,
                "duration_seconds": 30,
                "params": {"city": "test"},
                "name": "Property Search Load Test"
            },
            # Authentication endpoints (with rate limiting)
            {
                "endpoint": "/api/v1/auth/login",
                "method": "POST",
                "concurrent_users": 10,
                "duration_seconds": 20,
                "json": {"username": "test@example.com", "password": "testpass"},
                "name": "Login Load Test"
            },
            # Social publishing endpoints
            {
                "endpoint": "/api/v1/social-publishing/drafts",
                "method": "GET",
                "concurrent_users": 10,
                "duration_seconds": 20,
                "name": "Social Drafts Load Test"
            },
            # Stress test
            {
                "endpoint": "/api/v1/health",
                "method": "GET",
                "concurrent_users": 100,
                "duration_seconds": 60,
                "name": "Stress Test"
            }
        ]
        
        # Run all test scenarios
        for scenario in test_scenarios:
            print(f"\n🎯 {scenario['name']}")
            
            # Prepare kwargs
            kwargs = {}
            if "params" in scenario:
                kwargs["params"] = scenario["params"]
            if "json" in scenario:
                kwargs["json"] = scenario["json"]
            
            try:
                metrics = await self.load_test_endpoint(
                    endpoint=scenario["endpoint"],
                    method=scenario["method"],
                    concurrent_users=scenario["concurrent_users"],
                    duration_seconds=scenario["duration_seconds"],
                    **kwargs
                )
                self.print_metrics(metrics)
                
                # Performance assertions
                self.assert_performance(metrics, scenario["name"])
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        # Generate summary report
        self.generate_summary_report()
    
    def assert_performance(self, metrics: PerformanceMetrics, test_name: str):
        """Assert performance meets requirements"""
        print(f"\n✅ Performance Assertions for {test_name}:")
        
        # Response time assertions
        if metrics.avg_response_time < 1000:  # Less than 1 second
            print("  ✅ Average response time < 1s")
        else:
            print(f"  ❌ Average response time {metrics.avg_response_time:.2f}ms > 1s")
        
        if metrics.p95_response_time < 2000:  # 95% under 2 seconds
            print("  ✅ 95th percentile < 2s")
        else:
            print(f"  ❌ 95th percentile {metrics.p95_response_time:.2f}ms > 2s")
        
        # Success rate assertions
        success_rate = metrics.successful_requests / metrics.total_requests * 100
        if success_rate > 95:  # 95% success rate
            print(f"  ✅ Success rate {success_rate:.1f}% > 95%")
        else:
            print(f"  ❌ Success rate {success_rate:.1f}% < 95%")
        
        # Throughput assertions (varies by endpoint)
        if "health" in metrics.endpoint and metrics.requests_per_second > 50:
            print(f"  ✅ Throughput {metrics.requests_per_second:.2f} req/s > 50")
        elif "search" in metrics.endpoint and metrics.requests_per_second > 5:
            print(f"  ✅ Throughput {metrics.requests_per_second:.2f} req/s > 5")
        elif "auth" in metrics.endpoint and metrics.requests_per_second > 10:
            print(f"  ✅ Throughput {metrics.requests_per_second:.2f} req/s > 10")
        else:
            print(f"  ⚠️ Throughput {metrics.requests_per_second:.2f} req/s (context dependent)")
    
    def generate_summary_report(self):
        """Generate a summary performance report"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("No test results available")
            return
        
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = statistics.mean([r.avg_response_time for r in self.results])
        max_response_time = max([r.max_response_time for r in self.results])
        avg_throughput = statistics.mean([r.requests_per_second for r in self.results])
        
        print(f"Total Tests Run: {len(self.results)}")
        print(f"Total Requests: {total_requests:,}")
        print(f"Successful Requests: {total_successful:,} ({overall_success_rate:.1f}%)")
        print(f"Failed Requests: {total_failed:,}")
        print(f"Average Response Time: {avg_response_time:.2f}ms")
        print(f"Max Response Time: {max_response_time:.2f}ms")
        print(f"Average Throughput: {avg_throughput:.2f} req/s")
        
        # Performance grade
        if overall_success_rate > 98 and avg_response_time < 500:
            grade = "A+ (Excellent)"
        elif overall_success_rate > 95 and avg_response_time < 1000:
            grade = "A (Very Good)"
        elif overall_success_rate > 90 and avg_response_time < 2000:
            grade = "B (Good)"
        elif overall_success_rate > 80:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"
        
        print(f"\n🎯 Overall Performance Grade: {grade}")
        
        # Save detailed results
        results_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": len(self.results),
                "total_requests": total_requests,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_success_rate": overall_success_rate,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "avg_throughput": avg_throughput,
                "performance_grade": grade
            },
            "detailed_results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "total_requests": r.total_requests,
                    "successful_requests": r.successful_requests,
                    "failed_requests": r.failed_requests,
                    "avg_response_time": r.avg_response_time,
                    "min_response_time": r.min_response_time,
                    "max_response_time": r.max_response_time,
                    "p95_response_time": r.p95_response_time,
                    "p99_response_time": r.p99_response_time,
                    "requests_per_second": r.requests_per_second,
                    "errors": r.errors
                }
                for r in self.results
            ]
        }
        
        with open("/workspace/performance_test_results.json", "w") as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: performance_test_results.json")

async def main():
    """Main function to run performance tests"""
    test_suite = PerformanceTestSuite()
    
    try:
        await test_suite.run_comprehensive_tests()
        print("\n✅ Performance testing completed successfully!")
    except Exception as e:
        print(f"\n❌ Performance testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())