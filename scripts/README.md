# Scripts

Scripts utilitarios organizados por categoría.

## Estructura

### `database/`
Scripts para gestión de base de datos:
- `init_db.py` - Inicialización de base de datos
- `init_db_docker.py` - Inicialización dentro de Docker
- `backup_database.py` - Backup de base de datos
- `rebuild_db_simple.py` - Reconstrucción simple de DB
- `verify_database.py` - Verificación de integridad

### `seed/`
Scripts para poblar la base de datos con datos de prueba:
- `cleanup_and_seed_teacher.py` - Limpia y crea usuario docente
- `seed_activities.py` - Poblar actividades
- `seed_students_v2.py` - Poblar estudiantes
- `seed_users.py` - Poblar usuarios
- `quick_seed_activities.py` - Seed rápido de actividades
- `populate_comision1.py` - Poblar comisión específica

### `maintenance/`
Scripts de mantenimiento y utilidades:
- `apply_lms_migration.py` - Aplicar migraciones LMS
- `check_old_attempts.py` - Verificar intentos antiguos
- `clean_*.py` - Scripts de limpieza
- `update_*.py` - Scripts de actualización
- `verify_*.py` - Scripts de verificación
- `generate_student_conversations.py` - Generar conversaciones

### `setup/`
Scripts de instalación y configuración:
- `*.ps1` - Scripts PowerShell para Windows
- `*.sh` - Scripts Bash para Linux/Mac
- Incluyen setup de dependencias, bases de datos, etc.

## Uso

```bash
# Inicializar base de datos
python scripts/database/init_db.py

# Crear usuario docente
python scripts/seed/cleanup_and_seed_teacher.py

# Verificar sistema
python scripts/maintenance/verify_full_system.py
```
