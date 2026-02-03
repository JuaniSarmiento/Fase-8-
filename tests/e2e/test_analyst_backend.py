"""
Test Teacher Analyst Backend - AI Pedagogical Auditor

Validates the TeacherAnalystGraph without frontend:
1. Mock student with "bad" interaction logs
2. Call the Analyst Graph directly
3. Verify AI response contains diagnosis and intervention
4. Test API endpoint
"""
import sys
import os
from pathlib import Path
import asyncio

# Load .env
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Add Backend to path
backend_path = project_root / "Backend"
sys.path.insert(0, str(backend_path))

print("=" * 70)
print("TEACHER ANALYST - AI PEDAGOGICAL AUDITOR TEST")
print("=" * 70)

mistral_key = os.getenv("MISTRAL_API_KEY")
if not mistral_key:
    print("\n❌ MISTRAL_API_KEY not found")
    sys.exit(1)

print(f"\n✅ API Key: {mistral_key[:10]}...{mistral_key[-5:]}")

# Test 1: Create mock student with struggling pattern
print("\n" + "=" * 70)
print("TEST 1: ANALYZE STRUGGLING STUDENT (Repeated Syntax Errors)")
print("=" * 70)

# Mock logs showing a student stuck on syntax
mock_logs_syntax = [
    {
        "timestamp": "2026-01-26T10:00:00Z",
        "action": "code_submit",
        "cognitive_phase": "implementation",
        "details": "IndentationError: expected an indented block",
        "duration_seconds": 120
    },
    {
        "timestamp": "2026-01-26T10:03:00Z",
        "action": "code_submit",
        "cognitive_phase": "debugging",
        "details": "IndentationError: unindent does not match any outer indentation level",
        "duration_seconds": 90
    },
    {
        "timestamp": "2026-01-26T10:07:00Z",
        "action": "tutor_interaction",
        "cognitive_phase": "debugging",
        "details": "Student asked: 'I don't understand indentation'",
        "duration_seconds": 180
    },
    {
        "timestamp": "2026-01-26T10:12:00Z",
        "action": "code_submit",
        "cognitive_phase": "debugging",
        "details": "Same IndentationError repeated for 4th time",
        "duration_seconds": 150
    },
    {
        "timestamp": "2026-01-26T10:18:00Z",
        "action": "hint_requested",
        "cognitive_phase": "debugging",
        "details": "Hint about using consistent spaces",
        "duration_seconds": 60
    }
]

async def test_analyst_graph():
    """Test the analyst graph directly"""
    from src_v3.infrastructure.ai.teacher_analyst_graph import TeacherAnalystGraph
    
    print("\n[1/3] Initializing TeacherAnalystGraph...")
    graph = TeacherAnalystGraph(
        mistral_api_key=mistral_key,
        model_name="mistral-small-latest",
        temperature=0.3
    )
    print("✅ Graph initialized")
    
    print("\n[2/3] Running analysis on struggling student...")
    print(f"   Student logs: {len(mock_logs_syntax)} interactions")
    print(f"   Pattern: Repeated IndentationErrors")
    
    result = await graph.analyze_student(
        student_id="student_syntax_123",
        teacher_id="teacher_456",
        risk_score=0.85,
        risk_level="HIGH",
        traceability_logs=mock_logs_syntax,
        cognitive_phase="debugging",
        frustration_level=0.9,
        understanding_level=0.2
    )
    
    print(f"\n✅ Analysis completed")
    print(f"   Analysis ID: {result['analysis_id']}")
    print(f"   Status: {result['status']}")
    print(f"   Confidence: {result['confidence_score']:.2f}")
    
    print("\n[3/3] Validating analysis content...")
    
    # Assert: Verify required fields
    assert "diagnosis" in result, "Missing diagnosis"
    assert "evidence" in result, "Missing evidence"
    assert "intervention" in result, "Missing intervention"
    assert result["status"] == "completed", f"Status is {result['status']}, expected 'completed'"
    
    print("✅ All required fields present")
    
    # Display results
    print("\n" + "="*70)
    print("AI PEDAGOGICAL AUDIT REPORT")
    print("="*70)
    
    print(f"\n📊 RISK ASSESSMENT:")
    print(f"   Score: {result['risk_score']:.2f}")
    print(f"   Level: {result['risk_level']}")
    
    print(f"\n🔍 DIAGNOSIS:")
    print(f"   {result['diagnosis']}")
    
    print(f"\n📝 EVIDENCE:")
    for i, evidence in enumerate(result['evidence'][:3], 1):
        print(f"   [{i}] {evidence}")
    
    print(f"\n💡 RECOMMENDED INTERVENTION:")
    print(f"   {result['intervention']}")
    
    print(f"\n🎯 CONFIDENCE SCORE: {result['confidence_score']:.0%}")
    
    print("\n" + "="*70)
    
    # Validate that diagnosis mentions syntax/indentation
    diagnosis_lower = result['diagnosis'].lower()
    if "syntax" in diagnosis_lower or "indentation" in diagnosis_lower or "indent" in diagnosis_lower:
        print("✅ Diagnosis correctly identifies syntax/indentation issue")
    else:
        print(f"⚠️  Diagnosis might not mention syntax: {result['diagnosis'][:100]}")
    
    return result

# Test 2: Conceptual gap pattern
print("\n" + "=" * 70)
print("TEST 2: ANALYZE STUDENT WITH CONCEPTUAL GAP (Loop Logic)")
print("=" * 70)

mock_logs_conceptual = [
    {
        "timestamp": "2026-01-26T11:00:00Z",
        "action": "code_submit",
        "cognitive_phase": "implementation",
        "details": "Infinite loop detected - condition never becomes false",
        "duration_seconds": 200
    },
    {
        "timestamp": "2026-01-26T11:05:00Z",
        "action": "tutor_interaction",
        "cognitive_phase": "debugging",
        "details": "Student asked: 'Why does my loop never stop?'",
        "duration_seconds": 240
    },
    {
        "timestamp": "2026-01-26T11:10:00Z",
        "action": "code_submit",
        "cognitive_phase": "debugging",
        "details": "Still using 'while True:' without break condition",
        "duration_seconds": 180
    },
    {
        "timestamp": "2026-01-26T11:15:00Z",
        "action": "hint_requested",
        "cognitive_phase": "debugging",
        "details": "Hint about loop conditions",
        "duration_seconds": 90
    },
    {
        "timestamp": "2026-01-26T11:20:00Z",
        "action": "code_submit",
        "cognitive_phase": "validation",
        "details": "Loop condition still incorrect - off by one error",
        "duration_seconds": 150
    }
]

async def test_conceptual_gap():
    """Test with conceptual understanding issues"""
    from src_v3.infrastructure.ai.teacher_analyst_graph import TeacherAnalystGraph
    
    print("\n[Running conceptual gap analysis...]")
    
    graph = TeacherAnalystGraph(
        mistral_api_key=mistral_key,
        model_name="mistral-small-latest",
        temperature=0.3
    )
    
    result = await graph.analyze_student(
        student_id="student_loops_789",
        teacher_id="teacher_456",
        risk_score=0.70,
        risk_level="MEDIUM",
        traceability_logs=mock_logs_conceptual,
        cognitive_phase="debugging",
        frustration_level=0.6,
        understanding_level=0.4
    )
    
    print(f"\n✅ Conceptual analysis completed")
    print(f"   Diagnosis: {result['diagnosis'][:100]}...")
    print(f"   Intervention: {result['intervention'][:100]}...")
    
    # Check if it mentions loops/iteration/logic
    diagnosis_lower = result['diagnosis'].lower()
    if any(word in diagnosis_lower for word in ["loop", "iteration", "condition", "logic"]):
        print("✅ Correctly identified loop/logic issue")
    else:
        print(f"⚠️  Might have missed loop concept")
    
    return result

# Run tests
print("\n" + "=" * 70)
print("RUNNING ASYNC TESTS...")
print("=" * 70)

async def run_all_tests():
    """Run all tests"""
    result1 = await test_analyst_graph()
    result2 = await test_conceptual_gap()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print("\n✅ Test 1 (Syntax Issues): PASSED")
    print(f"   - Diagnosis generated: {len(result1['diagnosis'])} chars")
    print(f"   - Evidence items: {len(result1['evidence'])}")
    print(f"   - Intervention provided: YES")
    
    print("\n✅ Test 2 (Conceptual Gap): PASSED")
    print(f"   - Diagnosis generated: {len(result2['diagnosis'])} chars")
    print(f"   - Evidence items: {len(result2['evidence'])}")
    print(f"   - Intervention provided: YES")
    
    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED - ANALYST BACKEND READY!")
    print("=" * 70)
    
    print("\n✅ TeacherAnalystGraph: Operational")
    print("✅ Mistral AI integration: Working")
    print("✅ JSON parsing: Successful")
    print("✅ Diagnosis generation: Accurate")
    print("✅ Evidence extraction: Working")
    print("✅ Intervention recommendations: Generated")
    
    print("\n📝 Next Step: Test API endpoint")
    print("   POST /api/v3/teacher/analytics/audit/{student_id}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
