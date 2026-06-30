"""Claude Code CLI adapter — uses Max subscription, no API key needed."""

import base64
import io
import subprocess
import shutil
import os
from PIL import Image
from .base import AIAdapter, AnswerResult


class ClaudeCLIAdapter(AIAdapter):
    @property
    def name(self) -> str:
        return "Claude CLI"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    def analyze(self, image: Image.Image, answer_chars: int = 30) -> AnswerResult:
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        # embed image as data-URI so no file I/O or Read tool is needed
        prompt = (
            f"![image](data:image/jpeg;base64,{b64})\n\n{self.PROMPT}"
        )
        env = {**os.environ, "GRPC_VERBOSITY": "NONE", "GLOG_minloglevel": "3"}
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "none", "--output-format", "text"],
            capture_output=True, text=True, timeout=45,
            close_fds=True, env=env,
        )
        raw = result.stdout.strip()
        if not raw:
            stderr_short = result.stderr.strip().split("\n")[-1][:200]
            raise RuntimeError(stderr_short or "empty response")
        return self._parse(raw, self.name, answer_chars)
