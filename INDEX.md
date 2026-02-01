# 📖 BOOM Wizard Engine - Complete Documentation Index

## 🚀 Quick Start
- **First Time Setup**: [README.md](README.md#setup--installation)
- **Quick Start Scripts**: [start.sh](start.sh) / [start.bat](start.bat)
- **Docker Setup**: [README.md](README.md#docker-deployment)

## 📚 Core Documentation

### 1. [README.md](README.md)
**Complete project guide**
- Architecture overview
- Project structure
- Setup & installation (local + Docker)
- Usage examples
- Configuration guide
- Testing instructions
- Troubleshooting
- Production checklist

### 2. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
**Implementation summary**
- What's been created (complete file list)
- Key features implemented
- Quick start options
- Wizard schema summary
- Configuration overview
- Frontend integration preview
- Production checklist
- Definition of done

### 3. [API_REFERENCE.md](API_REFERENCE.md)
**Quick API reference**
- All endpoints with examples
- Request/response formats
- Wizard steps details
- UI component types
- Error responses
- Complete flow examples
- cURL command examples

### 4. [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)
**Frontend integration guide**
- Architecture overview
- Integration flow (7 steps)
- Code examples (JavaScript)
- Component rendering
- Event handling
- Progress tracking
- Blueprint display
- Error handling
- Styling tips
- Testing checklist

### 5. [ARCHITECTURE.md](ARCHITECTURE.md)
**System architecture diagrams**
- System architecture
- Request flow (wizard turn)
- Data flow (blueprint evolution)
- Generation flow
- Deployment architecture
- State machine diagram
- Security flow
- Logging & monitoring

### 6. [docs/ORCHESTRATOR.md](docs/ORCHESTRATOR.md)
**Wizard Orchestrator role**
- What is the Orchestrator
- Key principles (what it does/never does)
- When it's used (UI events vs free text)
- System prompt and rules
- Example extraction flows
- Implementation details
- Benefits and tradeoffs
- Best practices

## 🔧 Configuration Files

### Environment
- [.env.example](.env.example) - Production template
- [.env.testing](.env.testing) - Testing template with sample values

### Docker
- [Dockerfile](Dockerfile) - Container definition
- [docker-compose.yml](docker-compose.yml) - Multi-service setup

### Python
- [requirements.txt](requirements.txt) - Dependencies
- [Makefile](Makefile) - Common commands

### Misc
- [.gitignore](.gitignore) - Git ignore rules

## 💻 Source Code Structure

### Main Application
```
app/
├── main.py                      # FastAPI application entry point
│
├── api/                         # API Layer
│   ├── models.py                # Request/response Pydantic models
│   ├── routes_sessions.py       # Session management endpoints
│   └── routes_wizard.py         # Wizard turn & generation endpoints
│
├── core/                        # Core Configuration
│   ├── config.py                # Settings & environment variables
│   ├── logging.py               # Structured logging setup
│   └── security.py              # Authentication & HMAC
│
├── wizard/                      # Wizard Engine Core
│   ├── schema.py                # Wizard schema & step definitions
│   ├── state.py                 # Session & blueprint models
│   ├── flow.py                  # Flow control & validation logic
│   ├── ui.py                    # UI directive builders
│   └── extraction.py            # Input extraction & validation
│
├── llm/                         # LLM Provider Abstraction
│   ├── provider.py              # Base provider interface
│   ├── openai_provider.py       # OpenAI implementation
│   ├── gemini_provider.py       # Google Gemini implementation
│   ├── claude_provider.py       # Anthropic Claude implementation
│   └── prompts.py               # Prompt templates
│
├── storage/                     # Data Storage
│   └── redis_store.py           # Redis session storage
│
└── services/                    # Business Services
    └── generation_service.py    # Slides & report generation
```

### Tests
```
tests/
├── conftest.py                  # Test configuration
├── test_sessions.py             # Session endpoint tests
└── test_wizard_turns.py         # Wizard turn tests
```

## 📋 Key Concepts

### Wizard Flow
1. **Context** (14.3%) - Industry, business model, company size
2. **Objective** (28.6%) - Primary goal, notes
3. **Target Market** (42.9%) - Target role, geography, notes
4. **Value Proposition** (57.1%) - Offer type, problem, differentiator
5. **Channels & Assets** (71.4%) - Marketing channels, asset readiness
6. **Constraints** (85.7%) - Budget, timing, additional constraints
7. **Review** (100%) - Confirmation step

### Core Entities

**Session**
- session_id, tenant_id
- current_step, blueprint
- conversation_buffer
- created_at, updated_at

**Blueprint**
- Sections: context, objective, target_market, value_prop, channels_assets, constraints
- Each section: value (dict), status (draft/confirmed)

**UI Directive**
- type: single_select, multi_select, short_text, long_text, confirmation
- label, field, options, constraints

### API Patterns

**All requests require headers:**
```
X-Tenant-Id: boom
X-Api-Key: API_KEY_123
```

**Idempotency:**
- Every request has unique event_id
- Duplicate event_id returns cached response

**Response structure:**
```json
{
  "assistant_message": "...",
  "wizard": {
    "current_step": "...",
    "progress": 0.0,
    "blueprint": {...},
    "ui": {...},
    "validation": {...},
    "events": [...]
  }
}
```

## 🎯 Use Cases & Examples

### Use Case 1: Complete Wizard Flow
```bash
# See: README.md - Usage Examples
# Or: API_REFERENCE.md - Example Flow
```

### Use Case 2: Frontend Integration
```javascript
// See: FRONTEND_INTEGRATION.md - Complete Example Component
```

### Use Case 3: Add Custom LLM Provider
```python
# See: app/llm/provider.py
# Implement LLMProvider interface
```

### Use Case 4: Customize Wizard Schema
```python
# See: app/wizard/schema.py - WIZARD_SCHEMA
# Modify steps, fields, options
```

## 🔍 Finding What You Need

### "How do I start the application?"
→ [README.md](README.md#setup--installation) or [start.sh](start.sh)

### "What are all the API endpoints?"
→ [API_REFERENCE.md](API_REFERENCE.md)

### "How do I integrate with my frontend?"
→ [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)

### "What's the architecture?"
→ [ARCHITECTURE.md](ARCHITECTURE.md)

### "How do I configure LLM providers?"
→ [README.md](README.md#llm-providers)

### "What's been implemented?"
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

### "How do I customize the wizard?"
→ [app/wizard/schema.py](app/wizard/schema.py)

### "How do I add authentication?"
→ [app/core/security.py](app/core/security.py)

### "How do I run tests?"
→ [README.md](README.md#testing)

### "What's the deployment strategy?"
→ [ARCHITECTURE.md](ARCHITECTURE.md#deployment-architecture)

### "How do I troubleshoot issues?"
→ [README.md](README.md#troubleshooting)

## 📊 Project Statistics

- **Total Files**: 38
- **Python Modules**: 24
- **Test Files**: 3
- **Documentation Files**: 7
- **Configuration Files**: 4

### Lines of Code (approximate)
- Python code: ~2,500 lines
- Tests: ~200 lines
- Documentation: ~3,000 lines
- Configuration: ~200 lines

### Test Coverage
- Unit tests for core logic
- Integration tests for API endpoints
- Idempotency tests
- Authentication tests

## 🚢 Deployment Checklist

Before deploying, ensure you've reviewed:
- [ ] [README.md](README.md#production-checklist)
- [ ] [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#-production-checklist)
- [ ] Environment variables configured
- [ ] Security settings hardened
- [ ] Monitoring set up
- [ ] Backup strategy in place

## 🆘 Support & Resources

### Documentation
- **Local Swagger UI**: http://localhost:8000/docs (when running)
- **ReDoc**: http://localhost:8000/redoc (when running)
- **Health Check**: http://localhost:8000/health

### Common Commands
```bash
# Start with Docker
docker-compose up -d

# Start locally
python -m app.main

# Run tests
pytest -v

# View logs
docker-compose logs -f wizard_engine

# Stop services
docker-compose down

# Clean up
make clean
```

### Key Files for Debugging
- Logs: Check `docker-compose logs wizard_engine`
- Redis: `redis-cli` to inspect sessions
- Config: [app/core/config.py](app/core/config.py)
- Main app: [app/main.py](app/main.py)

## 📞 Contact

For questions or issues:
- Email: support@boom-digital.it
- Check logs first
- Review troubleshooting section
- Verify configuration

## 📝 Version History

- **v1.0.0** (January 2026) - Initial MVP release
  - Complete wizard engine
  - Multi-LLM support
  - Docker containerization
  - Full documentation

---

**BOOM Wizard Engine**
Built with ❤️ for BOOM Digital
© 2026 BOOM Digital - All rights reserved
