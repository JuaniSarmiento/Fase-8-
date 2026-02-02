"""
Admin Router - Gestión Administrativa (Backoffice)
Endpoints para crear materias, cursos, comisiones y gestionar roles de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateSubjectRequest(BaseModel):
    code: str = Field(..., description="Código único de la materia, ej: PROG-101")
    name: str = Field(..., description="Nombre de la materia")
    credits: int = Field(..., ge=1, le=10, description="Créditos de la materia")
    description: Optional[str] = None


class CreateCourseRequest(BaseModel):
    subject_id: str = Field(..., description="ID de la materia")
    year: int = Field(..., ge=2020, le=2030)
    semester: int = Field(..., ge=1, le=2)
    

class CreateCommissionRequest(BaseModel):
    course_id: str = Field(..., description="ID del curso")
    teacher_id: str = Field(..., description="ID del profesor")
    name: str = Field(..., description="Nombre de la comisión, ej: 'Comisión A'")
    schedule: Optional[dict] = Field(None, description="Horarios en formato JSON")
    capacity: Optional[int] = Field(None, ge=1, description="Capacidad máxima")


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="Nuevo rol: 'student', 'teacher', 'admin'")


class SubjectResponse(BaseModel):
    subject_id: str
    code: str
    name: str
    credits: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseResponse(BaseModel):
    course_id: str
    subject_id: str
    year: int
    semester: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommissionResponse(BaseModel):
    commission_id: str
    course_id: str
    teacher_id: str
    name: str
    schedule: Optional[dict]
    capacity: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(request: CreateSubjectRequest):
    """
    Crear una nueva materia en el sistema.
    
    Requiere rol de administrador.
    """
    # TODO: Implementar lógica de creación en repositorio
    # TODO: Verificar autenticación y rol de admin
    # TODO: Validar que el código no exista
    
    subject_id = str(uuid.uuid4())
    
    return SubjectResponse(
        subject_id=subject_id,
        code=request.code,
        name=request.name,
        credits=request.credits,
        created_at=datetime.now()
    )


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(request: CreateCourseRequest):
    """
    Abrir un nuevo curso/cursada anual.
    
    Requiere rol de administrador.
    """
    # TODO: Implementar lógica de creación en repositorio
    # TODO: Verificar autenticación y rol de admin
    # TODO: Validar que subject_id exista
    
    course_id = str(uuid.uuid4())
    
    return CourseResponse(
        course_id=course_id,
        subject_id=request.subject_id,
        year=request.year,
        semester=request.semester,
        created_at=datetime.now()
    )


@router.post("/commissions", response_model=CommissionResponse, status_code=status.HTTP_201_CREATED)
async def create_commission(request: CreateCommissionRequest):
    """
    Crear una nueva comisión para un curso.
    
    Requiere rol de administrador.
    """
    # TODO: Implementar lógica de creación en repositorio
    # TODO: Verificar autenticación y rol de admin
    # TODO: Validar que course_id y teacher_id existan
    
    commission_id = str(uuid.uuid4())
    
    return CommissionResponse(
        commission_id=commission_id,
        course_id=request.course_id,
        teacher_id=request.teacher_id,
        name=request.name,
        schedule=request.schedule,
        capacity=request.capacity,
        created_at=datetime.now()
    )


@router.post("/users/{user_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role(user_id: str, request: UpdateUserRoleRequest):
    """
    Promover o cambiar el rol de un usuario.
    
    Requiere rol de administrador.
    Permite cambiar entre: student, teacher, admin
    """
    # TODO: Implementar lógica de actualización en repositorio
    # TODO: Verificar autenticación y rol de admin
    # TODO: Validar que user_id exista
    # TODO: Validar que el rol sea válido
    
    valid_roles = ["student", "teacher", "admin"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    return {
        "message": f"User role updated to {request.role}",
        "user_id": user_id,
        "new_role": request.role
    }


@router.get("/subjects", response_model=List[SubjectResponse])
async def list_all_subjects(include_deleted: bool = False):
    """
    Listar todas las materias del sistema (para administración).
    
    Incluye materias eliminadas si include_deleted=true
    """
    # TODO: Implementar lógica de listado desde repositorio
    return []


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: str, soft_delete: bool = True):
    """
    Eliminar una materia del sistema.
    
    Por defecto hace soft delete (marca como eliminada).
    """
    # TODO: Implementar lógica de eliminación
    # TODO: Verificar que no tenga cursos activos
    pass


@router.get("/courses", response_model=List[CourseResponse])
async def list_all_courses(year: Optional[int] = None, semester: Optional[int] = None):
    """
    Listar todos los cursos del sistema (para administración).
    
    Filtros opcionales por año y semestre.
    """
    # TODO: Implementar lógica de listado desde repositorio
    return []
