"""
LMS Hierarchy Schemas - Modules, Enrollments, Gamification

Pydantic schemas for the new LMS hierarchical structure.
"""
from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ========================================
# ENUMS
# ========================================
class EnrollmentRoleEnum(str, Enum):
    """Enrollment role options"""
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    TA = "TA"
    OBSERVER = "OBSERVER"


class EnrollmentStatusEnum(str, Enum):
    """Enrollment status options"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"


# ========================================
# MODULE SCHEMAS
# ========================================
class ModuleBase(BaseModel):
    """Base module schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = Field(default=0, ge=0)
    is_published: bool = False
    metadata_json: dict = Field(default_factory=dict)


class ModuleCreate(ModuleBase):
    """Schema for creating a module"""
    course_id: str = Field(..., min_length=1)


class ModuleUpdate(BaseModel):
    """Schema for updating a module"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None
    metadata_json: Optional[dict] = None


class ModuleRead(ModuleBase):
    """Schema for reading a module"""
    model_config = ConfigDict(from_attributes=True)
    
    module_id: str
    course_id: str
    created_at: datetime
    updated_at: datetime
    
    # Optional nested activities (populated by endpoint)
    activities: Optional[List[Any]] = None  # List[ActivityRead] - avoid circular import


# ========================================
# ENROLLMENT SCHEMAS
# ========================================
class EnrollmentBase(BaseModel):
    """Base enrollment schema"""
    role: EnrollmentRoleEnum = EnrollmentRoleEnum.STUDENT
    status: EnrollmentStatusEnum = EnrollmentStatusEnum.ACTIVE
    metadata_json: dict = Field(default_factory=dict)


class EnrollmentCreate(EnrollmentBase):
    """Schema for creating an enrollment"""
    user_id: str = Field(..., min_length=1)
    course_id: str = Field(..., min_length=1)
    module_id: Optional[str] = Field(None, description="Module/commission to enroll student in")


class EnrollmentUpdate(BaseModel):
    """Schema for updating an enrollment"""
    role: Optional[EnrollmentRoleEnum] = None
    status: Optional[EnrollmentStatusEnum] = None
    metadata_json: Optional[dict] = None


class EnrollmentRead(EnrollmentBase):
    """Schema for reading an enrollment"""
    model_config = ConfigDict(from_attributes=True)
    
    enrollment_id: str
    user_id: str
    course_id: str
    module_id: Optional[str] = None
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    dropped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ========================================
# USER GAMIFICATION SCHEMAS
# ========================================
class UserGamificationBase(BaseModel):
    """Base gamification schema"""
    xp: int = Field(default=0, ge=0)
    level: int = Field(default=1, ge=1)
    streak_days: int = Field(default=0, ge=0)
    longest_streak: int = Field(default=0, ge=0)
    achievements: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    total_exercises_completed: int = Field(default=0, ge=0)
    total_activities_completed: int = Field(default=0, ge=0)
    total_hints_used: int = Field(default=0, ge=0)


class UserGamificationCreate(UserGamificationBase):
    """Schema for creating gamification record"""
    user_id: str = Field(..., min_length=1)


class UserGamificationUpdate(BaseModel):
    """Schema for updating gamification record"""
    xp: Optional[int] = Field(None, ge=0)
    level: Optional[int] = Field(None, ge=1)
    streak_days: Optional[int] = Field(None, ge=0)
    longest_streak: Optional[int] = Field(None, ge=0)
    last_activity_date: Optional[date] = None
    achievements: Optional[List[str]] = None
    badges: Optional[List[str]] = None
    total_exercises_completed: Optional[int] = Field(None, ge=0)
    total_activities_completed: Optional[int] = Field(None, ge=0)
    total_hints_used: Optional[int] = Field(None, ge=0)


class UserGamificationRead(UserGamificationBase):
    """Schema for reading gamification record"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    last_activity_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


# ========================================
# NESTED COURSE WITH MODULES (for student view)
# ========================================
class CourseWithModules(BaseModel):
    """Course with nested modules and activities"""
    model_config = ConfigDict(from_attributes=True)
    
    course_id: str
    name: str
    year: int
    semester: str
    modules: List[ModuleRead] = Field(default_factory=list)
    
    # Enrollment info
    enrollment_role: Optional[EnrollmentRoleEnum] = None
    enrollment_status: Optional[EnrollmentStatusEnum] = None
