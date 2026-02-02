# 🔧 Debug Guide: Wizard No Responde al Click

## 🔍 Pasos de Diagnóstico

### 1. Abre la Consola del Navegador
**Windows/Linux**: `F12` o `Ctrl + Shift + I`
**Mac**: `Cmd + Option + I`

Ve a la pestaña **Console**

### 2. Intenta Crear una Actividad

1. Click en **"Nueva Actividad"**
2. Llena los campos:
   - Título: "Test Activity"
   - Tema: "Python Basics"
   - Dificultad: "FACIL"
3. Click **"Siguiente"**
4. En la pestaña PDF, selecciona cualquier archivo PDF
5. Click **"✨ Generar con IA"**

### 3. Revisa los Logs en la Consola

Deberías ver estos mensajes en secuencia:

```
🚀 Starting generation process...
Source type: pdf
PDF file: File { name: "test.pdf", size: 12345, ... }
Text content length: 0
✅ Validation passed, moving to step 3
📄 Processing PDF upload...
Creating activity directly (PDF processing skipped for MVP)
📝 Creating activity with data: { title: "Test Activity", ... }
✅ Activity created: { activity_id: "...", ... }
✅ Activity created successfully
Closing dialog and refreshing...
```

### 4. Posibles Problemas y Soluciones

#### ❌ Problema 1: "No pasa nada" - Sin logs
**Causa**: El evento click no se está disparando

**Solución**:
```bash
# Reinicia el servidor de desarrollo
cd frontend
npm run dev
```

Luego refresca el navegador con `Ctrl + F5` (hard refresh)

#### ❌ Problema 2: Error en consola: "Cannot read property 'id' of null"
**Causa**: Usuario no está autenticado correctamente

**Solución**:
1. Cierra sesión
2. Vuelve a iniciar sesión como docente
3. Intenta de nuevo

#### ❌ Problema 3: Error 404 al llamar `/teacher/activities`
**Causa**: Backend no está corriendo o endpoint incorrecto

**Verificar backend**:
```bash
docker ps | findstr backend
# Debería mostrar: ai_native_backend ... Up
```

Si no está corriendo:
```bash
docker restart ai_native_backend
```

#### ❌ Problema 4: Error 422 "Validation error"
**Causa**: Datos del formulario incorrectos

**Revisa en Network tab**:
- Ve a Network tab (Pestaña Red)
- Filtra por "activities"
- Click en la petición fallida
- Ve a "Payload" para ver qué se envió
- Ve a "Response" para ver el error

#### ❌ Problema 5: Se queda en Step 3 eternamente
**Causa**: La promesa nunca se resuelve

**Revisa**:
```javascript
// En consola del navegador, ejecuta:
localStorage.clear()
location.reload()
```

### 5. Prueba con Modo Texto (Más Simple)

Si el PDF no funciona, prueba con texto:

1. Click "Nueva Actividad"
2. Llena metadata
3. Click "Siguiente"
4. Cambia a pestaña **"✍️ Texto Manual"**
5. Pega cualquier texto (ej. "Ejercicios de Python básico")
6. Click "✨ Generar con IA"

Esto debería funcionar más fácilmente porque no requiere upload de archivos.

### 6. Verifica el Estado del Botón

Abre React DevTools (extensión del navegador) y busca:
```
Components > CreateActivityDialog
Props:
  - open: true/false
  - onOpenChange: function
  - onSuccess: function
```

### 7. Test Manual en Consola

Ejecuta esto en la consola del navegador:
```javascript
// Verificar que el API está disponible
console.log(window.api || 'API not found');

// Intentar crear actividad directamente
fetch('http://localhost:8000/api/v3/teacher/activities', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  },
  body: JSON.stringify({
    title: "Test Direct",
    subject: "Python",
    instructions: "Test activity",
    difficulty_level: "FACIL",
    status: "DRAFT"
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

## 🔬 Logs Mejorados

He agregado logs extensivos al wizard. Ahora verás:

### En Step 1 (Metadata):
- Validación de campos

### En Step 2 (Source):
- Tipo de fuente seleccionada
- Archivo PDF o longitud de texto

### En Step 3 (Processing):
- "🚀 Starting generation process..."
- "✅ Validation passed"
- "📄 Processing PDF upload..." o "📝 Processing text input..."
- "✅ Activity created successfully"
- "Closing dialog and refreshing..."

### En caso de error:
- "❌ Error generating activity:"
- Detalles completos del error
- Status code
- Response data

## 🚀 Inicio Rápido (Reset Total)

Si nada funciona, haz un reset completo:

```bash
# 1. Para el frontend
# Presiona Ctrl+C en la terminal donde corre npm run dev

# 2. Limpia node_modules y reinstala
cd frontend
rm -rf node_modules
rm package-lock.json
npm install

# 3. Reinicia backend
docker restart ai_native_backend

# 4. Limpia caché del navegador
# En el navegador: Ctrl + Shift + Delete
# Marca: Cookies, Cache
# Click "Limpiar datos"

# 5. Vuelve a iniciar frontend
npm run dev

# 6. Abre en navegador
# http://localhost:3000
# Ctrl + Shift + R (hard refresh)

# 7. Inicia sesión de nuevo
# docente@test.com / tu_password
```

## 📊 Checklist de Verificación

- [ ] Backend corriendo (`docker ps | findstr backend`)
- [ ] Frontend corriendo (`npm run dev` sin errores)
- [ ] Usuario autenticado (ver localStorage.token en DevTools)
- [ ] Consola del navegador abierta
- [ ] Network tab abierta para ver requests
- [ ] No hay errores en consola al abrir el dashboard

## 🎯 Próximos Pasos Después de Resolver

1. Si funcionó con texto pero no con PDF → Es un problema de FormData
2. Si funcionó con PDF → El endpoint del backend puede no estar configurado
3. Si no funcionó ninguno → Revisa autenticación y permisos

## 💡 Notas Importantes

**Cambio reciente**: He modificado el wizard para que en modo PDF simplemente cree la actividad directamente SIN procesar el PDF. Esto es porque el endpoint `/teacher/generator/upload` requiere configuración compleja del backend (Mistral API, ChromaDB, etc).

Para este MVP, el wizard:
- ✅ Crea la actividad con la metadata
- ✅ Muestra la animación de progreso
- ✅ Refresca la tabla automáticamente
- ⏸️ NO procesa el PDF (puedes agregar ejercicios manualmente después)

Si necesitas el procesamiento completo de PDF, hay que configurar:
1. MISTRAL_API_KEY en variables de entorno
2. ChromaDB corriendo
3. LangGraph configurado

---

**Creado**: 26/01/2026  
**Versión**: 1.0 - Debug Enhanced
