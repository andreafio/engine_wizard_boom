# Input Normalizer Service

## Overview
The `InputNormalizerService` is responsible for cleaning and normalizing user input values before they are stored in the blueprint. This ensures data quality and consistency across the wizard engine.

## Features

### Text Cleaning
- Trims whitespace from input values
- Collapses multiple spaces, tabs, and newlines into single spaces
- Handles empty/null values gracefully

### Unknown Synonym Detection
Automatically maps common "unknown" synonyms to a standardized "unknown" value:
- "boh", "non so", "n/a", "na", "non lo so", "non ne ho idea"
- "non saprei", "nessuna idea", "non ho idea", "non so dire"
- "non specificato", "non definito", "non applicabile", "n.d."
- "tbd", "to be defined", "da definire", "?", "??", "???"
- "non ricordo", "non mi viene in mente", "non ho pensato"
- "non ho deciso", "non ho scelto", "non ho selezionato"

### Option ID Mapping
For fields with predefined options, attempts to map user input to option IDs:

1. **Exact Label Match**: Direct match with option labels (case-insensitive)
2. **Exact ID Match**: Direct match with option IDs (case-insensitive)
3. **Partial Match**: Input contains option label or vice versa
4. **Word Match**: Any word from input matches any word in option label
5. **No Mapping**: Falls back to cleaned text input

### Multi-Select Handling
For multi-select fields:
- Maps each item to option IDs when possible
- Filters out unknown synonyms
- Returns array of matched IDs
- Falls back to joined string if no options available

### Data Type Conversion
Handles various input types:
- Strings: cleaned and processed
- Arrays: joined or mapped depending on UI type
- Numbers/Booleans: converted to strings
- Null/Empty: handled gracefully

## Integration

The normalizer is automatically integrated into the `OrchestratorServiceV2` and processes all user input before blueprint storage. The normalized data includes:

```python
{
    "value": "normalized_value",           # The cleaned/normalized value
    "normalized_ids": ["id1", "id2"],     # Option IDs for multi-select
    "normalization_notes": "exact_match",  # Processing notes
    "ui_type": "single_select",           # Original UI type
    "source": "user",                     # Input source
    "evidence": "",                       # Additional context
    "timestamp": "2026-01-30T13:00:00Z"   # Processing timestamp
}
```

## Usage

```python
from app.services.input_normalizer_service import InputNormalizerService

normalizer = InputNormalizerService()

result = normalizer.normalize({
    "field": "context.industry",
    "ui_type": "single_select",
    "options": [
        {"id": "ecommerce", "label": "E-commerce"},
        {"id": "saas", "label": "SaaS"}
    ],
    "raw_value": "  E-commerce  ",
    "locale": "it-IT"
})

# Result:
{
    "field": "context.industry",
    "normalized_value": "ecommerce",  # Mapped to ID
    "normalized_ids": [],
    "is_unknown": False,
    "notes": "exact_label_match"
}
```

## Testing

Comprehensive test coverage includes:
- Unit tests for all normalization logic
- Integration tests with orchestrator
- Edge cases and error handling
- Multi-language support preparation

Run tests with:
```bash
pytest tests/test_input_normalizer.py
pytest tests/test_input_normalizer_integration.py
```