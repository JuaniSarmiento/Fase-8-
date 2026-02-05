# 📋 PROMPT PARA GEMINI - Informe Detallado del Proyecto

## INSTRUCCIONES PARA USAR ESTE PROMPT

Copia todo el contenido de la sección "PROMPT COMPLETO" y pégalo en Gemini junto con los archivos relevantes del proyecto.

---

## PROMPT COMPLETO PARA GEMINI

```
Necesito que analices este proyecto de plataforma educativa AI-Native y generes un informe exhaustivo y profesional que documente TODAS las funcionalidades implementadas.

# CONTEXTO DEL PROYECTO

Este es un proyecto de plataforma educativa con las siguientes características:
- **Nombre**: AI-Native Learning Platform (Fase 8)
- **Arquitectura**: Clean Architecture + DDD (Domain-Driven Design)
- **Backend**: Python 3.11, FastAPI, PostgreSQL, Redis, ChromaDB
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **IA**: OpenAI GPT-4, ChromaDB para RAG (Retrieval-Augmented Generation)
- **Deployment**: Docker, Docker Compose

# TU TAREA

Genera un documento markdown completo titulado "INFORME_FUNCIONALIDADES_COMPLETO.md" que incluya:

---

## 1. RESUMEN EJECUTIVO (2-3 páginas)

### 1.1 Visión General del Sistema
- Propósito y objetivos de la plataforma
- Arquitectura técnica de alto nivel
- Tecnologías principales utilizadas
- Usuarios objetivo (docentes, estudiantes, administradores)

### 1.2 Métricas del Proyecto
- Número total de endpoints API
- Líneas de código aproximadas (backend/frontend)
- Número de modelos de base de datos
- Número de componentes frontend

### 1.3 Estado Actual
- Funcionalidades completadas
- Nivel de madurez (MVP, Beta, Producción)
- Nivel de documentación
- Cobertura de tests

---

## 2. ARQUITECTURA TÉCNICA DETALLADA (5-7 páginas)

### 2.1 Arquitectura Backend

#### 2.1.1 Clean Architecture
Explica las capas:
- **Domain Layer**: Entidades, value objects, reglas de negocio
- **Application Layer**: Use cases, comandos, DTOs
- **Infrastructure Layer**: Persistencia, HTTP, cache, AI agents
- **Presentation Layer**: Routers, schemas, middleware

#### 2.1.2 Estructura de Directorios
Documenta la estructura completa de `backend/src_v3/`:
```
backend/src_v3/
├── core/
│   ├── domain/
│   ├── security.py
│   └── input_validation.py
├── application/
│   ├── auth/
│   ├── student/
│   └── teacher/
├── infrastructure/
│   ├── http/
│   ├── persistence/
│   ├── ai/
│   └── cache/
```

#### 2.1.3 Base de Datos
- Esquema completo de PostgreSQL
- Tablas principales y relaciones
- Índices implementados
- Migraciones (Alembic si aplica)

#### 2.1.4 Cache Layer (Redis)
- Configuración de Redis
- Estrategias de cache implementadas
- Decoradores @cached y @invalidate_cache
- TTL por tipo de endpoint
- Métricas de performance (hit rate)

#### 2.1.5 Vector Database (ChromaDB)
- Propósito y uso
- Colecciones implementadas
- Estrategia de embeddings
- Integración con OpenAI

### 2.2 Arquitectura Frontend

#### 2.2.1 Next.js App Router
- Estructura de rutas
- Layouts y páginas
- Server vs Client Components
- Routing dinámico

#### 2.2.2 State Management
- Zustand stores implementados
- Estado de autenticación
- Estado global vs local

#### 2.2.3 UI Components
- Biblioteca de componentes (shadcn/ui)
- Componentes custom principales
- Sistema de diseño (Tailwind)

### 2.3 Integración con IA

#### 2.3.1 Agentes IA Implementados
Lista y describe cada agente:
- Socratic Tutor Agent
- Code Review Agent
- Cognitive Trace Agent
- Otros agentes

#### 2.3.2 Flujo de Interacción
- Cómo se inicia una sesión con el tutor
- Procesamiento de mensajes
- Generación de respuestas
- Almacenamiento de conversaciones

---

## 3. FUNCIONALIDADES POR MÓDULO (20-30 páginas)

### 3.1 MÓDULO DE AUTENTICACIÓN

#### 3.1.1 Registro de Usuarios
**Endpoint**: `POST /api/v3/auth/register`

**Descripción completa**:
- Flujo de registro paso a paso
- Validaciones implementadas (username, email, password)
- Requisitos de contraseña (8+ chars, mayúscula, minúscula, dígito)
- Manejo de duplicados (email/username)
- Generación de JWT tokens
- Hashing de contraseñas (bcrypt)

**Request Example**:
```json
{
  "username": "estudiante01",
  "email": "estudiante01@example.com",
  "password": "Password123",
  "full_name": "Juan Pérez",
  "role": "student"
}
```

**Response Example**:
```json
{
  "user": {
    "id": "uuid-here",
    "username": "estudiante01",
    "email": "estudiante01@example.com",
    "full_name": "Juan Pérez",
    "roles": ["STUDENT"],
    "is_active": true
  },
  "tokens": {
    "access_token": "jwt-token-here",
    "refresh_token": "refresh-token-here",
    "token_type": "bearer"
  }
}
```

**Validaciones**:
- Username: 3-30 caracteres, alfanumérico + guiones
- Email: Formato RFC válido
- Password: 8+ caracteres, mayúscula, minúscula, dígito
- Full name: Opcional, 2-255 caracteres

**Manejo de Errores**:
- 409 Conflict: Username o email ya existe
- 400 Bad Request: Validación fallida
- 500 Internal Server Error: Error del servidor

**Logging**:
- Registro exitoso: INFO
- Username duplicado: WARNING
- Validación fallida: WARNING
- Error inesperado: ERROR

#### 3.1.2 Login
**Endpoint**: `POST /api/v3/auth/login`

**Descripción completa**:
[Similar nivel de detalle al punto anterior]

#### 3.1.3 Obtener Usuario Actual
**Endpoint**: `GET /api/v3/auth/me`

#### 3.1.4 Refresh Token
**Endpoint**: `POST /api/v3/auth/refresh`

### 3.2 MÓDULO DE ESTUDIANTES

#### 3.2.1 Dashboard del Estudiante
**Endpoint**: `GET /api/v3/student/dashboard`

**Descripción**:
- Resumen de progreso del estudiante
- Actividades pendientes
- Cursos inscritos
- Estadísticas de gamificación

**Caché**: 60 segundos (Redis)

#### 3.2.2 Listar Actividades Disponibles
**Endpoint**: `GET /api/v3/student/activities/available`

**Descripción**:
- Lista de actividades del estudiante
- Filtros por curso, módulo, estado
- Información de progreso
- Fechas de entrega

**Caché**: 45 segundos

#### 3.2.3 Iniciar Sesión de Aprendizaje
**Endpoint**: `POST /api/v3/student/session/start`

**Descripción completa**:
- Inicia una sesión interactiva con el tutor socrático
- Crea registro en base de datos
- Inicializa el agente de IA
- Establece contexto del ejercicio

**Request**:
```json
{
  "student_id": "uuid",
  "activity_id": "uuid",
  "mode": "SOCRATIC"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "start_time": "2026-02-05T19:30:00Z",
  "is_active": true,
  "cognitive_phase": "EXPLORATION"
}
```

#### 3.2.4 Enviar Mensaje al Tutor
**Endpoint**: `POST /api/v3/student/session/message`

**Descripción**:
- Envía mensaje del estudiante al tutor IA
- Procesamiento con contexto RAG
- Generación de respuesta socrática
- Actualización de cognitive trace
- Almacenamiento en ChromaDB

#### 3.2.5 WebSocket para Chat en Tiempo Real
**Endpoint**: `WS /api/v3/student/session/ws/{session_id}`

**Descripción**:
- Conexión WebSocket persistente
- Chat bidireccional en tiempo real
- Actualizaciones de estado
- Notificaciones de eventos

#### 3.2.6 Enviar Código para Revisión
**Endpoint**: `POST /api/v3/student/code/submit`

**Descripción**:
- Validación de código Python
- Análisis de seguridad
- Ejecución en sandbox
- Feedback del agente revisor

#### 3.2.7 Listar Cursos del Estudiante
**Endpoint**: `GET /api/v3/student/courses`

#### 3.2.8 Gamificación
**Endpoint**: `GET /api/v3/student/gamification`

**Descripción**:
- Puntos acumulados
- Logros desbloqueados
- Racha de días
- Ranking

**Caché**: 30 segundos

### 3.3 MÓDULO DE DOCENTES

#### 3.3.1 Listar Cursos del Docente
**Endpoint**: `GET /api/v3/teacher/courses`

**Caché**: 120 segundos

#### 3.3.2 Crear Módulo
**Endpoint**: `POST /api/v3/teacher/modules`

**Descripción**:
- Creación de módulos de aprendizaje
- Asociación con cursos
- Ordenamiento
- Prerrequisitos

#### 3.3.3 Crear Actividad
**Endpoint**: `POST /api/v3/teacher/activities`

**Descripción completa**:
- Tipos de actividad: ejercicio, proyecto, quiz
- Configuración de dificultad
- Descripción y requisitos
- Código starter
- Tests automáticos
- Criterios de evaluación

#### 3.3.4 Listar Actividades
**Endpoint**: `GET /api/v3/teacher/activities`

**Caché**: 45 segundos

#### 3.3.5 Detalle de Actividad
**Endpoint**: `GET /api/v3/teacher/activities/{id}`

**Caché**: 60 segundos

#### 3.3.6 Ver Estudiantes
**Endpoint**: `GET /api/v3/teacher/available_students`

**Caché**: 60 segundos

#### 3.3.7 Ver Módulos
**Endpoint**: `GET /api/v3/teacher/modules`

**Caché**: 90 segundos

### 3.4 MÓDULO DE ANALYTICS

#### 3.4.1 Estadísticas del Sistema
**Endpoint**: `GET /api/v3/system/stats`

**Descripción**:
- Total de usuarios
- Total de sesiones
- Sesiones hoy
- Intentos de ejercicios

**Caché**: 30 segundos

#### 3.4.2 Analytics por Curso
**Endpoint**: `GET /api/v3/analytics/courses/{id}`

**Descripción**:
- Tasa de completación
- Tiempo promedio
- Estudiantes activos
- Actividades completadas

**Caché**: 60 segundos

#### 3.4.3 Perfil de Riesgo del Estudiante
**Endpoint**: `GET /api/v3/analytics/students/{id}`

**Descripción**:
- Análisis de riesgo de abandono
- Patrones de comportamiento
- Recomendaciones de intervención

**Caché**: 45 segundos

#### 3.4.4 Analytics de Actividades
**Endpoint**: `GET /api/v3/analytics/activities/{id}/submissions_analytics`

#### 3.4.5 Trazabilidad del Estudiante
**Endpoint**: `GET /api/v3/analytics/students/{id}/traceability`

**Descripción**:
- Historial completo de interacciones
- Progresión por fase cognitiva
- Métricas temporales
- Gráficos de evolución

### 3.5 MÓDULO DE CATÁLOGO

#### 3.5.1 Listar Cursos
**Endpoint**: `GET /api/v3/catalog/courses`

#### 3.5.2 Detalle de Curso
**Endpoint**: `GET /api/v3/catalog/courses/{id}`

#### 3.5.3 Módulos de un Curso
**Endpoint**: `GET /api/v3/catalog/courses/{id}/modules`

### 3.6 MÓDULO DE INSCRIPCIONES

#### 3.6.1 Inscribir Estudiante
**Endpoint**: `POST /api/v3/enrollments`

#### 3.6.2 Listar Inscripciones
**Endpoint**: `GET /api/v3/enrollments`

#### 3.6.3 Actualizar Estado de Inscripción
**Endpoint**: `PUT /api/v3/enrollments/{id}/status`

### 3.7 MÓDULO DE GOBERNANZA

#### 3.7.1 Validar Ejercicio
**Endpoint**: `POST /api/v3/governance/validate_exercise`

**Descripción**:
- Validación de estructura de ejercicios
- Verificación de tests
- Validación de código starter

### 3.8 MÓDULO DE ADMINISTRACIÓN

#### 3.8.1 Gestión de Usuarios
**Endpoint**: `GET /api/v3/admin/users`

#### 3.8.2 Gestión de Roles
**Endpoint**: `PUT /api/v3/admin/users/{id}/roles`

### 3.9 MÓDULO DE NOTIFICACIONES

#### 3.9.1 Enviar Notificación
**Endpoint**: `POST /api/v3/notifications`

#### 3.9.2 Listar Notificaciones
**Endpoint**: `GET /api/v3/notifications`

#### 3.9.3 Marcar como Leída
**Endpoint**: `PUT /api/v3/notifications/{id}/read`

---

## 4. FUNCIONALIDADES FRONTEND (10-15 páginas)

### 4.1 PÁGINAS PÚBLICAS

#### 4.1.1 Landing Page
**Ruta**: `/`

**Descripción**:
- Hero section
- Features
- Call to action
- Redirección automática si está autenticado

#### 4.1.2 Página de Login
**Ruta**: `/login`

**Características**:
- Diseño de dos columnas (docente/estudiante)
- Validación de formulario
- Rate limiting del lado del cliente
- Manejo de errores específicos
- Redirección según rol

#### 4.1.3 Página de Registro
**Ruta**: `/register`

**Características**:
- Formulario completo
- Validación en tiempo real
- Feedback visual
- Manejo de errores por status code
- Mensajes contextuales

### 4.2 DASHBOARD ESTUDIANTE

#### 4.2.1 Vista Principal
**Ruta**: `/student/dashboard`

**Componentes**:
- Resumen de progreso
- Actividades pendientes
- Estadísticas de gamificación
- Gráficos de evolución

#### 4.2.2 Listado de Actividades
**Ruta**: `/student/activities`

**Características**:
- Lista de actividades disponibles
- Filtros y búsqueda
- Indicadores de progreso
- Botones de acción

#### 4.2.3 Interfaz de Sesión Interactiva
**Ruta**: `/student/activities/[id]`

**Características**:
- Editor de código (Monaco Editor)
- Chat en tiempo real con tutor
- Resaltado de sintaxis
- Ejecución de código
- Historial de mensajes
- Panel de instrucciones

### 4.3 DASHBOARD DOCENTE

#### 4.3.1 Gestión de Módulos
**Ruta**: `/teacher/modules`

**Características**:
- Lista de cursos y módulos
- Creación/edición de módulos
- Ordenamiento drag-and-drop
- Vista de árbol jerárquica

#### 4.3.2 Gestión de Actividades
**Ruta**: `/teacher/activities`

**Características**:
- CRUD completo de actividades
- Editor de código para starter code
- Configuración de tests
- Preview de actividad

#### 4.3.3 Vista de Estudiantes
**Ruta**: `/teacher/students`

**Características**:
- Lista de estudiantes inscritos
- Métricas de progreso
- Filtros por curso/módulo
- Acceso a analytics individuales

---

## 5. CARACTERÍSTICAS TÉCNICAS AVANZADAS (8-10 páginas)

### 5.1 Sistema de Cache (Redis)

#### 5.1.1 Configuración
- URL de conexión
- Pool de conexiones (50 max)
- Timeout (5s)
- Persistencia (AOF + RDB)

#### 5.1.2 Estrategias de Cache
**Decorador @cached**:
```python
@cached(ttl=60, key_prefix="endpoint_name")
async def my_endpoint(request: Request, ...):
    pass
```

**TTL por tipo de endpoint**:
- Sistema: 30s
- Cursos: 120s
- Estudiantes: 60s
- Actividades: 45s
- Gamificación: 30s

#### 5.1.3 Invalidación de Cache
**Decorador @invalidate_cache**:
```python
@invalidate_cache(pattern="student:*")
async def update_student(...):
    pass
```

#### 5.1.4 Métricas de Performance
- Hit rate actual: 38.46%
- Memoria usada: 1.09M
- Comandos procesados: 183
- Keyspace hits: 5
- Keyspace misses: 8

### 5.2 Seguridad

#### 5.2.1 Rate Limiting
**Configuración**:
- Autenticación: 5 req/min
- API general: 100 req/min
- Health checks: Sin límite

**Implementación**:
- Middleware custom
- Sliding window algorithm
- Headers informativos

#### 5.2.2 Security Headers
**Headers implementados**:
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy
- Permissions-Policy
- Strict-Transport-Security (producción)

#### 5.2.3 Validación de Entrada
**Validaciones implementadas**:
- Username: Regex, longitud
- Email: Formato RFC
- Password: Fortaleza
- UUID: Formato válido
- Filename: Path traversal prevention
- SQL Identifier: Sanitización

#### 5.2.4 Protección contra Ataques
- SQL Injection: Queries parametrizadas
- XSS: HTML escaping
- CSRF: Tokens (pendiente)
- Command Injection: Sanitización
- Path Traversal: Validación de paths

### 5.3 Logging y Monitoreo

#### 5.3.1 Sistema de Logging
**Archivos de log**:
- application.log: Todos los logs
- errors.log: Solo errores
- security.log: Eventos de auth/security

**Formatos**:
- Desarrollo: Texto coloreado
- Producción: JSON estructurado

**Rotación**:
- Tamaño máximo: 10MB
- Backups: 10 archivos

#### 5.3.2 Métricas Implementadas
**Sistema**:
- Uptime
- CPU usage
- Memoria
- Disk I/O

**Aplicación**:
- Request/response time
- Error rate
- Cache hit rate
- Database queries

**Negocio**:
- Usuarios activos
- Sesiones completadas
- Actividades enviadas
- Tasa de completación

### 5.4 Agentes de IA

#### 5.4.1 Socratic Tutor Agent
**Propósito**: Guiar al estudiante con preguntas socráticas

**Características**:
- Contexto de ejercicio desde ChromaDB
- Historial de conversación
- Fases cognitivas (Exploración, Comprensión, Aplicación, Reflexión)
- Generación de hints sin dar respuestas directas
- Evaluación de progreso

**Prompts**:
[Incluir ejemplo de prompt usado]

#### 5.4.2 Code Review Agent
**Propósito**: Revisar y dar feedback sobre código

**Características**:
- Análisis de sintaxis
- Evaluación de buenas prácticas
- Detección de errores comunes
- Sugerencias de mejora
- Verificación de tests

#### 5.4.3 Cognitive Trace Agent
**Propósito**: Rastrear progreso cognitivo

**Características**:
- Identificación de fase cognitiva
- Detección de misconceptions
- Patrones de aprendizaje
- Recomendaciones personalizadas

### 5.5 RAG (Retrieval-Augmented Generation)

#### 5.5.1 ChromaDB Integration
**Colecciones**:
- exercise_contexts: Contexto de ejercicios
- course_materials: Material de cursos
- student_submissions: Submissions históricas

**Embeddings**:
- Modelo: text-embedding-ada-002
- Dimensiones: 1536
- Provedor: OpenAI

#### 5.5.2 Flujo de RAG
1. Query del usuario
2. Embedding del query
3. Búsqueda de similitud en ChromaDB
4. Recuperación de top-k documentos
5. Construcción de contexto
6. Envío a GPT-4
7. Respuesta generada

---

## 6. MODELOS DE BASE DE DATOS (8-10 páginas)

Para cada tabla, documenta:

### 6.1 Tabla: users
**Descripción**: Almacena usuarios del sistema

**Columnas**:
| Columna | Tipo | Nullable | Default | Descripción |
|---------|------|----------|---------|-------------|
| id | VARCHAR(36) | NO | UUID | Primary key |
| username | VARCHAR(100) | NO | - | Username único |
| email | VARCHAR(255) | NO | - | Email único |
| hashed_password | VARCHAR(255) | NO | - | Password hasheado con bcrypt |
| full_name | VARCHAR(255) | YES | NULL | Nombre completo |
| roles | JSONB | NO | [] | Array de roles |
| is_active | BOOLEAN | NO | TRUE | Usuario activo |
| is_verified | BOOLEAN | NO | FALSE | Email verificado |
| last_login | TIMESTAMP | YES | NULL | Último login |
| login_count | INTEGER | NO | 0 | Contador de logins |
| created_at | TIMESTAMP | NO | NOW() | Fecha de creación |
| updated_at | TIMESTAMP | NO | NOW() | Fecha de actualización |

**Índices**:
- PRIMARY KEY (id)
- UNIQUE INDEX (username)
- UNIQUE INDEX (email)
- INDEX (roles) USING GIN

**Relaciones**:
- ONE-TO-MANY con sessions_v2
- ONE-TO-MANY con enrollments
- ONE-TO-MANY con user_gamification

### [Repetir para todas las tablas principales]

### Tablas documentadas:
- users
- sessions_v2
- exercise_attempts_v2
- cognitive_traces_v2
- courses
- modules
- activities
- exercises
- enrollments
- user_gamification
- risks
- notifications

---

## 7. COMPONENTES FRONTEND (8-10 páginas)

### 7.1 Componentes de UI (shadcn/ui)
Lista todos los componentes utilizados:
- Button
- Card
- Input
- Label
- Select
- Dialog
- Toaster
- etc.

### 7.2 Componentes Custom

#### 7.2.1 CodeEditor
**Ubicación**: `components/code-editor.tsx`

**Props**:
```typescript
interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  theme?: string;
  readOnly?: boolean;
}
```

**Características**:
- Monaco Editor
- Syntax highlighting
- Autocompletado
- Múltiples lenguajes

#### 7.2.2 ChatInterface
**Ubicación**: `components/chat-interface.tsx`

**Características**:
- Mensajes en tiempo real
- Auto-scroll
- Formato de código en mensajes
- Indicador de escritura

#### [Documentar todos los componentes custom]

---

## 8. FLUJOS DE USUARIO COMPLETOS (10-12 páginas)

### 8.1 Flujo: Registro e Inicio de Sesión

#### Paso 1: Usuario visita la plataforma
- Landing page en `/`
- Call-to-action "Registrarse"

#### Paso 2: Proceso de registro
1. Usuario hace clic en "Registrarse"
2. Navega a `/register`
3. Completa formulario
4. Frontend valida con Zod
5. POST a `/api/v3/auth/register`
6. Backend valida (username, email, password)
7. Verifica duplicados en BD
8. Hashea password con bcrypt
9. Crea usuario en tabla `users`
10. Genera JWT tokens
11. Retorna user + tokens
12. Frontend guarda en localStorage
13. Redirige según rol

#### Paso 3: Login subsecuente
[Documentar paso a paso]

### 8.2 Flujo: Estudiante Resuelve un Ejercicio

#### Paso 1: Acceso al ejercicio
[Documentar paso a paso desde dashboard hasta iniciar sesión]

#### Paso 2: Interacción con el tutor
[Documentar intercambio de mensajes]

#### Paso 3: Envío de código
[Documentar revisión y feedback]

#### Paso 4: Completación
[Documentar actualización de progreso]

### 8.3 Flujo: Docente Crea una Actividad
[Documentar paso a paso]

### 8.4 Flujo: Analytics y Reporting
[Documentar generación de reportes]

---

## 9. TESTING Y CALIDAD (5-7 páginas)

### 9.1 Tests Backend
- Unit tests
- Integration tests
- Cobertura actual

### 9.2 Tests Frontend
- Component tests
- E2E tests con Playwright
- Cobertura actual

### 9.3 Validación de Datos
- Esquemas Pydantic
- Zod schemas en frontend

### 9.4 Manejo de Errores
- Try-catch blocks
- Error boundaries en React
- Logging de errores

---

## 10. DEPLOYMENT Y DEVOPS (5-7 páginas)

### 10.1 Docker Configuration
- Dockerfile backend
- Dockerfile frontend
- docker-compose.yml
- docker-compose.production.yml

### 10.2 Variables de Entorno
[Listar todas las variables requeridas]

### 10.3 CI/CD (si aplica)
[Documentar pipeline]

### 10.4 Monitoreo en Producción
[Documentar herramientas y dashboards]

---

## 11. DOCUMENTACIÓN TÉCNICA EXISTENTE (2-3 páginas)

Lista y resume todos los documentos README y guías:
- README.md principal
- REDIS_INTEGRATION.md
- PRODUCTION_DEPLOYMENT.md
- PRODUCTION_CHECKLIST.md
- PRODUCTION_IMPROVEMENTS.md
- E2E_TESTING_GUIDE.md
- Otros documentos

---

## 12. ROADMAP Y PRÓXIMOS PASOS (3-4 páginas)

### 12.1 Funcionalidades Planificadas
- Features en desarrollo
- Features en backlog

### 12.2 Mejoras Técnicas
- Optimizaciones pendientes
- Refactoring necesario
- Deuda técnica

### 12.3 Prioridades
- Crítico
- Alto
- Medio
- Bajo

---

## 13. CONCLUSIONES (2 páginas)

### 13.1 Fortalezas del Sistema
[Lista de puntos fuertes]

### 13.2 Áreas de Mejora
[Lista de mejoras potenciales]

### 13.3 Recomendaciones
[Recomendaciones para el futuro]

---

# FORMATO DEL INFORME

- **Usa markdown** con headers, listas, tablas, code blocks
- **Incluye diagramas** en mermaid cuando sea apropiado
- **Usa emojis** para secciones principales
- **Code snippets** con syntax highlighting
- **Tablas** para datos estructurados
- **Ejemplos reales** de requests/responses
- **Screenshots** o descripciones visuales cuando sea relevante

# CRITERIOS DE CALIDAD

El informe debe ser:
1. **Exhaustivo**: Cubrir TODAS las funcionalidades
2. **Preciso**: Basarse en el código real
3. **Detallado**: Explicar el "cómo" y el "por qué"
4. **Técnico pero legible**: Balancear detalle técnico con claridad
5. **Estructurado**: Fácil de navegar con TOC
6. **Actualizado**: Reflejar el estado actual del proyecto
7. **Profesional**: Listo para presentar a stakeholders

# ARCHIVOS A ANALIZAR

Revisa especialmente:
- `backend/src_v3/` (toda la estructura)
- `frontend/app/` (todas las páginas)
- `frontend/components/` (todos los componentes)
- `docker-compose.yml`
- `README.md`
- Archivos de documentación en `docs/`
- Archivos de configuración (.env.example)

---

# OUTPUT ESPERADO

Un archivo markdown de 100-150 páginas con:
- Tabla de contenidos al inicio
- Todas las secciones solicitadas
- Código de ejemplo donde aplique
- Diagramas en mermaid
- Formato profesional

¿Estás listo para generar este informe completo?
```

---

## TIPS PARA USAR ESTE PROMPT CON GEMINI

1. **Sube los archivos clave**:
   - Toda la carpeta `backend/src_v3/`
   - Toda la carpeta `frontend/app/`
   - `README.md`
   - Archivos de documentación
   - `docker-compose.yml`

2. **Divide en secciones** si Gemini tiene límite de tokens:
   - Primera parte: Secciones 1-6
   - Segunda parte: Secciones 7-13

3. **Pide refinamientos**:
   - "Amplía la sección de arquitectura técnica"
   - "Agrega más detalles sobre los agentes de IA"
   - "Incluye diagramas mermaid para los flujos"

4. **Verifica y corrige**:
   - Revisa que los endpoints sean correctos
   - Verifica que los nombres de archivos sean exactos
   - Confirma que las funcionalidades descritas existan

5. **Personaliza**:
   - Ajusta el nivel de detalle según tu audiencia
   - Agrega o quita secciones según necesites
   - Incluye métricas específicas de tu proyecto
