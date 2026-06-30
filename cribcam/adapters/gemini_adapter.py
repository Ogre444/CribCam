"""Gemini free-tier vision adapter — supports up to 3 API keys with fallback."""

from PIL import Image
from .base import AIAdapter, AnswerResult


class GeminiAdapter(AIAdapter):
    def __init__(self, api_keys: list[str], model: str = "gemini-2.0-flash"):
        # Accept either a list or a single string for backwards compatibility
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        self._api_keys = [k for k in api_keys if k]
        self._model = model

    @property
    def name(self) -> str:
        return "Gemini"

    def is_available(self) -> bool:
        return bool(self._api_keys)

    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult:
        import google.genai as genai
        last_exc: Exception = RuntimeError("no keys configured")
        for key in self._api_keys:
            try:
                client = genai.Client(api_key=key)
                resp = client.models.generate_content(
                    model=self._model,
                    contents=[self.PROMPT, image],
                )
                raw = resp.text or ""
                return self._parse(raw, self.name, answer_chars)
            except Exception as e:
                last_exc = e
                continue
        raise last_exc
