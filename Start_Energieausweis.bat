@echo off
echo ==========================================
echo Starte Streamlit-App mit DB-Prüfung
echo ==========================================

REM Projekt-Root setzen
cd /d E:\Projekte\Programmierung\Energieausweis\Energieausweis-App

REM -----------------------------
REM 1️⃣ Prüfen, ob PostgreSQL läuft
REM -----------------------------
sc query postgresql-x64-18 | findstr /C:"RUNNING" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL läuft nicht. Starte den Dienst...
    net start postgresql-x64-18
    IF %ERRORLEVEL% NEQ 0 (
        echo Fehler: Konnte PostgreSQL nicht starten!
        pause
        exit /b
    )
    echo ✅ PostgreSQL wurde gestartet.
) ELSE (
    echo ✅ PostgreSQL läuft bereits.
)

REM -----------------------------
REM 2️⃣ Virtuelle Umgebung aktivieren
REM -----------------------------
call venv\Scripts\Activate
IF %ERRORLEVEL% NEQ 0 (
    echo Fehler: Konnte venv nicht aktivieren.
    pause
    exit /b
)
echo ✅ venv wurde aktiviert.

REM -----------------------------
REM 3️⃣ Prüfen, ob psycopg2 installiert ist
REM -----------------------------
python -c "import psycopg2" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo psycopg2 nicht gefunden. Installiere psycopg2-binary...
    @REM pip install psycopg2-binary
    IF %ERRORLEVEL% NEQ 0 (
        echo Fehler: Konnte psycopg2-binary nicht installieren!
        pause
        exit /b
    )
    echo ✅ psycopg2-binary erfolgreich installiert.
) ELSE (
    echo ✅ psycopg2 ist bereits installiert.
)

REM -----------------------------
REM 4️⃣ In src wechseln und Streamlit starten
REM -----------------------------
cd src
python -m streamlit run .\app.py --server.port 8501 --server.headless true

pause
