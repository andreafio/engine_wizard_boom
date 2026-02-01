# BOOM Wizard Engine

A production-ready wizard engine backend built with Python/FastAPI that drives a UI-first wizard experience.

## Architecture

- **Framework**: FastAPI + Uvicorn
- **State Management**: Redis (sessions)
- **Database**: PostgreSQL (optional, for events/analytics)
- **LLM Providers**: OpenAI, Google Gemini, Anthropic Claude
- **Containerization**: Docker + Docker Compose

## Project Structure

```
engine_wizard_boom/
├── app/
│   ├── api/                  # API routes
│   │   ├── models.py         # Request/response models
│   │   ├── routes_sessions.py
│   │   └── routes_wizard.py
│   ├── core/                 # Core configuration
│   │   ├── config.py         # Settings
│   │   ├── logging.py        # Structured logging
│   │   └── security.py       # Auth & HMAC
│   ├── wizard/               # Wizard engine logic
│   │   ├── schema.py         # Wizard schema & steps
│   │   ├── state.py          # Session state models
│   │   ├── flow.py           # Flow control & validation
│   │   ├── ui.py             # UI directive builders
│   │   └── extraction.py     # Input extraction
│   ├── llm/                  # LLM provider abstraction
│   │   ├── provider.py       # Base interface
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   ├── claude_provider.py
│   │   └── prompts.py
│   ├── storage/              # Data storage
│   │   └── redis_store.py
│   ├── services/             # Business services
│   │   └── generation_service.py
│   └── main.py               # FastAPI app
├── tests/                    # Tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Wizard Flow

The wizard follows a strict 7-step flow:

1. **Context**: Industry, business model, company size
2. **Objective**: Primary goal, notes
3. **Target Market**: Target role, geography, notes
4. **Value Proposition**: Offer type, problem solved, differentiator
5. **Channels & Assets**: Marketing channels, asset readiness
6. **Constraints**: Budget, timing, additional constraints
7. **Review**: Confirmation step

## API Endpoints

### Sessions

- `POST /v1/sessions/start` - Start a new wizard session
- `GET /v1/sessions/{session_id}` - Get session state
- `DELETE /v1/sessions/{session_id}` - Delete session

### Wizard

- `POST /v1/wizard/turn` - Process wizard turn (main endpoint)
- `POST /v1/wizard/confirm` - Confirm or edit review step
- `POST /v1/wizard/generate` - Generate final presentation and report

### Health

- `GET /health` - Health check
- `GET /` - Root info

## Setup & Installation

### Prerequisites

- Python 3.11+
- Redis
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup**:
```bash
cd engine_wizard_boom
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
```env
APP_ENV=dev
PORT=8000
REDIS_URL=redis://localhost:6379/0
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
TENANT_KEYS_JSON={"boom":"API_KEY_123"}
```

3. **Start Redis** (if not using Docker):
```bash
redis-server
```

4. **Run the application**:
```bash
python -m app.main
```

API will be available at `http://localhost:8000`

### Docker Deployment

1. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your LLM API keys
```

2. **Start all services**:
```bash
docker-compose up -d
```

This starts:
- Redis (port 6379)
- PostgreSQL (port 5432, optional)
- Wizard Engine API (port 8000)

3. **View logs**:
```bash
docker-compose logs -f wizard_engine
```

4. **Stop services**:
```bash
docker-compose down
```

## Usage Examples

### 1. Start a Session

```bash
curl -X POST http://localhost:8000/v1/sessions/start \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {"page_url": "https://example.com"},
    "consent": {"gdpr": true}
  }'
```

Response:
```json
{
  "session_id": "sess_abc123",
  "wizard": {
    "wizard_id": "strategic_snapshot_v1",
    "current_step": "context",
    "progress": 0.0,
    "ui": {
      "type": "single_select",
      "label": "In che settore opera la tua azienda?",
      "field": "industry",
      "options": [...]
    }
  }
}
```

### 2. Send a Wizard Turn

```bash
curl -X POST http://localhost:8000/v1/wizard/turn \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "event_id": "evt_unique_123",
    "ui_event": {
      "type": "selected_option",
      "field": "industry",
      "value": "ecommerce"
    }
  }'
```

### 3. Confirm and Generate

After completing all steps and reaching the review step:

```bash
# Confirm
curl -X POST http://localhost:8000/v1/wizard/confirm \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "event_id": "evt_confirm",
    "action": "confirm",
    "step": "review"
  }'

# Generate
curl -X POST http://localhost:8000/v1/wizard/generate \
  -H "X-Tenant-Id: boom" \
  -H "X-Api-Key: API_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_abc123",
    "event_id": "evt_generate",
    "format": "json"
  }'
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_sessions.py -v
```

## Security

- **API Key Authentication**: Every request requires `X-Tenant-Id` and `X-Api-Key` headers
- **HMAC Signatures**: Optional `X-Signature` header for request tamper-proofing
- **PII Masking**: Sensitive data is automatically masked in logs
- **Rate Limiting**: Built-in rate limiting via slowapi
- **CORS**: Configurable CORS middleware

## Configuration

Key settings in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/prod) | dev |
| `PORT` | API port | 8000 |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |
| `LLM_PROVIDER` | LLM provider (openai/gemini/claude) | openai |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `TENANT_KEYS_JSON` | Tenant API keys JSON | {"boom":"API_KEY_123"} |
| `SESSION_TTL_SECONDS` | Session TTL | 3600 |

## LLM Providers

The engine supports multiple LLM providers through a unified interface:

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Google Gemini
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-pro
```

### Anthropic Claude
```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

## Production Checklist

- [ ] Configure production `TENANT_KEYS_JSON` (use database instead)
- [ ] Set strong `HMAC_SECRET`
- [ ] Configure CORS `allow_origins` for your frontend domain
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up backup for Redis/Postgres
- [ ] Review rate limits
- [ ] Enable signature verification
- [ ] Set `APP_ENV=prod`

## Troubleshooting

### Redis Connection Failed
- Ensure Redis is running: `redis-cli ping`
- Check `REDIS_URL` in `.env`

### LLM Provider Errors
- Verify API key is set and valid
- Check API quota/limits
- Review logs for specific error messages

### Session Not Found
- Sessions expire after TTL (default 1 hour)
- Check Redis is running and session was saved

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

Proprietary - BOOM Digital

## Support

For issues or questions, contact: support@boom-digital.it
