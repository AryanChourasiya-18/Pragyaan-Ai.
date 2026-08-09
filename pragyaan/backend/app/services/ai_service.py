"""All LLM calls go through this module so the provider can be swapped in one place."""
import json
from typing import List

from openai import OpenAI

from app.config import settings
from app.services import vector_service

client = OpenAI(api_key=settings.openai_api_key)

SUMMARY_STYLE_PROMPTS = {
    "100_words": "Summarize the following text in exactly about 100 words.",
    "500_words": "Summarize the following text in about 500 words, covering all key points.",
    "bullet_points": "Summarize the following text as a concise, well-organized bulleted list.",
    "beginner": "Explain the following text in simple language for a beginner with no background.",
    "advanced": "Explain the following text at an advanced level, using precise technical terminology.",
    "eli10": "Explain the following text like I'm 10 years old, using a simple analogy.",
}


def _chat(system: str, user: str, temperature: float = 0.4) -> str:
    resp = client.chat.completions.create(
        model=settings.openai_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def summarize_text(full_text: str, style: str) -> str:
    instruction = SUMMARY_STYLE_PROMPTS.get(style, SUMMARY_STYLE_PROMPTS["bullet_points"])
    system = "You are a study assistant that writes accurate, exam-focused summaries strictly from the given text."
    # Truncate very long documents defensively; production should chunk + map-reduce.
    truncated = full_text[:24000]
    return _chat(system, f"{instruction}\n\nTEXT:\n{truncated}")


def answer_from_document(document_id: str, question: str):
    """RAG: retrieve relevant chunks, then answer strictly from them, citing pages."""
    hits = vector_service.query_similar(document_id, question, top_k=5)
    context = "\n\n".join(f"[Page {h['page']}]\n{h['text']}" for h in hits)

    system = (
        "You are a study assistant. Answer ONLY using the provided excerpts from the "
        "student's uploaded PDF. If the answer isn't in the excerpts, say you can't find "
        "it in this document. Always mention which page number(s) support your answer."
    )
    user = f"Excerpts:\n{context}\n\nQuestion: {question}"
    answer = _chat(system, user)

    sources = [{"page": h["page"], "snippet": h["text"][:180]} for h in hits]
    return answer, sources


def generate_quiz(full_text: str, question_types: List[str], difficulty: str,
                   exam_level: str, count: int) -> list:
    system = (
        "You are an exam question setter for Indian competitive exams (JEE/NEET) and "
        "school boards. Generate questions strictly from the given text. "
        "Return ONLY valid JSON, no markdown fences, no commentary."
    )
    exam_note = f" Target exam level: {exam_level}." if exam_level else ""
    user = f"""Generate {count} questions from this text.
Allowed types: {question_types}. Difficulty: {difficulty}.{exam_note}

Return a JSON array where each item has exactly:
{{
  "type": one of {question_types},
  "question_text": string,
  "options": array of 4 strings (only for mcq/true_false, else null),
  "correct_answer": string,
  "explanation": string,
  "source_page": integer or null
}}

TEXT:
{full_text[:20000]}
"""
    raw = _chat(system, user, temperature=0.6)
    return _safe_json_array(raw)


def generate_flashcards(full_text: str, count: int = 15) -> list:
    system = (
        "You create concise Anki-style flashcards from study material. "
        "Return ONLY a valid JSON array, no commentary."
    )
    user = f"""Create {count} flashcards from this text.
Each item: {{"front": "question or term", "back": "concise answer/definition"}}.

TEXT:
{full_text[:20000]}
"""
    raw = _chat(system, user, temperature=0.5)
    return _safe_json_array(raw)


def generate_notes(full_text: str, kind: str) -> str:
    prompts = {
        "revision": "Create structured revision notes with headings and sub-points.",
        "last_minute": "Create ultra-condensed last-minute revision notes — only the most exam-critical points.",
        "formula_sheet": "Extract every formula/equation mentioned, with a one-line meaning for each. Use markdown math notation where relevant.",
        "definitions": "List every important term and its precise definition, from this text.",
        "cheat_sheet": "Create a compact ethical study cheat sheet (for personal revision only, not for exam misuse): key facts, formulas, and definitions organized by sub-topic.",
    }
    instruction = prompts.get(kind, prompts["revision"])
    system = "You are a study assistant producing markdown study notes strictly from the given text."
    return _chat(system, f"{instruction}\n\nTEXT:\n{full_text[:22000]}")


def _safe_json_array(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1)
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # Best-effort recovery: find the first [ ... ] block.
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                return []
        return []
