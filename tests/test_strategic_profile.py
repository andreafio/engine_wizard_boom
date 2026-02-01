"""
Test Strategic Profile Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.strategic_profile_service import (
    StrategicProfileService,
    StrategicProfile,
    RecommendedAction,
    OpenQuestion,
    RiskWatchout,
    ActionPlanStep
)


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    llm = MagicMock()
    llm.generate_json = AsyncMock()
    return llm


@pytest.fixture
def strategic_profile_service(mock_llm):
    """Strategic profile service instance"""
    return StrategicProfileService(mock_llm)


@pytest.fixture
def sample_blueprint():
    """Sample blueprint data for testing"""
    return {
        "context": {
            "industry": "Software Development",
            "company_size": "50-100 employees",
            "description": "B2B SaaS company providing project management tools"
        },
        "objective": {
            "goal": "Increase market share by 15% in 12 months",
            "timeline": "Q4 2026",
            "budget": "50000"
        },
        "offer": {
            "value_prop": "Streamlined project management with AI insights",
            "pricing": "Subscription-based"
        },
        "audience": {
            "target_audience": ["Small to medium businesses", "Tech startups"],
            "persona": "Technical project managers"
        },
        "funnel": {
            "stages": ["Awareness", "Consideration", "Decision"],
            "conversion_goals": "10% conversion rate"
        },
        "channels": {
            "primary": ["LinkedIn", "Google Ads"],
            "budget": "30000"
        },
        "assets_tracking": {
            "kpis": ["CAC", "LTV", "Conversion Rate"]
        },
        "constraints": {
            "limitations": "Limited marketing team bandwidth"
        },
        "risks": {
            "risks": "Competitive market entry"
        }
    }


@pytest.mark.asyncio
async def test_generate_profile_success(strategic_profile_service, mock_llm, sample_blueprint):
    """Test successful profile generation"""
    mock_llm.generate_json.return_value = {
        "summary": "B2B SaaS company focused on project management tools. Targeting SMBs and tech startups with subscription model. Goal: 15% market share growth in 12 months with $50K budget.",
        "profile": {
            "context": {"industry": "Software Development", "company_size": "50-100 employees"},
            "objective": {"goal": "15% market share growth", "budget": "$50K"},
            "offer": {"value_prop": "AI-powered project management"},
            "audience": {"target": "SMBs and tech startups"},
            "funnel": {"stages": ["Awareness", "Consideration", "Decision"]},
            "channels": {"primary": ["LinkedIn", "Google Ads"]},
            "assets_tracking": {"kpis": ["CAC", "LTV", "Conversion Rate"]},
            "constraints": {"bandwidth": "Limited marketing team"},
            "risks": {"competition": "High competitive pressure"}
        },
        "assumptions": [
            "Current market share percentage not specified",
            "Competitor analysis incomplete"
        ],
        "open_questions": [
            {"question": "What is the current CAC and LTV?", "why_it_matters": "Critical for ROI calculation", "priority": 1},
            {"question": "How many active users currently?", "why_it_matters": "Baseline for growth measurement", "priority": 2}
        ],
        "risks_watchouts": [
            {"risk": "High competition in project management space", "impact": "high", "mitigation": "Focus on AI differentiation"},
            {"risk": "Limited marketing budget for growth goals", "impact": "medium", "mitigation": "Prioritize high-ROI channels"}
        ],
        "recommended_actions": [
            {"priority": 1, "action": "Complete competitor analysis", "why": "Critical for positioning strategy", "owner_hint": "Marketing"},
            {"priority": 2, "action": "Define current metrics baseline", "why": "Need data for goal tracking", "owner_hint": "Ops"},
            {"priority": 3, "action": "Develop content strategy for LinkedIn", "why": "Primary channel requires content plan", "owner_hint": "Marketing"}
        ],
        "action_plan_90min": [
            {"step": 1, "task": "Audit top 5 competitors", "output": "Competitive analysis spreadsheet"},
            {"step": 2, "task": "Pull current CAC/LTV data", "output": "Metrics dashboard"},
            {"step": 3, "task": "Draft LinkedIn content calendar", "output": "30-day content plan"}
        ],
        "confidence_map": {
            "high": ["context.company_size", "objective.budget", "channels.primary"],
            "medium": ["context.industry", "offer.value_prop", "audience.target_audience"],
            "low": ["funnel.conversion_goals", "assets_tracking.kpis", "risks.risks"]
        }
    }

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    assert isinstance(result, StrategicProfile)
    assert "B2B SaaS company" in result.summary
    assert len(result.assumptions) == 2
    assert len(result.open_questions) == 2
    assert result.open_questions[0].priority == 1
    assert result.open_questions[0].why_it_matters == "Critical for ROI calculation"
    assert len(result.risks_watchouts) == 2
    assert result.risks_watchouts[0].impact == "high"
    assert len(result.recommended_actions) == 3
    assert result.recommended_actions[0].priority == 1
    assert result.recommended_actions[0].owner_hint == "Marketing"
    assert len(result.action_plan_90min) == 3
    assert result.action_plan_90min[0].step == 1
    assert result.action_plan_90min[0].output == "Competitive analysis spreadsheet"
    assert "high" in result.confidence_map
    assert "medium" in result.confidence_map
    assert "low" in result.confidence_map


@pytest.mark.asyncio
async def test_generate_profile_with_minimal_blueprint(strategic_profile_service, mock_llm):
    """Test profile generation with minimal blueprint data"""
    minimal_blueprint = {
        "context": {"industry": "Tech"},
        "objective": {"goal": "Grow business"}
    }

    mock_llm.generate_json.return_value = {
        "summary": "Tech company seeking business growth. Limited strategic details available.",
        "profile": {
            "context": {"industry": "Tech"},
            "objective": {"goal": "Grow business"},
            "offer": {},
            "audience": {},
            "funnel": {},
            "channels": {},
            "assets_tracking": {},
            "constraints": {},
            "risks": {}
        },
        "assumptions": ["Most strategic elements undefined"],
        "open_questions": [
            {"question": "What products/services are offered?", "why_it_matters": "Need to define value proposition", "priority": 1},
            {"question": "Who is the target audience?", "why_it_matters": "Critical for campaign targeting", "priority": 2},
            {"question": "What channels will be used?", "why_it_matters": "Need channel strategy", "priority": 3}
        ],
        "risks_watchouts": [
            {"risk": "Undefined value proposition", "impact": "high", "mitigation": "Conduct value prop workshop"},
            {"risk": "No target audience defined", "impact": "high", "mitigation": "Create buyer personas"}
        ],
        "recommended_actions": [
            {"priority": 1, "action": "Define value proposition", "why": "Foundation for all marketing activities", "owner_hint": "Marketing"},
            {"priority": 2, "action": "Identify target audience", "why": "Critical for campaign targeting", "owner_hint": "Marketing"},
            {"priority": 3, "action": "Set specific measurable goals", "why": "Need concrete objectives to track", "owner_hint": "Ops"}
        ],
        "action_plan_90min": [
            {"step": 1, "task": "List all products/services", "output": "Product catalog"},
            {"step": 2, "task": "Identify top 3 customer segments", "output": "Audience segments doc"},
            {"step": 3, "task": "Draft value proposition statements", "output": "Value prop options"}
        ],
        "confidence_map": {
            "high": [],
            "medium": ["context.industry"],
            "low": ["objective.goal", "offer", "audience", "funnel", "channels"]
        }
    }

    result = await strategic_profile_service.generate_profile(minimal_blueprint)

    assert isinstance(result, StrategicProfile)
    assert "Tech company" in result.summary
    assert len(result.open_questions) >= 3
    assert len(result.recommended_actions) == 3
    assert result.confidence_map["high"] == []
    assert "context.industry" in result.confidence_map["medium"]


@pytest.mark.asyncio
async def test_generate_profile_llm_error_fallback(strategic_profile_service, mock_llm, sample_blueprint):
    """Test fallback behavior when LLM fails"""
    mock_llm.generate_json.side_effect = Exception("LLM service unavailable")

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    assert isinstance(result, StrategicProfile)
    assert "Unable to generate" in result.summary
    assert "error" in result.assumptions[0].lower()
    assert len(result.recommended_actions) == 0
    assert result.confidence_map["low"] == ["Profile generation"]


@pytest.mark.asyncio
async def test_generate_profile_empty_blueprint(strategic_profile_service, mock_llm):
    """Test profile generation with empty blueprint"""
    empty_blueprint = {}

    mock_llm.generate_json.return_value = {
        "summary": "No strategic information available. Complete blueprint required for profile generation.",
        "profile": {
            "context": {}, "objective": {}, "offer": {}, "audience": {},
            "funnel": {}, "channels": {}, "assets_tracking": {},
            "constraints": {}, "risks": {}
        },
        "assumptions": ["Blueprint is completely empty"],
        "open_questions": [
            {"question": "What industry is the company in?", "why_it_matters": "Foundation for strategic planning", "priority": 1},
            {"question": "What are the business objectives?", "why_it_matters": "Need clear goals to work towards", "priority": 2},
            {"question": "Who is the target audience?", "why_it_matters": "Critical for marketing effectiveness", "priority": 3}
        ],
        "risks_watchouts": [
            {"risk": "No strategic foundation", "impact": "high", "mitigation": "Complete blueprint sections"}
        ],
        "recommended_actions": [
            {"priority": 1, "action": "Complete context section", "why": "Foundation for strategic planning", "owner_hint": "Marketing"},
            {"priority": 2, "action": "Define business objectives", "why": "Need clear goals to work towards", "owner_hint": "Ops"},
            {"priority": 3, "action": "Identify target audience", "why": "Critical for marketing effectiveness", "owner_hint": "Marketing"}
        ],
        "action_plan_90min": [
            {"step": 1, "task": "Gather company information", "output": "Company profile doc"},
            {"step": 2, "task": "Define key objectives", "output": "Objectives list"},
            {"step": 3, "task": "Identify target segments", "output": "Audience definition"}
        ],
        "confidence_map": {
            "high": [],
            "medium": [],
            "low": ["All sections require completion"]
        }
    }

    result = await strategic_profile_service.generate_profile(empty_blueprint)

    assert isinstance(result, StrategicProfile)
    assert "No strategic information" in result.summary
    assert len(result.open_questions) >= 3
    assert len(result.recommended_actions) == 3


@pytest.mark.asyncio
async def test_recommended_actions_validation(strategic_profile_service, mock_llm, sample_blueprint):
    """Test that recommended actions are properly validated"""
    mock_llm.generate_json.return_value = {
        "summary": "Test summary",
        "profile": {},
        "assumptions": [],
        "open_questions": [],
        "risks_watchouts": [],
        "recommended_actions": [
            {"priority": 1, "action": "Test action 1", "why": "Reason 1", "owner_hint": "Marketing"},
            {"priority": 2, "action": "Test action 2", "why": "Reason 2", "owner_hint": "Sales"},
            {"priority": 3, "action": "Test action 3", "why": "Reason 3", "owner_hint": "Ops"}
        ],
        "action_plan_90min": [
            {"step": 1, "task": "Task 1", "output": "Output 1"},
            {"step": 2, "task": "Task 2", "output": "Output 2"},
            {"step": 3, "task": "Task 3", "output": "Output 3"}
        ],
        "confidence_map": {"high": [], "medium": [], "low": []}
    }

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    assert len(result.recommended_actions) == 3
    for action in result.recommended_actions:
        assert isinstance(action, RecommendedAction)
        assert 1 <= action.priority <= 3
        assert action.action
        assert action.why


@pytest.mark.asyncio
async def test_confidence_map_structure(strategic_profile_service, mock_llm, sample_blueprint):
    """Test that confidence map has required structure"""
    mock_llm.generate_json.return_value = {
        "summary": "Test summary",
        "profile": {},
        "assumptions": [],
        "open_questions": [],
        "risks_watchouts": [],
        "recommended_actions": [],
        "action_plan_90min": [
            {"step": 1, "task": "Task 1", "output": "Output 1"},
            {"step": 2, "task": "Task 2", "output": "Output 2"},
            {"step": 3, "task": "Task 3", "output": "Output 3"}
        ],
        "confidence_map": {
            "high": ["field1", "field2"],
            "medium": ["field3"],
            "low": ["field4", "field5", "field6"]
        }
    }

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    assert "high" in result.confidence_map
    assert "medium" in result.confidence_map
    assert "low" in result.confidence_map
    assert isinstance(result.confidence_map["high"], list)
    assert isinstance(result.confidence_map["medium"], list)
    assert isinstance(result.confidence_map["low"], list)


@pytest.mark.asyncio
async def test_guardrails_open_questions_max_8(strategic_profile_service, mock_llm, sample_blueprint):
    """Test that guardrails limit open questions to max 8"""
    # LLM returns 10 questions
    mock_llm.generate_json.return_value = {
        "summary": "Test summary",
        "profile": {},
        "assumptions": [],
        "open_questions": [
            {"question": f"Question {i}", "why_it_matters": f"Reason {i}", "priority": i}
            for i in range(1, 11)  # 10 questions
        ],
        "risks_watchouts": [],
        "recommended_actions": [],
        "action_plan_90min": [
            {"step": 1, "task": "Task 1", "output": "Output 1"},
            {"step": 2, "task": "Task 2", "output": "Output 2"},
            {"step": 3, "task": "Task 3", "output": "Output 3"}
        ],
        "confidence_map": {"high": [], "medium": [], "low": []}
    }

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    # Should be truncated to 8
    assert len(result.open_questions) == 8
    # Priorities should be sequential 1..8
    for idx, question in enumerate(result.open_questions, start=1):
        assert question.priority == idx


@pytest.mark.asyncio
async def test_guardrails_action_plan_min_3(strategic_profile_service, mock_llm, sample_blueprint):
    """Test that guardrails ensure action plan has at least 3 steps"""
    # LLM returns only 1 step
    mock_llm.generate_json.return_value = {
        "summary": "Test summary",
        "profile": {},
        "assumptions": [],
        "open_questions": [],
        "risks_watchouts": [],
        "recommended_actions": [],
        "action_plan_90min": [
            {"step": 1, "task": "Task 1", "output": "Output 1"}
        ],
        "confidence_map": {"high": [], "medium": [], "low": []}
    }

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    # Should be padded to 3
    assert len(result.action_plan_90min) >= 3
    # All steps should have outputs
    for step in result.action_plan_90min:
        assert step.output
        assert len(step.output) >= 5


@pytest.mark.asyncio
async def test_guardrails_action_plan_max_5(strategic_profile_service, mock_llm, sample_blueprint):
    """Test that guardrails limit action plan to max 5 steps"""
    # LLM returns 7 steps
    mock_llm.generate_json.return_value = {
        "summary": "Test summary",
        "profile": {},
        "assumptions": [],
        "open_questions": [],
        "risks_watchouts": [],
        "recommended_actions": [],
        "action_plan_90min": [
            {"step": i, "task": f"Task {i}", "output": f"Output {i}"}
            for i in range(1, 8)  # 7 steps
        ],
        "confidence_map": {"high": [], "medium": [], "low": []}
    }

    result = await strategic_profile_service.generate_profile(sample_blueprint)

    # Should be truncated to 5
    assert len(result.action_plan_90min) == 5
    # Steps should be sequential 1..5
    for idx, step in enumerate(result.action_plan_90min, start=1):
        assert step.step == idx