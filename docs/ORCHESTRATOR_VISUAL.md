# Wizard Orchestrator - Quick Visual Reference

## Dual Input Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
└───────────────┬─────────────────────────┬───────────────────────┘
                │                         │
        ┌───────▼───────┐         ┌──────▼──────┐
        │  UI Event     │         │  Free Text  │
        │  (Structured) │         │  (Vague)    │
        └───────┬───────┘         └──────┬──────┘
                │                        │
                │                        │
        ┌───────▼───────────────┐  ┌────▼──────────────────────┐
        │ PREFERRED PATH        │  │ FALLBACK PATH             │
        │ • Fast                │  │ • Flexible                │
        │ • Free                │  │ • LLM-powered             │
        │ • 100% accurate       │  │ • ~95% accurate           │
        └───────┬───────────────┘  └────┬──────────────────────┘
                │                        │
                │                        ▼
                │              ┌─────────────────────┐
                │              │  WIZARD ORCHESTRATOR│
                │              │  • Extract fields   │
                │              │  • Suggest options  │
                │              │  • Return confidence│
                │              └─────────┬───────────┘
                │                        │
                └────────────┬───────────┘
                             │
                     ┌───────▼────────┐
                     │  VALIDATION    │
                     │  • Schema check│
                     │  • Constraints │
                     └───────┬────────┘
                             │
                     ┌───────▼────────┐
                     │  UPDATE STATE  │
                     │  • Blueprint   │
                     │  • Progress    │
                     └───────┬────────┘
                             │
                             ▼
                      RETURN NEXT UI
```

## Orchestrator Decision Tree

```
User sends message
        │
        ▼
    Has ui_event?
        │
    ┌───┴───┐
    │       │
   YES     NO
    │       │
    │       └──► Has user_message?
    │                  │
    │              ┌───┴───┐
    │              │       │
    │             YES     NO
    │              │       │
    │              │       └──► ERROR: No input
    │              │
    │              ▼
    │     Initialize Orchestrator
    │              │
    │              ▼
    │     Call orchestrator.extract_field()
    │       • Current step
    │       • Expected field
    │       • Blueprint context
    │              │
    │              ▼
    │     LLM processes with strict rules:
    │       ❌ Never skip steps
    │       ❌ Never reorder
    │       ❌ Never invent
    │       ✅ Only extract current step
    │              │
    │              ▼
    │     Returns JSON:
    │       {
    │         extracted_fields: {...},
    │         confidence: "high|medium|low",
    │         suggested_options: [...]
    │       }
    │              │
    └──────────────┴──► MERGE paths
                   │
                   ▼
            Process field update
```

## Confidence Levels

```
┌─────────────────────────────────────────────────────────────┐
│  HIGH CONFIDENCE                                            │
│  • Clear, unambiguous input                                 │
│  • Direct match to options                                  │
│  • Engine: Accept immediately                               │
│                                                             │
│  Example: "We're an e-commerce company"                     │
│  → industry: "ecommerce" ✓                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MEDIUM CONFIDENCE                                          │
│  • Somewhat clear input                                     │
│  • 2-3 possible matches                                     │
│  • Engine: Show suggestions to user                         │
│                                                             │
│  Example: "We sell products online"                         │
│  → suggested: ["ecommerce", "b2b_services"] ?               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  LOW CONFIDENCE                                             │
│  • Vague or off-topic input                                 │
│  • No clear match                                           │
│  • Engine: Ask user to clarify or use UI                    │
│                                                             │
│  Example: "We do stuff"                                     │
│  → Can't extract, please clarify                            │
└─────────────────────────────────────────────────────────────┘
```

## Step Isolation

```
User input: "We're a SaaS company targeting managers with 10k budget"

Current step: CONTEXT
Expected field: industry

┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR BEHAVIOR                                      │
│                                                             │
│  ✅ EXTRACTS:  "SaaS" → industry                            │
│  ❌ IGNORES:   "managers" (future step: target_market)      │
│  ❌ IGNORES:   "10k budget" (future step: constraints)      │
│                                                             │
│  Reason: Never skip steps. Only extract for current step.  │
└─────────────────────────────────────────────────────────────┘

Returns:
{
  "extracted_fields": {"industry": "saas"},
  "confidence": "high",
  "suggested_options": []
}

Engine will ask about "managers" and "budget" when it reaches those steps.
```

## What Orchestrator NEVER Does

```
❌ NEVER: Skip Steps
┌────────────────────────────────────┐
│ Current: Step 2 (Objective)       │
│ User mentions: "We target CEOs"   │
│                                   │
│ ✓ Extracts: Nothing (not relevant)│
│ ✗ NEVER extracts for Step 3      │
└────────────────────────────────────┘

❌ NEVER: Generate Final Content
┌────────────────────────────────────┐
│ User: "Generate my slides"        │
│                                   │
│ ✓ Returns: No extraction          │
│ ✗ NEVER creates slides            │
│   (That's the Generator's job)   │
└────────────────────────────────────┘

❌ NEVER: Invent Information
┌────────────────────────────────────┐
│ User: "Our company does marketing"│
│ Field: company_size               │
│                                   │
│ ✓ Returns: No extraction          │
│ ✗ NEVER guesses "small" or "large"│
└────────────────────────────────────┘

❌ NEVER: Talk to User
┌────────────────────────────────────┐
│ Orchestrator returns JSON only    │
│                                   │
│ ✓ Returns: {"extracted_fields":{}}│
│ ✗ NEVER: "Can you clarify?"      │
│   (Engine handles user messages)  │
└────────────────────────────────────┘
```

## Cost Comparison

```
┌──────────────────────┬──────────┬────────┬──────────┐
│ Input Method         │ Latency  │ Cost   │ Accuracy │
├──────────────────────┼──────────┼────────┼──────────┤
│ UI Event (Chips)     │ ~50ms    │ $0     │ 100%     │
│ Free Text (Simple)   │ ~100ms   │ $0     │ ~90%     │
│ Free Text (LLM)      │ ~1-2s    │ ~$0.01 │ ~95%     │
└──────────────────────┴──────────┴────────┴──────────┘

Recommendation: Use UI events when possible
                Fall back to Orchestrator for flexibility
```

## Example API Flow with Orchestrator

```json
// Request (free text instead of ui_event)
POST /v1/wizard/turn
{
  "session_id": "sess_123",
  "event_id": "evt_456",
  "user_message": "We're in the e-commerce space"
}

// Internal: Orchestrator extraction
{
  "extracted_fields": {
    "industry": "ecommerce"
  },
  "confidence": "high",
  "suggested_options": []
}

// Response
{
  "assistant_message": "Qual è il tuo modello di business principale?",
  "wizard": {
    "current_step": "context",
    "progress": 14.3,
    "blueprint": {
      "context": {
        "value": {
          "industry": "ecommerce"
        },
        "status": "draft"
      }
    },
    "ui": {
      "type": "single_select",
      "field": "business_model",
      "label": "Qual è il tuo modello di business principale?",
      "options": [...]
    }
  }
}
```

## Monitoring Dashboard (Conceptual)

```
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATOR METRICS                                   │
├─────────────────────────────────────────────────────────┤
│  Total Extractions:     1,247                           │
│  High Confidence:       892 (71.5%) ✓                   │
│  Medium Confidence:     245 (19.6%) ~                   │
│  Low Confidence:        110 (8.9%)  ⚠                   │
│                                                         │
│  Avg Latency:          1.2s                             │
│  LLM Costs (today):    $2.45                            │
│  Success Rate:         95.3%                            │
│                                                         │
│  Most Extracted Field:  industry (342)                  │
│  Most Suggested:        ["ecommerce", "saas"]           │
└─────────────────────────────────────────────────────────┘
```

---

**Remember:** The Orchestrator is a **tool for the engine**, not a chatbot for users. It extracts structured data while respecting the wizard's deterministic flow.
