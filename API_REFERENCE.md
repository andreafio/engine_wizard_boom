# API Quick Reference

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require headers:
```
X-Tenant-Id: boom
X-Api-Key: API_KEY_123
```

---

## Endpoints

### 1. Start Session
**POST** `/v1/sessions/start`

Creates a new wizard session.

**Request:**
```json
{
  "context": {
    "page_url": "https://example.com",
    "utm_source": "google"
  },
  "consent": {
    "gdpr": true,
    "profiling": true
  }
}
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "wizard": {
    "wizard_id": "strategic_snapshot_v1",
    "current_step": "context",
    "progress": 0.0,
    "blueprint": {...},
    "ui": {
      "type": "single_select",
      "label": "In che settore opera la tua azienda?",
      "field": "industry",
      "options": [
        {"id": "ecommerce", "label": "E-commerce"},
        {"id": "b2b_services", "label": "Servizi B2B"}
      ]
    },
    "validation": {
      "required_fields": ["industry", "business_model", "company_size"],
      "errors": []
    },
    "events": []
  }
}
```

---

### 2. Wizard Turn
**POST** `/v1/wizard/turn`

Process user input and advance wizard.

**Request:**
```json
{
  "session_id": "sess_abc123",
  "event_id": "evt_unique_uuid",
  "ui_event": {
    "type": "selected_option",
    "field": "industry",
    "value": "ecommerce"
  },
  "context": {
    "page_url": "https://example.com"
  }
}
```

**UI Event Types:**
- `selected_option` - Single selection
- `multi_selected` - Multiple selections
- `text_submitted` - Text input
- `slider_changed` - Slider value
- `clicked` - Button click

**Response:**
```json
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

---

### 3. Get Session
**GET** `/v1/sessions/{session_id}`

Retrieve current session state.

**Response:**
```json
{
  "session_id": "sess_abc123",
  "wizard": {...}
}
```

---

### 4. Confirm Review
**POST** `/v1/wizard/confirm`

Confirm or edit at review step.

**Request:**
```json
{
  "session_id": "sess_abc123",
  "event_id": "evt_confirm",
  "action": "confirm",  // or "edit"
  "step": "review"
}
```

**Response (confirm):**
```json
{
  "status": "confirmed",
  "message": "Wizard completato! Procedi alla generazione."
}
```

**Response (edit):**
```json
{
  "status": "editing",
  "message": "Torna indietro per modificare.",
  "wizard": {...}
}
```

---

### 5. Generate Output
**POST** `/v1/wizard/generate`

Generate final presentation and report.

**Request:**
```json
{
  "session_id": "sess_abc123",
  "event_id": "evt_generate",
  "format": "json"  // json, html, pdf
}
```

**Response:**
```json
{
  "presentation": {
    "slides": [
      {
        "title": "Executive Summary",
        "bullets": [
          "Obiettivo: Generare nuovi lead B2B",
          "Target: Manager nel settore e-commerce",
          "Budget: €5.000-€10.000/mese"
        ]
      },
      {
        "title": "Strategia Canali",
        "bullets": [
          "Google Ads (Search): Lead generation",
          "LinkedIn Ads: Targeting professionale",
          "Email Marketing: Nurturing lead"
        ]
      }
    ]
  },
  "report": {
    "sections": [
      {
        "title": "Executive Summary",
        "content": "Questo piano strategico si concentra sulla generazione di lead B2B nel settore e-commerce..."
      },
      {
        "title": "Analisi Situazione",
        "content": "L'azienda opera nel settore e-commerce con un modello B2B..."
      }
    ],
    "assumptions": [
      "Budget mensile di €5.000-€10.000",
      "Target: Manager e decision maker",
      "Timeline: Inizio entro 1 mese"
    ],
    "next_steps": [
      "Setup account Google Ads",
      "Creazione landing page ottimizzate",
      "Configurazione tracking e analytics",
      "Launch campagne pilota"
    ]
  }
}
```

---

### 6. Delete Session
**DELETE** `/v1/sessions/{session_id}`

Delete a session.

**Response:**
```json
{
  "status": "deleted",
  "session_id": "sess_abc123"
}
```

---

### 7. Health Check
**GET** `/health`

Check API health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "env": "dev"
}
```

---

## Wizard Steps

1. **context** (14.3%)
   - industry
   - business_model
   - company_size

2. **objective** (28.6%)
   - primary_goal
   - goal_note (optional)

3. **target_market** (42.9%)
   - target_role
   - geo_scope
   - market_notes (optional)

4. **value_prop** (57.1%)
   - offer_type
   - key_problem
   - differentiator (optional)

5. **channels_assets** (71.4%)
   - channels (1-4 selections)
   - assets_ready
   - assets_notes (optional)

6. **constraints** (85.7%)
   - budget_range
   - timing
   - constraints_notes (optional)

7. **review** (100%)
   - user_confirmation

8. **completed**
   - Ready for generation

---

## UI Component Types

### single_select
```json
{
  "type": "single_select",
  "label": "Question text",
  "field": "field_name",
  "options": [
    {"id": "value1", "label": "Label 1"},
    {"id": "value2", "label": "Label 2"}
  ]
}
```

### multi_select
```json
{
  "type": "multi_select",
  "label": "Select multiple",
  "field": "field_name",
  "options": [...],
  "constraints": {
    "min": 1,
    "max": 4
  }
}
```

### short_text
```json
{
  "type": "short_text",
  "label": "Enter text",
  "field": "field_name",
  "constraints": {
    "placeholder": "Placeholder text"
  }
}
```

### long_text
```json
{
  "type": "long_text",
  "label": "Enter detailed text",
  "field": "field_name",
  "constraints": {
    "placeholder": "Placeholder text"
  }
}
```

### confirmation
```json
{
  "type": "confirmation",
  "label": "Confirm or edit",
  "field": "user_confirmation",
  "options": [
    {"id": "confirm", "label": "Conferma"},
    {"id": "edit", "label": "Modifica"}
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "detail": "Campo obbligatorio: industry"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials",
  "detail": "Invalid tenant ID"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "detail": "Session not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "An error occurred"
}
```

---

## Example Flow

```bash
# 1. Start session
curl -X POST http://localhost:8000/v1/sessions/start \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{"context":{},"consent":{"gdpr":true}}'

# 2. Select industry
curl -X POST http://localhost:8000/v1/wizard/turn \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "event_id": "evt_1",
    "ui_event": {
      "type": "selected_option",
      "field": "industry",
      "value": "ecommerce"
    }
  }'

# 3. Continue filling fields...
# ... (repeat for each field)

# 4. Confirm at review
curl -X POST http://localhost:8000/v1/wizard/confirm \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "event_id": "evt_confirm",
    "action": "confirm",
    "step": "review"
  }'

# 5. Generate output
curl -X POST http://localhost:8000/v1/wizard/generate \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "event_id": "evt_generate",
    "format": "json"
  }'
```

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test all endpoints directly.
