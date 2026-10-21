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
- Original-language provider interface
- Lexicon provider interface
- Local lexicon loader
- YouVersion integration scaffold
- IQ Bible integration scaffold
- Provider-status endpoint

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

Provider status:

    http://127.0.0.1:8000/api/providers

## Translation directories

- data/translations/ — public-domain/open translations that may legally be stored with the project
- data/private_translations/ — local-only, user-supplied files; gitignored

## Original-language and lexicon directories

- data/original_languages/ — Hebrew/Greek source datasets
- data/lexicons/ — Strong's, Thayer, BDB and related local lexicon files

## External provider configuration

Create a local .env file or set environment variables:

    YOUVERSION_APP_KEY=your_youversion_key
    IQBIBLE_API_KEY=your_iqbible_key

Do not commit real keys.

## Next implementation targets

1. Import verified WEB, KJV, ASV and BSB Scripture datasets.
2. Wire YouVersion passage/version endpoints into the translation registry.
3. Wire IQ Bible original-language endpoints into OriginalLanguageProvider.
4. Import local Strong's and Thayer datasets.
5. Import OSHB/WLC Hebrew morphology.
6. Add word-study endpoints and UI.
7. Add concordance, cross references and memorization.
8. Add Ollama-grounded explanations with source/permission checks.
