"""Unit tests for orchestrator service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator_service import OrchestratorService
from app.services.orchestrator_schema import OrchestratorOutput
from app.wizard.state import Session
from app.wizard.schema import WizardStep


@pytest.fixture
def sample_valid_orchestrator_output():
    """Sample valid orchestrator output."""
    return {
        "extracted_fields": {
            "industry": "B2B SaaS"
        },
        "field_status": {
            "industry": "confirmed"
        },
        "confidence": "high",
        "suggested_options": []
    }


@pytest.fixture
def sample_vague_orchestrator_output():
    """Sample output with suggestions when input is vague."""
    return {
        "extracted_fields": {},
        "field_status": {},
        "confidence": "low",
        "suggested_options": [
            {
                "field": "industry",
                "options": [
                    {"id": "b2b_saas", "label": "B2B SaaS"},
                    {"id": "ecommerce", "label": "E-commerce"},
                    {"id": "consulting", "label": "Consulting"}
                ]
            }
        ]
    }


@pytest.fixture
def mock_session():
    """Mock session for testing."""
    session = MagicMock(spec=Session)
    session.session_id = "test-session-456"
    session.current_step = WizardStep.CONTEXT
    session.get_blueprint_section = MagicMock(return_value=None)
    return session


def test_orchestrator_output_schema_validates(sample_valid_orchestrator_output):
    """Test that valid orchestrator output passes Pydantic validation."""
    validated = OrchestratorOutput.model_validate(sample_valid_orchestrator_output)
    assert validated.confidence == "high"
    assert validated.extracted_fields["industry"] == "B2B SaaS"
    assert validated.is_confirmed("industry")


def test_orchestrator_output_schema_validates_suggestions(sample_vague_orchestrator_output):
    """Test that output with suggestions validates correctly."""
    validated = OrchestratorOutput.model_validate(sample_vague_orchestrator_output)
    assert validated.confidence == "low"
    assert len(validated.extracted_fields) == 0
    assert len(validated.suggested_options) == 1
    assert validated.suggested_options[0].field == "industry"
    assert len(validated.suggested_options[0].options) == 3


def test_orchestrator_output_rejects_invalid_confidence():
    """Test that invalid confidence values are rejected."""
    invalid_output = {
        "extracted_fields": {"field": "value"},
        "field_status": {"field": "confirmed"},
        "confidence": "very_high",  # Invalid
        "suggested_options": []
    }
    
    with pytest.raises(Exception):  # ValidationError
        OrchestratorOutput.model_validate(invalid_output)


def test_orchestrator_output_rejects_invalid_status():
    """Test that invalid field status values are rejected."""
    invalid_output = {
        "extracted_fields": {"field": "value"},
        "field_status": {"field": "pending"},  # Invalid - must be draft/confirmed
        "confidence": "high",
        "suggested_options": []
    }
    
    with pytest.raises(Exception):  # ValidationError
        OrchestratorOutput.model_validate(invalid_output)


def test_orchestrator_output_helper_methods():
    """Test helper methods on OrchestratorOutput."""
    output = OrchestratorOutput(
        extracted_fields={"field1": "value1", "field2": "value2"},
        field_status={"field1": "confirmed", "field2": "draft"},
        confidence="medium",
        suggested_options=[]
    )
    
    assert output.is_confirmed("field1") is True
    assert output.is_confirmed("field2") is False
    assert output.get_value("field1") == "value1"
    assert output.get_value("field2") == "value2"
    assert output.get_value("field3") is None


@pytest.mark.asyncio
async def test_orchestrator_extracts_explicit_value(mock_session):
    """Test orchestrator extracts explicitly stated value."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "extracted_fields": {"industry": "B2B SaaS"},
        "field_status": {"industry": "confirmed"},
        "confidence": "high",
        "suggested_options": []
    })
    
    service = OrchestratorService(mock_llm)
    result = await service.extract_field(
        user_message="We are a B2B SaaS company",
        session=mock_session,
        expected_field="industry"
    )
    
    assert result["extracted_fields"]["industry"] == "B2B SaaS"
    assert result["field_status"]["industry"] == "confirmed"
    assert result["confidence"] == "high"


@pytest.mark.asyncio
async def test_orchestrator_marks_vague_input_as_draft(mock_session):
    """Test that vague input is marked as draft."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "extracted_fields": {"industry": "SaaS"},
        "field_status": {"industry": "draft"},
        "confidence": "medium",
        "suggested_options": []
    })
    
    service = OrchestratorService(mock_llm)
    result = await service.extract_field(
        user_message="We sell software",
        session=mock_session,
        expected_field="industry"
    )
    
    assert result["field_status"]["industry"] == "draft"
    assert result["confidence"] in ["medium", "low"]


@pytest.mark.asyncio
async def test_orchestrator_suggests_options_when_unclear(mock_session):
    """Test that orchestrator provides suggestions when input is unclear."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "extracted_fields": {},
        "field_status": {},
        "confidence": "low",
        "suggested_options": [
            {
                "field": "industry",
                "options": [
                    {"id": "b2b", "label": "B2B"},
                    {"id": "b2c", "label": "B2C"}
                ]
            }
        ]
    })
    
    service = OrchestratorService(mock_llm)
    result = await service.extract_field(
        user_message="We work with customers",
        session=mock_session,
        expected_field="industry"
    )
    
    assert len(result["suggested_options"]) > 0
    assert result["confidence"] == "low"


@pytest.mark.asyncio
async def test_orchestrator_does_not_invent_metrics(mock_session):
    """Test that orchestrator doesn't invent numeric data."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "extracted_fields": {},
        "field_status": {},
        "confidence": "low",
        "suggested_options": []
    })
    
    service = OrchestratorService(mock_llm)
    result = await service.extract_field(
        user_message="We want to improve our marketing",
        session=mock_session,
        expected_field="kpi_target"
    )
    
    # Should NOT invent CPL/CAC/ROI values
    extracted = result.get("extracted_fields", {})
    assert "kpi_target" not in extracted or not extracted["kpi_target"]


@pytest.mark.asyncio
async def test_orchestrator_fallback_on_llm_failure(mock_session):
    """Test fallback behavior when LLM fails."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(side_effect=Exception("LLM error"))
    
    service = OrchestratorService(mock_llm)
    result = await service.extract_field(
        user_message="Test input",
        session=mock_session,
        expected_field="industry"
    )
    
    # Should return fallback with draft status
    assert result["extracted_fields"]["industry"] == "Test input"
    assert result["field_status"]["industry"] == "draft"
    assert result["confidence"] == "low"
