# Clarifier Service

## Overview

The Clarifier Service generates contextual clarification options when field extraction is ambiguous. It provides 3-6 plausible, generic options that help users specify their intent without inventing facts or making assumptions.

## Key Features

- **Context-Aware**: Uses existing blueprint context (industry, business model, etc.) to generate relevant options
- **Generic Options**: Provides business-appropriate choices without specific numbers or performance claims
- **Fallback System**: Robust fallbacks for common field types when LLM generation fails
- **Pydantic Validation**: Strongly typed options with proper validation (3-6 options required)

## Architecture

```
Ambiguous User Input → ClarifierService → LLM → ClarifierOptions
                              ↓
                       Context Extraction
                              ↓
                       Fallback Options
```

## Usage

### Direct Usage

```python
from app.services.clarifier_service import generate_field_clarifier

clarifier = await generate_field_clarifier(
    current_field="context.industry",
    context={"business_model": "b2b"},
    user_message="Siamo nel tech"
)

print(clarifier.label)  # "Qual è il tuo settore di attività principale?"
print(len(clarifier.options))  # 4-6 options
```

### Integration with Field Extractor

The Clarifier Service is automatically called by the FieldExtractorService when `needs_clarification=True`:

```python
# When field extraction is ambiguous, clarifier options are automatically generated
result = await field_extractor.extract_field(
    current_section="Context",
    current_field="context.industry",
    # ... other params
)

if result.needs_clarification:
    # result.suggested_clarifier contains the options
    print(result.suggested_clarifier.label)
    for option in result.suggested_clarifier.options:
        print(f"- {option['id']}: {option['label']}")
```

## Context Extraction

The service extracts context from completed blueprint sections:

- **industry**: From `context.industry` field
- **business_model**: From `context.business_model` field  
- **offer_type**: From `objective.offer_type` field
- **target_role**: From `target_market.target_role` field

## Output Format

```json
{
  "ui_type": "single_select",
  "label": "Qual è il tuo settore di attività principale?",
  "options": [
    {"id": "tech", "label": "Tecnologia"},
    {"id": "finance", "label": "Finanza"},
    {"id": "healthcare", "label": "Sanità"},
    {"id": "retail", "label": "Commercio"}
  ]
}
```

## Fallback System

When LLM generation fails, the service provides field-specific fallbacks:

### Industry Field
```json
{
  "ui_type": "single_select",
  "label": "Qual è il tuo settore di attività principale?",
  "options": [
    {"id": "tech", "label": "Tecnologia"},
    {"id": "finance", "label": "Finanza"},
    {"id": "healthcare", "label": "Sanità"},
    {"id": "retail", "label": "Commercio"},
    {"id": "manufacturing", "label": "Produzione"}
  ]
}
```

### Business Model Field
```json
{
  "ui_type": "single_select", 
  "label": "Qual è il tuo modello di business?",
  "options": [
    {"id": "b2b", "label": "B2B (Business to Business)"},
    {"id": "b2c", "label": "B2C (Business to Consumer)"},
    {"id": "b2b2c", "label": "B2B2C (piattaforme)"},
    {"id": "marketplace", "label": "Marketplace"},
    {"id": "subscription", "label": "Abbonamento/SaaS"}
  ]
}
```

### Generic Fallback
For unknown fields:
```json
{
  "ui_type": "single_select",
  "label": "Per favore, specifica meglio [field_name]",
  "options": [
    {"id": "option1", "label": "Prima opzione"},
    {"id": "option2", "label": "Seconda opzione"}, 
    {"id": "option3", "label": "Terza opzione"}
  ]
}
```

## Guidelines

### Option Generation Rules

1. **Generic & Plausible**: Options should be business-appropriate without specific claims
2. **Mutually Exclusive**: Each option represents a distinct choice
3. **Context-Relevant**: Use available context to tailor options
4. **Concise Labels**: Keep option text clear and actionable
5. **Consistent IDs**: Use simple, lowercase identifiers

### Label Guidelines

- **Clear Questions**: Ask specific questions that address the ambiguity
- **Contextual**: Reference the field and available context
- **Actionable**: Guide users toward providing the needed information

## Testing

Run the clarifier tests:

```bash
# Unit tests
pytest tests/test_clarifier.py -v

# Integration with field extractor
pytest tests/test_field_extractor.py -v

# Full test suite
pytest tests/ -k "clarifier or field_extractor" --tb=short
```

## Error Handling

- **LLM Failures**: Automatic fallback to field-specific or generic options
- **Context Missing**: Works with empty context, provides generic options
- **Validation Errors**: Comprehensive logging with graceful degradation
- **Rate Limiting**: No built-in rate limiting (depends on LLM provider)

## Performance

- **Latency**: ~1-2 seconds per clarification generation
- **Caching**: No caching implemented (options are contextual)
- **Batch Processing**: Not supported (field-by-field clarification)

## Future Enhancements

- **Dynamic Context**: Extract more context from conversation history
- **Field-Specific Logic**: Custom clarification logic per field type
- **Multi-turn Clarification**: Follow-up questions based on user selections
- **A/B Testing**: Test different option sets for better user experience