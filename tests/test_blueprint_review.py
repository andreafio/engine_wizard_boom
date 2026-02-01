"""
Test Blueprint Review Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.blueprint_review_service import BlueprintReviewService, BlueprintReview, ReviewSummary


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    llm = MagicMock()
    llm.generate_json = AsyncMock()
    return llm


@pytest.fixture
def blueprint_review_service(mock_llm):
    """Blueprint review service instance"""
    return BlueprintReviewService(mock_llm)


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
        "funnel": {},
        "channels": {
            "primary": ["LinkedIn", "Google Ads"]
        },
        "assets_tracking": {},
        "constraints": {},
        "risks": {
            "risks": "Competitive market entry"
        }
    }


@pytest.mark.asyncio
async def test_review_blueprint_success(blueprint_review_service, mock_llm, sample_blueprint):
    """Test successful blueprint review"""
    mock_llm.generate_json.return_value = {
        "review": {
            "confirmed": [
                "Context: industry and company size confirmed",
                "Objective: 15% growth goal with $50K budget",
                "Channels: LinkedIn and Google Ads selected"
            ],
            "draft_to_confirm": [
                "Audience: target segments need verification",
                "Offer: pricing model details incomplete",
                "Risks: competitive analysis draft"
            ],
            "missing": [
                "Funnel: conversion stages not defined",
                "Assets: tracking KPIs missing",
                "Constraints: limitations not specified"
            ]
        }
    }

    result = await blueprint_review_service.review_blueprint(sample_blueprint)

    assert isinstance(result, BlueprintReview)
    assert len(result.review.confirmed) == 3
    assert len(result.review.draft_to_confirm) == 3
    assert len(result.review.missing) == 3
    assert "Context:" in result.review.confirmed[0]
    assert "Objective:" in result.review.confirmed[1]
    assert "Funnel:" in result.review.missing[0]


@pytest.mark.asyncio
async def test_review_blueprint_minimal_data(blueprint_review_service, mock_llm):
    """Test review with minimal blueprint data"""
    minimal_blueprint = {
        "context": {"industry": "Tech"},
        "objective": {}
    }

    mock_llm.generate_json.return_value = {
        "review": {
            "confirmed": [
                "Context: industry identified as Tech"
            ],
            "draft_to_confirm": [],
            "missing": [
                "Objective: business goals not defined",
                "Offer: value proposition missing",
                "Audience: target market undefined",
                "Funnel: sales process not specified",
                "Channels: marketing channels not selected",
                "Assets: tracking setup incomplete",
                "Constraints: limitations not identified",
                "Risks: risk assessment missing"
            ]
        }
    }

    result = await blueprint_review_service.review_blueprint(minimal_blueprint)

    assert isinstance(result, BlueprintReview)
    assert len(result.review.confirmed) == 1
    assert len(result.review.draft_to_confirm) == 0
    assert len(result.review.missing) >= 5
    assert "Objective:" in result.review.missing[0]


@pytest.mark.asyncio
async def test_review_blueprint_empty(blueprint_review_service, mock_llm):
    """Test review with empty blueprint"""
    empty_blueprint = {}

    mock_llm.generate_json.return_value = {
        "review": {
            "confirmed": [],
            "draft_to_confirm": [],
            "missing": [
                "Context: company information missing",
                "Objective: business goals undefined",
                "Offer: products/services not specified",
                "Audience: target market not identified",
                "Funnel: sales process not defined",
                "Channels: marketing channels not selected",
                "Assets: tracking setup missing",
                "Constraints: limitations not specified",
                "Risks: risk assessment incomplete"
            ]
        }
    }

    result = await blueprint_review_service.review_blueprint(empty_blueprint)

    assert isinstance(result, BlueprintReview)
    assert len(result.review.confirmed) == 0
    assert len(result.review.draft_to_confirm) == 0
    assert len(result.review.missing) >= 9


@pytest.mark.asyncio
async def test_review_blueprint_complete(blueprint_review_service, mock_llm):
    """Test review with complete blueprint data"""
    complete_blueprint = {
        "context": {"industry": "Software", "company_size": "100-500", "description": "SaaS company"},
        "objective": {"goal": "20% growth", "timeline": "12 months", "budget": "100000"},
        "offer": {"value_prop": "AI automation", "pricing": "SaaS subscription"},
        "audience": {"target_audience": ["SMBs"], "persona": "CTO"},
        "funnel": {"stages": ["Awareness", "Consideration", "Decision"]},
        "channels": {"primary": ["LinkedIn", "Content Marketing"]},
        "assets_tracking": {"kpis": ["CAC", "LTV"]},
        "constraints": {"limitations": "Small team"},
        "risks": {"risks": "Competition"}
    }

    mock_llm.generate_json.return_value = {
        "review": {
            "confirmed": [
                "Context: complete company profile",
                "Objective: growth targets with budget",
                "Offer: value prop and pricing defined",
                "Audience: target segments specified",
                "Funnel: sales stages mapped",
                "Channels: marketing channels selected",
                "Assets: KPIs identified",
                "Constraints: limitations noted",
                "Risks: competitive analysis done"
            ],
            "draft_to_confirm": [],
            "missing": []
        }
    }

    result = await blueprint_review_service.review_blueprint(complete_blueprint)

    assert isinstance(result, BlueprintReview)
    assert len(result.review.confirmed) >= 5
    assert len(result.review.draft_to_confirm) == 0
    assert len(result.review.missing) == 0


@pytest.mark.asyncio
async def test_review_blueprint_llm_error_fallback(blueprint_review_service, mock_llm, sample_blueprint):
    """Test fallback behavior when LLM fails"""
    mock_llm.generate_json.side_effect = Exception("LLM service unavailable")

    result = await blueprint_review_service.review_blueprint(sample_blueprint)

    assert isinstance(result, BlueprintReview)
    assert len(result.review.confirmed) == 1
    assert "Review generation failed" in result.review.confirmed[0]
    assert len(result.review.draft_to_confirm) == 0
    assert len(result.review.missing) == 0


@pytest.mark.asyncio
async def test_review_summary_validation(blueprint_review_service, mock_llm, sample_blueprint):
    """Test that review summary structure is properly validated"""
    mock_llm.generate_json.return_value = {
        "review": {
            "confirmed": ["Test confirmed item"],
            "draft_to_confirm": ["Test draft item"],
            "missing": ["Test missing item"]
        }
    }

    result = await blueprint_review_service.review_blueprint(sample_blueprint)

    assert isinstance(result.review, ReviewSummary)
    assert isinstance(result.review.confirmed, list)
    assert isinstance(result.review.draft_to_confirm, list)
    assert isinstance(result.review.missing, list)
    assert result.review.confirmed[0] == "Test confirmed item"