"""
Test Orchestrator Service V2
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator_service_v2 import (
    OrchestratorServiceV2,
    TurnInput,
    TurnOutput,
    SessionStore
)
from app.services.orchestrator_utils import QUESTION_BANK


class MockSessionStore(SessionStore):
    """Mock session store for testing"""

    def __init__(self):
        self.sessions = {}
        self.idempotent_cache = {}

    async def get_session(self, session_id: str, tenant_id: str) -> dict:
        return self.sessions.get(session_id, {
            "blueprint": {},
            "current_section": "Context"
        })

    async def put_session(self, session_id: str, tenant_id: str, session: dict) -> None:
        self.sessions[session_id] = session

    async def get_idempotent(self, session_id: str, event_id: str) -> dict:
        return self.idempotent_cache.get(f"{session_id}:{event_id}")

    async def put_idempotent(self, session_id: str, event_id: str, result: dict) -> None:
        self.idempotent_cache[f"{session_id}:{event_id}"] = result


@pytest.fixture
def mock_session_store():
    """Mock session store"""
    return MockSessionStore()


@pytest.fixture
def mock_services():
    """Mock all required services"""
    field_extractor = MagicMock()
    field_extractor.extract_field = AsyncMock()

    clarifier = MagicMock()
    clarifier.generate_clarifier = AsyncMock()

    critic = MagicMock()
    critic.critique_answer = AsyncMock()

    review = MagicMock()
    review.build_review = AsyncMock()

    profile = MagicMock()
    profile.generate_internal_profile = AsyncMock()

    return {
        "field_extractor": field_extractor,
        "clarifier": clarifier,
        "critic": critic,
        "review": review,
        "profile": profile
    }


@pytest.fixture
def orchestrator(mock_session_store, mock_services):
    """Orchestrator service instance"""
    return OrchestratorServiceV2(
        session_store=mock_session_store,
        field_extractor_service=mock_services["field_extractor"],
        clarifier_service=mock_services["clarifier"],
        quality_critic_service=mock_services["critic"],
        blueprint_review_service=mock_services["review"],
        strategic_profile_service=mock_services["profile"]
    )


@pytest.mark.asyncio
async def test_handle_turn_ui_event(orchestrator, mock_session_store, mock_services):
    """Test handling UI event input"""
    payload = TurnInput(
        session_id="test-session",
        event_id="test-event",
        ui_event={
            "field": "context.industry",
            "value": "technology",
            "ui_type": "single_select"
        }
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    assert isinstance(result, TurnOutput)
    assert "assistant_message" in result.__dict__
    assert "wizard" in result.__dict__
    assert result.wizard["current_section"] in QUESTION_BANK.keys()


@pytest.mark.asyncio
async def test_handle_turn_free_text_extraction(orchestrator, mock_session_store, mock_services):
    """Test handling free text with field extraction"""
    # Mock successful extraction
    mock_services["field_extractor"].extract_field.return_value = {
        "field": "context.industry",
        "value": "technology",
        "needs_clarification": False,
        "evidence": "extracted from text"
    }

    # Mock quality critique
    mock_services["critic"].critique_answer.return_value = MagicMock(
        recommend_deep_followup=False,
        followup_field=None,
        reason="good quality"
    )

    payload = TurnInput(
        session_id="test-session",
        event_id="test-event",
        user_message="We work in technology sector"
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    assert isinstance(result, TurnOutput)
    mock_services["field_extractor"].extract_field.assert_called_once()


@pytest.mark.asyncio
async def test_handle_turn_clarification_needed(orchestrator, mock_session_store, mock_services):
    """Test handling when clarification is needed"""
    # Mock extraction that needs clarification
    mock_services["field_extractor"].extract_field.return_value = {
        "field": "context.industry",
        "value": "tech",
        "needs_clarification": True,
        "evidence": "ambiguous"
    }

    # Mock clarifier response
    mock_services["clarifier"].generate_clarifier.return_value = {
        "type": "clarification",
        "field": "context.industry",
        "options": [
            {"id": "technology", "label": "Technology"},
            {"id": "telecom", "label": "Telecommunications"}
        ]
    }

    payload = TurnInput(
        session_id="test-session",
        event_id="test-event",
        user_message="We work in tech"
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    assert isinstance(result, TurnOutput)
    assert "clarification" in str(result.wizard["ui"]["type"]).lower()
    mock_services["clarifier"].generate_clarifier.assert_called_once()


@pytest.mark.asyncio
async def test_handle_turn_review_phase(orchestrator, mock_session_store, mock_services):
    """Test handling review phase transition"""
    # Set up session with completed blueprint
    session = {
        "blueprint": {
            "context": {"industry": {"value": "technology"}},
            "objective": {"goal": {"value": "grow business"}},
            "risks": {"main_risk": {"value": "competition"}},  # Complete one field in Risks
            # ... assume all other fields completed
        },
        "current_section": "Risks"  # Last section
    }
    mock_session_store.sessions["test-session"] = session

    # Mock review service
    mock_services["review"].build_review.return_value = {
        "confirmed": ["Context: industry confirmed"],
        "draft_to_confirm": [],
        "missing": []
    }

    payload = TurnInput(
        session_id="test-session",
        event_id="test-event",
        ui_event={
            "field": "risks.unknowns",
            "value": "market changes and new competitors",
            "ui_type": "long_text"
        }
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    # Should transition to Review phase
    assert result.wizard["current_section"] == "Review"
    assert "confirmation" in result.wizard["ui"]["type"]
    mock_services["review"].build_review.assert_called_once()


@pytest.mark.asyncio
async def test_handle_generate_internal(orchestrator, mock_session_store, mock_services):
    """Test internal profile generation"""
    # Set up session with blueprint
    session = {
        "blueprint": {
            "context": {"industry": {"value": "technology"}},
            "objective": {"goal": {"value": "grow business"}}
        }
    }
    mock_session_store.sessions["test-session"] = session

    # Mock profile generation
    mock_services["profile"].generate_internal_profile.return_value = {
        "summary": "Tech company growth strategy",
        "profile": {},
        "assumptions": [],
        "open_questions": [],
        "recommended_actions": [],
        "confidence_map": {}
    }

    result = await orchestrator.handle_generate_internal(
        "test-tenant", "test-session", "test-event"
    )

    assert isinstance(result, dict)
    assert "summary" in result
    mock_services["profile"].generate_internal_profile.assert_called_once()


@pytest.mark.asyncio
async def test_idempotency(orchestrator, mock_session_store):
    """Test idempotency handling"""
    # Cache a result
    cached_result = {"assistant_message": "cached", "wizard": {}}
    mock_session_store.idempotent_cache["test-session:test-event"] = cached_result

    payload = TurnInput(
        session_id="test-session",
        event_id="test-event"
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    assert result.__dict__ == cached_result


@pytest.mark.asyncio
async def test_progress_calculation(orchestrator, mock_session_store):
    """Test progress calculation in responses"""
    payload = TurnInput(
        session_id="test-session",
        event_id="test-event",
        ui_event={
            "field": "context.industry",
            "value": "technology",
            "ui_type": "single_select"
        }
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    assert "progress" in result.wizard
    assert isinstance(result.wizard["progress"], float)
    assert 0.0 <= result.wizard["progress"] <= 1.0


@pytest.mark.asyncio
async def test_wizard_response_structure(orchestrator, mock_session_store):
    """Test wizard response structure"""
    payload = TurnInput(
        session_id="test-session",
        event_id="test-event",
        ui_event={
            "field": "context.industry",
            "value": "technology",
            "ui_type": "single_select"
        }
    )

    result = await orchestrator.handle_turn("test-tenant", payload)

    required_keys = ["current_section", "progress", "blueprint", "ui", "validation", "events"]
    for key in required_keys:
        assert key in result.wizard

    assert "assistant_message" in result.__dict__
    assert isinstance(result.wizard["events"], list)