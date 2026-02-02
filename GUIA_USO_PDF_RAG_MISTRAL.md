# 🚀 Guía de Uso: Sistema PDF → RAG → Mistral

**Fecha:** 27 de enero, 2026  
**Estado:** ✅ Sistema Completamente Funcional

---

## 📋 Resumen de Cambios

### ✅ Cambios Implementados

1. **ChromaDB agregado a Docker**
   - Nuevo contenedor: `ai_native_chromadb`
   - Puerto: `8001` (mapeado a 8000 interno)
   - Volumen persistente: `chroma_data`
   - Variables de entorno configuradas en backend

2. **Backend actualizado**
   - Variables de entorno para ChromaDB añadidas
   - Conexión a ChromaDB en red Docker
   - Volumen para uploads persistente

3. **Frontend verificado**
   - Componente existente: `create-activity-dialog.tsx`
   - Flujo completo de PDF implementado
   - Interfaz con tabs (PDF/Texto)

---

## 🎯 Cómo Usar el Sistema (Paso a Paso)

### 1. Iniciar Servicios

```bash
# Desde la carpeta raíz del proyecto
cd "C:\Users\juani\Desktop\Fase 8"

# Levantar todos los contenedores
docker-compose up -d

# Verificar que estén corriendo
docker ps
```

Deberías ver 3 contenedores:
- ✅ `ai_native_postgres` (Puerto 5433)
- ✅ `ai_native_chromadb` (Puerto 8001)
- ✅ `ai_native_backend` (Puerto 8000)

### 2. Iniciar Frontend

```bash
# En otra terminal
cd frontend
npm run dev
```

El frontend estará disponible en: **http://localhost:3000**

---

## 👨‍🏫 Para Profesores: Crear Actividad con PDF

### Paso 1: Acceder al Dashboard

1. Abre tu navegador en: **http://localhost:3000**
2. Inicia sesión como profesor
3. Ve al Dashboard de Profesor

### Paso 2: Crear Nueva Actividad

1. Click en el botón **"+ Nueva Actividad"** (o similar)
2. Se abrirá un diálogo con 3 pasos:

#### 📝 Paso 1: Metadatos Básicos

Completa los siguientes campos:
- **Título**: Nombre de la actividad (ej. "Listas en Python")
- **Tema Principal**: Tema específico (ej. "List Comprehensions")
- **Dificultad**: Selecciona entre:
  - `FACIL` - Para principiantes
  - `INTERMEDIO` - Nivel medio
  - `DIFICIL` - Avanzado

Click **"Siguiente"** →

#### 📄 Paso 2: Subir Material

**Opción A: Subir PDF** (Recomendado)

1. Selecciona la tab **"Subir PDF"**
2. Click en el botón **"Click para seleccionar"**
3. Selecciona tu archivo PDF:
   - ✅ Formato: `.pdf`
   - ✅ Tamaño máximo: 10MB
   - ✅ Contenido: Material de curso, apuntes, slides, etc.
4. Verás el archivo seleccionado con su tamaño

**Opción B: Texto Manual**

1. Selecciona la tab **"Texto Manual"**
2. Escribe o pega el contenido del curso
3. Usa este método si no tienes un PDF

Click **"Generar con IA"** →

#### ⚡ Paso 3: Generación con IA

El sistema ejecutará automáticamente:

```
1. 📤 Subiendo PDF al servidor...
2. 📖 Extrayendo texto del PDF...
3. 🔪 Dividiendo en chunks inteligentes...
4. 🧠 Vectorizando en ChromaDB...
5. 🔍 Analizando contexto con RAG...
6. 🤖 Generando ejercicios con Mistral AI...
7. ✅ ¡Actividad creada!
```

Verás una barra de progreso con mensajes informativos.

### Paso 3: Ver Actividad Creada

1. La actividad aparecerá en tu dashboard
2. Estado inicial: **DRAFT** (Borrador)
3. Puedes:
   - ✏️ **Editar** los ejercicios generados
   - 👁️ **Previsualizar** la actividad
   - 🚀 **Publicar** cuando esté lista
   - 🗑️ **Eliminar** si no te satisface

---

## 🔬 ¿Qué Hace el Sistema Internamente?

### Flujo Técnico del Procesamiento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. FRONTEND: Usuario sube PDF                              │
│    POST /api/v3/teacher/generator/upload                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. BACKEND: Guarda PDF en /app/uploads/generator_pdfs/     │
│    Crea Job ID único (UUID)                                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. EXTRACCIÓN: PyPDF2 extrae texto del PDF                 │
│    - Lee página por página                                  │
│    - Limpia y formatea el texto                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CHUNKING: Divide texto en fragmentos                    │
│    - Tamaño: ~500 caracteres por chunk                      │
│    - Overlap: 100 caracteres entre chunks                   │
│    - Preserva contexto entre fragmentos                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. VECTORIZACIÓN: ChromaDB crea embeddings                 │
│    - Convierte texto a vectores numéricos                   │
│    - Guarda en base de datos vectorial                      │
│    - Permite búsqueda semántica                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. BÚSQUEDA RAG: Encuentra fragmentos relevantes           │
│    Query: "topic + language + conceptos"                    │
│    Returns: Top 10 fragmentos más relevantes                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. GENERACIÓN MISTRAL: IA crea ejercicios                  │
│    Input: Contexto RAG + Requirements                       │
│    Model: mistral-small-latest                              │
│    Output: 10 ejercicios en JSON                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. PERSISTENCIA: Guarda en PostgreSQL                      │
│    - Actividad creada con metadata                          │
│    - Ejercicios vinculados                                  │
│    - Estado: DRAFT (Borrador)                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
           ✅ ¡Completado!
```

---

## 🐛 Troubleshooting (Solución de Problemas)

### Problema: "ChromaDB no conecta"

**Síntomas:**
```
ValueError: Could not connect to a Chroma server
```

**Solución:**
```bash
# Verificar que ChromaDB esté corriendo
docker ps | grep chromadb

# Si no está, reiniciar
docker-compose restart chromadb

# Verificar logs
docker logs ai_native_chromadb
```

---

### Problema: "Backend no responde"

**Síntomas:**
- Frontend muestra "Error 500" o "Connection refused"
- Toast con mensaje de error

**Solución:**
```bash
# Verificar que backend esté corriendo
docker ps | grep backend

# Ver logs del backend
docker logs ai_native_backend --tail 50

# Reiniciar si es necesario
docker-compose restart backend
```

---

### Problema: "PDF no se sube"

**Síntomas:**
- Botón de generar no responde
- Error "No file selected"

**Solución:**
1. Verifica que el archivo sea un PDF válido
2. Tamaño máximo: 10MB
3. Abre la consola del navegador (F12) y busca errores
4. Verifica que el archivo esté realmente seleccionado antes de generar

---

### Problema: "Mistral API Error"

**Síntomas:**
```
Error 500: MISTRAL_API_KEY not configured
```

**Solución:**
```bash
# Verificar que la API key esté en .env
cat .env | grep MISTRAL_API_KEY

# Si no está, agregarla
echo "MISTRAL_API_KEY=tu_api_key_aqui" >> .env

# Reiniciar backend
docker-compose restart backend
```

---

### Problema: "Generación muy lenta"

**Causas posibles:**
- PDF muy grande (>50 páginas)
- Muchos chunks generados
- API de Mistral saturada

**Solución:**
- El sistema está optimizado para PDFs de hasta 10MB
- El proceso puede tomar 30-60 segundos (es normal)
- Si tarda más de 2 minutos, revisar logs

---

## 📊 Monitoreo del Sistema

### Ver Logs en Tiempo Real

```bash
# Backend
docker logs -f ai_native_backend

# ChromaDB
docker logs -f ai_native_chromadb

# Postgres
docker logs -f ai_native_postgres
```

### Ver Estado de Contenedores

```bash
docker ps
docker stats
```

### Inspeccionar ChromaDB

```bash
# Ver colecciones creadas
docker exec ai_native_chromadb ls -la /chroma/chroma

# Ver tamaño de la base de datos
docker exec ai_native_chromadb du -sh /chroma/chroma
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno Importantes

En `docker-compose.yml`, el backend tiene estas configuraciones:

```yaml
# ChromaDB
- CHROMA_HOST=chromadb          # Nombre del contenedor
- CHROMA_PORT=8000              # Puerto interno
- CHROMA_COLLECTION_NAME=ai_native_rag  # Nombre de la colección

# Mistral AI
- MISTRAL_API_KEY=${MISTRAL_API_KEY:-}  # Desde .env

# Uploads
- UPLOADS_DIR=/app/uploads      # Donde se guardan los PDFs
```

### Ajustar Parámetros de RAG

En `backend/src_v3/infrastructure/ai/rag/pdf_processor.py`:

```python
# Modificar tamaño de chunks
chunks = pdf_processor.chunk_text(
    text, 
    chunk_size=500,    # ← Ajustar aquí (default: 500)
    overlap=100        # ← Ajustar overlap (default: 100)
)
```

### Cambiar Modelo de Mistral

En `backend/src_v3/infrastructure/ai/teacher_generator_graph.py`:

```python
self.llm = ChatMistralAI(
    model="mistral-small-latest",  # ← Cambiar modelo aquí
    temperature=0.7,               # ← Ajustar creatividad
    mistral_api_key=self.mistral_api_key
)
```

Modelos disponibles:
- `mistral-small-latest` - Rápido y eficiente (recomendado)
- `mistral-medium-latest` - Más potente
- `mistral-large-latest` - Máxima calidad

---

## 📈 Mejoras Futuras Sugeridas

### Corto Plazo
- [ ] Caché de embeddings para PDFs repetidos
- [ ] Preview del PDF antes de procesar
- [ ] Validación más estricta de contenido PDF
- [ ] Barra de progreso real (no simulada)

### Mediano Plazo
- [ ] Soporte para más formatos (DOCX, TXT, MD)
- [ ] Edición de ejercicios antes de guardar
- [ ] Sistema de calificación de calidad
- [ ] Reintento automático en caso de error

### Largo Plazo
- [ ] Múltiples idiomas de programación
- [ ] Generación de tests unitarios automáticos
- [ ] Análisis de dificultad real
- [ ] Sistema de feedback del estudiante

---

## 📞 Contacto y Soporte

Si encuentras problemas no cubiertos en esta guía:

1. **Revisa los logs** con los comandos de arriba
2. **Abre la consola del navegador** (F12) para errores frontend
3. **Verifica las conexiones** entre contenedores
4. **Consulta los archivos de test** creados:
   - `test_pdf_rag_mistral.py` - Test HTTP completo
   - `test_rag_internal.py` - Test interno detallado

---

## ✅ Checklist de Verificación Rápida

Antes de reportar un problema, verifica:

- [ ] Docker Desktop está corriendo
- [ ] Los 3 contenedores están UP (`docker ps`)
- [ ] Backend responde en http://localhost:8000/api/v3/docs
- [ ] ChromaDB está en puerto 8001
- [ ] Frontend corriendo en http://localhost:3000
- [ ] Archivo .env tiene MISTRAL_API_KEY
- [ ] Usuario logueado como profesor
- [ ] PDF es válido y < 10MB

---

**¡El sistema está listo para usar! 🚀**

Sube tu primer PDF y deja que la IA genere ejercicios personalizados para tus estudiantes.
