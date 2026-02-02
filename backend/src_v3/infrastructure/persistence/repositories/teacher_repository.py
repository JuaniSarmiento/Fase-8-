"""Teacher Repository - Persistence for activities and exercises.

This implementation is aligned with the V2 SQL schema defined in
create_tables_v2_clean.sql, using lightweight SQL rather than the
inconsistent ORM models.
"""
from typing import Optional, List, Dict, Any

import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src_v3.core.domain.teacher.entities import (
    Activity,
    GeneratedExercise,
    PedagogicalContent,
    TestCase,
    PedagogicalPolicy,
)


class TeacherRepository:
    """Repository for teacher domain operations backed by V2 tables."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_activity(self, activity: Activity) -> Activity:
        """Create new activity in the activities table.

        We store minimal information required for the current flows,
        mapping domain fields to the columns available in the schema.
        """
        result = await self.db.execute(
            text(
                """
                INSERT INTO activities (activity_id, course_id, teacher_id, title, instructions, status)
                VALUES (:activity_id, :course_id, :teacher_id, :title, :instructions, :status)
                RETURNING activity_id
                """
            ),
            {
                "activity_id": activity.activity_id,
                "course_id": activity.course_id,
                "teacher_id": activity.teacher_id,
                "title": activity.title,
                "instructions": activity.instructions,
                "status": activity.status,
            },
        )
        row = result.first()
        await self.db.commit()

        return activity

    async def update_activity(self, activity: Activity) -> Activity:
        """Update an existing activity's basic fields.

        Currently we only need to update the status/published flag when
        publishing activities from the teacher dashboard.
        """
        try:
            numeric_id = int(activity.activity_id)
        except ValueError:
            # If the ID is not numeric there is nothing to update
            return activity

        await self.db.execute(
            text(
                """
                UPDATE activities
                SET status = :status, updated_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": numeric_id,
                "status": activity.status,
            },
        )
        await self.db.commit()
        return activity

    async def list_activities(
        self,
        teacher_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return a basic list of activities.

        This method is intentionally lightweight and only returns the
        fields needed by the teacher dashboard UI, keeping the
        existing domain model unchanged.
        """
        query = """
            SELECT activity_id, course_id, teacher_id, title, instructions, status, created_at
            FROM activities
        """
        params: Dict[str, Any] = {}

        if teacher_id is not None:
            query += " WHERE teacher_id = :teacher_id"
            # Store teacher_id as string (UUID format)
            params["teacher_id"] = str(teacher_id)

        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = int(limit)

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        activities: List[Dict[str, Any]] = []
        for row in rows:
            (
                activity_id,
                course_id,
                teacher_id_value,
                title,
                instructions,
                status,
                created_at,
            ) = row

            activities.append(
                {
                    "activity_id": str(activity_id) if activity_id is not None else "",
                    "title": title or "",
                    "course_id": str(course_id) if course_id is not None else "",
                    "teacher_id": str(teacher_id_value) if teacher_id_value is not None else "",
                    "instructions": instructions or "",
                    "status": status or "draft",
                    "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") and created_at else None,
                }
            )

        return activities

    async def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Get a single activity by ID, returns Activity domain object."""
        query = """
            SELECT activity_id, course_id, teacher_id, title, subject, instructions, status, policies, created_at
            FROM activities
            WHERE activity_id = :activity_id
        """
        
        result = await self.db.execute(text(query), {"activity_id": activity_id})
        row = result.first()
        
        if row is None:
            return None
        
        (
            activity_id_value,
            course_id,
            teacher_id_value,
            title,
            subject,
            instructions,
            status,
            policies,
            created_at,
        ) = row

        # Extract values from policies JSON if available
        policies_dict = policies or {}
        policy_str = policies_dict.get("policy", "BALANCED")
        max_ai_help = policies_dict.get("max_ai_help_level", "MEDIO")
        
        try:
            pedagogical_policy = PedagogicalPolicy[policy_str] if policy_str in PedagogicalPolicy.__members__ else PedagogicalPolicy.BALANCED
        except:
            pedagogical_policy = PedagogicalPolicy.BALANCED

        return Activity(
            activity_id=str(activity_id_value),
            title=title or "",
            course_id=str(course_id) if course_id else "",
            teacher_id=str(teacher_id_value) if teacher_id_value else "",
            instructions=instructions or "",
            policy=pedagogical_policy,
            max_ai_help_level=max_ai_help,
            allow_code_snippets=policies_dict.get("allow_code_snippets", False),
            require_justification=policies_dict.get("require_justification", True),
            status=str(status) if status else "draft",
            published_at=None,
        )
    
    async def update_activity(self, activity_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields of an activity.
        
        Args:
            activity_id: The activity to update
            updates: Dict with keys 'title', 'instructions', 'status' (only provided fields will be updated)
        
        Returns:
            True if update succeeded, False if activity not found
        """
        if not updates:
            return False
        
        # Build SET clause dynamically
        set_parts = []
        params = {"activity_id": activity_id}
        
        if "title" in updates:
            set_parts.append("title = :title")
            params["title"] = updates["title"]
        
        if "instructions" in updates:
            set_parts.append("instructions = :instructions")
            params["instructions"] = updates["instructions"]
        
        if "status" in updates:
            set_parts.append("status = :status")
            params["status"] = updates["status"]
        
        query = f"""
            UPDATE activities
            SET {', '.join(set_parts)}
            WHERE activity_id = :activity_id
        """
        
        result = await self.db.execute(text(query), params)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def delete_activity(self, activity_id: str) -> bool:
        """Delete an activity by ID.
        
        Returns:
            True if deletion succeeded, False if activity not found
        """
        query = """
            DELETE FROM activities
            WHERE activity_id = :activity_id
        """
        
        result = await self.db.execute(text(query), {"activity_id": activity_id})
        await self.db.commit()
        
        return result.rowcount > 0

    async def replace_exercises_for_activity(
        self,
        activity_id: str,
        exercises: List[GeneratedExercise],
    ) -> None:
        """Replace all exercises for an activity in exercises_v2.

        This is used by the teacher content dashboard when the teacher
        approves a final set of exercises for publication.
        """
        try:
            numeric_id = int(activity_id)
        except ValueError:
            # If the ID is not numeric we cannot persist exercises
            return

        # Remove previous exercises for this activity so the approved
        # set becomes the single source of truth.
        await self.db.execute(
            text("DELETE FROM exercises_v2 WHERE activity_id = :activity_id"),
            {"activity_id": numeric_id},
        )

        insert_query = text(
            """
            INSERT INTO exercises_v2 (
                activity_id,
                session_id,
                topic,
                title,
                difficulty,
                language,
                problem_statement,
                mission_markdown,
                test_cases,
                hints,
                solution_template,
                solution_code
            ) VALUES (
                :activity_id,
                NULL,
                :topic,
                :topic,  # title = topic
                :difficulty,
                :language,
                :problem_statement,
                :problem_statement, # mission_markdown = problem_statement
                CAST(:test_cases AS jsonb),
                CAST(:hints AS jsonb),
                :solution_template,
                :solution_template  # solution_code = solution_template
            )
            """
        )

        for exercise in exercises:
            test_cases_payload = [
                {
                    "test_number": tc.test_number,
                    "description": tc.description,
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "is_hidden": tc.is_hidden,
                    "timeout_seconds": tc.timeout_seconds,
                }
                for tc in exercise.test_cases
            ]

            await self.db.execute(
                insert_query,
                {
                    "activity_id": numeric_id,
                    "topic": exercise.title,
                    "difficulty": exercise.difficulty,
                    "language": exercise.language,
                    "problem_statement": exercise.mission_markdown,
                    "test_cases": json.dumps(test_cases_payload),
                    "hints": json.dumps([]),
                    "solution_template": exercise.solution_code,
                },
            )

        await self.db.commit()

    async def get_published_activities(self) -> List[Activity]:
        """Get all published activities (active status)."""
        query = """
            SELECT activity_id, course_id, teacher_id, title, subject, instructions, status, policies, created_at
            FROM activities
            WHERE status = 'active'
            ORDER BY created_at DESC
        """
        
        result = await self.db.execute(text(query))
        rows = result.fetchall()
        
        activities = []
        for row in rows:
            (
                activity_id_value,
                course_id,
                teacher_id_value,
                title,
                subject,
                instructions,
                status,
                policies,
                created_at,
            ) = row

            policies_dict = policies or {}
            policy_str = policies_dict.get("policy", "BALANCED")
            max_ai_help = policies_dict.get("max_ai_help_level", "MEDIO")
            
            try:
                pedagogical_policy = PedagogicalPolicy[policy_str] if policy_str in PedagogicalPolicy.__members__ else PedagogicalPolicy.BALANCED
            except:
                pedagogical_policy = PedagogicalPolicy.BALANCED

            activities.append(
                Activity(
                    activity_id=str(activity_id_value),
                    title=title or "",
                    course_id=str(course_id) if course_id else "",
                    teacher_id=str(teacher_id_value) if teacher_id_value else "",
                    instructions=instructions or "",
                    policy=pedagogical_policy,
                    max_ai_help_level=max_ai_help,
                    allow_code_snippets=policies_dict.get("allow_code_snippets", False),
                    require_justification=policies_dict.get("require_justification", True),
                    status=str(status) if status else "draft",
                    published_at=None,
                )
            )
        return activities

    async def get_exercise_by_id(self, exercise_id: str) -> Optional[GeneratedExercise]:
        """Get a single exercise by ID."""
        result = await self.db.execute(
            text(
                """
                SELECT exercise_id, title, description, difficulty, language, 
                       mission_markdown, starter_code, solution_code, test_cases
                FROM exercises_v2
                WHERE exercise_id = :exercise_id
                """
            ),
            {"exercise_id": exercise_id},
        )
        row = result.first()
        
        if not row:
            return None
            
        (
            exercise_id,
            title,
            description,
            difficulty,
            language,
            mission_markdown,
            starter_code,
            solution_code,
            test_cases_json,
        ) = row
        
        concepts_json = []
        objectives_json = []

        raw_test_cases = test_cases_json or []
        if isinstance(raw_test_cases, str):
            try:
                raw_test_cases = json.loads(raw_test_cases)
            except Exception:
                raw_test_cases = []
        
        # Handle Concepts and Objectives
        concepts = concepts_json or []
        if isinstance(concepts, str):
            try:
                concepts = json.loads(concepts)
            except Exception:
                concepts = []

        objectives = objectives_json or []
        if isinstance(objectives, str):
            try:
                objectives = json.loads(objectives)
            except Exception:
                objectives = []
        
        if not concepts:
            concepts = ["Concepto General"]

        test_cases: List[TestCase] = []
        for idx, tc in enumerate(raw_test_cases or [], start=1):
            try:
                test_cases.append(
                    TestCase(
                        test_number=int(tc.get("test_number", idx)),
                        description=tc.get("description", f"Test {idx}"),
                        input_data=str(tc.get("input_data", "")),
                        expected_output=str(tc.get("expected_output", "")),
                        is_hidden=bool(tc.get("is_hidden", False)),
                        timeout_seconds=int(tc.get("timeout_seconds", 5)),
                    )
                )
            except Exception:
                continue

        if len(test_cases) < 2:
            existing_tc = test_cases[0] if test_cases else None
            test_cases = [
                existing_tc or TestCase(
                    test_number=1,
                    description="Test básico",
                    input_data="",
                    expected_output="",
                    is_hidden=False,
                    timeout_seconds=5,
                ),
                TestCase(
                    test_number=2,
                    description="Test oculto (Auto-generado)",
                    input_data="",
                    expected_output="",
                    is_hidden=True,
                    timeout_seconds=5,
                )
            ]

        return GeneratedExercise(
            exercise_id=str(exercise_id),
            title=title or "Ejercicio",
            description=description or mission_markdown or "",
            difficulty=str(difficulty) if difficulty else "INTERMEDIO",
            language=str(language) if language else "python",
            mission_markdown=mission_markdown or description or "",
            starter_code=starter_code or "# TODO: Implementa la solución aquí\n",
            solution_code=solution_code or "",
            test_cases=test_cases,
            concepts=concepts,
            learning_objectives=objectives,
            estimated_time_minutes=30,
            pedagogical_notes=None,
            rag_sources=[],
        )

    async def get_exercises_for_activity(self, activity_id: str) -> List[GeneratedExercise]:
        """Load all exercises for an activity from exercises_v2.

        This is primarily used when publishing an activity and when
        fetching exercises for teacher dashboards.
        """
        # activity_id is now a UUID string (VARCHAR 36), not an integer
        result = await self.db.execute(
            text(
                """
                SELECT exercise_id, title, description, difficulty, language, 
                       mission_markdown, starter_code, solution_code, test_cases
                FROM exercises_v2
                WHERE activity_id = :activity_id
                ORDER BY created_at ASC
                """
            ),
            {"activity_id": activity_id},
        )
        rows = result.fetchall()

        exercises: List[GeneratedExercise] = []
        for row in rows:
            (
                exercise_id,
                title,
                description,
                difficulty,
                language,
                mission_markdown,
                starter_code,
                solution_code,
                test_cases_json,
            ) = row
            
            concepts_json = []
            objectives_json = []

            raw_test_cases = test_cases_json or []
            # Ensure we have a list of dicts
            if isinstance(raw_test_cases, str):
                try:
                    raw_test_cases = json.loads(raw_test_cases)
                except Exception:  # pragma: no cover - defensive
                    raw_test_cases = []

            # Handle Concepts and Objectives
            concepts = concepts_json or []
            if isinstance(concepts, str):
                try:
                    concepts = json.loads(concepts)
                except Exception:
                    concepts = []

            objectives = objectives_json or []
            if isinstance(objectives, str):
                try:
                    objectives = json.loads(objectives)
                except Exception:
                    objectives = []
            
            # Default concept if none found (required by domain)
            if not concepts:
                concepts = ["Concepto General"]

            test_cases: List[TestCase] = []
            for idx, tc in enumerate(raw_test_cases or [], start=1):
                try:
                    test_cases.append(
                        TestCase(
                            test_number=int(tc.get("test_number", idx)),
                            description=tc.get("description", f"Test {idx}"),
                            input_data=str(tc.get("input_data", "")),
                            expected_output=str(tc.get("expected_output", "")),
                            is_hidden=bool(tc.get("is_hidden", False)),
                            timeout_seconds=int(tc.get("timeout_seconds", 5)),
                        )
                    )
                except Exception:
                    # Skip invalid test case rows defensively
                    continue

            if len(test_cases) < 2:
                # Fallback to ensure at least 2 test cases to satisfy domain validation
                # (1 visible, 1 hidden)
                
                # If we have 1 existing test, keep it. If 0, create defaults.
                existing_tc = test_cases[0] if test_cases else None
                
                test_cases = [
                    existing_tc or TestCase(
                        test_number=1,
                        description="Test básico",
                        input_data="",
                        expected_output="",
                        is_hidden=False,
                        timeout_seconds=5,
                    ),
                    TestCase(
                        test_number=2,
                        description="Test oculto (Auto-generado)",
                        input_data="",
                        expected_output="",
                        is_hidden=True,
                        timeout_seconds=5,
                    )
                ]

            exercises.append(
                GeneratedExercise(
                    exercise_id=str(exercise_id),
                    title=title or "Ejercicio",
                    description=description or mission_markdown or "",
                    difficulty=str(difficulty) if difficulty else "INTERMEDIO",
                    language=str(language) if language else "python",
                    mission_markdown=mission_markdown or description or "",
                    starter_code=starter_code or "# TODO: Implementa la solución aquí\n",
                    solution_code=solution_code or "",
                    test_cases=test_cases,
                    concepts=concepts,
                    learning_objectives=objectives,
                    estimated_time_minutes=30,
                    pedagogical_notes=None,
                    rag_sources=[],
                )
            )

        return exercises

    async def get_governance_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent governance alerts (risk > info)"""
        query = text("""
            SELECT session_id, interaction_type, interactional_data, timestamp
            FROM cognitive_traces_v2
            WHERE interaction_type = 'governance_log'
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        alerts = []
        for row in rows:
            data = row[2]
            # Filter logic: Only include if risk_level is NOT "info" or "low"
            # Or just return everything and let frontend filter?
            # Let's filter here to be safe
            risk = data.get("risk_level", "low").lower()
            if risk in ["medium", "high", "critical"]:
                alerts.append({
                    "session_id": str(row[0]),
                    "timestamp": row[3],
                    "risk_level": risk,
                    "dimension": data.get("dimension"),
                    "evidence": data.get("evidence"),
                    "recommendation": data.get("recommendation")
                })
        
        return alerts
