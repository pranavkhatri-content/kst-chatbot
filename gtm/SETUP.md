# GTM local-dev integration

Wires the KST chatbot widget into a page via Google Tag Manager, backed by a
locally-running copy of the backend. This is the first integration step —
proving the real delivery mechanism (GTM injecting the widget into a page
that knows nothing about it) — before there's a server to deploy the backend
to, and without touching the real Merchant Centre GTM account.

## Architecture

Three independent pieces, deliberately decoupled:

1. **The host page** ([`test-page.html`](./test-page.html)) — near-blank, carries
   no reference to the widget at all. Its only job is to load GTM. Served by
   whatever static server you like, separate from the backend process.
2. **GTM** (sandbox container `GTM-K729V6VM`, account `KST Chatbot — Dev Sandbox`)
   — a Custom HTML tag containing the widget loader, firing on the test page.
3. **The backend** — a normal local `uvicorn` process, unaware GTM exists.

This mirrors the real target shape: a foreign page + GTM injection + a
backend that doesn't care how it's called.

## 1. Start the backend

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

Confirm: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`.

(If you're using `start.bat` instead, it runs on **8001**, not 8000 — update
the URLs in `kst-widget-loader.html` to match if so.)

## 2. Serve the test page — separately from the backend

From the `gtm/` directory, with whatever static server you prefer, e.g.:

```bash
python -m http.server 5500
```

Then open `http://localhost:5500/test-page.html`. It should show a plain
"intentionally left blank" page — no widget yet, since the GTM tag doesn't
exist.

## 3. Create the tag in GTM

1. Open container `GTM-K729V6VM` (`KST Chatbot — Dev Sandbox` account).
2. **Tags → New → Tag Configuration → Custom HTML.**
3. Paste the contents of [`kst-widget-loader.html`](./kst-widget-loader.html) in verbatim.
4. **Triggering:** `All Pages` is fine here — this container isn't installed
   anywhere except your own local test page, so there's no risk of it firing
   somewhere unintended.
5. Name it `KST Chatbot Widget — LOCAL DEV`, save. **Don't publish yet.**

## 4. Test via Preview — without publishing

Because the container snippet is genuinely on `test-page.html` (unlike the
real Merchant Centre page, which doesn't have this container), GTM's native
**Preview** mode connects to it directly:

1. In GTM, click **Preview**.
2. Enter `http://localhost:5500/test-page.html` and connect.
3. The test page opens with the debug connection active; your unpublished
   tag fires even though nothing is published.
4. Confirm in the Tag Assistant panel that the tag fired, and that the chat
   FAB appears on the page.

If it doesn't appear: check the browser console first. Likely causes are the
backend not running, or a mixed-content block if you switch the test page to
being served over HTTPS later (localhost is exempt from that in Chrome/Firefox,
but only over `http://localhost` — worth knowing if this setup changes).

## Later, when there's something real to point at

- Swap `http://localhost:8000` in `kst-widget-loader.html` for the real
  backend host.
- Tighten `allow_origins` in `backend/main.py` from `"*"` to the real host
  page's origin.
- This sandbox container was never meant to reach the live Merchant Centre —
  that integration is a separate step, into the container already installed
  there (`GTM-NQ5SKWVV`), once this proves out.
