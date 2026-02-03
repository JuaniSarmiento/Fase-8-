"""
Pytest configuration for AI-Native MVP V3 tests

Provides fixtures and configuration for all test modules with:
- Async test support
- In-memory SQLite database for fast tests
- Mock LLM providers (Mistral, Gemini, etc.)
- HTTP clients (authenticated and anonymous)
- Test data factories
"""
import asyncio
import pytest
from typing import AsyncGenerator, Dict, Any
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime

# Test database URL (usar sqlite en memoria para tests rápidos)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Import app
from backend.src_v3.infrastructure.http.app import create_app
from backend.src_v3.infrastructure.persistence.database import Base
from backend.src_v3.infrastructure.llm.base import LLMMessage, LLMResponse, LLMRole


# ==================== PYTEST CONFIGURATION ====================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM (will be mocked)"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== DATABASE FIXTURES ====================

@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        # Rollback is automatic when context exits


# ==================== HTTP CLIENT FIXTURES ====================

@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client for API testing."""
    app = create_app()
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_student_client(test_client: AsyncClient) -> AsyncClient:
    """Create an authenticated test client with student role."""
    # TODO: Implement JWT token generation for tests
    # For now, add a mock Authorization header
    test_client.headers["Authorization"] = "Bearer mock_student_token"
    test_client.headers["X-User-ID"] = "test_student_1"
    test_client.headers["X-User-Role"] = "student"
    return test_client


@pytest.fixture(scope="function")
async def authenticated_teacher_client(test_client: AsyncClient) -> AsyncClient:
    """Create an authenticated test client with teacher role."""
    test_client.headers["Authorization"] = "Bearer mock_teacher_token"
    test_client.headers["X-User-ID"] = "test_teacher_1"
    test_client.headers["X-User-Role"] = "teacher"
    return test_client


@pytest.fixture(scope="function")
async def authenticated_admin_client(test_client: AsyncClient) -> AsyncClient:
    """Create an authenticated test client with admin role."""
    test_client.headers["Authorization"] = "Bearer mock_admin_token"
    test_client.headers["X-User-ID"] = "test_admin_1"
    test_client.headers["X-User-Role"] = "admin"
    return test_client


# ==================== LLM MOCK FIXTURES ====================

@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(
        content: str = "Mocked AI response",
        model: str = "mistral-small-latest",
        prompt_tokens: int = 100,
        completion_tokens: int = 50
    ) -> LLMResponse:
        return LLMResponse(
            content=content,
            model=model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            },
            metadata={"finish_reason": "stop", "mocked": True}
        )
    return _create_response


@pytest.fixture
def mock_mistral_provider(mock_llm_response):
    """Mock MistralProvider for testing without API calls."""
    with patch("backend.src_v3.infrastructure.llm.mistral_provider.MistralProvider") as MockProvider:
        mock_instance = AsyncMock()
        
        # Configure generate method
        mock_instance.generate = AsyncMock(
            return_value=mock_llm_response(
                content="Mocked Mistral response: Excellent work on your solution!"
            )
        )
        
        # Configure generate_stream method
        async def mock_stream():
            chunks = ["Mocked ", "streaming ", "response"]
            for chunk in chunks:
                yield chunk
        
        mock_instance.generate_stream = AsyncMock(return_value=mock_stream())
        
        # Configure other methods
        mock_instance.count_tokens = MagicMock(return_value=50)
        mock_instance.supports_streaming = MagicMock(return_value=True)
        mock_instance.analyze_complexity = AsyncMock(
            return_value={"needs_pro": False, "reason": "Simple query", "confidence": 0.7}
        )
        
        MockProvider.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_exercise_generator():
    """Mock ExerciseGeneratorAgent for testing."""
    with patch("backend.src_v3.infrastructure.ai.exercise_generator.ExerciseGeneratorAgent") as MockGenerator:
        mock_instance = AsyncMock()
        
        # Configure generate method to return a mock exercise
        from backend.src_v3.core.domain.teacher.entities import GeneratedExercise, TestCase
        
        mock_exercise = GeneratedExercise(
            exercise_id=str(uuid.uuid4()),
            title="Mock Exercise: Calculate Factorial",
            description="Implement a function to calculate factorial",
            difficulty="INTERMEDIO",
            language="python",
            mission_markdown="## Mission\n\nImplement factorial function",
            starter_code="def factorial(n):\n    # TODO\n    pass",
            solution_code="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            test_cases=[
                TestCase(
                    test_number=1,
                    description="Test base case",
                    input_data="0",
                    expected_output="1",
                    is_hidden=False,
                    timeout_seconds=5
                ),
                TestCase(
                    test_number=2,
                    description="Test factorial of 5",
                    input_data="5",
                    expected_output="120",
                    is_hidden=False,
                    timeout_seconds=5
                )
            ],
            concepts=["recursion", "functions", "base case"],
            estimated_time_minutes=30,
            created_at=datetime.utcnow()
        )
        
        mock_instance.generate = AsyncMock(return_value=mock_exercise)
        
        MockGenerator.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_chroma_vector_store():
    """Mock ChromaVectorStore for testing RAG without ChromaDB."""
    with patch("backend.src_v3.infrastructure.ai.rag.chroma_store.ChromaVectorStore") as MockStore:
        mock_instance = MagicMock()
        
        # Configure query method to return mock RAG context
        mock_instance.query = MagicMock(
            return_value={
                "documents": [
                    "Fragmento 1: Las funciones en Python se definen con 'def'...",
                    "Fragmento 2: La recursión es cuando una función se llama a sí misma...",
                    "Fragmento 3: Los casos base son críticos para evitar recursión infinita..."
                ],
                "metadatas": [
                    {"source": "chapter_3.pdf", "page": 15},
                    {"source": "chapter_3.pdf", "page": 16},
                    {"source": "chapter_3.pdf", "page": 17}
                ],
                "distances": [0.2, 0.3, 0.4],
                "ids": ["doc_1", "doc_2", "doc_3"]
            }
        )
        
        mock_instance.add_documents = MagicMock()
        mock_instance.list_collections = MagicMock(return_value=["test_collection"])
        mock_instance.delete_collection = MagicMock()
        
        MockStore.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_langgraph_teacher_generator():
    """Mock TeacherGeneratorGraph for testing."""
    with patch("backend.src_v3.infrastructure.ai.teacher_generator_graph.TeacherGeneratorGraph") as MockGraph:
        mock_instance = AsyncMock()
        
        # Mock start_generation
        mock_instance.start_generation = AsyncMock(
            return_value={
                "job_id": str(uuid.uuid4()),
                "status": "generation",
                "awaiting_approval": True,
                "error": None
            }
        )
        
        # Mock get_draft
        mock_instance.get_draft = AsyncMock(
            return_value={
                "job_id": str(uuid.uuid4()),
                "status": "review",
                "draft_exercises": [
                    {
                        "title": f"Exercise {i}",
                        "description": f"Description for exercise {i}",
                        "difficulty": "medium" if i % 2 == 0 else "easy",
                        "concepts": ["concept1", "concept2"],
                        "mission_markdown": "## Mission\n\nSolve this...",
                        "starter_code": "# TODO",
                        "solution_code": "def solution(): pass",
                        "test_cases": []
                    }
                    for i in range(10)
                ],
                "awaiting_approval": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        
        # Mock approve_and_publish
        mock_instance.approve_and_publish = AsyncMock(
            return_value={
                "job_id": str(uuid.uuid4()),
                "status": "published",
                "approved_count": 10,
                "error": None
            }
        )
        
        MockGraph.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_langgraph_student_tutor():
    """Mock StudentTutorGraph for testing."""
    with patch("backend.src_v3.infrastructure.ai.student_tutor_graph.StudentTutorGraph") as MockGraph:
        mock_instance = AsyncMock()
        
        # Mock start_session
        mock_instance.start_session = AsyncMock(
            return_value={
                "session_id": str(uuid.uuid4()),
                "cognitive_phase": "exploration",
                "welcome_message": "¡Hola! Empecemos a trabajar en esta actividad...",
                "rag_context": ""
            }
        )
        
        # Mock send_message
        mock_instance.send_message = AsyncMock(
            return_value={
                "session_id": str(uuid.uuid4()),
                "cognitive_phase": "implementation",
                "tutor_response": "¿Por qué elegiste usar recursión? ¿Qué ventajas ves?",
                "frustration_level": 0.3,
                "understanding_level": 0.7,
                "hint_count": 1,
                "rag_context": "Fragmento del curso: La recursión es elegante..."
            }
        )
        
        # Mock get_session_history
        mock_instance.get_session_history = AsyncMock(
            return_value={
                "session_id": str(uuid.uuid4()),
                "student_id": "test_student_1",
                "activity_id": "test_activity_1",
                "cognitive_phase": "validation",
                "conversation": [
                    {"role": "tutor", "content": "¿Empezamos?", "timestamp": None},
                    {"role": "student", "content": "Sí, por favor", "timestamp": None}
                ],
                "frustration_level": 0.2,
                "understanding_level": 0.8,
                "total_interactions": 15,
                "hint_count": 3,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        
        MockGraph.return_value = mock_instance
        yield mock_instance


# ==================== TEST DATA FACTORIES ====================

@pytest.fixture
def create_test_user():
    """Factory for creating test users."""
    def _create_user(
        user_id: str = None,
        email: str = "test@example.com",
        role: str = "student",
        name: str = "Test User"
    ) -> Dict[str, Any]:
        return {
            "id": user_id or str(uuid.uuid4()),
            "email": email,
            "role": role,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        }
    return _create_user


@pytest.fixture
def create_test_activity():
    """Factory for creating test activities."""
    def _create_activity(
        activity_id: str = None,
        title: str = "Test Activity",
        course_id: str = "test_course_1",
        teacher_id: str = "test_teacher_1"
    ) -> Dict[str, Any]:
        return {
            "activity_id": activity_id or str(uuid.uuid4()),
            "title": title,
            "course_id": course_id,
            "teacher_id": teacher_id,
            "instructions": "Test instructions",
            "status": "active",
            "policy": "BALANCED",
            "max_ai_help_level": "MEDIO",
            "created_at": datetime.utcnow().isoformat()
        }
    return _create_activity


@pytest.fixture
def create_test_exercise():
    """Factory for creating test exercises."""
    def _create_exercise(
        exercise_id: str = None,
        title: str = "Test Exercise",
        difficulty: str = "INTERMEDIO"
    ) -> Dict[str, Any]:
        return {
            "exercise_id": exercise_id or str(uuid.uuid4()),
            "title": title,
            "description": "Test exercise description",
            "difficulty": difficulty,
            "language": "python",
            "starter_code": "# TODO",
            "solution_code": "def solution(): pass",
            "test_cases": [],
            "created_at": datetime.utcnow().isoformat()
        }
    return _create_exercise
