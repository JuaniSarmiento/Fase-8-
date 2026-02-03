# 🎯 Integración RAG Completa - Wizard de Actividades con IA

## ✅ Cambios Implementados

### 1. Frontend (`create-activity-dialog.tsx`)

#### Validación Mejorada
- ✅ Validación robusta antes de generar
- ✅ Mensajes de error claros y descriptivos
- ✅ Botón deshabilitado cuando falta el archivo PDF
- ✅ Indicador visual del estado del botón

#### UI Mejorada para PDF
```tsx
// Antes: Solo mostraba el nombre del archivo
{pdfFile ? pdfFile.name : 'Arrastra tu PDF...'}

// Ahora: Card visual completo con:
- ✅ Checkmark verde cuando hay archivo
- ⚠️ Warning amarillo cuando falta
- Tamaño del archivo en MB
- Botón para cambiar/eliminar archivo
```

#### Conexión con RAG Real
```typescript
// Conecta con el endpoint real de generación con LangGraph
const formData = new FormData();
formData.append('file', pdfFile!);
formData.append('teacher_id', user?.id || 'demo-teacher');
formData.append('course_id', 'default-course');
formData.append('topic', topic);
formData.append('difficulty', difficulty.toUpperCase());
formData.append('language', 'python');

const response = await api.post('/teacher/generator/upload', formData);
const jobId = response.data.job_id;

// Polling del status hasta completar
await pollJobStatus(jobId);
```

#### Sistema de Polling
```typescript
const pollJobStatus = async (jobId: string, maxAttempts = 30) => {
  // Hace polling cada 2 segundos
  // Máximo 60 segundos (30 intentos)
  // Detecta: completed, awaiting_approval, failed
  // Logs en cada intento para debugging
}
```

### 2. Backend (`teacher_router.py`)

#### Nuevo Endpoint: `/generator/{job_id}/status`
```python
@router.get("/generator/{job_id}/status", response_model=GeneratorJobResponse)
async def get_generation_status(job_id: str):
    """
    Endpoint ligero para polling de status.
    
    Estados posibles:
    - ingestion: Procesando PDF
    - generation: Generando ejercicios con IA
    - awaiting_approval: Draft listo para revisión
    - completed: Publicado
    - failed: Error
    """
```

**Ventajas sobre `/draft`:**
- ⚡ Más rápido (no retorna los ejercicios completos)
- 📊 Perfecto para polling
- 🎯 Solo retorna el estado actual

### 3. Backend AI (`teacher_generator_graph.py`)

#### Nuevo Método: `get_state()`
```python
async def get_state(self, job_id: str) -> Dict[str, Any]:
    """
    Obtiene el estado actual del job (lightweight).
    
    Returns:
        {
            "job_id": str,
            "current_step": str,  # ingestion, generation, etc.
            "draft_ready": bool,
            "published": bool,
            "error": Optional[str]
        }
    """
```

### 4. Docker Compose

#### Variable de Entorno Agregada
```yaml
environment:
  - MISTRAL_API_KEY=${MISTRAL_API_KEY:-}
```

Ya configurada en `.env`:
```bash
MISTRAL_API_KEY=dIP8GSbBnLhyGCSOiHvZn96W7CLgYM2J
```

## 🔄 Flujo Completo End-to-End

### 1. Usuario Sube PDF
```
Frontend → Validación → FormData → Backend
```

### 2. Backend Inicia Workflow LangGraph
```
/generator/upload
  ↓
start_generation()
  ↓
1. INGESTION: Extrae texto del PDF
2. VECTORIZATION: ChromaDB embeddings
3. GENERATION: Mistral + RAG → 10 ejercicios
4. REVIEW: Espera aprobación humana
```

### 3. Frontend Hace Polling
```
Cada 2 segundos:
GET /generator/{job_id}/status
  ↓
Si status === "completed" o "awaiting_approval"
  ↓
Crea actividad shell en la DB
  ↓
Muestra éxito y cierra wizard
```

### 4. Estados del Progress Bar
```
Ingestion:
  "Analizando contexto..."
  "Extrayendo conocimiento..."

Generation:
  "Diseñando ejercicios..."
  "Generando casos de prueba..."
  "Aplicando pedagogía..."

Finalization:
  "Persistiendo datos..."
  "¡Casi listo!"
```

## 🧪 Testing del Flujo

### Test Manual
1. Abre el wizard: Click en "Nueva Actividad"
2. Completa metadata:
   - Título: "Funciones en Python"
   - Tema: "Funciones y parámetros"
   - Dificultad: INTERMEDIO
3. Click "Siguiente"
4. Selecciona un PDF (ej: apuntes de Python)
5. **Verifica UI:**
   - ✅ Card verde aparece con nombre del archivo
   - ✅ Tamaño mostrado en MB
   - ✅ Botón "×" para eliminar
6. Click "Generar con IA"
7. **Observa logs en consola:**
   ```
   🚀 Starting generation process...
   📄 Processing PDF with RAG...
   Uploading to /teacher/generator/upload...
   ✅ Upload response: {job_id: "xxx", status: "processing"}
   🔄 Starting job polling for: xxx
   📊 Job status (attempt 1): processing
   📊 Job status (attempt 2): generation
   📊 Job status (attempt 3): awaiting_approval
   ✅ Generation completed!
   📝 Creating activity with data: {...}
   ✅ Activity created: {id: "yyy"}
   ```
8. **Resultado:**
   - Progress bar 100%
   - Toast verde: "¡Actividad creada con éxito!"
   - Wizard se cierra
   - Tabla se refresca automáticamente

### Test con Text Mode (Fallback)
Si el PDF no funciona inicialmente:
1. Tab "✍️ Texto Manual"
2. Pega texto: "Tema: Funciones en Python. Las funciones..."
3. Click "Generar con IA"
4. Debería crear la actividad directamente

## 🐛 Debugging

### Si el botón está deshabilitado:
- Verifica que el archivo esté seleccionado
- Debe aparecer el card verde con el nombre

### Si el upload falla:
```bash
# Verifica que el backend tiene la API key
docker exec ai_native_backend printenv MISTRAL_API_KEY

# Debe imprimir: dIP8GSbBnLhyGCSOiHvZn96W7CLgYM2J
```

### Si polling nunca completa:
- Revisa logs del backend: `docker logs ai_native_backend`
- Busca errores de Mistral API
- Verifica ChromaDB está disponible

### Console Logs Clave
```
✅ = Success
❌ = Error
🚀 = Start
📄 = PDF processing
📝 = Text processing
🔄 = Polling
📊 = Status update
⏳ = Waiting
```

## 📝 Próximos Pasos (Opcionales)

### 1. Preview de Ejercicios Generados
```typescript
// Después de polling completo:
const draft = await api.get(`/teacher/generator/${jobId}/draft`);
// Mostrar step 3.5: Preview de los 10 ejercicios
// Botones: "Aprobar Todos" | "Editar" | "Rechazar"
```

### 2. Edición de Ejercicios
```
Draft Preview → Select ejercicios → PUT /generator/{job_id}/approve
```

### 3. WebSocket para Progress Real-Time
```typescript
// En lugar de polling, usar WebSocket
const ws = new WebSocket(`ws://localhost:8000/generator/${jobId}/stream`);
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  setProgress(progress.percentage);
  setProgressMessage(progress.message);
};
```

### 4. Historial de Jobs
```
GET /teacher/generator/history
→ Lista de todos los jobs con sus estados
→ Posibilidad de reanudar jobs fallidos
```

## ✅ Checklist de Implementación

- [x] Validación robusta de PDF
- [x] UI mejorada con feedback visual
- [x] Conexión con endpoint RAG real
- [x] Sistema de polling implementado
- [x] Endpoint `/generator/{job_id}/status` creado
- [x] Método `get_state()` agregado a TeacherGeneratorGraph
- [x] MISTRAL_API_KEY agregada a docker-compose
- [x] Logs extensivos para debugging
- [x] Manejo de errores completo
- [ ] Preview de ejercicios generados (opcional)
- [ ] Edición de draft antes de publicar (opcional)
- [ ] WebSocket para progress real-time (opcional)

## 🚀 Para Activar

```bash
# 1. Reiniciar backend para cargar MISTRAL_API_KEY
docker-compose down
docker-compose up -d backend

# 2. Esperar a que esté listo (10 segundos)
docker logs -f ai_native_backend

# 3. Cuando veas "Application startup complete", ya está listo

# 4. Refresca el frontend
# Ctrl + Shift + R en el browser
```

## 📊 Arquitectura Final

```
[Frontend Wizard]
       ↓
   [FormData]
       ↓
POST /teacher/generator/upload
       ↓
[LangGraph Workflow]
       ↓
  ┌─────────────┐
  │  INGESTION  │ ← PDF → Text Chunks
  └─────────────┘
       ↓
  ┌─────────────┐
  │ ChromaDB    │ ← Embeddings
  └─────────────┘
       ↓
  ┌─────────────┐
  │ GENERATION  │ ← Mistral API + RAG
  └─────────────┘
       ↓
  ┌─────────────┐
  │   REVIEW    │ ← Human Checkpoint
  └─────────────┘
       ↓
GET /generator/{job_id}/status (polling)
       ↓
[Frontend Progress Bar]
       ↓
POST /teacher/activities (shell)
       ↓
[Dashboard Refresh]
       ↓
✅ DONE!
```

---
**Status:** ✅ READY TO TEST  
**Próximo paso:** Reiniciar backend y probar con un PDF real
