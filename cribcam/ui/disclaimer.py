"""Disclaimer window — shown before the main program launches."""

import sys
import webbrowser
import customtkinter as ctk
from pathlib import Path
from PIL import Image

_RICK = "https://youtu.be/dQw4w9WgXcQ?list=RDdQw4w9WgXcQ"

_TEXT = {
    "en": {
        "window_title": "Disclaimer",
        "heading":      "⚠  Disclaimer",
        "body": (
            "CRIBCam is intended solely for informational and personal educational purposes.\n\n"
            "By using this software, the user fully accepts that they bear sole responsibility "
            "for all consequences arising from its use — including, but not limited to, "
            "violations of institutional policies, disciplinary proceedings, or any other "
            "legal consequences.\n\n"
            "The developers accept no liability for any direct or indirect damage, consequence, "
            "or adverse legal outcome resulting from the use of this software.\n\n"
            "Use of this software is entirely at your own risk."
        ),
        "agree":    "✓  I Agree",
        "disagree": "✕  I Disagree",
    },
    "hu": {
        "window_title": "Felelősségi nyilatkozat",
        "heading":      "⚠  Felelősségi nyilatkozat",
        "body": (
            "A CRIBCam szoftver kizárólag tájékoztató és személyes oktatási célokra készült.\n\n"
            "A program használatával a felhasználó teljes mértékben elfogadja, hogy a szoftver "
            "alkalmazásából eredő minden következményért — beleértve, de nem kizárólagosan az "
            "intézményi szabályzatok megsértését, fegyelmi eljárásokat vagy bármilyen egyéb "
            "jogkövetkezményt — kizárólag a felhasználó tartozik felelősséggel.\n\n"
            "A fejlesztők nem vállalnak felelősséget a program közvetlen vagy közvetett "
            "használatából eredő semmilyen kárért, következményért vagy hátrányos jogkövetkezményért.\n\n"
            "A szoftver használata saját felelősségre történik."
        ),
        "agree":    "✓  Egyetértek",
        "disagree": "✕  Nem értek egyet",
    },
}


class DisclaimerWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.accepted = False
        self._lang = "en"

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.resizable(False, False)
        self._build()

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        self.protocol("WM_DELETE_WINDOW", self._disagree)
        self.attributes('-alpha', 0.0)
        self.after(30, lambda: self._fade_in(0.0))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        s = _TEXT[self._lang]
        self.title(s["window_title"])
        self.columnconfigure(0, weight=1)

        # CribCam logó az ablak tetején
        logo_path = Path(__file__).parent.parent.parent / "logo" / "nincshatter.png"
        if logo_path.exists():
            pil = Image.open(logo_path)
            self._logo_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(120, 120))
            ctk.CTkLabel(self, image=self._logo_img, text="").grid(
                row=0, column=0, pady=(16, 4))

        header = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=0)
        header.grid(row=1, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=s["heading"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF9F0A",
        ).grid(row=0, column=0, pady=16, padx=20, sticky="w")

        lang_btn = ctk.CTkSegmentedButton(
            header,
            values=["EN", "HU"],
            command=self._switch_lang,
            width=76,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lang_btn.set("EN" if self._lang == "en" else "HU")
        lang_btn.grid(row=0, column=1, padx=(0, 14), pady=16)

        text_frame = ctk.CTkFrame(self, fg_color="#161616", corner_radius=10,
                                  border_width=1, border_color="#2C2C2E")
        text_frame.grid(row=2, column=0, padx=16, pady=12, sticky="ew")

        ctk.CTkLabel(
            text_frame,
            text=s["body"],
            font=ctk.CTkFont(size=12),
            text_color="#AEAEB2",
            wraplength=360,
            justify="left",
        ).pack(padx=16, pady=14)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame,
            text=s["agree"],
            fg_color="#30D158", hover_color="#28B04A", text_color="#000000",
            height=38, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._agree,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text=s["disagree"],
            fg_color="#3A3A3C", hover_color="#FF453A", text_color="#AEAEB2",
            height=38, corner_radius=8,
            font=ctk.CTkFont(size=13),
            command=self._disagree,
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _switch_lang(self, value: str):
        self._lang = "en" if value == "EN" else "hu"
        for widget in self.winfo_children():
            widget.destroy()
        self._build()

    # ── Fade animations ───────────────────────────────────────────────────────

    def _fade_in(self, alpha: float) -> None:
        alpha = min(1.0, alpha + 0.04)
        self.attributes('-alpha', alpha)
        if alpha < 1.0:
            self.after(10, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha: float = 1.0, on_complete=None) -> None:
        alpha = max(0.0, alpha - 0.18)
        self.attributes('-alpha', alpha)
        if alpha > 0:
            self.after(10, lambda: self._fade_out(alpha, on_complete))
        else:
            self.destroy()
            if on_complete:
                on_complete()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _agree(self):
        self.accepted = True
        self._fade_out()

    def _disagree(self):
        webbrowser.open(_RICK)
        self._fade_out(on_complete=lambda: sys.exit(0))
