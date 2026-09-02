# Example Questions — KST Support Assistant

This file lists the categories of questions the KST Support Assistant is designed
to resolve, grounded in the current knowledge base (`backend/knowledge_chunks.py`,
25 chunks). It exists so reviewers can judge coverage without reading the whole
knowledge base, and so we can track gaps as new questions come in from real
merchant usage.

## 1. Conceptual / "what is this?"

- What is KST (Kelkoo Sales Tracking)?
- What's the difference between the Lead Tag and the Conversion Tag?
- How does KST attribution work? What's the conversion window?
- Why do my KST numbers differ from Google Analytics?
- Is KST GDPR compliant? What cookies does it set? Do I need consent?
- Where do I find my Merchant ID and Country Code?
- What are the supported country codes?

## 2. Installation — platform-specific

- How do I install KST using Google Tag Manager (GTM)?
  - How do I find my Data Layer variables?
  - How do I set up the Custom Event Trigger?
  - How do I install the Conversion Tag / Lead Tag in GTM?
- How do I install KST manually (no plugin/platform)?
- How do I install KST on Shopify / Shopify Plus?
- How do I install KST on WooCommerce?
- How do I install KST on PrestaShop (1.6 / 1.7 / 8)?
- How do I install KST on Magento (1 or 2)?
- How do I install KST on LightSpeed C-Series?
- How do I install KST on Unas?
- How do I implement KST server-to-server (no browser script)?
- What should I do before installing KST (legacy tag cleanup)?

## 3. Testing & verification

- How do I test that my KST installation is working?
- Where do I check if my pixel is firing correctly?
- How long after installing should I expect to see sales data?

## 4. Troubleshooting

- KST isn't tracking any sales / conversions — what do I check?
- My GTM tag isn't firing / orderId or orderValue is undefined.
- My Shopify pixel isn't firing on all devices, or revenue is formatted wrong.
- My PrestaShop variables aren't being replaced correctly.
- General checklist: what's most commonly misconfigured?

## 5. Performance / technical concerns

- Will KST slow down my website?
- Does KST work on a single-page application (SPA)?
- What's the file size / load time of the tags?

## 6. Escalation path (when the bot can't resolve it)

- "Other Issue" — free-text description of a problem not covered above.
  The bot searches the knowledge base for a best-effort answer; if the
  merchant says it's still unresolved, a Salesforce support case form is
  offered (UI built, Salesforce API wiring is a separate follow-up item —
  see [Implementation Plan](./IMPLEMENTATION_PLAN.md)).

## Known gaps / out of scope today

- Platforms not yet covered: BigCommerce, Wix, Squarespace, custom headless
  storefronts beyond the generic "manual" method.
- Billing/invoice disputes — the bot redirects to Merchant Centre support,
  it does not have billing data access.
- Anything not related to KST (general Kelkoo account questions, campaign
  bidding, etc.) — the bot should refuse and redirect, per the system prompt
  guardrail (see [Design Document — Guardrails](./DESIGN.md#6-guardrails-known-limitation)).

*This list should be updated as real merchant conversations surface new
recurring questions — see the "Update the knowledge base" step in the
[Implementation Plan](./IMPLEMENTATION_PLAN.md).*
