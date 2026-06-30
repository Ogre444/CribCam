"""OpenAI vision adapter (optional, paid)."""

import base64
import io
from PIL import Image
from .base import AIAdapter, AnswerResult


class OpenAIAdapter(AIAdapter):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "OpenAI"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult:
        from openai import OpenAI
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        client = OpenAI(api_key=self._api_key)
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
