from backend.database import connect


def get_setting(key: str, default: str | None = None) -> str | None:
    with connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with connect() as con:
        con.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def add_memory(kind: str, value: str, reference: str | None = None) -> int:
    with connect() as con:
        cur = con.execute(
            "INSERT INTO study_memory(kind, value, reference) VALUES (?, ?, ?)",
            (kind, value, reference),
        )
        return int(cur.lastrowid)


def list_memory(kind: str | None = None) -> list[dict]:
    with connect() as con:
        if kind:
            rows = con.execute(
                "SELECT * FROM study_memory WHERE kind=? ORDER BY id DESC", (kind,)
            ).fetchall()
        else:
            rows = con.execute("SELECT * FROM study_memory ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def add_memorization(reference: str, translation: str) -> int:
    with connect() as con:
        con.execute(
            "INSERT OR IGNORE INTO memorization_verses(reference, translation) VALUES (?, ?)",
            (reference, translation),
        )
        row = con.execute(
            "SELECT id FROM memorization_verses WHERE reference=? AND translation=?",
            (reference, translation),
        ).fetchone()
        return int(row["id"])


def list_memorization() -> list[dict]:
    with connect() as con:
        rows = con.execute("SELECT * FROM memorization_verses ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def review_memorization(item_id: int, correct: bool) -> None:
    column = "correct_count" if correct else "incorrect_count"
    with connect() as con:
        con.execute(
            f"UPDATE memorization_verses SET {column}={column}+1, last_reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
            (item_id,),
        )


def create_study_plan(title: str, topic: str, days: int) -> int:
    with connect() as con:
        cur = con.execute(
            "INSERT INTO study_plans(title, topic, days) VALUES (?, ?, ?)",
            (title, topic, days),
        )
        return int(cur.lastrowid)


def list_study_plans() -> list[dict]:
    with connect() as con:
        rows = con.execute("SELECT * FROM study_plans ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]
