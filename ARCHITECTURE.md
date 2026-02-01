# BOOM Wizard Engine - Architecture Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Google AI Studio / Custom React App               │  │
│  │  • Renders UI components (chips, forms, buttons)          │  │
│  │  • Displays wizard progress & blueprint                   │  │
│  │  • Sends user events to backend                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS + JSON
                       │ Headers: X-Tenant-Id, X-Api-Key
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Routes                                              │   │
│  │  • POST /v1/sessions/start                              │   │
│  │  • POST /v1/wizard/turn      ◄── Main endpoint          │   │
│  │  • POST /v1/wizard/confirm                              │   │
│  │  • POST /v1/wizard/generate                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────┴───────────────────────────────────┐    │
│  │  Middleware Layer                                       │    │
│  │  • Authentication (API Key + HMAC)                      │    │
│  │  • Rate Limiting                                        │    │
│  │  • CORS                                                 │    │
│  │  • Structured Logging (PII Masking)                     │    │
│  └─────────────────────────────────────────────────────────┘   │
└───────────┬────────────────────────────────┬────────────────────┘
            │                                │
            ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│   WIZARD ENGINE CORE     │    │     STORAGE LAYER            │
│                          │    │                              │
│  ┌────────────────────┐  │    │  ┌────────────────────────┐ │
│  │  State Machine     │  │    │  │  Redis                 │ │
│  │  • 7 Steps         │  │    │  │  • Sessions (TTL)      │ │
│  │  • Flow Control    │  │    │  │  • Fast State          │ │
│  │  • Validation      │  │◄───┼──┤  • Key: session:{id}   │ │
│  └────────────────────┘  │    │  └────────────────────────┘ │
│                          │    │                              │
│  ┌────────────────────┐  │    │  ┌────────────────────────┐ │
│  │  UI Builders       │  │    │  │  PostgreSQL (Optional) │ │
│  │  • Directives      │  │    │  │  • Events              │ │
│  │  • Components      │  │    │  │  • Analytics           │ │
│  └────────────────────┘  │    │  │  • Tenants             │ │
│                          │    │  └────────────────────────┘ │
│  ┌────────────────────┐  │    └──────────────────────────────┘
│  │  Blueprint         │  │
│  │  • Sections        │  │
│  │  • Statuses        │  │
│  └────────────────────┘  │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                    LLM PROVIDERS (Optional)                   │
│                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   OpenAI    │    │   Gemini    │    │   Claude    │     │
│  │  GPT-4o     │    │  Gemini Pro │    │  Claude 3   │     │
│  │             │    │             │    │   Sonnet    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                               │
│  Used for:                                                    │
│  • Field extraction from free text (fallback)                │
│  • Final generation (slides + report)                        │
│  • Optional suggestions                                      │
└──────────────────────────────────────────────────────────────┘
```

## Request Flow: Wizard Turn

```
User clicks option in frontend
         │
         ▼
Frontend sends ui_event
{
  session_id: "sess_abc",
  event_id: "evt_123",     ◄── Idempotency key
  ui_event: {
    type: "selected_option",
    field: "industry",
    value: "ecommerce"
  }
}
         │
         ▼
┌────────────────────────┐
│  Security Middleware   │
│  • Verify API Key      │
│  • Check HMAC (opt)    │
│  • Rate Limit          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Idempotency Check     │
│  Already processed?    │──Yes──► Return cached response
└────────┬───────────────┘
         │ No
         ▼
┌────────────────────────┐
│  Load Session          │
│  • Get from Redis      │
│  • Validate tenant     │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Extract Input         │
│  • Parse ui_event      │
│  • Get field & value   │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Validate Input        │
│  • Check schema        │
│  • Check constraints   │──Fail──► Return 400 error
└────────┬───────────────┘
         │ Pass
         ▼
┌────────────────────────┐
│  Update Blueprint      │
│  • Set field value     │
│  • Status: draft       │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Check Step Complete   │
│  All required fields?  │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Advance Step (if OK)  │
│  • Mark confirmed      │
│  • Move to next step   │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Build UI Directive    │
│  • Get next field      │
│  • Build component     │
│  • Calculate progress  │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Save Session          │
│  • Update Redis        │
│  • Add conversation    │
└────────┬───────────────┘
         │
         ▼
Return response
{
  assistant_message: "Next question...",
  wizard: {
    current_step: "objective",
    progress: 28.6,
    blueprint: {...},
    ui: {...}
  }
}
         │
         ▼
Frontend updates UI
```

## Data Flow: Blueprint Evolution

```
Step 1: CONTEXT
─────────────────
{
  context: {
    value: {
      industry: "ecommerce",
      business_model: "b2c",
      company_size: "small"
    },
    status: "confirmed"  ◄── After all fields filled
  },
  objective: {value: null, status: "draft"},
  ...
}

Step 2: OBJECTIVE
─────────────────
{
  context: {value: {...}, status: "confirmed"},
  objective: {
    value: {
      primary_goal: "leads",
      goal_note: "Double leads in 6 months"
    },
    status: "confirmed"
  },
  target_market: {value: null, status: "draft"},
  ...
}

... continues through all steps ...

Step 7: REVIEW
──────────────
{
  context: {value: {...}, status: "confirmed"},
  objective: {value: {...}, status: "confirmed"},
  target_market: {value: {...}, status: "confirmed"},
  value_prop: {value: {...}, status: "confirmed"},
  channels_assets: {value: {...}, status: "confirmed"},
  constraints: {value: {...}, status: "confirmed"}
}

After CONFIRM
─────────────
current_step: "completed"
→ Ready for generation
```

## Generation Flow

```
User confirms wizard
         │
         ▼
POST /v1/wizard/generate
         │
         ▼
┌────────────────────────┐
│  Load Session          │
│  Verify completed      │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Build Prompt          │
│  • Extract blueprint   │
│  • Format context      │
│  • Add instructions    │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Call LLM Provider     │
│  • OpenAI/Gemini       │
│  • Request JSON mode   │
│  • Generate content    │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Parse Response        │
│  • Validate JSON       │
│  • Structure slides    │
│  • Build report        │
└────────┬───────────────┘
         │
         ▼
Return
{
  presentation: {
    slides: [...]
  },
  report: {
    sections: [...],
    assumptions: [...],
    next_steps: [...]
  }
}
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      PRODUCTION                          │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Frontend   │    │   API LB     │    │   Redis   │ │
│  │   (Vercel)   │───▶│  (AWS ALB)   │───▶│ (Managed) │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
│                              │                           │
│                              ▼                           │
│                      ┌──────────────┐                    │
│                      │   Wizard API │                    │
│                      │  (ECS/K8s)   │                    │
│                      │  • Auto-scale│                    │
│                      │  • Health chk│                    │
│                      └──────┬───────┘                    │
│                             │                            │
│                             ▼                            │
│                      ┌──────────────┐                    │
│                      │  PostgreSQL  │                    │
│                      │   (RDS)      │                    │
│                      └──────────────┘                    │
│                                                          │
│  Monitoring: CloudWatch / Datadog                       │
│  Logs: CloudWatch Logs / ELK                            │
│  Secrets: AWS Secrets Manager                           │
└─────────────────────────────────────────────────────────┘
```

## State Machine Diagram

```
       START
         │
         ▼
    ┌─────────┐
    │ CONTEXT │ Step 1 (0-14%)
    └────┬────┘
         │ All required fields? Yes
         ▼
   ┌──────────┐
   │OBJECTIVE │ Step 2 (14-29%)
   └────┬─────┘
        │
        ▼
┌───────────────┐
│TARGET MARKET  │ Step 3 (29-43%)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  VALUE PROP   │ Step 4 (43-57%)
└───────┬───────┘
        │
        ▼
┌───────────────────┐
│CHANNELS & ASSETS  │ Step 5 (57-71%)
└────────┬──────────┘
         │
         ▼
  ┌─────────────┐
  │ CONSTRAINTS │ Step 6 (71-86%)
  └──────┬──────┘
         │
         ▼
    ┌────────┐
    │ REVIEW │ Step 7 (86-100%)
    └───┬────┘
        │
        ├──► Edit → Back to CONTEXT
        │
        └──► Confirm
             │
             ▼
       ┌───────────┐
       │ COMPLETED │
       └─────┬─────┘
             │
             ▼
        GENERATION
             │
             ▼
    ┌─────────────────┐
    │ SLIDES + REPORT │
    └─────────────────┘
```

## Security Flow

```
Request arrives
      │
      ▼
┌──────────────────┐
│ Extract Headers  │
│ • X-Tenant-Id    │
│ • X-Api-Key      │
│ • X-Signature    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Verify Tenant    │
│ • Tenant exists? │
│ • Key matches?   │
└────────┬─────────┘
         │ ✓
         ▼
┌──────────────────┐
│ Verify HMAC      │ (Optional)
│ • Signature OK?  │
└────────┬─────────┘
         │ ✓
         ▼
┌──────────────────┐
│ Rate Limit Check │
│ • Within limits? │
└────────┬─────────┘
         │ ✓
         ▼
    Process Request
```

## Logging & Monitoring

```
Every Request
     │
     ▼
┌─────────────────────┐
│ Structured Logging  │
│ • Request ID        │
│ • Tenant ID         │
│ • Session ID        │
│ • Action            │
│ • Duration          │
│ • Status            │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ PII Masking         │
│ • Email → ***       │
│ • Phone → ***       │
│ • API keys → ***    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Log Aggregation     │
│ • CloudWatch        │
│ • ELK Stack         │
│ • Datadog           │
└──────┬──────────────┘
       │
       ▼
   Dashboards & Alerts
```

---

These diagrams visualize the complete architecture and data flows
of the BOOM Wizard Engine system.
