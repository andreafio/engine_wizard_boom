# Quality Critic Service

## Overview

The Quality Critic Service evaluates the quality of wizard answers, providing objective scoring and recommendations for follow-up questions. It ensures answers meet minimum quality standards and identifies when additional information is needed.

## Key Features

- **Quality Scoring**: 0.0-1.0 scale with detailed guidelines for each range
- **Follow-up Recommendations**: Suggests specific fields for deep follow-up when answers are deficient
- **Field-Specific Expectations**: Tailored quality criteria for different field types
- **UI-Aware Evaluation**: Considers UI component type (text, select) in scoring
- **Section Consistency**: Follow-up recommendations stay within the same wizard section

## Architecture

```
User Answer → QualityCriticService → LLM → QualityCritique
                              ↓
                       Field-Specific Expectations
                              ↓
                       Scoring & Recommendations
```

## Usage

### Direct Usage

```python
from app.services.quality_critic_service import critique_wizard_answer

critique = await critique_wizard_answer(
    field="context.industry",
    value="Tech",
    ui_type="short_text",
    section="Context"
)

print(f"Score: {critique.quality_score}")  # 0.2
print(f"Follow-up needed: {critique.recommend_deep_followup}")  # True
print(f"Reason: {critique.reason}")  # "too vague, lacks specificity"
```

### Integration with Field Extractor

The Quality Critic is automatically called by the FieldExtractorService for successfully extracted answers:

```python
result = await field_extractor.extract_field(
    current_section="Context",
    current_field="context.industry",
    # ... other params
)

if result.quality_critique:
    score = result.quality_critique.quality_score
    if result.quality_critique.recommend_deep_followup:
        followup_field = result.quality_critique.followup_field
        # Handle follow-up recommendation
```

## Scoring Guidelines

### Score Ranges

- **0.0-0.2**: Vague, incomplete, or missing critical information
- **0.3-0.5**: Basic answer but lacks specificity or detail
- **0.6-0.8**: Good answer with reasonable detail and clarity
- **0.9-1.0**: Excellent answer with high specificity and completeness

### Follow-up Rules

- **Only recommend follow-up if score < 0.5** (seriously deficient answers)
- **Follow-up field must be from the SAME section**
- **Use dot.notation format** (e.g., "context.company_size")
- **Do NOT propose questions, only field names**

## Field-Specific Expectations

### Industry Field
```
- Should specify actual industry/sector (not "business" or "company")
- Be specific enough to inform marketing strategy
- Avoid vague terms like "tech" when more precision is possible
```

### Business Model Field
```
- Specify B2B, B2C, marketplace, subscription, etc.
- Explain how revenue is generated
- Be specific about the business approach
```

### Target Audience Field
```
- Define specific customer segments
- Include demographics, roles, or characteristics
- Be more specific than "everyone" or "businesses"
```

### Goal Field
```
- State specific, measurable objectives
- Include timeline or scope
- Be actionable and realistic
```

## Output Format

```json
{
  "quality_score": 0.3,
  "recommend_deep_followup": true,
  "followup_field": "context.company_size",
  "reason": "too vague, lacks specificity"
}
```

## Error Handling

- **LLM Failures**: Returns neutral score (0.5) with no follow-up recommendation
- **Invalid Fields**: Gracefully handles unknown field types with generic expectations
- **Context Issues**: Works with any section and UI type combination

## Performance

- **Latency**: ~1-2 seconds per critique
- **Caching**: No caching implemented (each answer is critiqued individually)
- **Batch Processing**: Not supported (answer-by-answer evaluation)

## Testing

Run the quality critic tests:

```bash
# Unit tests
pytest tests/test_quality_critic.py -v

# Integration with field extractor
pytest tests/test_field_extractor.py -v

# Full test suite
pytest tests/ -k "quality_critic or field_extractor" --tb=short
```

## Future Enhancements

- **Historical Context**: Consider previous answers in the same session
- **Adaptive Scoring**: Learn from user corrections and feedback
- **Multi-field Analysis**: Evaluate relationships between related fields
- **Confidence Calibration**: Fine-tune scoring thresholds based on field importance