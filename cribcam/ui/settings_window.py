"""Settings dialog."""

import customtkinter as ctk
from pathlib import Path
from ..core.config import Config, BACKENDS, POSITIONS
from ..core.camera import Camera
from ..core.i18n import t, load as i18n_load

def _list_monitors() -> list[tuple[int, str]]:
    try:
        import mss
        with mss.mss() as sct:
            result = []
            for i, m in enumerate(sct.monitors[1:], start=1):
                label = f"Monitor {i}  —  {m['width']}×{m['height']}"
                if m['left'] == 0 and m['top'] == 0:
                    label += "  (primary)"
                else:
                    label += f"  [+{m['left']}, +{m['top']}]"
                result.append((i, label))
            return result or [(1, "Monitor 1")]
    except Exception:
        return [(1, "Monitor 1")]


BACKEND_LABELS = {
    "groq": "Groq (free)",
    "gemini": "Gemini (free)",
    "claude_cli": "Claude CLI",
    "ollama": "Ollama (local)",
    "openai": "OpenAI",
}
CHAR_OPTIONS = ["10", "20", "30", "40", "50", "60", "80", "100", "0 (full)"]
LANG_OPTIONS = {"English": "en", "Magyar": "hu"}


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, cfg: Config, on_save):
        super().__init__(parent)
        self.title(t("settings_title"))
        self.resizable(False, False)
        self.grab_set()
        self._cfg = cfg
        self._on_save = on_save
        self._build()
        self.attributes('-alpha', 0.0)
        self.after(30, lambda: self._fade_in(0.0))

    def _section(self, parent, label: str, row: int):
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8E8E93").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 2))

    def _row(self, parent, label: str, row: int, widget):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13)) \
            .grid(row=row, column=0, sticky="w", padx=16, pady=4)
        widget.grid(row=row, column=1, sticky="ew", padx=16, pady=4)

    def _build(self):
        self.columnconfigure(0, weight=1)
        f = ctk.CTkScrollableFrame(self, width=420, height=480)
        f.pack(fill="both", expand=True, padx=0, pady=0)
        f.columnconfigure(1, weight=1)

        row = 0

        # ── Camera ───────────────────────────────────────
        self._section(f, t("settings_camera"), row); row += 1

        cams = Camera.list_cameras() or [(0, "Camera 0")]
        self._cam_index_map = {f"[{idx}] {name}": idx for idx, name in cams}
        cur_label = next(
            (lbl for lbl, idx in self._cam_index_map.items()
             if idx == self._cfg.camera_index),
            list(self._cam_index_map.keys())[0],
        )
        self._cam_var = ctk.StringVar(value=cur_label)
        self._row(f, t("settings_camera_index"), row,
                  ctk.CTkOptionMenu(f, variable=self._cam_var,
                                    values=list(self._cam_index_map.keys()))); row += 1

        # change-detection sensitivity (dHash bit threshold): 2–14, step 2
        sens_frame = ctk.CTkFrame(f, fg_color="transparent")
        sens_frame.columnconfigure(0, weight=1)
        self._sens_slider = ctk.CTkSlider(
            sens_frame, from_=2, to=14, number_of_steps=6,
            command=self._on_sens_change)
        self._sens_slider.set(self._cfg.hash_threshold)
        self._sens_slider.grid(row=0, column=0, sticky="ew")
        self._sens_val_lbl = ctk.CTkLabel(
            sens_frame, text=f"{int(self._cfg.hash_threshold)} bit",
            width=52, font=ctk.CTkFont(size=12), text_color="#8E8E93")
        self._sens_val_lbl.grid(row=0, column=1, padx=(8, 0))
        self._row(f, t("settings_sensitivity"), row, sens_frame); row += 1

        # ── AI Backend ───────────────────────────────────
        self._section(f, t("settings_ai"), row); row += 1

        backend_labels = [BACKEND_LABELS[b] for b in BACKENDS]
        current_label = BACKEND_LABELS.get(self._cfg.primary_backend, backend_labels[0])
        self._backend_var = ctk.StringVar(value=current_label)
        self._row(f, t("settings_primary"), row,
                  ctk.CTkOptionMenu(f, variable=self._backend_var, values=backend_labels)); row += 1

        groq_keys = (self._cfg.groq_api_keys or ["", "", ""])[:3]
        self._groq_keys = [ctk.StringVar(value=groq_keys[i]) for i in range(3)]
        for i in range(3):
            self._row(f, f"Groq API key {i+1}", row,
                      ctk.CTkEntry(f, textvariable=self._groq_keys[i], show="•")); row += 1

        keys = (self._cfg.gemini_api_keys or ["", "", ""])[:3]
        self._gemini_keys = [ctk.StringVar(value=keys[i]) for i in range(3)]
        for i in range(3):
            self._row(f, f"Gemini API key {i+1}", row,
                      ctk.CTkEntry(f, textvariable=self._gemini_keys[i], show="•")); row += 1

        self._ollama_model = ctk.StringVar(value=self._cfg.ollama_model)
        ollama_frame = ctk.CTkFrame(f, fg_color="transparent")
        ctk.CTkEntry(ollama_frame, textvariable=self._ollama_model).pack(
            side="left", fill="x", expand=True)
        self._ollama_info_btn = ctk.CTkButton(
            ollama_frame, text="ⓘ", width=28, height=28,
            fg_color="transparent", hover_color="#3A3A3C",
            font=ctk.CTkFont(size=15), text_color="#636366",
            corner_radius=6, command=self._toggle_ollama_info,
        )
        self._ollama_info_btn.pack(side="left", padx=(4, 0))
        self._row(f, t("settings_ollama_model"), row, ollama_frame); row += 1

        self._openai_key = ctk.StringVar(value=self._cfg.openai_api_key)
        self._row(f, "OpenAI API key (opt.)", row,
                  ctk.CTkEntry(f, textvariable=self._openai_key, show="•")); row += 1

        # ── Popup ────────────────────────────────────────
        self._section(f, t("settings_popup"), row); row += 1

        monitors = _list_monitors()
        self._monitor_map = {label: idx for idx, label in monitors}
        cur_mon_label = next(
            (label for idx, label in monitors if idx == self._cfg.monitor),
            monitors[0][1],
        )
        self._monitor_var = ctk.StringVar(value=cur_mon_label)
        self._row(f, t("settings_monitor"), row,
                  ctk.CTkOptionMenu(f, variable=self._monitor_var,
                                    values=[label for _, label in monitors])); row += 1

        pos_labels = [t(f"pos_{p}") for p in POSITIONS]
        pos_map = {t(f"pos_{p}"): p for p in POSITIONS}
        cur_pos = t(f"pos_{self._cfg.popup_position}")
        self._pos_var = ctk.StringVar(value=cur_pos)
        self._pos_map = pos_map
        self._row(f, t("settings_position"), row,
                  ctk.CTkOptionMenu(f, variable=self._pos_var, values=pos_labels)); row += 1

        cur_chars = "0 (full)" if self._cfg.answer_chars == 0 else str(self._cfg.answer_chars)
        self._chars_var = ctk.StringVar(value=cur_chars)
        self._row(f, t("settings_answer_chars"), row,
                  ctk.CTkOptionMenu(f, variable=self._chars_var, values=CHAR_OPTIONS)); row += 1

        # ── Appearance ───────────────────────────────────
        self._section(f, t("settings_appearance"), row); row += 1

        logo_dir = Path(__file__).parent.parent.parent / "logo"
        icons = sorted(p.name for p in logo_dir.glob("*.png")) if logo_dir.exists() else []
        self._icon_map = {Path(ic).stem: ic for ic in icons}
        icon_labels = list(self._icon_map.keys())
        cur_icon_label = (
            Path(self._cfg.app_icon).stem
            if self._cfg.app_icon and self._cfg.app_icon in icons
            else (icon_labels[0] if icon_labels else "")
        )
        self._icon_var = ctk.StringVar(value=cur_icon_label)
        if icon_labels:
            self._row(f, t("settings_app_icon"), row,
                      ctk.CTkOptionMenu(f, variable=self._icon_var,
                                        values=icon_labels)); row += 1

        # ── Language ─────────────────────────────────────
        self._section(f, t("settings_language"), row); row += 1
        lang_rev = {v: k for k, v in LANG_OPTIONS.items()}
        self._lang_var = ctk.StringVar(value=lang_rev.get(self._cfg.language, "English"))
        self._row(f, t("settings_language"), row,
                  ctk.CTkOptionMenu(f, variable=self._lang_var,
                                    values=list(LANG_OPTIONS.keys()))); row += 1

        # ── Buttons ──────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(btn_frame, text=t("settings_cancel"),
                      fg_color="#3A3A3C", hover_color="#48484A",
                      command=self._fade_out).pack(side="left", expand=True, padx=4)
        ctk.CTkButton(btn_frame, text=t("settings_save"),
                      command=self._save).pack(side="right", expand=True, padx=4)

    # ── Sensitivity slider ────────────────────────────────────────────────────

    def _on_sens_change(self, value: float):
        self._sens_val_lbl.configure(text=f"{int(round(value))} bit")

    # ── Ollama info popup ─────────────────────────────────────────────────────

    def _toggle_ollama_info(self):
        if hasattr(self, '_ollama_info_win') and self._ollama_info_win.winfo_exists():
            self._info_fade_out(self._ollama_info_win)
            return
        win = ctk.CTkToplevel(self)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        frame = ctk.CTkFrame(win, fg_color="#2C2C2E", corner_radius=10,
                              border_width=1, border_color="#48484A")
        frame.pack(padx=1, pady=1)
        ctk.CTkLabel(frame,
            text="Ollama  •  localhost:11434",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
        ).pack(padx=14, pady=(10, 2), anchor="w")
        ctk.CTkLabel(frame,
            text=t("settings_ollama_info"),
            font=ctk.CTkFont(size=11),
            text_color="#AEAEB2",
            justify="left",
        ).pack(padx=14, pady=(2, 12), anchor="w")
        win.update_idletasks()
        btn = self._ollama_info_btn
        x = btn.winfo_rootx() + btn.winfo_width() - win.winfo_width()
        y = btn.winfo_rooty() + btn.winfo_height() + 6
        win.geometry(f"+{x}+{y}")
        win.lift()
        self._ollama_info_win = win
        win.attributes('-alpha', 0.0)
        self._info_fade_in(win, 0.0)

    def _info_fade_in(self, win: ctk.CTkToplevel, alpha: float) -> None:
        if not win.winfo_exists():
            return
        alpha = min(1.0, alpha + 0.06)
        win.attributes('-alpha', alpha)
        if alpha < 1.0:
            self.after(10, lambda: self._info_fade_in(win, alpha))

    def _info_fade_out(self, win: ctk.CTkToplevel, alpha: float = 1.0) -> None:
        if not win.winfo_exists():
            return
        alpha = max(0.0, alpha - 0.12)
        win.attributes('-alpha', alpha)
        if alpha > 0:
            self.after(10, lambda: self._info_fade_out(win, alpha))
        else:
            win.destroy()

    # ── Fade animations ───────────────────────────────────────────────────────

    def _fade_in(self, alpha: float) -> None:
        alpha = min(1.0, alpha + 0.04)
        self.attributes('-alpha', alpha)
        if alpha < 1.0:
            self.after(10, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha: float = 1.0) -> None:
        alpha = max(0.0, alpha - 0.18)
        self.attributes('-alpha', alpha)
        if alpha > 0:
            self.after(10, lambda: self._fade_out(alpha))
        else:
            self.destroy()

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        cfg = self._cfg
        cfg.camera_index = self._cam_index_map.get(self._cam_var.get(), 0)
        cfg.hash_threshold = int(round(self._sens_slider.get()))
        label_to_key = {v: k for k, v in BACKEND_LABELS.items()}
        cfg.primary_backend = label_to_key.get(self._backend_var.get(), "groq")
        cfg.groq_api_keys = [v.get().strip() for v in self._groq_keys]
        cfg.gemini_api_keys = [v.get().strip() for v in self._gemini_keys]
        cfg.ollama_model = self._ollama_model.get()
        cfg.openai_api_key = self._openai_key.get()
        cfg.monitor = self._monitor_map.get(self._monitor_var.get(), 1)
        cfg.popup_position = self._pos_map.get(self._pos_var.get(), "top_right")
        chars_raw = self._chars_var.get().split()[0]
        cfg.answer_chars = int(chars_raw)
        cfg.app_icon = self._icon_map.get(self._icon_var.get(), "")
        cfg.language = LANG_OPTIONS.get(self._lang_var.get(), "en")
        i18n_load(cfg.language)
        cfg.save()
        self._on_save(cfg)
        self._fade_out()
