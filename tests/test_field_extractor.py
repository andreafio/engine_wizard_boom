"""
Test Field Extractor Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.field_extractor_service import FieldExtractorService, FieldExtractionResult


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    llm = MagicMock()
    llm.generate_json = AsyncMock()
    return llm


@pytest.fixture
def extractor_service(mock_llm):
    """Field extractor service instance"""
    return FieldExtractorService(mock_llm)


@pytest.mark.asyncio
async def test_extract_single_select_field(extractor_service, mock_llm):
    """Test extracting single select field"""
    # Mock LLM response
    mock_llm.generate_json.return_value = {
        "field": "context.industry",
        "value": "b2b",
        "status": "confirmed",
        "confidence": 0.9,
        "evidence": "user said 'azienda B2B'",
        "needs_clarification": False,
        "suggested_clarifier": None
    }

    result = await extractor_service.extract_field(
        current_section="Context",
        current_field="context.industry",
        ui_type="single_select",
        options=[{"id": "b2b", "label": "B2B"}, {"id": "b2c", "label": "B2C"}],
        user_message="Siamo una azienda B2B nel settore tech",
        blueprint_snippet={"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
    )

    assert result.field == "context.industry"
    assert result.value == "b2b"
    assert result.status == "confirmed"
    assert result.confidence == 0.9
    assert not result.needs_clarification


@pytest.mark.asyncio
async def test_extract_ambiguous_field(extractor_service, mock_llm):
    """Test extracting ambiguous field returns draft with clarifier"""
    # Mock LLM response for ambiguous answer
    mock_llm.generate_json.return_value = {
        "field": "context.industry",
        "value": None,
        "status": "draft",
        "confidence": 0.3,
        "evidence": "user said 'non so esattamente'",
        "needs_clarification": True,
        "suggested_clarifier": {
            "ui_type": "single_select",
            "label": "Qual è il tuo settore principale?",
            "options": [
                {"id": "tech", "label": "Tecnologia"},
                {"id": "finance", "label": "Finanza"},
                {"id": "other", "label": "Altro"}
            ]
        }
    }

    result = await extractor_service.extract_field(
        current_section="Context",
        current_field="context.industry",
        ui_type="single_select",
        options=[{"id": "tech", "label": "Tecnologia"}],
        user_message="Non so esattamente, forse tech o qualcosa del genere",
        blueprint_snippet={"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
    )

    assert result.field == "context.industry"
    assert result.value is None
    assert result.status == "draft"
    assert result.confidence == 0.3
    assert result.needs_clarification
    assert result.suggested_clarifier is not None
    assert result.suggested_clarifier.ui_type == "single_select"


@pytest.mark.asyncio
async def test_extract_uncertainty_reduces_confidence(extractor_service, mock_llm):
    """Test that uncertainty expressions reduce confidence"""
    # Mock LLM response with high confidence
    mock_llm.generate_json.return_value = {
        "field": "context.industry",
        "value": "tech",
        "status": "confirmed",
        "confidence": 0.8,
        "evidence": "user mentioned tech",
        "needs_clarification": False,
        "suggested_clarifier": None
    }

    result = await extractor_service.extract_field(
        current_section="Context",
        current_field="context.industry",
        ui_type="single_select",
        options=[{"id": "tech", "label": "Tecnologia"}],
        user_message="Boh, forse siamo nel tech",  # Contains uncertainty
        blueprint_snippet={"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
    )

    # Confidence should be reduced due to uncertainty
    assert result.confidence == 0.4
    assert "user expressed uncertainty" in result.evidence


@pytest.mark.asyncio
async def test_extract_text_field(extractor_service, mock_llm):
    """Test extracting text field"""
    mock_llm.generate_json.return_value = {
        "field": "context.description",
        "value": "Vendiamo software per aziende",
        "status": "confirmed",
        "confidence": 0.85,
        "evidence": "direct quote from user",
        "needs_clarification": False,
        "suggested_clarifier": None
    }

    result = await extractor_service.extract_field(
        current_section="Context",
        current_field="context.description",
        ui_type="long_text",
        options=[],
        user_message="Vendiamo software per aziende nel settore healthcare",
        blueprint_snippet={"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
    )

    assert result.field == "context.description"
    assert result.value == "Vendiamo software per aziende"
    assert result.status == "confirmed"
    assert result.confidence == 0.85


@pytest.mark.asyncio
async def test_extract_fallback_on_error(extractor_service, mock_llm):
    """Test fallback behavior when LLM fails"""
    # Mock LLM to raise exception
    mock_llm.generate_json.side_effect = Exception("LLM error")

    result = await extractor_service.extract_field(
        current_section="Context",
        current_field="context.industry",
        ui_type="single_select",
        options=[],
        user_message="Some message",
        blueprint_snippet={"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
    )

    # Should return safe fallback
    assert result.field == "context.industry"
    assert result.value is None
    assert result.status == "draft"
    assert result.confidence == 0.0
    assert result.needs_clarification
    assert result.suggested_clarifier is not None
    assert result.suggested_clarifier.ui_type == "short_text"


@pytest.mark.asyncio
async def test_extract_multi_select_field(extractor_service, mock_llm):
    """Test extracting multi-select field"""
    mock_llm.generate_json.return_value = {
        "field": "channels.primary",
        "value": ["social", "email"],
        "status": "confirmed",
        "confidence": 0.9,
        "evidence": "user mentioned social media and email",
        "needs_clarification": False,
        "suggested_clarifier": None
    }

    result = await extractor_service.extract_field(
        current_section="Channels",
        current_field="channels.primary",
        ui_type="multi_select",
        options=[
            {"id": "social", "label": "Social Media"},
            {"id": "email", "label": "Email Marketing"},
            {"id": "seo", "label": "SEO"}
        ],
        user_message="Usiamo social media e email marketing principalmente",
        blueprint_snippet={"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
    )

    assert result.field == "channels.primary"
    assert result.value == ["social", "email"]
    assert result.status == "confirmed"
    assert result.confidence == 0.9
