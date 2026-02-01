# Field Extractor Service

## Overview

The Field Extractor Service is a strict, LLM-powered field extraction system designed for the Wizard BOOM marketing engine. It provides precise, rule-based extraction of individual blueprint fields from user messages, with built-in validation and clarification mechanisms.

## Key Features

- **Strict Extraction**: Only extracts values for the specified field, never invents data
- **Confidence Scoring**: Provides confidence levels and evidence for extractions
- **Clarification Support**: Returns draft status with suggested clarifiers when input is ambiguous
- **UI-Aware**: Respects UI component types (single_select, multi_select, text fields)
- **Uncertainty Detection**: Automatically reduces confidence for uncertain user expressions

## Architecture

```
User Message → FieldExtractorService → LLM → FieldExtractionResult
                                      ↓
                            Validation & Formatting
                                      ↓
                            OrchestratorService (legacy compatibility)
```

## Usage

### Direct Usage

```python
from app.services.field_extractor_service import extract_wizard_field

result = await extract_wizard_field(
    current_section="Context",
    current_field="context.industry",
    ui_type="single_select",
    options=[{"id": "b2b", "label": "B2B"}, {"id": "b2c", "label": "B2C"}],
    user_message="Siamo una azienda B2B",
    blueprint_snippet={"field_state": {"value": None, "status": "missing"}}
)

print(result.value)  # "b2b"
print(result.status)  # "confirmed"
print(result.confidence)  # 0.9
```

### Integration with Orchestrator

The Field Extractor is automatically used by the OrchestratorService when field paths contain dots (e.g., "context.industry"):

```python
# Uses FieldExtractorService
result = await orchestrator.extract_field(
    user_message="Siamo nel settore tech B2B",
    session=session,
    expected_field="context.industry"
)

# Falls back to legacy extraction
result = await orchestrator.extract_field(
    user_message="Siamo nel settore tech",
    session=session,
    expected_field="industry"  # No dot
)
```

## Field Extraction Rules

### Core Principles

1. **No Invention**: Never invent facts, numbers, KPIs, budgets, or targets
2. **Field-Specific**: Only extract the requested field, ignore others
3. **UI Compliance**: Respect UI type constraints and option mappings
4. **Evidence-Based**: Provide short rationale for extraction decisions

### Status Logic

- **confirmed**: High confidence extraction (0.7+), clear user intent
- **draft**: Low confidence (0.0-0.4) or ambiguous input, may need clarification

### Confidence Adjustment

- **Uncertainty Detection**: Phrases like "non so", "boh", "forse" reduce confidence to 0.4
- **Evidence Quality**: Based on direct quotes vs. inference
- **Context Matching**: Higher confidence when value matches existing blueprint

## Output Format

```json
{
  "field": "context.industry",
  "value": "b2b",
  "status": "confirmed",
  "confidence": 0.9,
  "evidence": "user said 'azienda B2B'",
  "needs_clarification": false,
  "suggested_clarifier": null
}
```

### Clarification Response

When input is ambiguous:

```json
{
  "field": "context.industry",
  "value": null,
  "status": "draft",
  "confidence": 0.3,
  "evidence": "multiple possible interpretations",
  "needs_clarification": true,
  "suggested_clarifier": {
    "ui_type": "single_select",
    "label": "Qual è il tuo settore principale?",
    "options": [
      {"id": "tech", "label": "Tecnologia"},
      {"id": "finance", "label": "Finanza"}
    ]
  }
}
```

## Testing

Run the field extractor tests:

```bash
# Unit tests
pytest tests/test_field_extractor.py -v

# Integration tests
pytest tests/test_field_extractor_integration.py -v

# All orchestrator tests (backward compatibility)
pytest tests/test_orchestrator.py -v
```

## Error Handling

- **LLM Failures**: Graceful fallback with draft status and clarification request
- **Schema Mismatches**: Returns safe defaults when field definitions are missing
- **Invalid Paths**: Handles both "field" and "section.field" formats
- **Validation Errors**: Comprehensive logging with structured error information

## Performance

- **Latency**: ~2-3 seconds per extraction (LLM call dependent)
- **Caching**: No caching implemented (single-use extractions)
- **Batch Processing**: Not supported (field-by-field extraction)

## Future Enhancements

- **Multi-field Extraction**: Support for extracting multiple related fields
- **Context Learning**: Improve accuracy with conversation history
- **Custom Validators**: Field-specific validation rules
- **Confidence Calibration**: Fine-tune confidence thresholds per field type