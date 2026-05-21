# Changelog

All notable changes to the KST Chatbot are documented here.
Format: [Version] — Date — Author — Branch

---

## [1.1.0] — 2026-05-21 — Atik Jain — feat/atik-follow-up-sf-form

This release combines two sets of work:
- **Critical bug fixes** (originally in `fix/atik-static-files-and-api-key-fix`, never merged)
- **New conversation features** (follow-up flow, Other Issue path, SF case form, restart)

Both are delivered together in this branch.

---

### 🐛 Bug Fix 1 — Chatbot returning "Something went wrong" on every message

**Symptom:** Every message sent to the chatbot returned a 500 error and the UI showed "Sorry, something went wrong."

**Root cause:**
In `backend/main.py`, the `retriever` module was imported **before** `load_dotenv()` was called.
Since `retriever.py` reads `GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")` at module level
(i.e. the moment it is imported), the key was always `None` — causing a `403 PERMISSION_DENIED`
error from the Google Gemini Embeddings API on every single request.

**Fix — `backend/main.py`:**
Moved `import os` and `load_dotenv()` to the very top of the file, before all other imports.

```python
# BEFORE (broken)
from fastapi import FastAPI ...
from retriever import retrieve, build_context   # ← runs here, GEMINI_API_KEY = None
load_dotenv(...)                                # ← too late, key already read as None

# AFTER (fixed)
import os
from dotenv import load_dotenv
load_dotenv(...)                                # ← .env loaded first
from fastapi import FastAPI ...
from retriever import retrieve, build_context   # ← GEMINI_API_KEY now has the correct value
```

---

### 🐛 Bug Fix 2 — Chatbot UI had no styles or interactivity (blank / unstyled)

**Symptom:** The page loaded but the chat widget had no CSS styling and the JS was not working.

**Root cause:**
`demo.html` loads `frontend/kst-chatbot.css` and `frontend/kst-chatbot.js`, but FastAPI had
no route configured to serve files from the `frontend/` directory. Both files returned 404.

**Fix — `backend/main.py`:**
Added a `StaticFiles` mount so the `/frontend` URL path maps to the `frontend/` folder.

```python
from fastapi.staticfiles import StaticFiles

app.mount(
    "/frontend",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend")),
    name="frontend",
)
```

---

### 🔧 Change — Port reverted to 8000

**Reason:**
During development, port 8000 had ghost `LISTENING` entries from previous processes that
blocked the server from binding. A temporary workaround moved the server to port 8001.
The conflict has since been resolved — port is back to **8000**.

**Files changed:**
- `demo.html` — `data-api` attribute updated back to `http://localhost:8000/chat`
- Server started with: `uvicorn main:app --host 0.0.0.0 --port 8000`

---

### ✨ Feature 1 — Follow-up prompt after every answer

After every bot response, the chatbot now asks:

> **"Do you have any other doubt?"**
> `[ Yes ]` `[ No, end chat ]`

- **Yes** → bot acknowledges, scrolls to the quick-chips menu so the user can pick a topic
- **No** → bot says goodbye, input is disabled cleanly
- Buttons are disabled after one is clicked (prevents double-tap)

**File changed:** `frontend/kst-chatbot.js`

---

### ✨ Feature 2 — "Other Issue" chip with custom support flow

A new **"Other Issue"** chip (styled distinctly in orange outline) has been added to the quick-chips menu.

**Flow:**
```
User clicks "Other Issue"
    → Bot: "Please explain your issue in detail and I'll do my best to help."
    → User types their issue
    → RAG backend searches knowledge base and returns best-effort answer
    → Bot asks: "Was this helpful? Is your issue resolved?"
        [ Yes, resolved! ]  →  "Great! Glad I could help 😊" → back to normal follow-up
        [ No, still having issue ]  →  "Create SF Support Case" button appears
```

**File changed:** `frontend/kst-chatbot.js`

---

### ✨ Feature 3 — Salesforce Support Case form

When the user clicks **"📋 Create SF Support Case"**, an inline form appears inside the chat:

| Field | Type | Required |
|-------|------|----------|
| Your Name | Text | ✅ |
| Merchant ID | Text | ✅ |
| Email Address | Email | ✅ |
| Describe your issue | Textarea | ✅ |

**Behaviour:**
- All fields are validated on submit — empty fields highlighted in red
- On successful submit: form replaced with a success message confirming the email address
- Chat input is disabled after submission (case is open, no further action needed)
- **Note:** SF API integration is not wired yet — form UI is ready for connection

**Files changed:** `frontend/kst-chatbot.js`, `frontend/kst-chatbot.css`

---

### ✨ Feature 4 — "Start New Chat" restart button

When the chat ends (either via "No, end chat" or after SF case submission), a
**"🔄 Start New Chat"** button appears.

Clicking it:
- Clears all messages from the screen
- Resets the full conversation history
- Resets conversation state to `normal`
- Re-enables the input box
- Shows the welcome message again for a completely fresh session

**Files changed:** `frontend/kst-chatbot.js`, `frontend/kst-chatbot.css`

---

## [1.0.0] — Initial Commit — pranavkhatri-content

- FastAPI backend with RAG pipeline (ChromaDB + Google Gemini Embeddings)
- 21 KST knowledge chunks: installation, troubleshooting, GDPR, attribution, platforms
- `gemini-2.5-flash` for response generation
- `gemini-embedding-001` for vector search / retrieval
- Vanilla JS + CSS chatbot widget embedded in `demo.html`
- `ingest.py` for one-time knowledge base embedding into ChromaDB
- Platform support: GTM, Manual, Shopify, WooCommerce, PrestaShop, Magento, LightSpeed, Unas, Server-to-Server

---

## How to Run (Local)

```bash
# 1. Copy env file and add your Gemini API key
cp .env.example .env

# 2. Create virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r backend\requirements.txt

# 3. Embed knowledge base (run once)
cd backend
python ingest.py

# 4. Start server
uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Open browser
# http://localhost:8000
```

---

## Branch Strategy

| Branch | Purpose | Status |
|--------|---------|--------|
| `main` | Production — original code | Untouched |
| `fix/atik-static-files-and-api-key-fix` | Original bug fixes (not merged) | Superseded by below |
| `feat/atik-follow-up-sf-form` | Bug fixes + all new features | Pending review & merge |
