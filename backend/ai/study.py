import json
from typing import Any

from backend.ai.ollama import OllamaClient
from backend.bible.references import parse_reference
from backend.bible.usfm import to_usfm
from backend.integrations.iqbible import IQBibleClient


SYSTEM_PROMPT = """You are Bible-AI, a serious Christian Bible-study assistant.
Rules:
1. Never invent or reconstruct Bible verses. Scripture text must come from supplied sources.
2. Clearly distinguish SCRIPTURE, HISTORICAL/BACKGROUND, COMMENTARY, and THEOLOGICAL INTERPRETATION.
3. When Christians dispute a doctrine, present major historic Christian interpretations fairly and say it is disputed.
4. Distinguish evidence, interpretation, and faith claims in apologetics.
5. Prefer the supplied source material. Do not claim a source says something absent from it.
6. Be concise but scholarly. Use references when supplied.
7. Original-language claims must be grounded in supplied Greek/Hebrew/lexicon data.
8. Never silently substitute one Bible translation for another.
"""

MODE_GUIDANCE = {
    "study": "Explain the passage in literary and historical context, then interpretation and application.",
    "theology": "Compare the major Christian interpretations fairly. Name traditions/views, their key biblical arguments, and major objections.",
    "apologetics": "Separate historical/evidential claims from philosophical interpretation and from faith commitments.",
    "history": "Focus on biblical/church historical context, primary-source chronology, councils, movements, and development of doctrine.",
    "language": "Focus on Hebrew/Greek forms, lemmas, Strong's, morphology, semantic range, and occurrences. Avoid etymological fallacies.",
    "study_plan": "Create a practical progressive study plan using references, goals, questions, and memorization prompts.",
    "quiz": "Create a fair study quiz. Do not invent verse wording. Include an answer key separately.",
    "book_summary": "Summarize structure, authorship/date debates where relevant, historical setting, themes, outline, and major passages.",
    "topic_study": "Build a canonical topic study using representative passages, context, interpretive cautions, and major theological views where disputed.",
}


class StudyAI:
    def __init__(self):
        self.ollama = OllamaClient()
        self.iq = IQBibleClient()

    async def build_context(self, reference: str | None) -> dict[str, Any]:
        context: dict[str, Any] = {}
        if reference and self.iq.configured:
            try:
                parsed = parse_reference(reference)
                compact = to_usfm(parsed.book, parsed.chapter, parsed.start_verse, parsed.end_verse)
                context["iq_bible"] = await self.iq.ai_context(compact)
            except Exception as exc:
                context["iq_bible_error"] = str(exc)
        return context

    async def answer(
        self,
        question: str,
        reference: str | None = None,
        mode: str = "study",
        scripture_display: dict | None = None,
    ) -> dict:
        context = await self.build_context(reference)
        available = await self.ollama.available()

        sources = []
        if "iq_bible" in context:
            sources.append({"name": "IQ Bible API", "type": "study_context"})
        if scripture_display:
            sources.append({
                "name": scripture_display.get("translation", {}).get("name", "Bible translation"),
                "type": "scripture_display",
                "provider": scripture_display.get("provider"),
            })

        if not available:
            return {
                "answer": "Ollama is not running. Scripture and study-source retrieval are available, but AI explanation requires the configured local Ollama model.",
                "mode": mode,
                "reference": reference,
                "sources": sources,
                "context": context,
                "ai_available": False,
            }

        payload = {
            "reference": reference,
            "mode": mode,
            "mode_guidance": MODE_GUIDANCE.get(mode, MODE_GUIDANCE["study"]),
            "study_context": context,
        }
        if scripture_display:
            # YouVersion text remains a separate display layer unless its applicable terms permit AI grounding.
            payload["scripture_display_metadata"] = {
                "reference": scripture_display.get("reference"),
                "translation": scripture_display.get("translation"),
                "provider": scripture_display.get("provider"),
            }

        user_prompt = (
            f"Question: {question}\n\n"
            f"Mode: {mode}\n"
            f"Mode guidance: {payload['mode_guidance']}\n"
            f"Reference: {reference or 'none explicitly detected'}\n\n"
            "SOURCE MATERIAL (JSON):\n"
            + json.dumps(payload, ensure_ascii=False)[:40000]
            + "\n\nAnswer with clear section labels where useful. Distinguish source facts from interpretation."
        )
        answer = await self.ollama.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ])
        return {
            "answer": answer,
            "mode": mode,
            "reference": reference,
            "sources": sources,
            "ai_available": True,
        }
