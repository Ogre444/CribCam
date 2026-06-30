"""Groq free-tier vision adapter — supports up to 3 API keys with fallback."""

import base64
import io
from PIL import Image
from .base import AIAdapter, AnswerResult


class GroqAdapter(AIAdapter):
    def __init__(self, api_keys: list[str], model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        self._api_keys = [k for k in api_keys if k]
        self._model = model

    @property
    def name(self) -> str:
        return "Groq"

    def is_available(self) -> bool:
        return bool(self._api_keys)

    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult:
        from groq import Groq
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        last_exc: Exception = RuntimeError("no keys configured")
        for key in self._api_keys:
            try:
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    model=self._model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                            {"type": "text", "text": self.PROMPT},
                        ]
                    }],
                    max_tokens=200,
                )
                raw = resp.choices[0].message.content or ""
                return self._parse(raw, self.name, answer_chars)
            except Exception as e:
                last_exc = e
                continue
        raise last_exc
