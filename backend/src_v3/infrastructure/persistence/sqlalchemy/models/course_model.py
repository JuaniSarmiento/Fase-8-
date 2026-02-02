"""
Academic Structure Models - Subjects, Courses, Commissions.

Normalización de la estructura académica para evitar duplicación de datos.
"""
from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base


class SubjectModel(Base):
    """
    Subject model - Materias (ej: 'Programación I').
    
    Una materia es un concepto atemporal que se dicta en múltiples instancias (cursos).
    """
    __tablename__ = "subjects"
    
    # Identification
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    
    # Academic metadata
    credits = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)  # 1-10 (typical engineering program)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    courses = relationship("CourseModel", back_populates="subject", cascade="all, delete-orphan")
    exercises = relationship("ExerciseModel", back_populates="subject", foreign_keys="ExerciseModel.subject_id")
    
    # Indexes
    __table_args__ = (
        Index('idx_subjects_code', 'code'),
        Index('idx_subjects_active', 'is_active'),
    )


class CourseModel(Base):
    """
    Course model - Instancias de materias (ej: 'Prog I - 2025-1C').
    
    Un curso es una materia dictada en un período específico (año/semestre).
    """
    __tablename__ = "courses"
    
    # Reference to subject
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Course instance
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)  # 1 or 2
    
    # Schedule
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    subject = relationship("SubjectModel", back_populates="courses")
    commissions = relationship("CommissionModel", back_populates="course", cascade="all, delete-orphan")
    activities = relationship("ActivityModel", back_populates="course", foreign_keys="ActivityModel.course_id")
    
    # Indexes
    __table_args__ = (
        Index('idx_courses_subject', 'subject_id'),
        Index('idx_courses_year_semester', 'year', 'semester'),
        Index('idx_courses_active', 'is_active'),
    )


class CommissionModel(Base):
    """
    Commission model - Comisiones dentro de un curso (ej: 'K1021').
    
    Una comisión es un grupo de estudiantes dentro de un curso, con horario y docente específicos.
    """
    __tablename__ = "commissions"
    
    # Reference to course
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Commission identification
    code = Column(String(100), unique=True, nullable=False, index=True)
    
    # Schedule and capacity
    schedule = Column(JSONB, default=dict)  # {"monday": "14:00-18:00", "wednesday": "14:00-18:00"}
    capacity = Column(Integer, nullable=True)
    
    # Teacher
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    course = relationship("CourseModel", back_populates="commissions")
    teacher = relationship("UserModel", foreign_keys=[teacher_id])
    user_profiles = relationship("UserProfileModel", back_populates="commission")
    
    # Indexes
    __table_args__ = (
        Index('idx_commissions_course', 'course_id'),
        Index('idx_commissions_teacher', 'teacher_id'),
        Index('idx_commissions_code', 'code'),
    )
