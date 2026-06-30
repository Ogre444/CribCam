#!/bin/bash
#
# CRIBCam — macOS telepítő/indító
#
# Letölti a programot GitHubról (git clone), a következő futtatásoknál
# pedig frissíti (git pull), majd telepít és elindít.
# Telepítési hely: ~/CribCam
# Finderből dupla-kattintással is futtatható (.command kiterjesztés).
#
set -euo pipefail

REPO="https://github.com/Ogre444/CribCam.git"
TARGET="$HOME/CribCam"

echo "▶ CRIBCam — macOS telepítő"
echo "  cél: $TARGET"

# 1) git megléte
if ! command -v git >/dev/null 2>&1; then
    echo "✗ A git nincs telepítve. Telepítsd:  xcode-select --install"
    read -r -p "Nyomj Entert a kilépéshez..." _ || true
    exit 1
fi

# 2) letöltés (clone) vagy frissítés (pull)
if [ -d "$TARGET/.git" ]; then
    echo "  Frissítés a GitHubról (git pull)..."
    git -C "$TARGET" pull --ff-only || echo "  (a frissítés kihagyva, a meglévő verzió indul)"
else
    echo "  Letöltés a GitHubról (git clone)..."
    git clone --depth 1 "$REPO" "$TARGET"
fi
cd "$TARGET"

# 3) Python 3.10+ keresése
PYTHON=""
for cand in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$cand" >/dev/null 2>&1 \
       && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
        PYTHON="$cand"; break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "✗ Python 3.10+ kell: https://www.python.org/downloads/macos/"
    read -r -p "Nyomj Entert a kilépéshez..." _ || true
    exit 1
fi
echo "  Python: $("$PYTHON" --version)"

# 4) virtuális környezet
VENV="$TARGET/venv"
[ -d "$VENV" ] || { echo "  venv létrehozása..."; "$PYTHON" -m venv "$VENV"; }

# 5) Tkinter ellenőrzés
if ! "$VENV/bin/python" -c 'import tkinter' >/dev/null 2>&1; then
    echo "✗ A Tkinter hiányzik. Telepíts python.org-ról, vagy: brew install python-tk"
    read -r -p "Nyomj Entert a kilépéshez..." _ || true
    exit 1
fi

# 6) függőségek — csak ha a requirements.txt változott
REQ="$TARGET/requirements.txt"
STAMP="$VENV/.req-stamp"
if [ ! -f "$STAMP" ] || [ "$REQ" -nt "$STAMP" ]; then
    echo "  Függőségek telepítése/frissítése..."
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -r "$REQ"
    touch "$STAMP"
fi

# 7) indítás
echo "  Indítás..."
exec "$VENV/bin/python" "$TARGET/main.py"
