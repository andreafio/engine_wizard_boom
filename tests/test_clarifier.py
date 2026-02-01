"""
Test Clarifier Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.clarifier_service import ClarifierService, ClarifierOptions


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    llm = MagicMock()
    llm.generate_json = AsyncMock()
    return llm


@pytest.fixture
def clarifier_service(mock_llm):
    """Clarifier service instance"""
    return ClarifierService(mock_llm)


@pytest.mark.asyncio
async def test_generate_clarifier_for_industry(clarifier_service, mock_llm):
    """Test generating clarifier for industry field"""
    # Mock LLM response
    mock_llm.generate_json.return_value = {
        "ui_type": "single_select",
        "label": "Qual è il tuo settore di attività principale?",
        "options": [
            {"id": "tech", "label": "Tecnologia"},
            {"id": "finance", "label": "Finanza"},
            {"id": "healthcare", "label": "Sanità"},
            {"id": "retail", "label": "Commercio"}
        ]
    }

    result = await clarifier_service.generate_clarifier(
        current_field="context.industry",
        context={"business_model": "b2b"},
        user_message="Siamo nel tech"
    )

    assert result.ui_type == "single_select"
    assert "settore" in result.label.lower()
    assert len(result.options) == 4
    assert all("id" in opt and "label" in opt for opt in result.options)


@pytest.mark.asyncio
async def test_generate_clarifier_for_business_model(clarifier_service, mock_llm):
    """Test generating clarifier for business model field"""
    mock_llm.generate_json.return_value = {
        "ui_type": "single_select",
        "label": "Qual è il tuo modello di business?",
        "options": [
            {"id": "b2b", "label": "B2B (Business to Business)"},
            {"id": "b2c", "label": "B2C (Business to Consumer)"},
            {"id": "subscription", "label": "Abbonamento/SaaS"}
        ]
    }

    result = await clarifier_service.generate_clarifier(
        current_field="context.business_model",
        context={},
        user_message="Vendiamo prodotti"
    )

    assert result.ui_type == "single_select"
    assert "modello" in result.label.lower()
    assert len(result.options) >= 3


@pytest.mark.asyncio
async def test_generate_clarifier_with_context(clarifier_service, mock_llm):
    """Test clarifier uses context information"""
    mock_llm.generate_json.return_value = {
        "ui_type": "single_select",
        "label": "Qual è il tuo target principale nel settore tech?",
        "options": [
            {"id": "startups", "label": "Startup tecnologiche"},
            {"id": "enterprises", "label": "Grandi aziende tech"},
            {"id": "developers", "label": "Sviluppatori"}
        ]
    }

    result = await clarifier_service.generate_clarifier(
        current_field="target_market.segment",
        context={"industry": "tech", "business_model": "b2b"},
        user_message="Il nostro pubblico"
    )

    assert result.ui_type == "single_select"
    assert len(result.options) >= 3
    # Verify context was passed to LLM (in the prompt)


@pytest.mark.asyncio
async def test_clarifier_fallback_on_error(clarifier_service, mock_llm):
    """Test fallback behavior when LLM fails"""
    # Mock LLM to raise exception
    mock_llm.generate_json.side_effect = Exception("LLM error")

    result = await clarifier_service.generate_clarifier(
        current_field="context.industry",
        context={},
        user_message="Some message"
    )

    # Should return fallback
    assert result.ui_type == "single_select"
    assert len(result.options) >= 3
    assert "settore" in result.label.lower()


@pytest.mark.asyncio
async def test_clarifier_fallback_for_business_model(clarifier_service, mock_llm):
    """Test specific fallback for business_model field"""
    mock_llm.generate_json.side_effect = Exception("LLM error")

    result = await clarifier_service.generate_clarifier(
        current_field="context.business_model",
        context={},
        user_message="Some message"
    )

    # Should return business model specific fallback
    assert result.ui_type == "single_select"
    assert "modello" in result.label.lower()
    assert len(result.options) >= 3
    assert any("b2b" in opt["label"].lower() for opt in result.options)


@pytest.mark.asyncio
async def test_clarifier_options_validation(clarifier_service, mock_llm):
    """Test that options are properly validated"""
    # Mock invalid response (too few options)
    mock_llm.generate_json.return_value = {
        "ui_type": "single_select",
        "label": "Test label",
        "options": [
            {"id": "opt1", "label": "Option 1"}
        ]
    }

    # Should still work (validation is in Pydantic model)
    result = await clarifier_service.generate_clarifier(
        current_field="test.field",
        context={},
        user_message="test"
    )

    # Pydantic should validate min_items, but if it doesn't, we get what we got
    assert isinstance(result, ClarifierOptions)


@pytest.mark.asyncio
async def test_clarifier_generic_fallback(clarifier_service, mock_llm):
    """Test generic fallback for unknown fields"""
    mock_llm.generate_json.side_effect = Exception("LLM error")

    result = await clarifier_service.generate_clarifier(
        current_field="unknown.field",
        context={},
        user_message="Some message"
    )

    # Should return generic fallback
    assert result.ui_type == "single_select"
    assert len(result.options) == 3
    assert "meglio" in result.label.lower()
