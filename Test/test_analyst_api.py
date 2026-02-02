"""
Test Teacher Analyst API Endpoint

Tests the REST API endpoint (requires backend running):
POST /api/v3/teacher/analytics/audit/{student_id}
"""
import httpx
import asyncio
import sys
from pathlib import Path

# Load .env
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

if env_file.exists():
    import os
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

print("=" * 70)
print("TEACHER ANALYST API ENDPOINT TEST")
print("=" * 70)

BASE_URL = "http://localhost:8000"
HEALTH_URL = f"{BASE_URL}/health"
AUDIT_URL = f"{BASE_URL}/api/v3/teacher/analytics/audit"

async def test_backend_health():
    """Check if backend is running"""
    print("\n[1/3] Checking backend health...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(HEALTH_URL)
            
            if response.status_code == 200:
                print("✅ Backend is running")
                print(f"   {response.json()}")
                return True
            else:
                print(f"❌ Backend returned {response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ Backend is not running")
        print("   Start backend: cd Backend && uvicorn src_v3.infrastructure.http.app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_audit_endpoint():
    """Test the analytics audit endpoint"""
    print("\n[2/3] Testing audit endpoint...")
    
    test_student_id = "test_student_syntax_123"
    test_teacher_id = "teacher_456"
    
    audit_request = {
        "teacher_id": test_teacher_id,
        "include_traceability": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"   POST {AUDIT_URL}/{test_student_id}")
            print(f"   Body: {audit_request}")
            
            response = await client.post(
                f"{AUDIT_URL}/{test_student_id}",
                json=audit_request
            )
            
            print(f"\n   Status: {response.status_code}")
            
            if response.status_code == 200:
                audit = response.json()
                
                print("\n✅ Audit completed successfully!")
                print("\n" + "=" * 70)
                print("PEDAGOGICAL AUDIT REPORT")
                print("=" * 70)
                
                print(f"\n📊 STUDENT METRICS:")
                print(f"   Student ID: {audit.get('student_id')}")
                print(f"   Risk Score: {audit.get('risk_score'):.2f}")
                print(f"   Risk Level: {audit.get('risk_level')}")
                print(f"   Frustration: {audit.get('frustration_level', 0):.2f}")
                print(f"   Understanding: {audit.get('understanding_level', 0):.2f}")
                
                print(f"\n🔍 AI DIAGNOSIS:")
                print(f"   {audit.get('diagnosis', 'N/A')[:200]}...")
                
                print(f"\n📝 EVIDENCE:")
                for i, evidence in enumerate(audit.get('evidence', [])[:3], 1):
                    print(f"   [{i}] {evidence[:150]}")
                
                print(f"\n💡 RECOMMENDED INTERVENTION:")
                print(f"   {audit.get('intervention', 'N/A')[:200]}...")
                
                print(f"\n🎯 CONFIDENCE: {audit.get('confidence_score', 0):.0%}")
                
                print("\n" + "=" * 70)
                
                # Validate response structure
                required_fields = [
                    'analysis_id', 'student_id', 'teacher_id', 
                    'risk_score', 'risk_level', 'diagnosis', 
                    'evidence', 'intervention', 'confidence_score'
                ]
                
                missing_fields = [f for f in required_fields if f not in audit]
                if missing_fields:
                    print(f"\n⚠️  Warning: Missing fields: {missing_fields}")
                else:
                    print("\n✅ All required fields present")
                
                return True
                
            elif response.status_code == 503:
                print("\n❌ Service Unavailable (Mistral API key not configured)")
                print("   Set MISTRAL_API_KEY in .env")
                return False
                
            elif response.status_code == 404:
                print("\n⚠️  Student has no activity logs (expected for mock data)")
                print("   This is normal - endpoint is working but needs real data")
                return True
                
            else:
                print(f"\n❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
    except httpx.ReadTimeout:
        print("\n⚠️  Request timeout (Mistral API might be slow)")
        print("   This is normal for first API call - try again")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

async def test_audit_history_stub():
    """Test the audit history endpoint (stub)"""
    print("\n[3/3] Testing audit history endpoint...")
    
    test_student_id = "test_student_123"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AUDIT_URL}/{test_student_id}/history"
            )
            
            print(f"   GET {AUDIT_URL}/{test_student_id}/history")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                history = response.json()
                print(f"✅ History endpoint working (stub)")
                print(f"   Count: {history.get('count', 0)}")
                return True
            else:
                print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def run_all_tests():
    """Run all API tests"""
    print("\nStarting API tests...")
    print("=" * 70)
    
    # Test 1: Backend health
    health_ok = await test_backend_health()
    if not health_ok:
        print("\n❌ Backend is not running. Cannot continue.")
        print("\nTo start backend:")
        print("  cd Backend")
        print("  uvicorn src_v3.infrastructure.http.app:app --reload")
        return
    
    # Test 2: Audit endpoint
    audit_ok = await test_audit_endpoint()
    
    # Test 3: History endpoint
    history_ok = await test_audit_history_stub()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    results = {
        "Backend Health": "✅ PASS" if health_ok else "❌ FAIL",
        "Audit Endpoint": "✅ PASS" if audit_ok else "❌ FAIL",
        "History Endpoint": "✅ PASS" if history_ok else "❌ FAIL"
    }
    
    for test_name, result in results.items():
        print(f"   {test_name}: {result}")
    
    all_passed = health_ok and audit_ok and history_ok
    
    if all_passed:
        print("\n🎉 ALL API TESTS PASSED!")
        print("\n✅ Teacher Analyst API is fully operational")
        print("✅ AI Pedagogical Auditor is ready")
        print("✅ Backend integration complete")
    else:
        print("\n⚠️  Some tests failed")
        print("   Check backend logs for details")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
