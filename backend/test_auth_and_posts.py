import asyncio
import aiohttp
import json

async def test_auth_and_posts():
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Check if the server is running
            print("=== TESTING SERVER CONNECTIVITY ===")
            try:
                async with session.get(f"{base_url}/docs") as response:
                    print(f"Server status: {response.status}")
                    if response.status == 200:
                        print("✅ Server is running")
                    else:
                        print("❌ Server is not responding properly")
                        return
            except Exception as e:
                print(f"❌ Cannot connect to server: {e}")
                return
            
            # Test 2: Check authentication endpoint
            print("\n=== TESTING AUTHENTICATION ===")
            try:
                # Try to get posts without authentication
                async with session.get(f"{base_url}/api/v1/enhanced-posts/posts/") as response:
                    print(f"Enhanced posts endpoint status: {response.status}")
                    if response.status == 401:
                        print("✅ Authentication is required (expected)")
                    else:
                        print(f"❌ Unexpected status: {response.status}")
                        text = await response.text()
                        print(f"Response: {text[:200]}...")
            except Exception as e:
                print(f"❌ Error testing authentication: {e}")
            
            # Test 3: Check unified publishing endpoint
            print("\n=== TESTING UNIFIED PUBLISHING ENDPOINT ===")
            try:
                # Try to access unified publishing endpoint
                async with session.get(f"{base_url}/api/v1/publishing/publish") as response:
                    print(f"Unified publishing endpoint status: {response.status}")
                    if response.status == 405:  # Method not allowed for GET
                        print("✅ Unified publishing endpoint exists")
                    else:
                        print(f"❌ Unexpected status: {response.status}")
                        text = await response.text()
                        print(f"Response: {text[:200]}...")
            except Exception as e:
                print(f"❌ Error testing unified publishing: {e}")
            
            # Test 4: Check if we can get any public endpoints
            print("\n=== TESTING PUBLIC ENDPOINTS ===")
            try:
                async with session.get(f"{base_url}/api/v1/agent/public/test/posts") as response:
                    print(f"Public agent posts endpoint status: {response.status}")
                    if response.status == 200:
                        print("✅ Public endpoints are working")
                        data = await response.json()
                        print(f"Response data: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        print(f"❌ Public endpoint failed: {response.status}")
                        text = await response.text()
                        print(f"Response: {text[:200]}...")
            except Exception as e:
                print(f"❌ Error testing public endpoints: {e}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_and_posts())
