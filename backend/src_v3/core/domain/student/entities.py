"""
Student Domain Module - Tutor Socrático with LangGraph

Domain entities for student learning sessions and interactions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class CognitivePhase(Enum):
    """Cognitive phases in learning process"""
    EXPLORATION = "exploration"
    DECOMPOSITION = "decomposition"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    VALIDATION = "validation"
    REFLECTION = "reflection"


class TutorMode(Enum):
    """Tutor operation modes"""
    SOCRATIC = "socratic"
    GUIDED = "guided"
    AUTONOMOUS = "autonomous"


@dataclass(frozen=True)
class StudentSession:
    """
    Domain entity for student learning session.
    
    Immutable representation of a session with cognitive state.
    """
    session_id: str
    student_id: str
    activity_id: str
    course_id: Optional[str]
    mode: TutorMode
    cognitive_phase: CognitivePhase
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool = True
    
    # Cognitive state
    autonomy_level: float = 0.5  # 0.0 to 1.0
    engagement_score: float = 0.5
    ai_dependency_score: float = 0.0
    
    # Metrics
    total_interactions: int = 0
    hints_used: int = 0
    errors_encountered: int = 0
    
    def __post_init__(self):
        """Validate domain invariants"""
        if not 0 <= self.autonomy_level <= 1:
            raise ValueError("autonomy_level must be between 0 and 1")
        if not 0 <= self.engagement_score <= 1:
            raise ValueError("engagement_score must be between 0 and 1")
        if not 0 <= self.ai_dependency_score <= 1:
            raise ValueError("ai_dependency_score must be between 0 and 1")
        if self.end_time and self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate session duration in minutes"""
        if not self.end_time:
            return None
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60
    
    @property
    def needs_intervention(self) -> bool:
        """Check if teacher intervention is needed"""
        return (
            self.ai_dependency_score > 0.7 or
            self.autonomy_level < 0.3 or
            self.engagement_score < 0.3
        )


@dataclass(frozen=True)
class TutorMessage:
    """
    Domain entity for tutor-student interaction message.
    
    Represents a single message in the Socratic dialogue.
    """
    message_id: str
    session_id: str
    sender: str  # 'student' or 'tutor'
    content: str
    timestamp: datetime
    cognitive_phase: CognitivePhase
    
    # Context
    current_code: Optional[str] = None
    error_context: Optional[Dict[str, Any]] = None
    rag_context: Optional[List[str]] = None
    
    # Analysis
    requires_guidance: bool = False
    frustration_level: float = 0.0
    understanding_level: float = 0.5
    
    def __post_init__(self):
        """Validate message"""
        if not self.content.strip():
            raise ValueError("Message content cannot be empty")
        if self.sender not in ['student', 'tutor']:
            raise ValueError("Sender must be 'student' or 'tutor'")
        if not 0 <= self.frustration_level <= 1:
            raise ValueError("frustration_level must be between 0 and 1")
        if not 0 <= self.understanding_level <= 1:
            raise ValueError("understanding_level must be between 0 and 1")
    
    @property
    def is_from_student(self) -> bool:
        """Check if message is from student"""
        return self.sender == 'student'
    
    @property
    def needs_encouragement(self) -> bool:
        """Check if student needs encouragement"""
        return self.frustration_level > 0.6 and self.is_from_student


@dataclass(frozen=True)
class LearningObjective:
    """
    Domain entity for learning objective.
    
    Represents what the student should learn/achieve in a session.
    """
    objective_id: str
    title: str
    description: str
    competencies: List[str]
    difficulty_level: str  # INICIAL, INTERMEDIO, AVANZADO
    estimated_time_minutes: int
    
    # Progress tracking
    is_achieved: bool = False
    achievement_percentage: float = 0.0
    
    def __post_init__(self):
        """Validate objective"""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.difficulty_level not in ['INICIAL', 'INTERMEDIO', 'AVANZADO']:
            raise ValueError("Invalid difficulty level")
        if not 0 <= self.achievement_percentage <= 100:
            raise ValueError("achievement_percentage must be between 0 and 100")
        if self.estimated_time_minutes <= 0:
            raise ValueError("estimated_time_minutes must be positive")
    
    @property
    def is_partially_achieved(self) -> bool:
        """Check if partially achieved"""
        return 0 < self.achievement_percentage < 100
    
    @property
    def competencies_count(self) -> int:
        """Count of competencies"""
        return len(self.competencies)


@dataclass
class SocraticDialogue:
    """
    Aggregate root for Socratic dialogue session.
    
    Manages the conversation flow between tutor and student.
    Mutable to allow conversation evolution.
    """
    session_id: str
    student_id: str
    activity_id: str
    messages: List[TutorMessage] = field(default_factory=list)
    current_phase: CognitivePhase = CognitivePhase.EXPLORATION
    learning_objective: Optional[LearningObjective] = None
    
    # State
    is_active: bool = True
    last_interaction: Optional[datetime] = None
    
    def add_message(self, message: TutorMessage) -> None:
        """Add message to dialogue"""
        if not self.is_active:
            raise ValueError("Cannot add message to inactive dialogue")
        if message.session_id != self.session_id:
            raise ValueError("Message session_id doesn't match dialogue")
        
        self.messages.append(message)
        self.last_interaction = message.timestamp
        
        # Update phase if needed
        if message.cognitive_phase != self.current_phase:
            self.current_phase = message.cognitive_phase
    
    def get_recent_messages(self, count: int = 5) -> List[TutorMessage]:
        """Get recent messages"""
        return self.messages[-count:] if self.messages else []
    
    def get_student_messages(self) -> List[TutorMessage]:
        """Get only student messages"""
        return [msg for msg in self.messages if msg.is_from_student]
    
    def get_tutor_messages(self) -> List[TutorMessage]:
        """Get only tutor messages"""
        return [msg for msg in self.messages if not msg.is_from_student]
    
    @property
    def message_count(self) -> int:
        """Total message count"""
        return len(self.messages)
    
    @property
    def average_frustration(self) -> float:
        """Average frustration level from student messages"""
        student_msgs = self.get_student_messages()
        if not student_msgs:
            return 0.0
        return sum(msg.frustration_level for msg in student_msgs) / len(student_msgs)
    
    @property
    def requires_intervention(self) -> bool:
        """Check if teacher intervention is needed"""
        return self.average_frustration > 0.7 or self.message_count > 50


# Domain exceptions
class StudentDomainException(Exception):
    """Base exception for student domain"""
    pass


class InvalidSessionStateException(StudentDomainException):
    """Session is in invalid state"""
    pass


class UnauthorizedAccessException(StudentDomainException):
    """Student not authorized for this resource"""
    pass


class LearningObjectiveNotMetException(StudentDomainException):
    """Learning objective not met"""
    pass
