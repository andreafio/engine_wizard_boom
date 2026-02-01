"""
Test suite for Research and Intelligence Service
"""
import pytest
from app.services.research_service import (
    ResearchService,
    ResearchOutput,
    SocialPresence,
    AdCampaign,
    CompetitorInsight
)
from app.llm.openai_provider import OpenAIProvider


@pytest.fixture
def research_service():
    """Create research service with LLM provider"""
    llm = OpenAIProvider()
    return ResearchService(llm)


def test_social_presence_schema():
    """Test SocialPresence schema validation"""
    profile = SocialPresence(
        platform="linkedin",
        handle="acme-corp",
        followers=5000,
        posting_frequency="weekly",
        content_themes=["product", "culture"],
        engagement_level="medium"
    )
    
    assert profile.platform == "linkedin"
    assert profile.followers == 5000
    assert len(profile.content_themes) == 2


def test_ad_campaign_schema():
    """Test AdCampaign schema validation"""
    campaign = AdCampaign(
        platform="facebook",
        ad_id="fb_123",
        title="Lead Gen Campaign",
        description="Get 100 leads per month",
        media_type="image",
        is_active=True,
        target_audience="Marketing Managers",
        estimated_budget="5k-10k/month"
    )
    
    assert campaign.platform == "facebook"
    assert campaign.is_active is True
    assert "leads" in campaign.description.lower()


def test_competitor_insight_schema():
    """Test CompetitorInsight schema validation"""
    competitor = CompetitorInsight(
        name="CompetitorX",
        website="https://competitorx.com",
        positioning="AI-powered marketing automation",
        key_differentiators=["AI features", "Lower price"],
        active_channels=["linkedin", "google ads"]
    )
    
    assert competitor.name == "CompetitorX"
    assert len(competitor.key_differentiators) == 2
    assert "linkedin" in competitor.active_channels


def test_research_output_schema():
    """Test ResearchOutput schema validation"""
    research = ResearchOutput(
        company_name="Acme Corp",
        industry="B2B SaaS",
        social_profiles=[
            SocialPresence(
                platform="linkedin",
                handle="acme",
                followers=1000,
                posting_frequency="weekly",
                content_themes=["tech"],
                engagement_level="high"
            )
        ],
        active_campaigns=[
            AdCampaign(
                platform="facebook",
                title="Test Campaign",
                description="Test",
                media_type="image"
            )
        ],
        competitors=[
            CompetitorInsight(
                name="Competitor A",
                positioning="Market leader"
            )
        ],
        marketing_insights=[
            "Insight 1",
            "Insight 2",
            "Insight 3"
        ],
        recommended_channels=["linkedin", "google ads"],
        content_gaps=["Video content", "Case studies"]
    )
    
    assert research.company_name == "Acme Corp"
    assert len(research.social_profiles) == 1
    assert len(research.marketing_insights) >= 3
    assert len(research.competitors) <= 5


def test_research_output_requires_min_insights():
    """Test that at least 3 insights are required"""
    with pytest.raises(ValueError):
        ResearchOutput(
            company_name="Test",
            industry="Tech",
            marketing_insights=["Only one insight"]  # Should fail (min=3)
        )


def test_research_output_limits_competitors():
    """Test that max 5 competitors are allowed"""
    competitors = [
        CompetitorInsight(name=f"Competitor {i}", positioning="Test")
        for i in range(5)  # Max allowed is 5
    ]
    
    research = ResearchOutput(
        company_name="Test",
        industry="Tech",
        competitors=competitors,
        marketing_insights=["A", "B", "C"]
    )
    
    assert len(research.competitors) == 5


@pytest.mark.asyncio
async def test_research_service_mock_data(research_service):
    """Test research service with mock data"""
    research = await research_service.research_company(
        company_name="Acme Corp",
        industry="B2B SaaS",
        website="https://acme.com",
        session_id="test-session"
    )
    
    assert research.company_name == "Acme Corp"
    assert research.industry == "B2B SaaS"
    assert research.website_url == "https://acme.com"
    assert len(research.social_profiles) > 0
    assert len(research.active_campaigns) > 0
    assert len(research.data_sources) > 0


@pytest.mark.asyncio
async def test_search_social_profiles(research_service):
    """Test social profile search (mock)"""
    profiles = await research_service._search_social_profiles("Acme Corp")
    
    assert len(profiles) > 0
    assert any(p.platform == "linkedin" for p in profiles)
    assert all(p.followers is not None for p in profiles if p.platform == "linkedin")


@pytest.mark.asyncio
async def test_search_ad_libraries(research_service):
    """Test ad library search (mock)"""
    campaigns = await research_service._search_ad_libraries("Acme Corp")
    
    assert len(campaigns) > 0
    assert any(c.platform == "facebook" for c in campaigns)
    assert all(c.is_active in [True, False] for c in campaigns)


@pytest.mark.asyncio
async def test_identify_competitors_fallback(research_service):
    """Test competitor identification with LLM fallback"""
    competitors = await research_service._identify_competitors(
        company_name="Acme Corp",
        industry="B2B SaaS"
    )
    
    # Should return empty list on error (no API key in test env)
    assert isinstance(competitors, list)
    assert len(competitors) <= 5


@pytest.mark.asyncio
async def test_generate_insights_fallback(research_service):
    """Test insight generation with fallback"""
    insights = await research_service._generate_insights(
        company_name="Acme Corp",
        industry="B2B SaaS",
        social_profiles=[],
        ad_campaigns=[],
        competitors=[]
    )
    
    # Should return fallback data on error
    assert "insights" in insights
    assert "channels" in insights
    assert "gaps" in insights
    assert len(insights["insights"]) > 0


def test_data_sources_list(research_service):
    """Test data sources are documented"""
    sources = research_service._get_data_sources()
    
    assert len(sources) > 0
    assert any("Facebook" in s for s in sources)
    assert any("Google" in s for s in sources)
    assert any("LinkedIn" in s for s in sources)


@pytest.mark.asyncio
async def test_service_cleanup(research_service):
    """Test HTTP client cleanup"""
    await research_service.close()
    # Should not raise exception


# Integration test (skipped without API key)
@pytest.mark.skip(reason="Requires API keys and real API calls")
@pytest.mark.asyncio
async def test_real_facebook_ad_library():
    """
    Integration test for Facebook Ad Library
    Requires: FB_ACCESS_TOKEN environment variable
    """
    from app.services.research_service import research_company_intelligence
    
    research = await research_company_intelligence(
        company_name="Nike",
        industry="Sportswear",
        website="https://nike.com"
    )
    
    assert len(research.active_campaigns) > 0
    facebook_ads = [c for c in research.active_campaigns if c.platform == "facebook"]
    assert len(facebook_ads) > 0
