# BOOM Wizard Engine — Documentazione Completa

> Documento unificato. Sostituisce: README.md, ARCHITECTURE.md, ARCHITECTURE_OVERVIEW.md, API_REFERENCE.md, FRONTEND_INTEGRATION.md, PROJECT_SUMMARY.md, SERVICE_INTEGRATION_MAP.md, STRATEGIC_PROFILE_V2.md, QUESTION_BANK_INTEGRATION.md, INTEGRATION_STATUS.md, docs/*

---

## Indice

1. [Cos'è](#1-cosè)
2. [Stack tecnologico](#2-stack-tecnologico)
3. [Struttura del progetto](#3-struttura-del-progetto)
4. [Setup e avvio](#4-setup-e-avvio)
5. [Configurazione](#5-configurazione)
6. [Architettura](#6-architettura)
7. [Il Wizard: flusso e step](#7-il-wizard-flusso-e-step)
8. [Question Bank](#8-question-bank)
9. [Servizi business](#9-servizi-business)
10. [Strategic Profile V2](#10-strategic-profile-v2)
11. [LLM Providers](#11-llm-providers)
12. [API Reference](#12-api-reference)
13. [Integrazione frontend](#13-integrazione-frontend)
14. [Sicurezza](#14-sicurezza)
15. [Testing](#15-testing)
16. [Deploy e produzione](#16-deploy-e-produzione)
17. [Troubleshooting](#17-troubleshooting)
18. [Roadmap](#18-roadmap)

---

## 1. Cos'è

**BOOM Wizard Engine** è un backend Python/FastAPI che alimenta un wizard interattivo di marketing strategico. Guida le aziende attraverso 10 sezioni strutturate per raccogliere informazioni strategiche e generare automaticamente presentazioni e report consulenziali tramite LLM (OpenAI, Gemini, Claude).

Il backend è completamente separato dal frontend. È progettato per essere consumato da Google AI Studio o da qualsiasi applicazione web/mobile.

---

## 2. Stack tecnologico

| Layer | Tecnologia | Versione |
|---|---|---|
| Framework | FastAPI + Uvicorn | 0.109 / 0.27 |
| Sessions | Redis | 5.0.1 |
| DB persistente | PostgreSQL (opzionale) | 15 |
| LLM | OpenAI / Anthropic / Google | — |
| Validazione | Pydantic v2 | 2.5.3 |
| ORM | SQLAlchemy async | 2.0.25 |
| Auth | python-jose + passlib | — |
| Rate limiting | Slowapi | 0.1.9 |
| Logging | Structlog (JSON) | 24.1.0 |
| HTTP client | HTTPX | 0.26.0 |
| Testing | Pytest + pytest-asyncio | 7.4.4 / 0.23.3 |
| Container | Docker + Docker Compose | — |

---

## 3. Struttura del progetto

```
engine_wizard_boom/
├── app/
│   ├── main.py                        # FastAPI app, middleware, routers
│   ├── api/
│   │   ├── models.py                  # Pydantic request/response models
│   │   ├── routes_sessions.py         # Endpoints sessioni
│   │   └── routes_wizard.py           # Endpoints wizard (turn, confirm, generate)
│   ├── core/
│   │   ├── config.py                  # Settings da .env
│   │   ├── logging.py                 # Structured logging + PII masking
│   │   └── security.py                # API Key auth + HMAC verification
│   ├── wizard/
│   │   ├── schema.py                  # Definizione step, campi, UIComponentTypes
│   │   ├── state.py                   # Modelli Session e Blueprint
│   │   ├── flow.py                    # Controllo flusso e validazione step
│   │   ├── ui.py                      # Builder per UI directives
│   │   └── extraction.py              # Parsing input da UI events
│   ├── llm/
│   │   ├── provider.py                # Abstract base + Factory
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   ├── claude_provider.py
│   │   ├── prompts.py                 # Tutti i prompt template
│   │   └── schemas.py                 # Output schemas (GenerationOutput)
│   ├── storage/
│   │   └── redis_store.py             # Redis store con fallback in-memory
│   └── services/
│       ├── orchestrator_service_v2.py # Coordinatore principale
│       ├── orchestrator_service.py    # Legacy/compat
│       ├── orchestrator_schema.py
│       ├── orchestrator_utils.py      # Question bank loader
│       ├── field_extractor_service.py
│       ├── clarifier_service.py
│       ├── quality_critic_service.py
│       ├── consistency_checker_service.py
│       ├── blueprint_review_service.py
│       ├── strategic_profile_service.py
│       ├── generation_service.py
│       ├── generation_guardrails.py
│       ├── input_normalizer_service.py
│       ├── integrity_summarizer_service.py
│       ├── fact_classifier_service.py
│       ├── research_service.py
│       ├── review_service.py
│       └── review_schema.py
├── tests/                             # 16+ test file
├── docs/                              # Documentazione servizi dettagliata
├── question_bank_v1.json              # Question bank (41 domande, 10 sezioni)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── Makefile
└── start.sh / start.bat
```

---

## 4. Setup e avvio

### Docker (raccomandato)

```bash
cp .env.example .env
# Aggiungere le API key nel .env

docker-compose up -d
# API disponibile su http://localhost:8000
# Swagger: http://localhost:8000/docs
```

`docker-compose up` avvia tre container:
- **redis:6379** — session storage
- **postgres:5432** — storage opzionale per eventi/analytics
- **wizard_engine:8000** — l'API FastAPI

### Sviluppo locale

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # configurare API keys

redis-server                    # avviare Redis separatamente

python -m app.main
```

### Script quick start

```bash
./start.sh      # Unix/Mac
start.bat       # Windows
```

---

## 5. Configurazione

Tutte le variabili vanno nel file `.env` (vedi `.env.example`).

| Variabile | Descrizione | Default |
|---|---|---|
| `APP_ENV` | Ambiente (`dev`/`prod`) | `dev` |
| `PORT` | Porta API | `8000` |
| `HOST` | Bind address | `0.0.0.0` |
| `REDIS_URL` | Connessione Redis | `redis://localhost:6379/0` |
| `SESSION_TTL_SECONDS` | Scadenza sessioni | `3600` |
| `LLM_PROVIDER` | Provider LLM (`openai`/`gemini`/`claude`) | `openai` |
| `OPENAI_API_KEY` | API key OpenAI | — |
| `OPENAI_MODEL` | Modello OpenAI | `gpt-4o-mini` |
| `GEMINI_API_KEY` | API key Google | — |
| `GEMINI_MODEL` | Modello Gemini | `gemini-pro` |
| `ANTHROPIC_API_KEY` | API key Anthropic | — |
| `ANTHROPIC_MODEL` | Modello Claude | `claude-3-sonnet-20240229` |
| `TENANT_KEYS_JSON` | Mappa tenant → API key | `{"boom":"API_KEY_123"}` |
| `HMAC_SECRET` | Segreto per firma HMAC (opzionale) | — |
| `CORS_ORIGINS` | Origins permesse per CORS | `*` |

---

## 6. Architettura

### Schema generale

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                       │
│  Google AI Studio / React App / Browser                  │
│  • Renderizza UI components (chip, form, button)         │
│  • Mostra progresso e blueprint                          │
│  • Invia eventi utente al backend                        │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS + JSON
                        │ X-Tenant-Id + X-Api-Key
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   FASTAPI APPLICATION                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Middleware: Auth · Rate Limit · CORS · Logging   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ API Routes                                        │   │
│  │  POST /v1/sessions/start                         │   │
│  │  POST /v1/wizard/turn   ◄── endpoint principale  │   │
│  │  POST /v1/wizard/confirm                         │   │
│  │  POST /v1/wizard/generate                        │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
               ▼                          ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│   WIZARD ENGINE CORE    │   │      STORAGE LAYER        │
│  • State machine 10 step│   │  Redis  → sessions TTL    │
│  • Flow control         │◄──│  Postgres → eventi (opt.) │
│  • UI directive builder │   │  In-memory → test/fallback│
│  • Blueprint model      │   └──────────────────────────┘
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│              INTELLIGENT SERVICES (14)                   │
│  Orchestrator · FieldExtractor · Clarifier · Critic      │
│  BlueprintReview · StrategicProfile · Generation · ...   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   LLM PROVIDERS                          │
│   OpenAI (GPT-4o)   │   Gemini Pro   │   Claude Sonnet  │
│   • Field extraction · Clarification · Quality check     │
│   • Generation slides + report finale                    │
└─────────────────────────────────────────────────────────┘
```

### Pattern architetturali

**State Machine deterministica** — il flow del wizard non usa LLM per decidere il prossimo step. La progressione è schema-based, prevedibile, testabile.

**Provider Factory** — interfaccia astratta `LLMProvider` con factory per creare istanze OpenAI/Gemini/Claude. Cambiare provider = cambiare una variabile d'ambiente.

**Service Orchestration** — `OrchestratorServiceV2` coordina i servizi specializzati in pipeline:
```
Input → Normalize → Extract → (Clarify?) → Critique → Apply → Next Question
```

**Idempotency** — ogni request porta un `event_id`. Il risultato viene cachato in Redis con chiave `{session_id}:{event_id}`. Retry sicuri senza duplicati.

**Immutable state updates** — lo stato della sessione viene copiato, aggiornato e riscritto, mai mutato in place.

---

## 7. Il Wizard: flusso e step

### State machine

```
START
  │
  ▼
┌─────────┐       ┌───────────┐     ┌───────────┐     ┌───────────┐
│ CONTEXT │──────▶│ OBJECTIVE │────▶│   OFFER   │────▶│ AUDIENCE  │
│  0-10%  │       │  10-20%   │     │  20-30%   │     │  30-40%   │
└─────────┘       └───────────┘     └───────────┘     └───────────┘
                                                             │
                                                             ▼
┌──────────────┐  ┌───────────────┐  ┌────────────┐  ┌───────────┐
│  CONSTRAINTS │◄─│ ASSETS/TRACK. │◄─│  CHANNELS  │◄─│  FUNNEL   │
│   70-80%     │  │    60-70%     │  │  50-60%    │  │  40-50%   │
└──────────────┘  └───────────────┘  └────────────┘  └───────────┘
       │
       ▼
    ┌───────┐
    │ RISKS │ 80-90%
    └───┬───┘
        │
        ▼
    ┌────────┐
    │ REVIEW │ 90-100%
    └───┬────┘
        ├──► Edit → torna allo step richiesto
        └──► Confirm
                │
                ▼
          ┌───────────┐
          │ COMPLETED │ → pronto per /generate
          └───────────┘
```

### I 10 step

| # | Sezione | Campi chiave |
|---|---|---|
| 1 | **Context** | industry, company_size, location, founded_year |
| 2 | **Objective** | primary_goal, success_metrics, challenges |
| 3 | **Offer** | product_description, key_differentiator, pricing_model |
| 4 | **Audience** | target_role, company_size_target, geography |
| 5 | **Funnel** | awareness_channels, consideration_stage, decision_triggers |
| 6 | **Channels** | marketing_channels, channel_priority, channel_budget |
| 7 | **AssetsTracking** | existing_assets, tracking_setup, kpis |
| 8 | **Constraints** | budget_range, timeline, team_size |
| 9 | **Risks** | main_risks, mitigation_awareness |
| 10 | **Review** | user_confirmation |

### Flusso di un turn

```
Frontend invia ui_event
       │
       ▼
Middleware: auth + rate limit
       │
       ▼
Idempotency check → se già processato: restituisce risposta cachata
       │ (nuovo evento)
       ▼
Carica sessione da Redis
       │
       ▼
┌──────────────────────────────────────────┐
│   INPUT TYPE?                            │
│                                          │
│  UI Event ──────────────────────────┐   │
│  (selected_option, multi_selected,  │   │
│   text_submitted, slider_changed)   │   │
│                                     ▼   │
│  Free Text ───► FieldExtractor      │   │
│                      │              │   │
│               needs_clarification?  │   │
│                 ├─ Sì: ClarifierUI  │   │
│                 └─ No: QualityCritic│   │
│                         │           │   │
└─────────────────────────┼───────────┘   │
                          │               │
                          ▼               │
                   apply_answer() ◄───────┘
                          │
                          ▼
                   step completato?
                   ├─ No: build next field UI
                   └─ Sì: advance step → build next step UI
                          │
                          ▼
                   salva sessione in Redis
                          │
                          ▼
                   restituisce risposta al frontend
```

---

## 8. Question Bank

Le domande del wizard sono definite in `question_bank_v1.json` (41 domande, 10 sezioni). Non sono hardcoded in Python.

### Struttura di una domanda

```json
{
  "id": "context_industry",
  "section": "Context",
  "field": "blueprint.context.industry",
  "ui": {
    "type": "single_select",
    "label": "In che settore opera la tua azienda?",
    "field": "industry",
    "options": [
      {"id": "ecommerce", "label": "E-commerce"},
      {"id": "b2b_services", "label": "Servizi B2B"}
    ]
  },
  "layer": "core",
  "depends_on": [],
  "info_gain": 0.95,
  "effort": 0.1,
  "can_be_inferred": false,
  "ask_if_confidence_below": 0.8
}
```

### Layer system

| Layer | Descrizione |
|---|---|
| `core` | Domande essenziali, sempre poste (~70% del totale) |
| `deep` | Domande avanzate, poste in base a qualità/contesto (~30%) |

### Distribuzione per sezione

| Sezione | Domande |
|---|---|
| Context | 7 |
| Objective | 4 |
| Offer | 5 |
| Audience | 5 |
| Funnel | 4 |
| Channels | 4 |
| AssetsTracking | 5 |
| Constraints | 4 |
| Risks | 2 |
| Review | 1 |
| **Totale** | **41** |

### Caricamento

```python
# app/services/orchestrator_utils.py
QUESTION_BANK = load_question_bank()  # caricato all'import, lookup O(1)
```

---

## 9. Servizi business

### OrchestratorServiceV2 (`orchestrator_service_v2.py`)

Coordinatore centrale. Riceve ogni turn dall'API e smista il lavoro agli altri servizi.

```python
# Pseudo-codice del flow interno
async def handle_turn(session, payload):
    if payload.ui_event:
        value = input_normalizer.normalize(payload.ui_event)
        apply_answer(blueprint, field, value)
    elif payload.user_message:
        extraction = await field_extractor.extract_field(message, context)
        if extraction.needs_clarification:
            return await clarifier.generate_clarifier(extraction, context)
        quality = await critic.critique_answer(extraction, blueprint)
        apply_quality_hint(blueprint, quality)
        apply_answer(blueprint, extraction.field, extraction.value)
    
    next_question = pick_next_question(blueprint, question_bank)
    return build_response(session, blueprint, next_question)
```

### FieldExtractorService (`field_extractor_service.py`)

Usa LLM per estrarre un valore strutturato da testo libero.

**Output:**
```python
ExtractionResult(
    field="industry",
    value="ecommerce",
    confidence=0.92,          # 0.0 - 1.0
    needs_clarification=False,
    reasoning="L'utente ha menzionato 'vendita online'"
)
```

**Latenza:** ~2-3s (include chiamata LLM)

### ClarifierService (`clarifier_service.py`)

Invocato quando `confidence < threshold` o `needs_clarification=True`. Genera 3-6 opzioni contestuali per aiutare l'utente a specificare la risposta.

**Latenza:** ~1-2s

### QualityCriticService (`quality_critic_service.py`)

Valuta la qualità di una risposta estratta.

**Output:**
```python
QualityCritique(
    score=0.75,               # 0.0 - 1.0
    follow_up_fields=["differentiator", "pricing_model"],
    quality_hints={"completeness": "medium"},
    recommendation="Chiedere il differenziatore competitivo"
)
```

**Latenza:** ~1-2s

### BlueprintReviewService (`blueprint_review_service.py`)

Costruisce il riepilogo pre-generazione mostrando all'utente cosa è confermato, in bozza, o mancante.

**Output:**
```python
ReviewSummary(
    confirmed=["Settore: E-commerce", "Obiettivo: Lead generation"],
    draft=["Budget: ~€5k/mese"],
    missing=["Canali specifici non selezionati"]
)
```

### StrategicProfileService (`strategic_profile_service.py`)

Genera il profilo strategico consulenziale dopo la conferma. Vedi [Strategic Profile V2](#10-strategic-profile-v2) per lo schema completo.

**Regola fondamentale:** usa SOLO campi con `status="confirmed"` come fatti. Tutto il resto va in assunzioni o open questions.

### GenerationService (`generation_service.py`)

Genera la presentazione (slide) e il report finale una volta che il wizard è in stato `completed`.

**Output:**
```json
{
  "presentation": {
    "slides": [
      {"title": "Executive Summary", "bullets": ["..."]},
      {"title": "Strategia Canali", "bullets": ["..."]}
    ]
  },
  "report": {
    "sections": [{"title": "...", "content": "..."}],
    "assumptions": ["..."],
    "next_steps": ["..."]
  }
}
```

### InputNormalizerService (`input_normalizer_service.py`)

Pulisce e normalizza l'input prima della memorizzazione nel blueprint.

- Trim + collasso spazi multipli
- Mapping sinonimi ambigui (`"boh"` → `"unknown"`)
- Mapping option ID per campi select
- Gestione array multi-select
- Conversione tipi + validazione

### ConsistencyCheckerService (`consistency_checker_service.py`)

Rileva conflitti logici tra campi del blueprint (es. budget troppo basso per i canali selezionati).

### Mappa di integrazione completa

```
User Input (UI Event o Free Text)
    │
    ▼
OrchestratorServiceV2.handle_turn()
    │
    ├── UI Event path:
    │   InputNormalizerService.normalize()
    │   └── apply_answer() → blueprint update diretto
    │
    └── Free Text path:
        FieldExtractorService.extract_field()
        │   └── Output: (value, confidence, needs_clarification)
        │
        ├── SE needs_clarification:
        │   ClarifierService.generate_clarifier()
        │   └── RETURN clarification UI (interrompe il flow)
        │
        └── ALTRIMENTI:
            QualityCriticService.critique_answer()
            ConsistencyCheckerService.check()
            apply_quality_hint() → store flags nel blueprint
            apply_answer() → update blueprint
            pick_next_question() → prossima domanda

Quando current_section == "Review":
    BlueprintReviewService.build_review()
    └── RETURN review UI per conferma utente

Dopo conferma review:
    StrategicProfileService.generate_internal_profile()
    └── RETURN profilo strategico completo
```

---

## 10. Strategic Profile V2

Il profilo strategico V2 ha struttura consulenziale con guardrail post-LLM.

### Schema output completo

```json
{
  "summary": "Max 10 righe di sintesi",
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
  "assumptions": ["Solo assunzioni, mai fatti inventati"],
  "open_questions": [
    {
      "question": "Qual è il CAC e LTV attuali?",
      "why_it_matters": "Critico per calcolo ROI",
      "priority": 1
    }
  ],
  "risks_watchouts": [
    {
      "risk": "Alta concorrenza nel segmento target",
      "impact": "high",
      "mitigation": "Focus su differenziazione AI"
    }
  ],
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Audit top 5 competitor",
      "why": "Critico per strategia di posizionamento",
      "owner_hint": "Marketing"
    }
  ],
  "action_plan_90min": [
    {
      "step": 1,
      "task": "Audit top 5 competitor",
      "output": "Spreadsheet analisi competitiva"
    }
  ],
  "confidence_map": {
    "high": ["industry", "primary_goal"],
    "medium": ["budget_range"],
    "low": ["timeline"]
  }
}
```

### Guardrail automatici (post-LLM)

| Campo | Regola |
|---|---|
| `open_questions` | Max 8. Se > 8 → troncato. Priorità rinumerate 1..8 |
| `action_plan_90min` | Min 3, max 5 step. Se < 3 → padding con fallback. Output mancanti → "Deliverable for step X" |
| Fatti | Solo campi `status="confirmed"`. Draft/missing → solo in assumptions/questions/risks |
| Metriche | Mai inventate. Se mancanti → esplicito in assumptions |

### Owner hint

Ogni `recommended_action` ha un campo `owner_hint` con valore `Marketing`, `Sales`, o `Ops` per chiarire la responsabilità esecutiva.

---

## 11. LLM Providers

### Configurazione per provider

**OpenAI**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # oppure gpt-4o
```

**Google Gemini**
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-pro
```

**Anthropic Claude**
```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

### Provider Factory

```python
from app.llm.provider import get_llm_provider

llm = await get_llm_provider()   # istanzia il provider configurato in .env
```

Ogni provider implementa l'interfaccia astratta `LLMProvider`:
```python
async def complete(prompt: str, schema: dict | None = None) -> str: ...
async def complete_json(prompt: str, schema: dict) -> dict: ...
```

### Utilizzo LLM per servizio

| Servizio | Quando chiama LLM | Latenza tipica |
|---|---|---|
| FieldExtractor | Free text input | ~2-3s |
| Clarifier | Confidence bassa | ~1-2s |
| QualityCritic | Post-extraction | ~1-2s |
| BlueprintReview | Fase Review | ~2-3s |
| StrategicProfile | Post-confirm | ~3-5s |
| GenerationService | `/generate` | ~5-10s |
| UI Events | **Mai** | <200ms |

---

## 12. API Reference

### Autenticazione

Tutti gli endpoint richiedono questi header:

```
X-Tenant-Id: boom
X-Api-Key: API_KEY_123
```

Header opzionale per verifica HMAC:
```
X-Signature: <hmac-sha256>
```

---

### POST `/v1/sessions/start`

Crea una nuova sessione wizard.

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

**Response `200`:**
```json
{
  "session_id": "sess_abc123",
  "wizard": {
    "wizard_id": "strategic_snapshot_v1",
    "current_step": "context",
    "progress": 0.0,
    "blueprint": {},
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
    }
  }
}
```

---

### POST `/v1/wizard/turn`

Processa l'input dell'utente e avanza il wizard. È l'endpoint principale.

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

**Tipi di `ui_event.type`:**

| Tipo | Descrizione |
|---|---|
| `selected_option` | Selezione singola da chip/radio |
| `multi_selected` | Selezione multipla (value è array) |
| `text_submitted` | Input testuale libero |
| `slider_changed` | Valore da slider |
| `clicked` | Click su pulsante |

**Response `200`:**
```json
{
  "assistant_message": "Qual è il tuo modello di business principale?",
  "wizard": {
    "current_step": "context",
    "progress": 14.3,
    "blueprint": {
      "context": {
        "value": {"industry": "ecommerce"},
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

### GET `/v1/sessions/{session_id}`

Recupera lo stato corrente di una sessione.

**Response `200`:**
```json
{
  "session_id": "sess_abc123",
  "wizard": { ... }
}
```

---

### POST `/v1/wizard/confirm`

Conferma o richiede modifica nello step Review.

**Request:**
```json
{
  "session_id": "sess_abc123",
  "event_id": "evt_confirm",
  "action": "confirm",
  "step": "review"
}
```

`action` può essere `"confirm"` o `"edit"`.

**Response `200` (confirm):**
```json
{
  "status": "confirmed",
  "message": "Wizard completato! Procedi alla generazione."
}
```

**Response `200` (edit):**
```json
{
  "status": "editing",
  "message": "Torna indietro per modificare.",
  "wizard": { ... }
}
```

---

### POST `/v1/wizard/generate`

Genera la presentazione e il report finale. Richiede sessione in stato `completed`.

**Request:**
```json
{
  "session_id": "sess_abc123",
  "event_id": "evt_generate",
  "format": "json"
}
```

**Response `200`:**
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
      }
    ]
  },
  "report": {
    "sections": [
      {
        "title": "Executive Summary",
        "content": "Questo piano strategico si concentra sulla generazione di lead B2B..."
      }
    ],
    "assumptions": ["Budget mensile di €5.000-€10.000"],
    "next_steps": ["Setup account Google Ads", "Creazione landing page"]
  }
}
```

---

### DELETE `/v1/sessions/{session_id}`

Elimina una sessione.

**Response `200`:**
```json
{
  "status": "deleted",
  "session_id": "sess_abc123"
}
```

---

### GET `/health`

Health check.

**Response `200`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "env": "dev"
}
```

---

### Componenti UI

Il campo `wizard.ui` nella response indica al frontend cosa renderizzare:

**`single_select`**
```json
{
  "type": "single_select",
  "label": "Testo domanda",
  "field": "nome_campo",
  "options": [{"id": "val1", "label": "Label 1"}]
}
```

**`multi_select`**
```json
{
  "type": "multi_select",
  "label": "Seleziona più opzioni",
  "field": "channels",
  "options": [...],
  "constraints": {"min": 1, "max": 4}
}
```

**`short_text`** / **`long_text`**
```json
{
  "type": "short_text",
  "label": "Descrivi il tuo prodotto",
  "field": "product_description",
  "constraints": {"placeholder": "Es: SaaS per la gestione..."}
}
```

**`confirmation`**
```json
{
  "type": "confirmation",
  "label": "Conferma o modifica",
  "field": "user_confirmation",
  "options": [
    {"id": "confirm", "label": "Conferma"},
    {"id": "edit", "label": "Modifica"}
  ]
}
```

---

### Errori

| Status | Descrizione |
|---|---|
| `400` | Validation error — campo mancante o valore non valido |
| `401` | Credenziali non valide (tenant ID o API key) |
| `404` | Sessione non trovata (scaduta o inesistente) |
| `429` | Rate limit superato |
| `500` | Errore interno |

```json
{
  "error": "Not found",
  "detail": "Session not found or expired"
}
```

---

## 13. Integrazione frontend

### Flusso completo JavaScript

```javascript
class WizardClient {
  constructor(baseUrl, tenantId, apiKey) {
    this.baseUrl = baseUrl;
    this.tenantId = tenantId;
    this.apiKey = apiKey;
    this.sessionId = null;
  }

  get headers() {
    return {
      'Content-Type': 'application/json',
      'X-Tenant-Id': this.tenantId,
      'X-Api-Key': this.apiKey
    };
  }

  async start(pageUrl) {
    const res = await fetch(`${this.baseUrl}/v1/sessions/start`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        context: { page_url: pageUrl },
        consent: { gdpr: true }
      })
    });
    const { session_id, wizard } = await res.json();
    this.sessionId = session_id;
    return wizard;
  }

  async turn(field, value, type = 'selected_option') {
    const res = await fetch(`${this.baseUrl}/v1/wizard/turn`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        session_id: this.sessionId,
        event_id: crypto.randomUUID(),   // idempotency key
        ui_event: { type, field, value }
      })
    });
    return await res.json();
  }

  async confirm(action = 'confirm') {
    const res = await fetch(`${this.baseUrl}/v1/wizard/confirm`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        session_id: this.sessionId,
        event_id: crypto.randomUUID(),
        action,
        step: 'review'
      })
    });
    return await res.json();
  }

  async generate() {
    const res = await fetch(`${this.baseUrl}/v1/wizard/generate`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        session_id: this.sessionId,
        event_id: crypto.randomUUID(),
        format: 'json'
      })
    });
    return await res.json();
  }
}

// Utilizzo
const client = new WizardClient('http://localhost:8000', 'boom', 'API_KEY_123');
const wizard = await client.start(window.location.href);
renderUI(wizard.ui);
```

### Render UI components

```javascript
function renderUI(ui) {
  switch (ui.type) {
    case 'single_select':  return renderChips(ui);
    case 'multi_select':   return renderCheckboxes(ui);
    case 'short_text':     return renderInput(ui);
    case 'long_text':      return renderTextarea(ui);
    case 'confirmation':   return renderConfirmation(ui);
  }
}

function renderChips(ui) {
  return `
    <div class="wizard-field">
      <label>${ui.label}</label>
      <div class="chips">
        ${ui.options.map(opt => `
          <button class="chip" data-value="${opt.id}" data-field="${ui.field}">
            ${opt.label}
          </button>
        `).join('')}
      </div>
    </div>
  `;
}
```

### Gestione eventi

```javascript
document.addEventListener('click', async (e) => {
  const chip = e.target.closest('.chip');
  if (!chip) return;
  
  const { field, value } = chip.dataset;
  const { assistant_message, wizard } = await client.turn(field, value);
  
  updateProgress(wizard.progress);
  updateBlueprint(wizard.blueprint);
  renderUI(wizard.ui);
  showMessage(assistant_message);
});
```

### Aggiornamento progress e blueprint

```javascript
function updateProgress(progress) {
  document.querySelector('.progress-bar').style.width = progress + '%';
}

function updateBlueprint(blueprint) {
  const panel = document.querySelector('.blueprint-panel');
  panel.innerHTML = Object.entries(blueprint)
    .filter(([, section]) => section.value)
    .map(([key, section]) => `
      <div class="section ${section.status}">
        <h4>${formatStep(key)} ${section.status === 'confirmed' ? '✓' : ''}</h4>
        <pre>${JSON.stringify(section.value, null, 2)}</pre>
      </div>
    `).join('');
}
```

### Error handling

```javascript
async function safeApiCall(fn) {
  try {
    return await fn();
  } catch (err) {
    if (err.status === 401) showError('Credenziali non valide');
    else if (err.status === 404) showError('Sessione scaduta. Riavvia.');
    else if (err.status === 429) showError('Troppo veloce. Riprova.');
    else showError('Errore di rete. Riprova.');
    throw err;
  }
}
```

### CSS essenziale

```css
.chip {
  padding: 12px 24px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}
.chip:hover { border-color: #2196F3; }
.chip.selected { background: #2196F3; color: white; border-color: #2196F3; }

.progress-bar {
  height: 4px;
  background: #2196F3;
  transition: width 0.3s ease;
}

.blueprint-panel {
  position: fixed;
  right: 0; top: 0;
  width: 300px; height: 100vh;
  background: #f9f9f9;
  padding: 20px;
  overflow-y: auto;
}

.section.confirmed { border-left: 4px solid #4CAF50; }
.section.draft { border-left: 4px solid #FF9800; }
```

### Best practices

1. **Idempotency** — usare sempre `crypto.randomUUID()` per ogni turn, mai riutilizzare lo stesso `event_id`
2. **Loading state** — mostrare spinner durante le chiamate LLM (~2-3s)
3. **Session storage** — salvare `session_id` in `sessionStorage` per sopravvivere a reload
4. **Blueprint panel** — aggiornarlo dopo ogni turn per feedback in tempo reale
5. **Validation errors** — mostrare `wizard.validation.errors` se presenti

---

## 14. Sicurezza

### Autenticazione multi-tenant

Ogni richiesta richiede `X-Tenant-Id` + `X-Api-Key`. La mappa tenant→key è in `TENANT_KEYS_JSON`.

In produzione: spostare su database invece di env var.

### HMAC Signature (opzionale)

Per prevenire tampering delle request, attivare con `HMAC_SECRET`:

```
X-Signature: sha256=<hmac-sha256-del-body>
```

### Flow sicurezza

```
Request
  │
  ▼
Estrai X-Tenant-Id + X-Api-Key
  │
  ▼
Tenant esiste? Key corrisponde? ──No──► 401
  │ Sì
  ▼
HMAC valido? (se configurato) ──No──► 403
  │ Sì
  ▼
Rate limit OK? ──No──► 429
  │ Sì
  ▼
Processa request
```

### Altre misure

| Misura | Implementazione |
|---|---|
| PII masking | Email/phone/API key mascherati nei log (structlog) |
| Rate limiting | Slowapi, configurabile per tenant |
| CORS | `allow_origins` configurabile via env |
| Session isolation | Sessioni isolate per tenant in Redis |
| Idempotency | Dedup automatico via `event_id` |

### Checklist produzione sicurezza

- [ ] Cambiare `TENANT_KEYS_JSON` con keys forti (o migrare su DB)
- [ ] Impostare `HMAC_SECRET` forte e attivare verifica firma
- [ ] Configurare `CORS_ORIGINS` con i domini specifici del frontend
- [ ] Abilitare HTTPS/TLS a livello load balancer
- [ ] Configurare `APP_ENV=prod`
- [ ] Rivedere rate limits per i propri volumi

---

## 15. Testing

### Struttura test

```
tests/
├── conftest.py                       # Fixtures pytest (Redis mock, session)
├── test_e2e_llm.py                   # Test end-to-end con LLM reali
├── test_generation.py                # Generazione slide + report
├── test_orchestrator.py              # Orchestrator V1
├── test_orchestrator_v2.py           # Orchestrator V2 (8 test case)
├── test_field_extractor.py           # Estrazione campi (unit)
├── test_field_extractor_integration.py
├── test_input_normalizer.py
├── test_input_normalizer_integration.py
├── test_clarifier.py
├── test_quality_critic.py
├── test_quality_critic_updated.py
├── test_blueprint_review.py
├── test_review.py
└── test_research.py
```

### Eseguire i test

```bash
# Tutti i test
pytest -v

# Con coverage
pytest --cov=app --cov-report=html tests/

# Solo un servizio
pytest tests/test_orchestrator_v2.py -v -s

# Salta test che richiedono API LLM reali
pytest -k "not e2e_llm" -v

# Makefile shortcut
make test
```

### Latency targets (da rispettare nei test)

| Operazione | Target |
|---|---|
| UI Event (no LLM) | < 200ms |
| Free text (estrazione) | < 3s |
| Clarification | < 2s |
| Review phase | < 3s |
| Generation | < 10s |

### Environment di test

File `.env.testing` con chiavi fittizie. Il Redis store ha un fallback in-memory automatico, quindi i test unitari non richiedono Redis attivo.

---

## 16. Deploy e produzione

### Docker Compose (dev/staging)

```bash
docker-compose up -d

# Logs
docker-compose logs -f wizard_engine

# Stop
docker-compose down
```

### Architettura produzione consigliata

```
┌──────────────┐    ┌──────────────┐    ┌───────────┐
│   Frontend   │    │   API Load   │    │   Redis   │
│   (Vercel)   │───▶│   Balancer   │───▶│ (Managed) │
└──────────────┘    └──────────────┘    └───────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Wizard API  │
                    │  (ECS/K8s)   │
                    │  Auto-scale  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │    (RDS)     │
                    └──────────────┘
Secrets: AWS Secrets Manager
Logs: CloudWatch / ELK
Monitoring: Datadog / CloudWatch
```

### Checklist deploy

- [ ] `APP_ENV=prod`
- [ ] API keys LLM configurate come secrets (non in .env in chiaro)
- [ ] Redis managed con persistence abilitata
- [ ] HTTPS attivo
- [ ] CORS configurato con domini specifici
- [ ] HMAC secret configurato
- [ ] Rate limits rivisti per i volumi attesi
- [ ] Health check `/health` configurato nel load balancer
- [ ] Log aggregation configurata
- [ ] Alerting su error rate e latenza P95

### Variabili d'ambiente produzione

```env
APP_ENV=prod
REDIS_URL=rediss://user:pass@managed-redis:6380/0
OPENAI_API_KEY=sk-prod-...
TENANT_KEYS_JSON={"boom":"<strong-random-key>"}
HMAC_SECRET=<strong-random-secret>
CORS_ORIGINS=https://mio-frontend.vercel.app
SESSION_TTL_SECONDS=3600
```

---

## 17. Troubleshooting

### Redis connection failed
```bash
redis-cli ping          # deve rispondere PONG
# Verificare REDIS_URL nel .env
```

### Session not found
- Le sessioni scadono dopo `SESSION_TTL_SECONDS` (default 1h)
- Verificare che Redis sia attivo e che la sessione sia stata salvata

### LLM provider errors
- Verificare che l'API key sia valida e non scaduta
- Controllare le quote/rate limits del provider
- Leggere i log strutturati per il messaggio di errore specifico

### Logs
```bash
# Docker
docker-compose logs -f wizard_engine

# Locale (log su stdout in formato JSON)
python -m app.main 2>&1 | jq .
```

### API docs interattiva
```
http://localhost:8000/docs    # Swagger UI
http://localhost:8000/redoc   # ReDoc
```

---

## 18. Roadmap

### Phase 1 — Core Stabilization
- [x] Tutti i servizi core implementati
- [x] Orchestrator V2 con input normalization
- [x] Test coverage completo
- [x] Question bank da JSON esterno
- [ ] Redis session store in produzione
- [ ] Integration testing con servizi reali

### Phase 2 — Advanced Features
- [ ] Adattamento dinamico delle domande in base a risposte precedenti
- [ ] Supporto multi-lingua
- [ ] A/B testing framework per question bank
- [ ] Advanced analytics sul funnel di completamento

### Phase 3 — Performance & Scale
- [ ] Response caching layer
- [ ] Batch processing optimization
- [ ] Auto-scaling configuration
- [ ] CDN integration

### Phase 4 — Intelligence Enhancement
- [ ] Machine learning per priorità domande (info_gain dinamico)
- [ ] User behavior analysis
- [ ] Predictive clarification
- [ ] Research service (pre-fill blueprint da dati pubblici)
- [ ] Adaptive questioning basato su confidence

---

*BOOM Wizard Engine — Proprietà di BOOM Digital — support@boom-digital.it*
