"""Application configuration — persisted as JSON."""

import json
import os
from dataclasses import dataclass, asdict, field


CONFIG_PATH = os.path.expanduser("~/.cribcam/config.json")

BACKENDS = ["gemini", "groq", "claude_cli", "ollama", "openai"]
POSITIONS = ["top_right", "top_left", "bottom_right", "bottom_left", "center"]


@dataclass
class Config:
    # Camera
    camera_index: int = 0
    interval: float = 5.0
    hash_threshold: int = 6   # dHash bit-difference to count as "changed" (2–14, step 2)

    # AI
    primary_backend: str = "gemini"
    gemini_api_keys: list = field(default_factory=lambda: ["", "", ""])
    gemini_model: str = "gemini-3.1-flash-lite"
    groq_api_keys: list = field(default_factory=lambda: ["", "", ""])
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    ollama_model: str = "llava"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Popup
    monitor: int = 1
    popup_position: str = "top_right"
    answer_chars: int = 30

    # UI
    language: str = "en"
    app_icon: str = ""   # filename inside logo/ dir; "" = use default

    def save(self) -> None:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "Config":
        if not os.path.exists(CONFIG_PATH):
            return cls()
        try:
            with open(CONFIG_PATH) as f:
                data = json.load(f)
            obj = cls()
            # migrate old single groq key
            if "groq_api_key" in data and "groq_api_keys" not in data:
                data["groq_api_keys"] = [data["groq_api_key"], "", ""]
            # migrate old single gemini key
            if "gemini_api_key" in data and "gemini_api_keys" not in data:
                data["gemini_api_keys"] = [data["gemini_api_key"], "", ""]
            for k, v in data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            # ensure always exactly 3 slots, strip whitespace
            for attr in ("gemini_api_keys", "groq_api_keys"):
                keys = getattr(obj, attr) or []
                setattr(obj, attr, [(k.strip() if isinstance(k, str) else "") for k in (keys + ["", "", ""])[:3]])
            return obj
        except Exception:
            return cls()
