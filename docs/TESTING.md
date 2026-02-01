# Test Suite - Wizard BOOM Engine

## ✅ Test Summary

**Total Tests**: 30 (25 unit + 5 E2E integration)
**Status**: ✅ **All 25 unit tests passing**

### Test Coverage

| Module | Tests | Status | Coverage |
|--------|-------|--------|----------|
| **Generator** | 7 | ✅ PASS | Schema validation, guardrails, assumptions, fallback |
| **Orchestrator** | 10 | ✅ PASS | Field extraction, confidence, status, suggestions |
| **Reviewer** | 8 | ✅ PASS | Blueprint review, confirmed/draft separation |
| **E2E LLM** | 5 | ⏭️ SKIP | Requires API key (real LLM calls) |

---

## 🧪 Test Files

### 1. [`test_generation.py`](tests/test_generation.py) - Generator Service (7 tests)

**Cosa testa:**
- ✅ Schema Pydantic validation (`GenerationOutput`)
- ✅ Bullet hygiene (max 140 chars, no duplicates)
- ✅ Assumptions enforcement quando mancano metriche
- ✅ Guardrails: invented numbers detection
- ✅ Fallback quando LLM fallisce

**Run:**
```bash
pytest tests/test_generation.py -v
```

**Output atteso:**
```
test_generation_output_schema_validates ✓
test_generation_output_rejects_invalid_slides ✓
test_generation_output_enforces_bullet_length ✓
test_generation_output_removes_duplicate_bullets ✓
test_assumptions_added_when_no_metrics ✓
test_fallback_on_bad_llm_response ✓
test_invented_numbers_moved_to_assumptions ✓

7 passed in 0.10s
```

---

### 2. [`test_orchestrator.py`](tests/test_orchestrator.py) - Orchestrator Service (10 tests)

**Cosa testa:**
- ✅ Schema validation (`OrchestratorOutput`)
- ✅ Field extraction (confirmed vs draft)
- ✅ Confidence levels (high/medium/low)
- ✅ Suggested options quando input vago
- ✅ NO invenzione metriche/KPI
- ✅ Fallback su LLM failure

**Run:**
```bash
pytest tests/test_orchestrator.py -v
```

**Output atteso:**
```
test_orchestrator_output_schema_validates ✓
test_orchestrator_output_schema_validates_suggestions ✓
test_orchestrator_output_rejects_invalid_confidence ✓
test_orchestrator_output_rejects_invalid_status ✓
test_orchestrator_output_helper_methods ✓
test_orchestrator_extracts_explicit_value ✓
test_orchestrator_marks_vague_input_as_draft ✓
test_orchestrator_suggests_options_when_unclear ✓
test_orchestrator_does_not_invent_metrics ✓
test_orchestrator_fallback_on_llm_failure ✓

10 passed in 0.15s
```

---

### 3. [`test_review.py`](tests/test_review.py) - Review Service (8 tests)

**Cosa testa:**
- ✅ Schema validation (`ReviewOutput`)
- ✅ Separazione confirmed vs to_confirm
- ✅ Helper: `is_ready_for_generation()`
- ✅ Ignora sezioni vuote
- ✅ Formato conciso (1 line/item)
- ✅ Fallback su LLM failure

**Run:**
```bash
pytest tests/test_review.py -v
```

**Output atteso:**
```
test_review_output_schema_validates ✓
test_review_output_ready_for_generation ✓
test_review_output_helper_methods ✓
test_review_separates_confirmed_and_draft ✓
test_review_all_confirmed_ready_for_generation ✓
test_review_fallback_on_llm_failure ✓
test_review_ignores_empty_sections ✓
test_review_output_concise_format ✓

8 passed in 0.15s
```

---

### 4. [`test_e2e_llm.py`](tests/test_e2e_llm.py) - End-to-End Integration (5 tests)

**⚠️ IMPORTANTE: Questi test fanno chiamate reali a OpenAI API**

**Cosa testa:**
- 🔴 Orchestrator con input reale (explicit + vague)
- 🔴 Review service con blueprint completo
- 🔴 Generator con output finale completo
- 🔴 Full workflow: orchestrator → review → generation

**Setup:**
```bash
# Windows
set OPENAI_API_KEY=sk-...

# Linux/Mac
export OPENAI_API_KEY=sk-...
```

**Run:**
```bash
# Con verbose output per vedere i risultati reali
pytest tests/test_e2e_llm.py -v -s

# Singolo test
pytest tests/test_e2e_llm.py::test_orchestrator_real_extraction -v -s
```

**Esempio output atteso:**
```
================================================================================
TEST: Orchestrator - Explicit Value Extraction
================================================================================

📥 USER INPUT: Siamo una startup B2B SaaS nel settore HR tech
🎯 EXPECTED FIELD: industry

📤 LLM OUTPUT:
  Extracted Fields: {'industry': 'B2B SaaS - HR tech'}
  Field Status: {'industry': 'confirmed'}
  Confidence: high

✅ Test passed!
```

---

## 🚀 Quick Start

### Run tutti i test unitari (veloci, no API calls)
```bash
pytest tests/test_generation.py tests/test_orchestrator.py tests/test_review.py -v
```

**Output:**
```
25 passed in 0.14s
```

---

### Run test E2E (con API key)

**1. Set API key:**
```bash
set OPENAI_API_KEY=sk-proj-your-key-here
```

**2. Run test orchestrator (estratti reali):**
```bash
pytest tests/test_e2e_llm.py::test_orchestrator_real_extraction -v -s
```

**Output atteso:**
```
TEST: Orchestrator - Explicit Value Extraction
📥 USER INPUT: Siamo una startup B2B SaaS nel settore HR tech
📤 LLM OUTPUT:
  Extracted Fields: {'industry': 'B2B SaaS - HR tech'}
  Field Status: {'industry': 'confirmed'}
  Confidence: high
✅ Test passed!
```

**3. Run test generator (output completo):**
```bash
pytest tests/test_e2e_llm.py::test_generator_real_output -v -s
```

**Output atteso:**
```
TEST: Generator - Complete Presentation & Report

📋 BLUEPRINT INPUT:
  Industry: B2B SaaS
  Goal: Lead Generation (100/month)
  Target: Marketing Managers in Italia

📤 GENERATED OUTPUT:

📊 PRESENTATION (6 slides):

  Slide 1: Strategia Marketing B2B SaaS
    • Focus su Lead Generation per Marketing Manager
    • Target: 100 lead qualificati al mese
    • Canali prioritari: LinkedIn, Google Ads, Content Marketing

  Slide 2: Contesto e Mercato
    • Settore B2B SaaS in crescita in Italia
    • Target: aziende tech con focus su automazione
    • Budget disponibile: 5k-10k mensili

  [... 4 slide aggiuntive ...]

📄 REPORT (6 sections):

  [Executive Summary]
  Strategia marketing per acquisizione lead qualificati nel settore B2B SaaS...

  [Contesto Strategico]
  Analisi del mercato italiano B2B SaaS con focus su Marketing Managers...

  [... 4 sezioni aggiuntive ...]

🎯 NEXT STEPS (4):
  • Setup campagne LinkedIn Ads con targeting preciso
  • Creazione landing page ottimizzate per conversione
  • Attivazione strategia content marketing su blog aziendale
  • Setup tracking e analytics per monitoraggio KPI

✅ Test passed!
```

**4. Run full workflow (tutti i 3 agenti):**
```bash
pytest tests/test_e2e_llm.py::test_full_workflow_e2e -v -s
```

**Output atteso:**
```
TEST: Full End-to-End Workflow

📍 STEP 1: Orchestrator - Extract Context
  Extracted: {'industry': 'E-commerce moda sostenibile'}

📍 STEP 2: Review - Verify Blueprint
  Confirmed items: 6
  To confirm: 0

📍 STEP 3: Generator - Create Output
  Slides created: 7
  Report sections: 6
  Assumptions: 0

✅ Complete workflow test passed!
```

---

## 📊 Test Scenarios

### Scenario 1: Blueprint-Only Generation (NO invenzione dati)
```python
# Input: blueprint senza metriche
blueprint = {
    "objective": {"primary_goal": "Brand Awareness"}
    # NO CPL, CAC, ROI
}

# Output atteso:
{
    "slides": [...],
    "assumptions": [
        "Mancano dati quantitativi (CPL, CAC): priorità qualitative"
    ]
}
```
✅ Test: `test_assumptions_added_when_no_metrics`

---

### Scenario 2: Guardrails - Invented Numbers
```python
# LLM output: contiene numeri non nel blueprint
{
    "slides": [
        {"bullets": ["CPL target: 25€"]}  # ❌ INVENTATO
    ]
}

# Dopo guardrails:
{
    "slides": [
        {"bullets": ["[rimosso]"]}
    ],
    "assumptions": [
        "Dati numerici rimossi: non presenti nel blueprint"
    ]
}
```
✅ Test: `test_invented_numbers_moved_to_assumptions`

---

### Scenario 3: Orchestrator - Vague Input
```python
# Input: "Vogliamo crescere"
# Expected field: "primary_goal"

# Output:
{
    "extracted_fields": {},
    "field_status": {},
    "confidence": "low",
    "suggested_options": [
        {
            "field": "primary_goal",
            "options": [
                {"id": "lead_gen", "label": "Lead Generation"},
                {"id": "brand_awareness", "label": "Brand Awareness"}
            ]
        }
    ]
}
```
✅ Test: `test_orchestrator_suggests_options_when_unclear`

---

### Scenario 4: Review - Mixed Status
```python
# Blueprint con confirmed + draft
blueprint = {
    "context": {"value": {...}, "status": "confirmed"},
    "objective": {"value": {...}, "status": "draft"}
}

# Output:
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
✅ Test: `test_review_separates_confirmed_and_draft`

---

## 🎯 Key Validations

### Generator Guardrails
1. ✅ Slides: 6-8 (validated by Pydantic)
2. ✅ Bullets: 3-5 per slide (validated)
3. ✅ Bullet length: max 140 chars (auto-truncated)
4. ✅ No duplicate bullets (auto-removed)
5. ✅ Assumptions quando no metrics (enforced)
6. ✅ Invented numbers moved to assumptions

### Orchestrator Rules
1. ✅ Only extract current step fields
2. ✅ Never invent metrics/KPIs
3. ✅ Mark "draft" if uncertain
4. ✅ Mark "confirmed" only if explicit
5. ✅ Provide suggestions when unclear
6. ✅ Fallback su LLM failure

### Reviewer Rules
1. ✅ Separate confirmed vs draft
2. ✅ Ignore empty sections
3. ✅ Concise format (1 line/item)
4. ✅ Helper: `is_ready_for_generation()`
5. ✅ Fallback su LLM failure

---

## 🐛 Debugging

### Test fallisce con "ModuleNotFoundError"
```bash
# Install dependencies
pip install -r requirements.txt
```

### E2E test skipped
```bash
# Check API key
echo %OPENAI_API_KEY%

# Set if missing
set OPENAI_API_KEY=sk-...
```

### Vedere output dettagliato
```bash
# Use -s flag
pytest tests/test_e2e_llm.py -v -s

# Vedere solo log
pytest tests/test_generation.py -v --log-cli-level=INFO
```

---

## 📈 Coverage Report

```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest tests/test_generation.py tests/test_orchestrator.py tests/test_review.py --cov=app --cov-report=html

# Open report
start htmlcov/index.html
```

---

## 🚦 CI/CD Integration

**GitHub Actions example:**
```yaml
- name: Run unit tests
  run: pytest tests/test_generation.py tests/test_orchestrator.py tests/test_review.py -v

- name: Run E2E tests (with API key)
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: pytest tests/test_e2e_llm.py -v
  if: github.ref == 'refs/heads/main'
```

---

## 📝 Notes

- **Unit tests**: No external dependencies, veloci (~0.15s)
- **E2E tests**: Richiedono API key, lenti (~5-10s per test)
- **Cost**: E2E tests fanno chiamate reali (usa `gpt-4o-mini` per costi bassi)
- **Skip**: E2E tests sono automaticamente skippati se no API key

---

## ✅ Summary

| Category | Count | Status |
|----------|-------|--------|
| **Total Tests** | 30 | ✅ 25 PASS + ⏭️ 5 SKIP |
| **Generator** | 7 | ✅ PASS |
| **Orchestrator** | 10 | ✅ PASS |
| **Reviewer** | 8 | ✅ PASS |
| **E2E Integration** | 5 | ⏭️ SKIP (require API key) |

**Run all unit tests:**
```bash
pytest tests/test_generation.py tests/test_orchestrator.py tests/test_review.py -v
# ✅ 25 passed in 0.14s
```

**Run E2E with API key:**
```bash
set OPENAI_API_KEY=sk-...
pytest tests/test_e2e_llm.py::test_full_workflow_e2e -v -s
```
