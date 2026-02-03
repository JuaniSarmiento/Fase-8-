# 🚀 Guía de Inicio Rápido - Panel de Estudiantes

## Instalación de Dependencias

### Frontend
```bash
cd frontend
npm install
```

Las siguientes dependencias son necesarias (ya incluidas en package.json):
- `@monaco-editor/react` - Editor de código
- `@radix-ui/react-scroll-area` - Componente de scroll
- `@radix-ui/react-separator` - Separadores
- `react-markdown` - Renderizado de Markdown
- `react-syntax-highlighter` - Syntax highlighting
- `@types/react-syntax-highlighter` - TypeScript types

## Iniciar el Sistema

### 1. Iniciar el Backend
```bash
cd backend
python -m uvicorn src_v3.main:app --reload
```

El backend estará disponible en: `http://localhost:8000`

### 2. Iniciar el Frontend
```bash
cd frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:3000`

## Credenciales de Prueba

### Estudiante
- **Email**: `juan.martinez@example.com`
- **Password**: `password123`

### Profesor (para crear actividades)
- **Email**: `maria.garcia@example.com`
- **Password**: `password123`

## Flujo de Uso Completo

### Paso 1: Profesor Crea Actividad
1. Login como profesor
2. Ir a "Nueva Actividad"
3. Subir PDF con material del curso
4. Generar ejercicios con el wizard
5. Aprobar y publicar actividad

### Paso 2: Estudiante Accede a Actividad
1. Login como estudiante (`juan.martinez@example.com`)
2. Se redirige automáticamente a `/student/activities`
3. Ver lista de actividades disponibles
4. Click en "Comenzar Actividad"

### Paso 3: Trabajar en la Actividad
1. **Panel izquierdo**: Leer la consigna
2. **Panel central**: Escribir código
3. **Panel derecho**: Usar tutor IA cuando necesites ayuda

### Paso 4: Guardar y Enviar
1. Click en "Guardar Borrador" (ilimitado, no cuenta como envío)
2. Cuando estés listo: "Enviar Solución"
3. Tu nota se actualizará si reenvías

## Características del Tutor IA

### Cómo Funciona:
- Usa el material PDF que el profesor subió (RAG)
- Responde con preguntas guía (método Socrático)
- NO da la respuesta directa
- Ayuda a razonar paso a paso

### Ejemplos de Preguntas:
```
Estudiante: "¿Cómo hago un bucle?"
Tutor: "Buena pregunta. Primero, ¿qué necesitas repetir en tu código?"

Estudiante: "No sé por qué mi código da error"
Tutor: "Revisemos juntos. ¿Qué crees que hace la línea 5 de tu código?"

Estudiante: "¿Está bien mi solución?"
Tutor: "¿Por qué elegiste usar una lista aquí? ¿Qué otras opciones consideraste?"
```

## Estructura de URLs

```
/student/dashboard          → Redirect a /student/activities
/student/activities         → Lista de actividades
/student/activities/[id]    → Vista de actividad individual
```

## Variables de Entorno Requeridas

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://...

# Mistral AI (para tutor IA)
MISTRAL_API_KEY=your_mistral_key_here

# ChromaDB (opcional, usa local por defecto)
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v3
```

## Solución de Problemas

### El tutor IA no responde correctamente
- Verificar que `MISTRAL_API_KEY` esté configurada
- Si no hay API key, el sistema usa respuestas de fallback
- Revisar logs del backend para errores

### No se carga el contexto RAG
- Verificar que el profesor haya subido un PDF para la actividad
- ChromaDB debe estar ejecutándose (o usar modo local)
- El sistema funciona con fallback si RAG no está disponible

### El código no se guarda
- Verificar que el backend esté ejecutándose
- Revisar la consola del navegador para errores
- El código también se guarda temporalmente en localStorage

### No aparecen actividades
- Verificar que el estudiante esté inscrito en algún curso
- El profesor debe haber publicado actividades
- Revisar la base de datos: tabla `sessions_v2` para relación estudiante-actividad

## Verificación del Sistema

### Backend Health Check
```bash
curl http://localhost:8000/api/v3/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-27T..."
}
```

### Frontend Health Check
- Abrir: `http://localhost:3000`
- Debería ver la página de login

### Database Check
```sql
-- Verificar actividades
SELECT activity_id, title, status FROM activities;

-- Verificar estudiantes en actividades
SELECT DISTINCT user_id, activity_id 
FROM sessions_v2 
WHERE user_id = '73c6ea9f-95f7-4a62-ae09-c620fbcb7082';

-- Verificar submissions
SELECT * FROM submissions 
WHERE student_id = '73c6ea9f-95f7-4a62-ae09-c620fbcb7082';
```

## Próximos Pasos Recomendados

1. **Testing**: Crear tests E2E con Playwright
2. **Mobile**: Optimizar UI para dispositivos móviles
3. **Notificaciones**: Agregar sistema de notificaciones
4. **Analytics**: Dashboard de progreso del estudiante
5. **Gamificación**: Badges y logros

## Recursos Adicionales

- **Documentación completa**: `PANEL_ESTUDIANTES_COMPLETO.md`
- **API Reference**: `BACKEND_API_REFERENCE.md`
- **Tests**: Directorio `frontend/tests/`

## Soporte

Para problemas o dudas:
1. Revisar logs del backend: `uvicorn` output
2. Revisar consola del navegador (F12)
3. Verificar variables de entorno
4. Consultar documentación del proyecto

¡Disfruta del panel de estudiantes! 🎉
