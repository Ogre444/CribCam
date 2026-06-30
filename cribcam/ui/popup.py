"""Floating answer popup — always on top, draggable, monitor-aware."""

import tkinter as tk
import customtkinter as ctk
from typing import Optional
from ..adapters.base import AnswerResult
from ..core.i18n import t

POSITIONS = {
    "top_right":    lambda mw, mh, pw, ph: (mw - pw - 20, 20),
    "top_left":     lambda mw, mh, pw, ph: (20, 20),
    "bottom_right": lambda mw, mh, pw, ph: (mw - pw - 20, mh - ph - 40),
    "bottom_left":  lambda mw, mh, pw, ph: (20, mh - ph - 40),
    "center":       lambda mw, mh, pw, ph: ((mw - pw) // 2, (mh - ph) // 2),
}


class AnswerPopup(ctk.CTkToplevel):
    def __init__(self, result: AnswerResult, monitor_geom: str, position: str):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)

        self._drag_x = 0
        self._drag_y = 0

        # Layout
        self.configure(fg_color="#1C1C1E")
        frame = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14,
                             border_width=1, border_color="#3A3A3C")
        frame.pack(padx=0, pady=0)

        close_btn = ctk.CTkButton(
            frame, text="×", width=24, height=24,
            fg_color="transparent", hover_color="#3A3A3C",
            text_color="#8E8E93", font=ctk.CTkFont(size=16),
            command=self.destroy
        )
        close_btn.grid(row=0, column=1, sticky="ne", padx=(4, 6), pady=(6, 0))

        if result.letter and result.letter != "-":
            letter_lbl = ctk.CTkLabel(
                frame,
                text=t("popup_answer", letter=result.letter),
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color="#30D158",
            )
            letter_lbl.grid(row=0, column=0, sticky="w", padx=(14, 4), pady=(10, 2))

        if result.text:
            text_lbl = ctk.CTkLabel(
                frame,
                text=result.text,
                font=ctk.CTkFont(size=13),
                text_color="#E5E5EA",
                wraplength=280,
                justify="left",
            )
            text_lbl.grid(row=1, column=0, columnspan=2, sticky="w",
                          padx=14, pady=(0, 4))

        backend_lbl = ctk.CTkLabel(
            frame,
            text=t("popup_backend", backend=result.backend),
            font=ctk.CTkFont(size=10),
            text_color="#636366",
        )
        backend_lbl.grid(row=2, column=0, columnspan=2, sticky="w",
                         padx=14, pady=(0, 8))

        self.update_idletasks()
        pw, ph = self.winfo_width(), self.winfo_height()

        # Parse monitor geometry  "WxH+X+Y"
        try:
            size, ox, oy = monitor_geom.split("+", 2)
            mw, mh = map(int, size.split("x"))
            ox, oy = int(ox), int(oy)
        except Exception:
            mw, mh, ox, oy = 1920, 1080, 0, 0

        fn = POSITIONS.get(position, POSITIONS["top_right"])
        rx, ry = fn(mw, mh, pw, ph)
        self.geometry(f"+{ox + rx}+{oy + ry}")

        # Draggable
        frame.bind("<ButtonPress-1>", self._drag_start)
        frame.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")
