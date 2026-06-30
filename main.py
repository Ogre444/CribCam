#!/usr/bin/env python3
"""CRIBCam — camera-based AI answer assistant."""

import sys
from pathlib import Path


def _set_dock_icon() -> None:
    """macOS: replaces the Python dock icon with the CribCam logo."""
    if sys.platform != "darwin":
        return
    logo = Path(__file__).parent / "logo" / "nincshatter.png"
    if not logo.exists():
        found = list((Path(__file__).parent / "logo").glob("*.png"))
        if not found:
            return
        logo = found[0]
    try:
        from AppKit import NSApplication, NSImage
        ns_image = NSImage.alloc().initWithContentsOfFile_(str(logo))
        NSApplication.sharedApplication().setApplicationIconImage_(ns_image)
    except Exception:
        pass


if __name__ == "__main__":
    from cribcam.ui.disclaimer import DisclaimerWindow
    from cribcam.ui.main_window import MainWindow

    disclaimer = DisclaimerWindow()
    _set_dock_icon()  # NSApp már inicializálva van az első CTk ablak után
    disclaimer.mainloop()

    if disclaimer.accepted:
        app = MainWindow()
        app.mainloop()
