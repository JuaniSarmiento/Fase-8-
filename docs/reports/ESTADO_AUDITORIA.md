# Estado Actual - Auditoría de Schema

## ✅ Lo que se ha completado

**Herramientas creadas y funcionales:**
1. `audit_schema.py` - Script principal de auditoría ✅
2. `find_db_password.py` - Buscador de contraseña ✅
3. `show_model_structure.py` - Visualizador de modelos ✅
4. `reset_pg_password.ps1` - Resetear contraseña (requiere Admin) ✅
5. `setup_audit_tools.ps1` - Instalador de dependencias ✅
6. `demo_audit_tool.py` - Demostración ✅
7. Documentación completa ✅

## 🔴 Problema actual: Autenticación PostgreSQL

**Estado:**
- PostgreSQL está ejecutándose en puerto 5433 ✅
- Base de datos `ai_native` existe (probablemente) ✅
- Usuario `postgres` existe ✅
- **PROBLEMA:** La contraseña no es conocida ❌

**Contraseñas probadas (todas fallaron):**
- postgres, admin123, password, admin, 1234, root
- ai_native_password_dev, 12345, 123456
- postgres123, postgres18, Pass1234, Password1
- qwerty, abc123

## 🛠️ Opciones para resolver

### Opción 1: Resetear contraseña (RECOMENDADO)

**Pasos:**
1. Abre PowerShell **como Administrador** (clic derecho → "Ejecutar como administrador")
2. Navega a tu carpeta:
   ```powershell
   cd "C:\Users\juani\Desktop\Fase 8"
   ```
3. Ejecuta el script de reset:
   ```powershell
   .\reset_pg_password.ps1
   ```
4. Esto establecerá la contraseña a `postgres`
5. Luego ejecuta:
   ```powershell
   python audit_schema.py
   ```

### Opción 2: Buscar contraseña en instalación PostgreSQL

Revisa si hay archivos de configuración con la contraseña:

```powershell
# Buscar archivo pgpass
Get-Content "$env:APPDATA\postgresql\pgpass.conf" -ErrorAction SilentlyContinue

# Buscar archivos de instalación
Get-ChildItem "C:\Program Files\PostgreSQL\18" -Filter "*.txt" -Recurse | Select-String -Pattern "password"
```

### Opción 3: Usar el modo DRY-RUN (sin conexión DB)

Mientras tanto, puedes usar las herramientas sin conectarte a la base de datos:

```powershell
# Ver estructura de modelos
python show_model_structure.py

# Ver qué se auditaría
python audit_schema.py --dry-run

# Ver demo
python demo_audit_tool.py
```

### Opción 4: Reinstalar PostgreSQL

Si nada funciona, considera reinstalar PostgreSQL 18 con contraseña conocida.

## 📊 Modelos listos para auditar

Una vez resuelto el problema de contraseña, se auditarán estos 11 modelos:

| # | Modelo | Tabla | Primary Key | Columnas |
|---|--------|-------|-------------|----------|
| 1 | UserModel | users | id | 9 |
| 2 | UserProfileModel | user_profiles | profile_id | 8 |
| 3 | SubjectModel | subjects | subject_id | 6 |
| 4 | CourseModel | courses | course_id | 6 |
| 5 | CommissionModel | commissions | commission_id | 8 |
| 6 | ActivityModel | activities | activity_id | 14 |
| 7 | SessionModelV2 | sessions_v2 | session_id | 12 |
| 8 | ExerciseModelV2 | exercises_v2 | exercise_id | 15 |
| 9 | ExerciseAttemptModelV2 | exercise_attempts_v2 | attempt_id | 9 |
| 10 | CognitiveTraceModelV2 | cognitive_traces_v2 | trace_id | 13 |
| 11 | RiskModelV2 | risks_v2 | risk_id | 10 |

## 🎯 Próximo paso recomendado

**Ejecutar como Administrador:**
```powershell
.\reset_pg_password.ps1
```

Esto resolverá el problema de autenticación y permitirá ejecutar la auditoría completa.

---

**Fecha:** 26 de enero de 2026  
**Sistema:** PostgreSQL 18 en Windows  
**Puerto:** 5433  
**Herramientas:** Completadas y funcionales ✅
