# 🔧 INSTRUCCIONES: Reconstruir Base de Datos

## Problema Actual
La contraseña de PostgreSQL no es conocida y necesitamos reconstruir la base de datos.

## ✅ Solución (Método Recomendado)

### Opción 1: Usando PowerShell como Administrador

1. **Clic derecho** en el archivo `RUN_AS_ADMIN.ps1`
2. Selecciona **"Ejecutar con PowerShell"**
3. Acepta el diálogo de UAC (Control de Cuentas de Usuario)
4. El script hará automáticamente:
   - Resetear contraseña a "postgres"
   - Eliminar base de datos existente
   - Crear nueva base de datos "ai_native"
   - Crear todas las tablas
   - Actualizar .env

### Opción 2: Desde Terminal PowerShell

```powershell
# 1. Abrir PowerShell como Administrador
#    (Busca "PowerShell" → Clic derecho → Ejecutar como administrador)

# 2. Navegar a la carpeta
cd "C:\Users\juani\Desktop\Fase 8"

# 3. Ejecutar el script
.\rebuild_database.ps1
```

## 🔄 Método Alternativo (Si conoces la contraseña actual)

Si conoces la contraseña actual de PostgreSQL:

```powershell
# Editar el script y cambiar la password
notepad rebuild_db_simple.py
# Busca: passwords_to_try = [...]
# Agrega tu contraseña a la lista

# Ejecutar
python rebuild_db_simple.py
```

## 📋 Lo que hace el script

1. ✅ Verifica que PostgreSQL esté corriendo
2. ✅ Resetea la contraseña a "postgres"
3. ✅ Elimina la base de datos existente
4. ✅ Crea una nueva base de datos "ai_native"
5. ✅ Actualiza el archivo .env
6. ✅ Crea todas las tablas usando SQLAlchemy
7. ✅ Verifica la conexión

## 📊 Después de la reconstrucción

Una vez completado, ejecuta:

```powershell
# Verificar que todo funcione
python audit_schema.py

# Ver las tablas creadas
python show_model_structure.py
```

## ⚠️ Nota Importante

Este proceso **eliminará todos los datos existentes** en la base de datos. Solo hazlo si:
- Estás en desarrollo/testing
- No hay datos importantes que conservar
- Quieres empezar desde cero

## 🆘 Si algo sale mal

1. Verifica que PostgreSQL esté corriendo:
   ```powershell
   Get-Service postgresql-x64-18
   ```

2. Si el servicio está detenido:
   ```powershell
   Start-Service postgresql-x64-18
   ```

3. Revisa los logs de PostgreSQL en:
   ```
   C:\Program Files\PostgreSQL\18\data\log\
   ```

## ✅ Resultado Esperado

Al finalizar verás:

```
============================================
Reconstruccion completada!
============================================

Credenciales:
  Host: 127.0.0.1
  Puerto: 5433
  Usuario: postgres
  Password: postgres
  Base de datos: ai_native

Proximo paso:
  python audit_schema.py
```

## 🎯 Siguiente Paso

Una vez que la base de datos esté reconstruida:

```powershell
# Ejecutar la auditoría de schema
python audit_schema.py
```

Esto verificará que todos los modelos Python coincidan exactamente con las tablas de la base de datos.
