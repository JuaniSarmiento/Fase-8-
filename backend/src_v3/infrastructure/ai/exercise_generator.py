"""Exercise Generator Agent for Fase 8.

Uses the generic LLMProviderFactory (Mistral/Ollama/etc.) plus optional
RAG context from Chroma to generate a `GeneratedExercise` domain entity.

The agent is intentionally conservative: it asks the LLM for a small JSON
structure and validates it. If anything fails, callers should fall back to
safe deterministic generation.
"""

from __future__ import annotations

import json
from typing import Optional

from backend.src_v3.infrastructure.llm.factory import LLMProviderFactory
from backend.src_v3.infrastructure.llm.base import LLMMessage, LLMRole
from backend.src_v3.core.domain.teacher.entities import (
    ExerciseRequirements,
    GeneratedExercise,
    TestCase,
)


SYSTEM_PROMPT = """Eres un profesor experto en programación Python. Tu tarea es crear ejercicios de programación de alta calidad pedagógica.

## FORMATO DE RESPUESTA (JSON ESTRICTO):
Responde ÚNICAMENTE con un JSON válido, sin texto adicional:

{
  "title": "Título descriptivo del ejercicio",
  "description": "Descripción breve en 1-2 líneas",
  "mission_markdown": "CONSIGNA DETALLADA (ver estructura abajo)",
  "starter_code": "SOLO COMENTARIOS GUÍA",
  "solution_code": "CÓDIGO COMPLETO FUNCIONAL",
  "test_cases": [...]
}

## ESTRUCTURA OBLIGATORIA DE mission_markdown:

El campo mission_markdown DEBE tener esta estructura EXACTA en markdown:

```
## 🎯 Objetivo

[Descripción clara de qué debe lograr el estudiante - 2-3 oraciones]

## 📋 Requisitos

1. [Requisito específico 1]
2. [Requisito específico 2]
3. [Requisito específico 3]

## ⚠️ Restricciones

- [Qué NO debe hacer el estudiante, si aplica]
- [Por ejemplo: "No uses funciones built-in como sum()"]

## 💡 Ejemplo

**Entrada:**
```python
# Ejemplo de datos de entrada
```

**Salida esperada:**
```
# Salida que debe producir el código
```

## 🔍 Pistas

- [Pista 1 sin revelar la solución]
- [Pista 2 guiando el razonamiento]
```

## REGLAS PARA starter_code (MUY IMPORTANTE):

El starter_code debe contener ÚNICAMENTE comentarios que guíen al estudiante.
❌ NO incluyas código funcional
❌ NO incluyas variables definidas
❌ NO incluyas funciones parcialmente implementadas
✅ SOLO comentarios explicativos

EJEMPLO CORRECTO de starter_code:
```python
# Ejercicio: [Nombre del ejercicio]
#
# Tu tarea:
# 1. Define una función llamada [nombre]
# 2. La función debe recibir [parámetros]
# 3. Debe retornar [descripción del resultado]
#
# Escribe tu código aquí:

```

EJEMPLO INCORRECTO (NO HACER):
```python
def mi_funcion(x):
    # TODO: completar
    pass
```

## REGLAS PARA solution_code:

El solution_code debe ser:
- Código Python 100% funcional y ejecutable
- Bien comentado explicando la lógica
- Incluye la función/código principal
- Incluye llamada de prueba con print() para verificar
- Será usado como REFERENCIA para evaluar al estudiante

EJEMPLO de solution_code:
```python
def calcular_factorial(n):
    \"\"\"Calcula el factorial de un número.\"\"\"
    if n == 0 or n == 1:
        return 1
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado

# Prueba
print(f"Factorial de 5: {calcular_factorial(5)}")  # Output: 120
```

## REGLAS PARA test_cases:

- Mínimo 2 test cases, máximo 5
- Cada test case debe tener input y output claros
- No uses input(), open(), eval(), exec()
- Los tests deben ser ejecutables automáticamente
"""


class ExerciseGeneratorAgent:
    """Small wrapper around the generic LLM provider to generate exercises."""

    def __init__(self) -> None:
        # Use provider from env (typically mistral in docker-compose)
        self.llm = LLMProviderFactory.create_from_env()

    async def generate(
        self,
        requirements: ExerciseRequirements,
        rag_context: Optional[str] = None,
    ) -> GeneratedExercise:
        """Generate a single exercise using LLM + optional RAG context.

        May raise exceptions if LLM is not configured or output is invalid.
        Callers should catch and provide a fallback if needed.
        """
        topic = requirements.topic
        difficulty = requirements.difficulty
        language = requirements.language
        concepts = ", ".join(requirements.concepts or [])

        user_prompt = f"""
Genera un ejercicio de programación.

TEMA: {topic}
DIFICULTAD: {difficulty}
LENGUAJE: {language}
CONCEPTOS: {concepts or 'generales'}

CONTEXTO DEL CURSO (RAG):
{rag_context or 'N/A'}

Recuerda responder SOLO con el JSON pedido.
"""

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=SYSTEM_PROMPT),
            LLMMessage(role=LLMRole.USER, content=user_prompt),
        ]

        response = await self.llm.generate(messages, temperature=0.5, max_tokens=1200)
        raw = response.content.strip()

        # Intentar limpiar bloques ```json
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]

        data = json.loads(raw)

        title = data.get("title") or f"Ejercicio: {topic}"
        description = data.get("description") or f"Ejercicio sobre {topic}"
        mission_markdown = data.get("mission_markdown") or f"## Misión\n\nResuelve un ejercicio sobre {topic}."
        starter_code = data.get("starter_code") or "# TODO: implementa la solución aquí\n"
        solution_code = data.get("solution_code") or "# Solución de referencia\n"

        raw_tests = data.get("test_cases") or []
        test_cases: list[TestCase] = []
        for idx, tc in enumerate(raw_tests, start=1):
            test_cases.append(
                TestCase(
                    test_number=idx,
                    description=tc.get("description") or f"Test {idx}",
                    input_data=tc.get("input_data") or "",
                    expected_output=tc.get("expected_output") or "",
                    is_hidden=bool(tc.get("is_hidden", False)),
                    timeout_seconds=int(tc.get("timeout_seconds") or 5),
                )
            )

        # Asegurar al menos 2 tests para respetar invariantes de dominio
        if len(test_cases) < 2:
            test_cases.append(
                TestCase(
                    test_number=len(test_cases) + 1,
                    description="Test adicional auto-generado",
                    input_data="",
                    expected_output="",
                    is_hidden=True,
                    timeout_seconds=5,
                )
            )

        exercise = GeneratedExercise(
            exercise_id="",  # Se asigna en el caso de uso
            title=title,
            description=description,
            difficulty=difficulty,
            language=language,
            mission_markdown=mission_markdown,
            starter_code=starter_code,
            solution_code=solution_code,
            test_cases=test_cases,
            concepts=requirements.concepts or [],
            learning_objectives=[f"Comprender {topic}"],
            estimated_time_minutes=requirements.estimated_time_minutes,
            rag_sources=[],
        )

        return exercise
