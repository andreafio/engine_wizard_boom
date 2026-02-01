# Strategic Profile Service V2 - Consulting-Grade

## Overview
Enhanced internal profile generation with consulting-grade structure and deterministic guardrails.

## New Features (V2)

### 1. Structured Open Questions
- **Max 8 questions** (enforced by guardrails)
- Each question includes:
  - `question`: The question text
  - `why_it_matters`: Business impact explanation
  - `priority`: 1-8 (sequential, auto-assigned)

```json
{
  "open_questions": [
    {
      "question": "What is the current CAC and LTV?",
      "why_it_matters": "Critical for ROI calculation",
      "priority": 1
    }
  ]
}
```

### 2. Risks & Watchouts
- Identifies risks linked to draft/missing data
- Includes impact level and mitigation strategy
- Non-generic: tied to actual blueprint gaps

```json
{
  "risks_watchouts": [
    {
      "risk": "High competition in project management space",
      "impact": "high",
      "mitigation": "Focus on AI differentiation"
    }
  ]
}
```

### 3. 90-Minute Action Plan
- **3-5 concrete steps** (enforced by guardrails)
- Each step has:
  - `step`: Sequential number 1-5
  - `task`: Actionable task description
  - `output`: Concrete deliverable (mandatory)

```json
{
  "action_plan_90min": [
    {
      "step": 1,
      "task": "Audit top 5 competitors",
      "output": "Competitive analysis spreadsheet"
    }
  ]
}
```

### 4. Enhanced Recommended Actions
- Added `owner_hint` field: "Marketing", "Sales", or "Ops"
- Clearer ownership assignment for execution

```json
{
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Complete competitor analysis",
      "why": "Critical for positioning strategy",
      "owner_hint": "Marketing"
    }
  ]
}
```

## Truth Rules (NON-NEGOTIABLE)

1. **Use ONLY confirmed fields as facts**
   - Fields with `status="confirmed"` → can be stated as facts
   - Fields with `status="draft"` or missing → must appear only in assumptions/questions/risks

2. **Never invent metrics**
   - No invented KPIs, budgets, targets, timelines, or performance results
   - If metrics are missing, explicitly state as assumption

3. **Reframe unconfirmed data**
   - If something sounds like a fact but isn't confirmed → move to assumptions or open questions

## Guardrails (Post-LLM)

### Automatic Corrections
1. **Open Questions**
   - If > 8 → truncate to 8
   - Priorities auto-renumbered 1..8 sequentially

2. **Action Plan**
   - If < 3 steps → pad with fallback steps
   - If > 5 steps → truncate to 5
   - Missing outputs → add generic "Deliverable for step X"
   - Steps auto-renumbered 1..N sequentially

## Complete Output Schema

```json
{
  "summary": "max 10 lines",
  "profile": {
    "context": {},
    "objective": {},
    "offer": {},
    "audience": {},
    "funnel": {},
    "channels": {},
    "assets_tracking": {},
    "constraints": {},
    "risks": {}
  },
  "assumptions": ["..."],
  "open_questions": [
    {
      "question": "...",
      "why_it_matters": "...",
      "priority": 1
    }
  ],
  "risks_watchouts": [
    {
      "risk": "...",
      "impact": "high|medium|low",
      "mitigation": "..."
    }
  ],
  "recommended_actions": [
    {
      "priority": 1,
      "action": "...",
      "why": "...",
      "owner_hint": "Marketing|Sales|Ops"
    }
  ],
  "action_plan_90min": [
    {
      "step": 1,
      "task": "...",
      "output": "..."
    }
  ],
  "confidence_map": {
    "high": ["..."],
    "medium": ["..."],
    "low": ["..."]
  }
}
```

## Usage

### In Code
```python
from app.services.strategic_profile_service import StrategicProfileService

# Create service
service = StrategicProfileService(llm_provider)

# Generate profile
profile = await service.generate_profile(blueprint)

# Or get as dict for orchestrator
internal_profile = await service.generate_internal_profile(blueprint)
```

### API Endpoint
```
POST /generate_internal_profile
{
  "blueprint": { ... }
}
```

## Testing

All tests passing:
- ✅ 9/9 strategic profile tests
- ✅ Guardrails validation (max 8 questions, 3-5 action steps)
- ✅ Structured output validation
- ✅ Error handling and fallbacks

## Next Steps

After V2 is deployed:
1. **Review → Edit Flow**: Enable users to edit specific blueprint sections based on review feedback
2. **Profile Polish**: Automated clarity improvements without adding new facts
3. **Section Router**: Smart routing for which sections to prioritize for editing
