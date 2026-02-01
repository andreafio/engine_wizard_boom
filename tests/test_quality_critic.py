"""
Test Quality Critic Service (Rule-based)
"""
import pytest
from app.services.quality_critic_service import QualityCriticService, QualityCritique


@pytest.fixture
def quality_critic():
    """Quality critic service instance (rule-based)"""
    return QualityCriticService()


@pytest.mark.asyncio
async def test_critique_high_quality_answer(quality_critic):
    """Test critiquing a high-quality answer"""
    result = await quality_critic.critique_answer(
        field="context.industry",
        value="Software development for healthcare institutions",
        ui_type="short_text",
        section="Context"
    )

    assert result.quality_score == 0.8  # Rule-based: specific and concise
    assert result.is_vague == False
    assert result.recommend_deep == False
    assert result.recommended_followup_field is None
    assert result.reason == "specific and concise"


@pytest.mark.asyncio
async def test_critique_low_quality_vague_answer(quality_critic):
    """Test critiquing a low-quality vague answer"""
    result = await quality_critic.critique_answer(
        field="context.industry",
        value="tech",
        ui_type="short_text",
        section="Context"
    )

    assert result.quality_score == 0.3  # Rule-based: too brief
    assert result.is_vague == True
    assert result.recommend_deep == True
    assert result.recommended_followup_field == "context.company_size"
    assert result.reason == "too brief"


@pytest.mark.asyncio
async def test_critique_select_answer(quality_critic):
    assert result.recommended_followup_field == "context.company_size"
    assert result.reason == "too brief"


@pytest.mark.asyncio
async def test_critique_select_answer(quality_critic):
    """Test critiquing a select field answer"""
    result = await quality_critic.critique_answer(
        field="context.business_model",
        value="b2b",
        ui_type="single_select",
        section="Context"
    )

    assert result.quality_score == 0.9  # Rule-based: selection made
    assert result.is_vague == False
    assert result.recommend_deep == False


@pytest.mark.asyncio
async def test_critique_multi_select_answer(quality_critic):
    """Test critiquing a multi-select field answer"""
    result = await quality_critic.critique_answer(
        field="channels.primary",
        value=["social", "email"],
        ui_type="multi_select",
        section="Channels"
    )

    assert result.quality_score == 0.9  # Rule-based: selection made
    assert result.is_vague == False
    assert result.recommend_deep == False


@pytest.mark.asyncio
async def test_critique_long_text_answer(quality_critic):
    """Test critiquing a long text answer"""
    long_description = """
    We are a B2B SaaS company specializing in project management software
    for construction firms. Our platform helps contractors manage timelines,
    budgets, and team collaboration across multiple construction sites.
    We serve mid-sized construction companies with 50-500 employees.
    """

    result = await quality_critic.critique_answer(
        field="context.description",
        value=long_description,
        ui_type="long_text",
        section="Context"
    )

    assert result.quality_score == 0.9  # Rule-based: detailed and specific
    assert result.is_vague == False
    assert result.recommend_deep == False


@pytest.mark.asyncio
async def test_critique_answer_with_followup(quality_critic):
    """Test critiquing an answer that needs follow-up"""
    result = await quality_critic.critique_answer(
        field="objective.primary_goal",
        value="grow my business",
        ui_type="short_text",
        section="Objective"
    )

    assert result.quality_score == 0.2  # Rule-based: generic marketing phrase
    assert result.is_vague == True
    assert result.recommend_deep == True
    assert result.recommended_followup_field == "objective.secondary_goals"
    assert result.reason == "generic marketing phrase"


@pytest.mark.asyncio
async def test_critique_different_sections(quality_critic):
    """Test critiquing answers from different sections"""
    result = await quality_critic.critique_answer(
        field="channels.primary",
        value="social",
        ui_type="short_text",
        section="Channels"
    )

    assert result.quality_score == 0.3  # Rule-based: too brief
    assert result.is_vague == True
    assert result.recommend_deep == True
    assert result.recommended_followup_field is None  # No specific followup for this field


@pytest.mark.asyncio
async def test_critique_structured_value(quality_critic):
    """Test critiquing a structured value (dict)"""
    structured_value = {
        "primary": "social_media",
        "secondary": "email",
        "budget": "5000"
    }

    result = await quality_critic.critique_answer(
        field="channels.strategy",
        value=structured_value,
        ui_type="multi_select",
        section="Channels"
    )

    assert result.quality_score == 0.9  # Rule-based: selection made (dict converted to string)
    assert result.is_vague == False
    assert result.recommend_deep == False
