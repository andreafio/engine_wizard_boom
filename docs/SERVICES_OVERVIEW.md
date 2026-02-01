# Services Directory

## Overview

The `app/services/` directory contains the core business logic for the Wizard BOOM marketing engine. These services provide intelligent field extraction, clarification handling, and quality assessment capabilities.

## Architecture

```
app/services/
├── field_extractor_service.py    # Strict field extraction with validation
├── clarifier_service.py          # Contextual clarification options
├── quality_critic_service.py     # Answer quality scoring & follow-ups
├── strategic_profile_service.py  # Internal strategic profile generation
├── blueprint_review_service.py   # Pre-generation review summaries
├── input_normalizer_service.py   # Input cleaning and normalization
├── orchestrator_service.py       # Service coordination & legacy compatibility
├── orchestrator_service_v2.py    # Advanced orchestrator with normalization
└── generation_service.py        # Content generation (existing)
```

## Service Responsibilities

### FieldExtractorService
**Purpose**: Extract and validate field values from user input with high precision.

**Key Features**:
- Strict validation rules per field type
- Confidence scoring for extraction certainty
- Automatic clarification generation for ambiguous inputs
- Quality critique integration for answer assessment

**Integration**: Called by orchestrator for field extraction requests.

### ClarifierService
**Purpose**: Generate contextual clarification options when user input is ambiguous.

**Key Features**:
- Field-specific option generation
- Context-aware suggestions (3-6 options per field)
- Fallback system for common field types
- UI-ready option formatting

**Integration**: Automatically invoked by FieldExtractorService when confidence is low.

### QualityCriticService
**Purpose**: Evaluate answer quality and recommend follow-up fields for completeness.

**Key Features**:
- 0.0-1.0 quality scoring system
- Field-specific quality expectations
- Follow-up field recommendations
- Section-aware suggestions

**Integration**: Automatically applied to successful field extractions.

### StrategicProfileService
**Purpose**: Generate internal strategic profiles for marketing/sales teams from blueprint data.

**Key Features**:
- Blueprint-only analysis with no invented metrics
- Operational strategic insights and recommendations
- Confidence mapping of blueprint completeness
- Identification of assumptions and open questions
- Prioritized action recommendations

**Integration**: Used for comprehensive strategic analysis of complete blueprints.

### BlueprintReviewService
**Purpose**: Create concise review summaries for user confirmation before final output generation.

**Key Features**:
- Pre-generation blueprint validation
- Categorization of confirmed, draft, and missing items
- Short bullet-point format for clarity
- Section-aware gap analysis
- No final output generation

**Integration**: Used before generation to show users what needs confirmation.

### OrchestratorService
**Purpose**: Coordinate all services while maintaining backward compatibility.

**Key Features**:
- Service orchestration and error handling
- Legacy format conversion
- Context extraction for enhanced services
- Fallback mechanisms

**Integration**: Main entry point for field extraction operations.

### InputNormalizerService
**Purpose**: Clean and normalize user input values before blueprint storage.

**Key Features**:
- Text cleaning (trim, collapse spaces)
- Unknown synonym mapping ("boh" → "unknown")
- Option ID mapping for select fields
- Multi-select array handling
- Data type conversion and validation

**Integration**: Automatically applied by OrchestratorServiceV2 before blueprint storage.

## Data Flow

```
User Input
    ↓
OrchestratorServiceV2.handle_turn()
    ↓
InputNormalizerService.normalize()  ← New normalization step
    ↓
Blueprint Storage (cleaned data)
    ↓
FieldExtractorService.extract_field()  (for free text)
    ├── ClarifierService.generate_clarifier()  (if ambiguous)
    └── QualityCriticService.critique_answer()  (if successful)
    ↓
Legacy Format Conversion
    ↓
Wizard Response
```

## Shared Dependencies

### LLM Provider
All services use the shared LLM provider for intelligent processing:

```python
from app.llm.provider import get_llm_provider

llm = await get_llm_provider()
```

### Logging
Comprehensive logging across all services:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

### Configuration
Services access shared configuration:

```python
from app.core.config import get_config

config = get_config()
```

## Error Handling

### Service-Level Errors
- **LLM Failures**: Graceful degradation with fallbacks
- **Validation Errors**: Clear error messages with suggestions
- **Timeout Issues**: Configurable timeouts with retries

### Integration Errors
- **Service Unavailable**: Fallback to basic functionality
- **Data Corruption**: Validation at service boundaries
- **Context Loss**: Robust context passing between services

## Testing Strategy

### Unit Tests
Each service has comprehensive unit tests:

```bash
# Individual service tests
pytest tests/test_field_extractor.py -v
pytest tests/test_clarifier.py -v
pytest tests/test_quality_critic.py -v
pytest tests/test_orchestrator.py -v
```

### Integration Tests
Cross-service integration validation:

```bash
# Service integration
pytest tests/test_field_extractor_integration.py -v

# Full system tests
pytest tests/test_sessions.py -v
pytest tests/test_wizard_turns.py -v
```

### Test Coverage
- **Unit Tests**: 100% coverage for all service methods
- **Integration Tests**: End-to-end service workflows
- **Error Scenarios**: Comprehensive error condition testing

## Performance Considerations

### Latency
- **Field Extraction**: ~2-3 seconds (includes LLM calls)
- **Clarification**: ~1-2 seconds
- **Quality Critique**: ~1-2 seconds
- **Total per field**: ~3-5 seconds

### Optimization Strategies
- **Async Processing**: All services use async/await
- **Concurrent Calls**: Multiple LLM calls can run in parallel
- **Caching**: Consider response caching for repeated inputs
- **Batch Processing**: Future enhancement for multiple fields

## Configuration

Services are configured through the central config system:

```python
# app/core/config.py
@dataclass
class Config:
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    extraction_timeout: int = 30
    clarification_options_count: int = 4
    quality_critique_enabled: bool = True
```

## Monitoring & Observability

### Logging Levels
- **INFO**: Normal operation events
- **WARNING**: Degraded functionality (fallbacks used)
- **ERROR**: Service failures requiring attention

### Metrics
- Service call counts and success rates
- Average response times per service
- Error rates and types
- LLM token usage

## Development Guidelines

### Adding New Services
1. Create service class with async methods
2. Add comprehensive unit tests
3. Integrate with orchestrator
4. Update documentation
5. Add integration tests

### Service Interface Standards
- All services return Pydantic models
- Async methods for non-blocking operation
- Comprehensive error handling
- Detailed logging for debugging

### Testing Standards
- 100% unit test coverage
- Integration tests for service interactions
- Error scenario coverage
- Performance regression testing

## Future Enhancements

### Planned Features
- **Service Caching**: Response caching for improved performance
- **Batch Processing**: Multi-field extraction optimization
- **Historical Context**: Session-aware quality assessment
- **Adaptive Learning**: Quality threshold calibration

### Architecture Improvements
- **Service Discovery**: Dynamic service loading
- **Circuit Breakers**: Resilience pattern implementation
- **Metrics Collection**: Performance monitoring integration
- **Configuration Management**: Runtime configuration updates

## Troubleshooting

### Common Issues

**LLM Provider Errors**
```
Symptom: Service returns neutral/fallback responses
Solution: Check LLM provider configuration and API keys
```

**Timeout Errors**
```
Symptom: Operations fail with timeout exceptions
Solution: Increase timeout values in config or check network connectivity
```

**Integration Failures**
```
Symptom: Services don't coordinate properly
Solution: Verify orchestrator service integration and context passing
```

### Debug Mode
Enable debug logging for detailed service operation traces:

```python
import logging
logging.getLogger('app.services').setLevel(logging.DEBUG)
```

## Related Documentation

- [Field Extractor Service](docs/FIELD_EXTRACTOR_SERVICE.md)
- [Clarifier Service](docs/CLARIFIER_SERVICE.md)
- [Quality Critic Service](docs/QUALITY_CRITIC_SERVICE.md)
- [Orchestrator Service](docs/ORCHESTRATOR_SERVICE.md)
- [API Reference](API_REFERENCE.md)
- [Architecture Overview](ARCHITECTURE.md)