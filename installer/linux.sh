#!/usr/bin/env bash
#
# CRIBCam — Linux / Kali telepítő/indító
#
# Letölti a programot GitHubról (git clone), a következő futtatásoknál
# frissíti (git pull), telepíti a függőségeket, majd elindít.
# Telepítési hely: ~/CribCam
# Futtatás:  bash linux.sh
#
set -euo pipefail

REPO="https://github.com/Ogre444/CribCam.git"
TARGET="$HOME/CribCam"

echo "▶ CRIBCam — Linux/Kali telepítő"
echo "  cél: $TARGET"

# 1) rendszercsomagok (Debian/Kali/Ubuntu)
if command -v apt-get >/dev/null 2>&1; then
    need=()
    command -v git >/dev/null 2>&1            || need+=(git)
    dpkg -s python3-venv  >/dev/null 2>&1      || need+=(python3-venv)
    dpkg -s python3-tk    >/dev/null 2>&1      || need+=(python3-tk)
    ldconfig -p 2>/dev/null | grep -q 'libGL\.so\.1'        || need+=(libgl1)
    ldconfig -p 2>/dev/null | grep -q 'libglib-2\.0\.so\.0' || need+=(libglib2.0-0)
    if [ ${#need[@]} -gt 0 ]; then
        echo "  Hiányzó rendszercsomagok telepítése: ${need[*]}"
        sudo apt-get update -qq
        sudo apt-get install -y "${need[@]}"
    fi
elif ! command -v git >/dev/null 2>&1; then
    echo "✗ A git nincs telepítve, és nem apt-alapú a rendszer. Telepítsd kézzel a git-et."
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
    echo "✗ Python 3.10+ nem található. Telepítsd: sudo apt install python3"
    exit 1
fi
echo "  Python: $("$PYTHON" --version)"

# 4) virtuális környezet
VENV="$TARGET/venv"
[ -d "$VENV" ] || { echo "  venv létrehozása..."; "$PYTHON" -m venv "$VENV"; }

# 5) függőségek — csak ha a requirements.txt változott
REQ="$TARGET/requirements.txt"
STAMP="$VENV/.req-stamp"
if [ ! -f "$STAMP" ] || [ "$REQ" -nt "$STAMP" ]; then
    echo "  Függőségek telepítése/frissítése..."
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -r "$REQ"
    touch "$STAMP"
fi

# 6) kamera-hozzáférés tipp
if ! id -nG 2>/dev/null | grep -qw video; then
    echo "  ⓘ Kamera tipp: sudo usermod -aG video \"$USER\"  (újbejelentkezés után lép életbe)"
fi

# 7) indítás
echo "  Indítás..."
exec "$VENV/bin/python" "$TARGET/main.py"
