# Wizard Engine Architecture Overview

## System Components

### Core Services

#### 1. OrchestratorServiceV2
**Location**: `app/services/orchestrator_service_v2.py`
**Purpose**: Central coordinator for all wizard interactions
**Key Features**:
- Deterministic question flow through structured sections
- Multi-modal input handling (UI events + free text)
- Intelligent service integration with automatic clarification
- Review phase before profile generation
- Idempotent operations with event deduplication

#### 2. FieldExtractorService
**Location**: `app/services/field_extractor_service.py`
**Purpose**: Extract structured data from natural language input
**Key Features**:
- LLM-powered field extraction with confidence scoring
- Automatic clarification detection
- Fallback handling for ambiguous inputs

#### 3. ClarifierService
**Location**: `app/services/clarifier_service.py`
**Purpose**: Generate contextual clarification options
**Key Features**:
- Dynamic option generation based on context
- Multiple choice and free text options
- Fallback systems for edge cases

#### 4. QualityCriticService
**Location**: `app/services/quality_critic_service.py`
**Purpose**: Assess answer quality and recommend improvements
**Key Features**:
- 0.0-1.0 quality scoring
- Follow-up question recommendations
- Quality hint storage for future reference

#### 5. BlueprintReviewService
**Location**: `app/services/blueprint_review_service.py`
**Purpose**: Create pre-generation review summaries
**Key Features**:
- Categorized review (confirmed/draft/missing)
- User confirmation workflow
- Final validation before generation

#### 6. StrategicProfileService
**Location**: `app/services/strategic_profile_service.py`
**Purpose**: Generate internal strategic profiles
**Key Features**:
- Comprehensive operational insights
- Marketing/sales team recommendations
- Data-driven strategic analysis

### Supporting Infrastructure

#### Session Store
**Location**: `app/storage/redis_store.py` (interface)
**Purpose**: Persistent session state management
**Key Features**:
- Abstract interface for different backends (Redis/Memory)
- Idempotency support for event deduplication
- Tenant isolation and session scoping

#### Question Bank
**Location**: `app/services/orchestrator_utils.py`
**Purpose**: Structured question definitions and flow logic
**Key Features**:
- Section-based organization
- Dependency management
- Deterministic progression logic

#### LLM Providers
**Location**: `app/llm/` (multiple providers)
**Purpose**: Unified interface to different LLM services
**Key Features**:
- OpenAI, Claude, Gemini support
- Configurable models and parameters
- Error handling and fallbacks

## Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│ Orchestrator V2  │───▶│  Session Store  │
│                 │    │                  │    │                 │
│ • UI Events     │    │ • Turn Handling  │    │ • State Persist │
│ • Free Text     │    │ • Service Coord  │    │ • Idempotency   │
│ • Context       │    │ • Progress Calc  │    │ • Cache         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intelligent Services                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │Field Extract│  │  Clarifier  │  │Quality Critic│  │ Review  │  │
│  │             │  │             │  │             │  │ Service │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘  │
│                                                                 │
│  ┌─────────────┐                                                 │
│  │Strategic    │                                                 │
│  │Profile      │                                                 │
│  └─────────────┘                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Question Flow Logic

### Section Progression
1. **Context** → Company basics (industry, size, location)
2. **Objective** → Business goals and challenges
3. **Offer** → Value proposition and differentiation
4. **Audience** → Target market and customer segments
5. **Funnel** → Sales process and customer journey
6. **Channels** → Marketing channels and tactics
7. **AssetsTracking** → KPIs and measurement
8. **Constraints** → Limitations and boundaries
9. **Risks** → Risk assessment and mitigation
10. **Review** → Final confirmation and validation

### Flow States
- **Normal Flow**: Sequential question progression
- **Clarification Interrupt**: Pause for ambiguous input resolution
- **Review Phase**: Pre-generation validation
- **Generation Ready**: All data collected and confirmed

## Key Design Patterns

### Service Integration Pattern
```python
# Orchestrator coordinates services based on input type
if ui_event:
    # Direct application
    apply_answer(blueprint, ui_event)
elif user_message:
    # Service chain: Extract → Clarify → Critique
    extraction = await field_extractor.extract_field(user_message, context)
    if extraction.needs_clarification:
        clarification = await clarifier.generate_clarifier(extraction, context)
        return clarification_ui
    quality = await critic.critique_answer(extraction, blueprint)
    apply_answer(blueprint, extraction)
```

### Idempotency Pattern
```python
# Prevent duplicate processing
cache_key = f"{session_id}:{event_id}"
cached_result = await session_store.get_idempotent(cache_key)
if cached_result:
    return cached_result

# Process and cache
result = await process_turn(payload)
await session_store.put_idempotent(cache_key, result)
return result
```

### State Management Pattern
```python
# Immutable state updates
current_state = await session_store.get_session(session_id, tenant_id)
new_state = current_state.copy()
new_state['blueprint'] = updated_blueprint
new_state['current_section'] = next_section
await session_store.put_session(session_id, tenant_id, new_state)
```

## Testing Strategy

### Unit Testing
- **Service Isolation**: Mock all dependencies
- **Flow Logic**: Test question progression algorithms
- **State Transitions**: Verify blueprint updates
- **Error Handling**: Test failure scenarios

### Integration Testing
- **End-to-End Flows**: Complete wizard journeys
- **Service Coordination**: Verify inter-service communication
- **Data Consistency**: Ensure blueprint integrity across services

### Test Coverage
- **Orchestrator**: 8 comprehensive test cases
- **Individual Services**: 15+ tests per service
- **Utilities**: Question bank and helper functions
- **Error Scenarios**: Failure recovery and edge cases

## Performance Characteristics

### Latency Targets
- **UI Events**: < 200ms (no external calls)
- **Free Text Processing**: < 3s (LLM extraction + quality check)
- **Clarification Generation**: < 2s (LLM option generation)
- **Review Phase**: < 3s (LLM summary generation)

### Scalability Considerations
- **Async Processing**: Non-blocking service calls
- **Caching Layer**: Idempotency and response caching
- **Session Isolation**: Tenant-based data partitioning
- **Resource Pooling**: Connection reuse for external services

## Deployment Architecture

### Containerized Deployment
```yaml
# docker-compose.yml structure
services:
  wizard-engine:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
    ports:
      - "8000:8000"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### Environment Configuration
- **Development**: Local Redis, mock LLM services
- **Staging**: Cloud Redis, real LLM services with rate limits
- **Production**: Managed Redis, production LLM endpoints

## Monitoring & Observability

### Key Metrics
- **Throughput**: Turns processed per second
- **Latency**: P95 response times by operation type
- **Error Rates**: Service failure percentages
- **Progress Rates**: User completion funnel analysis

### Logging Strategy
- **Structured Logs**: JSON format with correlation IDs
- **Service Tracing**: Request/response logging for all services
- **Error Context**: Detailed error information with stack traces
- **Performance Logs**: Timing information for optimization

## Future Roadmap

### Phase 1: Core Stabilization
- [x] Implement all core services
- [x] Complete orchestrator integration
- [x] Comprehensive test coverage
- [ ] Redis session store implementation
- [ ] Integration testing with real services

### Phase 2: Advanced Features
- [ ] Dynamic question adaptation
- [ ] Multi-language support
- [ ] A/B testing framework
- [ ] Advanced analytics

### Phase 3: Performance & Scale
- [ ] Response caching layer
- [ ] Batch processing optimization
- [ ] CDN integration
- [ ] Auto-scaling configuration

### Phase 4: Intelligence Enhancement
- [ ] Machine learning for question optimization
- [ ] User behavior analysis
- [ ] Predictive clarification
- [ ] Automated quality improvement