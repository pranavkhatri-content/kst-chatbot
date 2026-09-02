"""
knowledge_chunks.py — Loads the KST knowledge base and exposes it as CHUNKS.

The data itself lives in knowledge_chunks.jsonl (one JSON object per line),
built from per-topic batch files under dataset/ via build_dataset.py. It moved
out of this module when the knowledge base grew past ~100 entries: a JSONL file
diffs and reviews far better than a multi-thousand-line Python literal.

This module stays the import surface so ingest.py, retriever.py and the eval
harness keep working unchanged:

    from knowledge_chunks import CHUNKS

Chunk fields
------------
Retrieval-critical (see ingest.py — ONLY these are embedded):
  id         unique slug, e.g. "shopify__conversion-tag"
  topic      human-readable label; embedded as its own vector
  queries    anticipated user phrasings; EACH is embedded as its own vector.
             This is what retrieval actually matches against, so a chunk with
             thin queries is effectively unreachable no matter how good its
             content is.

Answer-time:
  content    what the LLM reads. Code/parameters/tables are verbatim from the
             docs; surrounding prose is condensed and reworded.
  doc_url    canonical link the bot cites to the merchant.

Provenance metadata:
  tier            1 = derived from a single documentation section
                  2 = editorial synthesis across several pages
  derived         true on tier 2 only; retriever.build_context() labels these
                  so the model doesn't present them as Kelkoo's own wording
  source_urls     tier 2 only — every page the note draws on
  page_title      the source page's title
  section_heading the heading this chunk came from (null if whole-page)
  last_modified   page's stated last-modified date, if it publishes one
  crawled_at      date the source was fetched
  contains_code   whether content includes a code block
  platform_tags   gtm | manual | magento | shopify | woocommerce | unas |
                  prestashop-1.6 | prestashop-1.7 | prestashop-8 | lightspeed |
                  server-to-server | none
"""

import json
import os

_JSONL = os.path.join(os.path.dirname(__file__), "knowledge_chunks.jsonl")


def load_chunks(path: str = _JSONL) -> list[dict]:
    """Read the JSONL knowledge base. Blank lines and // comments are skipped."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Build it first:\n"
            f"    python build_dataset.py"
        )
    chunks = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno} invalid JSON: {exc}") from exc
    return chunks


CHUNKS = load_chunks()
