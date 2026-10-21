from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.ai.study import StudyAI
from backend.bible.references import extract_reference, parse_reference
from backend.database import connect, init_db
from backend.integrations.iqbible import IQBibleClient
from backend.integrations.youversion import YouVersionClient
from backend.services.scripture import ScriptureService
from backend.study.repository import (
    add_memory,
    add_memorization,
    create_study_plan,
    get_setting,
    list_memory,
    list_memorization,
    list_study_plans,
    review_memorization,
    set_setting,
)


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

app = FastAPI(title="Bible-AI", version="0.8.0")
scripture = ScriptureService()
study_ai = StudyAI()
iq = IQBibleClient()
youversion = YouVersionClient()


class NoteCreate(BaseModel):
    reference: str
    note: str
    translation: str | None = None


class SettingUpdate(BaseModel):
    value: str


class MemoryCreate(BaseModel):
    kind: str
    value: str
    reference: str | None = None


class MemorizationCreate(BaseModel):
    reference: str
    translation: str = "WEB"


class MemorizationReview(BaseModel):
    correct: bool


class StudyPlanCreate(BaseModel):
    title: str
    topic: str
    days: int = Field(default=7, ge=1, le=365)
    generate: bool = True


class ChatRequest(BaseModel):
    question: str
    reference: str | None = None
    translation: str | None = None
    bible_id: int | None = None
    mode: str = "study"


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": "Bible-AI",
        "version": "0.8.0",
        "ollama": await study_ai.ollama.available(),
        "youversion_configured": youversion.configured,
        "iqbible_configured": iq.configured,
    }


@app.get("/api/providers")
async def providers():
    return {
        "youversion": {
            "configured": youversion.configured,
            "purpose": "Licensed Scripture retrieval/display",
        },
        "iqbible": {
            "configured": iq.configured,
            "purpose": "AI context, original-language, Strong's, lexicon, morphology and study enrichment",
        },
        "ollama": {
            "configured": await study_ai.ollama.available(),
            "model": study_ai.ollama.model,
            "purpose": "Local AI reasoning/explanation",
        },
    }


@app.get("/api/translations")
async def translations(language: str = "en"):
    return await scripture.list_translations(language)


@app.get("/api/passage")
async def passage(
    reference: str,
    translation: str = "WEB",
    bible_id: int | None = None,
):
    try:
        return await scripture.get_passage(reference, translation, bible_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/compare")
async def compare(reference: str, translations: str = "KJV,NIV,BSB"):
    codes = [x.strip() for x in translations.split(",") if x.strip()]
    return {
        "reference": parse_reference(reference).canonical(),
        "comparisons": await scripture.compare(reference, codes),
    }


@app.get("/api/word-study/strongs/{strong_number}")
async def strongs_lookup(strong_number: str):
    if not iq.configured:
        raise HTTPException(status_code=503, detail="IQ Bible API is not configured.")
    try:
        return {
            "strong_number": strong_number.upper(),
            "provider": "IQ Bible API",
            "data": await iq.strongs(strong_number),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/word-study/context")
async def word_study_context(reference: str):
    if not iq.configured:
        raise HTTPException(status_code=503, detail="IQ Bible API is not configured.")
    try:
        parsed = parse_reference(reference)
        from backend.bible.usfm import to_usfm
        compact = to_usfm(parsed.book, parsed.chapter, parsed.start_verse, parsed.end_verse)
        return {
            "reference": parsed.canonical(),
            "provider": "IQ Bible API",
            "data": await iq.ai_context(compact),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/morphology/{code}")
async def morphology(code: str):
    if not iq.configured:
        raise HTTPException(status_code=503, detail="IQ Bible API is not configured.")
    try:
        return {"code": code, "provider": "IQ Bible API", "data": await iq.morphology(code)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    detected = payload.reference
    if not detected:
        extracted = extract_reference(payload.question)
        if extracted:
            detected = extracted.canonical()

    translation = payload.translation or get_setting("preferred_translation", "WEB") or "WEB"
    display = None
    if detected:
        try:
            display = await scripture.get_passage(detected, translation, payload.bible_id)
        except Exception:
            display = None

    with connect() as con:
        con.execute(
            "INSERT INTO chat_history(role, content, reference, mode) VALUES (?, ?, ?, ?)",
            ("user", payload.question, detected, payload.mode),
        )

    result = await study_ai.answer(
        question=payload.question,
        reference=detected,
        mode=payload.mode,
        scripture_display=display,
    )
    result["scripture"] = display

    with connect() as con:
        con.execute(
            "INSERT INTO chat_history(role, content, reference, mode) VALUES (?, ?, ?, ?)",
            ("assistant", result.get("answer", ""), detected, payload.mode),
        )

    return result


@app.get("/api/chat/history")
def chat_history(limit: int = 50):
    limit = max(1, min(limit, 200))
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM chat_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


@app.post("/api/notes")
def create_note(payload: NoteCreate):
    with connect() as con:
        cur = con.execute(
            "INSERT INTO notes(reference, translation, note) VALUES (?, ?, ?)",
            (payload.reference, payload.translation, payload.note),
        )
        note_id = cur.lastrowid
    return {"id": note_id, **payload.model_dump()}


@app.get("/api/notes")
def notes(reference: str | None = None):
    with connect() as con:
        if reference:
            rows = con.execute(
                "SELECT * FROM notes WHERE reference=? ORDER BY id DESC",
                (reference,),
            ).fetchall()
        else:
            rows = con.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


@app.get("/api/settings/{key}")
def setting(key: str):
    return {"key": key, "value": get_setting(key)}


@app.put("/api/settings/{key}")
def update_setting(key: str, payload: SettingUpdate):
    set_setting(key, payload.value)
    return {"key": key, "value": payload.value}


@app.post("/api/memory")
def create_memory(payload: MemoryCreate):
    item_id = add_memory(payload.kind, payload.value, payload.reference)
    return {"id": item_id, **payload.model_dump()}


@app.get("/api/memory")
def memory(kind: str | None = None):
    return list_memory(kind)


@app.post("/api/memorization")
def memorize(payload: MemorizationCreate):
    item_id = add_memorization(payload.reference, payload.translation)
    return {"id": item_id, **payload.model_dump()}


@app.get("/api/memorization")
def memorization():
    return list_memorization()


@app.post("/api/memorization/{item_id}/review")
def review(item_id: int, payload: MemorizationReview):
    review_memorization(item_id, payload.correct)
    return {"id": item_id, "correct": payload.correct}


@app.post("/api/study-plans")
async def study_plan(payload: StudyPlanCreate):
    plan_id = create_study_plan(payload.title, payload.topic, payload.days)
    generated = None

    if payload.generate:
        prompt = (
            f"Create a {payload.days}-day Bible study plan on '{payload.topic}'. "
            "For each day provide a focus, 1-3 Scripture references, a short study goal, "
            "one reflection question, and one optional memorization verse. "
            "Do not invent verse wording; give references only."
        )
        generated = await study_ai.answer(prompt, mode="study_plan")
        with connect() as con:
            import json
            con.execute(
                "UPDATE study_plans SET content_json=? WHERE id=?",
                (json.dumps(generated, ensure_ascii=False), plan_id),
            )

    return {
        "id": plan_id,
        "title": payload.title,
        "topic": payload.topic,
        "days": payload.days,
        "generated": generated,
    }


@app.get("/api/study-plans")
def study_plans():
    return list_study_plans()


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/app.js")
def app_js():
    return FileResponse(FRONTEND / "app.js", media_type="application/javascript")


@app.get("/styles.css")
def styles():
    return FileResponse(FRONTEND / "styles.css", media_type="text/css")
