# Changelog

## v1.3

- **Adjustable change-detection sensitivity** in Settings (2–14 bits, default 6),
  applied live without restarting the app.
- **Stability improvements for long (multi-hour) sessions:** thread-safe UI updates
  via a main-thread queue, a watchdog that restarts the scan thread if it dies, and
  automatic camera reconnect after repeated failed frames.
- **Cross-platform installers** (macOS / Windows / Kali) that fetch the program from
  GitHub and keep it up to date.
- Logo added to the README and the disclaimer window.
