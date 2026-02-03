# Backend API Reference - src_v3
## Complete Technical Summary for Frontend Development

**Base URL**: `http://localhost:8000/api/v3`

---

## Table of Contents
1. [Authentication](#authentication)
2. [Router: Auth](#router-auth)
3. [Router: Student](#router-student)
4. [Router: Teacher](#router-teacher)
5. [Router: Admin](#router-admin)
6. [Router: Analytics](#router-analytics)
7. [Router: Governance](#router-governance)
8. [Router: Catalog](#router-catalog)
9. [Router: Enrollments](#router-enrollments)
10. [Router: Notifications](#router-notifications)
11. [Database Models](#database-models)
12. [Enums & Constants](#enums--constants)

---

## Authentication

### JWT Token Handling
- **Header**: `Authorization: Bearer <token>`
- **Algorithm**: HS256
- **Access Token Expiry**: 30 minutes (default)
- **Refresh Token Expiry**: 7 days (default)
- **Token Payload**: `{ "user_id": "string", "exp": timestamp, "type": "access|refresh" }`

### Login Endpoint
- **POST** `/api/v3/auth/login`

### Security Functions
- Password hashing: bcrypt (12 rounds)
- Token generation: JWT (jose library)
- Token validation: Automatic via `oauth2_scheme` dependency

---

## Router: Auth

**Prefix**: `/api/v3/auth`  
**Tag**: `Authentication`

### Endpoints

#### POST `/auth/login`
**Description**: JSON login with email/password  
**Body**: `LoginRequest`
```json
{
  "email": "string",
  "password": "string"
}
```
**Response**: `UserWithTokensResponse`
```json
{
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "full_name": "string | null",
    "roles": ["string"],
    "is_active": true
  },
  "tokens": {
    "access_token": "string",
    "refresh_token": "string | null",
    "token_type": "bearer"
  }
}
```

#### POST `/auth/token`
**Description**: OAuth2 form login (for Swagger)  
**Body**: Form data (`username`, `password`)  
**Response**: `TokensSchema`
```json
{
  "access_token": "string",
  "refresh_token": "string | null",
  "token_type": "bearer"
}
```

#### POST `/auth/register`
**Description**: Register new user  
**Body**: `RegisterRequest`
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string | null",
  "role": "student"
}
```
**Response**: `UserWithTokensResponse`

#### GET `/auth/me`
**Description**: Get current user info  
**Headers**: `Authorization: Bearer <token>`  
**Response**: `UserResponse`
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "full_name": "string | null",
  "roles": ["string"],
  "is_active": true
}
```

#### POST `/auth/refresh`
**Description**: Refresh access token  
**Body**: `{ "refresh_token": "string" }`  
**Response**: `TokensSchema`

---

## Router: Student

**Prefix**: `/api/v3/student`  
**Tag**: `Student`

### Endpoints

#### POST `/student/sessions`
**Description**: Start new learning session  
**Body**: `StartSessionRequest`
```json
{
  "student_id": "string | int",
  "activity_id": "string | int",
  "course_id": "string | int | null",
  "mode": "SOCRATIC"
}
```
**Response**: `StartSessionResponse`
```json
{
  "session_id": "string",
  "student_id": "string",
  "activity_id": "string",
  "mode": "string",
  "cognitive_phase": "string",
  "start_time": "datetime",
  "is_active": true
}
```

#### POST `/student/sessions/{session_id}/chat`
**Description**: Send message to Socratic tutor  
**Body**: `SendMessageRequest`
```json
{
  "message": "string",
  "current_code": "string | null",
  "error_context": "dict | null"
}
```
**Response**: `TutorMessageResponse`
```json
{
  "message_id": "string",
  "session_id": "string",
  "sender": "string",
  "content": "string",
  "timestamp": "datetime",
  "cognitive_phase": "string",
  "frustration_level": 0.5,
  "understanding_level": 0.7,
  "response": "string"
}
```

#### GET `/student/sessions/{session_id}/history`
**Description**: Get conversation history  
**Query**: `limit: int = 50`  
**Response**: `SessionHistoryResponse`
```json
{
  "session_id": "string",
  "student_id": "string",
  "activity_id": "string",
  "message_count": 10,
  "messages": [/* TutorMessageResponse[] */],
  "average_frustration": 0.4,
  "requires_intervention": false
}
```

#### POST `/student/sessions/{session_id}/submit`
**Description**: Submit code for review  
**Body**: `SubmitCodeRequest`
```json
{
  "code": "string",
  "language": "python"
}
```
**Response**: `SubmitCodeResponse`
```json
{
  "feedback": "string",
  "execution": {},
  "passed": true
}
```

#### WebSocket `/student/ws/sessions/{session_id}/chat`
**Description**: Real-time chat with tutor  
**Messages**:
- Client → Server: `{"message": "string", "topic": "string | null", "cognitive_phase": "string"}`
- Server → Client: `{"type": "chunk|end|error", "content": "string"}`

#### GET `/student/grades`
**Description**: Get student grades  
**Query**: `course_id?: string`, `passed_only?: bool`  
**Response**: `GradeResponse[]`
```json
[{
  "grade_id": "string",
  "student_id": "string",
  "activity_id": "string",
  "course_id": "string | null",
  "grade": 8.5,
  "max_grade": 10.0,
  "passed": true,
  "teacher_feedback": "string | null",
  "submission_count": 3,
  "last_submission_at": "datetime | null",
  "graded_at": "datetime | null",
  "graded_by": "string | null",
  "activity_title": "string",
  "course_name": "string | null"
}]
```

#### GET `/student/grades/summary`
**Description**: Get grades summary  
**Response**:
```json
{
  "student_id": "string",
  "total_activities": 0,
  "graded_activities": 0,
  "pending_activities": 0,
  "passed_activities": 0,
  "failed_activities": 0,
  "average_grade": 0.0,
  "highest_grade": 0.0,
  "lowest_grade": 0.0
}
```

#### GET `/student/activities/history`
**Description**: Get activity history  
**Query**: `student_id: string`  
**Response**: `ActivityHistoryItem[]`
```json
[{
  "activity_id": "string",
  "activity_title": "string",
  "course_id": "string",
  "course_name": "string",
  "status": "not_started|in_progress|submitted|graded",
  "last_interaction": "string | null",
  "grade": 8.5,
  "passed": true,
  "cognitive_phase": "string | null",
  "completion_percentage": 75.0
}]
```

#### POST `/student/enrollments/join`
**Description**: Join course with access code  
**Body**: `JoinCourseRequest`
```json
{
  "access_code": "string"
}
```
**Response**: `EnrollmentResponse`

#### GET `/student/activities/{activity_id}/workspace`
**Description**: Get workspace for activity  
**Query**: `student_id: string`  
**Response**: `WorkspaceResponse`
```json
{
  "activity_id": "string",
  "activity_title": "string",
  "instructions": "string (markdown)",
  "expected_concepts": ["string"],
  "starter_code": "string",
  "template_code": "string",
  "tutor_context": "string",
  "language": "python",
  "difficulty": "medium",
  "estimated_time_minutes": 45
}
```

#### POST `/student/activities/{activity_id}/tutor`
**Description**: Chat with tutor (LangGraph)  
**Query**: `student_id: string`  
**Body**: `TutorChatRequest`
```json
{
  "student_message": "string",
  "current_code": "string | null",
  "error_message": "string | null"
}
```
**Response**: `TutorChatResponse`
```json
{
  "tutor_response": "string",
  "cognitive_phase": "implementation",
  "frustration_level": 0.3,
  "understanding_level": 0.7,
  "hint_count": 1,
  "rag_context_used": "string"
}
```

---

## Router: Teacher

**Prefix**: `/api/v3/teacher`  
**Tag**: `Teacher`

### Endpoints

#### POST `/teacher/activities`
**Description**: Create new activity  
**Body**: `CreateActivityRequest`
```json
{
  "title": "string",
  "course_id": "string | int",
  "teacher_id": "string | int",
  "instructions": "string | null",
  "description": "string | null",
  "topics": ["string"] | null,
  "difficulty": "string | null",
  "start_date": "string | null",
  "due_date": "string | null",
  "policy": "BALANCED",
  "max_ai_help_level": "MEDIO"
}
```
**Response**: `ActivityResponse`
```json
{
  "activity_id": "string",
  "title": "string",
  "course_id": "string",
  "teacher_id": "string",
  "instructions": "string",
  "policy": "BALANCED",
  "status": "draft",
  "max_ai_help_level": "MEDIO"
}
```

#### GET `/teacher/activities`
**Description**: List activities for dashboard  
**Query**: `teacher_id?: string`, `limit: int = 50`  
**Response**: `ActivityListItem[]`
```json
[{
  "activity_id": "string",
  "title": "string",
  "course_id": "string",
  "teacher_id": "string",
  "instructions": "string | null",
  "status": "draft",
  "created_at": "string | null"
}]
```

#### GET `/teacher/activities/{activity_id}`
**Description**: Get activity detail  
**Response**: `ActivityListItem`

#### PUT `/teacher/activities/{activity_id}`
**Description**: Update activity  
**Query**: `title?: string`, `instructions?: string`, `activity_status?: string`  
**Response**: `{"message": "string", "activity_id": "string"}`

#### DELETE `/teacher/activities/{activity_id}`
**Description**: Delete activity  
**Response**: `204 No Content`

#### POST `/teacher/activities/{activity_id}/exercises`
**Description**: Generate exercise with RAG  
**Body**: `GenerateExerciseRequest`
```json
{
  "topic": "string",
  "difficulty": "FACIL|INTERMEDIO|DIFICIL",
  "unit_number": 1,
  "language": "python",
  "concepts": ["string"] | null,
  "estimated_time_minutes": 30
}
```
**Response**: `ExerciseResponse`
```json
{
  "exercise_id": "string",
  "title": "string",
  "description": "string",
  "difficulty": "FACIL",
  "language": "python",
  "mission_markdown": "string",
  "starter_code": "string",
  "has_solution": true,
  "test_cases": [{
    "test_number": 1,
    "description": "string",
    "input_data": "string",
    "expected_output": "string",
    "is_hidden": false,
    "timeout_seconds": 5
  }],
  "concepts": ["string"],
  "learning_objectives": ["string"],
  "estimated_time_minutes": 30,
  "visible_test_count": 3,
  "hidden_test_count": 2
}
```

#### GET `/teacher/activities/{activity_id}/exercises`
**Description**: Get all exercises for activity  
**Response**: `ExerciseResponse[]`

#### PUT `/teacher/activities/{activity_id}/publish`
**Description**: Publish activity  
**Response**: `ActivityResponse`

#### POST `/teacher/activities/{activity_id}/approve-and-publish`
**Description**: Approve exercises and publish  
**Body**: `ApproveAndPublishRequest`
```json
{
  "exercises": [{
    "exercise_id": "string",
    "title": "string",
    "description": "string",
    "instructions": "string",
    "initial_code": "string",
    "language": "python",
    "difficulty": "easy",
    "estimated_time_minutes": 30,
    "test_cases": [{
      "input": "string",
      "expected_output": "string",
      "is_public": true
    }]
  }]
}
```
**Response**: `ActivityResponse`

#### POST `/teacher/activities/{activity_id}/documents`
**Description**: Upload PDF for RAG processing  
**Body**: Form data with `file: UploadFile`  
**Response**:
```json
{
  "success": true,
  "message": "string",
  "filename": "string",
  "activity_id": "string",
  "rag_processing": "started"
}
```

#### GET `/teacher/activities/{activity_id}/students`
**Description**: Get students enrolled in activity  
**Response**:
```json
[{
  "student_id": "string",
  "email": "string",
  "full_name": "string",
  "total_exercises": 10,
  "submitted_exercises": 7,
  "graded_exercises": 5,
  "avg_score": 8.5,
  "last_submission": "datetime | null",
  "progress_percentage": 70.0
}]
```

#### GET `/teacher/activities/{activity_id}/students/{student_id}/submissions`
**Description**: Get student submissions  
**Response**:
```json
[{
  "exercise_id": "string",
  "exercise_title": "string",
  "difficulty": "FACIL",
  "points": 10,
  "submission_id": "string",
  "code": "string",
  "status": "graded",
  "score": 10,
  "feedback": "string",
  "submitted_at": "datetime",
  "graded_at": "datetime",
  "attempt_number": 1
}]
```

#### GET `/teacher/activities/{activity_id}/submissions`
**Description**: Get all submissions for activity  
**Query**: `student_id?: string`, `exercise_id?: string`, `passed_only?: bool`, `limit: int = 100`  
**Response**: `SubmissionResponse[]` (currently empty - TODO)

#### POST `/teacher/submissions/{submission_id}/grade`
**Description**: Grade submission  
**Body**: `GradeSubmissionRequest`
```json
{
  "grade": 8.5,
  "feedback": "string | null",
  "override_ai": true
}
```
**Response**:
```json
{
  "message": "string",
  "submission_id": "string",
  "grade": 8.5,
  "is_manual_grade": true,
  "graded_by": "string",
  "graded_at": "datetime",
  "audit_created": true
}
```

#### GET `/teacher/activities/{activity_id}/dashboard`
**Description**: Get activity dashboard  
**Response**: `DashboardResponse`
```json
{
  "activity_id": "string",
  "activity_title": "string",
  "students": [{
    "student_id": "string",
    "student_name": "string",
    "status": "submitted",
    "submissions_count": 3,
    "last_submission_date": "string | null",
    "grade": 8.5,
    "passed": true,
    "cognitive_phase": "validation",
    "frustration_level": 0.3,
    "understanding_level": 0.8
  }],
  "total_students": 25,
  "students_started": 20,
  "students_submitted": 15,
  "students_passed": 12,
  "average_grade": 7.8,
  "pass_rate": 0.8
}
```

#### GET `/teacher/students/{student_id}/activities/{activity_id}/traceability`
**Description**: Get N4 cognitive traceability  
**Response**: `CognitiveTraceability`
```json
{
  "student_id": "string",
  "activity_id": "string",
  "cognitive_journey": [{
    "phase": "exploration",
    "start_time": "datetime",
    "end_time": "datetime",
    "duration_minutes": 15,
    "interactions": 5,
    "hints_given": 1
  }],
  "interactions": [{
    "timestamp": "datetime",
    "role": "student|tutor",
    "message": "string",
    "cognitive_phase": "string",
    "was_hint": false
  }],
  "code_evolution": [{
    "timestamp": "datetime",
    "phase": "implementation",
    "code": "string",
    "lines_count": 20
  }],
  "frustration_curve": [0.5, 0.6, 0.4],
  "understanding_curve": [0.3, 0.4, 0.6],
  "total_hints": 5,
  "total_time_minutes": 85,
  "final_phase": "reflection",
  "completed": true
}
```

#### POST `/teacher/generator/upload`
**Description**: Upload PDF for exercise generation (LangGraph)  
**Query**: `teacher_id: string`, `course_id: string`, `topic: string`, `difficulty: string = "mixed"`, `language: string = "python"`, `concepts: string = ""`  
**Body**: Form data with `file: UploadFile`  
**Response**: `GeneratorJobResponse`
```json
{
  "job_id": "string",
  "status": "processing",
  "awaiting_approval": false,
  "error": null
}
```

#### GET `/teacher/generator/{job_id}/status`
**Description**: Check generation job status  
**Response**: `GeneratorJobResponse`
```json
{
  "job_id": "string",
  "status": "ingestion|generation|awaiting_approval|completed|failed",
  "awaiting_approval": false,
  "error": "string | null"
}
```

#### GET `/teacher/generator/{job_id}/draft`
**Description**: Get draft exercises  
**Response**: `DraftResponse`
```json
{
  "job_id": "string",
  "status": "awaiting_approval",
  "draft_exercises": [{
    "title": "string",
    "description": "string",
    "difficulty": "easy",
    "concepts": ["string"],
    "mission_markdown": "string",
    "starter_code": "string",
    "solution_code": "string",
    "test_cases": [{}]
  }],
  "awaiting_approval": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### PUT `/teacher/generator/{job_id}/approve`
**Description**: Approve draft exercises  
**Body**: `ApproveExercisesRequest`
```json
{
  "approved_indices": [0, 2, 5] | null
}
```
**Response**: `GeneratorJobResponse`

#### POST `/teacher/analytics/audit/{student_id}`
**Description**: Generate AI pedagogical audit  
**Body**: `AnalyticsAuditRequest`
```json
{
  "teacher_id": "string",
  "activity_id": "string | null",
  "include_traceability": true
}
```
**Response**: `AnalyticsAuditResponse`
```json
{
  "analysis_id": "string",
  "student_id": "string",
  "risk_score": 0.75,
  "risk_level": "HIGH",
  "diagnosis": "string",
  "evidence": ["string"],
  "intervention": "string",
  "confidence_score": 0.85,
  "status": "completed",
  "error_message": null,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Router: Admin

**Prefix**: `/api/v3/admin`  
**Tag**: `Admin`

### Endpoints

#### POST `/admin/subjects`
**Description**: Create subject  
**Body**: `CreateSubjectRequest`
```json
{
  "code": "PROG-101",
  "name": "string",
  "credits": 4,
  "description": "string | null"
}
```
**Response**: `SubjectResponse`
```json
{
  "subject_id": "string",
  "code": "PROG-101",
  "name": "string",
  "credits": 4,
  "created_at": "datetime"
}
```

#### POST `/admin/courses`
**Description**: Create course  
**Body**: `CreateCourseRequest`
```json
{
  "subject_id": "string",
  "year": 2025,
  "semester": 1
}
```
**Response**: `CourseResponse`

#### POST `/admin/commissions`
**Description**: Create commission  
**Body**: `CreateCommissionRequest`
```json
{
  "course_id": "string",
  "teacher_id": "string",
  "name": "Comisión A",
  "schedule": {} | null,
  "capacity": 30 | null
}
```
**Response**: `CommissionResponse`

#### POST `/admin/users/{user_id}/role`
**Description**: Update user role  
**Body**: `UpdateUserRoleRequest`
```json
{
  "role": "student|teacher|admin"
}
```
**Response**:
```json
{
  "message": "string",
  "user_id": "string",
  "new_role": "teacher"
}
```

#### GET `/admin/subjects`
**Query**: `include_deleted: bool = false`  
**Response**: `SubjectResponse[]`

#### DELETE `/admin/subjects/{subject_id}`
**Query**: `soft_delete: bool = true`  
**Response**: `204 No Content`

#### GET `/admin/courses`
**Query**: `year?: int`, `semester?: int`  
**Response**: `CourseResponse[]`

---

## Router: Analytics

**Prefix**: `/api/v3/analytics`  
**Tag**: `Analytics V3`

### Endpoints

#### GET `/analytics/courses/{course_id}`
**Description**: Get course analytics  
**Response**: `CourseAnalyticsResponse`
```json
{
  "course_id": "string",
  "course_name": "string",
  "total_students": 50,
  "average_risk_score": 0.35,
  "students_at_risk_count": 5,
  "completion_rate": 0.85,
  "student_profiles": [{
    "student_id": "string",
    "student_name": "string",
    "risk_score": 0.65,
    "risk_level": "MEDIUM",
    "completion_rate": 0.75,
    "avg_session_duration_minutes": 45.0,
    "total_sessions": 10,
    "last_activity_at": "datetime | null"
  }]
}
```

#### GET `/analytics/students/{student_id}`
**Description**: Get student risk profile  
**Query**: `course_id?: string`  
**Response**: `StudentRiskProfileResponse`
```json
{
  "student_id": "string",
  "student_name": "string",
  "risk_score": 0.45,
  "risk_level": "MEDIUM",
  "completion_rate": 0.70,
  "avg_session_duration_minutes": 38.5,
  "total_sessions": 12,
  "total_hints_requested": 15,
  "avg_frustration_level": 0.4,
  "last_activity_at": "datetime"
}
```

---

## Router: Governance

**Prefix**: `/api/v3/governance`  
**Tag**: `Governance / GSR`

### Endpoints

#### GET `/governance/sessions/{session_id}`
**Description**: Get session governance status  
**Response**: `GovernanceResponse`
```json
{
  "has_risk": true,
  "student_id": "string | null",
  "session_id": "string | null",
  "risk_score": 0.75,
  "risk_level": "HIGH",
  "ai_dependency_score": 0.8,
  "ai_dependency_level": "HIGH",
  "risk_factors": {},
  "created_at": "datetime | null",
  "ai_analysis": {}
}
```

#### GET `/governance/students/{student_id}`
**Description**: Get student governance status  
**Response**: `GovernanceResponse`

#### GET `/governance/config`
**Description**: Get governance configuration  
**Response**: `GovernanceConfigResponse`
```json
{
  "ai_dependency_threshold": 0.8,
  "risk_score_critical_threshold": 0.75,
  "risk_score_warning_threshold": 0.5,
  "max_consecutive_ai_hints": 5,
  "frustration_intervention_threshold": 0.7,
  "auto_notify_teacher": true,
  "auto_notify_student": false
}
```

#### PUT `/governance/config`
**Description**: Update governance config  
**Body**: `UpdateGovernanceConfigRequest`  
**Response**: `GovernanceConfigResponse`

#### POST `/governance/incidents/report`
**Description**: Report governance incident  
**Body**: `ReportIncidentRequest`
```json
{
  "incident_type": "hallucination|toxic_response|inappropriate_hint|other",
  "session_id": "string | null",
  "message_id": "string | null",
  "description": "string",
  "severity": "low|medium|high|critical",
  "reported_by_role": "student|teacher|system",
  "ai_response": "string | null",
  "context": {} | null
}
```
**Response**: `IncidentResponse`

#### GET `/governance/incidents`
**Query**: `status?: string`, `severity?: string`, `incident_type?: string`, `limit: int = 50`  
**Response**: `IncidentResponse[]`

---

## Router: Catalog

**Prefix**: `/api/v3/catalog`  
**Tag**: `Catalog`

### Endpoints

#### GET `/catalog/subjects`
**Query**: `active_only: bool = true`  
**Response**: `SubjectResponse[]`
```json
[{
  "id": 1,
  "code": "PROG-101",
  "name": "string",
  "description": "string | null",
  "credits": 4,
  "semester": 1,
  "is_active": true
}]
```

#### GET `/catalog/subjects/{subject_id}/courses`
**Query**: `active_only: bool = true`  
**Response**: `CourseResponse[]`
```json
[{
  "id": 1,
  "subject_id": 1,
  "year": 2025,
  "semester": 1,
  "start_date": "date | null",
  "end_date": "date | null",
  "is_active": true
}]
```

#### GET `/catalog/courses/{course_id}/commissions`
**Response**: `CommissionResponse[]`
```json
[{
  "id": 1,
  "course_id": 1,
  "code": "K1021",
  "schedule": "string | null",
  "capacity": 30,
  "teacher_id": "string | null"
}]
```

---

## Router: Enrollments

**Prefix**: `/api/v3/enrollments`  
**Tag**: `Enrollments`

### Endpoints

#### POST `/enrollments/join`
**Description**: Student joins course with code  
**Body**: `JoinCourseRequest`
```json
{
  "course_code": "string",
  "commission_id": "string | null"
}
```
**Response**: `EnrollmentResponse`
```json
{
  "enrollment_id": "string",
  "student_id": "string",
  "course_id": "string",
  "commission_id": "string | null",
  "enrolled_at": "datetime",
  "status": "active"
}
```

#### GET `/enrollments/my-courses`
**Description**: Get student's courses  
**Response**: `EnrollmentResponse[]`

#### DELETE `/enrollments/{course_id}`
**Description**: Drop course  
**Response**: `204 No Content`

#### POST `/enrollments/teacher/courses/{course_id}/students`
**Description**: Teacher adds student  
**Body**: `AddStudentRequest`
```json
{
  "student_id": "string",
  "commission_id": "string | null"
}
```
**Response**: `EnrollmentResponse`

#### GET `/enrollments/teacher/courses/{course_id}/students`
**Query**: `commission_id?: string`, `status_filter?: string`  
**Response**: `StudentInCourseResponse[]`
```json
[{
  "student_id": "string",
  "user_id": "string",
  "full_name": "string",
  "email": "string",
  "enrolled_at": "datetime",
  "commission_name": "string | null",
  "status": "active"
}]
```

#### POST `/enrollments/teacher/courses/{course_id}/access-code`
**Query**: `commission_id?: string`, `expires_in_days: int = 30`  
**Response**:
```json
{
  "course_id": "string",
  "commission_id": "string | null",
  "access_code": "ABC12345",
  "expires_at": "datetime",
  "message": "string"
}
```

---

## Router: Notifications

**Prefix**: `/api/v3/notifications`  
**Tag**: `Notifications`

### Endpoints

#### GET `/notifications`
**Query**: `unread_only: bool = true`, `type_filter?: string`, `severity_filter?: string`, `limit: int = 50`  
**Response**: `NotificationResponse[]`
```json
[{
  "notification_id": "string",
  "user_id": "string",
  "type": "risk_alert|grade_posted|enrollment_confirmed|system_announcement",
  "title": "string",
  "message": "string",
  "severity": "info|warning|critical",
  "data": {} | null,
  "read": false,
  "created_at": "datetime",
  "read_at": "datetime | null"
}]
```

#### GET `/notifications/unread-count`
**Response**:
```json
{
  "unread_count": 5,
  "critical_count": 1
}
```

#### POST `/notifications/mark-read`
**Body**: `MarkReadRequest`
```json
{
  "notification_ids": ["string"]
}
```
**Response**:
```json
{
  "marked_count": 3,
  "message": "string"
}
```

#### POST `/notifications/webhooks`
**Body**: `WebhookConfigRequest`
```json
{
  "url": "https://hooks.slack.com/...",
  "events": ["risk_alert", "grade_posted"],
  "active": true,
  "secret": "string | null"
}
```
**Response**: `WebhookConfigResponse`

---

## Database Models

### users
```sql
id: VARCHAR(36) PRIMARY KEY
email: VARCHAR(255) UNIQUE NOT NULL
username: VARCHAR(100) UNIQUE NOT NULL
hashed_password: VARCHAR(255) NOT NULL
full_name: VARCHAR(255) NULL
roles: JSONB NOT NULL DEFAULT '[]'
is_active: BOOLEAN NOT NULL DEFAULT TRUE
is_verified: BOOLEAN NOT NULL DEFAULT FALSE
last_login: TIMESTAMP WITH TIME ZONE NULL
login_count: INTEGER NOT NULL DEFAULT 0
created_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
deleted_at: TIMESTAMP WITH TIME ZONE NULL
```

### activities
```sql
activity_id: VARCHAR(36) PRIMARY KEY
title: VARCHAR(255) NOT NULL
description: TEXT NULL
instructions: TEXT NOT NULL
evaluation_criteria: JSONB DEFAULT '[]'
course_id: VARCHAR(36) FK -> courses.course_id
teacher_id: VARCHAR(36) FK -> users.id
policies: JSONB NOT NULL DEFAULT '{}'
difficulty: ENUM (INICIAL, INTERMEDIO, AVANZADO) NULL
estimated_duration_minutes: INTEGER NULL
learning_objectives: JSONB DEFAULT '[]'
tags: JSONB DEFAULT '[]'
status: ENUM (draft, active, archived) NOT NULL DEFAULT 'draft'
published_at: TIMESTAMP WITH TIME ZONE NULL
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
deleted_at: TIMESTAMP WITH TIME ZONE NULL
```

### exercises
```sql
exercise_id: VARCHAR(36) PRIMARY KEY
activity_id: VARCHAR(36) NOT NULL
title: VARCHAR(255) NOT NULL
description: TEXT NULL
difficulty: VARCHAR(50) NULL
exercise_type: VARCHAR(50) NOT NULL
language: VARCHAR(50) NOT NULL DEFAULT 'python'
test_cases: JSONB NULL
solution: TEXT NULL
template_code: TEXT NULL
order_index: INTEGER DEFAULT 0
is_active: BOOLEAN DEFAULT TRUE
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
```

### submissions
```sql
submission_id: VARCHAR(36) PRIMARY KEY
student_id: VARCHAR(36) FK -> users.id
activity_id: VARCHAR(36) FK -> activities.activity_id
code_snapshot: TEXT NOT NULL
status: ENUM (pending, submitted, graded, reviewed) NOT NULL DEFAULT 'pending'
auto_grade: FLOAT NULL
final_grade: FLOAT NULL
is_manual_grade: BOOLEAN NOT NULL DEFAULT FALSE
ai_feedback: TEXT NULL
teacher_feedback: TEXT NULL
test_results: JSONB NULL
execution_error: TEXT NULL
graded_by: VARCHAR(36) FK -> users.id
graded_at: TIMESTAMP WITH TIME ZONE NULL
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
submitted_at: TIMESTAMP WITH TIME ZONE NULL
```

### sessions
```sql
id: VARCHAR(36) PRIMARY KEY
student_id: VARCHAR(100) NOT NULL
activity_id: VARCHAR(100) NOT NULL
course_id: VARCHAR(100) NULL
user_id: VARCHAR(36) FK -> users.id
mode: VARCHAR(50) NOT NULL DEFAULT 'tutor'
simulator_type: VARCHAR(50) NULL
start_time: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
end_time: TIMESTAMP WITH TIME ZONE NULL
state: JSONB NOT NULL DEFAULT '{}'
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
```

### subjects
```sql
id: VARCHAR(36) PRIMARY KEY
code: VARCHAR(50) UNIQUE NOT NULL
name: VARCHAR(255) NOT NULL
description: TEXT NULL
credits: INTEGER NULL
semester: INTEGER NULL
is_active: BOOLEAN NOT NULL DEFAULT TRUE
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
```

### courses
```sql
course_id: VARCHAR(36) PRIMARY KEY
subject_id: VARCHAR(36) FK -> subjects.id
year: INTEGER NOT NULL
semester: INTEGER NOT NULL
start_date: DATE NULL
end_date: DATE NULL
is_active: BOOLEAN NOT NULL DEFAULT TRUE
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
```

### commissions
```sql
commission_id: VARCHAR(36) PRIMARY KEY
course_id: VARCHAR(36) FK -> courses.course_id
code: VARCHAR(100) UNIQUE NOT NULL
schedule: JSONB DEFAULT '{}'
capacity: INTEGER NULL
teacher_id: VARCHAR(36) FK -> users.id
created_at: TIMESTAMP WITH TIME ZONE NOT NULL
updated_at: TIMESTAMP WITH TIME ZONE NOT NULL
```

### grade_audits
```sql
audit_id: VARCHAR(36) PRIMARY KEY
submission_id: VARCHAR(36) FK -> submissions.submission_id
instructor_id: VARCHAR(36) FK -> users.id
previous_grade: FLOAT NULL
new_grade: FLOAT NOT NULL
was_auto_grade: BOOLEAN NOT NULL
override_reason: TEXT NULL
timestamp: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
```

---

## Enums & Constants

### Difficulty Levels
```python
# Activities
INICIAL = "INICIAL"
INTERMEDIO = "INTERMEDIO"
AVANZADO = "AVANZADO"

# Exercises (alternative format)
FACIL = "FACIL" | "facil"
INTERMEDIO = "INTERMEDIO" | "intermedio"
DIFICIL = "DIFICIL" | "dificil"

# Frontend mapping
easy = "FACIL"
medium = "INTERMEDIO"
hard = "DIFICIL"
```

### Cognitive Phases (N4 System)
```python
EXPLORATION = "exploration"
DECOMPOSITION = "decomposition"
PLANNING = "planning"
IMPLEMENTATION = "implementation"
DEBUGGING = "debugging"
VALIDATION = "validation"
REFLECTION = "reflection"
```

### Tutor Modes
```python
SOCRATIC = "SOCRATIC"
DIRECT = "DIRECT"
GUIDED = "GUIDED"
```

### Pedagogical Policies
```python
STRICT = "STRICT"
BALANCED = "BALANCED"
PERMISSIVE = "PERMISSIVE"
```

### AI Help Levels
```python
BAJO = "BAJO"
MEDIO = "MEDIO"
ALTO = "ALTO"
```

### Risk Levels
```python
LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"
CRITICAL = "CRITICAL"
```

### Activity Status
```python
draft = "draft"
active = "active"
archived = "archived"
```

### Submission Status
```python
pending = "pending"
submitted = "submitted"
graded = "graded"
reviewed = "reviewed"
```

### Enrollment Status
```python
active = "active"
dropped = "dropped"
completed = "completed"
```

### Exercise Types
```python
CODE_COMPLETION = "code_completion"
CODE_CORRECTION = "code_correction"
CODE_FROM_SCRATCH = "code_from_scratch"
MULTIPLE_CHOICE = "multiple_choice"
CONCEPTUAL = "conceptual"
```

### Programming Languages
```python
python = "python"
javascript = "javascript"
java = "java"
cpp = "cpp"
c = "c"
```

### Notification Types
```python
risk_alert = "risk_alert"
grade_posted = "grade_posted"
enrollment_confirmed = "enrollment_confirmed"
system_announcement = "system_announcement"
```

### Notification Severities
```python
info = "info"
warning = "warning"
critical = "critical"
```

### Incident Types
```python
hallucination = "hallucination"
toxic_response = "toxic_response"
inappropriate_hint = "inappropriate_hint"
other = "other"
```

---

## Relationships & Foreign Keys

### User Relationships
- `users.id` → `activities.teacher_id` (One-to-Many: User can create many activities)
- `users.id` → `submissions.student_id` (One-to-Many: User can have many submissions)
- `users.id` → `submissions.graded_by` (One-to-Many: User can grade many submissions)
- `users.id` → `sessions.user_id` (One-to-Many: User can have many sessions)
- `users.id` → `commissions.teacher_id` (One-to-Many: User can teach many commissions)

### Activity Relationships
- `activities.activity_id` → `exercises.activity_id` (One-to-Many: Activity has many exercises)
- `activities.activity_id` → `submissions.activity_id` (One-to-Many: Activity has many submissions)
- `activities.course_id` → `courses.course_id` (Many-to-One: Activities belong to courses)

### Course Relationships
- `subjects.id` → `courses.subject_id` (One-to-Many: Subject has many course instances)
- `courses.course_id` → `commissions.course_id` (One-to-Many: Course has many commissions)
- `courses.course_id` → `activities.course_id` (One-to-Many: Course has many activities)

### Submission Relationships
- `submissions.submission_id` → `grade_audits.submission_id` (One-to-Many: Submission has audit trail)

---

## API Response Patterns

### Success Response
```json
{
  "data": {...},
  "message": "string",
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "string",
  "status_code": 400
}
```

### Pagination (when applicable)
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 50,
  "has_next": true
}
```

---

## Notes for Frontend Development

1. **All IDs are strings** (VARCHAR(36) UUIDs in database)
2. **Dates are ISO 8601 strings** with timezone: `"2026-01-26T10:30:00Z"`
3. **Base URL prefix**: Always use `/api/v3` for all endpoints
4. **Authentication**: Include `Authorization: Bearer <token>` header on all protected routes
5. **File uploads**: Use `multipart/form-data` with `UploadFile` field
6. **WebSockets**: Use `ws://localhost:8000/api/v3/student/ws/sessions/{session_id}/chat`
7. **JSONB fields**: Store/send as regular JSON objects, DB handles serialization
8. **NULL vs undefined**: Backend accepts both `null` and omitted fields for optional parameters
9. **Enums**: Send as uppercase strings (`"FACIL"`, `"INTERMEDIO"`, `"DIFICIL"`)
10. **Error handling**: All errors return HTTP status codes + `{"detail": "message"}` body

---

## Environment Variables

```bash
# Required
JWT_SECRET_KEY=<secret-key-min-32-chars>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Optional (with defaults)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
UPLOADS_DIR=./uploads
MISTRAL_API_KEY=<mistral-api-key>
MISTRAL_MODEL=mistral-small-latest
```

---

**End of API Reference**

*Generated: 2026-01-26*  
*Backend Version: src_v3*  
*Base URL: http://localhost:8000/api/v3*
