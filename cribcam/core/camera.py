"""Camera capture via OpenCV."""

import cv2
import threading
from PIL import Image
from typing import Optional


class Camera:
    def __init__(self, index: int = 0):
        self._index = index
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(self._index)
        return self._cap.isOpened()

    def capture(self) -> Optional[Image.Image]:
        if not self._cap or not self._cap.isOpened():
            return None
        with self._lock:
            ret, frame = self._cap.read()
        if not ret:
            return None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def close(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    @staticmethod
    def list_cameras(max_check: int = 5) -> list[tuple[int, str]]:
        """Returns (index, label) pairs for available cameras."""
        available = []
        for i in range(max_check):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        names = Camera._get_camera_names(len(available))
        return [(idx, names[i] if i < len(names) else f"Camera {idx}")
                for i, idx in enumerate(available)]

    @staticmethod
    def _get_camera_names(count: int) -> list[str]:
        import sys
        import subprocess
        import re
        if sys.platform == "darwin":
            try:
                out = subprocess.check_output(
                    ["system_profiler", "SPCameraDataType"],
                    text=True, timeout=3, stderr=subprocess.DEVNULL,
                )
                names = re.findall(r"^    (.+):$", out, re.MULTILINE)
                if names:
                    return names
            except Exception:
                pass
        return [f"Camera {i}" for i in range(count)]
