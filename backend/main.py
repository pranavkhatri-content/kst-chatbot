import os
from dotenv import load_dotenv

# Load .env FIRST — before any other imports that read env vars at module level
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from typing import List
from retriever import retrieve, build_context

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models"
    f"/{GEMINI_MODEL}:generateContent"
)

# ── Fixed system prompt (small — no knowledge baked in) ──────────────────────
BASE_SYSTEM_PROMPT = """
You are the Kelkoo Sales Tracking (KST) Support Assistant — a helpful, concise chatbot embedded in the Kelkoo Merchant Centre and documentation website.

Your purpose is to:
1. Answer general questions about Kelkoo Sales Tracking (KST).
2. Guide merchants step-by-step through KST installation on their specific platform.
3. Troubleshoot common KST issues.

You will be given relevant excerpts from the official KST documentation to answer each question.
Each excerpt includes a [Source N: Topic] label and a Documentation URL.

Guidelines:
- Always lead your answer with the relevant documentation link.
- Be concise. Use bullet points and code blocks where helpful.
- Only use information from the provided sources — do not invent Merchant IDs, country codes, or tracking URLs.
- If asked about installation, share the doc link first, give a 2-3 sentence summary, then ask if they want the full steps.
- Respond in the same language the merchant writes in.
- For issues not covered in the sources, direct merchants to: https://merchant.kelkoogroup.com/app/campaign/sales-tracking
""".strip()

app = FastAPI(title="KST Chatbot RAG API")

# Serve frontend static files (CSS, JS)
app.mount(
    "/frontend",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend")),
    name="frontend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # ── 1. Retrieve relevant chunks using recent conversation context ────────
    user_messages = [m.content for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    retrieval_query = " ".join(user_messages[-3:])

    async with httpx.AsyncClient(timeout=30) as client:
        chunks = retrieve(retrieval_query, top_k=3)
        context = build_context(chunks)

        # ── 2. Build dynamic system prompt with retrieved context ────────────
        system_prompt = (
            BASE_SYSTEM_PROMPT
            + "\n\n---\n\n## Relevant KST Documentation (retrieved for this query)\n\n"
            + context
        )

        # ── 3. Build conversation history (last 20 messages) ─────────────────
        history = request.messages[-20:]
        contents = []
        for msg in history:
            role = "model" if msg.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
        }

        # ── 4. Call Gemini ────────────────────────────────────────────────────
        resp = await client.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
        )

    if resp.status_code != 200:
        print(f"[Gemini Error] {resp.status_code}: {resp.text}")
        raise HTTPException(status_code=502, detail=resp.text)

    data = resp.json()
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    return ChatResponse(reply=reply)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "demo.html"))
