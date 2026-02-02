"""
TeacherGeneratorGraph - LangGraph Workflow for Exercise Generation

Implements a stateful workflow for PDF ingestion and exercise generation:
1. ingest_pdf: Process PDF & vectorize to ChromaDB
2. generate_draft: Use Mistral to generate 10 exercises from PDF context
3. human_review: Checkpoint for teacher approval
4. publish: Save approved exercises to database

Uses:
- LangGraph for state management
- Mistral AI for generation
- ChromaDB for RAG context
"""
from __future__ import annotations

import logging
import uuid
import traceback
from datetime import datetime
from typing import TypedDict, Annotated, Sequence, Literal, Optional, Dict, Any, List
from pathlib import Path
import operator
from json_repair import repair_json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import threading

# Global shared memory for job states (thread-safe)
_shared_memory_lock = threading.Lock()
_shared_memory_store = {}
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_mistralai import ChatMistralAI

from backend.src_v3.infrastructure.ai.rag.document_processor import DocumentProcessor
from backend.src_v3.infrastructure.ai.rag.chroma_store import ChromaVectorStore
from backend.src_v3.core.domain.teacher.entities import (
    ExerciseRequirements,
    GeneratedExercise,
    TestCase,
)

logger = logging.getLogger(__name__)


class GeneratorState(TypedDict):
    """State for the exercise generator workflow"""
    # Identifiers
    job_id: str
    teacher_id: str
    course_id: str
    
    # Input
    pdf_path: str
    pdf_content: str
    requirements: Dict[str, Any]  # ExerciseRequirements serialized
    
    # Processing
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_phase: Literal["ingestion", "generation", "review", "published", "error"]
    
    # RAG Context
    collection_name: str
    rag_context: str
    
    # Generated Content
    draft_exercises: List[Dict[str, Any]]  # List of 10 exercises
    approved_exercises: List[str]  # Exercise IDs approved by teacher
    
    # Metadata
    error_message: Optional[str]
    created_at: str
    updated_at: str
    
    # Checkpointing
    awaiting_human_approval: bool


SYSTEM_PROMPT = """Eres un Profesor Experto en Programación Python especializado en crear ejercicios educativos de alta calidad.

Tu tarea es generar EXACTAMENTE 10 ejercicios de programación distintos basados en el material del curso proporcionado.

## REGLAS CRÍTICAS:

1. Usa SOLO información del contexto RAG (fragmentos del PDF)
2. NO inventes conceptos que no estén en el PDF
3. Cada ejercicio DEBE incluir TODOS los campos especificados

## ESTRUCTURA OBLIGATORIA PARA CADA EJERCICIO:

### mission_markdown (CONSIGNA DETALLADA - MUY IMPORTANTE):
El campo mission_markdown DEBE tener esta estructura EXACTA en Markdown:

```
## 🎯 Objetivo

[Descripción clara de qué debe lograr el estudiante - 2-3 oraciones]

## 📋 Requisitos

1. [Requisito específico 1]
2. [Requisito específico 2]  
3. [Requisito específico 3]

## ⚠️ Restricciones

- [Qué NO debe hacer el estudiante]
- [Por ejemplo: "No uses funciones built-in como sum()"]

## 💡 Ejemplo

**Entrada:**
[Ejemplo de datos de entrada]

**Salida esperada:**
[Salida que debe producir el código]

## 🔍 Pistas

- [Pista 1 sin revelar la solución]
- [Pista 2 guiando el razonamiento]
```

### starter_code (SOLO COMENTARIOS - CRÍTICO):
El starter_code debe contener ÚNICAMENTE comentarios que guíen al estudiante.
❌ NO incluyas código funcional
❌ NO incluyas variables definidas  
❌ NO incluyas funciones parcialmente implementadas
✅ SOLO comentarios explicativos

EJEMPLO CORRECTO:
```python
# Ejercicio: [Nombre]
#
# Tu tarea:
# 1. Define una función llamada [nombre]
# 2. La función debe recibir [parámetros]
# 3. Debe retornar [descripción]
#
# Escribe tu código aquí:

```

EJEMPLO INCORRECTO (NO HACER):
```python
def mi_funcion(x):
    # TODO: completar
    pass
```

### solution_code (CÓDIGO COMPLETO):
- Código Python 100% funcional y ejecutable
- Bien comentado explicando la lógica
- Incluye función principal Y llamada de prueba con print()
- Este código se usará para EVALUAR al estudiante

### test_cases:
- Mínimo 3 test cases por ejercicio
- Al menos 1 debe ser hidden (is_hidden: true)
- Inputs y outputs claros y verificables

## DIFICULTAD:
- 3 ejercicios "facil" (easy)
- 4 ejercicios "intermedio" (medium)  
- 3 ejercicios "dificil" (hard)

## FORMATO DE SALIDA (JSON ESTRICTO):
Retorna SOLO un JSON válido con esta estructura (sin markdown, sin texto extra):

{
  "exercises": [
    {
      "title": "Título descriptivo",
      "description": "Descripción breve 1-2 líneas",
      "difficulty": "facil|intermedio|dificil",
      "language": "python",
      "concepts": ["concepto1", "concepto2"],
      "mission_markdown": "## 🎯 Objetivo\\n...",
      "starter_code": "# Instrucciones...\\n# Tu código aquí:\\n",
      "solution_code": "def solucion():\\n    ...\\n\\nprint(solucion())",
      "test_cases": [
        {
          "description": "Test básico",
          "input_data": "5",
          "expected_output": "25",
          "is_hidden": false,
          "timeout_seconds": 5
        }
      ]
    }
  ]
}

NO añadas texto fuera del JSON. NO uses markdown code blocks.
"""


class TeacherGeneratorGraph:
    """
    LangGraph workflow for teacher exercise generation
    
    Phases:
    1. INGESTION: Process PDF, extract text, vectorize to ChromaDB
    2. GENERATION: Use Mistral + RAG to generate 10 exercises
    3. REVIEW: Human checkpoint for teacher approval
    4. PUBLISHED: Save approved exercises to database
    """
    
    def __init__(
        self,
        mistral_api_key: str,
        chroma_persist_directory: str = "./chroma_data",
        model_name: str = "mistral-large-latest"
    ):
        """
        Initialize the generator graph
        
        Args:
            mistral_api_key: Mistral API key
            chroma_persist_directory: Path to ChromaDB storage
            model_name: Mistral model to use (default: mistral-large-latest)
        """
        # Validate API key
        if not mistral_api_key:
            raise ValueError("mistral_api_key is required and cannot be None or empty")
        
        self.mistral_api_key = mistral_api_key
        self.chroma_persist_directory = chroma_persist_directory
        self.model_name = model_name or "mistral-large-latest"
        
        # Initialize LLM
        self.llm = ChatMistralAI(
            model=self.model_name,
            temperature=0.5,
            mistral_api_key=self.mistral_api_key
        )
        
        # Initialize document processor and vector store
        self.doc_processor = DocumentProcessor()
        self.vector_store = ChromaVectorStore(persist_directory=chroma_persist_directory)
        
        # Checkpointer for human-in-the-loop (shared memory across instances)
        global _shared_memory_store
        if not hasattr(self.__class__, '_shared_checkpointer'):
            self.__class__._shared_checkpointer = MemorySaver()
        self.memory = self.__class__._shared_checkpointer
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(
            "TeacherGeneratorGraph initialized",
            extra={"model": model_name, "chroma_dir": chroma_persist_directory}
        )
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(GeneratorState)
        
        # Add nodes
        workflow.add_node("ingest_pdf", self._ingest_pdf_node)
        workflow.add_node("generate_draft", self._generate_draft_node)
        workflow.add_node("human_review", self._human_review_node)
        workflow.add_node("publish", self._publish_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Define edges
        workflow.set_entry_point("ingest_pdf")
        
        # Conditional routing from ingestion
        workflow.add_conditional_edges(
            "ingest_pdf",
            self._route_after_ingestion,
            {
                "generate": "generate_draft",
                "error": "handle_error"
            }
        )
        
        # Conditional routing from generation
        workflow.add_conditional_edges(
            "generate_draft",
            self._route_after_generation,
            {
                "review": "human_review",
                "error": "handle_error"
            }
        )
        
        # Human review is a terminal checkpoint - execution stops here
        # To continue, teacher must call approve_and_publish which resumes the graph
        workflow.add_edge("human_review", END)
        
        workflow.add_edge("publish", END)
        workflow.add_edge("handle_error", END)
        
        # Compile with checkpointer for persistence
        return workflow.compile(checkpointer=self.memory)
    
    # ==================== NODE IMPLEMENTATIONS ====================
    
    def _ingest_pdf_node(self, state: GeneratorState) -> GeneratorState:
        """
        Phase 1: Ingest PDF and vectorize to ChromaDB
        """
        try:
            logger.info(f"Starting PDF ingestion for job {state['job_id']}")
            
            pdf_path = Path(state["pdf_path"])
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
            # Extract text from PDF
            documents = self.doc_processor.process_pdf(str(pdf_path))
            pdf_content = "\n\n".join([doc["content"] for doc in documents])
            
            # Create unique collection for this job (not course, to avoid collisions)
            collection_name = f"job_{state['job_id']}_docs"
            
            # Vectorize and store in ChromaDB
            self.vector_store.add_documents(
                documents=documents,
                collection_name=collection_name
            )
            
            # Update state
            state["pdf_content"] = pdf_content[:5000]  # Truncate for state storage
            state["collection_name"] = collection_name
            state["current_phase"] = "ingestion_complete"  # Changed to indicate completion
            state["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(
                f"PDF ingestion complete for job {state['job_id']}",
                extra={"docs_count": len(documents), "collection": collection_name}
            )
            
            return state
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - PDF ingestion: {error_trace}")
            state["current_phase"] = "error"
            state["error_message"] = f"PDF ingestion failed: {str(e)}\n\nFull traceback:\n{error_trace}"
            return state
    
    def _generate_draft_node(self, state: GeneratorState) -> GeneratorState:
        """
        Phase 2: Generate 10 exercises using Mistral + RAG
        """
        try:
            logger.info(f"🎨 Starting exercise generation for job {state['job_id']}")
            state["current_phase"] = "generation"  # Update phase immediately
            state["updated_at"] = datetime.utcnow().isoformat()
            
            # Retrieve relevant context from ChromaDB
            requirements = state["requirements"]
            topic = requirements.get("topic", "Python programming")
            
            # Query vector store for relevant chunks
            query = f"Conceptos y ejemplos sobre {topic} para crear ejercicios de programación"
            results = self.vector_store.query(
                query_text=query,
                collection_name=state["collection_name"],
                n_results=10
            )
            
            # Build RAG context
            rag_context = "\n\n".join([
                f"[Fragmento {i+1}]\n{doc}"
                for i, doc in enumerate(results["documents"])
            ])
            
            state["rag_context"] = rag_context[:10000]  # Truncate
            
            # Build prompt for Mistral
            user_prompt = f"""
Analyze the following course material and generate EXACTLY 10 programming exercises.

COURSE MATERIAL (Relevant fragments from PDF):
{rag_context}

REQUIREMENTS:
- Topic: {requirements.get('topic')}
- Target difficulty: {requirements.get('difficulty', 'mixed')}
- Programming language: {requirements.get('language', 'python')}
- Key concepts to cover: {', '.join(requirements.get('concepts', []))}
- Total exercises: 10 (3 easy + 4 medium + 3 hard)

IMPORTANT:
1. Base ALL exercises on the provided course material
2. Ensure proper difficulty progression
3. Include complete test cases for each exercise
4. Return ONLY the JSON object (no markdown code blocks, no extra text)
"""
            
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]
            
            # Call Mistral
            logger.info(f"🤖 Calling Mistral AI for job {state['job_id']}...")
            response = self.llm.invoke(messages)
            raw_content = response.content
            logger.info(f"✅ Mistral responded for job {state['job_id']}, parsing {len(raw_content)} chars...")
            
            # Parse JSON response with robust cleaning
            import json
            import re
            
            # Clean markdown code blocks if present
            cleaned_content = raw_content.strip()
            
            # Remove markdown JSON code blocks
            if "```json" in cleaned_content:
                cleaned_content = re.search(r'```json\s*(.+?)\s*```', cleaned_content, re.DOTALL)
                if cleaned_content:
                    cleaned_content = cleaned_content.group(1)
            elif "```" in cleaned_content:
                cleaned_content = re.search(r'```\s*(.+?)\s*```', cleaned_content, re.DOTALL)
                if cleaned_content:
                    cleaned_content = cleaned_content.group(1)
            
            # Remove any leading/trailing whitespace and newlines
            cleaned_content = cleaned_content.strip()
            
            # --- ROBUST PARSING LOGIC START ---
            try:
                # 1. Try standard parsing first
                data = json.loads(cleaned_content)
            except Exception as e:
                print(f"⚠️ Standard JSON parse failed: {e}. Attempting repair...")
                try:
                    # 2. Use json_repair to fix missing commas/brackets
                    # return_objects=True ensures we get a Dict/List, not a string
                    data = repair_json(cleaned_content, return_objects=True)

                    if not data:
                        raise ValueError("json_repair returned empty data")

                    print("✅ JSON successfully repaired.")
                except Exception as repair_error:
                    # 3. If repair fails, log the raw content for debugging and crash
                    print(f"❌ FATAL: Could not repair JSON. Raw content preview: {cleaned_content[:200]}...")
                    raise ValueError(f"AI Output Parsing Failed: {str(repair_error)}")
            # --- ROBUST PARSING LOGIC END ---
            
            # --- ROBUST EXERCISE EXTRACTION ---
            exercises = []
            if isinstance(data, list):
                # Case A: AI returned a direct list of exercises
                print(f"ℹ️ AI returned a direct LIST of {len(data)} exercises.")
                exercises = data
            elif isinstance(data, dict):
                # Case B: AI returned a dictionary wrapper
                print("ℹ️ AI returned a DICTIONARY wrapper.")
                # Try common keys
                exercises = data.get("exercises") or data.get("activities") or []
            else:
                # Case C: Unknown format
                print(f"⚠️ Unknown data type received: {type(data)}")
                
            if not exercises:
                 print(f"⚠️ WARNING: No exercises found in data. Keys/Content: {str(data)[:200]}")
            # --- END ROBUST EXTRACTION ---
            
            if len(exercises) != 10:
                logger.warning(f"Expected 10 exercises, got {len(exercises)}")
            
            # Update state
            state["draft_exercises"] = exercises
            state["current_phase"] = "generation"
            state["awaiting_human_approval"] = True
            state["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"✅ Exercise generation complete for job {state['job_id']}: {len(exercises)} exercises created")
            
            # Add message to history
            state["messages"] = state.get("messages", []) + [
                HumanMessage(content=user_prompt),
                AIMessage(content=f"Generated {len(exercises)} exercises")
            ]
            
            logger.info(
                f"Exercise generation complete for job {state['job_id']}",
                extra={"exercises_count": len(exercises)}
            )
            
            return state
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - Exercise generation: {error_trace}")
            state["current_phase"] = "error"
            state["error_message"] = f"Generation failed: {str(e)}\n\nFull traceback:\n{error_trace}"
            state["awaiting_human_approval"] = False
            return state
    
    def _human_review_node(self, state: GeneratorState) -> GeneratorState:
        """
        Phase 3: Human checkpoint - wait for teacher approval
        
        This is the final node before human intervention.
        The graph execution will END here and save the state.
        Teacher must call approve_and_publish to continue.
        """
        logger.info(f"✋ Job {state['job_id']} reached human review checkpoint - execution will stop here")
        
        state["current_phase"] = "review"
        state["awaiting_human_approval"] = True
        state["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"🏁 Job {state['job_id']} ready for approval with {len(state.get('draft_exercises', []))} exercises")
        
        return state
    
    def _publish_node(self, state: GeneratorState) -> GeneratorState:
        """
        Phase 4: Publish approved exercises to database
        
        Note: Actual DB persistence happens in the use case layer.
        This node just marks the job as published.
        """
        try:
            logger.info(f"Publishing exercises for job {state['job_id']}")
            
            # Filter approved exercises
            approved_ids = set(state.get("approved_exercises", []))
            
            if not approved_ids:
                # If no explicit approval, approve all
                approved_ids = set(range(len(state["draft_exercises"])))
            
            # Mark as published
            state["current_phase"] = "published"
            state["awaiting_human_approval"] = False
            state["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(
                f"Job {state['job_id']} published successfully",
                extra={"approved_count": len(approved_ids)}
            )
            
            return state
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - Publishing: {error_trace}")
            state["current_phase"] = "error"
            state["error_message"] = f"Publishing failed: {str(e)}\n\nFull traceback:\n{error_trace}"
            return state
    
    def _handle_error_node(self, state: GeneratorState) -> GeneratorState:
        """Handle errors and mark job as failed"""
        logger.error(
            f"Job {state['job_id']} failed: {state.get('error_message', 'Unknown error')}"
        )
        
        state["current_phase"] = "error"
        state["awaiting_human_approval"] = False
        state["updated_at"] = datetime.utcnow().isoformat()
        
        return state
    
    # ==================== ROUTING FUNCTIONS ====================
    
    def _route_after_ingestion(self, state: GeneratorState) -> str:
        """Route after PDF ingestion"""
        current_phase = state.get("current_phase", "")
        logger.info(f"🔀 Routing after ingestion: current_phase={current_phase}")
        
        if current_phase == "error":
            logger.info("🔀 → Going to error handler")
            return "error"
        
        logger.info("🔀 → Going to generate_draft")
        return "generate"
    
    def _route_after_generation(self, state: GeneratorState) -> str:
        """Route after exercise generation"""
        current_phase = state.get("current_phase", "")
        logger.info(f"🔀 Routing after generation: current_phase={current_phase}")
        
        if current_phase == "error":
            logger.info("🔀 → Going to error handler")
            return "error"
        
        logger.info("🔀 → Going to human_review")
        return "review"
    
    def _route_after_review(self, state: GeneratorState) -> str:
        """Route after human review"""
        # Check if teacher has approved
        if not state.get("awaiting_human_approval", True):
            if state.get("approved_exercises"):
                return "publish"
            else:
                return "regenerate"
        return "wait"
    
    # ==================== HELPER METHODS ====================
    
    async def _run_graph_until_checkpoint(self, initial_state: GeneratorState, config: dict, job_id: str):
        """
        Execute the graph until it reaches a human approval checkpoint.
        This runs in the background and saves state progressively.
        """
        try:
            logger.info(f"🎯 Executing graph for job {job_id}")
            logger.info(f"🎯 Initial state phase: {initial_state.get('current_phase')}")
            
            # Use ainvoke instead of astream to execute the full graph
            # The graph will automatically stop at the human_review checkpoint
            final_state = await self.graph.ainvoke(initial_state, config)
            
            logger.info(f"🏁 Graph execution completed for job {job_id}")
            logger.info(f"🏁 Final phase: {final_state.get('current_phase')}")
            logger.info(f"🏁 Awaiting approval: {final_state.get('awaiting_human_approval')}")
            logger.info(f"🏁 Draft exercises count: {len(final_state.get('draft_exercises', []))}")
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"💥 Graph execution failed for job {job_id}: {error_trace}")
    
    # ==================== PUBLIC API ====================
    
    async def start_generation(
        self,
        teacher_id: str,
        course_id: str,
        pdf_path: str,
        requirements: ExerciseRequirements,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new exercise generation job
        
        Args:
            teacher_id: ID of the teacher
            course_id: ID of the course
            pdf_path: Path to the PDF file
            requirements: Exercise generation requirements
            job_id: Optional job ID (will generate one if not provided)
        
        Returns:
            Dict with job_id and initial state
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
        else:
            job_id = str(job_id)  # Ensure it's a string
        
        initial_state: GeneratorState = {
            "job_id": job_id,
            "teacher_id": teacher_id,
            "course_id": course_id,
            "pdf_path": pdf_path,
            "pdf_content": "",
            "requirements": {
                "topic": requirements.topic,
                "difficulty": requirements.difficulty,
                "language": requirements.language,
                "concepts": requirements.concepts,
                "count": requirements.count
            },
            "messages": [],
            "current_phase": "ingestion",
            "collection_name": "",
            "rag_context": "",
            "draft_exercises": [],
            "approved_exercises": [],
            "error_message": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "awaiting_human_approval": False
        }
        
        # Run the graph asynchronously
        config = {"configurable": {"thread_id": job_id}}
        
        try:
            logger.info(f"🚀 Starting graph execution for job {job_id}")
            
            # Execute graph asynchronously - it will save checkpoints as it progresses
            # The BackgroundTasks from FastAPI will handle keeping this alive
            await self._run_graph_until_checkpoint(initial_state, config, job_id)
            
            logger.info(f"✅ Job {job_id} execution completed")
            
            return {
                "job_id": job_id,
                "status": "processing",
                "awaiting_approval": False,
                "error": None
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - Start generation: {error_trace}")
            return {
                "job_id": job_id,
                "status": "error",
                "awaiting_approval": False,
                "error": f"{str(e)}\n\nFull traceback:\n{error_trace}"
            }
    
    async def get_draft(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve the draft exercises for a job
        
        Args:
            job_id: The generation job ID
        
        Returns:
            Dict with draft exercises and metadata
        """
        config = {"configurable": {"thread_id": job_id}}
        
        try:
            # Get current state from checkpointer
            state = await self.graph.aget_state(config)
            
            if not state:
                return {"error": "Job not found"}
            
            return {
                "job_id": job_id,
                "status": state.values.get("current_phase"),
                "draft_exercises": state.values.get("draft_exercises", []),
                "awaiting_approval": state.values.get("awaiting_human_approval", False),
                "created_at": state.values.get("created_at"),
                "updated_at": state.values.get("updated_at")
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - Get draft: {error_trace}")
            return {"error": f"{str(e)}\n\nFull traceback:\n{error_trace}"}
    
    async def get_state(self, job_id: str) -> Dict[str, Any]:
        """
        Get the current state of a generation job (lightweight, for status polling)
        
        Args:
            job_id: The generation job ID
        
        Returns:
            Dict with current state information
        """
        config = {"configurable": {"thread_id": job_id}}
        
        try:
            logger.info(f"🔍 Checking state for job {job_id}")
            
            # Get current state from checkpointer
            state = await self.graph.aget_state(config)
            
            logger.info(f"📦 State retrieved: exists={state is not None}, values={bool(state.values) if state else False}")
            
            if not state or not state.values:
                logger.warning(f"⚠️ Job {job_id} not found in checkpointer")
                return {"error": "Job not found"}
            
            logger.info(f"✅ Job {job_id} found, phase: {state.values.get('current_phase', 'unknown')}")
            
            return {
                "job_id": job_id,
                "current_step": state.values.get("current_phase", "unknown"),
                "draft_ready": state.values.get("awaiting_human_approval", False),
                "published": state.values.get("published", False),
                "error": state.values.get("error"),
                "created_at": state.values.get("created_at"),
                "updated_at": state.values.get("updated_at")
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - Get state: {error_trace}")
            return {"error": f"{str(e)}\n\nFull traceback:\n{error_trace}"}
    
    async def approve_and_publish(
        self,
        job_id: str,
        approved_exercise_indices: Optional[List[int]] = None,
        db_session: Optional[Any] = None,
        activity_title: Optional[str] = None,
        activity_description: Optional[str] = None,
        module_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve draft and continue to publishing
        
        Args:
            job_id: The generation job ID
            approved_exercise_indices: List of indices to approve (None = approve all)
            db_session: SQLAlchemy async session for persistence (optional)
            activity_title: Title for the created activity
            activity_description: Description for the activity
            module_id: Module ID to link the activity to
        
        Returns:
            Dict with publication status and activity_id if persisted
        """
        config = {"configurable": {"thread_id": job_id}}
        
        try:
            # Get current state
            state = await self.graph.aget_state(config)
            
            if not state or not state.values:
                return {"error": "Job not found"}
            
            logger.info(f"📝 Approving job {job_id}, current phase: {state.values.get('current_phase')}")
            
            # Determine which exercises to approve
            if approved_exercise_indices is not None:
                approved_indices = approved_exercise_indices
            else:
                # Approve all
                total_exercises = len(state.values.get("draft_exercises", []))
                approved_indices = list(range(total_exercises))
            
            logger.info(f"✅ Approving {len(approved_indices)} exercises")
            
            # Extract approved exercises from state
            all_exercises = state.values.get("draft_exercises", [])
            approved_exercises = [
                all_exercises[i]
                for i in approved_indices
                if i < len(all_exercises)
            ]
            
            logger.info(f"📦 Extracted {len(approved_exercises)} exercises for persistence")
            
            # Update state to mark as published
            await self.graph.aupdate_state(
                config,
                {
                    "awaiting_human_approval": False,
                    "approved_exercises": [str(i) for i in approved_indices],
                    "current_phase": "published"  # Mark as published
                }
            )
            
            logger.info(f"✅ State updated to 'published'")
            
            response = {
                "job_id": job_id,
                "status": "published",
                "approved_count": len(approved_indices),
                "error": None
            }
            
            # If DB session provided, persist to database
            if db_session:
                from backend.src_v3.infrastructure.ai.db_persistence import publish_exercises_to_db
                
                logger.info(f"💾 Persisting {len(approved_exercises)} exercises to database...")
                
                # Persist to database
                persistence_result = await publish_exercises_to_db(
                    db_session=db_session,
                    teacher_id=state.values["teacher_id"],
                    course_id=state.values["course_id"],
                    approved_exercises=approved_exercises,
                    activity_title=activity_title or f"Generated Activity {job_id[:8]}",
                    activity_description=activity_description or "Auto-generated from course material",
                    module_id=module_id
                )
                
                response["activity_id"] = persistence_result["activity_id"]
                response["exercise_ids"] = persistence_result["exercise_ids"]
                response["persisted"] = True
                
                logger.info(
                    f"Published exercises to database: {persistence_result['activity_id']}",
                    extra={"job_id": job_id, "activity_id": persistence_result["activity_id"]}
                )
            
            return response
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"CRITICAL AI FAILURE - Approve and publish: {error_trace}")
            return {"error": f"{str(e)}\n\nFull traceback:\n{error_trace}"}
