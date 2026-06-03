# BOOM Wizard Engine

Backend FastAPI per un wizard di consulenza marketing strategica in 7 step. Gestisce sessioni Redis, flusso deterministico, multi-LLM (OpenAI / Gemini / Claude) e generazione del profilo strategico.

## Avvio rapido (Docker)

```bash
cp .env.example .env
# Configura OPENAI_API_KEY (o altro provider) e TENANT_KEYS_JSON in .env

docker-compose up -d
```

API disponibile su `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

## Avvio locale (senza Docker)

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
# Assicurati che Redis sia in esecuzione su localhost:6379
python -m app.main
```

## Variabili d'ambiente essenziali

| Variabile | Descrizione |
|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` |
| `LLM_PROVIDER` | `openai` / `gemini` / `claude` |
| `OPENAI_API_KEY` | Chiave API OpenAI |
| `TENANT_KEYS_JSON` | `{"boom":"API_KEY_123"}` |
| `APP_ENV` | `dev` / `prod` |

## Struttura

```
app/
  api/          # Routes e modelli HTTP
  core/         # Config, logging, security
  llm/          # Adapter multi-provider LLM
  services/     # Servizi business (14 moduli)
  storage/      # Redis store e adapter
  wizard/       # Schema, state machine, flow
tests/          # Test suite pytest
docs/           # Documentazione dettagliata
```

## Documentazione

- [Guida completa](docs/GUIDE.md) — architettura, API reference, deploy, troubleshooting
- [Indice documentazione](docs/INDEX.md) — tutti i servizi e moduli

## Test

```bash
pytest
pytest --cov=app tests/
```
