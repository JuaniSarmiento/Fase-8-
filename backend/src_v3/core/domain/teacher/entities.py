"""
Teacher Domain Module - Exercise Generation with RAG

Domain entities for teacher activities, content creation, and pedagogy.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ExerciseType(Enum):
    """Types of exercises"""
    CODING = "coding"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    ANALYSIS = "analysis"
    DESIGN = "design"


class PedagogicalPolicy(Enum):
    """Pedagogical policies for AI assistance"""
    MINIMAL = "minimal"  # Minimal hints
    BALANCED = "balanced"  # Balanced guidance
    SUPPORTIVE = "supportive"  # More help allowed
    AUTONOMOUS = "autonomous"  # Student must solve independently


@dataclass(frozen=True)
class ExerciseRequirements:
    """
    Value object for exercise generation requirements.
    
    Specifies what kind of exercise to generate.
    """
    topic: str
    difficulty: str  # FACIL, INTERMEDIO, AVANZADO
    unit_number: int
    language: str
    estimated_time_minutes: int
    concepts: List[str]
    count: int = 3  # Number of exercises to generate
    
    # Constraints
    max_lines_of_code: Optional[int] = None
    requires_external_libs: bool = False
    allow_recursion: bool = True
    
    def __post_init__(self):
        """Validate requirements"""
        if not self.topic.strip():
            raise ValueError("Topic cannot be empty")
        if self.difficulty not in ['FACIL', 'INTERMEDIO', 'AVANZADO']:
            raise ValueError("Invalid difficulty")
        if self.unit_number < 1:
            raise ValueError("unit_number must be positive")
        if self.estimated_time_minutes < 5:
            raise ValueError("estimated_time_minutes must be >= 5")
        if not self.concepts:
            raise ValueError("At least one concept required")
    
    @property
    def is_advanced(self) -> bool:
        """Check if advanced exercise"""
        return self.difficulty == 'AVANZADO'


@dataclass(frozen=True)
class TestCase:
    """
    Value object for exercise test case.
    
    Represents a unit test for validating student solutions.
    """
    test_number: int
    description: str
    input_data: str
    expected_output: str
    is_hidden: bool = False
    timeout_seconds: int = 5
    
    def __post_init__(self):
        """Validate test case"""
        if self.test_number < 1:
            raise ValueError("test_number must be positive")
        if not self.description.strip():
            raise ValueError("Description cannot be empty")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
    
    @property
    def is_visible(self) -> bool:
        """Check if visible to student"""
        return not self.is_hidden


@dataclass(frozen=True)
class GeneratedExercise:
    """
    Domain entity for generated exercise.
    
    Immutable representation of a complete exercise.
    """
    exercise_id: str
    title: str
    description: str
    difficulty: str
    language: str
    
    # Content
    mission_markdown: str
    starter_code: str
    solution_code: str
    
    # Validation
    test_cases: List[TestCase]
    
    # Metadata
    concepts: List[str]
    learning_objectives: List[str]
    estimated_time_minutes: int
    pedagogical_notes: Optional[str] = None
    
    # Generation metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    rag_sources: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate exercise"""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.mission_markdown.strip():
            raise ValueError("Mission cannot be empty")
        if not self.starter_code.strip():
            raise ValueError("Starter code cannot be empty")
        if not self.test_cases:
            raise ValueError("At least one test case required")
        # if len(self.test_cases) < 2:
        #     raise ValueError("At least 2 test cases recommended")
    
    @property
    def hidden_test_count(self) -> int:
        """Count hidden tests"""
        return sum(1 for test in self.test_cases if test.is_hidden)
    
    @property
    def visible_test_count(self) -> int:
        """Count visible tests"""
        return sum(1 for test in self.test_cases if not test.is_hidden)
    
    @property
    def has_solution(self) -> bool:
        """Check if solution is provided"""
        return bool(self.solution_code and self.solution_code.strip())


@dataclass(frozen=True)
class PedagogicalContent:
    """
    Domain entity for pedagogical content (apuntes/notes).
    
    Represents course materials used for RAG context.
    """
    content_id: str
    title: str
    unit_number: int
    subject_code: str
    
    # Content
    content_markdown: str
    examples: List[str]
    key_concepts: List[str]
    
    # Metadata
    author: str
    created_at: datetime
    version: int = 1
    
    # RAG metadata
    chunk_count: int = 0
    is_indexed: bool = False
    
    def __post_init__(self):
        """Validate content"""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.content_markdown.strip():
            raise ValueError("Content cannot be empty")
        if self.unit_number < 1:
            raise ValueError("unit_number must be positive")
        if not self.subject_code.strip():
            raise ValueError("subject_code cannot be empty")
    
    @property
    def has_examples(self) -> bool:
        """Check if has examples"""
        return bool(self.examples)
    
    @property
    def concept_count(self) -> int:
        """Count key concepts"""
        return len(self.key_concepts)


@dataclass
class Activity:
    """
    Aggregate root for teaching activity.
    
    Manages exercises, content, and pedagogical policies.
    Mutable to allow activity evolution.
    """
    activity_id: str
    title: str
    course_id: str
    teacher_id: str
    
    # Content
    instructions: str
    exercises: List[GeneratedExercise] = field(default_factory=list)
    pedagogical_content: List[PedagogicalContent] = field(default_factory=list)
    
    # Policies
    policy: PedagogicalPolicy = PedagogicalPolicy.BALANCED
    max_ai_help_level: str = "MEDIO"
    allow_code_snippets: bool = False
    require_justification: bool = True
    
    # Status
    status: str = "draft"  # draft, active, archived
    published_at: Optional[datetime] = None
    
    def add_exercise(self, exercise: GeneratedExercise) -> None:
        """Add exercise to activity"""
        if self.status == "archived":
            raise ValueError("Cannot add exercise to archived activity")
        if any(e.exercise_id == exercise.exercise_id for e in self.exercises):
            raise ValueError("Exercise already exists in activity")
        
        self.exercises.append(exercise)
    
    def remove_exercise(self, exercise_id: str) -> None:
        """Remove exercise from activity"""
        if self.status == "archived":
            raise ValueError("Cannot remove exercise from archived activity")
        
        self.exercises = [e for e in self.exercises if e.exercise_id != exercise_id]
    
    def add_content(self, content: PedagogicalContent) -> None:
        """Add pedagogical content"""
        if any(c.content_id == content.content_id for c in self.pedagogical_content):
            raise ValueError("Content already exists in activity")
        
        self.pedagogical_content.append(content)
    
    def publish(self) -> None:
        """Publish activity"""
        if self.status != "draft":
            raise ValueError("Can only publish draft activities")
        if not self.exercises:
            raise ValueError("Cannot publish activity without exercises")
        
        self.status = "active"
        self.published_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive activity"""
        if self.status == "archived":
            raise ValueError("Activity already archived")
        
        self.status = "archived"
    
    @property
    def exercise_count(self) -> int:
        """Total exercises"""
        return len(self.exercises)
    
    @property
    def content_count(self) -> int:
        """Total pedagogical content"""
        return len(self.pedagogical_content)
    
    @property
    def is_published(self) -> bool:
        """Check if published"""
        return self.status == "active" and self.published_at is not None
    
    @property
    def total_estimated_time(self) -> int:
        """Total estimated time for all exercises"""
        return sum(ex.estimated_time_minutes for ex in self.exercises)


# Domain exceptions
class TeacherDomainException(Exception):
    """Base exception for teacher domain"""
    pass


class InvalidExerciseException(TeacherDomainException):
    """Exercise is invalid"""
    pass


class InsufficientRAGContextException(TeacherDomainException):
    """Not enough RAG context to generate exercise"""
    pass


class ActivityPublicationException(TeacherDomainException):
    """Cannot publish activity"""
    pass
