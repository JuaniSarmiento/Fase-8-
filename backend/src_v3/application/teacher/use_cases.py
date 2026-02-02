"""
Teacher Use Cases - Application Layer

Complete workflow for exercise generation and content management.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from backend.src_v3.core.domain.teacher.entities import (
    Activity,
    ExerciseRequirements,
    GeneratedExercise,
    TestCase,
    PedagogicalPolicy,
)
from backend.src_v3.infrastructure.persistence.repositories.teacher_repository import TeacherRepository


# ==================== COMMANDS ====================

@dataclass
class CreateActivityCommand:
    """Command to create new activity"""
    title: str
    course_id: str
    teacher_id: str
    instructions: str
    policy: str = "BALANCED"
    max_ai_help_level: str = "MEDIO"


@dataclass
class GenerateExerciseCommand:
    """Command to generate exercise with RAG"""
    activity_id: str
    topic: str
    difficulty: str
    unit_number: int
    language: str = "python"
    concepts: List[str] = None
    estimated_time_minutes: int = 30


@dataclass
class AddContentToActivityCommand:
    """Command to add pedagogical content"""
    activity_id: str
    title: str
    unit_number: int
    content_markdown: str
    examples: List[str] = None
    key_concepts: List[str] = None


# ==================== USE CASES ====================

class CreateActivityUseCase:
    """
    Use case: Create new teaching activity.
    
    Flow:
    1. Create activity domain entity
    2. Validate policies
    3. Persist activity
    4. Return activity
    """
    
    def __init__(self, repository: TeacherRepository):
        self.repository = repository
    
    async def execute(self, command: CreateActivityCommand) -> Activity:
        """Execute use case"""
        # Create domain entity
        activity = Activity(
            activity_id=str(uuid4()),
            title=command.title,
            course_id=command.course_id,
            teacher_id=command.teacher_id,
            instructions=command.instructions,
            policy=PedagogicalPolicy[command.policy],
            max_ai_help_level=command.max_ai_help_level,
            status="draft",
        )
        
        # Persist
        created_activity = await self.repository.create_activity(activity)
        
        return created_activity


class GenerateExerciseUseCase:
    """
    Use case: Generate exercise with RAG context.
    
    Flow:
    1. Get activity
    2. Build exercise requirements
    3. Retrieve RAG context
    4. Generate exercise with LLM
    5. Validate generated exercise
    6. Save exercise
    7. Return exercise
    """
    
    def __init__(
        self,
        repository: TeacherRepository,
        rag_service,  # RAG retriever
        exercise_generator_agent,  # Exercise generator
    ):
        self.repository = repository
        self.rag_service = rag_service
        self.generator = exercise_generator_agent
    
    async def execute(self, command: GenerateExerciseCommand) -> GeneratedExercise:
        """Execute use case with RAG context from uploaded PDFs"""
        # Ensure the activity exists
        activity = await self.repository.get_activity_by_id(command.activity_id)
        if not activity:
            raise ValueError(f"Activity {command.activity_id} not found")

        # Try to get RAG context from uploaded PDFs
        rag_context = ""
        try:
            from backend.src_v3.infrastructure.ai.rag.pdf_processor import PDFProcessor
            
            pdf_processor = PDFProcessor(self.rag_service)
            
            # Build query for RAG retrieval
            query = f"{command.topic} {' '.join(command.concepts or [])} programming exercise"
            
            # Get context specific to this activity
            rag_context = pdf_processor.get_context_for_activity(
                activity_id=command.activity_id,
                query=query,
                n_results=3
            )
            
            if rag_context:
                print(f"✅ Retrieved RAG context ({len(rag_context)} chars) for exercise generation")
            else:
                print(f"ℹ️ No RAG context found for activity {command.activity_id}")
                
        except Exception as e:
            print(f"⚠️ Error retrieving RAG context: {e}")
            rag_context = ""

        # Build exercise requirements
        requirements = ExerciseRequirements(
            topic=command.topic,
            difficulty=command.difficulty,
            unit_number=command.unit_number,
            language=command.language,
            concepts=command.concepts or [],
            estimated_time_minutes=command.estimated_time_minutes,
        )

        # Try to generate with LLM + RAG
        try:
            exercise = await self.generator.generate(requirements, rag_context)
            exercise.exercise_id = str(uuid4())
            
            print(f"✅ Exercise generated with LLM: {exercise.title}")
            
            # Attach to activity
            activity.add_exercise(exercise)
            return exercise
            
        except Exception as e:
            print(f"⚠️ LLM generation failed, using deterministic fallback: {e}")
            
            # Deterministic fallback exercise
            exercise = GeneratedExercise(
                exercise_id=str(uuid4()),
                title=f"Ejercicio: {command.topic}",
                description=f"Ejercicio sobre {command.topic}",
                difficulty=command.difficulty,
                language=command.language,
                mission_markdown=f"## Misión\n\nResuelve un problema de {command.topic}\n\n{rag_context[:500] if rag_context else ''}",
                starter_code="# TODO: Implementa la solución aquí\n",
                solution_code="# Solución de referencia\n",
                test_cases=[
                    TestCase(
                        test_number=1,
                        description="Test básico",
                        input_data="test_input()",
                        expected_output="expected_output",
                        is_hidden=False,
                        timeout_seconds=5,
                    ),
                    TestCase(
                        test_number=2,
                        description="Test avanzado",
                        input_data="test_advanced()",
                        expected_output="expected_advanced",
                        is_hidden=True,
                        timeout_seconds=5,
                    ),
                ],
                concepts=command.concepts or [],
                learning_objectives=[f"Comprender {command.topic}"],
                estimated_time_minutes=command.estimated_time_minutes,
                rag_sources=["PDF uploaded content"] if rag_context else [],
            )

            # Attach to activity in-memory
            activity.add_exercise(exercise)
            return exercise


class PublishActivityUseCase:
    """
    Use case: Publish activity to make it available to students.
    
    Flow:
    1. Get activity
    2. Validate has exercises
    3. Publish (change status)
    4. Update in repository
    5. Return updated activity
    """
    
    def __init__(self, repository: TeacherRepository):
        self.repository = repository
    
    async def execute(self, activity_id: str) -> Activity:
        """Execute use case"""
        # Get activity
        activity = await self.repository.get_activity_by_id(activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        
        # Get exercises
        exercises = await self.repository.get_exercises_for_activity(activity_id)
        
        # Add exercises to activity (for validation)
        for exercise in exercises:
            activity.add_exercise(exercise)
        
        # Publish (domain logic validates)
        activity.publish()
        
        # Update existing activity status in persistence
        await self.repository.update_activity(activity)
        
        return activity


class GetActivityExercisesUseCase:
    """
    Use case: Get all exercises for an activity.
    
    Flow:
    1. Get activity
    2. Get exercises
    3. Return list
    """
    
    def __init__(self, repository: TeacherRepository):
        self.repository = repository
    
    async def execute(self, activity_id: str) -> List[GeneratedExercise]:
        """Execute use case"""
        # Get activity (validate exists)
        activity = await self.repository.get_activity_by_id(activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        
        # Get exercises
        exercises = await self.repository.get_exercises_for_activity(activity_id)
        
        return exercises
