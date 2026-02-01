# Research & Intelligence Module

## Overview

Il modulo **Research Service** estende il Wizard BOOM Engine con capacità di **ricerca e intelligence marketing** automatizzate. Dopo il completamento del wizard, il sistema effettua ricerche approfondite su:

1. **Social Media Presence** - Profili aziendali su LinkedIn, Facebook, Instagram, Twitter
2. **Ad Libraries** - Campagne pubblicitarie attive su Facebook, Google, LinkedIn
3. **Competitor Analysis** - Identificazione competitor e loro strategie
4. **AI Insights** - Sintesi intelligente con raccomandazioni actionable

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Service                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Social    │  │  Ad Library  │  │  Competitor  │      │
│  │   Search    │  │  Monitoring  │  │  Analysis    │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           ▼                                 │
│                  ┌────────────────┐                         │
│                  │  AI Synthesis  │                         │
│                  │   (LLM GPT-4)  │                         │
│                  └────────┬───────┘                         │
│                           ▼                                 │
│                  ┌────────────────┐                         │
│                  │ ResearchOutput │                         │
│                  └────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. Facebook Ad Library API

**API Endpoint:** `https://graph.facebook.com/v18.0/ads_archive`

**Query Parameters:**
- `search_terms`: Company name
- `ad_reached_countries`: Target countries (e.g., "IT" for Italy)
- `ad_active_status`: "ACTIVE" / "INACTIVE" / "ALL"
- `access_token`: Facebook App Access Token

**Example Response:**
```json
{
  "data": [
    {
      "id": "123456789",
      "ad_creative_bodies": ["Get 100 leads per month"],
      "ad_creative_link_titles": ["Lead Generation Platform"],
      "ad_delivery_start_time": "2026-01-15T10:00:00Z",
      "ad_snapshot_url": "https://...",
      "page_name": "Acme Corp",
      "spend": { "lower_bound": "5000", "upper_bound": "10000" }
    }
  ]
}
```

**Setup:**
1. Create Facebook App: https://developers.facebook.com/apps/
2. Add "Marketing API" product
3. Get Access Token (requires Business Verification for ad library access)

---

### 2. Google Ads Transparency Center

**URL:** `https://adstransparency.google.com/`

**Note:** No official API available. Options:
- Manual research via web interface
- Web scraping (respect rate limits and robots.txt)
- Google Custom Search API for advertiser identification

**Data Available:**
- Advertiser name
- Ad copy and creatives
- Approximate date range
- Format (text, image, video)

---

### 3. LinkedIn Ads (Limited)

**API:** LinkedIn Marketing API
**Endpoint:** `https://api.linkedin.com/v2/adAnalytics`

**Note:** Requires:
- LinkedIn Partner API access
- Company Page Admin permissions
- Not publicly available for competitor research

**Alternative:** Use LinkedIn Company Search API to find profiles and estimate activity.

---

### 4. Social Media APIs

#### LinkedIn Company Search
```
GET https://api.linkedin.com/v2/search/companies
Authorization: Bearer {access_token}
```

#### Facebook Graph API (Public Pages)
```
GET https://graph.facebook.com/v18.0/{page-id}
  ?fields=name,followers_count,about,website
  &access_token={token}
```

#### Twitter API v2
```
GET https://api.twitter.com/2/users/by/username/{username}
  ?user.fields=public_metrics,description
```

---

## Pydantic Schemas

### SocialPresence
```python
class SocialPresence(BaseModel):
    platform: str  # linkedin, facebook, instagram, twitter
    handle: Optional[str]
    followers: Optional[int]
    posting_frequency: Optional[str]  # daily, weekly, monthly
    content_themes: List[str]
    engagement_level: Optional[str]  # high, medium, low
```

### AdCampaign
```python
class AdCampaign(BaseModel):
    platform: str  # facebook, google, linkedin
    ad_id: Optional[str]
    title: str
    description: str
    media_type: str  # image, video, carousel
    started_running: Optional[str]
    is_active: bool
    target_audience: Optional[str]
    estimated_budget: Optional[str]
    call_to_action: Optional[str]
    landing_page: Optional[str]
```

### CompetitorInsight
```python
class CompetitorInsight(BaseModel):
    name: str
    website: Optional[str]
    positioning: Optional[str]
    key_differentiators: List[str]
    active_channels: List[str]
    estimated_market_share: Optional[str]
```

### ResearchOutput
```python
class ResearchOutput(BaseModel):
    company_name: str
    industry: str
    social_profiles: List[SocialPresence]
    active_campaigns: List[AdCampaign]
    competitors: List[CompetitorInsight]
    marketing_insights: List[str]  # min=3, max=10
    recommended_channels: List[str]
    content_gaps: List[str]
    research_date: str
    data_sources: List[str]
```

---

## Usage

### Basic Usage

```python
from app.services.research_service import research_company_intelligence

# After wizard completion
research = await research_company_intelligence(
    company_name="Acme Corp",
    industry="B2B SaaS",
    website="https://acme.com",
    session_id="wizard-session-123"
)

print(f"Found {len(research.social_profiles)} social profiles")
print(f"Found {len(research.active_campaigns)} active ad campaigns")
print(f"Identified {len(research.competitors)} competitors")

# Marketing insights
for insight in research.marketing_insights:
    print(f"• {insight}")

# Recommended channels
print(f"Recommended channels: {', '.join(research.recommended_channels)}")
```

### Integration with Wizard Flow

```python
from app.services.orchestrator_service import OrchestratorService
from app.services.generation_service import GenerationService
from app.services.research_service import research_company_intelligence

# Step 1: Complete wizard (orchestrator + generation)
orchestrator = OrchestratorService(llm_provider)
generation = GenerationService(llm_provider)

blueprint = await orchestrator.extract_context(...)
output = await generation.generate(blueprint, ...)

# Step 2: Run research in background
research = await research_company_intelligence(
    company_name=blueprint.context.company_name,
    industry=blueprint.context.industry,
    website=blueprint.context.website
)

# Step 3: Enrich output with research insights
enriched_output = {
    "presentation": output.slides,
    "report": output.report_sections,
    "intelligence": {
        "social_presence": research.social_profiles,
        "active_campaigns": research.active_campaigns,
        "competitors": research.competitors,
        "insights": research.marketing_insights
    }
}
```

---

## AI Synthesis

Il modulo usa **GPT-4** per sintetizzare i dati raccolti in insights actionable:

### Prompt Template

```
You are a marketing intelligence analyst. Analyze this research data:

COMPANY: {company_name}
INDUSTRY: {industry}

SOCIAL MEDIA PRESENCE:
- linkedin: 5000 followers, posts weekly
- facebook: 2000 followers, posts monthly

ACTIVE AD CAMPAIGNS:
- facebook: "Lead Gen Campaign" (active)
- google: "B2B SaaS Platform" (active)

COMPETITORS:
- CompetitorX: AI-powered automation
- CompetitorY: Budget-friendly option

Provide:
1. Marketing Insights (5-10 observations)
2. Recommended Channels
3. Content Gaps (opportunities)

Return JSON:
{
  "insights": ["Insight 1", "Insight 2", ...],
  "channels": ["linkedin", "google ads"],
  "gaps": ["Gap 1", "Gap 2"]
}
```

### Output Example

```json
{
  "insights": [
    "Company has low social engagement despite active ads - consider content strategy",
    "Competitors heavily investing in LinkedIn - opportunity to differentiate",
    "No video content found - major gap in current strategy",
    "Ad spend estimate 5k-10k/month - below industry average",
    "Strong presence on Facebook but low engagement - optimize targeting"
  ],
  "channels": [
    "linkedin",
    "google ads",
    "content marketing",
    "video marketing"
  ],
  "gaps": [
    "No video content on social media",
    "Missing thought leadership articles",
    "No case studies in ad campaigns",
    "Limited Instagram presence"
  ]
}
```

---

## Testing

### Run Tests

```bash
# All research tests
pytest tests/test_research.py -v

# With coverage
pytest tests/test_research.py --cov=app.services.research_service

# Skip integration tests (require API keys)
pytest tests/test_research.py -v -m "not skip"
```

### Test Coverage

- ✅ Schema validation (SocialPresence, AdCampaign, CompetitorInsight, ResearchOutput)
- ✅ Mock data testing (social profiles, ad campaigns)
- ✅ LLM fallback on error
- ✅ Service cleanup (HTTP client)
- ⏭️ Integration tests (skipped without API keys)

---

## Environment Variables

```bash
# Facebook Ad Library
FACEBOOK_APP_ID=your_app_id
FACEBOOK_ACCESS_TOKEN=your_access_token

# LinkedIn API
LINKEDIN_ACCESS_TOKEN=your_token

# Twitter API v2
TWITTER_BEARER_TOKEN=your_bearer_token

# OpenAI (already configured)
OPENAI_API_KEY=sk-...
```

---

## API Rate Limits

| Provider | Limit | Cost |
|----------|-------|------|
| **Facebook Ad Library** | 200 calls/hour | Free |
| **LinkedIn API** | 100 calls/day (free tier) | Paid tiers available |
| **Twitter API v2** | 500k tweets/month (Basic) | $100/month |
| **OpenAI GPT-4** | 10k requests/day | ~$0.01/1k tokens |

---

## Roadmap

### Phase 1: Foundation (Current)
- ✅ Pydantic schemas
- ✅ Mock data for testing
- ✅ AI synthesis with GPT-4
- ✅ Basic test coverage

### Phase 2: Real Integrations
- ⏭️ Facebook Ad Library API integration
- ⏭️ Google Ads web scraping
- ⏭️ LinkedIn Company Search API
- ⏭️ Twitter API v2 integration

### Phase 3: Advanced Features
- ⏭️ Historical ad tracking (detect trends)
- ⏭️ Sentiment analysis on social content
- ⏭️ Competitive pricing intelligence
- ⏭️ Automated reporting (weekly summaries)

### Phase 4: UI Integration
- ⏭️ Research dashboard in frontend
- ⏭️ Real-time ad monitoring alerts
- ⏭️ Competitor comparison charts
- ⏭️ Export to PDF/PPT

---

## Security & Privacy

### Data Handling
- ✅ Only public data collected
- ✅ No PII (personally identifiable information)
- ✅ API keys stored in environment variables
- ✅ HTTPS for all API calls
- ✅ Rate limiting to respect provider policies

### Compliance
- **GDPR**: Only public business data (no personal data)
- **Facebook Terms**: Respect Ad Library API usage policies
- **robots.txt**: Respect web scraping rules
- **Rate Limits**: Don't exceed provider limits

---

## Troubleshooting

### Facebook Ad Library Returns Empty
**Issue:** No ads found for company name

**Solutions:**
1. Try different search terms (company variations)
2. Check if company uses different business name for ads
3. Verify `ad_reached_countries` parameter (use "ALL" for global)
4. Check if ads are inactive (use `ad_active_status: "ALL"`)

### LinkedIn API Access Denied
**Issue:** 403 Forbidden on API calls

**Solutions:**
1. Verify access token is valid (check expiration)
2. Ensure app has correct permissions (r_organization_social)
3. Check if company page exists and is public
4. Consider LinkedIn Partner Program for advanced access

### LLM Insights Too Generic
**Issue:** AI-generated insights lack specificity

**Solutions:**
1. Provide more context in prompt (industry details, goals)
2. Include more research data (social metrics, ad performance)
3. Use GPT-4 instead of GPT-3.5 for better analysis
4. Add few-shot examples in prompt

---

## Examples

### Example 1: B2B SaaS Company

```python
research = await research_company_intelligence(
    company_name="Slack",
    industry="B2B SaaS - Collaboration",
    website="https://slack.com"
)

# Output:
# - social_profiles: 5 platforms (LinkedIn, Twitter, Facebook, Instagram, YouTube)
# - active_campaigns: 12 ads (Facebook: 7, Google: 5)
# - competitors: 3 (Microsoft Teams, Zoom, Discord)
# - insights: 8 actionable recommendations
# - recommended_channels: ["linkedin", "google ads", "youtube", "content marketing"]
```

### Example 2: E-commerce Fashion

```python
research = await research_company_intelligence(
    company_name="Zara",
    industry="E-commerce - Fashion",
    website="https://zara.com"
)

# Output:
# - social_profiles: Instagram (45M followers), Facebook (28M)
# - active_campaigns: 25 ads (heavy Instagram + Facebook)
# - competitors: H&M, Uniqlo, Mango
# - insights: Focus on visual content, influencer partnerships
# - recommended_channels: ["instagram", "facebook", "tiktok", "influencer marketing"]
```

---

## Contributing

Per aggiungere nuove data sources:

1. Crea metodo `_search_new_platform()` in `ResearchService`
2. Aggiungi schema Pydantic se necessario
3. Integra in `research_company()` orchestrator
4. Aggiungi test in `tests/test_research.py`
5. Documenta rate limits e API keys richieste

---

_Ultimo aggiornamento: 29 Gennaio 2026_
