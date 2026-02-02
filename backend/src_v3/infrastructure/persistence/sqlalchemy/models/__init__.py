"""
SQLAlchemy Models - Improved with normalized academic structure

V2 models include:
- Normalized structure (Subjects → Courses → Commissions)
- Proper ForeignKeys with CASCADE/SET NULL
- Enums for all status/type fields
- Soft delete support
- Comprehensive indexes

V3 additions (LMS Hierarchy):
- ModuleModel (Course → Module → Activity hierarchy)
- EnrollmentModel (Many-to-Many Users ↔ Courses with roles)
- UserGamificationModel (XP, levels, streaks)
"""
from backend.src_v3.infrastructure.persistence.sqlalchemy.simple_models import (
    Base,
    UserModel,
    UserProfileModel,
    SubjectModel,
    CourseModel,
    CommissionModel,
    ActivityModel,
    SessionModelV2,
    ExerciseModelV2,
    ExerciseAttemptModelV2,
    CognitiveTraceModelV2,
    RiskModelV2,
    # Enums
    ActivityStatus,
    DifficultyLevel,
    SessionStatus,
    SessionMode,
    ExerciseDifficulty,
    ProgrammingLanguage,
    TraceLevel,
    InteractionType,
)

# V3 LMS Hierarchy Models
from .module_model import ModuleModel
from .enrollment_model import EnrollmentModel, EnrollmentRole, EnrollmentStatus
from .gamification_model import UserGamificationModel

__all__ = [
    "Base",
    # Users & Profiles
    "UserModel",
    "UserProfileModel",
    # Academic Structure
    "SubjectModel",
    "CourseModel",
    "CommissionModel",
    # LMS Hierarchy (V3)
    "ModuleModel",
    "EnrollmentModel",
    "EnrollmentRole",
    "EnrollmentStatus",
    "UserGamificationModel",
    # Activities
    "ActivityModel",
    "ActivityStatus",
    "DifficultyLevel",
    # Sessions (V2)
    "SessionModelV2",
    "SessionStatus",
    "SessionMode",
    # Exercises (V2)
    "ExerciseModelV2",
    "ExerciseDifficulty",
    "ProgrammingLanguage",
    # Attempts (V2)
    "ExerciseAttemptModelV2",
    # Traces (V2)
    "CognitiveTraceModelV2",
    "TraceLevel",
    "InteractionType",
    # Risks (V2)
    "RiskModelV2",
]
