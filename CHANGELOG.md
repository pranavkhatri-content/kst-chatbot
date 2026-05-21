# Changelog

All notable changes to KST Chatbot are documented here.

---

## [1.1.0] - 2026-05-21

### Fixed — Critical: API key not loading on startup (chatbot returned 500 on every message)

**Root cause:**  
In `backend/main.py`, the `retriever` module was imported at the top of the file before `load_dotenv()` was called. Since `retriever.py` reads `GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")` at module level (on import), the key was always `None` at that point — causing a `403 PERMISSION_DENIED` error from the Gemini Embeddings API on every chat request.

**Fix (`backend/main.py`):**  
Moved `import os` and `load_dotenv()` to the very top of the file — before any other imports — so the `.env` file is loaded into the environment before any module tries to read from it.

```python
# BEFORE (broken)
from fastapi import FastAPI ...
from retriever import retrieve, build_context   # reads GEMINI_API_KEY here — .env not loaded yet
load_dotenv(...)                                # too late

# AFTER (fixed)
import os
from dotenv import load_dotenv
load_dotenv(...)                                # .env loaded first
from fastapi import FastAPI ...
from retriever import retrieve, build_context   # GEMINI_API_KEY now available
```

---

### Added — Static file serving for frontend assets (chatbot UI had no styles or interactivity)

**Root cause:**  
`demo.html` references `frontend/kst-chatbot.css` and `frontend/kst-chatbot.js`, but the FastAPI server had no route to serve those files — they returned 404, leaving the chat widget unstyled and non-functional.

**Fix (`backend/main.py`):**  
Added `StaticFiles` mount so the `/frontend` path serves files from the `frontend/` directory.

```python
from fastapi.staticfiles import StaticFiles

app.mount(
    "/frontend",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend")),
    name="frontend",
)
```

---

### Changed — Backend port moved from 8000 to 8001

**Reason:**  
Port 8000 had ghost LISTENING entries left over from previous server processes that could not be cleared without a system restart, causing new server instances to fail with `[WinError 10048] address already in use`.

**Files changed:**
- `demo.html` — updated `data-api` attribute from `http://localhost:8000/chat` to `http://localhost:8001/chat`
- Server is now started with `uvicorn main:app --host 0.0.0.0 --port 8001`

---

## [1.0.0] - Initial Commit

- FastAPI backend with RAG pipeline using ChromaDB + Google Gemini Embeddings
- 21 KST knowledge chunks covering installation, troubleshooting, GDPR, attribution
- `gemini-2.5-flash` for chat generation, `gemini-embedding-001` for vector search
- Vanilla JS/CSS chatbot widget embedded in `demo.html`
- `ingest.py` for one-time knowledge base embedding
- Support for GTM, Shopify, WooCommerce, PrestaShop, Magento, LightSpeed, Unas, Server-to-Server installs
