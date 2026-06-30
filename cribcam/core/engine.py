"""AI engine — builds fallback chain from config."""

import threading
import time
from PIL import Image
from typing import Callable, Optional
from .config import Config
from ..adapters.base import AIAdapter, AnswerResult
from ..adapters.groq_adapter import GroqAdapter
from ..adapters.gemini_adapter import GeminiAdapter
from ..adapters.claude_cli_adapter import ClaudeCLIAdapter
from ..adapters.ollama_adapter import OllamaAdapter
from ..adapters.openai_adapter import OpenAIAdapter

BACKEND_ORDER = ["gemini", "groq", "claude_cli", "ollama", "openai"]

_RESIZE_MAX = 768      # px on longest side before sending to API
_FORCE_INTERVAL = 60.0 # seconds — force re-analyze even if hash says "same"
_HASH_THRESHOLD = 8    # Hamming distance out of 64 bits to count as "changed"


class _ChangeDetector:
    """dHash-based image change detector, robust to minor camera noise.

    Uses a 9×8 difference hash (64 bits). Camera sensor noise and JPEG
    re-encoding typically cause < 3 bit flips; a real content change
    (new question on screen) causes 15–40 bit flips.

    Additionally forces a refresh every _FORCE_INTERVAL seconds as a
    safety net for long sessions (3–4 h) where slow drift could
    accumulate below the per-frame threshold.
    """

    def __init__(self) -> None:
        self._last_hash: Optional[list[int]] = None
        self._last_forced: float = 0.0
        self._lock = threading.Lock()

    def has_changed(self, image: Image.Image, threshold: int = _HASH_THRESHOLD) -> bool:
        now = time.monotonic()
        new_hash = self._dhash(image)  # computed outside lock (CPU work)

        with self._lock:
            force = (now - self._last_forced) >= _FORCE_INTERVAL

            if force or self._last_hash is None:
                self._last_hash = new_hash
                self._last_forced = now
                return True

            distance = sum(a != b for a, b in zip(new_hash, self._last_hash))
            if distance > threshold:
                self._last_hash = new_hash
                return True

            return False

    def reset(self) -> None:
        with self._lock:
            self._last_hash = None
            self._last_forced = 0.0

    @staticmethod
    def _dhash(image: Image.Image) -> list[int]:
        # Resize to 9×8 grayscale → compare adjacent pixels horizontally → 64 bits
        thumb = image.convert("L").resize((9, 8), Image.LANCZOS)
        pixels = list(thumb.getdata())
        return [
            1 if pixels[r * 9 + c] > pixels[r * 9 + c + 1] else 0
            for r in range(8)
            for c in range(8)
        ]


def _resize_for_api(image: Image.Image) -> Image.Image:
    """Resize so the longest side is at most _RESIZE_MAX px. No-op if already smaller."""
    w, h = image.size
    longest = max(w, h)
    if longest <= _RESIZE_MAX:
        return image
    scale = _RESIZE_MAX / longest
    return image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def _build_adapters(cfg: Config) -> dict[str, AIAdapter]:
    return {
        "groq":       GroqAdapter(cfg.groq_api_keys, cfg.groq_model),
        "gemini":     GeminiAdapter(cfg.gemini_api_keys, cfg.gemini_model),
        "claude_cli": ClaudeCLIAdapter(),
        "ollama":     OllamaAdapter(cfg.ollama_model),
        "openai":     OpenAIAdapter(cfg.openai_api_key, cfg.openai_model),
    }


class Engine:
    def __init__(
        self,
        cfg: Config,
        on_fallback: Optional[Callable[[str], None]] = None,
        on_trying: Optional[Callable[[str], None]] = None,
    ):
        self._cfg = cfg
        self._on_fallback = on_fallback
        self._on_trying = on_trying
        self._adapters = _build_adapters(cfg)
        self._change_detector = _ChangeDetector()
        self._last_result: Optional[AnswerResult] = None

    def reload(self, cfg: Config) -> None:
        self._cfg = cfg
        self._adapters = _build_adapters(cfg)
        self._change_detector.reset()
        self._last_result = None

    def _chain(self) -> list[AIAdapter]:
        primary = self._cfg.primary_backend
        order = [primary] + [k for k in BACKEND_ORDER if k != primary]
        return [self._adapters[k] for k in order if k in self._adapters]

    def analyze(
        self,
        image: Image.Image,
        force: bool = False,
    ) -> tuple[Optional[AnswerResult], str]:
        """Returns (result, error_message). On success error_message is empty.

        If the image hasn't changed since last call (and force=False),
        returns the cached result immediately without calling any backend.
        force=True bypasses the cache — use for manual captures.
        """
        changed = self._change_detector.has_changed(image, self._cfg.hash_threshold)

        if not changed and not force and self._last_result is not None:
            cached = AnswerResult(
                letter=self._last_result.letter,
                text=self._last_result.text,
                backend=self._last_result.backend,
                raw=self._last_result.raw,
                cached=True,
            )
            return cached, ""

        api_image = _resize_for_api(image)
        chain = self._chain()
        primary_name = chain[0].name if chain else "?"
        errors: list[str] = []

        for adapter in chain:
            if not adapter.is_available():
                errors.append(f"{adapter.name}: not configured")
                continue

            if self._on_trying:
                self._on_trying(adapter.name)

            try:
                result = adapter.analyze(api_image, self._cfg.answer_chars)
                if adapter.name != primary_name and self._on_fallback:
                    self._on_fallback(adapter.name)
                self._last_result = result
                return result, ""
            except Exception as e:
                short = str(e).split("\n")[0][:120]
                errors.append(f"{adapter.name}: {short}")
                continue

        return None, " | ".join(errors) or "no backends available"
