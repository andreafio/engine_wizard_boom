# Blueprint Review Service

## Overview

The Blueprint Review Service creates concise review summaries for user confirmation before final output generation. It analyzes blueprint completeness and categorizes items as confirmed, draft (needs confirmation), or missing.

## Key Features

- **Pre-Generation Validation**: Reviews blueprint before creating final outputs
- **User Confirmation**: Shows what will be included vs. what needs confirmation
- **Gap Analysis**: Identifies missing critical sections
- **Concise Bullets**: Short, clear bullet points for each category
- **Section-Aware**: Uses section names for clarity

## Architecture

```
Blueprint Data → BlueprintReviewService → LLM → BlueprintReview
                              ↓
                       Analysis Framework:
                       - Confirmed: Ready for use
                       - Draft to Confirm: Needs user approval
                       - Missing: Critical gaps identified
```

## Usage

### Direct Usage

```python
from app.services.blueprint_review_service import review_blueprint_for_confirmation

blueprint = {
    "context": {"industry": "Software", "company_size": "50-100"},
    "objective": {"goal": "15% growth", "budget": "50000"},
    # ... complete blueprint
}

review = await review_blueprint_for_confirmation(blueprint)

print("Confirmed items:")
for item in review.review.confirmed:
    print(f"  • {item}")

print("Needs confirmation:")
for item in review.review.draft_to_confirm:
    print(f"  • {item}")
```

### Service Integration

```python
from app.services.blueprint_review_service import BlueprintReviewService
from app.llm.openai_provider import OpenAIProvider

llm = OpenAIProvider(api_key="your-key", model="gpt-4o-mini")
service = BlueprintReviewService(llm)

review = await service.review_blueprint(blueprint)
```

## Input Format

The service expects a complete blueprint with standard sections:

```json
{
  "blueprint": {
    "context": {
      "industry": "Software Development",
      "company_size": "50-100 employees"
    },
    "objective": {
      "goal": "Increase market share by 15%",
      "budget": "50000"
    },
    "offer": {
      "value_prop": "AI-powered project management"
    },
    "audience": {
      "target_audience": ["SMBs", "Startups"]
    },
    "funnel": {},
    "channels": {
      "primary": ["LinkedIn", "Google Ads"]
    },
    "assets_tracking": {},
    "constraints": {},
    "risks": {
      "risks": "Competitive market"
    }
  }
}
```

## Output Format

Returns a `BlueprintReview` object with categorized items:

```json
{
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
```

## Analysis Categories

### Confirmed
- **Ready for Use**: Complete, validated data that can be used directly
- **No User Action Needed**: Items ready for final output generation
- **High Confidence**: Data that meets quality standards

### Draft to Confirm
- **Needs Verification**: Incomplete or draft data requiring user approval
- **User Decision Required**: Items that need confirmation before proceeding
- **Medium Confidence**: Data exists but may need refinement

### Missing
- **Critical Gaps**: Empty sections that are essential for complete strategy
- **Blocks Generation**: Missing items that prevent final output creation
- **Low Confidence**: No data available for these strategic elements

## Bullet Format Rules

### Structure
- **Section Prefix**: Always include section name (e.g., "Context:", "Objective:")
- **Concise**: Keep each bullet under 50 characters
- **Specific**: Be clear about what's confirmed, draft, or missing
- **Actionable**: Focus on key strategic elements

### Examples
```
✅ Confirmed:
  "Context: industry and company size confirmed"
  "Objective: 15% growth goal with $50K budget"
  "Channels: LinkedIn and Google Ads selected"

⚠️  Draft to Confirm:
  "Audience: target segments need verification"
  "Offer: pricing model details incomplete"
  "Risks: competitive analysis draft"

❌ Missing:
  "Funnel: conversion stages not defined"
  "Assets: tracking KPIs missing"
  "Constraints: limitations not specified"
```

## Integration with Generation Flow

### Pre-Generation Check
```python
# Review blueprint before generation
review = await review_blueprint_for_confirmation(blueprint)

if review.review.missing:
    # Show missing items to user
    return {"status": "incomplete", "missing": review.review.missing}

if review.review.draft_to_confirm:
    # Show items needing confirmation
    return {"status": "needs_confirmation", "to_confirm": review.review.draft_to_confirm}

# Proceed with generation
content = await generation_service.generate(blueprint)
```

### User Confirmation Flow
```python
# Get review
review = await review_blueprint_for_confirmation(blueprint)

# Show to user for confirmation
confirmed_items = review.review.confirmed
needs_confirmation = review.review.draft_to_confirm
missing_items = review.review.missing

# User confirms draft items or provides missing data
# Then proceed with generation
```

## Error Handling

### LLM Failures
- **Fallback Response**: Safe default with error indication
- **Graceful Degradation**: Continues with manual review option
- **Error Logging**: Detailed error information for debugging

### Data Validation
- **Schema Validation**: Pydantic models ensure output structure
- **Type Safety**: Proper data types for all fields
- **Constraint Enforcement**: List types and validation rules

## Performance

- **Latency**: ~2-3 seconds per review
- **Token Usage**: Moderate (blueprint analysis + categorized output)
- **Caching**: No caching implemented (each review is unique)
- **Batch Processing**: Not supported (one blueprint at a time)

## Testing

Run the blueprint review tests:

```bash
# Unit tests
pytest tests/test_blueprint_review.py -v

# All service tests
pytest tests/ -k "blueprint_review" --tb=short
```

## Comparison with Existing Review Service

| Feature | Existing Review Service | Blueprint Review Service |
|---------|------------------------|-------------------------|
| Input | Session object with status | Raw blueprint JSON |
| Output | confirmed/to_confirm | confirmed/draft_to_confirm/missing |
| Purpose | Pre-generation validation | User confirmation summary |
| Integration | Tied to session workflow | Standalone service |

## Future Enhancements

- **Interactive Confirmation**: Allow users to confirm items directly in review
- **Auto-Fix Suggestions**: Recommend how to complete missing items
- **Progress Tracking**: Show completion percentage by section
- **Custom Validation Rules**: Configurable requirements by use case
- **Historical Comparison**: Compare reviews across blueprint versions