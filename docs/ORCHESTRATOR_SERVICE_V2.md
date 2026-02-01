# Orchestrator Service V2

## Overview

The Orchestrator Service V2 is an advanced wizard orchestrator that integrates all intelligent services for a deterministic, resilient question flow. It provides seamless coordination between field extraction, clarification, quality assessment, review, and profile generation.

## Key Features

- **Deterministic Question Flow**: Predictable progression through wizard sections
- **Multi-Modal Input**: Handles both UI events and free text input
- **Intelligent Service Integration**: Automatic clarification and quality assessment
- **Review Phase**: Pre-generation validation with user confirmation
- **Idempotent Operations**: Safe retry handling with event deduplication
- **Progress Tracking**: Real-time completion percentage calculation

## Architecture

```
User Input (UI Event or Free Text)
    ↓
OrchestratorServiceV2.handle_turn()
    ├── Idempotency Check
    ├── Session State Load
    ├── pick_next_question() → Current Question
    ├── Apply User Input
    │   ├── UI Event → apply_answer()
    │   └── Free Text → FieldExtractorService
    │       ├── Needs Clarification → ClarifierService
    │       └── Quality Check → QualityCriticService
    ├── Advance Logic
    │   ├── pick_next_question() → Next Question
    │   └── Review Phase → BlueprintReviewService
    └── Response Building
        ├── TurnOutput with Assistant Message
        └── Wizard State with UI Configuration
```

## Service Integration

### FieldExtractorService
- **Purpose**: Extract structured data from free text input
- **Integration**: Called when user provides free text instead of UI selection
- **Fallback**: Handles ambiguous input gracefully

### ClarifierService
- **Purpose**: Generate clarification options for ambiguous answers
- **Integration**: Automatically invoked when extraction confidence is low
- **Flow**: Interrupts normal flow to get clarification before proceeding

### QualityCriticService
- **Purpose**: Assess answer quality and recommend follow-ups
- **Integration**: Applied to all successful extractions
- **Hints**: Stores quality hints for future reference

### BlueprintReviewService
- **Purpose**: Create pre-generation review summaries
- **Integration**: Called when transitioning to Review phase
- **Confirmation**: Provides user with final validation opportunity

### StrategicProfileService
- **Purpose**: Generate internal strategic profiles
- **Integration**: Called after user confirms review
- **Output**: Complete strategic analysis for marketing/sales teams

## Question Flow Logic

### Deterministic Progression
```python
current_section, current_question = pick_next_question(
    blueprint=blueprint,
    question_bank=QUESTION_BANK,
    current_section=current_section
)
```

### Section Order
1. **Context** - Company information
2. **Objective** - Business goals
3. **Offer** - Value proposition
4. **Audience** - Target market
5. **Funnel** - Sales process
6. **Channels** - Marketing channels
7. **AssetsTracking** - KPIs and metrics
8. **Constraints** - Limitations
9. **Risks** - Risk assessment
10. **Review** - Final confirmation

### Flow States
- **Normal**: Ask next unanswered question
- **Clarification**: Interrupt for ambiguous input resolution
- **Review**: Pre-generation validation
- **Complete**: All questions answered, ready for generation

## Input/Output Formats

### TurnInput
```python
@dataclass
class TurnInput:
    session_id: str
    event_id: str
    ui_event: Optional[Dict[str, Any]] = None  # {type, field, value, ui_type}
    user_message: Optional[str] = None
    context: Dict[str, Any] = None
```

### TurnOutput
```python
@dataclass
class TurnOutput:
    assistant_message: str
    wizard: Dict[str, Any]  # Complete wizard state
```

### Wizard State Structure
```json
{
  "current_section": "Context",
  "progress": 0.15,
  "blueprint": {
    "context": {
      "industry": {
        "value": "technology",
        "ui_type": "single_select",
        "source": "user",
        "evidence": "",
        "timestamp": "2026-01-30T13:00:00Z"
      }
    }
  },
  "ui": {
    "type": "single_select",
    "label": "In che settore opera la tua azienda?",
    "field": "context.company_size",
    "options": [...]
  },
  "validation": {"errors": []},
  "events": [{"type": "saved", "label": "Salvato ✓"}]
}
```

## Session Management

### Session Store Interface
```python
class SessionStore:
    async def get_session(self, session_id: str, tenant_id: str) -> Dict[str, Any]
    async def put_session(self, session_id: str, tenant_id: str, session: Dict[str, Any]) -> None
    async def get_idempotent(self, session_id: str, event_id: str) -> Optional[Dict[str, Any]]
    async def put_idempotent(self, session_id: str, event_id: str, result: Any) -> None
```

### Session State
```json
{
  "blueprint": {
    "context": {...},
    "objective": {...},
    // ... all sections
  },
  "current_section": "Context"
}
```

## Idempotency Handling

### Event Deduplication
- **Event ID**: Unique identifier for each user interaction
- **Cache Key**: `{session_id}:{event_id}`
- **TTL**: Configurable cache expiration
- **Safety**: Prevents duplicate processing of same event

### Cache Strategy
```python
# Check cache first
cached = await session_store.get_idempotent(session_id, event_id)
if cached:
    return TurnOutput(**cached)

# Process turn...

# Cache result
await session_store.put_idempotent(session_id, event_id, result.__dict__)
```

## Progress Calculation

### Algorithm
```python
def calculate_progress(blueprint: Dict[str, Any]) -> float:
    total_questions = sum(len(section.questions) for section in QUESTION_BANK.values())
    answered_questions = count_answered_questions(blueprint)
    return answered_questions / total_questions
```

### Progress States
- **0.0**: No questions answered
- **0.33**: Context section complete
- **0.67**: Core strategy sections complete
- **1.0**: All questions answered, ready for review

## Error Handling

### Service Failures
- **LLM Errors**: Graceful fallback with error indication
- **Session Errors**: Safe session state handling
- **Validation Errors**: Input validation with clear error messages

### Recovery Strategies
- **Fallback UI**: Safe UI configuration when services fail
- **Partial State**: Preserve valid data when errors occur
- **User Guidance**: Clear error messages with recovery instructions

## Testing Strategy

### Unit Tests
- **Service Integration**: Mock all dependent services
- **Flow Logic**: Test question progression logic
- **State Management**: Verify session state handling
- **Error Scenarios**: Test failure recovery

### Integration Tests
- **End-to-End Flows**: Complete wizard journeys
- **Service Coordination**: Verify service interaction
- **Data Consistency**: Ensure blueprint integrity

## Usage Examples

### Basic Turn Handling
```python
orchestrator = OrchestratorServiceV2(
    session_store=redis_store,
    field_extractor_service=field_extractor,
    clarifier_service=clarifier,
    quality_critic_service=critic,
    blueprint_review_service=review,
    strategic_profile_service=profile
)

# Handle UI event
result = await orchestrator.handle_turn(
    tenant_id="tenant-123",
    payload=TurnInput(
        session_id="session-456",
        event_id="event-789",
        ui_event={
            "field": "context.industry",
            "value": "technology",
            "ui_type": "single_select"
        }
    )
)

print(result.assistant_message)
print(f"Progress: {result.wizard['progress']}")
```

### Free Text Input
```python
result = await orchestrator.handle_turn(
    tenant_id="tenant-123",
    payload=TurnInput(
        session_id="session-456",
        event_id="event-790",
        user_message="We work in the technology industry with 50 employees"
    )
)
```

### Profile Generation
```python
profile = await orchestrator.handle_generate_internal(
    tenant_id="tenant-123",
    session_id="session-456",
    event_id="generate-001"
)

print(profile["summary"])
```

## Performance Considerations

### Latency Targets
- **UI Events**: < 200ms (no LLM calls)
- **Free Text**: < 3s (field extraction + quality check)
- **Clarification**: < 2s (clarifier service)
- **Review Phase**: < 3s (review generation)

### Optimization Strategies
- **Async Processing**: All service calls are async
- **Caching**: Idempotency cache for repeated requests
- **Lazy Loading**: Services loaded only when needed
- **Batch Operations**: Minimize individual service calls

## Monitoring & Observability

### Key Metrics
- **Turn Duration**: Time to process each turn
- **Service Call Counts**: Usage statistics per service
- **Error Rates**: Failure rates by service and operation
- **Progress Distribution**: User completion rates

### Logging
- **Turn Events**: Start/complete with key parameters
- **Service Calls**: Request/response logging
- **State Changes**: Blueprint and session updates
- **Errors**: Detailed error context and stack traces

## Future Enhancements

### Advanced Features
- **Dynamic Questions**: Questions that adapt based on previous answers
- **Branching Logic**: Conditional question paths
- **Multi-Language Support**: Localized question banks
- **A/B Testing**: Alternative question flows

### Performance Improvements
- **Response Caching**: Cache common LLM responses
- **Batch Processing**: Process multiple turns concurrently
- **Progressive Loading**: Lazy-load question banks
- **CDN Integration**: Distribute static assets

### Analytics Integration
- **User Behavior**: Track question completion patterns
- **Conversion Funnels**: Measure drop-off points
- **Quality Metrics**: Monitor answer quality trends
- **Performance Analytics**: System performance dashboards