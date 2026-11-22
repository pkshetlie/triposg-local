@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Lance d'abord installer.bat
  pause
  exit /b 1
)
set PYTHONIOENCODING=utf-8
echo Chargement du modele (1 a 4 min), le navigateur va s'ouvrir sur http://127.0.0.1:7860
echo Ferme cette fenetre pour arreter.
".venv\Scripts\python.exe" app.py
pause
