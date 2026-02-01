# Setup API Keys per Ricerca Web Real-Time

## 🔍 Perché servono?

GPT-4 ha un knowledge cutoff (dati fino a ~Aprile 2024) e **non può cercare informazioni aggiornate** su aziende specifiche come Alfagoma SPA.

Per ottenere **dati real-time** dobbiamo usare API di ricerca web.

---

## 🆓 API Gratuite Disponibili

### 1. **Serper.dev** (Raccomandato)
- **API:** Google Search API (alternativa ufficiale)
- **Free Tier:** 2,500 ricerche/mese GRATIS
- **Setup:** 2 minuti
- **Qualità:** ⭐⭐⭐⭐⭐ (risultati Google)

**Come ottenere:**
1. Vai su: https://serper.dev
2. Click "Sign Up Free"
3. Conferma email
4. Dashboard → Copia API Key

**Aggiungi al .env:**
```bash
SERPER_API_KEY=your_key_here
```

---

### 2. **Bing Search API** (Alternativa)
- **API:** Microsoft Bing Web Search
- **Free Tier:** 3,000 ricerche/mese GRATIS
- **Setup:** 5 minuti (richiede Azure account)
- **Qualità:** ⭐⭐⭐⭐ (risultati Bing)

**Come ottenere:**
1. Vai su: https://portal.azure.com
2. Crea account gratuito (no carta richiesta per tier free)
3. Cerca "Bing Search API v7"
4. Crea risorsa con Free pricing tier (F1)
5. Dashboard → Keys → Copia Key 1

**Aggiungi al .env:**
```bash
BING_SEARCH_API_KEY=your_key_here
```

---

## 🚀 Setup Rapido (Serper.dev - 2 minuti)

### Step 1: Registrati
```
https://serper.dev
→ Sign Up Free
→ Conferma email
```

### Step 2: Ottieni API Key
```
Dashboard → API Key → Copy
```

### Step 3: Configura
```powershell
# Windows PowerShell
$env:SERPER_API_KEY = "your_key_here"

# Oppure aggiungi a .env file:
echo SERPER_API_KEY=your_key_here >> .env
```

### Step 4: Test
```bash
python test_alfagoma_research.py
```

---

## 📊 Confronto API

| Provider | Free Tier | Setup | Qualità | Velocità |
|----------|-----------|-------|---------|----------|
| **Serper.dev** | 2,500/mese | 2 min | Google | Veloce |
| **Bing API** | 3,000/mese | 5 min | Bing | Media |
| **SerpAPI** | 100/mese | 2 min | Google | Veloce |
| **ScraperAPI** | 1,000/mese | 3 min | Any | Lenta |

**Raccomandazione:** Usa **Serper.dev** per semplicità e qualità.

---

## 🔧 Esempio Utilizzo

### Senza Web Search (dati vecchi)
```python
research = await research_company_intelligence(
    company_name="Alfagoma SPA",
    industry="Manifatturiero"
)
# ❌ GPT usa solo knowledge base (dati fino ad Aprile 2024)
# Competitor generici, nessuna info recente
```

### Con Web Search (dati aggiornati)
```python
# Imposta SERPER_API_KEY
os.environ["SERPER_API_KEY"] = "your_key"

research = await research_company_intelligence(
    company_name="Alfagoma SPA",
    industry="Manifatturiero"
)
# ✅ GPT analizza risultati Google real-time
# Competitor reali, info aggiornate, news recenti
```

---

## 📝 Cosa Cambia con Web Search?

### Prima (solo GPT knowledge):
```json
{
  "competitors": [
    "Parker Hannifin (global leader)",
    "Bosch Rexroth (automation)",
    "Continental AG (automotive)"
  ],
  "insights": [
    "Company has low social engagement",
    "Competitors invest in LinkedIn"
  ]
}
```

### Dopo (con Google Search):
```json
{
  "competitors": [
    "Competitor A (web: trovato su Google, settore specifico italiano)",
    "Competitor B (web: news recente, nuova acquisizione)",
    "Competitor C (web: sito simile, stessa regione)"
  ],
  "insights": [
    "Web search: Alfagoma SPA specializzata in componenti idraulici",
    "Web search: Recente espansione mercato europeo (news 2025)",
    "Web search: Competitor locale X ha lanciato prodotto simile"
  ]
}
```

---

## 🎯 Risultati Attesi

### Con SERPER_API_KEY configurato:

```
🔍 Avvio ricerca...
✅ Web search: 5 risultati Google trovati
   - Alfagoma SPA - Official Website
   - Alfagoma SPA su LinkedIn
   - Alfagoma SPA: Componenti Industriali (news)
   
📊 Competitor identificati (da web search):
   1. Competitor reale trovato su Google
   2. Azienda italiana settore simile
   3. Partner/distributore menzionato online
   
💡 Insights basati su dati real-time:
   - Prodotti specifici trovati su sito web
   - News recenti analizzate
   - Presenza online reale valutata
```

---

## ⚠️ Fallback Automatico

Se **nessuna API key** configurata:
- ✅ Il sistema funziona comunque
- ⚠️ Usa solo GPT knowledge base (dati vecchi)
- 📝 Log: "no_web_search_api - Set SERPER_API_KEY for real-time data"

---

## 💰 Costi

| Provider | Free Tier | Oltre Free | Costo |
|----------|-----------|------------|-------|
| Serper.dev | 2,500 | 5,000 | $50/mese |
| Bing API | 3,000 | 100,000 | $3/1k |
| SerpAPI | 100 | 5,000 | $50/mese |

**Per uso normale:** Free tier sufficiente (2,500 ricerche = 80+ ricerche/giorno)

---

## 🚦 Quick Start

```powershell
# 1. Registrati Serper.dev (2 min)
start https://serper.dev

# 2. Copia API key

# 3. Configura
$env:SERPER_API_KEY = "paste_your_key"
$env:OPENAI_API_KEY = "your_openai_key"

# 4. Test
python test_alfagoma_research.py

# 5. Verifica log
# ✅ "searching_web" → Web search attivo
# ✅ "web_results: 5 found" → Dati real-time
```

---

## 📚 Risorse

- **Serper.dev Docs:** https://serper.dev/docs
- **Bing API Docs:** https://learn.microsoft.com/en-us/bing/search-apis/
- **SerpAPI (alternativa):** https://serpapi.com

---

## ✅ Checklist

- [ ] Registrato su Serper.dev
- [ ] Ottenuto API key
- [ ] Aggiunto `SERPER_API_KEY` al .env
- [ ] Testato con `python test_alfagoma_research.py`
- [ ] Verificato log "searching_web"
- [ ] Risultati contengono dati real-time

**Tempo totale setup:** ~3 minuti

---

_Senza web search API, GPT usa solo knowledge base (dati fino ad Aprile 2024)._
_Con Serper.dev, GPT analizza risultati Google in tempo reale._
