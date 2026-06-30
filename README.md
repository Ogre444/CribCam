# CRIBCam

A camera-based AI answer assistant. It periodically analyzes the webcam image with a
vision model and shows the answer to a multiple-choice question in a floating popup.

> **Disclaimer:** CRIBCam is intended solely for informational and personal educational
> purposes. The user bears sole responsibility for any consequences of its use.

---

## One-step install

The installer downloads the program from this repository, installs the dependencies,
and launches it. The program is placed in `~/CribCam` (Windows: `%USERPROFILE%\CribCam`).

| Platform | Action |
|---|---|
| **macOS** | Download [`installer/macos.command`](installer/macos.command), then double-click. |
| **Windows** | Download [`installer/windows.bat`](installer/windows.bat), then double-click. |
| **Kali / Linux** | `bash installer/linux.sh` |

See [`installer/README.md`](installer/README.md) for details.

**Prerequisite:** `git` and **Python 3.10+** on the machine. (On Kali/Linux the
installer also offers to install the required `apt` packages.)

---

## Backends

The program supports multiple AI backends with an automatic fallback chain:
Gemini · Groq · Claude CLI · Ollama (local) · OpenAI.

Enter your API keys inside the program, under Settings — they are stored in
`~/.cribcam/config.json`, **never in this repository**.

> The **Claude CLI** backend uses the separately installed `claude` command (it is not
> bundled). The other backends work without it.

---

## Development

```bash
git clone https://github.com/Ogre444/CribCam.git
cd CribCam
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```
