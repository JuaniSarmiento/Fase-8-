# Tests

Suite de pruebas del proyecto consolidada.

## Estructura

### `e2e/`
Tests end-to-end que prueban flujos completos (48 archivos):

**Tests de Flujo Completo:**
- `test_full_conversation_e2e.py` - Test de conversación completa con tutor
- `test_complete_student_flow_e2e.py` - Flujo completo de estudiante
- `test_e2e_student_flow_complete.py` - Flujo E2E estudiante completo
- `test_e2e_real.py` - Tests E2E reales
- `test_e2e_validation.py` - Validación E2E
- `test_e2e_rag_validation.py` - Validación E2E del sistema RAG
- `test_simple_e2e.py` - Tests E2E simplificados

**Tests de Integración:**
- `test_integration.py` - Tests de integración general
- `test_auth_integration.py` - Integración de autenticación
- `test_analytics_integration.py` - Integración de analytics
- `test_catalog_integration.py` - Integración del catálogo
- `test_governance_integration.py` - Integración de governance
- `test_mistral_integration.py` - Integración con Mistral AI
- `test_teacher_generate_exercise_integration.py` - Integración generación ejercicios

**Tests de API:**
- `test_api.py` - Tests generales de API
- `test_api_endpoints.py` - Tests de endpoints específicos
- `test_analyst_api.py` - API del analista
- `test_mistral_api.py` - API de Mistral

**Tests de Backend:**
- `test_analyst_backend.py` - Backend del analista
- `test_grading_service.py` - Servicio de calificación
- `test_models.py` - Tests de modelos

**Tests de Flujos por Rol:**
- `test_student_flow.py` - Flujo de estudiante
- `test_student_use_cases.py` - Casos de uso estudiante
- `test_teacher_flow.py` - Flujo de profesor
- `test_teacher_use_cases.py` - Casos de uso profesor

**Tests de IA y RAG:**
- `test_ai_tutor.py` - Tests del tutor IA
- `test_rag_internal.py` - Tests del sistema RAG interno
- `test_pdf_rag_mistral.py` - Tests de RAG con PDFs y Mistral
- `test_mistral_simple.py` - Tests simples de Mistral
- `test_real_mistral.py` - Tests reales de Mistral
- `validate_mistral.py` - Validación de Mistral

**Tests de PDFs:**
- `debug_pdf.py` - Debug de procesamiento PDF
- `test_new_pdf.py` - Tests de nuevos PDFs

**Configuración:**
- `conftest.py` - Configuración de pytest y fixtures
- `test_e2e_docker.sh` - Script para tests E2E en Docker

### `unit/`
Tests unitarios (por implementar)

## Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests E2E específicos
pytest tests/e2e/test_full_conversation_e2e.py

# Tests por categoría
pytest tests/e2e/ -k "integration"
pytest tests/e2e/ -k "student"
pytest tests/e2e/ -k "mistral"

# Con verbose
pytest -v

# Con coverage
pytest --cov=backend/src_v3

# Solo tests rápidos (excluir E2E completos)
pytest tests/e2e/ -k "not e2e_real"
```

## Configuración

Ver `pytest.ini` en la raíz del proyecto para configuración de pytest.

## Notas

- **Total de tests E2E**: 48 archivos
- Todos los tests han sido consolidados desde múltiples ubicaciones
- Los tests E2E requieren que los servicios Docker estén corriendo
- Algunos tests requieren variables de entorno configuradas (.env)
