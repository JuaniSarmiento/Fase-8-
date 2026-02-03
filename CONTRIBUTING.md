# Contribuir a AI-Native Learning Platform

¡Gracias por tu interés en contribuir! Este documento proporciona guías para contribuir al proyecto.

## Estructura del Proyecto

```
Fase 8/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── scripts/          # Scripts utilitarios
│   ├── database/     # Gestión de BD
│   ├── seed/         # Datos de prueba
│   ├── maintenance/  # Mantenimiento
│   └── setup/        # Instalación
├── tests/            # Suite de pruebas
│   ├── e2e/          # End-to-end tests
│   └── unit/         # Unit tests
├── docs/             # Documentación
│   ├── architecture/ # Diseño técnico
│   ├── guides/       # Guías de uso
│   ├── reports/      # Reportes
│   └── resources/    # Recursos (PDFs)
└── sql/              # Scripts SQL
    ├── init/         # Inicialización
    └── migrations/   # Migraciones
```

## Convenciones de Código

### Backend (Python)
- **Style Guide**: PEP 8
- **Type Hints**: Usar type hints en todas las funciones
- **Naming**: snake_case para funciones y variables
- **Classes**: PascalCase para clases
- **Async**: Usar async/await para operaciones I/O

```python
async def get_user_by_email(email: str) -> Optional[User]:
    """Obtiene usuario por email.
    
    Args:
        email: Email del usuario
        
    Returns:
        Usuario o None si no existe
    """
    pass
```

### Frontend (TypeScript/React)
- **Style Guide**: Airbnb React/JSX Style Guide
- **Naming**: camelCase para variables, PascalCase para componentes
- **Hooks**: Prefijo "use" para custom hooks
- **Props**: TypeScript interfaces para props

```typescript
interface ButtonProps {
  text: string;
  onClick: () => void;
  disabled?: boolean;
}

export function Button({ text, onClick, disabled = false }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {text}
    </button>
  );
}
```

## Workflow de Desarrollo

### 1. Setup Inicial
```bash
# Clonar repositorio
git clone <repo-url>
cd "Fase 8"

# Instalar dependencias backend
pip install -r requirements.txt

# Instalar dependencias frontend
cd frontend
npm install
```

### 2. Levantar Entorno de Desarrollo
```bash
# Docker (backend + postgres + chromadb)
docker-compose up -d

# Frontend (desarrollo)
cd frontend
npm run dev
```

### 3. Crear Branch
```bash
git checkout -b feature/nombre-feature
```

### 4. Desarrollo
- Escribir código siguiendo convenciones
- Agregar tests si es necesario
- Actualizar documentación si aplica

### 5. Testing
```bash
# Backend tests
pytest tests/e2e/

# Frontend tests (cuando existan)
cd frontend
npm test
```

### 6. Commit
```bash
git add .
git commit -m "feat: descripción del cambio"
```

**Formato de commits:**
- `feat:` Nueva funcionalidad
- `fix:` Bug fix
- `docs:` Cambios en documentación
- `style:` Formato, sin cambios de código
- `refactor:` Refactorización
- `test:` Agregar tests
- `chore:` Tareas de mantenimiento

### 7. Push y Pull Request
```bash
git push origin feature/nombre-feature
```

## Agregar Nueva Funcionalidad

### Backend (Nueva Ruta API)
1. Crear endpoint en `backend/src_v3/infrastructure/http/api/v3/routers/`
2. Agregar lógica de negocio en `backend/src_v3/domain/`
3. Actualizar repositorio si necesita BD en `backend/src_v3/infrastructure/persistence/repositories/`
4. Agregar tests en `tests/e2e/`
5. Documentar en `BACKEND_API_REFERENCE.md`

### Frontend (Nuevo Componente)
1. Crear componente en `frontend/components/`
2. Agregar tipos si es necesario en interfaces
3. Actualizar store si maneja estado global
4. Documentar props y uso

## Migraciones de Base de Datos

### Crear Nueva Migración
1. Crear archivo en `sql/migrations/migrate_YYYY_MM_DD_descripcion.sql`
2. Escribir SQL con comentarios explicativos:
```sql
-- Migración: Agregar campo avatar a users
-- Fecha: 2024-01-15
-- Autor: Tu Nombre

ALTER TABLE users ADD COLUMN avatar_url TEXT;
```

3. Probar migración:
```bash
docker exec ai_native_postgres psql -U postgres -d ai_native -f /sql/migrations/migrate_2024_01_15_avatar.sql
```

4. Documentar en `sql/README.md`

## Scripts Utilitarios

### Agregar Nuevo Script
Colocar en la carpeta apropiada:
- `scripts/database/` - Gestión de BD
- `scripts/seed/` - Datos de prueba
- `scripts/maintenance/` - Mantenimiento
- `scripts/setup/` - Instalación

Seguir convenciones:
```python
"""
Script: seed_new_data.py
Propósito: Poblar nuevos datos de prueba
Uso: python scripts/seed/seed_new_data.py
"""

def main():
    """Función principal del script."""
    pass

if __name__ == "__main__":
    main()
```

## Testing

### Agregar Tests E2E
En `tests/e2e/test_nueva_funcionalidad.py`:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_nueva_funcionalidad():
    """Test de nueva funcionalidad."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v3/nueva-ruta")
        assert response.status_code == 200
```

## Documentación

### Actualizar Documentación
- **API Changes**: Actualizar `docs/reports/BACKEND_API_REFERENCE.md`
- **Features**: Crear reporte en `docs/reports/NOMBRE_FEATURE_COMPLETE.md`
- **Guías**: Agregar en `docs/guides/`
- **Architecture**: Actualizar `docs/architecture/` si hay cambios estructurales

## Debugging

### Backend
```bash
# Ver logs Docker
docker logs ai_native_backend -f

# Debugger Python (agregar en código)
import pdb; pdb.set_trace()
```

### Frontend
- Usar React DevTools
- Console en navegador
- Network tab para API calls

## Preguntas Frecuentes

**¿Dónde van los nuevos archivos?**
- Scripts → `scripts/[database|seed|maintenance|setup]/`
- Tests → `tests/[e2e|unit]/`
- Docs → `docs/[architecture|guides|reports]/`
- SQL → `sql/[init|migrations]/`

**¿Cómo reinicio la base de datos?**
```bash
python scripts/database/rebuild_db_simple.py
python scripts/seed/cleanup_and_seed_teacher.py
```

**¿Cómo pruebo cambios del frontend?**
```bash
cd frontend
npm run dev
# Abrir http://localhost:3000
```

## Contacto

Para preguntas o ayuda, contactar al equipo de desarrollo.
