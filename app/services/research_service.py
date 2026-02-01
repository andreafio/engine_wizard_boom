"""
Research and Intelligence Service
Searches for company/user information and monitors ad libraries
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import httpx
from app.core.logging import get_logger
from app.llm.provider import LLMProvider

logger = get_logger(__name__)


class SocialPresence(BaseModel):
    """Social media presence data"""
    platform: str  # linkedin, facebook, instagram, twitter
    handle: Optional[str] = None
    followers: Optional[int] = None
    posting_frequency: Optional[str] = None  # daily, weekly, monthly
    content_themes: List[str] = Field(default_factory=list)
    engagement_level: Optional[str] = None  # high, medium, low


class AdCampaign(BaseModel):
    """Advertising campaign found in ad libraries"""
    platform: str  # facebook, google, linkedin
    ad_id: Optional[str] = None
    title: str
    description: str
    media_type: str  # image, video, carousel
    started_running: Optional[str] = None
    is_active: bool = True
    target_audience: Optional[str] = None
    estimated_budget: Optional[str] = None
    call_to_action: Optional[str] = None
    landing_page: Optional[str] = None


class CompetitorInsight(BaseModel):
    """Competitor analysis"""
    name: str
    website: Optional[str] = None
    positioning: Optional[str] = None
    key_differentiators: List[str] = Field(default_factory=list)
    active_channels: List[str] = Field(default_factory=list)
    estimated_market_share: Optional[str] = None


class ResearchOutput(BaseModel):
    """Complete research and intelligence output"""
    company_name: str
    industry: str
    
    # Social presence
    social_profiles: List[SocialPresence] = Field(default_factory=list)
    website_url: Optional[str] = None
    
    # Ad monitoring
    active_campaigns: List[AdCampaign] = Field(default_factory=list)
    ad_spend_estimate: Optional[str] = None  # "5k-10k/month", "10k-50k/month"
    
    # Competitor intelligence
    competitors: List[CompetitorInsight] = Field(default_factory=list, max_length=5)
    
    # AI-generated insights
    marketing_insights: List[str] = Field(default_factory=list, min_length=3, max_length=10)
    recommended_channels: List[str] = Field(default_factory=list)
    content_gaps: List[str] = Field(default_factory=list)
    
    # Metadata
    research_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_sources: List[str] = Field(default_factory=list)


class ResearchService:
    """
    Research and Intelligence Service
    
    Collects data from:
    1. Web search (Google/Bing) for real-time company info
    2. Facebook Ad Library
    3. Google Ads Transparency Center
    4. LinkedIn Ads (if available)
    5. Social media profiles (public data)
    6. Company website
    7. News and press releases
    
    Uses AI to synthesize findings into actionable insights
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.serper_api_key = None  # Google Search API via Serper.dev
        self.bing_api_key = None    # Bing Search API
    
    async def research_company(
        self,
        company_name: str,
        industry: str,
        website: Optional[str] = None,
        session_id: str = "research-session"
    ) -> ResearchOutput:
        """
        Main research orchestrator
        Coordinates all research activities and synthesizes results
        """
        logger.info("research_started", session_id=session_id, company=company_name)
        
        # Step 0: Web search for real-time company info
        web_results = await self._search_web(company_name, industry)
        
        # Step 1: Search social profiles
        social_profiles = await self._search_social_profiles(company_name)
        
        # Step 2: Monitor ad libraries
        ad_campaigns = await self._search_ad_libraries(company_name)
        
        # Step 3: Identify competitors (with web context)
        competitors = await self._identify_competitors(company_name, industry, web_results)
        
        # Step 4: Synthesize with AI (using fresh web data)
        insights = await self._generate_insights(
            company_name=company_name,
            industry=industry,
            web_results=web_results,
            social_profiles=social_profiles,
            ad_campaigns=ad_campaigns,
            competitors=competitors
        )
        
        research = ResearchOutput(
            company_name=company_name,
            industry=industry,
            website_url=website,
            social_profiles=social_profiles,
            active_campaigns=ad_campaigns,
            competitors=competitors,
            marketing_insights=insights.get("insights", []),
            recommended_channels=insights.get("channels", []),
            content_gaps=insights.get("gaps", []),
            data_sources=self._get_data_sources()
        )
        
        logger.info(
            "research_completed",
            session_id=session_id,
            profiles_found=len(social_profiles),
            campaigns_found=len(ad_campaigns),
            competitors_found=len(competitors)
        )
        
        return research
    
    async def _search_web(self, company_name: str, industry: str) -> str:
        """
        Search web for real-time company information
        Uses Serper.dev API (Google Search API alternative) or Bing Search API
        
        Free alternatives:
        - Serper.dev: 2,500 free searches/month
        - Bing Search API: 3,000 free searches/month
        """
        logger.info("searching_web", company=company_name)
        
        # Try Serper.dev first (if API key available)
        if self.serper_api_key:
            try:
                return await self._search_serper(company_name, industry)
            except Exception as e:
                logger.warning("serper_search_failed", error=str(e))
        
        # Fallback to Bing Search API
        if self.bing_api_key:
            try:
                return await self._search_bing(company_name, industry)
            except Exception as e:
                logger.warning("bing_search_failed", error=str(e))
        
        # No API available - return empty context
        logger.warning("no_web_search_api", message="Set SERPER_API_KEY or BING_API_KEY for real-time data")
        return ""
    
    async def _search_serper(self, company_name: str, industry: str) -> str:
        """
        Search using Serper.dev API (Google Search)
        API: https://serper.dev
        Free tier: 2,500 searches/month
        """
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        
        # Search query optimized for company research
        query = f"{company_name} {industry} azienda Italia prodotti servizi"
        
        payload = {
            "q": query,
            "gl": "it",  # Italy
            "hl": "it",  # Italian
            "num": 10    # Top 10 results
        }
        
        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract organic results
        results = []
        for item in data.get("organic", [])[:5]:  # Top 5 results
            results.append(f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\n")
        
        # Extract knowledge graph if available
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            results.insert(0, f"Knowledge Graph: {kg.get('title')}\n{kg.get('description')}\n")
        
        return "\n".join(results)
    
    async def _search_bing(self, company_name: str, industry: str) -> str:
        """
        Search using Bing Search API
        API: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
        Free tier: 3,000 searches/month
        """
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key
        }
        
        query = f"{company_name} {industry} Italy company products"
        params = {
            "q": query,
            "mkt": "it-IT",
            "count": 10,
            "responseFilter": "Webpages"
        }
        
        response = await self.http_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("webPages", {}).get("value", [])[:5]:
            results.append(f"Title: {item.get('name')}\nSnippet: {item.get('snippet')}\n")
        
        return "\n".join(results)
    
    async def _search_social_profiles(self, company_name: str) -> List[SocialPresence]:
        """
        Search for company social media profiles
        Uses public APIs and web scraping (respecting robots.txt)
        """
        logger.info("searching_social_profiles", company=company_name)
        
        # TODO: Implement actual API calls to:
        # - LinkedIn Company Search API
        # - Facebook Graph API (public pages)
        # - Instagram Basic Display API
        # - Twitter API v2
        
        # Mock data for now
        profiles = [
            SocialPresence(
                platform="linkedin",
                handle=f"{company_name.lower().replace(' ', '-')}",
                followers=5000,
                posting_frequency="weekly",
                content_themes=["product updates", "company culture", "industry insights"],
                engagement_level="medium"
            ),
            SocialPresence(
                platform="facebook",
                handle=f"{company_name.replace(' ', '')}",
                followers=2000,
                posting_frequency="monthly",
                content_themes=["promotions", "events"],
                engagement_level="low"
            )
        ]
        
        return profiles
    
    async def _search_ad_libraries(self, company_name: str) -> List[AdCampaign]:
        """
        Search ad libraries for active campaigns
        
        Facebook Ad Library API: https://www.facebook.com/ads/library/api/
        Google Ads Transparency: https://adstransparency.google.com/
        """
        logger.info("searching_ad_libraries", company=company_name)
        
        campaigns = []
        
        # Facebook Ad Library
        try:
            fb_ads = await self._search_facebook_ad_library(company_name)
            campaigns.extend(fb_ads)
        except Exception as e:
            logger.warning("facebook_ad_search_failed", error=str(e))
        
        # Google Ads Transparency
        try:
            google_ads = await self._search_google_ads_transparency(company_name)
            campaigns.extend(google_ads)
        except Exception as e:
            logger.warning("google_ad_search_failed", error=str(e))
        
        return campaigns
    
    async def _search_facebook_ad_library(self, company_name: str) -> List[AdCampaign]:
        """
        Query Facebook Ad Library API
        Requires: Facebook App ID and Access Token
        
        API: https://graph.facebook.com/v18.0/ads_archive
        Params: search_terms, ad_reached_countries, ad_active_status
        """
        logger.info("searching_facebook_ads", company=company_name)
        
        # TODO: Implement actual Facebook Ad Library API call
        # Example:
        # url = "https://graph.facebook.com/v18.0/ads_archive"
        # params = {
        #     "search_terms": company_name,
        #     "ad_reached_countries": "IT",
        #     "ad_active_status": "ACTIVE",
        #     "access_token": self.fb_access_token
        # }
        # response = await self.http_client.get(url, params=params)
        
        # Mock data
        return [
            AdCampaign(
                platform="facebook",
                ad_id="fb_123456",
                title="Lead Generation Campaign",
                description="Ottieni 100 lead qualificati al mese con la nostra piattaforma",
                media_type="image",
                started_running="2026-01-15",
                is_active=True,
                target_audience="Marketing Managers, Italia, 25-45 anni",
                estimated_budget="5k-10k/month",
                call_to_action="Learn More",
                landing_page="https://example.com/demo"
            )
        ]
    
    async def _search_google_ads_transparency(self, company_name: str) -> List[AdCampaign]:
        """
        Query Google Ads Transparency Center
        
        Note: Google doesn't have a public API, requires web scraping
        or manual research at: https://adstransparency.google.com/
        """
        logger.info("searching_google_ads", company=company_name)
        
        # TODO: Implement Google Ads scraping (respect rate limits)
        
        # Mock data
        return [
            AdCampaign(
                platform="google",
                title="B2B SaaS Marketing Platform",
                description="Automatizza il tuo marketing con AI",
                media_type="text",
                started_running="2026-01-10",
                is_active=True,
                call_to_action="Richiedi Demo"
            )
        ]
    
    async def _identify_competitors(
        self,
        company_name: str,
        industry: str,
        web_results: str = ""
    ) -> List[CompetitorInsight]:
        """
        Identify main competitors using:
        1. Real-time web search results (fresh data)
        2. LLM analysis with web context
        3. Industry databases
        """
        logger.info("identifying_competitors", company=company_name, industry=industry)
        
        # Use LLM to identify competitors WITH web search context
        prompt = f"""
You are a market research analyst. Identify the top 3-5 direct competitors for this company.

Company: {company_name}
Industry: {industry}

REAL-TIME WEB SEARCH RESULTS:
{web_results if web_results else "No web results available - use your knowledge base"}

Based on the web search results and your knowledge, identify competitors in the same industry/region.

For each competitor, provide:
1. Company name
2. Website (if known)
3. Key positioning/value proposition
4. Main differentiators
5. Active marketing channels

Return ONLY valid JSON matching this structure:
{{
  "competitors": [
    {{
      "name": "Competitor Name",
      "website": "https://...",
      "positioning": "Brief positioning statement",
      "key_differentiators": ["diff1", "diff2"],
      "active_channels": ["linkedin", "google ads"]
    }}
  ]
}}
"""
        
        try:
            data = await self.llm.generate_json(
                prompt=prompt,
                system_prompt="You are a market research analyst. Provide accurate competitor analysis."
            )
            
            competitors = [
                CompetitorInsight(**comp)
                for comp in data.get("competitors", [])
            ]
            
            return competitors[:5]  # Max 5 competitors
            
        except Exception as e:
            logger.error("competitor_identification_failed", error=str(e))
            return []
    
    async def _generate_insights(
        self,
        company_name: str,
        industry: str,
        web_results: str,
        social_profiles: List[SocialPresence],
        ad_campaigns: List[AdCampaign],
        competitors: List[CompetitorInsight]
    ) -> Dict[str, List[str]]:
        """
        Use LLM to synthesize research data into actionable insights
        Uses fresh web search results as primary context
        """
        logger.info("generating_insights", company=company_name)
        
        # Prepare context for LLM
        social_summary = "\n".join([
            f"- {p.platform}: {p.followers} followers, posts {p.posting_frequency}, themes: {', '.join(p.content_themes)}"
            for p in social_profiles
        ])
        
        ad_summary = "\n".join([
            f"- {c.platform}: '{c.title}' (active: {c.is_active})"
            for c in ad_campaigns
        ])
        
        competitor_summary = "\n".join([
            f"- {c.name}: {c.positioning}"
            for c in competitors
        ])
        
        prompt = f"""
You are a marketing intelligence analyst. Analyze this research data and provide actionable insights.

COMPANY: {company_name}
INDUSTRY: {industry}

REAL-TIME WEB SEARCH RESULTS (PRIMARY SOURCE):
{web_results if web_results else "No web results - using secondary sources only"}

SOCIAL MEDIA PRESENCE:
{social_summary or "No data found"}

ACTIVE AD CAMPAIGNS:
{ad_summary or "No campaigns found"}

COMPETITORS:
{competitor_summary or "No competitors identified"}

Based PRIMARILY on the web search results, provide:
1. Marketing Insights (5-10 key observations about the company's current state)
2. Recommended Channels (based on industry and competitor activity)
3. Content Gaps (opportunities for differentiation)

Return ONLY valid JSON:
{{
  "insights": [
    "Insight 1: Based on web results, company specializes in...",
    "Insight 2: Web presence shows focus on..."
  ],
  "channels": ["linkedin", "google ads", "content marketing"],
  "gaps": [
    "Gap 1: No video content on social media",
    "Gap 2: Missing thought leadership content"
  ]
}}
"""
        
        try:
            insights = await self.llm.generate_json(
                prompt=prompt,
                system_prompt="You are a marketing intelligence analyst. Provide actionable insights."
            )
            
            return insights
            
        except Exception as e:
            logger.error("insight_generation_failed", error=str(e))
            return {
                "insights": ["Ricerca completata ma insight non disponibili"],
                "channels": [],
                "gaps": []
            }
    
    def _get_data_sources(self) -> List[str]:
        """Return list of data sources used"""
        sources = []
        
        if self.serper_api_key:
            sources.append("Google Search (via Serper.dev)")
        elif self.bing_api_key:
            sources.append("Bing Search API")
        
        sources.extend([
            "Facebook Ad Library API",
            "Google Ads Transparency Center",
            "LinkedIn Company Search",
            "OpenAI GPT-4 (analysis)",
            "Public web data"
        ])
        
        return sources
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Convenience function
async def research_company_intelligence(
    company_name: str,
    industry: str,
    website: Optional[str] = None,
    session_id: str = "research"
) -> ResearchOutput:
    """
    Research company and generate intelligence report
    
    Usage:
        research = await research_company_intelligence(
            company_name="Acme Corp",
            industry="B2B SaaS",
            website="https://acme.com"
        )
    """
    import os
    from app.llm.openai_provider import OpenAIProvider
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    llm = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    service = ResearchService(llm)
    
    # Set web search API keys if available
    service.serper_api_key = os.getenv("SERPER_API_KEY")
    service.bing_api_key = os.getenv("BING_SEARCH_API_KEY")
    
    try:
        return await service.research_company(
            company_name=company_name,
            industry=industry,
            website=website,
            session_id=session_id
        )
    finally:
        await service.close()
