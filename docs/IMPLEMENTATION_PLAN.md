# Implementation Plan — KST Support Chatbot (CPI-2633)

Iterative story list: simple → complex. Each stage is shippable/demoable on
its own; later stages only proceed once the prior stage is validated. See
[Design Document](./DESIGN.md) for the reasoning behind each choice referenced
here, and the [architecture diagram](../README.md#architecture) for the system
diagram.

## Stage 0 — Foundation (done)

- [x] RAG pipeline: knowledge base (25 chunks), local embeddings, ChromaDB
      retrieval, LLM generation (Gemini)
- [x] Embeddable JS/CSS widget (no framework dependency)
- [x] Conversational UX: quick-chip menu, follow-up flow ("any other doubt?"),
      "Other Issue" free-text path, "Start New Chat" reset
- [x] Salesforce case form UI (submission not yet wired to a real API)
- [x] Local demo environment (`demo.html`, `start.bat`)

## Stage 1 — Provider flexibility (done)

- [x] Move embeddings off the paid Gemini API to a local model (cost removal,
      independent of which LLM answers questions)
- [x] Switchable LLM provider (`LLM_PROVIDER` config: `gemini` | `internal`),
      same RAG pipeline feeds either model
- [x] Per-request provider override + testing dropdown in the widget (for
      side-by-side comparison during evaluation — not intended for merchants)
- [x] Fix multi-turn retrieval bug (dual-query retrieval) surfaced while
      testing the internal model
- [x] Request/response logging for debugging and provider comparison
- [x] Output token cap (guard against runaway generation)

## Stage 2 — Pre-launch hardening (next)

- [ ] **Guardrail tightening**: address the observed off-topic-answer gap
      (see [Design Document §6](./DESIGN.md#6-guardrails-known-limitation)) —
      evaluate a lightweight pre-classification step to reject clearly
      out-of-scope input before it reaches the LLM
- [ ] **Architecture review**: schedule the review Georgios flagged
      (external-facing chatbot best practices) before wider rollout
- [ ] **Load/latency testing**: confirm response times are acceptable under
      concurrent merchant load (relevant regardless of which LLM provider is
      live)
- [ ] **Content QA pass**: verify all 25 knowledge chunks against current
      KST documentation for accuracy (docs may have drifted since chunks were
      authored)
- [ ] Decide RAG-vs-full-context question (see [Design Document open
      questions](./DESIGN.md#8-open-questions-for-reviewers)) before scaling
      the knowledge base further

## Stage 3 — Merchant Centre integration

- [ ] Embed the widget into the real Merchant Centre page (currently only
      proven against a mock demo page)
- [ ] Confirm CORS / auth context: does the widget need to know which
      merchant/country is logged in, to personalize responses?
- [ ] Analytics: track chatbot usage (questions asked, resolution rate,
      escalation rate) to measure the ticket-deflection goal from the epic
- [ ] Staging deployment + smoke test

## Stage 4 — Hardening

- [ ] Wire the Salesforce case form to a real API (currently UI-only success
      state)
- [ ] Server-side conversation logging, if approved (see [Design Document
      open questions](./DESIGN.md#8-open-questions-for-reviewers) — needs a
      decision on merchant PII handling first)
- [ ] Multilingual verification: test the "respond in the same language"
      instruction across the merchant base's actual language mix
- [ ] Decide and execute on the LLM provider default (Gemini vs. internal
      Gemma) once the data science team's GPU/reasoning-budget work lands —
      see [Design Document §5](./DESIGN.md#5-llm-provider-the-central-open-decision)

## Stage 5 — Scale / iterate (only if needed)

- [ ] Expand platform coverage beyond the current 8 (based on real gaps
      surfaced by Stage 3 analytics)
- [ ] Re-evaluate chunking/retrieval tuning (`top_k`, distance threshold) using
      real merchant question data instead of synthetic test questions
- [ ] Consider query rewriting (e.g. HyDE-style) for retrieval if ambiguous
      follow-up questions remain a problem at scale

---

**Sizing note**: Stages 0–1 are complete. Stages 2–4 are the near-term scope
for the current 5MD "Tracking" allocation on this epic; Stage 5 is intentionally
deferred until real usage data justifies it, in line with the "simpler before
complex" principle requested for this plan.
