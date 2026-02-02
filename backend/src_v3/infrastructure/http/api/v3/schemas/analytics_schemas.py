"""
Analytics API Schemas

Pydantic models for request/response validation.
These are separate from domain entities (API layer concern).
"""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class StudentRiskProfileResponse(BaseModel):
    """
    Student Risk Profile Response Schema
    """
    student_id: str
    student_name: str
    email: str
    status: str
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    time_spent_minutes: int = Field(ge=0)
    exercises_completed: int = Field(ge=0)
    total_exercises: int = Field(ge=0)
    completion_rate: float = Field(ge=0, le=100)
    last_activity: datetime
    average_attempts: float = Field(ge=0)
    ai_dependency_score: float = Field(ge=0, le=100)
    is_at_risk: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "202301",
                "student_name": "John Doe",
                "email": "john.doe@example.com",
                "status": "in_progress",
                "risk_score": 45.5,
                "risk_level": "medium",
                "time_spent_minutes": 120,
                "exercises_completed": 7,
                "total_exercises": 10,
                "completion_rate": 70.0,
                "last_activity": "2026-01-22T10:30:00",
                "average_attempts": 2.3,
                "ai_dependency_score": 35.0,
                "is_at_risk": False
            }
        }


class CourseAnalyticsResponse(BaseModel):
    """
    Course Analytics Response Schema
    """
    course_id: str
    total_students: int = Field(ge=0)
    average_risk: float = Field(ge=0, le=100)
    students_at_risk: int = Field(ge=0)
    risk_percentage: float = Field(ge=0, le=100)
    completion_rate: float = Field(ge=0, le=100)
    has_critical_risks: bool
    students: List[StudentRiskProfileResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "course_id": "PROG-101",
                "total_students": 25,
                "average_risk": 42.3,
                "students_at_risk": 5,
                "risk_percentage": 20.0,
                "completion_rate": 65.5,
                "has_critical_risks": True,
                "students": []
            }
        }
