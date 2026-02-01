# LLM Roles Documentation

This document describes the three distinct LLM roles in the Wizard BOOM engine and their strict operational boundaries.

## Overview

The system uses **three independent LLM agents** with completely different responsibilities:

1. **Orchestrator** - Field extraction during wizard flow
2. **Reviewer** - Blueprint review before generation
3. **Generator** - Final output creation after confirmation

These agents **NEVER** overlap in functionality and operate at different stages of the workflow.

---

## 1. Orchestrator (Field Extraction Agent)

### Role
A backend assistant that helps extract structured data from free-text user input during the wizard flow.

### When It Runs
- Only during active wizard steps (CONTEXT → OBJECTIVE → ... → CONSTRAINTS)
- Only when user provides free text instead of using UI components
- Never after blueprint is completed

### Core Identity
```
You are a Wizard Orchestrator inside a backend engine.
You are NOT a chatbot. You do NOT talk to the end user.
```

### Input
```json
{
  "current_step": "context|objective|...",
  "step_required_fields": ["industry", "business_model"],
  "step_ui_fields": [...],
  "project_blueprint": {...},
  "user_message": "We are a B2B SaaS startup..."
}
```

### Task
Extract **ONLY** information relevant to the current step fields.

### Critical Rules
- ✅ Extract only fields from `step_ui_fields`
- ❌ Never extract fields from other steps
- ❌ Never invent metrics, KPIs, or numeric data
- ❌ Never skip steps or reorder wizard flow
- ✅ Mark data as "draft" if confidence is low/medium
- ✅ Mark as "confirmed" only if user statement is explicit

### Output Format
```json
{
  "extracted_fields": {
    "industry": "B2B SaaS"
  },
  "field_status": {
    "industry": "confirmed"
  },
  "confidence": "high|medium|low",
  "suggested_options": [
    {
      "field": "business_model",
      "options": [
        {"id": "subscription", "label": "Subscription"},
        {"id": "freemium", "label": "Freemium"}
      ]
    }
  ]
}
```

### Examples

**Good Extraction (Explicit)**
```
User: "We are a B2B SaaS company targeting CMOs in Italy"
Output:
{
  "extracted_fields": {
    "industry": "B2B SaaS",
    "target_role": "CMO",
    "geo_scope": "Italia"
  },
  "field_status": {
    "industry": "confirmed",
    "target_role": "confirmed",
    "geo_scope": "confirmed"
  },
  "confidence": "high"
}
```

**Draft Extraction (Vague)**
```
User: "We sell software to businesses"
Output:
{
  "extracted_fields": {
    "industry": "B2B Software"
  },
  "field_status": {
    "industry": "draft"
  },
  "confidence": "medium",
  "suggested_options": [...]
}
```

**No Extraction (Requires Clarification)**
```
User: "What options do I have?"
Output:
{
  "extracted_fields": {},
  "field_status": {},
  "confidence": "low",
  "suggested_options": [
    {
      "field": "industry",
      "options": [
        {"id": "b2b_saas", "label": "B2B SaaS"},
        {"id": "ecommerce", "label": "E-commerce"},
        {"id": "consulting", "label": "Consulenza"}
      ]
    }
  ]
}
```

**Anti-Pattern (Inventing Data) ❌**
```
User: "We want to grow our business"
BAD OUTPUT:
{
  "extracted_fields": {
    "primary_goal": "Lead Generation",
    "kpi_target": "CPL: 25€, CAC: 150€"  // ❌ INVENTED!
  }
}

CORRECT OUTPUT:
{
  "extracted_fields": {},
  "suggested_options": [
    {
      "field": "primary_goal",
      "options": [
        {"id": "brand_awareness", "label": "Brand Awareness"},
        {"id": "lead_gen", "label": "Lead Generation"}
      ]
    }
  ]
}
```

---

## 2. Reviewer (Blueprint Review Agent)

### Role
A review summarizer that prepares a concise confirmation summary before final generation.

### When It Runs
- After blueprint is complete but before generation
- When user requests review via `/review` endpoint or before `/generate`
- Never during wizard flow or after generation

### Core Identity
```
You are a review summarizer for a wizard.
Do NOT generate the final presentation or report.
```

### Input
```json
{
  "context": {
    "value": {"industry": "B2B SaaS", "business_model": "Subscription"},
    "status": "confirmed"
  },
  "objective": {
    "value": {"primary_goal": "Lead Generation"},
    "status": "draft"
  },
  ...
}
```

### Task
Produce a concise review for user confirmation:
- List **confirmed** items clearly (facts ready to use)
- List **drafts** as "to confirm" (needs validation)

### Critical Rules
- ✅ Only list items that have actual values (not empty/null)
- ✅ Confirmed items: `status = "confirmed"`
- ✅ To confirm items: `status = "draft"` or status missing
- ✅ Keep descriptions concise (1 line per item)
- ❌ Do NOT generate slides or reports
- ❌ Do NOT invent additional information

### Output Format
```json
{
  "review": {
    "confirmed": [
      "Settore: B2B SaaS",
      "Business Model: Subscription"
    ],
    "to_confirm": [
      "Obiettivo: Lead Generation (da confermare)"
    ]
  }
}
```

### Examples

**Good Review (Mixed Status)**
```json
Blueprint:
{
  "context": {
    "value": {"industry": "B2B SaaS"},
    "status": "confirmed"
  },
  "objective": {
    "value": {"primary_goal": "Lead Generation"},
    "status": "draft"
  }
}

Output:
{
  "review": {
    "confirmed": [
      "Settore: B2B SaaS",
      "Business Model: Subscription"
    ],
    "to_confirm": [
      "Obiettivo: Lead Generation (da confermare)",
      "Budget: 5k-10k (da validare)"
    ]
  }
}
```

**Good Review (All Confirmed - Ready)**
```json
Blueprint: all sections have status="confirmed"

Output:
{
  "review": {
    "confirmed": [
      "Settore: E-commerce",
      "Obiettivo: Brand Awareness",
      "Target: End Consumer",
      "Budget: 10k confermato"
    ],
    "to_confirm": []
  }
}
```

**Anti-Pattern (Adding Extra Info) ❌**
```json
BAD OUTPUT:
{
  "review": {
    "confirmed": [
      "Settore: B2B SaaS",
      "Competitive advantage: Strong tech stack"  // ❌ NOT IN BLUEPRINT
    ]
  }
}

CORRECT OUTPUT:
{
  "review": {
    "confirmed": [
      "Settore: B2B SaaS"
    ],
    "to_confirm": []
  }
}
```

---

## 3. Generator (Strategic Output Agent)

### Role
A strategic consultant that creates executive-ready presentations and reports from a completed blueprint.

### When It Runs
- Only after blueprint review is complete and confirmed
- When `/generate` endpoint is called
- Never during wizard flow or review phase

### Core Identity
```
You are a strategic output generator for an executive-ready deliverable.
```

### Input
```json
{
  "context": {
    "value": {"industry": "B2B SaaS", ...},
    "status": "confirmed"
  },
  "objective": {
    "value": {"primary_goal": "Lead Generation", ...},
    "status": "confirmed"
  },
  ...
}
```

### Task
Generate two outputs:
- **A) Presentation**: 6–8 slides with 3–5 bullets each
- **B) Report**: 1–2 pages equivalent (6 sections)

### Blueprint-Only Rules
1. ✅ Use ONLY **confirmed** fields as facts
2. ❌ Draft fields must NOT be stated as facts (only as assumptions)
3. ❌ Do not invent numbers, KPIs, market sizes, benchmarks
4. ✅ If assumptions are necessary, list them in `assumptions[]`
5. ✅ Keep tone professional, concise, no hype

### Output Format
```json
{
  "slides": [
    {
      "title": "Strategia Marketing B2B SaaS",
      "bullets": [
        "Focus su Lead Generation per CMO target",
        "Canali prioritari: LinkedIn, Google Ads, Content Marketing",
        "Budget allocato su Q1-Q2 2026"
      ]
    },
    ...
  ],
  "report_sections": [
    {
      "title": "Executive Summary",
      "content": "Strategia marketing per [company] nel settore B2B SaaS..."
    },
    ...
  ],
  "assumptions": [
    "Mancano dati quantitativi (CPL, CAC): priorità qualitative"
  ],
  "next_steps": [
    "Definire KPI target con stakeholder",
    "Validare budget con CFO",
    "Avviare test campagne LinkedIn"
  ]
}
```

### Constraints
- ✅ Slides: exactly 6 to 8
- ✅ Bullets per slide: 3 to 5
- ✅ Bullets max length: 140 characters
- ✅ No duplicates in bullets
- ✅ Report sections: exactly 5 to 7
- ✅ Language: Italian
- ✅ Tone: Professional, executive-level, data-driven

### Examples

**Good Generation (Data-Driven)**
```json
Blueprint:
{
  "objective": {"primary_goal": "Lead Generation", "goal_note": "Target CPL: 25€"},
  "target_market": {"target_role": "CMO", "geo_scope": "Italia"}
}

Output:
{
  "slides": [
    {
      "title": "Obiettivo: Lead Generation B2B",
      "bullets": [
        "Target: CMO in Italia",
        "CPL obiettivo: 25€ (dato fornito)",
        "Focus su qualità lead vs. volume"
      ]
    }
  ],
  "assumptions": []
}
```

**Good Generation (Missing Metrics)**
```json
Blueprint:
{
  "objective": {"primary_goal": "Brand Awareness"},
  "constraints": {"budget_range": "5k-10k"}
}

Output:
{
  "slides": [...],
  "assumptions": [
    "Mancano dati quantitativi (CPL, CAC, conversioni): priorità qualitative",
    "Budget range indicativo, da validare con CFO"
  ]
}
```

**Anti-Pattern (Inventing Data) ❌**
```json
Blueprint:
{
  "objective": {"primary_goal": "Lead Generation"}
  // No KPI provided
}

BAD OUTPUT:
{
  "slides": [
    {
      "title": "KPI Target",
      "bullets": [
        "CPL target: 25€",  // ❌ INVENTED
        "CAC: 150€",        // ❌ INVENTED
        "Conversion: 5%"    // ❌ INVENTED
      ]
    }
  ]
}

CORRECT OUTPUT:
{
  "slides": [
    {
      "title": "Obiettivi Qualitativi",
      "bullets": [
        "Generazione lead qualificati",
        "Posizionamento brand nel settore",
        "Da definire: KPI quantitativi con team"
      ]
    }
  ],
  "assumptions": [
    "Mancano dati quantitativi: priorità qualitative",
    "KPI da definire in fase di planning esecutivo"
  ]
}
```

---

## Validation & Guardrails

### Orchestrator Validation
**Schema**: `OrchestratorOutput` (Pydantic)
- ✅ `field_status` must be "draft" or "confirmed"
- ✅ `confidence` must be "high", "medium", or "low"
- ✅ `suggested_options`: max 3 per field
- ✅ Only fields from current step

**Location**: `app/services/orchestrator_schema.py`

### Reviewer Validation
**Schema**: `ReviewOutput` (Pydantic)
- ✅ `confirmed`: list of confirmed items
- ✅ `to_confirm`: list of draft items
- ✅ Helper: `is_ready_for_generation()` - True if no to_confirm items
- ✅ Helper: `has_items_to_confirm()` - True if to_confirm not empty
- ✅ Helper: `total_items()` - Count of all items

**Location**: `app/services/review_schema.py`

### Generator Validation
**Schema**: `GenerationOutput` (Pydantic)
- ✅ Slides: 6-8 exactly
- ✅ Bullets: 3-5 per slide
- ✅ Bullet length: max 140 chars
- ✅ No duplicate bullets (case-insensitive)
- ✅ Report sections: 5-7 exactly

**Location**: `app/llm/schemas.py`

**Guardrails**: `apply_all_guardrails()`
1. ✅ Enforce assumptions when no metrics
2. ✅ Detect invented numbers (not in blueprint)
3. ✅ Move invented claims to assumptions
4. ✅ Remove bullets with unverified data

**Location**: `app/services/generation_guardrails.py`

---

## Workflow Separation

```
┌─────────────────────────────────────────────┐
│         WIZARD FLOW (Step 1-6)              │
│                                             │
│  User → Orchestrator → Extract Fields       │
│         (draft/confirmed)                   │
│                                             │
│  Blueprint building...                      │
│                                             │
└─────────────────────────────────────────────┘
                    ↓
         [Blueprint Complete]
                    ↓
┌─────────────────────────────────────────────┐
│         REVIEW PHASE                        │
│                                             │
│  Blueprint → Reviewer → Confirmation List   │
│              (confirmed vs to_confirm)      │
│                                             │
│  User reviews and confirms...               │
│                                             │
└─────────────────────────────────────────────┘
                    ↓
         [User Confirms Review]
                    ↓
┌─────────────────────────────────────────────┐
│         GENERATION PHASE                    │
│                                             │
│  Blueprint → Generator → Slides + Report    │
│              (validated output)             │
│                                             │
└─────────────────────────────────────────────┘
```

**Key Principle**: The three agents **NEVER** run simultaneously and operate in strict sequence.

---

## Testing

### Orchestrator Tests
**File**: `tests/test_orchestrator.py`

Key scenarios:
- ✅ Extracts explicit values as "confirmed"
- ✅ Marks vague input as "draft"
- ✅ Provides suggestions when unclear
- ✅ Does NOT invent metrics
- ✅ Fallback on LLM failure

### Reviewer Tests
**File**: `tests/test_review.py`

Key scenarios:
- ✅ Separates confirmed and draft items
- ✅ Shows ready for generation when all confirmed
- ✅ Ignores empty sections
- ✅ Fallback on LLM failure
- ✅ Concise format (1 line per item)

### Generator Tests
**File**: `tests/test_generation.py`

Key scenarios:
- ✅ Validates output schema
- ✅ Adds assumptions when no metrics
- ✅ Returns fallback on bad LLM response
- ✅ Moves invented numbers to assumptions
- ✅ Enforces bullet hygiene (length, duplicates)

---

## Summary

| Aspect | Orchestrator | Reviewer | Generator |
|--------|-------------|----------|-----------|
| **Phase** | During wizard | After wizard, before generation | After review confirmed |
| **Input** | User free text | Completed blueprint + status | Confirmed blueprint |
| **Output** | Extracted fields + status | Confirmed vs to_confirm lists | Slides + Report |
| **Validation** | OrchestratorOutput | ReviewOutput | GenerationOutput + guardrails |
| **Can invent data?** | ❌ NO | ❌ NO | ❌ NO |
| **Can talk to user?** | ❌ NO | ❌ NO | ❌ NO |
| **Language** | Italian/English | Italian | Italian only |
| **Confidence tracking** | ✅ Yes (high/med/low) | ❌ N/A | ❌ N/A |
| **Status tracking** | ✅ Yes (draft/confirmed) | ✅ Yes (separates by status) | ❌ N/A |
| **Assumptions** | ❌ N/A | ❌ N/A | ✅ Yes (explicit list) |

All three agents are **assistants to the engine**, not user-facing chatbots.
