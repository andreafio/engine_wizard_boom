# Wizard Orchestrator Role

## What is the Orchestrator?

The **Wizard Orchestrator** is an optional LLM-powered component that helps extract structured data from free-text user input. It is NOT a chatbot - it's a specialized extraction engine that assists the wizard flow.

## Key Principles

### ✅ What the Orchestrator DOES

- **Extracts structured data** from vague user messages
- **Operates within the current step** only
- **Suggests options** when input is unclear
- **Returns confidence levels** (high, medium, low)
- **Assists the engine** - not the user directly

### ❌ What the Orchestrator NEVER Does

- **Skip steps** - Cannot jump ahead in the wizard
- **Reorder flow** - Cannot change step sequence
- **Generate final outputs** - Not responsible for slides/reports
- **Invent information** - Only extracts what's in the input
- **Talk to users** - Only returns structured JSON to the engine

## When is it Used?

### Primary Path: UI Events (No LLM)
```
User clicks "E-commerce" → Frontend sends ui_event → Engine processes directly
```
**Deterministic, fast, no LLM cost**

### Fallback Path: Free Text (Uses Orchestrator)
```
User types "we sell online" → Orchestrator extracts → Returns {industry: "ecommerce"}
```
**Flexible, LLM-powered, higher latency**

## Orchestrator Architecture

```
User free text
     │
     ▼
┌─────────────────────────────────┐
│   Wizard Turn Endpoint          │
│   Detects: user_message present │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  OrchestratorService.extract()  │
│  • Current step context         │
│  • Blueprint summary            │
│  • Field schema                 │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│        LLM Provider             │
│  (OpenAI/Gemini/Claude)         │
│                                 │
│  System: ORCHESTRATOR_PROMPT    │
│  User: Extraction prompt        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│       Returns JSON              │
│  {                              │
│    extracted_fields: {...},     │
│    confidence: "high|med|low",  │
│    suggested_options: [...]     │
│  }                              │
└────────────┬────────────────────┘
             │
             ▼
     Engine validates & proceeds
```

## System Prompt

```
You are a Wizard Orchestrator operating inside a product engine.

You are NOT a chatbot.
You are NOT a creative assistant.

You act as a PROJECT MANAGER controlling a structured wizard flow.

MISSION:
Help the engine extract structured information from user input
and keep the wizard moving forward without breaking the step logic.

RULES:
- Never skip steps
- Never reorder steps
- Never generate final outputs
- Never invent information

STATE:
You receive the current_step and project_blueprint.
You may only extract or suggest data relevant to the current_step.

IF USER INPUT IS VAGUE:
- Extract what is possible
- Mark fields as "draft"
- Suggest 2–3 reasonable options

OUTPUT:
Return ONLY valid JSON with:
- extracted_fields (field -> value)
- confidence (high|medium|low)
- suggested_options (if needed)

You do not talk to the user.
You assist the engine.
```

## Example Flows

### Example 1: Clear Input (High Confidence)

**Context:**
- Step: `context`
- Field: `industry`
- User input: "We're an e-commerce company"

**Orchestrator extracts:**
```json
{
  "extracted_fields": {
    "industry": "ecommerce"
  },
  "confidence": "high",
  "suggested_options": []
}
```

**Engine:** Accepts and advances

---

### Example 2: Vague Input (Low Confidence)

**Context:**
- Step: `context`
- Field: `industry`
- User input: "We sell stuff online to businesses"

**Orchestrator extracts:**
```json
{
  "extracted_fields": {
    "industry": null
  },
  "confidence": "low",
  "suggested_options": ["ecommerce", "b2b_services", "saas"]
}
```

**Engine:** Can prompt user to clarify or show suggested options

---

### Example 3: Multi-field Input (Extracts Current Step Only)

**Context:**
- Step: `context`
- Field: `industry`
- User input: "We're a SaaS company targeting managers with a budget of 10k"

**Orchestrator extracts:**
```json
{
  "extracted_fields": {
    "industry": "saas"
  },
  "confidence": "high",
  "suggested_options": []
}
```

**Note:** Even though the user mentioned "managers" and "10k budget", the orchestrator ONLY extracts data for the current step (`context`). It ignores information about future steps.

---

### Example 4: Off-topic Input

**Context:**
- Step: `objective`
- Field: `primary_goal`
- User input: "What time is it?"

**Orchestrator extracts:**
```json
{
  "extracted_fields": {},
  "confidence": "low",
  "suggested_options": []
}
```

**Engine:** Returns validation error or asks user to provide relevant input

---

## Implementation

### In Code

The orchestrator is implemented in [app/services/orchestrator_service.py](../app/services/orchestrator_service.py):

```python
orchestrator = OrchestratorService(llm_provider)
result = await orchestrator.extract_field(
    user_message="We're in e-commerce",
    session=session,
    expected_field="industry"
)
```

### Automatic Usage

When a user sends `user_message` instead of `ui_event`, the wizard turn endpoint automatically:

1. Initializes the orchestrator
2. Passes current step context
3. Gets structured extraction
4. Validates against schema
5. Proceeds with normal flow

### Configuration

The orchestrator uses the same LLM provider as generation:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## Benefits

✅ **Flexible input** - Users can type naturally
✅ **Structured output** - Always returns valid JSON
✅ **Context-aware** - Knows current step and blueprint
✅ **Confidence scoring** - Indicates extraction quality
✅ **Suggestion capability** - Helps with vague inputs
✅ **Step isolation** - Never leaks future step data

## Tradeoffs

### UI Events (Preferred)
- ✅ Fast (no LLM call)
- ✅ Free (no API cost)
- ✅ 100% accurate
- ❌ Less flexible

### Free Text + Orchestrator (Fallback)
- ✅ Very flexible
- ✅ Natural language
- ❌ LLM latency (~1-2s)
- ❌ API cost per request
- ❌ ~95% accuracy

## Best Practices

1. **Prefer UI events** - Use structured inputs when possible
2. **Fallback gracefully** - Use orchestrator for free text
3. **Validate confidence** - Check confidence level before accepting
4. **Show suggestions** - Present suggested_options to user if confidence is low
5. **Log extractions** - Monitor orchestrator performance

## Monitoring

Track orchestrator usage:

```python
logger.info("orchestrator_extracted",
           step=current_step,
           field=expected_field,
           confidence=result.get("confidence"))
```

Key metrics:
- **Extraction success rate** - % of high confidence extractions
- **Average confidence** - Overall extraction quality
- **Suggestion frequency** - How often suggestions are needed
- **Latency** - Time to extract (LLM call overhead)

## Testing

Test the orchestrator with various inputs:

```python
# Clear input
result = await orchestrator.extract_field(
    "We're an e-commerce company",
    session,
    "industry"
)
assert result["confidence"] == "high"
assert result["extracted_fields"]["industry"] == "ecommerce"

# Vague input
result = await orchestrator.extract_field(
    "We sell things",
    session,
    "industry"
)
assert result["confidence"] == "low"
assert len(result["suggested_options"]) > 0
```

---

## Summary

The Wizard Orchestrator is a **specialized extraction tool**, not a general-purpose AI. It:

- Operates under strict rules
- Never breaks wizard flow
- Only extracts current-step data
- Returns structured output
- Assists the engine, not the user

This design keeps the wizard **deterministic and predictable** while still allowing **flexible input methods**.
