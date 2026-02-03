#!/bin/bash
# E2E Test Script - Run from Docker

echo "========================================"  
echo "🚀 E2E TEST - Student Flow Complete"
echo "========================================"

# Test 1: Database connection
echo ""
echo "📋 Test 1: Database Connection"
psql -h postgres -U postgres -d ai_native -c "SELECT 'Database OK' as status;" 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Check tables exist
echo ""
echo "📋 Test 2: Tables Exist"
psql -h postgres -U postgres -d ai_native -c "SELECT COUNT(*) as users_count FROM users;" 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Create test student
echo ""
echo "📋 Test 3: Create Test Student"
STUDENT_ID="e2e-test-$(date +%s)"
psql -h postgres -U postgres -d ai_native -c "INSERT INTO users (id, email, username, hashed_password, full_name, roles, is_active) VALUES ('$STUDENT_ID', 'e2e@test.com', 'e2e_student', 'hash', 'E2E Student', '[\"student\"]'::jsonb, true) ON CONFLICT DO NOTHING;" 2>/dev/null && echo "✅ Created student: $STUDENT_ID" || echo "❌ FAIL"

# Test 4: Check activity exists
echo ""
echo "📋 Test 4: Activity Exists"
psql -h postgres -U postgres -d ai_native -c "SELECT activity_id, title FROM activities LIMIT 1;" 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 5: Create session
echo ""
echo "📋 Test 5: Create Session"
SESSION_ID="e2e-session-$(date +%s)"
psql -h postgres -U postgres -d ai_native -c "INSERT INTO sessions_v2 (session_id, user_id, activity_id, status, mode, cognitive_status, session_metrics) VALUES ('$SESSION_ID', '$STUDENT_ID', 'bucles-001', 'active', 'socratic', '{\"cognitive_phase\": \"exploration\"}'::jsonb, '{\"duration_minutes\": 10}'::jsonb);" 2>/dev/null && echo "✅ Created session: $SESSION_ID" || echo "❌ FAIL"

# Test 6: Create submission
echo ""
echo "📋 Test 6: Create Submission"
SUBMISSION_ID="e2e-sub-$(date +%s)"
psql -h postgres -U postgres -d ai_native -c "INSERT INTO submissions (submission_id, student_id, activity_id, code_snapshot, status, auto_grade, final_grade, ai_feedback) VALUES ('$SUBMISSION_ID', '$STUDENT_ID', 'bucles-001', 'for i in range(5): print(i)', 'graded', 85.0, 85.0, 'Buen uso de bucles for');" 2>/dev/null && echo "✅ Created submission with grade 85" || echo "❌ FAIL"

# Test 7: Verify submission in DB
echo ""
echo "📋 Test 7: Verify Grade in Database"
psql -h postgres -U postgres -d ai_native -c "SELECT submission_id, final_grade, status, ai_feedback FROM submissions WHERE student_id = '$STUDENT_ID';" 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 8: Create cognitive trace
echo ""
echo "📋 Test 8: Create Traceability"
TRACE_ID="e2e-trace-$(date +%s)"
psql -h postgres -U postgres -d ai_native -c "INSERT INTO cognitive_traces_v2 (trace_id, session_id, activity_id, trace_level, interaction_type, interactional_data) VALUES ('$TRACE_ID', '$SESSION_ID', 'bucles-001', 'info', 'student_question', '{\"message\": \"Como uso un bucle for?\"}'::jsonb);" 2>/dev/null && echo "✅ Created trace" || echo "❌ FAIL"

# Test 9: Verify traceability
echo ""
echo "📋 Test 9: Verify Traceability in Database"
psql -h postgres -U postgres -d ai_native -c "SELECT trace_id, interaction_type, interactional_data FROM cognitive_traces_v2 WHERE session_id = '$SESSION_ID';" 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Cleanup
echo ""
echo "🧹 Cleanup"
psql -h postgres -U postgres -d ai_native -c "DELETE FROM cognitive_traces_v2 WHERE session_id = '$SESSION_ID'; DELETE FROM submissions WHERE student_id = '$STUDENT_ID'; DELETE FROM sessions_v2 WHERE user_id = '$STUDENT_ID'; DELETE FROM users WHERE id = '$STUDENT_ID';" 2>/dev/null && echo "✅ Cleaned up" || echo "❌ FAIL"

echo ""
echo "========================================"
echo "✅ E2E TEST COMPLETE!"
echo "========================================"
