@echo off
echo ==========================================
echo Starte Streamlit-App mit virtuellem Environment
echo ==========================================

REM Projekt-Root setzen
cd /d E:\Projekte\Programmierung\Energieausweis\Energieausweis-App

REM venv aktivieren
call venv\Scripts\Activate

IF %ERRORLEVEL% NEQ 0 (
    echo Fehler: Konnte venv nicht aktivieren.
    pause
    exit /b
)

echo venv wurde aktiviert.

REM in src wechseln (falls dein app.py dort liegt)
cd src

REM Streamlit starten
python -m streamlit run .\app.py

pause
