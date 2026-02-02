"""
Enrollments Router - Gestión de Inscripciones
Endpoints para que estudiantes se inscriban a cursos y profesores gestionen inscripciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class JoinCourseRequest(BaseModel):
    course_code: str = Field(..., description="Código de acceso del curso proporcionado por el profesor")
    commission_id: Optional[str] = Field(None, description="ID de la comisión específica (opcional)")


class AddStudentRequest(BaseModel):
    student_id: str = Field(..., description="ID del estudiante a añadir")
    commission_id: Optional[str] = Field(None, description="ID de la comisión específica (opcional)")


class EnrollmentResponse(BaseModel):
    enrollment_id: str
    student_id: str
    course_id: str
    commission_id: Optional[str]
    enrolled_at: datetime
    status: str  # active, dropped, completed
    
    class Config:
        from_attributes = True


class StudentInCourseResponse(BaseModel):
    student_id: str
    user_id: str
    full_name: str
    email: str
    enrolled_at: datetime
    commission_name: Optional[str]
    status: str
    
    class Config:
        from_attributes = True


# ============================================================================
# ENDPOINTS - ESTUDIANTE
# ============================================================================

@router.post("/join", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def join_course(request: JoinCourseRequest):
    """
    Estudiante se inscribe a un curso usando un código de acceso.
    
    El profesor genera un código de acceso que los estudiantes usan para inscribirse.
    Requiere autenticación de estudiante.
    """
    # TODO: Implementar lógica de inscripción
    # TODO: Verificar autenticación del estudiante
    # TODO: Validar el código de acceso
    # TODO: Verificar capacidad de la comisión si está especificada
    # TODO: Verificar que no esté ya inscrito
    
    enrollment_id = str(uuid.uuid4())
    
    # Mock response
    return EnrollmentResponse(
        enrollment_id=enrollment_id,
        student_id="mock-student-id",
        course_id="mock-course-id",
        commission_id=request.commission_id,
        enrolled_at=datetime.now(),
        status="active"
    )


@router.get("/my-courses", response_model=List[EnrollmentResponse])
async def get_my_enrollments():
    """
    Obtener todos los cursos en los que está inscrito el estudiante autenticado.
    
    Requiere autenticación de estudiante.
    """
    # TODO: Implementar lógica de consulta
    # TODO: Verificar autenticación del estudiante
    # TODO: Obtener enrollments del estudiante desde repositorio
    
    return []


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def drop_course(course_id: str):
    """
    Estudiante se da de baja de un curso.
    
    Marca el enrollment como 'dropped' en lugar de eliminarlo.
    Requiere autenticación de estudiante.
    """
    # TODO: Implementar lógica de baja
    # TODO: Verificar autenticación del estudiante
    # TODO: Verificar que esté inscrito en el curso
    # TODO: Validar políticas de baja (fechas límite, etc.)
    
    pass


# ============================================================================
# ENDPOINTS - PROFESOR
# ============================================================================

@router.post("/teacher/courses/{course_id}/students", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def add_student_to_course(course_id: str, request: AddStudentRequest):
    """
    Profesor añade un estudiante manualmente a su curso.
    
    Útil para casos especiales o inscripciones tardías.
    Requiere autenticación de profesor.
    """
    # TODO: Implementar lógica de inscripción manual
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular del curso
    # TODO: Validar que el estudiante exista
    # TODO: Verificar que no esté ya inscrito
    
    enrollment_id = str(uuid.uuid4())
    
    return EnrollmentResponse(
        enrollment_id=enrollment_id,
        student_id=request.student_id,
        course_id=course_id,
        commission_id=request.commission_id,
        enrolled_at=datetime.now(),
        status="active"
    )


@router.get("/teacher/courses/{course_id}/students", response_model=List[StudentInCourseResponse])
async def list_students_in_course(
    course_id: str,
    commission_id: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """
    Listar todos los estudiantes inscritos en un curso.
    
    Filtros opcionales por comisión y estado (active, dropped, completed).
    Requiere autenticación de profesor.
    """
    # TODO: Implementar lógica de listado
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor tenga acceso al curso
    # TODO: Aplicar filtros si están presentes
    
    return []


@router.delete("/teacher/courses/{course_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_from_course(course_id: str, student_id: str):
    """
    Profesor remueve un estudiante de su curso.
    
    Marca el enrollment como 'dropped' por decisión del profesor.
    Requiere autenticación de profesor.
    """
    # TODO: Implementar lógica de remoción
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular del curso
    # TODO: Registrar el motivo en un log de auditoría
    
    pass


@router.post("/teacher/courses/{course_id}/access-code", status_code=status.HTTP_200_OK)
async def generate_access_code(course_id: str, commission_id: Optional[str] = None, expires_in_days: int = 30):
    """
    Generar un código de acceso para que estudiantes se inscriban.
    
    El código puede ser para todo el curso o para una comisión específica.
    Requiere autenticación de profesor.
    """
    # TODO: Implementar generación de código
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular del curso
    # TODO: Generar código único y almacenar con fecha de expiración
    
    import random
    import string
    
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    return {
        "course_id": course_id,
        "commission_id": commission_id,
        "access_code": code,
        "expires_at": datetime.now(),
        "message": "Share this code with your students to join the course"
    }


@router.get("/teacher/courses/{course_id}/access-codes")
async def list_access_codes(course_id: str):
    """
    Listar todos los códigos de acceso activos para un curso.
    
    Requiere autenticación de profesor.
    """
    # TODO: Implementar listado de códigos
    # TODO: Verificar autenticación del profesor
    # TODO: Verificar que el profesor sea titular del curso
    
    return []
