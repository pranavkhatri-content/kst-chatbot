@echo off
echo ============================================================
echo  KST Chatbot RAG - Setup and Start
echo ============================================================

cd /d "%~dp0"

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo [2/4] Installing dependencies...
pip install -r backend\requirements.txt --quiet

:: Run ingestion if chroma_db doesn't exist yet
if not exist "chroma_db" (
    echo [3/4] First run - embedding knowledge base into ChromaDB...
    cd backend
    python ingest.py
    cd ..
) else (
    echo [3/4] ChromaDB already exists, skipping ingestion.
    echo       Delete the chroma_db folder and re-run to re-embed.
)

:: Start server
echo [4/4] Starting KST RAG server on http://localhost:8000
echo       Open http://localhost:8000 in your browser.
echo       Press Ctrl+C to stop.
echo.
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
