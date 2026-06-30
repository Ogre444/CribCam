"""Abstract AI adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from PIL import Image


@dataclass
class AnswerResult:
    letter: str          # "A", "B", "C", "D", or "" if not MCQ
    text: str            # answer text or full response
    backend: str         # which backend produced this
    raw: str             # full raw response
    cached: bool = False # True if returned from cache (image unchanged)


class AIAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult: ...

    PROMPT = (
        "You are looking at an exam or quiz question with answer choices.\n"
        "\n"
        "Your ONLY job: decide which single answer is correct and output it.\n"
        "\n"
        "STRICT RULES:\n"
        "- Pick EXACTLY ONE answer. Never list multiple options.\n"
        "- Use the label EXACTLY as it appears in the image (e.g. A/B/C/D or 1/2/3/4 or a)/b)/c)/d)).\n"
        "- Do NOT explain your reasoning. Do NOT repeat the question. Do NOT list the choices.\n"
        "- Do NOT think out loud. Output only the two lines below.\n"
        "\n"
        "OUTPUT FORMAT (exactly two lines, nothing else):\n"
        "LETTER: <the label from the image>\n"
        "ANSWER: <the answer text>\n"
        "\n"
        "If there are no answer choices (open question), output:\n"
        "LETTER: -\n"
        "ANSWER: <your answer, max 1 sentence>\n"
    )

    def _parse(self, raw: str, backend: str, answer_chars: int) -> AnswerResult:
        letter = ""
        text = ""
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith("LETTER:"):
                letter = line.split(":", 1)[1].strip()
                # normalise common label formats: "A)", "A.", "1)", "1." → "A" / "1"
                letter = letter.rstrip(").:").strip().upper()
            elif upper.startswith("ANSWER:"):
                text = line.split(":", 1)[1].strip()
        # fallback: if model ignored format, use entire raw as answer text
        if not letter and not text:
            text = raw.strip()
        if answer_chars > 0 and len(text) > answer_chars:
            text = text[:answer_chars] + "…"
        return AnswerResult(letter=letter, text=text, backend=backend, raw=raw)
