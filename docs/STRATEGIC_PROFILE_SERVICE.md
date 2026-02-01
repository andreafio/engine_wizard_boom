# Strategic Profile Service

## Overview

The Strategic Profile Service generates internal strategic profiles for marketing/sales teams from blueprint data. It creates operational strategic analysis based on confirmed blueprint fields, identifying assumptions, open questions, and recommended actions.

## Key Features

- **Blueprint-Only Analysis**: Uses only confirmed fields as facts, no invented metrics
- **Operational Tone**: Concise, actionable insights for marketing/sales teams
- **Confidence Mapping**: Categorizes blueprint completeness (high/medium/low confidence)
- **Strategic Recommendations**: 3 prioritized next steps with rationale
- **Gap Analysis**: Identifies assumptions and open questions requiring clarification

## Architecture

```
Blueprint Data → StrategicProfileService → LLM → StrategicProfile
                              ↓
                       Analysis Framework:
                       - Summary (max 10 lines)
                       - Reorganized Profile
                       - Assumptions & Questions
                       - Recommended Actions
                       - Confidence Mapping
```

## Usage

### Direct Usage

```python
from app.services.strategic_profile_service import generate_strategic_profile

blueprint = {
    "context": {"industry": "Software", "company_size": "50-100"},
    "objective": {"goal": "15% growth", "budget": "50000"},
    # ... other sections
}

profile = await generate_strategic_profile(blueprint)

print(f"Summary: {profile.summary}")
print(f"High Confidence Areas: {profile.confidence_map['high']}")
print(f"Top Priority Action: {profile.recommended_actions[0].action}")
```

### Service Integration

```python
from app.services.strategic_profile_service import StrategicProfileService
from app.llm.openai_provider import OpenAIProvider

llm = OpenAIProvider(api_key="your-key", model="gpt-4o-mini")
service = StrategicProfileService(llm)

profile = await service.generate_profile(blueprint)
```

## Input Format

The service expects a complete blueprint with the following sections:

```json
{
  "blueprint": {
    "context": {
      "industry": "Software Development",
      "company_size": "50-100 employees",
      "description": "B2B SaaS company"
    },
    "objective": {
      "goal": "Increase market share by 15%",
      "timeline": "Q4 2026",
      "budget": "50000"
    },
    "offer": {
      "value_prop": "AI-powered project management",
      "pricing": "Subscription-based"
    },
    "audience": {
      "target_audience": ["SMBs", "Tech startups"],
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
      "risks": "High competitive market entry"
    }
  }
}
```

## Output Format

Returns a `StrategicProfile` object with the following structure:

```json
{
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
    "What is the current CAC and LTV?",
    "How many active users currently?"
  ],
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Complete competitor analysis",
      "why": "Critical for positioning strategy"
    },
    {
      "priority": 2,
      "action": "Define current metrics baseline",
      "why": "Need data for goal tracking"
    },
    {
      "priority": 3,
      "action": "Develop content strategy for LinkedIn",
      "why": "Primary channel requires content plan"
    }
  ],
  "confidence_map": {
    "high": ["context.company_size", "objective.budget", "channels.primary"],
    "medium": ["context.industry", "offer.value_prop", "audience.target_audience"],
    "low": ["funnel.conversion_goals", "assets_tracking.kpis", "risks.risks"]
  }
}
```

## Analysis Framework

### Summary
- **Max 10 lines**: Concise operational overview
- **Tone**: Professional, actionable for marketing/sales teams
- **Focus**: Key business context, objectives, and constraints

### Profile
- **Reorganized Data**: Blueprint information structured by section
- **Operational Insights**: Business-focused interpretation
- **Confirmed Facts Only**: No invented or assumed data

### Assumptions
- **Incomplete Data**: What we're assuming based on missing information
- **Draft Fields**: Items marked as assumptions rather than facts
- **Business Logic**: Reasonable inferences from available data

### Open Questions
- **Critical Gaps**: Information needed for complete strategy
- **Clarification Needs**: Areas requiring additional input
- **Priority Order**: Most important questions first

### Recommended Actions
- **3 Actions Maximum**: Prioritized next steps
- **Priority Levels**: 1 (highest) to 3 (important but not urgent)
- **Rationale**: Clear "why" explanation for each action

### Confidence Map
- **High Confidence**: Confirmed data with specific metrics/details
- **Medium Confidence**: Confirmed data but lacking some specifics
- **Low Confidence**: Draft, incomplete, or missing critical information

## Rules & Constraints

### Data Usage Rules
- **Confirmed Fields Only**: Use as established facts
- **Draft Fields**: Appear only as assumptions or open questions
- **No Invention**: Never create numbers (CPL, CAC, ROAS, etc.) unless explicitly confirmed
- **Blueprint-Only**: All insights must be derived from provided blueprint data

### Operational Tone
- **Concise**: Avoid verbose explanations
- **Actionable**: Focus on what marketing/sales teams can do
- **Professional**: Business-appropriate language
- **Practical**: Grounded in real business operations

## Error Handling

### LLM Failures
- **Fallback Response**: Safe default profile with error indication
- **Graceful Degradation**: Continues operation with reduced functionality
- **Error Logging**: Detailed error information for debugging

### Data Validation
- **Schema Validation**: Pydantic models ensure output structure
- **Type Safety**: Proper data types for all fields
- **Constraint Enforcement**: Max lengths and required fields

## Performance

- **Latency**: ~3-5 seconds per profile generation
- **Token Usage**: Moderate (blueprint analysis + structured output)
- **Caching**: No caching implemented (each request is unique)
- **Batch Processing**: Not supported (one blueprint at a time)

## Testing

Run the strategic profile tests:

```bash
# Unit tests
pytest tests/test_strategic_profile.py -v

# All service tests
pytest tests/ -k "strategic_profile" --tb=short
```

## Integration Examples

### With Orchestrator Service

```python
# Get blueprint from session
blueprint = await orchestrator.get_blueprint(session_id)

# Generate strategic profile
profile = await generate_strategic_profile(blueprint)

# Use in marketing planning
if profile.confidence_map["low"]:
    # Handle low confidence areas
    pass
```

### With Generation Service

```python
# Generate profile first
profile = await generate_strategic_profile(blueprint)

# Use insights in content generation
context = {
    "strategic_profile": profile.model_dump(),
    "confidence_level": "high" if not profile.confidence_map["low"] else "medium"
}

# Generate marketing materials
content = await generation_service.generate_content(context)
```

## Future Enhancements

- **Historical Comparison**: Compare profiles across time periods
- **Team Collaboration**: Multi-user profile editing and approval
- **Automated Updates**: Profile updates when blueprint changes
- **Export Formats**: PDF reports, presentations, and dashboards
- **Integration APIs**: Connect with CRM, marketing automation tools