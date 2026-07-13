# Changelog

All notable changes to the KST Chatbot are documented here.
Format: [Version] — Date — Author — Branch

---

## [1.3.0] — 2026-07-13 — Pranav Khatri — feature/internal-llm-provider-switch

This release removes the paid-API dependency for embeddings and adds a switchable
LLM provider so the chatbot can run on either Google Gemini or Kelkoo's internal
Gemma server.

---

### ✨ Change 1 — Embeddings moved from Gemini API to local sentence-transformers

**Problem:**
Every question triggered a paid Gemini Embedding API call (plus one call per chunk
at ingest time). This was the largest driver of API cost since it fired on every
single request.

**Fix — `backend/retriever.py` + `backend/ingest.py`:**
Embeddings now run fully locally via `sentence-transformers` (`all-MiniLM-L6-v2`,
configurable via `EMBED_MODEL` in `.env`). No API key, no cost, no network call.
`ingest.py` reuses the exact same embedder as retrieval so vectors always match.

⚠ **Re-ingestion required** — the embedding model changed, so old vectors are
invalid. Delete `chroma_db/` and run `python ingest.py` (or `start.bat` does it
automatically).

Note: first request after server start loads the embedding model into memory
(~2-5s one-time delay). First ever run downloads the model (~80MB) from HuggingFace.

---

### ✨ Change 2 — Switchable LLM provider (Gemini ⇄ internal Gemma)

**`backend/main.py`:**
- New `LLM_PROVIDER` setting in `.env`: `"gemini"` (default) or `"internal"`
- `"internal"` calls Kelkoo's llama.cpp server (OpenAI-compatible API) at
  `LLM_BASE_URL` with model `LLM_MODEL` — currently
  `gemma-4-26B-A4B-it-UD-Q3_K_M.gguf` on `dc1-kdp-dev-worker-01`
- The `/chat` endpoint also accepts an optional per-request `provider` field that
  overrides the `.env` default (used by the widget's model picker)
- Every request logs which provider/model answered: `[LLM] provider=... model=...`
- Internal model runs with `temperature: 0.2` for factual answers

**Known limitation:** the internal Gemma server (CPU, reasoning model) currently
takes ~38s per answer vs ~5s for Gemini. Raised with the data science team
(GPU offload + `--reasoning-budget 0` would bring it to ~2-4s).

---

### ✨ Change 3 — Model picker in the widget header (testing)

**`frontend/kst-chatbot.js` + `frontend/kst-chatbot.css`:**
A dropdown in the chat header lets you switch between "Gemini" and
"Gemma (internal)" per conversation, for side-by-side comparison. The selection
is sent as `provider` with each `/chat` request. Switching posts a confirmation
message in the chat.

---

### 🐛 Bug Fix — Chat header invisible on short screens

**Symptom:** On viewports shorter than ~680px, the widget's entire header
(title, expand/close buttons, model picker) was pushed above the visible screen.

**Root cause:** `#kst-chat-window` had a hardcoded `height: 580px` with
`bottom: 96px` — on short screens the window extended past the viewport top.

**Fix — `frontend/kst-chatbot.css`:**
Added `max-height: calc(100dvh - 120px)` so the window always fits the viewport.

---

**Files changed:**
- `backend/retriever.py` — local embeddings
- `backend/ingest.py` — local embeddings, reuses retriever's embedder
- `backend/main.py` — provider switch + per-request override + logging
- `backend/requirements.txt` — added sentence-transformers
- `frontend/kst-chatbot.js` — model picker
- `frontend/kst-chatbot.css` — picker styles + max-height fix
- `.env.example` — new configuration keys

---

## [1.2.0] — 2026-05-22 — Sebastian Krishna — feature/rag-retrieval-optimization

This release optimises the RAG retrieval pipeline across four areas:
chunk granularity, embedding quality, retrieval precision, and multi-turn context.

---

### 🔧 Change 1 — Split large chunks into focused sub-chunks (20 → 25 chunks)

**Problem:**
Several knowledge chunks covered multiple distinct topics in a single entry. For example,
`install_gtm` contained all 5 GTM setup steps (~30 lines), `install_prestashop` covered
versions 1.6, 1.7 AND 8, and `install_magento` covered both Magento 1 and 2. When these
chunks are embedded, the resulting vector is a diluted average of all subtopics — causing
weaker semantic matches when a user asks about a specific step or version.

**Fix — `backend/knowledge_chunks.py`:**
Split the three worst offenders into focused sub-chunks:
- `install_gtm` → `install_gtm_overview`, `install_gtm_datalayer`, `install_gtm_tags`
- `install_prestashop` → `install_prestashop_8_17`, `install_prestashop_16`
- `install_magento` → `install_magento2`, `install_magento1`

Each sub-chunk now covers a single focused topic, producing tighter embedding vectors
that match more precisely to user queries.

---

### ✨ Change 2 — Add query preambles for better semantic matching

**Problem:**
Chunks were embedded using `topic + content`, which reads like documentation. But users
don't phrase questions like documentation headings — they say things like "my sales aren't
showing up" or "where is my merchant ID". The embedding model needs to match against how
users actually speak, not how docs are written.

**Fix — `backend/knowledge_chunks.py` + `backend/ingest.py`:**
Added a `queries` field to every chunk containing 3–7 anticipated user phrasings:

```python
# Example from knowledge_chunks.py
{
    "id": "troubleshooting_general",
    "queries": [
        "KST not working",
        "no conversions showing",
        "sales not tracking",
        "pixel not firing",
        "zero sales in dashboard",
    ],
    ...
}
```

In `ingest.py`, the text sent to the embedding model now includes these queries:

```python
# BEFORE
text = f"{chunk['topic']}\n\n{chunk['content']}"

# AFTER
queries_block = "\n".join(chunk.get("queries", []))
text = f"{chunk['topic']}\n\n{queries_block}\n\n{chunk['content']}"
```

The stored document (what the LLM reads at answer time) remains unchanged — only the
embedding vector is enriched.

---

### 🔧 Change 3 — Add distance threshold and reduce top_k (5 → 3)

**Problem:**
The retriever always returned exactly 5 chunks (`top_k=5`) regardless of relevance. With
only 20–25 chunks total, this meant 20–25% of the entire knowledge base was injected into
every prompt. Chunks #4 and #5 were often barely related noise that the LLM had to wade
through, increasing token cost and risking off-topic answers.

**Fix — `backend/retriever.py`:**
- Reduced default `top_k` from 5 to 3
- Added a `max_distance` parameter (default `1.0` for cosine distance) that filters out
  chunks beyond the threshold — if only 2 results are truly relevant, you get 2 instead
  of being padded with noise
- Added debug logging that prints the distance score for each candidate chunk, enabling
  future threshold tuning

```python
# BEFORE
def retrieve(query: str, top_k: int = 5) -> list[dict]:

# AFTER
def retrieve(query: str, top_k: int = 3, max_distance: float = 1.0) -> list[dict]:
    ...
    for doc, meta, dist in zip(...):
        print(f"  [{round(dist, 4)}] {meta['topic']}")
        if dist > max_distance:
            break
        chunks.append(...)
```

---

### ✨ Change 4 — Conversational retrieval using multi-turn context

**Problem:**
Retrieval used only the latest user message. In multi-turn conversations, follow-up
questions lose their topic context. For example:

```
User: "How do I install KST on Shopify?"
Bot:  (explains Shopify steps)
User: "What about the conversion tag part?"
```

The follow-up "What about the conversion tag part?" was embedded alone — matching GTM,
Manual, and Shopify conversion tag chunks equally, because "Shopify" wasn't in the query.

**Fix — `backend/main.py`:**
The retrieval query now joins the last 3 user messages instead of just the latest one:

```python
# BEFORE
latest_user_msg = next(
    (m.content for m in reversed(request.messages) if m.role == "user"),
    None,
)
chunks = retrieve(latest_user_msg, top_k=5)

# AFTER
user_messages = [m.content for m in request.messages if m.role == "user"]
retrieval_query = " ".join(user_messages[-3:])
chunks = retrieve(retrieval_query, top_k=3)
```

This means the follow-up query becomes `"How do I install KST on Shopify? What about the
conversion tag part?"` — which correctly retrieves Shopify-specific conversion tag chunks.

---

### ⚠️ Re-ingestion required

The `chroma_db/` directory has been deleted. After pulling this branch, run:

```bash
cd backend
python ingest.py
```

Or simply run `start.bat`, which detects the missing `chroma_db/` and re-ingests automatically.

**Files changed:**
- `backend/knowledge_chunks.py` — chunk splits + query preambles
- `backend/retriever.py` — distance threshold + debug logging
- `backend/ingest.py` — include queries in embedding text
- `backend/main.py` — multi-turn retrieval query

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

## [1.0.0] — Initial Commit — Sebastian Krishna

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
| `feature/rag-retrieval-optimization` | RAG retrieval pipeline optimization | Pending review & merge |
