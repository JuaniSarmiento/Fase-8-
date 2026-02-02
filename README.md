# AI-Native Learning Platform - Fase 8

## 📚 Descripción del Proyecto

Plataforma educativa avanzada con inteligencia artificial integrada para el aprendizaje de programación. El sistema proporciona tutorías personalizadas, evaluación automática de ejercicios de código y retroalimentación en tiempo real utilizando modelos de lenguaje LLM (Mistral, OpenAI) y técnicas de RAG (Retrieval-Augmented Generation).

### Características Principales

- **Tutorías Interactivas con IA**: Asistente inteligente que guía a los estudiantes usando diferentes modos pedagógicos (Socrático, Directo, Wizard/Asistente)
- **Evaluación Automática de Código**: Análisis de código Python con feedback instantáneo
- **Sistema de Gamificación**: XP, niveles, rachas y logros para motivar el aprendizamiento
- **Gestión de Cursos y Módulos**: Organización jerárquica de contenido educativo
- **RAG con ChromaDB**: Base de conocimiento vectorial para consultas contextuales
- **Autenticación y Roles**: Sistema completo de usuarios (Profesores, Estudiantes, Admins)
- **Dashboard Analítico**: Visualización de progreso y métricas de aprendizaje

---

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico

#### Backend
- **Framework**: FastAPI (Python 3.11)
- **Base de Datos**: PostgreSQL 15
- **ORM**: SQLAlchemy (async)
- **Vector DB**: ChromaDB para embeddings y RAG
- **LLM Providers**: Mistral AI, OpenAI GPT-4
- **Containerización**: Docker & Docker Compose

#### Frontend
- **Framework**: Next.js 16.1.4 (Turbopack)
- **UI Library**: React 18 con TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Animaciones**: Framer Motion

#### Infraestructura
```
┌─────────────────┐
│   Frontend      │
│  Next.js:3000   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend       │
│  FastAPI:8000   │
└────┬───────┬────┘
     │       │
     ▼       ▼
┌─────────┐ ┌──────────┐
│PostgreSQL│ │ChromaDB  │
│  :5433   │ │  :8001   │
└──────────┘ └──────────┘
```

---

## 🚀 Instalación y Configuración

### Requisitos Previos

- **Docker Desktop** (Windows/Mac) o Docker Engine (Linux)
- **Node.js** 18+ y npm/yarn
- **Python** 3.11+
- **Git**
- **PowerShell** (Windows) o Bash (Linux/Mac)

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd "Fase 8"
```

### 2. Configurar Variables de Entorno

#### Backend (`backend/.env`)
```env
# Base de Datos
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ai_native

# Mistral AI (Proveedor LLM Principal)
MISTRAL_API_KEY=your_mistral_api_key_here

# OpenAI (Opcional)
OPENAI_API_KEY=your_openai_api_key_here

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# JWT Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v3
```

### 3. Iniciar Servicios Backend con Docker

```bash
# Iniciar PostgreSQL y ChromaDB
docker-compose up -d

# Verificar que los contenedores estén ejecutándose
docker ps
```

Deberías ver:
- `ai_native_backend` (puerto 8000)
- `ai_native_postgres` (puerto 5433→5432)
- `ai_native_chromadb` (puerto 8001→8000)

### 4. Inicializar Base de Datos

```bash
# Crear tablas y esquema
docker exec ai_native_postgres psql -U postgres -d ai_native -f /docker-entrypoint-initdb.d/init_database.sql

# O usar el script de Python
python init_db.py
```

### 5. Crear Usuario Docente Inicial

```powershell
# Windows PowerShell
python cleanup_and_seed_teacher.py
```

Esto crea el usuario:
- **Email**: `docente@ainative.edu`
- **Password**: `docente123`
- **Usuario**: `docente`

### 6. Iniciar Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend estará disponible en `http://localhost:3000`

---

## 📖 Guía de Uso

### Para Profesores

#### 1. Iniciar Sesión
- Navega a `http://localhost:3000/login`
- Sección "Docente": usuario `docente`, contraseña `docente`
- Serás redirigido a `/teacher/modules`

#### 2. Crear un Curso
```bash
# Via API o directamente en la base de datos
docker exec ai_native_postgres psql -U postgres -d ai_native -c "
INSERT INTO courses (course_id, subject_code, year, semester, created_at)
VALUES (gen_random_uuid()::text, 'PROG1', '2026', '1C', NOW());
"
```

#### 3. Crear un Módulo
- En el dashboard, click en "Crear Módulo"
- Completa: Nombre, Descripción, Curso asociado
- El módulo se crea con `is_published = false`

#### 4. Crear Actividades
```bash
# Ejemplo: Crear actividad en un módulo
docker exec ai_native_postgres psql -U postgres -d ai_native -c "
INSERT INTO activities (activity_id, module_id, title, instructions, status, difficulty_level, order_index)
VALUES (
  gen_random_uuid()::text,
  '<module_id>',
  'Bucles en Python',
  'Implementa un bucle for que imprima números del 1 al 10',
  'active',
  'facil',
  0
);
"
```

#### 5. Publicar Módulo e Inscribir Estudiantes
```sql
-- Publicar módulo
UPDATE modules SET is_published = true WHERE module_id = '<module_id>';

-- Inscribir estudiante
INSERT INTO enrollments (enrollment_id, user_id, course_id, module_id, role, status, enrolled_at)
VALUES (
  gen_random_uuid()::text,
  '<student_id>',
  '<course_id>',
  '<module_id>',
  'STUDENT',
  'ACTIVE',
  NOW()
);
```

### Para Estudiantes

#### 1. Registro
- Navega a `http://localhost:3000/register`
- Completa: Nombre completo, Usuario, Email, Contraseña
- Se crea automáticamente con rol `STUDENT`

#### 2. Iniciar Sesión
- En `/login`, sección "Estudiante"
- Usa tu email (o username@estudiantes.edu) y contraseña
- Serás redirigido a `/student/activities`

#### 3. Ver Actividades
- En "Mis Actividades" verás tus cursos inscritos
- Expande un módulo para ver las actividades disponibles
- Click en "Iniciar" para comenzar una actividad

#### 4. Interactuar con el Tutor IA
- Al iniciar una actividad, se crea una sesión de chat
- **Modo Socrático**: El tutor hace preguntas guía sin dar respuestas directas
- **Modo Directo**: Respuestas más explicativas y directas
- **Modo Wizard**: Asistente paso a paso con ejemplos

#### 5. Escribir y Evaluar Código
- Usa el editor de código integrado
- Click en "Evaluar Código" para obtener feedback automático
- El tutor analizará tu código y sugerirá mejoras

---

## 🗂️ Estructura del Proyecto

```
Fase 8/
├── backend/
│   ├── src_v3/                          # Código fuente principal
│   │   ├── application/                 # Capa de aplicación
│   │   │   ├── auth/                   # Casos de uso de autenticación
│   │   │   ├── schemas/                # Schemas Pydantic
│   │   │   └── tutor/                  # Lógica del tutor IA
│   │   ├── domain/                     # Modelos de dominio
│   │   ├── infrastructure/             # Capa de infraestructura
│   │   │   ├── http/                   # API HTTP (FastAPI)
│   │   │   │   └── api/v3/routers/    # Endpoints REST
│   │   │   ├── llm/                    # Integraciones LLM
│   │   │   │   ├── mistral_provider.py
│   │   │   │   └── openai_provider.py
│   │   │   ├── persistence/            # Repositorios y modelos DB
│   │   │   │   ├── repositories/
│   │   │   │   └── sqlalchemy/models/
│   │   │   └── rag/                    # Sistema RAG con ChromaDB
│   │   └── core/                       # Configuración y utilidades
│   ├── main.py                         # Punto de entrada FastAPI
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/                            # Next.js App Router
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx         # Página de login
│   │   │   └── register/page.tsx      # Página de registro
│   │   ├── student/
│   │   │   ├── activities/            # Vista de actividades
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx     # Actividad específica
│   │   │   └── dashboard/             # Dashboard estudiante
│   │   ├── teacher/
│   │   │   ├── modules/               # Gestión de módulos
│   │   │   └── analytics/             # Analíticas
│   │   └── page.tsx                   # Página raíz (redirect)
│   ├── components/
│   │   ├── ui/                        # shadcn/ui components
│   │   ├── student/                   # Componentes estudiante
│   │   │   ├── chat-interface.tsx
│   │   │   ├── code-editor.tsx
│   │   │   └── gamification-widget.tsx
│   │   └── teacher/                   # Componentes profesor
│   ├── lib/
│   │   ├── api.ts                     # Cliente API Axios
│   │   └── utils.ts
│   ├── store/
│   │   └── auth-store.ts              # Zustand store
│   ├── package.json
│   └── next.config.ts
│
├── docker-compose.yml                  # Configuración Docker
├── init_database.sql                   # Schema SQL inicial
├── cleanup_and_seed_teacher.py         # Script seed profesor
└── README.md                           # Este archivo
```

---

## 🔌 API Endpoints Principales

### Autenticación (`/api/v3/auth`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/auth/login` | Login con email/password |
| POST | `/auth/register` | Registro de nuevo usuario |
| GET | `/auth/me` | Obtener usuario actual |

### Estudiantes (`/api/v3/student`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/student/courses` | Listar cursos con módulos y actividades |
| GET | `/student/gamification` | Obtener estadísticas de gamificación |
| POST | `/student/sessions` | Crear sesión de tutoría |
| POST | `/student/sessions/{id}/chat` | Enviar mensaje al tutor IA |
| POST | `/student/evaluate-code` | Evaluar código Python |

### Profesores (`/api/v3/teacher`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/teacher/modules` | Listar módulos del profesor |
| POST | `/teacher/modules` | Crear nuevo módulo |
| GET | `/teacher/analytics` | Obtener analíticas del curso |
| POST | `/teacher/activities` | Crear actividad |

---

## 🗄️ Esquema de Base de Datos

### Tablas Principales

#### `users`
```sql
- id (VARCHAR 36, PK)
- username (VARCHAR 50, UNIQUE)
- email (VARCHAR 255, UNIQUE)
- hashed_password (TEXT)
- full_name (VARCHAR 255)
- roles (JSONB) -- ["TEACHER"] o ["STUDENT"]
- is_active (BOOLEAN)
- created_at, updated_at (TIMESTAMP)
```

#### `courses`
```sql
- course_id (VARCHAR 36, PK)
- subject_code (VARCHAR 50)
- year (INTEGER)
- semester (VARCHAR 10)
- created_at, updated_at (TIMESTAMP)
```

#### `modules`
```sql
- module_id (VARCHAR 36, PK)
- course_id (VARCHAR 36, FK → courses)
- title (VARCHAR 255)
- description (TEXT)
- order_index (INTEGER)
- is_published (BOOLEAN)
- created_at, updated_at (TIMESTAMP)
```

#### `activities`
```sql
- activity_id (VARCHAR 36, PK)
- module_id (VARCHAR 36, FK → modules)
- title (VARCHAR 255)
- instructions (TEXT)
- status (VARCHAR 50) -- 'active', 'published', 'draft'
- difficulty_level (VARCHAR 50) -- 'facil', 'intermedio', 'dificil'
- order_index (INTEGER)
- created_at, updated_at (TIMESTAMP)
```

#### `enrollments`
```sql
- enrollment_id (VARCHAR 36, PK)
- user_id (VARCHAR 36, FK → users)
- course_id (VARCHAR 36, FK → courses)
- module_id (VARCHAR 36, FK → modules, NULLABLE)
- role (VARCHAR 50) -- 'STUDENT', 'TEACHER'
- status (VARCHAR 50) -- 'ACTIVE', 'INACTIVE'
- enrolled_at (TIMESTAMP)
```

#### `user_gamification`
```sql
- user_id (VARCHAR 36, PK, FK → users)
- xp (INTEGER)
- level (INTEGER)
- streak_days (INTEGER)
- longest_streak (INTEGER)
- achievements (JSONB)
- badges (JSONB)
- total_exercises_completed (INTEGER)
- total_activities_completed (INTEGER)
```

#### `tutor_sessions`
```sql
- session_id (VARCHAR 36, PK)
- student_id (VARCHAR 36, FK → users)
- activity_id (VARCHAR 36, FK → activities)
- mode (VARCHAR 50) -- 'SOCRATIC', 'DIRECT', 'WIZARD'
- created_at, updated_at (TIMESTAMP)
```

#### `chat_messages`
```sql
- message_id (VARCHAR 36, PK)
- session_id (VARCHAR 36, FK → tutor_sessions)
- role (VARCHAR 50) -- 'user', 'assistant', 'system'
- content (TEXT)
- timestamp (TIMESTAMP)
```

---

## 🤖 Sistema de IA y RAG

### Modelos LLM Soportados

1. **Mistral AI** (Predeterminado)
   - Modelo: `mistral-large-latest`
   - Streaming: Sí
   - Mejor para: Razonamiento complejo, tutorías Socráticas

2. **OpenAI GPT-4**
   - Modelo: `gpt-4-turbo-preview`
   - Streaming: Sí
   - Mejor para: Explicaciones detalladas, feedback de código

### RAG (Retrieval-Augmented Generation)

El sistema usa ChromaDB para almacenar y recuperar conocimiento contextual:

```python
# Proceso RAG
1. Ingestión: PDFs → Chunks → Embeddings → ChromaDB
2. Query: Pregunta estudiante → Embedding
3. Retrieval: Top-K documentos similares
4. Augmentation: Contexto + Pregunta → LLM
5. Response: Respuesta contextualizada
```

**Comandos útiles:**

```python
# Agregar documentos al RAG
python backend/scripts/ingest_documents.py --pdf path/to/document.pdf

# Probar consulta RAG
python test_rag_internal.py
```

---

## 🎮 Sistema de Gamificación

### Mecánicas

- **XP (Experience Points)**: Se gana completando ejercicios
- **Niveles**: Cada 100 XP = 1 nivel
- **Rachas**: Días consecutivos de actividad
- **Logros**: Badges por hitos específicos

### Cálculo de XP

```python
# Por ejercicio completado
xp_base = 10
difficulty_multiplier = {
    'facil': 1.0,
    'intermedio': 1.5,
    'dificil': 2.0
}
xp_earned = xp_base * difficulty_multiplier[difficulty]
```

---

## 🔧 Troubleshooting

### El frontend no se conecta al backend

```bash
# Verificar que el backend esté corriendo
curl http://localhost:8000/api/v3/health

# Verificar variables de entorno
echo $NEXT_PUBLIC_API_URL  # Debe ser http://localhost:8000/api/v3
```

### Error 404 en gamificación

El sistema ahora crea automáticamente registros de gamificación. Si persiste:

```sql
-- Crear manualmente
INSERT INTO user_gamification (user_id, xp, level, streak_days, longest_streak, achievements, badges)
VALUES ('<user_id>', 0, 1, 0, 0, '[]'::jsonb, '[]'::jsonb);
```

### No veo módulos en "Mis Actividades"

1. Verificar que el módulo esté publicado:
```sql
UPDATE modules SET is_published = true WHERE module_id = '<module_id>';
```

2. Verificar enrollment del estudiante:
```sql
SELECT * FROM enrollments WHERE user_id = '<student_id>';
```

3. Crear enrollment si no existe:
```sql
INSERT INTO enrollments (enrollment_id, user_id, course_id, module_id, role, status, enrolled_at)
VALUES (gen_random_uuid()::text, '<student_id>', '<course_id>', '<module_id>', 'STUDENT', 'ACTIVE', NOW());
```

### Error al registrar usuario (500)

Verificar que la columna `role` no exista en la tabla `users` (debe ser solo `roles` JSONB):

```sql
\d users  -- Ver estructura de la tabla
```

### ChromaDB no responde

```bash
# Reiniciar ChromaDB
docker restart ai_native_chromadb

# Verificar logs
docker logs ai_native_chromadb
```

### PostgreSQL connection refused

```bash
# Verificar que el puerto esté correcto
docker ps | grep postgres

# Reiniciar PostgreSQL
docker restart ai_native_postgres
```

---

## 📊 Comandos Útiles

### Docker

```bash
# Ver logs del backend
docker logs ai_native_backend -f

# Acceder a la base de datos
docker exec -it ai_native_postgres psql -U postgres -d ai_native

# Reiniciar todos los servicios
docker-compose restart

# Limpiar y reconstruir
docker-compose down -v
docker-compose up --build -d
```

### Base de Datos

```sql
-- Ver todos los usuarios
SELECT id, username, email, roles FROM users;

-- Ver cursos y módulos
SELECT c.subject_code, m.title, m.is_published
FROM courses c
LEFT JOIN modules m ON c.course_id = m.course_id;

-- Ver actividades de un módulo
SELECT title, status, difficulty_level
FROM activities
WHERE module_id = '<module_id>';

-- Ver enrollments de un estudiante
SELECT u.username, c.subject_code, m.title, e.role, e.status
FROM enrollments e
JOIN users u ON e.user_id = u.id
JOIN courses c ON e.course_id = c.course_id
LEFT JOIN modules m ON e.module_id = m.module_id
WHERE u.id = '<student_id>';
```

### Testing

```bash
# Test completo end-to-end
python test_full_conversation_e2e.py

# Test de RAG
python test_rag_internal.py

# Test de login
python test_login.py
```

---

## 🔐 Seguridad

### Autenticación JWT

- Tokens expiran en 30 minutos (configurable)
- Refresh tokens para renovación
- Passwords hasheados con bcrypt

### CORS

Configurado en `backend/.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Para producción, cambiar a dominios reales.

### Variables Sensibles

**NUNCA** commits:
- `MISTRAL_API_KEY`
- `OPENAI_API_KEY`
- `SECRET_KEY`
- Contraseñas de base de datos

Usar `.env` y agregarlo a `.gitignore`.

---

## 🚢 Despliegue a Producción

### Checklist

- [ ] Cambiar `SECRET_KEY` a valor aleatorio seguro
- [ ] Configurar `ALLOWED_ORIGINS` con dominio real
- [ ] Usar PostgreSQL gestionado (AWS RDS, Supabase, etc.)
- [ ] Configurar HTTPS con certificado SSL
- [ ] Variables de entorno en servicio de hosting
- [ ] Configurar ChromaDB persistente
- [ ] Habilitar logging en archivo
- [ ] Configurar backup automático de DB
- [ ] Rate limiting en endpoints de IA
- [ ] Monitoreo con Sentry (opcional, ya configurado)

### Servicios Recomendados

- **Backend**: Railway, Render, Fly.io
- **Frontend**: Vercel, Netlify
- **Database**: Supabase, AWS RDS, DigitalOcean
- **Vector DB**: Pinecone, Weaviate Cloud

---

## 📝 Licencia

Este proyecto es parte de la asignatura de Ingeniería de Software - Universidad.

---

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agrega nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crea un Pull Request

---

## 📧 Contacto y Soporte

Para preguntas, problemas o sugerencias, crear un issue en el repositorio o contactar al equipo de desarrollo.

---

**Última actualización**: Febrero 2, 2026
**Versión**: 3.0.0 (Fase 8)

### Por qué Dataclasses frozen?

- Immutability garantiza integridad de datos
- Facilita reasoning sobre el código
- Evita side effects

### Por qué separar Schemas de Entities?

- Schemas son contratos HTTP (Pydantic)
- Entities son lógica de negocio (Python puro)
- Desacoplamiento permite evolución independiente

---

## 🐛 Troubleshooting

### Error: "Module not found"

```bash
# Asegúrate de estar en el directorio correcto
cd fase8
python main.py
```

### Error: "Connection refused" (PostgreSQL)

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Reiniciar servicios
docker-compose restart postgres
```

### Error: "Table doesn't exist"

```bash
# Inicializar BD
docker-compose exec api python init_db.py
```

---

## 📧 Contacto

Para preguntas sobre la arquitectura o migración, contacta al equipo de desarrollo.

---

**Versión**: 3.0.0  
**Fecha**: Enero 2026  
**Arquitectura**: Clean Architecture + DDD  
**Estado**: ✅ Módulo Analytics Completado
