"""
LangGraph State Graph for Socratic Tutor Flow

Implements the learning cycle with state transitions.
"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import operator


class TutorState(TypedDict):
    """State for tutor interaction graph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    cognitive_phase: str
    student_id: str
    session_id: str
    activity_id: str
    frustration_level: float
    understanding_level: float
    rag_context: str


def create_tutor_graph():
    """
    Create LangGraph state graph for tutor flow.
    
    Phases:
    1. EXPLORATION - Student explores problem space
    2. DECOMPOSITION - Break down problem
    3. PLANNING - Create solution plan
    4. IMPLEMENTATION - Write code
    5. DEBUGGING - Fix issues
    6. VALIDATION - Test and verify
    7. REFLECTION - Learn from experience
    """
    
    workflow = StateGraph(TutorState)
    
    # Define nodes (each phase has a node)
    workflow.add_node("exploration", exploration_node)
    workflow.add_node("decomposition", decomposition_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("implementation", implementation_node)
    workflow.add_node("debugging", debugging_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("reflection", reflection_node)
    
    # Define edges (transitions between phases)
    workflow.add_edge("exploration", "decomposition")
    workflow.add_edge("decomposition", "planning")
    workflow.add_edge("planning", "implementation")
    workflow.add_edge("implementation", "debugging")
    workflow.add_edge("debugging", "validation")
    workflow.add_edge("validation", "reflection")
    workflow.add_edge("reflection", END)
    
    # Set entry point
    workflow.set_entry_point("exploration")
    
    return workflow.compile()


# Node implementations
def exploration_node(state: TutorState) -> TutorState:
    """Exploration phase - understand the problem"""
    state["cognitive_phase"] = "exploration"
    return state


def decomposition_node(state: TutorState) -> TutorState:
    """Decomposition phase - break down problem"""
    state["cognitive_phase"] = "decomposition"
    return state


def planning_node(state: TutorState) -> TutorState:
    """Planning phase - create solution strategy"""
    state["cognitive_phase"] = "planning"
    return state


def implementation_node(state: TutorState) -> TutorState:
    """Implementation phase - write code"""
    state["cognitive_phase"] = "implementation"
    return state


def debugging_node(state: TutorState) -> TutorState:
    """Debugging phase - fix errors"""
    state["cognitive_phase"] = "debugging"
    return state


def validation_node(state: TutorState) -> TutorState:
    """Validation phase - test solution"""
    state["cognitive_phase"] = "validation"
    return state


def reflection_node(state: TutorState) -> TutorState:
    """Reflection phase - learn from experience"""
    state["cognitive_phase"] = "reflection"
    return state
