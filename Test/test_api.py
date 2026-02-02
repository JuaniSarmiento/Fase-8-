"""
Simple test script to verify API works
"""
import asyncio
import httpx


async def _run_endpoints():
    """Async worker that tests basic API endpoints.

    Wrapped by a synchronous pytest test so we don't depend on
    async-specific pytest plugins.
    """
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("=== Testing Fase 8 API ===\n")
        
        # Test 1: Health check
        print("[1/5] Testing health check...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check OK")
                print(f"  Version: {data.get('version')}")
                print(f"  Status: {data.get('status')}")
            else:
                print(f"✗ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Health check error: {e}")
        
        print()
        
        # Test 2: Root endpoint
        print("[2/5] Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Root endpoint OK")
                print(f"  Message: {data.get('message')}")
            else:
                print(f"✗ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Root endpoint error: {e}")
        
        print()
        
        # Test 3: API Docs
        print("[3/5] Testing API docs...")
        try:
            response = await client.get(f"{base_url}/api/v3/docs")
            if response.status_code == 200:
                print(f"✓ API docs accessible")
            else:
                print(f"✗ API docs failed: {response.status_code}")
        except Exception as e:
            print(f"✗ API docs error: {e}")
        
        print()
        
        # Test 4: Analytics endpoint (empty course)
        print("[4/5] Testing analytics endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v3/analytics/courses/TEST-COURSE")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Analytics endpoint OK")
                print(f"  Course ID: {data.get('course_id')}")
                print(f"  Total students: {data.get('total_students')}")
            else:
                print(f"✗ Analytics endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Analytics endpoint error: {e}")
        
        print()
        
        # Test 5: System info
        print("[5/5] Testing system info...")
        try:
            response = await client.get(f"{base_url}/api/v3/system/info")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ System info OK")
                print(f"  App: {data.get('app_name')}")
                print(f"  Architecture: {data.get('architecture')}")
            else:
                print(f"✗ System info failed: {response.status_code}")
        except Exception as e:
            print(f"✗ System info error: {e}")
        
        print("\n=== Test Complete ===")


def test_endpoints():
    """Pytest entrypoint that runs the async checks.

    Using asyncio.run allows this to work with vanilla pytest
    without additional async plugins.
    """
    asyncio.run(_run_endpoints())


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the API is running on http://localhost:8000\n")
    asyncio.run(_run_endpoints())
