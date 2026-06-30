@echo off
setlocal enabledelayedexpansion
rem ============================================================
rem  CRIBCam - Windows telepito/indito
rem  Letolti a programot GitHubrol (git clone), a kovetkezo
rem  futtatasoknal frissiti (git pull), telepit es elindit.
rem  Telepitesi hely: %USERPROFILE%\CribCam
rem  Dupla-kattintassal futtathato.
rem ============================================================

set "REPO=https://github.com/Ogre444/CribCam.git"
set "TARGET=%USERPROFILE%\CribCam"

echo ^> CRIBCam - Windows telepito
echo   cel: %TARGET%

rem 1) git megléte
where git >nul 2>&1
if errorlevel 1 (
  echo [HIBA] A git nincs telepitve. Telepitsd: https://git-scm.com/download/win
  pause
  exit /b 1
)

rem 2) letoltes (clone) vagy frissites (pull)
if exist "%TARGET%\.git" (
  echo   Frissites a GitHubrol (git pull)...
  git -C "%TARGET%" pull --ff-only
) else (
  echo   Letoltes a GitHubrol (git clone)...
  git clone --depth 1 "%REPO%" "%TARGET%"
)
cd /d "%TARGET%"

rem 3) Python kereses
set "PYTHON="
where py >nul 2>&1 && set "PYTHON=py -3"
if not defined PYTHON ( where python >nul 2>&1 && set "PYTHON=python" )
if not defined PYTHON (
  echo [HIBA] Nem talalhato Python. Telepitsd: https://www.python.org/downloads/windows/
  echo        A telepiteskor pipald be az "Add python.exe to PATH" opciot.
  pause
  exit /b 1
)
for /f "tokens=*" %%V in ('%PYTHON% --version') do echo   Python: %%V

rem 4) virtualis kornyezet
set "VENV=%TARGET%\venv"
if not exist "%VENV%" (
  echo   venv letrehozasa...
  %PYTHON% -m venv "%VENV%"
)

rem 5) fuggosegek - csak ha a requirements.txt ujabb a stampnel
set "REQ=%TARGET%\requirements.txt"
set "STAMP=%VENV%\.req-stamp"
set "NEED=no"
for /f %%R in ('powershell -NoProfile -Command "if(!(Test-Path '%STAMP%') -or (Get-Item '%REQ%').LastWriteTime -gt (Get-Item '%STAMP%').LastWriteTime){'yes'}else{'no'}"') do set "NEED=%%R"
if "!NEED!"=="yes" (
  echo   Fuggosegek telepitese/frissitese...
  "%VENV%\Scripts\python.exe" -m pip install -q --upgrade pip
  "%VENV%\Scripts\pip.exe" install -q -r "%REQ%"
  echo stamp> "%STAMP%"
)

rem 6) inditas
echo   Inditas...
"%VENV%\Scripts\python.exe" "%TARGET%\main.py"
if errorlevel 1 pause
endlocal
