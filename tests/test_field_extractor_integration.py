"""
Integration test for Field Extractor in Orchestrator
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator_service import OrchestratorService
from app.wizard.state import Session
from app.wizard.schema import WizardStep


@pytest.mark.asyncio
async def test_orchestrator_uses_field_extractor_for_full_paths():
    """Test that orchestrator uses FieldExtractorService for full field paths."""
    # Mock LLM for field extractor (quality critic is now rule-based)
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        # Field extraction result
        "field": "context.industry",
        "value": "b2b",
        "status": "confirmed",
        "confidence": 0.9,
        "evidence": "user said 'azienda B2B'",
        "needs_clarification": False,
        "suggested_clarifier": None
    })

    service = OrchestratorService(mock_llm)

    # Mock session
    mock_session = MagicMock(spec=Session)
    mock_session.current_step = WizardStep.CONTEXT
    mock_session.get_blueprint_section.return_value = None  # No existing data

    # Test with full field path
    result = await service.extract_field(
        user_message="Siamo una azienda B2B nel settore tech",
        session=mock_session,
        expected_field="context.industry"
    )

    # Should use field extractor and convert to legacy format
    assert result["extracted_fields"]["context.industry"] == "b2b"
    assert result["field_status"]["context.industry"] == "confirmed"
    assert result["confidence"] == "high"  # 0.9 -> high

    # Verify field extractor was called once (extraction only, critique is rule-based)
    assert mock_llm.generate_json.call_count == 1


@pytest.mark.asyncio
async def test_orchestrator_fallback_to_legacy_for_simple_fields():
    """Test that orchestrator falls back to legacy extraction for simple field names."""
    # Mock LLM for legacy orchestrator
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "extracted_fields": {"industry": "B2B SaaS"},
        "field_status": {"industry": "confirmed"},
        "confidence": "high",
        "suggested_options": []
    })

    service = OrchestratorService(mock_llm)

    # Mock session
    mock_session = MagicMock(spec=Session)
    mock_session.current_step = WizardStep.CONTEXT
    mock_session.get_blueprint_section.return_value = None

    # Test with simple field name (no dot)
    result = await service.extract_field(
        user_message="We are a B2B SaaS company",
        session=mock_session,
        expected_field="industry"
    )

    # Should use legacy extraction
    assert result["extracted_fields"]["industry"] == "B2B SaaS"
    assert result["field_status"]["industry"] == "confirmed"
    assert result["confidence"] == "high"
