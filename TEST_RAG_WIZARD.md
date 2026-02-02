# 🎯 Guía de Prueba: Wizard de Actividades con RA G

## ✅ Estado del Sistema

### Backend
- ✅ Contenedor: `ai_native_backend` corriendo
- ✅ Puerto: 8000
- ✅ MISTRAL_API_KEY configurada: `dIP8G...YM2J`
- ✅ Base de datos: PostgreSQL en puerto 5433
- ✅ Endpoints RAG disponibles:
  - POST `/api/v3/teacher/generator/upload`
  - GET `/api/v3/teacher/generator/{job_id}/status`
  - GET `/api/v3/teacher/generator/{job_id}/draft`

### Frontend
- Port: 3000 (Next.js Dev Server)
- CreateActivityDialog: ✅ Actualizado con validación
- Polling: ✅ Implementado (cada 2 segundos, máx 60s)
- UI: ✅ Feedback visual mejorado

## 🧪 Prueba del Flujo Completo

### Preparación (Solo si el frontend no está corriendo)
```powershell
cd "c:\Users\juani\Desktop\Fase 8\frontend"
npm run dev
```

### Paso 1: Abrir el Wizard
1. Navega a: http://localhost:3000/teacher/dashboard
2. Haz login si es necesario
3. Click en el botón **"Nueva Actividad"**

### Paso 2: Llenar Metadata (Step 1)
```
✏️ Título: Funciones en Python Avanzadas
📚 Tema: Funciones, parámetros y decoradores
🎯 Dificultad: INTERMEDIO
```
4. Click **"Siguiente"**

### Paso 3: Seleccionar PDF (Step 2)

#### Opción A: Crear un PDF de Prueba
```powershell
# Crear un archivo de texto con contenido
@"
Introducción a Funciones en Python

Las funciones son bloques reutilizables de código que realizan tareas específicas.

Sintaxis básica:
def nombre_funcion(parametros):
    # código
    return resultado

Parámetros:
- Posicionales: Se pasan en orden
- Por nombre: param=valor
- Por defecto: def func(x=10)
- *args: Lista variable de argumentos
- **kwargs: Diccionario de argumentos

Decoradores:
Un decorador es una función que modifica el comportamiento de otra función.

Ejemplo:
@decorador
def mi_funcion():
    pass

Ejercicios sugeridos:
1. Crear función que calcule factorial
2. Implementar decorador para medir tiempo de ejecución
3. Función con *args y **kwargs
"@ | Out-File -FilePath "$env:USERPROFILE\Desktop\python_funciones.txt" -Encoding UTF8

# Convertir a PDF (requiere instalación)
# O simplemente sube el .txt como si fuera PDF para testing
```

#### Opción B: Modo Texto (Más Fácil)
1. Click en la tab **"✍️ Texto Manual"**
2. Pega este contenido:
```
Tema: Funciones en Python

Las funciones permiten encapsular lógica reutilizable.

Conceptos clave:
- Definición con def
- Parámetros posicionales y por nombre
- Return values
- Scope de variables
- Decoradores básicos

Ejercicios a generar:
1. Función que valida email
2. Decorador de logging
3. Función recursiva (factorial)
4. Manejo de *args y **kwargs
5. Closures y funciones anidadas
```

### Paso 4: Generar con IA

#### Si usas PDF:
1. Click en el input de archivo
2. Selecciona tu PDF
3. Deberías ver: **✅ Card verde** con nombre del archivo y tamaño
4. El botón debe decir: **"✨ Generar con IA"**
5. Click en el botón

#### Si usas Texto:
1. Pega el contenido
2. El botón debe estar habilitado
3. Click **"✨ Generar con IA"**

### Paso 5: Observar el Proceso

#### Consola del Browser (F12 → Console)
Deberías ver logs similares a:
```
🚀 Starting generation process...
Source type: pdf
PDF file: python_funciones.pdf
✅ Validation passed, moving to step 3
📄 Processing PDF with RAG...
Uploading to /teacher/generator/upload...
✅ Upload response: {job_id: "abc-123", status: "processing"}
🔄 Starting job polling for: abc-123
📊 Job status (attempt 1): ingestion
📊 Job status (attempt 2): generation
📊 Job status (attempt 3): generation
📊 Job status (attempt 4): awaiting_approval
✅ Generation completed!
📝 Creating activity with data: {title: "Funciones...", ...}
✅ Activity created: {id: "xyz-789"}
Closing dialog and refreshing...
```

#### UI del Progress Bar
Verás mensajes rotando:
```
⏳ Analizando contexto...
⏳ Extrayendo conocimiento...
⏳ Diseñando ejercicios...
⏳ Generando casos de prueba...
⏳ Aplicando pedagogía...
⏳ Persistiendo datos...
⏳ ¡Casi listo!
✅ ¡Actividad creada exitosamente!
```

### Paso 6: Verificar Resultado

1. **Toast Verde** aparece: "¡Actividad creada con éxito!"
2. **Wizard se cierra** automáticamente
3. **Tabla se refresca** mostrando la nueva actividad
4. La actividad aparece como **"DRAFT"** (borrador)

## 🐛 Troubleshooting

### Problema 1: Botón Deshabilitado
**Síntoma:** No puedo hacer click en "Generar con IA"

**Solución:**
1. Verifica que esté el card verde con el archivo
2. Si usa texto, verifica que el textarea no esté vacío
3. Si el card no aparece, recarga la página: `Ctrl + Shift + R`

### Problema 2: Error "MISTRAL_API_KEY not configured"
**Síntoma:** Error 503 en la consola

**Solución:**
```powershell
# Verificar que la key esté configurada
docker exec ai_native_backend printenv MISTRAL_API_KEY

# Debe imprimir: dIP8GSbBnLhyGCSOiHvZn96W7CLgYM2J
# Si no, reiniciar:
cd "c:\Users\juani\Desktop\Fase 8"
docker-compose down
docker-compose up -d backend
```

### Problema 3: Polling Nunca Completa
**Síntoma:** Progress bar se queda en "Generando..." por más de 60 segundos

**Causa Probable:** El workflow de LangGraph está fallando

**Solución:**
```powershell
# Ver logs del backend en tiempo real
docker logs -f ai_native_backend

# Buscar errores relacionados con:
# - Mistral API (rate limit, invalid key)
# - ChromaDB (no disponible)
# - PDF processing (archivo corrupto)
```

### Problema 4: Error 404 en `/generator/{job_id}/status`
**Síntoma:** Console muestra "404 Not Found"

**Causa:** El endpoint recién agregado no se cargó

**Solución:**
```powershell
# Reiniciar backend
docker-compose restart backend

# Esperar 10 segundos
Start-Sleep -Seconds 10

# Verificar que esté up
docker ps | findstr backend
```

### Problema 5: Modo Texto No Crea Ejercicios
**Síntoma:** Se crea la actividad pero sin ejercicios

**Comportamiento Esperado:** ✅ Esto es normal por ahora
- El modo texto crea solo el "shell" de la actividad
- Los ejercicios se pueden agregar manualmente después
- Para ejercicios auto-generados, usa el modo PDF

## 📊 Verificación de Éxito

### Checklist Post-Generación
- [ ] Toast verde apareció
- [ ] Wizard se cerró automáticamente
- [ ] Nueva actividad visible en la tabla
- [ ] Estado de actividad: "DRAFT"
- [ ] No hay errores en console
- [ ] Backend logs muestran éxito

### Verificar en Base de Datos
```sql
-- Conectar a la base de datos
docker exec -it ai_native_postgres psql -U postgres -d ai_native

-- Ver última actividad creada
SELECT id, title, subject, difficulty_level, status, created_at 
FROM exercises_v2 
ORDER BY created_at DESC 
LIMIT 5;

-- Debe mostrar tu nueva actividad con status='DRAFT'
```

### Verificar Job en Logs
```powershell
# Buscar el job_id en los logs
docker logs ai_native_backend | Select-String "job_id"

# Debe mostrar el workflow completo:
# - Job created: {job_id}
# - Ingestion complete
# - Generation complete
# - Draft ready
```

## 🎯 Flujo Ideal (Timeline)

```
t=0s   : Click "Generar con IA"
t=1s   : Upload PDF → Backend recibe
t=2s   : LangGraph inicia ingestion
t=5s   : PDF procesado → Texto extraído
t=8s   : ChromaDB embeddings creados
t=10s  : Mistral API consultado (1ra vez)
t=15s  : Generando ejercicio 1/10
t=20s  : Generando ejercicio 5/10
t=25s  : Generando ejercicio 10/10
t=30s  : Draft completo → awaiting_approval
t=31s  : Frontend detecta status="awaiting_approval"
t=32s  : Crea actividad shell en DB
t=33s  : Toast + cierre + refresh
```

**Total:** ~30-35 segundos para un PDF típico

## 🔄 Próximo Test: Ver Ejercicios Generados

Para ver los ejercicios que generó la IA:

```powershell
# Con el job_id de los logs
$jobId = "abc-123-xyz"  # Reemplaza con tu job_id real

# Llamar al endpoint de draft (con curl o Postman)
curl http://localhost:8000/api/v3/teacher/generator/$jobId/draft

# Deberías ver JSON con 10 ejercicios:
{
  "job_id": "abc-123",
  "status": "awaiting_approval",
  "draft_exercises": [
    {
      "title": "Validador de Email con Regex",
      "description": "Implementa una función...",
      "difficulty": "INTERMEDIO",
      "concepts": ["regex", "string", "validation"],
      "mission_markdown": "...",
      "starter_code": "def validate_email(email: str) -> bool:\n    pass",
      "solution_code": "import re\n...",
      "test_cases": [...]
    },
    // ... 9 más
  ]
}
```

## ✅ Éxito Confirmado

Si llegaste aquí y todo funcionó:

1. ✅ Frontend conectado con backend RAG
2. ✅ Upload de PDF funcional
3. ✅ LangGraph workflow ejecutándose
4. ✅ Mistral API generando contenido
5. ✅ ChromaDB almacenando embeddings
6. ✅ Polling de status funcional
7. ✅ Actividad creada en base de datos
8. ✅ UI actualizada automáticamente

**🎉 Sistema RAG completamente integrado y funcional!**

---
**Próximo Paso:** Implementar UI de preview para ver y editar los 10 ejercicios antes de publicar
