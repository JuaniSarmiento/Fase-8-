"""
TeacherAnalystGraph - AI Pedagogical Auditor

Analyzes student N4 traceability logs using Mistral AI to:
1. Diagnose learning difficulties (syntax, logic, or conceptual)
2. Provide evidence from interaction logs
3. Recommend specific interventions for teachers

Uses:
- LangGraph for workflow orchestration
- Mistral AI for cognitive analysis
- N4 Traceability logs as input
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TypedDict, Dict, Any, List, Optional
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_mistralai import ChatMistralAI

logger = logging.getLogger(__name__)


class AnalystState(TypedDict):
    """State for pedagogical analysis workflow"""
    # Identifiers
    analysis_id: str
    student_id: str
    teacher_id: str
    
    # Input Data
    risk_score: float  # 0.0 - 1.0
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    traceability_logs: List[Dict[str, Any]]
    
    # Student Metrics
    total_interactions: int
    error_count: int
    hint_count: int
    time_spent_seconds: int
    cognitive_phase: str
    frustration_level: float
    understanding_level: float
    
    # Analysis Output
    diagnosis: str
    evidence: List[str]
    intervention: str
    confidence_score: float  # 0.0 - 1.0
    
    # Metadata
    status: str  # analyzing, completed, error
    error_message: Optional[str]
    created_at: str
    updated_at: str


ANALYST_SYSTEM_PROMPT = """You are an expert Computer Science Pedagogical Auditor with deep expertise in:
- Cognitive Science and Learning Theory
- Programming Education Pedagogy
- Student Performance Analysis
- N4 Cognitive Framework (7 phases)

Your mission is to analyze student interaction logs and provide actionable insights for teachers.

ANALYSIS FRAMEWORK:
1. **Syntax Issues:** Typos, missing semicolons, incorrect indentation
2. **Logic Errors:** Wrong conditions, infinite loops, off-by-one errors
3. **Conceptual Gaps:** Misunderstanding of fundamental concepts (recursion, OOP, etc.)
4. **Cognitive Overload:** Too many hints needed, high frustration, stuck in early phases
5. **Behavioral Patterns:** Trial-and-error looping, copy-paste without understanding

OUTPUT REQUIREMENTS:
Generate a structured JSON assessment with:
{
  "diagnosis": "Primary issue category (syntax/logic/conceptual/overload/behavioral)",
  "diagnosis_detail": "Detailed explanation of the problem (2-3 sentences)",
  "evidence": [
    "Quote 1: Specific error or question from logs",
    "Quote 2: Pattern showing repeated behavior",
    "Quote 3: Indicator of understanding level"
  ],
  "intervention": "Specific recommendation for the teacher (actionable, concrete)",
  "intervention_priority": "immediate/high/medium/low",
  "confidence_score": 0.85
}

CRITICAL RULES:
1. Be BRUTALLY HONEST - Teachers need truth, not sugar-coating
2. Quote ACTUAL text from logs as evidence
3. Make interventions SPECIFIC and ACTIONABLE
4. If risk is HIGH, recommend immediate action
5. Consider the cognitive phase - students in "exploration" need different help than "debugging"
6. Return ONLY valid JSON (no markdown, no extra text)
"""


class TeacherAnalystGraph:
    """
    LangGraph workflow for AI-powered pedagogical analysis
    
    Analyzes student performance based on N4 traceability logs
    and generates actionable insights for teachers.
    """
    
    def __init__(
        self,
        mistral_api_key: str,
        model_name: str = "mistral-small-latest",
        temperature: float = 0.3  # Lower for more analytical
    ):
        """
        Initialize the Teacher Analyst Graph
        
        Args:
            mistral_api_key: Mistral AI API key
            model_name: Model to use (default: mistral-small-latest)
            temperature: Lower = more analytical (default: 0.3)
        """
        self.mistral_api_key = mistral_api_key
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize Mistral LLM
        self.llm = ChatMistralAI(
            api_key=mistral_api_key,
            model=model_name,
            temperature=temperature
        )
        
        # Memory for workflow persistence
        self.memory = MemorySaver()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        logger.info(
            f"TeacherAnalystGraph initialized with model={model_name}, temp={temperature}"
        )
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AnalystState)
        
        # Single analysis node
        workflow.add_node("analyze", self._analyze_node)
        
        # Set entry point
        workflow.set_entry_point("analyze")
        
        # End after analysis
        workflow.add_edge("analyze", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _analyze_node(self, state: AnalystState) -> AnalystState:
        """
        Main analysis node - calls Mistral AI to generate pedagogical assessment
        """
        try:
            logger.info(
                f"Starting analysis for student {state['student_id']}",
                extra={"risk_score": state['risk_score']}
            )
            
            state["status"] = "analyzing"
            
            # Build context from traceability logs
            logs_summary = self._summarize_logs(state["traceability_logs"])
            
            # Build prompt for Mistral
            user_prompt = f"""
STUDENT PERFORMANCE DATA:

RISK ASSESSMENT:
- Risk Score: {state['risk_score']:.2f} (0=excellent, 1=critical)
- Risk Level: {state['risk_level']}
- Cognitive Phase: {state['cognitive_phase']}
- Frustration Level: {state['frustration_level']:.2f}
- Understanding Level: {state['understanding_level']:.2f}

INTERACTION METRICS:
- Total Interactions: {state['total_interactions']}
- Errors Encountered: {state['error_count']}
- Hints Requested: {state['hint_count']}
- Time Spent: {state['time_spent_seconds']} seconds

TRACEABILITY LOGS (N4 Cognitive Journey):
{logs_summary}

---

Analyze this data and generate a comprehensive pedagogical assessment.
Focus on actionable insights that will help the teacher understand WHY this student is struggling.
"""
            
            messages = [
                SystemMessage(content=ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]
            
            # Call Mistral
            logger.info("Calling Mistral AI for analysis...")
            response = self.llm.invoke(messages)
            raw_content = response.content
            
            # Parse JSON response
            assessment = self._parse_assessment(raw_content)
            
            # Update state with analysis results
            state["diagnosis"] = assessment.get("diagnosis_detail", "Unable to diagnose")
            state["evidence"] = assessment.get("evidence", [])
            state["intervention"] = assessment.get("intervention", "Monitor student progress")
            state["confidence_score"] = assessment.get("confidence_score", 0.7)
            state["status"] = "completed"
            state["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(
                f"Analysis completed for student {state['student_id']}",
                extra={
                    "diagnosis": assessment.get("diagnosis"),
                    "confidence": state["confidence_score"]
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            state["status"] = "error"
            state["error_message"] = str(e)
            state["diagnosis"] = "Analysis error"
            state["evidence"] = []
            state["intervention"] = "Unable to generate recommendations due to system error"
            state["confidence_score"] = 0.0
            return state
    
    def _summarize_logs(self, logs: List[Dict[str, Any]]) -> str:
        """
        Summarize traceability logs for the prompt
        
        Args:
            logs: List of interaction dictionaries
            
        Returns:
            Formatted string summary
        """
        if not logs:
            return "(No interaction logs available)"
        
        # Take up to last 10 interactions
        recent_logs = logs[-10:] if len(logs) > 10 else logs
        
        summary_lines = []
        for i, log in enumerate(recent_logs, 1):
            timestamp = log.get("timestamp", "unknown")
            action = log.get("action", "unknown")
            phase = log.get("cognitive_phase", "unknown")
            details = log.get("details", "")
            
            summary_lines.append(
                f"[{i}] {timestamp} | Phase: {phase} | Action: {action}\n    Details: {details[:200]}"
            )
        
        return "\n".join(summary_lines)
    
    def _parse_assessment(self, raw_content: str) -> Dict[str, Any]:
        """
        Parse Mistral's JSON response with robust error handling
        
        Args:
            raw_content: Raw response from Mistral
            
        Returns:
            Parsed assessment dictionary
        """
        import re
        
        # Clean markdown code blocks
        cleaned = raw_content.strip()
        
        if "```json" in cleaned:
            match = re.search(r'```json\s*(.+?)\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
        elif "```" in cleaned:
            match = re.search(r'```\s*(.+?)\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
        
        # Try standard JSON parsing first
        try:
            assessment = json.loads(cleaned.strip())
            return assessment
        except json.JSONDecodeError as e:
            logger.warning(f"Standard JSON parsing failed: {e}")
            
            # Try with strict=False (allows control characters)
            try:
                assessment = json.loads(cleaned.strip(), strict=False)
                return assessment
            except:
                pass
            
            # Try to fix common issues: unescaped quotes, newlines in strings
            try:
                # Replace unescaped newlines in string values
                fixed = re.sub(
                    r'("(?:diagnosis_detail|intervention)"\s*:\s*"[^"]*)\n([^"]*")',
                    r'\1 \2',
                    cleaned,
                    flags=re.DOTALL
                )
                assessment = json.loads(fixed, strict=False)
                logger.info("Successfully parsed JSON after fixing newlines")
                return assessment
            except Exception as fix_error:
                logger.warning(f"Failed to fix JSON: {fix_error}")
            
            # Last resort: extract values with regex
            logger.warning("Attempting regex extraction as fallback")
            try:
                diagnosis_match = re.search(r'"diagnosis"\s*:\s*"([^"]+)"', cleaned)
                detail_match = re.search(r'"diagnosis_detail"\s*:\s*"(.+?)"(?=\s*[,}])', cleaned, re.DOTALL)
                evidence_match = re.search(r'"evidence"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
                intervention_match = re.search(r'"intervention"\s*:\s*"(.+?)"(?=\s*[,}])', cleaned, re.DOTALL)
                confidence_match = re.search(r'"confidence_score"\s*:\s*([0-9.]+)', cleaned)
                
                evidence_list = []
                if evidence_match:
                    evidence_str = evidence_match.group(1)
                    evidence_list = re.findall(r'"([^"]+)"', evidence_str)
                
                return {
                    "diagnosis": diagnosis_match.group(1) if diagnosis_match else "unknown",
                    "diagnosis_detail": detail_match.group(1).strip() if detail_match else "Unable to extract",
                    "evidence": evidence_list[:5],  # Limit to 5 items
                    "intervention": intervention_match.group(1).strip() if intervention_match else "Review required",
                    "confidence_score": float(confidence_match.group(1)) if confidence_match else 0.5
                }
            except Exception as regex_error:
                logger.error(f"Regex extraction failed: {regex_error}")
            
            # Absolute fallback
            return {
                "diagnosis": "parsing_error",
                "diagnosis_detail": "Unable to parse AI response",
                "evidence": [raw_content[:200]],
                "intervention": "Manual review required",
                "intervention_priority": "high",
                "confidence_score": 0.0
            }
    
    async def analyze_student(
        self,
        student_id: str,
        teacher_id: str,
        risk_score: float,
        risk_level: str,
        traceability_logs: List[Dict[str, Any]],
        cognitive_phase: str = "unknown",
        frustration_level: float = 0.5,
        understanding_level: float = 0.5
    ) -> Dict[str, Any]:
        """
        Analyze a student's performance and generate pedagogical insights
        
        Args:
            student_id: Student identifier
            teacher_id: Teacher identifier
            risk_score: Calculated risk score (0.0 - 1.0)
            risk_level: Risk category (LOW/MEDIUM/HIGH/CRITICAL)
            traceability_logs: List of interaction logs
            cognitive_phase: Current N4 phase
            frustration_level: Student frustration (0.0 - 1.0)
            understanding_level: Student understanding (0.0 - 1.0)
            
        Returns:
            Analysis results dictionary
        """
        # Calculate metrics from logs
        total_interactions = len(traceability_logs)
        error_count = sum(1 for log in traceability_logs if log.get("action") == "error")
        hint_count = sum(1 for log in traceability_logs if "hint" in str(log.get("details", "")).lower())
        time_spent = sum(log.get("duration_seconds", 0) for log in traceability_logs)
        
        # Create initial state
        initial_state = AnalystState(
            analysis_id=str(uuid.uuid4()),
            student_id=student_id,
            teacher_id=teacher_id,
            risk_score=risk_score,
            risk_level=risk_level,
            traceability_logs=traceability_logs,
            total_interactions=total_interactions,
            error_count=error_count,
            hint_count=hint_count,
            time_spent_seconds=time_spent,
            cognitive_phase=cognitive_phase,
            frustration_level=frustration_level,
            understanding_level=understanding_level,
            diagnosis="",
            evidence=[],
            intervention="",
            confidence_score=0.0,
            status="pending",
            error_message=None,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Run workflow
        config = {"configurable": {"thread_id": initial_state["analysis_id"]}}
        result = await self.workflow.ainvoke(initial_state, config)
        
        # Return analysis results
        return {
            "analysis_id": result["analysis_id"],
            "student_id": result["student_id"],
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "diagnosis": result["diagnosis"],
            "evidence": result["evidence"],
            "intervention": result["intervention"],
            "confidence_score": result["confidence_score"],
            "status": result["status"],
            "error_message": result.get("error_message"),
            "created_at": result["created_at"],
            "updated_at": result["updated_at"]
        }
