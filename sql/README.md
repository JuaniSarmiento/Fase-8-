# SQL

Scripts SQL para base de datos PostgreSQL.

## Estructura

### `init/`
Scripts de inicialización del esquema:
- `init_database.sql` - Schema completo inicial
- `create_tables.sql` - Creación de tablas principales
- `create_tables_v2_clean.sql` - Schema V2 limpio

**Uso:**
```bash
docker exec ai_native_postgres psql -U postgres -d ai_native -f /sql/init/init_database.sql
```

### `migrations/`
Migraciones y actualizaciones del esquema:
- `migrate_lms_hierarchy.sql` - Migración de jerarquía LMS
- `migrate_full_schema_v2.sql` - Migración completa a V2
- `migrate_enums_to_text.sql` - Convertir enums a text
- `migrate_enrollments_*.sql` - Migraciones de enrollments
- `update_*.sql` - Actualizaciones específicas
- `add_critical_indexes.sql` - Agregar índices de performance
- `clean_database.sql` - Limpieza de base de datos

**Aplicar migración:**
```bash
docker exec ai_native_postgres psql -U postgres -d ai_native -f /sql/migrations/nombre_migracion.sql
```

## Orden de Ejecución Recomendado

1. **Inicialización** (primera vez):
   ```bash
   psql -f sql/init/init_database.sql
   ```

2. **Migraciones** (en orden cronológico):
   ```bash
   psql -f sql/migrations/migrate_lms_hierarchy.sql
   psql -f sql/migrations/add_critical_indexes.sql
   ```

3. **Limpieza** (si es necesario):
   ```bash
   psql -f sql/migrations/clean_database.sql
   ```
