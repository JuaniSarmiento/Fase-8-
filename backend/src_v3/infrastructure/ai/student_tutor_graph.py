"""
StudentTutorGraph - LangGraph Workflow for Socratic Tutoring

Implements N4 Cognitive Traceability with 7 phases:
1. EXPLORATION - Understand the problem
2. DECOMPOSITION - Break down into parts
3. PLANNING - Design solution strategy
4. IMPLEMENTATION - Write code
5. DEBUGGING - Fix errors
6. VALIDATION - Test solution
7. REFLECTION - Learn from experience

Uses:
- LangGraph for stateful cognitive phase transitions
- Mistral AI for Socratic dialogue
- ChromaDB for RAG context from course materials
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TypedDict, Annotated, Sequence, Literal, Optional, Dict, Any, List
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_mistralai import ChatMistralAI

from backend.src_v3.infrastructure.ai.rag.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class TutorState(TypedDict):
    """State for Socratic tutor interaction"""
    # Identifiers
    session_id: str
    student_id: str
    activity_id: str
    course_id: str
    
    # Cognitive Phase (N4 Level)
    cognitive_phase: Literal[
        "exploration",
        "decomposition", 
        "planning",
        "implementation",
        "debugging",
        "validation",
        "reflection"
    ]
    
    # Conversation
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # RAG Context
    collection_name: str
    rag_context: str
    
    # Student State
    current_code: str
    error_messages: List[str]
    frustration_level: float  # 0.0 - 1.0
    understanding_level: float  # 0.0 - 1.0
    hint_count: int
    
    # Activity Context
    activity_instructions: str
    expected_concepts: List[str]
    
    # Metadata
    created_at: str
    updated_at: str
    total_interactions: int


SOCRATIC_SYSTEM_PROMPT = """You are a Socratic AI Tutor for a programming course, specialized in guiding students through reflective questioning.

YOUR MISSION:
- DO NOT give the solution directly
- ASK QUESTIONS to make the student think
- USE the course context (RAG) from the syllabus to guide
- ADAPT your style based on the current cognitive phase
- DETECT frustration levels and adjust your approach accordingly

COGNITIVE PHASES (N4 Framework):
1. EXPLORATION: Help understand the problem ("What does the problem ask for?")
2. DECOMPOSITION: Help break down the problem ("What parts does this problem have?")
3. PLANNING: Help design the solution ("What steps would you follow?")
4. IMPLEMENTATION: Help write code ("What data structure would you use?")
5. DEBUGGING: Help find errors ("What do you think causes this error?")
6. VALIDATION: Help test the solution ("How would you verify it works?")
7. REFLECTION: Help reflect on learning ("What did you learn from this?")

CRITICAL RULES:
1. NEVER provide complete code solutions
2. USE the RAG context to reference course material when available
3. If frustration_level > 0.7, provide more direct hints
4. If the answer is in the course context, guide the student to find it
5. If not in the context, use general programming knowledge but mention it's outside the syllabus
6. Always respond in the same language as the student's question
4. Si understanding_level < 0.3, simplifica tu lenguaje
5. Limita hints a 3 por fase
6. Celebra los avances del estudiante

FORMATO DE RESPUESTA:
Responde SOLO con texto natural, sin JSON. Haz UNA pregunta Socrática a la vez.
"""


class StudentTutorGraph:
    """
    LangGraph workflow for Socratic tutoring with N4 cognitive traceability
    
    Manages state transitions through 7 cognitive phases, providing
    contextualized guidance using RAG from course materials.
    """
    
    def __init__(
        self,
        mistral_api_key: str,
        chroma_persist_directory: str = "./chroma_data",
        model_name: str = "mistral-small-latest"  # Use small for cost-effectiveness
    ):
        """
        Initialize the tutor graph
        
        Args:
            mistral_api_key: Mistral API key
            chroma_persist_directory: Path to ChromaDB storage
            model_name: Mistral model to use
        """
        self.mistral_api_key = mistral_api_key
        self.chroma_persist_directory = chroma_persist_directory
        self.model_name = model_name
        
        # Initialize LLM
        self.llm = ChatMistralAI(
            model=model_name,
            temperature=0.7,  # Higher for more creative tutoring
            mistral_api_key=mistral_api_key
        )
        
        # Initialize vector store for RAG
        self.vector_store = ChromaVectorStore(persist_directory=chroma_persist_directory)
        
        # Memory for session persistence
        self.memory = MemorySaver()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(
            "StudentTutorGraph initialized",
            extra={"model": model_name, "chroma_dir": chroma_persist_directory}
        )
    
    def _build_graph(self) -> StateGraph:
        """Build the cognitive phase state machine"""
        workflow = StateGraph(TutorState)
        
        # Add nodes for each cognitive phase
        workflow.add_node("exploration", self._exploration_node)
        workflow.add_node("decomposition", self._decomposition_node)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("implementation", self._implementation_node)
        workflow.add_node("debugging", self._debugging_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("reflection", self._reflection_node)
        
        # Set entry point
        workflow.set_entry_point("exploration")
        
        # Define conditional transitions (student can move back/forward)
        for phase in [
            "exploration",
            "decomposition",
            "planning",
            "implementation",
            "debugging",
            "validation"
        ]:
            workflow.add_conditional_edges(
                phase,
                self._route_next_phase,
                {
                    "exploration": "exploration",
                    "decomposition": "decomposition",
                    "planning": "planning",
                    "implementation": "implementation",
                    "debugging": "debugging",
                    "validation": "validation",
                    "reflection": "reflection",
                    "end": END
                }
            )
        
        # Reflection always ends
        workflow.add_edge("reflection", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    # ==================== PHASE NODES ====================
    
    def _exploration_node(self, state: TutorState) -> TutorState:
        """
        Phase 1: EXPLORATION - Understanding the problem
        
        Student explores the problem space and understands requirements.
        Tutor asks: "What does the problem ask for?"
        """
        state["cognitive_phase"] = "exploration"
        return self._generate_tutoring_response(state)
    
    def _decomposition_node(self, state: TutorState) -> TutorState:
        """
        Phase 2: DECOMPOSITION - Breaking down the problem
        
        Student identifies sub-problems and components.
        Tutor asks: "What parts does this problem have?"
        """
        state["cognitive_phase"] = "decomposition"
        return self._generate_tutoring_response(state)
    
    def _planning_node(self, state: TutorState) -> TutorState:
        """
        Phase 3: PLANNING - Designing the solution
        
        Student creates a step-by-step plan.
        Tutor asks: "What steps would you follow?"
        """
        state["cognitive_phase"] = "planning"
        return self._generate_tutoring_response(state)
    
    def _implementation_node(self, state: TutorState) -> TutorState:
        """
        Phase 4: IMPLEMENTATION - Writing code
        
        Student implements the solution.
        Tutor asks: "What data structure would you use?"
        """
        state["cognitive_phase"] = "implementation"
        return self._generate_tutoring_response(state)
    
    def _debugging_node(self, state: TutorState) -> TutorState:
        """
        Phase 5: DEBUGGING - Fixing errors
        
        Student identifies and fixes errors.
        Tutor asks: "What do you think causes this error?"
        """
        state["cognitive_phase"] = "debugging"
        return self._generate_tutoring_response(state)
    
    def _validation_node(self, state: TutorState) -> TutorState:
        """
        Phase 6: VALIDATION - Testing the solution
        
        Student tests and verifies correctness.
        Tutor asks: "How would you test if this works?"
        """
        state["cognitive_phase"] = "validation"
        return self._generate_tutoring_response(state)
    
    def _reflection_node(self, state: TutorState) -> TutorState:
        """
        Phase 7: REFLECTION - Learning from experience
        
        Student reflects on what they learned.
        Tutor asks: "What did you learn from this?"
        """
        state["cognitive_phase"] = "reflection"
        return self._generate_tutoring_response(state)
    
    def _generate_tutoring_response(self, state: TutorState) -> TutorState:
        """
        Generate Socratic response using Mistral + RAG context
        
        This is the core tutoring logic that:
        1. Retrieves relevant course material (RAG)
        2. Analyzes student's frustration/understanding
        3. Generates phase-appropriate Socratic question
        """
        try:
            # Get latest student message
            last_messages = state["messages"][-3:] if len(state["messages"]) > 3 else state["messages"]
            
            # Retrieve RAG context based on current phase and student question
            if last_messages and isinstance(last_messages[-1], HumanMessage):
                student_query = last_messages[-1].content
            else:
                student_query = f"Help with {state['cognitive_phase']} phase"
            
            # Query course materials
            rag_results = self.vector_store.query(
                query_text=student_query,
                collection_name=state["collection_name"],
                n_results=3
            )
            
            rag_context = "\n\n".join([
                f"[Material del curso - Fragmento {i+1}]\n{doc}"
                for i, doc in enumerate(rag_results["documents"])
            ])
            
            state["rag_context"] = rag_context[:3000]  # Truncate
            
            # Build context-aware prompt
            context_info = f"""
ACTIVITY CONTEXT:
{state['activity_instructions'][:500]}

EXPECTED CONCEPTS TO MASTER:
{', '.join(state['expected_concepts'])}

COURSE MATERIAL (RAG Context from Syllabus):
{rag_context}

--- STUDENT STATE ---
CURRENT COGNITIVE PHASE: {state['cognitive_phase'].upper()}
FRUSTRATION LEVEL: {state['frustration_level']:.2f} (0=calm, 1=very frustrated)
UNDERSTANDING LEVEL: {state['understanding_level']:.2f} (0=low, 1=high)
HINTS GIVEN IN THIS PHASE: {state['hint_count']}
TOTAL INTERACTIONS: {state['total_interactions']}

STUDENT'S CURRENT CODE:
```python
{state['current_code'][:500] if state['current_code'] else '(no code yet)'}
```

RECENT ERROR MESSAGES:
{chr(10).join(state['error_messages'][-2:]) if state['error_messages'] else '(no errors)'}

GUIDANCE FOR YOUR RESPONSE:
- If frustration is high (>0.7), be more supportive and give clearer hints
- If understanding is low (<0.3), ask simpler, more basic questions
- Use the RAG context to reference specific concepts from the course material
- If the student's question relates to material in RAG, guide them to discover it
- If not in RAG, acknowledge it's beyond the current syllabus but provide general guidance
"""
            
            # Build messages for LLM
            messages = [
                SystemMessage(content=SOCRATIC_SYSTEM_PROMPT),
                SystemMessage(content=context_info)
            ]
            
            # Add conversation history (last 6 messages)
            messages.extend(last_messages[-6:])
            
            # Generate response
            response = self.llm.invoke(messages)
            ai_response = response.content
            
            # Update state
            state["messages"] = state["messages"] + [AIMessage(content=ai_response)]
            state["total_interactions"] += 1
            state["updated_at"] = datetime.utcnow().isoformat()
            
            # Update hint count
            if "hint" in ai_response.lower() or "te sugiero" in ai_response.lower():
                state["hint_count"] += 1
            
            logger.info(
                f"Tutoring response generated for session {state['session_id']}",
                extra={
                    "phase": state['cognitive_phase'],
                    "frustration": state['frustration_level'],
                    "interactions": state['total_interactions']
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to generate tutoring response: {e}", exc_info=True)
            
            # Fallback response
            fallback_msg = "¿Puedes explicarme con más detalle qué parte te resulta difícil?"
            state["messages"] = state["messages"] + [AIMessage(content=fallback_msg)]
            state["total_interactions"] += 1
            state["updated_at"] = datetime.utcnow().isoformat()
            
            return state
    
    def _route_next_phase(self, state: TutorState) -> str:
        """
        Route to next cognitive phase based on student progress
        
        Analyzes the conversation to determine if student should:
        - Stay in current phase
        - Progress to next phase
        - Go back to previous phase
        - End session (reflection complete)
        """
        current_phase = state["cognitive_phase"]
        interactions_in_phase = state["total_interactions"]
        understanding = state["understanding_level"]
        
        # Natural progression order
        phase_order = [
            "exploration",
            "decomposition",
            "planning",
            "implementation",
            "debugging",
            "validation",
            "reflection"
        ]
        
        current_index = phase_order.index(current_phase)
        
        # Simple heuristic: progress after 3+ interactions if understanding is good
        if interactions_in_phase >= 3 and understanding > 0.6:
            # Move to next phase
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
            else:
                return "end"
        
        # Check if student explicitly signals readiness
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            content_lower = last_message.content.lower()
            
            # Student wants to move forward
            if any(phrase in content_lower for phrase in ["siguiente", "next", "avanzar", "continuar"]):
                if current_index < len(phase_order) - 1:
                    return phase_order[current_index + 1]
            
            # Student wants to go back
            if any(phrase in content_lower for phrase in ["volver", "back", "anterior", "no entiendo"]):
                if current_index > 0:
                    return phase_order[current_index - 1]
        
        # Default: stay in current phase
        return current_phase
    
    # ==================== PUBLIC API ====================
    
    async def start_session(
        self,
        student_id: str,
        activity_id: str,
        course_id: str,
        activity_instructions: str,
        expected_concepts: List[str],
        starter_code: str = ""
    ) -> Dict[str, Any]:
        """
        Start a new tutoring session
        
        Args:
            student_id: ID of the student
            activity_id: ID of the activity
            course_id: ID of the course
            activity_instructions: The exercise instructions
            expected_concepts: List of concepts to learn
            starter_code: Initial code template
        
        Returns:
            Dict with session_id and initial message
        """
        session_id = str(uuid.uuid4())
        collection_name = f"course_{course_id}_exercises"
        
        initial_state: TutorState = {
            "session_id": session_id,
            "student_id": student_id,
            "activity_id": activity_id,
            "course_id": course_id,
            "cognitive_phase": "exploration",
            "messages": [],
            "collection_name": collection_name,
            "rag_context": "",
            "current_code": starter_code,
            "error_messages": [],
            "frustration_level": 0.0,
            "understanding_level": 0.5,  # Start neutral
            "hint_count": 0,
            "activity_instructions": activity_instructions,
            "expected_concepts": expected_concepts,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "total_interactions": 0
        }
        
        # Add welcome message
        welcome = f"""¡Hola! Soy tu tutor personal para esta actividad.

Vamos a trabajar juntos siguiendo un proceso de pensamiento estructurado.

Empecemos con la **fase de EXPLORACIÓN**: ¿Has leído el enunciado del ejercicio? ¿Qué crees que te pide hacer?"""
        
        initial_state["messages"] = [AIMessage(content=welcome)]
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            # Initialize state in graph
            await self.graph.aupdate_state(config, initial_state)
            
            return {
                "session_id": session_id,
                "cognitive_phase": "exploration",
                "welcome_message": welcome,
                "rag_context": ""
            }
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}", exc_info=True)
            return {
                "session_id": session_id,
                "cognitive_phase": "exploration",
                "welcome_message": welcome,
                "error": str(e)
            }
    
    async def send_message(
        self,
        session_id: str,
        student_message: str,
        current_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send student message and get tutor response
        
        Args:
            session_id: The tutoring session ID
            student_message: Student's question/message
            current_code: Current code (if changed)
            error_message: Any error from code execution
        
        Returns:
            Dict with tutor_response and updated state
        """
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            # Get current state
            state = await self.graph.aget_state(config)
            
            if not state:
                return {"error": "Session not found"}
            
            # Update state with new information
            updated_state = dict(state.values)
            updated_state["messages"] = list(updated_state["messages"]) + [
                HumanMessage(content=student_message)
            ]
            
            if current_code:
                updated_state["current_code"] = current_code
            
            if error_message:
                updated_state["error_messages"] = updated_state["error_messages"] + [error_message]
            
            # Analyze frustration/understanding (simple heuristics)
            if "no entiendo" in student_message.lower() or "ayuda" in student_message.lower():
                updated_state["frustration_level"] = min(1.0, updated_state["frustration_level"] + 0.2)
                updated_state["understanding_level"] = max(0.0, updated_state["understanding_level"] - 0.1)
            
            if "ya entendí" in student_message.lower() or "gracias" in student_message.lower():
                updated_state["frustration_level"] = max(0.0, updated_state["frustration_level"] - 0.2)
                updated_state["understanding_level"] = min(1.0, updated_state["understanding_level"] + 0.2)
            
            # Invoke graph to generate response
            result = await self.graph.ainvoke(updated_state, config)
            
            # Get tutor's response (last AI message)
            tutor_response = ""
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    tutor_response = msg.content
                    break
            
            return {
                "session_id": session_id,
                "cognitive_phase": result["cognitive_phase"],
                "tutor_response": tutor_response,
                "frustration_level": result["frustration_level"],
                "understanding_level": result["understanding_level"],
                "hint_count": result["hint_count"],
                "rag_context": result.get("rag_context", "")
            }
            
        except Exception as e:
            logger.error(f"Failed to send message in session {session_id}: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get full session history with N4 traceability
        
        Args:
            session_id: The tutoring session ID
        
        Returns:
            Dict with full conversation and cognitive trace
        """
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            state = await self.graph.aget_state(config)
            
            if not state:
                return {"error": "Session not found"}
            
            # Build conversation history
            conversation = []
            for msg in state.values["messages"]:
                conversation.append({
                    "role": "student" if isinstance(msg, HumanMessage) else "tutor",
                    "content": msg.content,
                    "timestamp": getattr(msg, "timestamp", None)
                })
            
            return {
                "session_id": session_id,
                "student_id": state.values["student_id"],
                "activity_id": state.values["activity_id"],
                "cognitive_phase": state.values["cognitive_phase"],
                "conversation": conversation,
                "frustration_level": state.values["frustration_level"],
                "understanding_level": state.values["understanding_level"],
                "total_interactions": state.values["total_interactions"],
                "hint_count": state.values["hint_count"],
                "created_at": state.values["created_at"],
                "updated_at": state.values["updated_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get session history: {e}", exc_info=True)
            return {"error": str(e)}
