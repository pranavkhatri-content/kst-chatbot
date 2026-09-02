# Design Document — KST Support Chatbot (CPI-2633)

**Author:** Pranav Khatri
**Status:** Draft for review
**Related:** [Architecture diagram](../README.md#architecture) · [Example Questions](./example-questions.md) · [Implementation Plan](./IMPLEMENTATION_PLAN.md)

## 1. Problem statement

KST installation spans 8+ e-commerce platforms, each with different steps.
Merchants who get stuck raise support tickets for repetitive, well-documented
questions ("where do I put the lead tag in Shopify?", "why aren't my sales
showing?"). This does not scale with support headcount, and a merchant who
gives up mid-installation means untracked sales, billing disputes, and churn
risk. Full problem framing lives in the epic description on
[CPI-2633](https://kelkoogroup.atlassian.net/browse/CPI-2633).

## 2. Goal

An AI chatbot embedded in the Merchant Centre that resolves the majority of
KST installation/troubleshooting questions instantly and self-serve, with a
clear escalation path (Salesforce case) for anything it cannot resolve.

## 3. Approach: Retrieval-Augmented Generation (RAG)

Rather than fine-tuning a model or hand-coding a decision tree, the system
retrieves relevant KST documentation for each question and has an LLM
generate the answer strictly from that retrieved content. See the
[architecture diagram](../README.md#architecture) for the component
breakdown.

This was chosen over:
- **Fine-tuning** — too costly to keep in sync as documentation changes, and
  provides no natural way to cite sources.
- **A rule-based / decision-tree bot** — brittle, doesn't handle free-text
  phrasing, and doesn't scale to open-ended troubleshooting questions.

## 4. Key technical choices and why

| Choice | Decision | Reasoning |
|---|---|---|
| Embeddings | Local (`sentence-transformers`, `all-MiniLM-L6-v2`) | Originally used Gemini's embedding API; this ran on *every* question and was the largest driver of API cost. Moved to a local model — zero cost, zero external dependency, no accuracy loss observed on our knowledge base size. |
| Vector store | ChromaDB (embedded, file-based) | No separate database service to run/maintain; sufficient for 25 chunks today and scales to low thousands without infra changes. |
| Chunking | 25 hand-authored chunks, one topic each | Earlier iteration had broader chunks (e.g. all 5 GTM steps in one); splitting into focused sub-chunks produced tighter, more precise retrieval matches (documented in `CHANGELOG.md` v1.2.0). |
| Retrieval | Dual-query: latest message (primary) + recent conversation (context), top-k merged, cosine-distance threshold | A single joined "last 3 messages" query let earlier conversation topics drown out the current question in multi-turn chats (e.g. "What is KST?" → "Shopify setup" failed to retrieve the Shopify chunk). Fixed in v1.3.1 — see `CHANGELOG.md`. |
| LLM provider | Switchable: Gemini 2.5 Flash (default) or internal Gemma-4-26B via llama.cpp | See [Section 5](#5-llm-provider-the-central-open-decision) below — this is the item most needing alignment. |
| Frontend | Vanilla JS + CSS widget, no framework/deps | Needs to embed into an existing Merchant Centre page via a single `<script>` tag with zero build-step friction for whichever team owns that integration. |

## 5. LLM provider: the central open decision

This is the primary "choice" this document exists to align on.

**Gemini 2.5 Flash** (currently the default):
- Fast (~5–10s per answer), mature, stable.
- Costs money per request; data leaves Kelkoo infrastructure to Google.

**Internal Gemma-4-26B** (via Kelkoo's llama.cpp server, dev environment):
- Free, keeps data on Kelkoo infrastructure.
- Currently **CPU-bound**: prompt processing measured at ~87 tokens/sec,
  producing 3–38s response times depending on prompt-cache hits. It is also a
  *reasoning* model that generates hidden "thinking" tokens before answering,
  adding further latency.
- Quality of answers (when it responds) has been equivalent to Gemini in
  side-by-side testing on the same RAG pipeline.

**What would resolve this in Gemma's favour:** GPU allocation for the
inference server (would likely bring prompt processing from ~23s to under 1s)
and/or disabling the reasoning budget (`--reasoning-budget 0` in llama.cpp) for
this use case, where deep reasoning isn't needed for documentation lookup.
Both are infrastructure/data-science decisions outside this doc's scope, and
are flagged to the data science team as a dependency.

**Current direction (pending final alignment, not a closed decision):** ship
on Gemini for the initial rollout — latency matters for a support-facing chat
widget, and Gemma isn't there yet — while treating the internal provider as
the intended long-term target given it's free and keeps data on Kelkoo
infrastructure. The switchable provider (already built) exists precisely so
this transition can happen without a rewrite: once GPU allocation and/or the
reasoning-budget change land, we revisit the default and expect to move to
Gemma. This direction is not yet finalized and should be confirmed as part of
this review. See [Implementation Plan](./IMPLEMENTATION_PLAN.md) for the
concrete story sequencing this implies.

## 6. Guardrails (known limitation)

The system prompt instructs the model to (a) answer only from retrieved KST
documentation and (b) refuse/redirect anything unrelated. This is enforced via
prompt instruction, not a hard technical filter. **Observed in testing:** a
message like "call an ambulance for me" was answered directly from the model's
general training instead of being refused — the guardrail did not hold in that
case. Tightening the system prompt language reduced but did not eliminate this
risk. A stricter fix (e.g. a lightweight pre-classification step that rejects
clearly off-topic input before it reaches the LLM) is deferred to a follow-up
story — see [Implementation Plan](./IMPLEMENTATION_PLAN.md#stage-4--hardening).

## 7. What is explicitly out of scope for v1

- Multilingual support (system prompt currently says "respond in the same
  language the merchant writes in" but this is untested/unverified at scale).
- Salesforce case creation via real API (the form UI exists; submission is
  currently a UI-only success state — see Implementation Plan).
- Conversation persistence/analytics (history lives in the browser only).
- Support for e-commerce platforms beyond the 8 currently documented.

## 8. Open questions for reviewers

- **LLM provider default** — Gemini now, Gemma later? Timeline dependency on
  data science team's GPU/reasoning-budget work (Section 5).
- <a name="open-question-rag-vs-full-context"></a>**RAG vs. full-context** — at
  25 chunks (~6,500 tokens), the entire knowledge base fits comfortably inside
  a single prompt for either model. Is the retrieval layer's added complexity
  justified today, or should we simplify to "always inject everything" until
  the knowledge base grows past a size where that's no longer true? (Rough
  threshold to revisit this: once total chunk content exceeds ~50k tokens.)
- <a name="open-question-internal-model-readiness"></a>**Internal model
  readiness** — what's the realistic timeline for GPU allocation to the Gemma
  server? This determines when the internal-provider path can become default.
- <a name="open-question-conversation-persistence"></a>**Conversation
  logging** — do we need server-side conversation logging for QA/analytics, or
  does that introduce data-handling requirements (merchant PII in chat
  transcripts) that need separate sign-off?
- **Architecture review** — Georgios has flagged wanting architecture input
  (e.g. from Bastien Deshayes or someone else in that function) specifically
  on best practices for building an *external-facing* chatbot. This document
  is the starting point for that review, not a replacement for it.
