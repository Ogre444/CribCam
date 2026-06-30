"""Main application window."""

import sys
import queue
import threading
import time
import tkinter as tk
import webbrowser
import customtkinter as ctk
from pathlib import Path
from PIL import Image
from typing import Optional

from ..core.config import Config
from ..core.camera import Camera
from ..core.engine import Engine
from ..core.i18n import t
from .settings_window import SettingsWindow
from .popup import AnswerPopup

_GITHUB_URL = "https://github.com/Ogre444/CribCam"
_APP_VERSION = "1.3"


def _find_logo() -> Optional[Path]:
    logo_dir = Path(__file__).parent.parent.parent / "logo"
    preferred = logo_dir / "nincshatter.png"
    if preferred.exists():
        return preferred
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        found = list(logo_dir.glob(ext))
        if found:
            return found[0]
    return None


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _monitor_geometry(monitor_index: int) -> str:
    try:
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors
            idx = max(1, min(monitor_index, len(monitors) - 1))
            m = monitors[idx]
            return f"{m['width']}x{m['height']}+{m['left']}+{m['top']}"
    except Exception:
        return "1920x1080+0+0"


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._cfg = Config.load()
        from ..core.i18n import load as i18n_load
        i18n_load(self._cfg.language)

        self.title(t("app_title"))
        self.resizable(False, False)
        self.geometry("360x520")

        self._camera = Camera(self._cfg.camera_index)
        self._camera.open()
        self._engine = Engine(self._cfg, on_fallback=self._on_fallback,
                              on_trying=self._on_trying)
        self._running = False
        self._closing = False
        self._scan_thread: Optional[threading.Thread] = None
        self._current_popup: Optional[AnswerPopup] = None
        self._ui_queue: "queue.Queue" = queue.Queue()
        self._failed_frames = 0

        self._build()
        self._update_preview_loop()
        self._poll_ui_queue()
        self._watchdog()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_icon(self._cfg.app_icon)
        self.attributes('-alpha', 0.0)
        self.after(30, lambda: self._fade_in(0.0))

    # ── Icon ──────────────────────────────────────────────────────────────────

    def _apply_icon(self, filename: str) -> None:
        logo_dir = Path(__file__).parent.parent.parent / "logo"
        if filename:
            path = logo_dir / filename
            if not path.exists():
                path = None
        else:
            preferred = logo_dir / "nincshatter.png"
            path = preferred if preferred.exists() else next(logo_dir.glob("*.png"), None)
        if path is None:
            return
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication, NSImage
                ns_img = NSImage.alloc().initWithContentsOfFile_(str(path))
                NSApplication.sharedApplication().setApplicationIconImage_(ns_img)
            except Exception:
                pass
        else:
            try:
                from PIL import ImageTk
                photo = ImageTk.PhotoImage(Image.open(path))
                self.iconphoto(True, photo)
                self._taskbar_icon = photo  # prevent GC
            except Exception:
                pass

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
        title_frame.columnconfigure(1, weight=1)

        logo_path = _find_logo()
        if logo_path:
            pil_logo = Image.open(logo_path)
            logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(56, 56))
            logo_lbl = ctk.CTkLabel(title_frame, image=logo_img, text="", cursor="hand2")
            logo_lbl.grid(row=0, column=0, padx=(0, 10), sticky="w")
            logo_lbl.bind("<Button-1>", lambda e: webbrowser.open(_GITHUB_URL))
            logo_lbl._image = logo_img

        info_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(info_frame, text=f"v{_APP_VERSION}",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="github.com/Ogre444/CribCam",
                     font=ctk.CTkFont(size=10), text_color="#636366").pack(anchor="w")

        ctk.CTkButton(title_frame, text="⚙", width=32, height=32,
                      fg_color="transparent", hover_color="#3A3A3C",
                      font=ctk.CTkFont(size=18),
                      command=self._open_settings).grid(row=0, column=2, sticky="e")

        preview_frame = ctk.CTkFrame(self, fg_color="#161616", corner_radius=10,
                                     border_width=1, border_color="#2C2C2E")
        preview_frame.grid(row=1, column=0, padx=16, pady=(10, 0))
        self._preview_label = ctk.CTkLabel(preview_frame, text="", width=324, height=182)
        self._preview_label.pack(padx=3, pady=3)

        status_frame = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=8)
        status_frame.grid(row=2, column=0, padx=16, pady=(8, 4), sticky="ew")
        self._status_var = tk.StringVar(value=t("status_idle"))
        ctk.CTkLabel(status_frame, textvariable=self._status_var,
                     font=ctk.CTkFont(size=12),
                     text_color="#8E8E93", wraplength=312).pack(pady=6)

        slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        slider_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 0))
        slider_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(slider_frame, text=t("settings_interval"),
                     font=ctk.CTkFont(size=12), text_color="#8E8E93").grid(
            row=0, column=0, sticky="w")
        self._interval_val_lbl = ctk.CTkLabel(
            slider_frame, text=f"{self._cfg.interval:.0f}s",
            font=ctk.CTkFont(size=12), text_color="#8E8E93", width=36)
        self._interval_val_lbl.grid(row=0, column=2, sticky="e")

        self._interval_slider = ctk.CTkSlider(
            slider_frame, from_=1, to=30, number_of_steps=29,
            command=self._on_interval_change)
        self._interval_slider.set(self._cfg.interval)
        self._interval_slider.grid(row=0, column=1, sticky="ew", padx=8)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=10)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self._start_btn = ctk.CTkButton(
            btn_frame, text=t("btn_start"),
            fg_color="#30D158", hover_color="#28B04A", text_color="#000000",
            height=36, corner_radius=8,
            command=self._toggle)
        self._start_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(
            btn_frame, text=t("btn_capture"),
            fg_color="#3A3A3C", hover_color="#48484A",
            height=36, corner_radius=8,
            command=self._manual_capture).grid(row=0, column=1, padx=(4, 0), sticky="ew")

        self._backend_var = tk.StringVar(value="")
        ctk.CTkLabel(self, textvariable=self._backend_var,
                     font=ctk.CTkFont(size=11), text_color="#48484A").grid(
            row=5, column=0, padx=16, pady=(0, 10))

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

    # ── Camera preview loop ───────────────────────────────────────────────────

    def _update_preview_loop(self):
        if self._closing:
            return
        try:
            frame = self._camera.capture()
            if frame:
                frame.thumbnail((328, 185))
                photo = ctk.CTkImage(light_image=frame, dark_image=frame, size=(328, 185))
                self._preview_label.configure(image=photo)
                self._preview_label._image = photo
        except Exception:
            pass
        self.after(100, self._update_preview_loop)

    # ── Thread-safe UI bridge ─────────────────────────────────────────────────

    def _post(self, fn) -> None:
        """Worker-szálból érkező UI-frissítés — a fő szál hajtja végre.

        A Tkinter nem szálbiztos: a worker csak sorba tesz, a fő szál fut.
        """
        self._ui_queue.put(fn)

    def _poll_ui_queue(self) -> None:
        if self._closing:
            return
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(50, self._poll_ui_queue)

    def _watchdog(self) -> None:
        """Ha a scan-szál futás közben elhalt, újraindítja (3-4 órás stabilitás)."""
        if self._closing:
            return
        if self._running and (self._scan_thread is None or not self._scan_thread.is_alive()):
            self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self._scan_thread.start()
        self.after(2000, self._watchdog)

    # ── Scan loop ─────────────────────────────────────────────────────────────

    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self._running = True
        self._start_btn.configure(
            text=t("btn_stop"), fg_color="#FF453A", hover_color="#CC3830")
        self._status_var.set(t("status_running", interval=int(self._cfg.interval)))
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()

    def _stop(self):
        self._running = False
        self._start_btn.configure(
            text=t("btn_start"), fg_color="#30D158", hover_color="#28B04A",
            text_color="#000000")
        self._status_var.set(t("status_idle"))

    def _scan_loop(self):
        while self._running:
            try:
                self._do_capture()
            except Exception as e:
                self._post(lambda e=e: self._status_var.set(
                    t("status_camera_error", error=str(e)[:50])))
            for _ in range(max(1, int(self._cfg.interval * 10))):
                if not self._running:
                    return
                time.sleep(0.1)

    def _manual_capture(self):
        def run():
            try:
                self._do_capture(True)
            except Exception as e:
                self._post(lambda e=e: self._status_var.set(
                    t("status_camera_error", error=str(e)[:50])))
        threading.Thread(target=run, daemon=True).start()

    def _do_capture(self, force: bool = False):
        self._post(lambda: self._status_var.set(t("status_analyzing")))
        frame = self._camera.capture()
        if frame is None:
            # kamera-elvesztés: pár sikertelen frame után újranyitjuk
            self._failed_frames += 1
            if self._failed_frames >= 3:
                self._camera.reopen()
                self._failed_frames = 0
            self._post(lambda: self._status_var.set(
                t("status_camera_error", error="no frame")))
            return
        self._failed_frames = 0
        result, err = self._engine.analyze(frame, force=force)
        if result is None:
            self._post(lambda e=err: self._status_var.set(
                f"{t('status_no_backend')} — {e}"))
            return
        if result.cached:
            status = (t("status_running", interval=int(self._cfg.interval))
                      if self._running else t("status_idle"))
            self._post(lambda s=status: self._status_var.set(s))
            return
        self._post(lambda r=result: self._show_result(r))

    def _show_result(self, result):
        status = (t("status_running", interval=int(self._cfg.interval))
                  if self._running else t("status_idle"))
        self._status_var.set(status)
        self._backend_var.set(f"↳ {result.backend}")

        if self._current_popup and self._current_popup.winfo_exists():
            self._current_popup.destroy()

        geom = _monitor_geometry(self._cfg.monitor)
        self._current_popup = AnswerPopup(result, geom, self._cfg.popup_position)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_trying(self, backend_name: str):
        self._post(lambda n=backend_name: self._status_var.set(f"⏳ {n}..."))

    def _on_fallback(self, backend_name: str):
        self._post(lambda: self._status_var.set(
            t("status_fallback", backend=backend_name)))

    def _on_interval_change(self, value: float):
        self._cfg.interval = round(value)
        self._interval_val_lbl.configure(text=f"{int(value)}s")

    def _open_settings(self):
        SettingsWindow(self, self._cfg, self._on_settings_saved)

    def _on_settings_saved(self, cfg: Config):
        lang_changed = cfg.language != self._cfg.language
        self._cfg = cfg
        if self._cfg.camera_index != self._camera._index:
            self._camera.close()
            self._camera = Camera(self._cfg.camera_index)
        self._engine.reload(cfg)
        self._apply_icon(cfg.app_icon)
        if lang_changed:
            self._rebuild()
        else:
            self._interval_slider.set(cfg.interval)
            self._interval_val_lbl.configure(text=f"{int(cfg.interval)}s")

    def _rebuild(self):
        was_running = self._running
        if was_running:
            self._stop()
        for widget in self.winfo_children():
            widget.destroy()
        self._build()
        self._update_preview_loop()
        if was_running:
            self._start()

    def _on_close(self):
        self._closing = True
        self._running = False
        self._camera.close()
        self._fade_out()
