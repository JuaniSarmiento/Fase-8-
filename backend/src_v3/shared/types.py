"""
Shared types and constants
"""
from enum import Enum


class AgentMode(str, Enum):
    """Agent operation modes."""
    TUTOR = "tutor"
    GENERATOR = "generator"
    AUDITOR = "auditor"
    SIMULATOR = "simulator"


class ExerciseType(str, Enum):
    """Exercise types."""
    CODE_COMPLETION = "code_completion"
    CODE_CORRECTION = "code_correction"
    CODE_FROM_SCRATCH = "code_from_scratch"
    MULTIPLE_CHOICE = "multiple_choice"
    CONCEPTUAL = "conceptual"


class DifficultyLevel(str, Enum):
    """Difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProgrammingLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
