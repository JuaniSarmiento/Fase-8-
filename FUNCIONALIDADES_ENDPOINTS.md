# 🎯 FUNCIONALIDADES DEL BACKEND - AI-Native MVP V3

## 📚 RESUMEN GENERAL

El backend es una plataforma de aprendizaje con IA que incluye:
- **Analytics** de progreso y riesgo estudiantil
- **Tutor Socrático** con IA para estudiantes
- **Generación de ejercicios** con IA para profesores
- **Gestión de actividades** y cursos
- **Sistema de gobernanza** (GSR) para detección de riesgo
- **Autenticación y autorización** JWT
- **Catálogo académico** (materias, cursos, comisiones)

---

## 🔌 TODOS LOS ENDPOINTS

### 1️⃣ **Analytics** (`/api/v3/analytics`)

#### `GET /api/v3/analytics/courses/{course_id}`
Obtiene análisis agregado de un curso completo:
- Total de estudiantes
- Score promedio de riesgo
- Estudiantes en riesgo
- Tasa de completitud
- Perfiles individuales de estudiantes

**Ejemplo Response:**
```json
{
  "course_id": "PROG-101",
  "total_students": 25,
  "average_risk_score": 0.35,
  "students_at_risk_count": 5,
  "completion_rate": 78.5,
  "student_profiles": [...]
}
```

#### `GET /api/v3/analytics/students/{student_id}/risk-profile`
Obtiene el perfil de riesgo de un estudiante específico:
- Score de riesgo (0-1)
- Nivel de riesgo (BAJO/MEDIO/ALTO/CRITICO)
- Factores de riesgo identificados
- Recomendaciones
- Score de dependencia de IA

**Ejemplo Response:**
```json
{
  "student_id": "STU001",
  "risk_score": 0.65,
  "risk_level": "MEDIO",
  "risk_factors": {
    "ai_dependency": 0.7,
    "error_rate": 0.4,
    "completion_rate": 0.5
  },
  "ai_dependency_score": 0.7,
  "recommendations": [...]
}
```

---

### 2️⃣ **Student** (`/api/v3/student`) - Tutor Socrático con IA

#### `POST /api/v3/student/sessions/start`
Inicia una sesión de aprendizaje con el tutor de IA:
- Modo Socrático (preguntas guiadas)
- Seguimiento cognitivo
- Detección de frustración

**Request:**
```json
{
  "student_id": "STU001",
  "activity_id": "ACT001",
  "course_id": "PROG-101",
  "mode": "SOCRATIC"
}
```

**Response:**
```json
{
  "session_id": "sess-123",
  "student_id": "STU001",
  "activity_id": "ACT001",
  "mode": "SOCRATIC",
  "cognitive_phase": "EXPLORATION",
  "start_time": "2026-01-25T...",
  "is_active": true
}
```

#### `POST /api/v3/student/sessions/{session_id}/message`
Envía un mensaje al tutor de IA:
- Análisis cognitivo en tiempo real
- Detección de frustración
- Respuestas socráticas adaptativas

**Request:**
```json
{
  "message": "No entiendo cómo usar loops",
  "current_code": "for i in range(10):\n  ...",
  "error_context": {...}
}
```

**Response:**
```json
{
  "message_id": "msg-456",
  "session_id": "sess-123",
  "sender": "tutor",
  "content": "Excelente pregunta. ¿Qué crees que hace range(10)?",
  "cognitive_phase": "UNDERSTANDING",
  "frustration_level": 0.3,
  "understanding_level": 0.6
}
```

#### `GET /api/v3/student/sessions/{session_id}/history`
Obtiene el historial de conversación con métricas:
- Todos los mensajes
- Nivel promedio de frustración
- Requiere intervención humana

#### `POST /api/v3/student/sessions/{session_id}/submit-code`
Envía código para revisión por IA:
- Análisis de calidad
- Detección de errores
- Sugerencias de mejora

#### `WebSocket /api/v3/student/sessions/{session_id}/ws`
Chat en tiempo real con el tutor de IA

---

### 3️⃣ **Teacher** (`/api/v3/teacher`) - Herramientas para Profesores

#### `POST /api/v3/teacher/activities`
Crea una nueva actividad de aprendizaje:
- Define política de uso de IA (STRICT/BALANCED/PERMISSIVE)
- Nivel máximo de ayuda de IA
- Instrucciones y recursos

**Request:**
```json
{
  "title": "Introducción a Loops",
  "course_id": "PROG-101",
  "teacher_id": "TEACH001",
  "instructions": "Crear un programa que...",
  "policy": "BALANCED",
  "max_ai_help_level": "MEDIO"
}
```

#### `GET /api/v3/teacher/activities`
Lista todas las actividades del profesor

#### `GET /api/v3/teacher/activities/{activity_id}`
Obtiene detalles de una actividad específica

#### `PUT /api/v3/teacher/activities/{activity_id}`
Actualiza una actividad existente

#### `POST /api/v3/teacher/activities/{activity_id}/publish`
Publica una actividad (la hace visible para estudiantes)

#### `POST /api/v3/teacher/exercises/generate`
**🤖 GENERACIÓN DE EJERCICIOS CON IA**:
- Genera automáticamente ejercicios de programación
- Con casos de prueba
- Solución de referencia
- Explicación didáctica

**Request:**
```json
{
  "topic": "Bucles for en Python",
  "difficulty": "INTERMEDIO",
  "unit_number": 3,
  "language": "python",
  "concepts": ["iteración", "range", "acumuladores"],
  "estimated_time_minutes": 45
}
```

**Response:**
```json
{
  "exercise_id": "ex-789",
  "title": "Suma de números pares",
  "description": "Crear una función que...",
  "difficulty": "INTERMEDIO",
  "test_cases": [
    {
      "test_number": 1,
      "input_data": "[1,2,3,4,5]",
      "expected_output": "6",
      "is_hidden": false
    }
  ],
  "reference_solution": "def suma_pares(lista): ...",
  "pedagogical_explanation": "Este ejercicio enseña...",
  "estimated_time_minutes": 45
}
```

#### `GET /api/v3/teacher/activities/{activity_id}/exercises`
Lista ejercicios de una actividad

#### `POST /api/v3/teacher/documents/upload`
Sube documentos de referencia (PDF, DOCX, MD)

#### `GET /api/v3/teacher/documents`
Lista documentos subidos

#### `POST /api/v3/teacher/documents/{document_id}/ingest`
Ingesta documento al RAG (Retrieval Augmented Generation)

#### `GET /api/v3/teacher/documents/{document_id}/status`
Verifica estado de ingesta del documento

---

### 4️⃣ **Authentication** (`/api/v3/auth`)

#### `POST /api/v3/auth/login`
Login con email y contraseña:
**Request:**
```json
{
  "email": "student@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "student01",
    "email": "student@example.com",
    "full_name": "Juan Pérez",
    "roles": ["student"],
    "is_active": true
  },
  "tokens": {
    "access_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

#### `POST /api/v3/auth/token`
Login OAuth2 (para Swagger UI):
- Formato: `application/x-www-form-urlencoded`
- username=email, password=password

#### `POST /api/v3/auth/register`
Registra un nuevo usuario:
**Request:**
```json
{
  "username": "student02",
  "email": "student2@example.com",
  "password": "securepass",
  "full_name": "María García",
  "role": "student"
}
```

#### `GET /api/v3/auth/me`
Obtiene perfil del usuario autenticado (requiere Bearer token):
**Headers:**
```
Authorization: Bearer eyJ...
```

---

### 5️⃣ **Governance / GSR** (`/api/v3/governance`) - Sistema de Gestión de Riesgo

#### `GET /api/v3/governance/sessions/{session_id}`
Obtiene estado de gobernanza/riesgo de una sesión:
- Score de riesgo
- Nivel de riesgo
- Score de dependencia de IA
- Factores de riesgo
- **Análisis de IA** (opcional)

**Response:**
```json
{
  "has_risk": true,
  "session_id": "sess-123",
  "student_id": "STU001",
  "risk_score": 0.72,
  "risk_level": "MEDIO",
  "ai_dependency_score": 0.8,
  "ai_dependency_level": "ALTO",
  "risk_factors": {
    "excessive_ai_help": true,
    "low_code_quality": false,
    "high_error_rate": true
  },
  "ai_analysis": {
    "risk_level": "MEDIO",
    "dimension": "Dependencia de IA",
    "evidence": "El estudiante solicita ayuda en cada paso...",
    "recommendation": "Sugerir ejercicios sin IA..."
  }
}
```

#### `GET /api/v3/governance/students/{student_id}`
Obtiene estado de gobernanza/riesgo global del estudiante

---

### 6️⃣ **Catalog** (`/api/v3/catalog`) - Catálogo Académico

#### `GET /api/v3/catalog/subjects`
Lista todas las materias:
- Código, nombre, descripción
- Créditos, semestre
- Solo activas (query param: `active_only=true`)

**Response:**
```json
[
  {
    "id": 1,
    "code": "PROG-101",
    "name": "Introducción a la Programación",
    "description": "Fundamentos de programación",
    "credits": 6,
    "semester": 1,
    "is_active": true
  }
]
```

#### `GET /api/v3/catalog/subjects/{subject_id}/courses`
Lista cursos de una materia específica:
- Año, semestre
- Fechas de inicio/fin

#### `GET /api/v3/catalog/courses/{course_id}/commissions`
Lista comisiones de un curso:
- Código de comisión
- Horario, capacidad
- ID del profesor

---

### 7️⃣ **System** (`/api/v3/system`) - Sistema y Monitoreo

#### `GET /api/v3/system/health/detailed`
Health check detallado con componentes:
- Estado de base de datos
- Estado de Redis
- Disponibilidad de LLM
- Versión de la app

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T...",
  "app_name": "AI-Native MVP V3",
  "version": "3.0.0",
  "debug_mode": true,
  "components": {
    "database": {
      "status": "healthy",
      "type": "PostgreSQL"
    },
    "redis": {
      "status": "configured",
      "url": "redis://localhost:6379/0"
    },
    "llm": {
      "status": "configured",
      "provider": "OpenAI"
    }
  }
}
```

#### `GET /api/v3/system/info`
Información del sistema:
- Nombre y versión
- Arquitectura
- Features habilitadas
- Configuración

#### `GET /api/v3/system/stats`
Estadísticas del sistema:
- Número de usuarios
- Número de sesiones activas
- Número de actividades

---

### 8️⃣ **Endpoints Raíz**

#### `GET /`
Información general del API

#### `GET /health`
Health check básico (solo DB)

#### `GET /metrics`
Métricas de Prometheus para monitoreo

#### `GET /api/v3/docs`
Documentación interactiva Swagger UI

#### `GET /api/v3/redoc`
Documentación ReDoc

#### `GET /api/v3/openapi.json`
Especificación OpenAPI en JSON

---

## 🎯 FUNCIONALIDADES CLAVE

### 🤖 **Inteligencia Artificial**

1. **Tutor Socrático Adaptativo**
   - Preguntas guiadas según nivel cognitivo
   - Detección de frustración en tiempo real
   - Ajuste dinámico de dificultad

2. **Generación de Ejercicios**
   - Ejercicios de programación con casos de prueba
   - Soluciones de referencia
   - Explicaciones pedagógicas

3. **Análisis de Código**
   - Revisión automática de calidad
   - Detección de errores comunes
   - Sugerencias de mejora

4. **Sistema de Gobernanza con IA**
   - Análisis de riesgo académico
   - Detección de dependencia excesiva de IA
   - Recomendaciones personalizadas

### 📊 **Analytics y Monitoreo**

1. **Analytics de Curso**
   - Métricas agregadas por curso
   - Identificación de estudiantes en riesgo
   - Tasas de completitud

2. **Perfiles de Riesgo**
   - Score de riesgo individual
   - Factores de riesgo identificados
   - Score de dependencia de IA

3. **Seguimiento de Sesiones**
   - Historial de interacciones
   - Métricas cognitivas
   - Alertas de intervención

### 🎓 **Gestión Académica**

1. **Actividades de Aprendizaje**
   - Creación y gestión de actividades
   - Políticas de uso de IA configurables
   - Publicación y control de acceso

2. **Catálogo Académico**
   - Materias, cursos y comisiones
   - Estructura organizacional
   - Filtros y búsquedas

3. **Gestión de Documentos**
   - Upload de materiales (PDF, DOCX, MD)
   - Ingesta a RAG
   - Consulta por estudiantes

### 🔐 **Seguridad y Autenticación**

1. **JWT Authentication**
   - Login seguro
   - Tokens de acceso
   - Roles y permisos

2. **Control de Acceso**
   - Estudiantes, profesores, administradores
   - Permisos granulares
   - Sesiones seguras

---

## 📦 ARQUITECTURA

### Clean Architecture + DDD (Domain-Driven Design)

```
┌─────────────────────────────────────────────┐
│         HTTP Layer (FastAPI Routers)        │
│   analytics_router, student_router, etc.    │
└─────────────────┬───────────────────────────┘
                  │ DTOs
┌─────────────────▼───────────────────────────┐
│        Application Layer (Use Cases)        │
│  GetCourseAnalytics, SendMessageToTutor     │
└─────────────────┬───────────────────────────┘
                  │ Domain Entities
┌─────────────────▼───────────────────────────┐
│         Domain Layer (Entities)             │
│  CourseAnalytics, StudentRiskProfile        │
└─────────────────┬───────────────────────────┘
                  │ Interfaces (Ports)
┌─────────────────▼───────────────────────────┐
│    Infrastructure Layer (Repositories)      │
│  SQLAlchemy, LLM Providers, RAG, AI         │
└─────────────────────────────────────────────┘
```

### 🔧 **Tecnologías**

- **Framework**: FastAPI 0.115.6
- **ORM**: SQLAlchemy 2.0.37 (Async)
- **Database**: PostgreSQL + AsyncPG
- **Validación**: Pydantic 2.10.5
- **Auth**: JWT (python-jose)
- **LLMs**: OpenAI, Anthropic, Google Gemini
- **RAG**: LangChain + ChromaDB
- **Embeddings**: Sentence Transformers
- **Monitoring**: Prometheus
- **Testing**: pytest + pytest-asyncio

---

## 🎨 PATRONES DE DISEÑO

1. **Repository Pattern**: Abstracción de acceso a datos
2. **Dependency Injection**: FastAPI Depends()
3. **Use Case Pattern**: Lógica de negocio encapsulada
4. **DTO Pattern**: Separación request/response de domain
5. **Factory Pattern**: Creación de LLM providers
6. **Circuit Breaker**: Resiliencia en llamadas externas
7. **Strategy Pattern**: Múltiples proveedores LLM

---

**Total: 40+ endpoints funcionando** ✅
