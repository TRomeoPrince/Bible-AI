# Bible-AI

Bible-AI is a local-first Christian Scripture study system. It is structured around **retrieval from known Bible sources first** and AI explanation second.

## Current v0.1 foundation

- Structured Bible reference parsing
- Pluggable translation-provider interface
- Translation permission metadata
- Local public/open translation support
- Private user-supplied translation support without committing copyrighted text
- Passage lookup API
- Parallel comparison API
- SQLite study notes
- Browser UI
- Translation registry with available/unavailable states

## Core architecture rule

The language model is not treated as an authoritative source of Scripture text. Exact Bible text must come from a registered translation provider.

## Run locally

PowerShell:

    git clone https://github.com/TRomeoPrince/Bible-AI.git
    cd Bible-AI
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn backend.main:app --reload

Then open:

    http://127.0.0.1:8000

## Translation directories

- data/translations/ — public-domain/open translations that may legally be stored with the project
- data/private_translations/ — local-only, user-supplied files; gitignored

## Planned next steps

1. Import verified WEB, KJV, ASV and BSB datasets.
2. Add provider-aware comparison UI.
3. Add natural-language reference extraction.
4. Add Ollama grounding that checks ai_grounding_allowed before supplying text to the model.
5. Add concordance search.
6. Add Hebrew/Greek/Strong's providers.
7. Add cross references and memorization.
