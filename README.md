# Bible-AI

Bible-AI is a local-first Christian study system built around **structured Scripture retrieval first, source-aware AI second**.

Current development target: **v0.8 (~80% functional core)**.

## What works now

### Scripture
- Natural-language reference detection for normal references such as `John 3:3` and `Romans 8:28-30`
- Live licensed Bible discovery and passage retrieval through YouVersion
- Translation selector populated from the versions licensed to your YouVersion App Key
- Parallel translation comparison
- Exact translation/provider attribution kept separate from commentary
- Local translation-provider architecture for future public-domain/offline Bibles

### Original languages and word study
- IQ Bible API v2 integration
- Strong's Greek/Hebrew lookup
- IQ Bible AI/study context endpoint
- Morphology-code decoding endpoint
- Optional local Thayer's Greek-English Lexicon support
- Provider/source labels kept in responses

### AI study
- Local Ollama reasoning layer
- Bible Study mode
- Theology comparison mode
- Apologetics mode
- Biblical/church-history mode
- Original-language mode
- Quiz generation
- Book-summary generation
- Topic-study generation
- Study-plan generation
- Guardrail: the model must not invent Scripture wording

### Persistent study memory
SQLite stores:
- notes
- preferred translation
- passages studied
- questions asked
- chat history
- memorization verses and review counts
- study plans

### Browser UI
The browser app now has:
- Ask Bible-AI
- Scripture lookup
- Parallel comparison
- Word Study
- Study Memory / memorization
- Study-plan generation
- live provider-status display

## Architecture

```text
Browser UI
   |
FastAPI
   |
   +-- ScriptureService
   |      +-- YouVersion (licensed translation display)
   |      +-- Local translation providers
   |
   +-- StudyAI
   |      +-- IQ Bible AI/study context
   |      +-- Ollama local model
   |
   +-- Word Study
   |      +-- IQ Bible Strong's / morphology / lexicons
   |      +-- Local Thayer dataset (optional)
   |
   +-- SQLite
          +-- notes
          +-- preferences
          +-- memory
          +-- memorization
          +-- study plans
          +-- chat history
```

## Important source rule

Bible-AI does not treat the language model as a Bible-text database.

- YouVersion passages are retrieved from YouVersion and displayed as supplied.
- IQ Bible supplies AI/study context, Strong's and language resources.
- AI explanations are visibly separate from Scripture.
- Bible-AI does not silently substitute another translation.

## Setup on Windows

From PowerShell or Command Prompt:

```powershell
git clone https://github.com/TRomeoPrince/Bible-AI.git
cd Bible-AI

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

Create a file named `.env` in the repository root:

```env
YOUVERSION_APP_KEY=your_real_key
IQBIBLE_API_KEY=your_real_key
IQBIBLE_BASE_URL=https://api.iqbible.com

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

Never commit `.env`.

### Ollama

Install Ollama, then pull the configured model:

```powershell
ollama pull qwen2.5:3b
```

Then run Bible-AI:

```powershell
uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Provider status:

```text
http://127.0.0.1:8000/api/providers
```

Health status:

```text
http://127.0.0.1:8000/api/health
```

## Optional local Thayer lexicon

Bible-AI can install the public-domain/CC0 digitized Thayer dataset locally:

```powershell
python scripts/install_open_data.py thayer
```

The downloaded dataset stays local and is ignored by Git.

## Main API endpoints

```text
GET  /api/translations
GET  /api/passage
GET  /api/compare

GET  /api/word-study/strongs/{G-or-H-number}
GET  /api/word-study/context
GET  /api/morphology/{code}

POST /api/chat
POST /api/tools/quiz
POST /api/tools/topic-study
POST /api/tools/book-summary

POST /api/notes
GET  /api/notes

POST /api/memorization
GET  /api/memorization
POST /api/memorization/{id}/review

POST /api/study-plans
GET  /api/study-plans
```

## What remains for v1.0

The remaining ~20% is intentionally the heavier finishing layer:

- verified offline WEB/KJV/ASV/BSB imports
- local OSHB/WLC Hebrew + morphology
- additional open Greek morphology datasets
- richer rendered interlinear UI instead of raw IQ-context JSON
- cross-reference graph visualization
- actual memorization quiz/session UI
- deeper curated church-history primary-source corpus
- theological source library / RAG
- online academic research connector
- citations rendered at paragraph/claim level
- caching that exactly follows each provider's license rules
- full API error/retry telemetry
- mobile-ready sync/auth
- packaging for a simple Windows launcher
- security and production deployment hardening

## Development

CI compiles the backend and runs tests on every push to `main`.

This project is intentionally modular so the same FastAPI backend can later power a mobile client.
