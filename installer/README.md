# CRIBCam — Installation

One **self-contained installer script** per platform. Each downloads the program from
GitHub (`git clone`), updates it on subsequent runs (`git pull`), installs the
dependencies, and launches it. Install location: `~/CribCam`
(Windows: `%USERPROFILE%\CribCam`).

> The scripts are self-sufficient — no need to clone manually first. They keep working
> as the program evolves (they operate from `requirements.txt` and `main.py`).

---

## Prerequisite
- **git** and **Python 3.10+** installed.
  - macOS: `git` via `xcode-select --install`; Python from [python.org](https://www.python.org/downloads/macos/).
  - Windows: [git-scm.com](https://git-scm.com/download/win), [python.org](https://www.python.org/downloads/windows/) (check "Add to PATH").
  - Kali/Linux: the script offers to install the `apt` packages (`git`, `python3-venv`, `python3-tk`, `libgl1`, `libglib2.0-0`).

## Launch

| Platform | Action |
|---|---|
| **macOS** | Double-click `macos.command`. |
| **Windows** | Double-click `windows.bat`. |
| **Kali / Linux** | `bash linux.sh` |

The first run downloads and installs the program (takes a bit longer). Later runs
update if a new version exists, then start instantly.

## What the script does
1. Checks for `git` (and system packages on Kali/Linux).
2. `git clone` (first time) or `git pull` (update) into `~/CribCam`.
3. Finds Python 3.10+, creates the `venv`.
4. Installs/updates dependencies — **only when `requirements.txt` changed**.
5. Starts `main.py`.

## Notes
- **Claude CLI backend:** not bundled — the `claude` command must be installed
  separately and on your `PATH`. The other backends work without it.
- **Camera permission:** prompted by macOS on first run. On Kali/Linux, if the camera
  won't start: `sudo usermod -aG video "$USER"`, then log back in.
- Settings are stored in `~/.cribcam/config.json` (not in the program folder).
