# Service Integration Map & V2 Unlocks

## 4) Service Integration Points (Mappa Precisione)

### OrchestratorServiceV2 Service Integration

```
User Input (UI Event or Free Text)
    ↓
OrchestratorServiceV2.handle_turn()
    ├── UI Event Path:
    │   └── apply_answer() → Direct blueprint update
    │
    └── Free Text Path:
        ├── FieldExtractorService.extract_field()
        │   ├── Prompt: "Field Extractor"
        │   ├── Input: user_message + context
        │   └── Output: ExtractionResult (value, confidence, needs_clarification)
        │
        ├── IF needs_clarification:
        │   ├── ClarifierService.generate_clarifier()
        │   │   ├── Prompt: "Suggest Options"
        │   │   ├── Input: extraction_result + _build_clarifier_context(blueprint)
        │   │   └── Output: ClarifierOptions (UI config for clarification)
        │   └── RETURN: clarification_ui (interrupt normal flow)
        │
        └── ELSE: proceed with extraction
            ├── QualityCriticService.critique_answer()
            │   ├── Prompt: "Quality Critic"
            │   ├── Input: extraction_result + blueprint context
            │   └── Output: QualityCritique (score, followups, hints)
            │
            ├── _apply_quality_hint() → Store quality flags in blueprint
            ├── apply_answer() → Update blueprint with extracted value
            └── pick_next_question() → Determine next question
```

### Review Phase Integration

```
When current_section == "Review":
    ├── BlueprintReviewService.build_review()
    │   ├── Prompt: "Review Builder"
    │   ├── Input: complete blueprint
    │   └── Output: ReviewSummary (confirmed/draft/missing categories)
    │
    └── RETURN: review_ui (user confirmation required)
```

### Profile Generation Integration

```
After user confirms review:
    ├── StrategicProfileService.generate_internal_profile()
    │   ├── Prompt: "Strategic Profile Generator"
    │   ├── Input: confirmed blueprint
    │   └── Output: StrategicProfile (insights, recommendations, actions)
    │
    └── RETURN: final profile
```

## Service Reference Matrix

| Service | Method | Prompt Reference | Integration Point | Input Context |
|---------|--------|------------------|-------------------|---------------|
| **FieldExtractorService** | `extract_field()` | "Field Extractor" (SERVICES_OVERVIEW.md) | Free text processing | user_message + field_context |
| **ClarifierService** | `generate_clarifier()` | "Suggest Options" (SERVICES_OVERVIEW.md) | Ambiguous extraction | extraction_result + blueprint_context |
| **QualityCriticService** | `critique_answer()` | "Quality Critic" (SERVICES_OVERVIEW.md) | Post-extraction validation | extraction_result + blueprint |
| **BlueprintReviewService** | `build_review()` | "Review Builder" (BLUEPRINT_REVIEW_SERVICE.md) | Review phase | complete_blueprint |
| **StrategicProfileService** | `generate_internal_profile()` | "Strategic Profile Generator" | Post-confirmation | confirmed_blueprint |

## 5) V2 Unlocks (Cosa è Stato Sbloccato)

### 🎯 **Wizard Completo (Tutte le Sezioni)**
- **10 sezioni strutturate**: Context → Objective → Offer → Audience → Funnel → Channels → AssetsTracking → Constraints → Risks → Review
- **Question Bank deterministico**: 50+ domande organizzate per sezione con dipendenze
- **Progress tracking**: Calcolo real-time del completamento (0.0 → 1.0)
- **State management**: Sessione persistente attraverso tutte le fasi

### 🔀 **Sequenziale ma Variabile (Selector)**
- **Deterministic flow**: Progressione prevedibile attraverso le sezioni
- **Dynamic adaptation**: Possibilità di saltare domande basate su risposte precedenti
- **Quality-driven branching**: Follow-up profondi basati su critica qualità
- **Context-aware**: Domande successive influenzate da risposte precedenti

### 🧠 **LLM Usato in Modo Non Distruttivo**
- **Isolated services**: Ogni servizio LLM lavora su input specifici senza side effects
- **Confidence scoring**: Ogni estrazione valutata per affidabilità (0.0-1.0)
- **Fallback systems**: Comportamento graceful quando LLM fallisce
- **Caching intelligente**: Idempotency per evitare chiamate duplicate
- **Error boundaries**: Isolamento dei failure per servizio

### ✅ **Review Serena Prima della Generazione**
- **Pre-generation validation**: Review obbligatoria prima della generazione profilo
- **User confirmation**: Controllo umano sui dati raccolti
- **Draft/Missing categorization**: Identificazione chiara di cosa manca
- **Quality assurance**: Possibilità di correggere prima della generazione finale

### 🔮 **Pronto per Research Layer (Pre-fill Draft)**
- **Modular architecture**: Facile aggiunta di research service
- **Draft population**: Possibilità di pre-riempire risposte con dati ricercati
- **Fallback hierarchy**: Research → User Input → Default Values
- **Confidence layering**: Research data con confidence separato da user input
- **Async enrichment**: Possibilità di arricchire blueprint in background

## V2 Architectural Advantages

### Separation of Concerns
```
├── Data Collection (Wizard Flow)
├── Quality Assurance (Critique + Review)
├── Intelligence (LLM Services)
└── Generation (Strategic Profile)
```

### Scalability Vectors
- **Horizontal**: Più istanze di orchestrator indipendenti
- **Vertical**: Aggiunta servizi senza modificare core flow
- **Intelligence**: Upgrade LLM senza cambiare integration points
- **UI**: Frontend completamente separato dalla logica di business

### Reliability Features
- **Idempotency**: Sicurezza retry senza duplicati
- **Graceful degradation**: Funzionamento anche con servizi parziali
- **State isolation**: Sessioni indipendenti e isolabili
- **Error recovery**: Recovery automatico da failure temporanei

### Future-Proof Design
- **Service abstraction**: Facile sostituzione di qualsiasi servizio
- **Configuration-driven**: Question bank caricabile dinamicamente
- **Event-driven**: Architettura pronta per event streaming
- **API-first**: Design pronto per microservices evolution