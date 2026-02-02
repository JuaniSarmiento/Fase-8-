"""
Database persistence helper for TeacherGeneratorGraph

Handles saving generated exercises to PostgreSQL.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import from models __init__ (uses simple_models.ActivityModel)
from backend.src_v3.infrastructure.persistence.sqlalchemy.models import (
    ActivityModel,  # This comes from simple_models.py
    ModuleModel,  # Must be imported for FK relationship to work
    CourseModel,  # Must be imported even if not used directly - needed for relationships
    ExerciseModelV2,  # Use V2 model that matches exercises_v2 table
    ExerciseDifficulty,
    ProgrammingLanguage,
)

logger = logging.getLogger(__name__)


async def publish_exercises_to_db(
    db_session: AsyncSession,
    teacher_id: str,
    course_id: str,
    approved_exercises: List[Dict[str, Any]],
    activity_title: str,
    activity_description: str,
    module_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Persist approved exercises to database as a new Activity
    
    Args:
        db_session: SQLAlchemy async session
        teacher_id: ID of the teacher creating the activity
        course_id: ID of the course
        approved_exercises: List of exercise dictionaries from LangGraph
        activity_title: Title for the generated activity
        activity_description: Description for the activity
        module_id: Optional module ID to link the activity to
    
    Returns:
        Dict with activity_id and list of created exercise_ids
    
    Raises:
        RuntimeError: If database persistence fails
    """
    try:
        logger.info(f"Persisting {len(approved_exercises)} exercises to database")
        
        # 1. Create Activity record
        activity_id = str(uuid.uuid4())  # Generate simple UUID (36 chars including hyphens)
        activity = ActivityModel(
            activity_id=activity_id,
            title=activity_title,
            subject=activity_description or "Auto-generated exercises",  # Use description as subject
            unit_id="1",  # Default unit
            instructions="Complete the following exercises based on the course material.",
            course_id=None,  # Always NULL for now - course setup required separately
            module_id=module_id,  # ✅ Link to module
            order_index=0,  # ✅ First activity in module
            teacher_id=teacher_id,
            policies={
                "allow_retries": True,
                "max_attempts": 3,
                "show_solution_after_submit": False
            },
            difficulty_level="intermedio",  # Average difficulty
            status="active",  # Use lowercase string
            start_date=datetime.utcnow(),
            end_date=None  # Open-ended
        )
        
        db_session.add(activity)
        logger.info(f"Created activity: {activity_id}")
        
        # 2. Create Exercise records
        exercise_ids = []
        for idx, exercise_data in enumerate(approved_exercises):
            exercise_id = str(uuid.uuid4())  # Generate simple UUID (36 chars)
            
            # Map difficulty to enum
            # Map difficulty to enum
            difficulty_map = {
                "easy": "facil",
                "medium": "intermedio",
                "hard": "dificil",
                "facil": "facil",
                "intermedio": "intermedio",
                "dificil": "dificil",
            }
            difficulty = difficulty_map.get(
                exercise_data.get("difficulty", "medium").lower(),
                "intermedio"
            )
            
            exercise = ExerciseModelV2(
                exercise_id=exercise_id,
                activity_id=activity_id,  # Link to parent activity
                title=exercise_data.get("title", f"Exercise {idx + 1}"),
                description=exercise_data.get("description", ""),
                subject_id=None,  # Set to NULL - no subject mapping for now
                unit_number=1,  # Default unit
                difficulty=difficulty,
                language="python",
                mission_markdown=exercise_data.get("mission_markdown") or exercise_data.get("description", "Complete this exercise."),
                starter_code=exercise_data.get("starter_code", "# TODO: Write your code here\n"),
                solution_code=exercise_data.get("solution_code", ""),
                test_cases=exercise_data.get("test_cases", []),
                tags=["auto-generated"],
                estimated_time_minutes=15
            )
            
            db_session.add(exercise)
            exercise_ids.append(exercise_id)
            logger.debug(f"Created exercise {idx + 1}/{len(approved_exercises)}: {exercise.title}")
        
        # 3. Commit transaction
        await db_session.commit()
        
        logger.info(
            f"Successfully persisted activity {activity_id} with {len(exercise_ids)} exercises",
            extra={"activity_id": activity_id, "exercise_count": len(exercise_ids)}
        )
        
        return {
            "activity_id": activity_id,
            "exercise_ids": exercise_ids,
            "total_exercises": len(exercise_ids),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to persist exercises to database: {e}", exc_info=True)
        await db_session.rollback()
        raise RuntimeError(f"Database persistence failed: {str(e)}")


async def get_activity_with_exercises(
    db_session: AsyncSession,
    activity_id: str
) -> Dict[str, Any]:
    """
    Retrieve an activity with all its exercises
    
    Args:
        db_session: SQLAlchemy async session
        activity_id: ID of the activity
    
    Returns:
        Dict with activity and exercises data
    """
    try:
        # Fetch activity
        result = await db_session.execute(
            select(ActivityModel).where(ActivityModel.activity_id == activity_id)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        
        # Fetch exercises
        result = await db_session.execute(
            select(ExerciseModel)
            .where(ExerciseModel.activity_id == activity_id)
            .order_by(ExerciseModel.order_index)
        )
        exercises = result.scalars().all()
        
        return {
            "activity_id": activity.activity_id,
            "title": activity.title,
            "description": activity.description,
            "status": activity.status,
            "exercise_count": len(exercises),
            "exercises": [
                {
                    "title": ex.title,
                    "description": ex.description,
                    "difficulty": ex.difficulty,
                    "language": ex.language,
                    "order_index": ex.order_index
                }
                for ex in exercises
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve activity: {e}", exc_info=True)
        raise RuntimeError(f"Failed to retrieve activity: {str(e)}")
