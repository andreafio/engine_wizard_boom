"""Unit tests for review service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.review_service import ReviewService
from app.services.review_schema import ReviewOutput
from app.wizard.state import Session
from app.wizard.schema import Blueprint, BlueprintSection, FieldStatus


@pytest.fixture
def sample_valid_review_output():
    """Sample valid review output."""
    return {
        "review": {
            "confirmed": [
                "Settore: B2B SaaS",
                "Obiettivo: Lead Generation",
                "Target: CMO"
            ],
            "to_confirm": [
                "Budget: 5k-10k (da validare)"
            ]
        }
    }


@pytest.fixture
def mock_session_with_mixed_status():
    """Mock session with both confirmed and draft fields."""
    session = MagicMock(spec=Session)
    session.session_id = "test-review-123"
    session.blueprint = MagicMock(spec=Blueprint)
    
    # Confirmed fields
    session.blueprint.context = BlueprintSection(
        value={"industry": "B2B SaaS", "business_model": "Subscription"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.objective = BlueprintSection(
        value={"primary_goal": "Lead Generation"},
        status=FieldStatus.CONFIRMED
    )
    
    # Draft fields
    session.blueprint.target_market = BlueprintSection(
        value={"target_role": "CMO"},
        status=FieldStatus.DRAFT
    )
    session.blueprint.constraints = BlueprintSection(
        value={"budget_range": "5k-10k"},
        status=FieldStatus.DRAFT
    )
    
    # Empty sections
    session.blueprint.value_prop = BlueprintSection(value={})
    session.blueprint.channels_assets = BlueprintSection(value={})
    
    return session


@pytest.fixture
def mock_session_all_confirmed():
    """Mock session with all confirmed fields."""
    session = MagicMock(spec=Session)
    session.session_id = "test-review-456"
    session.blueprint = MagicMock(spec=Blueprint)
    
    session.blueprint.context = BlueprintSection(
        value={"industry": "E-commerce"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.objective = BlueprintSection(
        value={"primary_goal": "Brand Awareness"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.target_market = BlueprintSection(value={})
    session.blueprint.value_prop = BlueprintSection(value={})
    session.blueprint.channels_assets = BlueprintSection(value={})
    session.blueprint.constraints = BlueprintSection(value={})
    
    return session


def test_review_output_schema_validates(sample_valid_review_output):
    """Test that valid review output passes Pydantic validation."""
    validated = ReviewOutput.model_validate(sample_valid_review_output)
    assert len(validated.review.confirmed) == 3
    assert len(validated.review.to_confirm) == 1
    assert validated.has_items_to_confirm() is True
    assert validated.is_ready_for_generation() is False


def test_review_output_ready_for_generation():
    """Test that review with no to_confirm items is ready."""
    output = {
        "review": {
            "confirmed": ["Item 1", "Item 2"],
            "to_confirm": []
        }
    }
    
    validated = ReviewOutput.model_validate(output)
    assert validated.is_ready_for_generation() is True
    assert validated.has_items_to_confirm() is False


def test_review_output_helper_methods():
    """Test helper methods on ReviewOutput."""
    output = ReviewOutput(
        review={
            "confirmed": ["A", "B", "C"],
            "to_confirm": ["D", "E"]
        }
    )
    
    assert output.total_items() == 5
    assert output.has_items_to_confirm() is True
    assert output.is_ready_for_generation() is False


@pytest.mark.asyncio
async def test_review_separates_confirmed_and_draft(mock_session_with_mixed_status):
    """Test that review service separates confirmed and draft items."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "review": {
            "confirmed": [
                "Settore: B2B SaaS",
                "Business Model: Subscription",
                "Obiettivo: Lead Generation"
            ],
            "to_confirm": [
                "Target: CMO (da confermare)",
                "Budget: 5k-10k (da validare)"
            ]
        }
    })
    
    service = ReviewService(mock_llm)
    result = await service.review_blueprint(mock_session_with_mixed_status)
    
    assert len(result["review"]["confirmed"]) == 3
    assert len(result["review"]["to_confirm"]) == 2


@pytest.mark.asyncio
async def test_review_all_confirmed_ready_for_generation(mock_session_all_confirmed):
    """Test that review with all confirmed items shows ready for generation."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "review": {
            "confirmed": [
                "Settore: E-commerce",
                "Obiettivo: Brand Awareness"
            ],
            "to_confirm": []
        }
    })
    
    service = ReviewService(mock_llm)
    result = await service.review_blueprint(mock_session_all_confirmed)
    
    validated = ReviewOutput.model_validate(result)
    assert validated.is_ready_for_generation() is True


@pytest.mark.asyncio
async def test_review_fallback_on_llm_failure(mock_session_with_mixed_status):
    """Test fallback behavior when LLM fails."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(side_effect=Exception("LLM error"))
    
    service = ReviewService(mock_llm)
    result = await service.review_blueprint(mock_session_with_mixed_status)
    
    # Should return fallback with manual extraction
    assert "review" in result
    assert "confirmed" in result["review"]
    assert "to_confirm" in result["review"]


@pytest.mark.asyncio
async def test_review_ignores_empty_sections(mock_session_with_mixed_status):
    """Test that review doesn't include empty sections."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "review": {
            "confirmed": [
                "Settore: B2B SaaS",
                "Obiettivo: Lead Generation"
            ],
            "to_confirm": [
                "Target: CMO"
            ]
        }
    })
    
    service = ReviewService(mock_llm)
    result = await service.review_blueprint(mock_session_with_mixed_status)
    
    # Should not include value_prop or channels_assets (empty sections)
    all_items = result["review"]["confirmed"] + result["review"]["to_confirm"]
    assert not any("value_prop" in item.lower() for item in all_items)
    assert not any("channels" in item.lower() for item in all_items)


@pytest.mark.asyncio
async def test_review_output_concise_format():
    """Test that review output is concise (1 line per item)."""
    output = {
        "review": {
            "confirmed": [
                "Settore: B2B SaaS",
                "Obiettivo: Lead Generation con focus su qualità lead"
            ],
            "to_confirm": []
        }
    }
    
    validated = ReviewOutput.model_validate(output)
    
    # Each item should be reasonably short
    for item in validated.review.confirmed:
        assert len(item) < 200  # Reasonable length for 1 line
