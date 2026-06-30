"""Anthropic API adapter — uses claude API key directly, no CLI sessions."""

import base64
import io
from PIL import Image
from .base import AIAdapter, AnswerResult


class ClaudeAPIAdapter(AIAdapter):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "Claude API"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult:
        import anthropic
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        client = anthropic.Anthropic(api_key=self._api_key)
        resp = client.messages.create(
            model=self._model,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": self.PROMPT},
                ],
            }],
        )
        raw = resp.content[0].text if resp.content else ""
        return self._parse(raw, self.name, answer_chars)
