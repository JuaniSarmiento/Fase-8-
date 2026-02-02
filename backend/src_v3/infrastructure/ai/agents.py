"""LangGraph / AI agents wired to LLM providers + RAG."""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging

from prometheus_client import Counter

from backend.src_v3.core.domain.student.entities import (
    TutorMessage,
    CognitivePhase,
    TutorMode,
)
from backend.src_v3.infrastructure.llm.factory import LLMProviderFactory
from backend.src_v3.infrastructure.llm.base import LLMMessage, LLMRole
from backend.src_v3.infrastructure.ai.rag import ChromaRAGService


logger = logging.getLogger(__name__)


LLM_CALLS_TOTAL = Counter(
    "llm_calls_total",
    "Total LLM calls made by AI agents",
    labelnames=["agent", "provider"],
)


# ==================== TUTOR SOCRÁTICO ====================

SOCRATIC_TUTOR_PROMPT = """Eres un Tutor Socrático de Programación especializado en el Ciclo Heurístico.

## TU MISIÓN:
Guiar al estudiante hacia el descubrimiento autónomo a través de preguntas estratégicas.

## REGLAS DE ORO (NUNCA LAS ROMPAS):
1. ❌ JAMÁS des código resuelto, ni parcial ni completo
2. ❌ JAMÁS resuelvas el problema por el estudiante
3. ✅ Responde SIEMPRE con preguntas que desafíen su razonamiento
4. ✅ Usa el Ciclo Heurístico: Exploración → Descomposición → Abstracción → Validación
5. ✅ Sé breve y directo (máximo 3-4 oraciones)
6. ✅ Si detectas frustración, simplifica sin dar la respuesta

## CICLO HEURÍSTICO:
**Exploración:** "¿Qué sabes sobre X?" "¿Has visto algo similar antes?"
**Descomposición:** "¿Cómo dividirías este problema en partes más pequeñas?"
**Abstracción:** "¿Qué patrón reconoces aquí?"
**Validación:** "¿Cómo verificarías que funciona correctamente?"

## DETECCIÓN DE FRUSTRACIÓN:
Si el estudiante dice: "No entiendo nada", "Esto es muy difícil", "Dame la respuesta"
→ Responde: "Entiendo que es desafiante. Empecemos por algo más simple: [pregunta básica relacionada]"

## TU ESTILO:
- Empático pero firme
- Nunca condescendiente
- Celebra el razonamiento, no solo las respuestas correctas
- Usa analogías del mundo real
"""


class SocraticTutorAgent:
    """
    Tutor Socrático Agent - Pedagogical AI with domain awareness and RAG.
    
    Uses Mistral as LLM core with ChromaDB for context retrieval.
    """
    
    def __init__(self):
        """Initialize tutor agent with Mistral + RAG"""
        self.llm_factory = LLMProviderFactory()
        # Will use LLM_PROVIDER env (mistral by default in docker-compose)
        self.llm = self.llm_factory.create_from_env()
        self.rag_service = ChromaRAGService()
    
    async def respond(
        self,
        student_message: str,
        session_id: str,
        conversation_history: List[Dict],
        cognitive_phase: str = "exploration",
        topic: Optional[str] = None,
        exercise_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate Socratic response to student message.
        
        Args:
            student_message: Student's message content
            session_id: Session ID for tracking
            conversation_history: Previous messages
            cognitive_phase: Current learning phase
            topic: Topic for RAG context
            exercise_context: Current exercise details (title, description, mission)
        
        Returns:
            Dict with response, cognitive phase, and metadata
        """
        # Get RAG context if topic provided
        rag_context = ""
        if topic:
            rag_context = self.rag_service.get_context_for_topic(topic)
        
        # Build conversation context
        system_prompt = SOCRATIC_TUTOR_PROMPT
        
        # Add exercise context if available
        if exercise_context:
            exercise_section = f"""
## EJERCICIO ACTUAL DEL ESTUDIANTE:
- **Título:** {exercise_context.get('title', 'Sin título')}
- **Dificultad:** {exercise_context.get('difficulty', 'Desconocida')}
- **Lenguaje:** {exercise_context.get('language', 'python')}
- **Descripción:** {exercise_context.get('description', 'Sin descripción')}
- **Misión/Instrucciones:**
{exercise_context.get('mission', 'Sin instrucciones específicas')}

Tu objetivo es ayudar al estudiante a resolver ESTE ejercicio específico usando el método socrático.
"""
            system_prompt += exercise_section
        
        if rag_context:
            system_prompt += f"\n\nContexto académico (RAG):\n{rag_context}\n"
        
        # Build LLMMessage history (limit last 5 turns)
        llm_messages: List[LLMMessage] = []

        # System prompt as first message
        llm_messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system_prompt))

        # Conversation history comes as list[dict] {role, content}
        for msg in conversation_history[-5:]:
            role_str = msg.get("role", "user")
            if role_str == "assistant":
                role = LLMRole.ASSISTANT
            elif role_str == "system":
                role = LLMRole.SYSTEM
            else:
                role = LLMRole.USER
            llm_messages.append(
                LLMMessage(role=role, content=msg.get("content", ""))
            )

        # Current student message
        llm_messages.append(LLMMessage(role=LLMRole.USER, content=student_message))

        # Generate response with configured provider (mock/ollama/mistral/...)
        llm_response = await self.llm.generate(
            messages=llm_messages,
            temperature=0.7,
            max_tokens=500,
        )

        # Metrics + structured logging
        provider = "unknown"
        try:
            info = self.llm.get_model_info()
            provider = str(info.get("provider", "unknown"))
        except Exception:  # pragma: no cover - defensive
            pass
        LLM_CALLS_TOTAL.labels(agent="socratic_tutor", provider=provider).inc()

        logger.info(
            "socratic_tutor_llm_call",
            extra={
                "agent": "socratic_tutor",
                "provider": provider,
                "session_id": session_id,
                "rag_used": bool(rag_context),
            },
        )

        return {
            "response": llm_response.content,
            "cognitive_phase": cognitive_phase,
            "rag_used": bool(rag_context),
            "rag_context": rag_context if rag_context else None,
            "model": llm_response.model,
        }

    async def respond_stream(
        self,
        student_message: str,
        session_id: str,
        conversation_history: List[Dict],
        cognitive_phase: str = "exploration",
        topic: Optional[str] = None,
    ):
        """Streaming variant of respond using LLMProvider.generate_stream.

        Yields text chunks as they are produced by the LLM. If the
        underlying provider does not implement streaming, it falls back
        to a single full response chunk.
        """
        rag_context = ""
        if topic:
            rag_context = self.rag_service.get_context_for_topic(topic)

        system_prompt = SOCRATIC_TUTOR_PROMPT
        if rag_context:
            system_prompt += f"\n\nContexto académico:\n{rag_context}\n"

        llm_messages: List[LLMMessage] = []
        llm_messages.append(LLMMessage(role=LLMRole.SYSTEM, content=system_prompt))

        for msg in conversation_history[-5:]:
            role_str = msg.get("role", "user")
            if role_str == "assistant":
                role = LLMRole.ASSISTANT
            elif role_str == "system":
                role = LLMRole.SYSTEM
            else:
                role = LLMRole.USER
            llm_messages.append(LLMMessage(role=role, content=msg.get("content", "")))

        llm_messages.append(LLMMessage(role=LLMRole.USER, content=student_message))

        provider = "unknown"
        try:
            info = self.llm.get_model_info()
            provider = str(info.get("provider", "unknown"))
        except Exception:  # pragma: no cover - defensive
            pass
        LLM_CALLS_TOTAL.labels(agent="socratic_tutor", provider=provider).inc()

        logger.info(
            "socratic_tutor_llm_stream_call",
            extra={
                "agent": "socratic_tutor",
                "provider": provider,
                "session_id": session_id,
                "rag_used": bool(rag_context),
            },
        )

        try:
            async for chunk in self.llm.generate_stream(
                messages=llm_messages,
                temperature=0.7,
                max_tokens=500,
            ):
                text = getattr(chunk, "content", None) or str(chunk)
                if text:
                    yield text
        except Exception:
            # Fallback: non-streaming response
            llm_response = await self.llm.generate(
                messages=llm_messages,
                temperature=0.7,
                max_tokens=500,
            )
            if llm_response.content:
                yield llm_response.content


# ==================== AUDITOR DE CÓDIGO ====================

CODE_AUDITOR_PROMPT = """## ROL: Evaluador de Codigo Educativo

Eres un evaluador de codigo para estudiantes. Tu mision es calificar si el codigo cumple con la consigna del ejercicio.

## CRITERIO PRINCIPAL:
Si el codigo CUMPLE la consigna y produce el resultado esperado = nota ALTA (70-100)
Si el codigo cumple PARCIALMENTE = nota MEDIA (50-69)
Si el codigo NO cumple o tiene errores graves = nota BAJA (0-49)

## ESCALA DE CALIFICACION:
- 90-100: Codigo cumple perfectamente la consigna
- 80-89: Codigo funciona correctamente con detalles menores
- 70-79: Codigo cumple la consigna basica
- 50-69: Cumple parcialmente o tiene errores menores
- 30-49: Tiene errores pero muestra comprension
- 0-29: No funcional o no cumple la consigna

## REGLAS IMPORTANTES:
1. Si hay CODIGO DE REFERENCIA, compara la FUNCIONALIDAD, no la sintaxis exacta
2. Un codigo diferente pero que CUMPLE la consigna = nota ALTA
3. Ser GENEROSO con estudiantes principiantes
4. Valorar el INTENTO y la LOGICA aunque no sea perfecto
5. Si el codigo ejecuta sin errores y produce output correcto = minimo 70 puntos

## FORMATO DE RESPUESTA (JSON ESTRICTO):
{
  "score": <int 0-100>,
  "feedback": "<que esta bien y que podria mejorar>",
  "suggestion": "<consejo breve para mejorar>"
}

RESPONDE SOLO CON EL JSON, sin texto adicional.
"""


class CodeAuditorAgent:
    """
    Code Auditor Agent - Critical code reviewer with grading capabilities.
    
    Migrated from Fase 7 with improvements:
    - Domain-aware (works with code submissions)
    - Integrates with sandbox execution results
    - Stateless operation
    - Returns structured JSON grading
    """
    
    def __init__(
        self,
        llm_provider: Optional[object] = None,
    ):
        """Initialize auditor agent.

        If no provider is passed, it falls back to the global
        LLMProviderFactory configuration (LLM_PROVIDER env var).
        """
        if llm_provider is not None:
            self.llm = llm_provider
        else:
            factory = LLMProviderFactory()
            # Uses LLM_PROVIDER from environment (mock/ollama/mistral/...)
            self.llm = factory.create_from_env()
    
    async def audit(
        self,
        code: str,
        language: str,
        execution_result: Optional[Dict[str, Any]] = None,
        exercise_description: Optional[str] = None,
        solution_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Audit submitted code and provide critical feedback and grade.
        
        Args:
            code: Student's code submission
            language: Programming language
            execution_result: Results from sandbox execution
            exercise_description: Exercise context (mission, description)
            solution_code: Reference solution for comparison
        
        Returns:
            Dict with score, feedback, suggestion.
        """
        # Build audit request
        audit_request = f"Audita este código {language} del estudiante y califícalo:\n\n```{language}\n{code}\n```"
        
        if exercise_description:
            audit_request += f"\n\n## CONSIGNA DEL EJERCICIO:\n{exercise_description}"
        
        if solution_code:
            audit_request += f"\n\n## CÓDIGO DE REFERENCIA (solución correcta):\n```{language}\n{solution_code}\n```"
            audit_request += "\n\nNOTA: Compara el código del estudiante con la referencia. El estudiante NO necesita tener el código idéntico, solo debe cumplir la consigna."
        
        if execution_result:
            audit_request += f"\n\n## RESULTADO DE EJECUCIÓN (Sandbox):\n"
            audit_request += f"- Exit code: {execution_result.get('exit_code', 'N/A')}\n"
            audit_request += f"- Stdout: {execution_result.get('stdout', '')[:500]}\n"
            audit_request += f"- Stderr: {execution_result.get('stderr', '')[:500]}\n"
            
            if execution_result.get('exit_code') != 0:
                audit_request += "\n⚠️ El código falló al ejecutarse. Esto afecta negativamente la nota."
        
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=CODE_AUDITOR_PROMPT),
            LLMMessage(role=LLMRole.USER, content=audit_request),
        ]

        response = await self.llm.generate(messages, temperature=0.2)

        provider = "unknown"
        try:
            info = self.llm.get_model_info()
            provider = str(info.get("provider", "unknown"))
        except Exception:  # pragma: no cover - defensive
            pass
        LLM_CALLS_TOTAL.labels(agent="code_auditor", provider=provider).inc()

        logger.info(
            "code_auditor_llm_call",
            extra={
                "agent": "code_auditor",
                "provider": provider,
                "language": language,
                "has_execution_result": bool(execution_result),
            },
        )
        
        # Parse JSON response
        try:
            content = response.content
            # Clean generic markdown ticks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
                
            result = json.loads(content.strip())
            return {
                "score": int(result.get("score", 50)),
                "feedback": str(result.get("feedback", "No feedback provided")),
                "suggestion": str(result.get("suggestion", "")),
            }
        except Exception as e:
            logger.warning(f"Failed to parse Code Auditor JSON: {e}. Raw response: {response.content}")
            # Fallback
            return {
                "score": 50,
                "feedback": response.content, # Return raw text as feedback if JSON fails
                "suggestion": "Revisar formato de respuesta del auditor.",
            }


# ==================== GOVERNANCE AGENT ====================

GOVERNANCE_PROMPT = """## ROL: Agente de Gobernanza Ética y Control de Riesgos

Eres el guardián ético del sistema educativo. Tu misión es detectar y prevenir:
1. Dependencia excesiva de IA
2. Plagio o copypaste de soluciones
3. Patrones de fraude académico
4. Riesgos cognitivos y emocionales

## DIMENSIONES DE ANÁLISIS:

### 1. Dependencia de IA
- Más de 5 consultas consecutivas sin implementación
- Solicitudes de "dame el código completo"
- Copypaste directo de respuestas anteriores

### 2. Integridad Académica
- Código idéntico a ejemplos del curso
- Soluciones de fuentes externas
- Cambios superficiales en código provisto

### 3. Bienestar Cognitivo
- Frustración prolongada (>10 interacciones sin progreso)
- Burnout patterns
- Desmotivación extrema

## NIVELES DE ALERTA:
- **INFO**: Comportamiento normal
- **LOW**: Patrón emergente, monitorear
- **MEDIUM**: Intervención preventiva recomendada
- **HIGH**: Requiere intervención docente inmediata
- **CRITICAL**: Riesgo grave, detener sesión

## OUTPUT:
Retorna JSON con:
- risk_level: Nivel de riesgo detectado
- dimension: Dimensión afectada
- evidence: Lista de evidencias
- recommendation: Acción recomendada
"""


class GovernanceAgent:
    """Governance Agent - Ethical and risk monitoring via LLM.

    This agent consumes lightweight session metrics and (optionally)
    recent messages, and returns a **JSON-parseable** assessment with
    the shape:

    - risk_level: "info" | "low" | "medium" | "high" | "critical"
    - dimension: e.g. "ai_dependency", "integrity", "wellbeing"
    - evidence: list[str]
    - recommendation: str

    The agent is typically enabled via an environment flag in the
    dependency container, so tests/environments without an external LLM
    can run without depending on it.
    """

    def __init__(self, llm_provider: Optional[object] = None) -> None:
        if llm_provider is not None:
            self.llm = llm_provider
        else:
            factory = LLMProviderFactory()
            self.llm = factory.create_from_env()

    async def analyze_session(
        self,
        session_metrics: Dict[str, Any],
        recent_messages: List[TutorMessage],
    ) -> Dict[str, Any]:
        """Analyze session for ethical/risk issues and return structured JSON.

        Parsing is robust: if the LLM does not return valid JSON, we
        fall back to a safe, medium-risk assessment.
        """
        # Build analysis request
        analysis_request = "Analiza esta sesión para detectar riesgos y devuelve SOLO JSON.\n\n"
        analysis_request += "Métricas de sesión (pueden faltar algunas):\n"
        for key, value in (session_metrics or {}).items():
            analysis_request += f"- {key}: {value}\n"

        if recent_messages:
            analysis_request += "\nÚltimas interacciones:\n"
            for msg in recent_messages[-5:]:
                analysis_request += f"- [{msg.sender}] {msg.content[:120]}...\n"

        system_prompt = (
            GOVERNANCE_PROMPT
            + "\n\nIMPORTANTE: Devuelve SOLO un JSON válido con las claves: "
            "risk_level, dimension, evidence, recommendation. Sin texto adicional."
        )

        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
            LLMMessage(role=LLMRole.USER, content=analysis_request),
        ]

        response = await self.llm.generate(messages, temperature=0.3)

        provider = "unknown"
        try:
            info = self.llm.get_model_info()
            provider = str(info.get("provider", "unknown"))
        except Exception:  # pragma: no cover - defensive
            pass
        LLM_CALLS_TOTAL.labels(agent="governance", provider=provider).inc()

        logger.info(
            "governance_llm_call",
            extra={
                "agent": "governance",
                "provider": provider,
                "has_metrics": bool(session_metrics),
                "messages_count": len(recent_messages or []),
            },
        )

        return self._parse_response(response.content)

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        """Parse LLM JSON output into a normalized dict.

        If parsing fails or fields are missing, reasonable defaults are
        applied so callers can always rely on the same shape.
        """
        if not raw:
            return self._fallback("Respuesta vacía del LLM")

        try:
            data = json.loads(raw)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to parse governance JSON: %s", exc)
            return self._fallback(raw)

        risk_level = str(data.get("risk_level", "medium")).lower()
        allowed_levels = {"info", "low", "medium", "high", "critical"}
        if risk_level not in allowed_levels:
            risk_level = "medium"

        dimension = str(data.get("dimension", "ai_dependency"))

        evidence = data.get("evidence") or []
        if not isinstance(evidence, list):
            evidence = [evidence]
        evidence = [str(e) for e in evidence][:5]

        recommendation = str(data.get("recommendation") or "")
        if not recommendation:
            recommendation = (
                "Revisar la sesión; el agente de gobernanza no proporcionó "
                "una recomendación explícita."
            )

        return {
            "risk_level": risk_level,
            "dimension": dimension,
            "evidence": evidence,
            "recommendation": recommendation,
        }

    def _fallback(self, raw: str) -> Dict[str, Any]:
        """Fallback assessment when JSON cannot be parsed."""
        snippet = (raw or "")[:200]
        return {
            "risk_level": "medium",
            "dimension": "ai_dependency",
            "evidence": [snippet] if snippet else [],
            "recommendation": (
                "No se pudo interpretar correctamente la salida del LLM. "
                "Usar juicio docente para revisar la sesión."
            ),
        }
