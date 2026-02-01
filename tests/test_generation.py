"""Unit tests for generation service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.generation_service import GenerationService
from app.llm.schemas import GenerationOutput
from app.wizard.state import Session
from app.wizard.schema import Blueprint, BlueprintSection, FieldStatus


@pytest.fixture
def sample_valid_output():
    """Sample valid generation output."""
    return {
        "slides": [
            {"title": "Slide 1", "bullets": ["Point 1", "Point 2", "Point 3"]},
            {"title": "Slide 2", "bullets": ["Point A", "Point B", "Point C"]},
            {"title": "Slide 3", "bullets": ["Item 1", "Item 2", "Item 3"]},
            {"title": "Slide 4", "bullets": ["Detail 1", "Detail 2", "Detail 3"]},
            {"title": "Slide 5", "bullets": ["Info 1", "Info 2", "Info 3"]},
            {"title": "Slide 6", "bullets": ["Note 1", "Note 2", "Note 3"]},
        ],
        "report_sections": [
            {"title": "Executive Summary", "content": "Summary text here with sufficient length"},
            {"title": "Context", "content": "Context analysis with details"},
            {"title": "Insights", "content": "Key insights from the blueprint"},
            {"title": "Recommendations", "content": "Actionable recommendations"},
            {"title": "Next Steps", "content": "Next steps and timeline"}
        ],
        "assumptions": ["Assumption 1", "Assumption 2"],
        "next_steps": ["Step 1", "Step 2", "Step 3"]
    }


@pytest.fixture
def blueprint_no_metrics():
    """Blueprint without any quantitative metrics."""
    return {
        "context": {
            "industry": "B2B SaaS",
            "business_model": "Subscription",
            "company_size": "Startup"
        },
        "objective": {
            "primary_goal": "Brand Awareness"
        },
        "target_market": {
            "target_role": "Marketing Manager",
            "geo_scope": "Italia"
        },
        "value_prop": {
            "offer_type": "Software Platform",
            "key_problem": "Manual processes"
        }
    }


@pytest.fixture
def blueprint_with_metrics():
    """Blueprint with quantitative metrics."""
    return {
        "context": {
            "industry": "E-commerce",
            "business_model": "B2C",
            "company_size": "Scale-up"
        },
        "objective": {
            "primary_goal": "Lead Generation",
            "goal_note": "Target CPL: 25€, CAC: 150€, Conversion rate: 5%"
        },
        "target_market": {
            "target_role": "End Consumer",
            "geo_scope": "Italia + DACH"
        }
    }


@pytest.fixture
def mock_session_no_metrics():
    """Mock session without metrics (no numbers or KPIs)."""
    session = MagicMock(spec=Session)
    session.session_id = "test-session-123"
    session.blueprint = Blueprint()
    
    # Setup blueprint sections - NO NUMERIC DATA
    session.blueprint.context = BlueprintSection(
        value={"industry": "SaaS", "business_model": "Subscription"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.objective = BlueprintSection(
        value={"primary_goal": "Brand Awareness"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.target_market = BlueprintSection(
        value={"target_role": "Manager", "geo_scope": "Italia"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.value_prop = BlueprintSection(
        value={"offer_type": "Software Platform"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.channels_assets = BlueprintSection(value={})
    session.blueprint.constraints = BlueprintSection(value={})
    
    return session


def test_generation_output_schema_validates(sample_valid_output):
    """Test that valid output passes Pydantic validation."""
    validated = GenerationOutput.model_validate(sample_valid_output)
    assert len(validated.slides) == 6
    assert len(validated.report_sections) == 5
    assert len(validated.next_steps) == 3


def test_generation_output_rejects_invalid_slides():
    """Test that invalid slides (too few bullets) are rejected."""
    invalid_output = {
        "slides": [
            {"title": "Slide 1", "bullets": ["Only one bullet"]},  # Invalid: needs 3-5
        ],
        "report_sections": [
            {"title": "Summary", "content": "Content here"}
        ],
        "assumptions": [],
        "next_steps": ["Step 1", "Step 2", "Step 3"]
    }
    
    with pytest.raises(Exception):  # ValidationError
        GenerationOutput.model_validate(invalid_output)


def test_generation_output_enforces_bullet_length():
    """Test that bullets over 140 chars are truncated."""
    long_bullet = "This is an extremely long bullet point that exceeds the maximum allowed character limit of 140 characters and should be automatically truncated to fit"
    
    output = {
        "slides": [
            {"title": "Test 1", "bullets": [long_bullet, "Bullet 2", "Bullet 3"]},
            {"title": "Test 2", "bullets": ["A", "B", "C"]},
            {"title": "Test 3", "bullets": ["D", "E", "F"]},
            {"title": "Test 4", "bullets": ["G", "H", "I"]},
            {"title": "Test 5", "bullets": ["J", "K", "L"]},
            {"title": "Test 6", "bullets": ["M", "N", "O"]},
        ],
        "report_sections": [
            {"title": "Summary", "content": "Content here with sufficient length"},
            {"title": "Context", "content": "Context content"},
            {"title": "Insights", "content": "Insights content"},
            {"title": "Actions", "content": "Actions content"},
            {"title": "Next", "content": "Next steps content"}
        ],
        "assumptions": [],
        "next_steps": ["Step 1", "Step 2", "Step 3"]
    }
    
    validated = GenerationOutput.model_validate(output)
    assert all(len(bullet) <= 140 for bullet in validated.slides[0].bullets)


def test_generation_output_removes_duplicate_bullets():
    """Test that duplicate bullets are removed."""
    output = {
        "slides": [
            {"title": "Test 1", "bullets": ["Point 1", "Point 1", "Point 2", "Point 3"]},
            {"title": "Test 2", "bullets": ["A", "B", "C"]},
            {"title": "Test 3", "bullets": ["D", "E", "F"]},
            {"title": "Test 4", "bullets": ["G", "H", "I"]},
            {"title": "Test 5", "bullets": ["J", "K", "L"]},
            {"title": "Test 6", "bullets": ["M", "N", "O"]},
        ],
        "report_sections": [
            {"title": "Summary", "content": "Content here with sufficient length"},
            {"title": "Context", "content": "Context content"},
            {"title": "Insights", "content": "Insights content"},
            {"title": "Actions", "content": "Actions content"},
            {"title": "Next", "content": "Next steps content"}
        ],
        "assumptions": [],
        "next_steps": ["Step 1", "Step 2", "Step 3"]
    }
    
    validated = GenerationOutput.model_validate(output)
    bullets = validated.slides[0].bullets
    assert len(bullets) == len(set(b.lower() for b in bullets))


@pytest.mark.asyncio
async def test_assumptions_added_when_no_metrics(mock_session_no_metrics):
    """Test that assumptions are added when blueprint lacks metrics."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "slides": [
            {"title": "Slide 1", "bullets": ["A", "B", "C"]},
            {"title": "Slide 2", "bullets": ["D", "E", "F"]},
            {"title": "Slide 3", "bullets": ["G", "H", "I"]},
            {"title": "Slide 4", "bullets": ["J", "K", "L"]},
            {"title": "Slide 5", "bullets": ["M", "N", "O"]},
            {"title": "Slide 6", "bullets": ["P", "Q", "R"]},
        ],
        "report_sections": [
            {"title": "Summary", "content": "Summary content here"},
            {"title": "Context", "content": "Context content"},
            {"title": "Insights", "content": "Insights content"},
            {"title": "Actions", "content": "Actions content"},
            {"title": "Next", "content": "Next steps content"}
        ],
        "assumptions": [],
        "next_steps": ["Step 1", "Step 2", "Step 3"]
    })
    
    service = GenerationService(mock_llm)
    result = await service.generate_output(mock_session_no_metrics)
    
    # Should have added assumption about missing metrics
    assert len(result["assumptions"]) > 0
    assert any("quantitativ" in a.lower() or "kpi" in a.lower() 
              for a in result["assumptions"])


@pytest.mark.asyncio
async def test_fallback_on_bad_llm_response(mock_session_no_metrics):
    """Test that fallback is used when LLM returns invalid JSON."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value="NOT VALID JSON AT ALL")
    
    service = GenerationService(mock_llm)
    result = await service.generate_output(mock_session_no_metrics)
    
    # Should return valid fallback output
    validated = GenerationOutput.model_validate(result)
    assert len(validated.slides) >= 6
    assert "fallback" in str(result["assumptions"]).lower()


@pytest.mark.asyncio
async def test_invented_numbers_moved_to_assumptions(mock_session_no_metrics):
    """Test that bullets with invented numbers are flagged."""
    mock_llm = AsyncMock()
    mock_llm.generate_json = AsyncMock(return_value={
        "slides": [
            {"title": "Slide 1", "bullets": ["CPL target: 25€", "CAC: 150€", "ROI: 300%"]},
            {"title": "Slide 2", "bullets": ["Valid point", "Another valid", "Third point"]},
            {"title": "Slide 3", "bullets": ["Point A", "Point B", "Point C"]},
            {"title": "Slide 4", "bullets": ["Point D", "Point E", "Point F"]},
            {"title": "Slide 5", "bullets": ["Point G", "Point H", "Point I"]},
            {"title": "Slide 6", "bullets": ["Point J", "Point K", "Point L"]},
        ],
        "report_sections": [
            {"title": "Summary", "content": "Summary content"},
            {"title": "Context", "content": "Context"},
            {"title": "Insights", "content": "Insights"},
            {"title": "Actions", "content": "Actions"},
            {"title": "Next", "content": "Next"}
        ],
        "assumptions": [],
        "next_steps": ["Step 1", "Step 2", "Step 3"]
    })
    
    service = GenerationService(mock_llm)
    result = await service.generate_output(mock_session_no_metrics)
    
    # Assumptions should mention removed numeric data
    assert any("numeri" in a.lower() or "blueprint" in a.lower() 
              for a in result["assumptions"])
