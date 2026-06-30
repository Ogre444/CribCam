"""Ollama local vision adapter."""

import base64
import io
import urllib.request
import json
from PIL import Image
from .base import AIAdapter, AnswerResult


class OllamaAdapter(AIAdapter):
    def __init__(self, model: str = "llava"):
        self._model = model
        self._endpoint = "http://localhost:11434"

    @property
    def name(self) -> str:
        return f"Ollama ({self._model})"

    def is_available(self) -> bool:
        try:
            urllib.request.urlopen(f"{self._endpoint}/api/tags", timeout=2)
            return True
        except Exception:
            return False

    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult:
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        payload = json.dumps({
            "model": self._model,
            "prompt": self.PROMPT,
            "images": [b64],
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            f"{self._endpoint}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        raw = data.get("response", "")
        return self._parse(raw, self.name, answer_chars)
