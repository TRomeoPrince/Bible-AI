from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.bible.registry import list_translations, local_provider
from backend.database import connect, init_db
from backend.integrations.iqbible import IQBibleClient
from backend.integrations.youversion import YouVersionClient


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

app = FastAPI(title="Bible-AI", version="0.1.0")


class NoteCreate(BaseModel):
    reference: str
    note: str
    translation: str | None = None


@app.on_event("startup")
def startup() -> None:
    init_db()
    local_provider.reload()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Bible-AI", "version": "0.1.0"}


@app.get("/api/providers")
def providers():
    youversion = YouVersionClient()
    iqbible = IQBibleClient()
    return {
        "youversion": {
            "configured": youversion.configured,
            "purpose": "Licensed Scripture retrieval/display"
        },
        "iqbible": {
            "configured": iqbible.configured,
            "purpose": "Original-language, Strong's, lexicon and study enrichment"
        },
        "local_scripture": {
            "configured": True,
            "installed_translations": [t.code for t in local_provider.translations()]
        }
    }


@app.get("/api/translations")
def translations():
    return [item.model_dump() for item in list_translations()]


@app.get("/api/passage")
def passage(reference: str, translation: str = "WEB"):
    try:
        return local_provider.get_passage(translation, reference).model_dump()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/compare")
def compare(reference: str, translations: str = "WEB,KJV"):
    output = []
    for code in [part.strip().upper() for part in translations.split(",") if part.strip()]:
        try:
            output.append({
                "translation": code,
                "status": "ok",
                "result": local_provider.get_passage(code, reference).model_dump(),
            })
        except (KeyError, ValueError) as exc:
            output.append({"translation": code, "status": "unavailable", "error": str(exc)})
    return {"reference": reference, "comparisons": output}


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


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/app.js")
def app_js():
    return FileResponse(FRONTEND / "app.js", media_type="application/javascript")


@app.get("/styles.css")
def styles():
    return FileResponse(FRONTEND / "styles.css", media_type="text/css")
