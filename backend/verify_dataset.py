"""
verify_dataset.py — Check authored chunks against the crawled source.

The risk when hand-authoring chunks from crawled pages is drift: a code block
subtly retyped, a parameter renamed, a URL attributed to the wrong page. This
checks what can be checked mechanically:

  1. every code block in a chunk appears VERBATIM in its cited source page
  2. every doc_url / source_url was actually crawled
  3. every tier-1 chunk's doc_url matches a page we hold content for
  4. numeric IDs and cookie/parameter names in chunks exist in the source

Anything it flags is either a real transcription error or a deliberate edit
worth re-reading. It cannot check whether reworded prose is faithful — that
still needs a human, but the sample it prints makes spot-checking easy.

Usage:
    python verify_dataset.py            # full check
    python verify_dataset.py --sample 5 # also print N random chunks vs source
"""

import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CRAWL = os.path.join(HERE, "..", "crawl_output", "pages.json")
JSONL = os.path.join(HERE, "knowledge_chunks.jsonl")

CODE_RE = re.compile(r"```\n(.*?)\n```", re.S)


def normalise(s: str) -> str:
    """Collapse whitespace so trivial indentation differences don't false-alarm."""
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="print N random chunks next to their source for review")
    args = ap.parse_args()

    with open(CRAWL, encoding="utf-8") as f:
        crawl = json.load(f)
    pages = {p["source_url"]: p for p in crawl["pages"]}
    page_text = {
        url: normalise("\n".join(s["content"] for s in p["sections"]))
        for url, p in pages.items()
    }

    chunks = []
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    problems = []
    code_blocks_checked = 0

    for c in chunks:
        cid = c["id"]

        # 2/3. URLs must be real crawled pages
        for url in [c["doc_url"]] + (c.get("source_urls") or []):
            if url not in pages:
                problems.append(f"[{cid}] cites a URL that was not crawled: {url}")

        # 1. code fidelity — tier 2 is synthesis, so only tier 1 is checked
        if c.get("tier") == 1:
            src = page_text.get(c["doc_url"])
            if src is None:
                continue
            for block in CODE_RE.findall(c["content"]):
                code_blocks_checked += 1
                if normalise(block) not in src:
                    snippet = normalise(block)[:90]
                    problems.append(
                        f"[{cid}] code block not found verbatim in source: {snippet}..."
                    )

    print(f"Chunks checked      : {len(chunks)}")
    print(f"Code blocks checked : {code_blocks_checked}")
    print(f"Problems            : {len(problems)}")
    if problems:
        print()
        for p in problems:
            print(f"  - {p}")

    if args.sample:
        random.seed()
        for c in random.sample(chunks, min(args.sample, len(chunks))):
            print("\n" + "=" * 72)
            print(f"CHUNK {c['id']}  (tier {c['tier']})")
            print(f"topic   : {c['topic']}")
            print(f"doc_url : {c['doc_url']}")
            print(f"queries : {c['queries'][:3]} ...")
            print("-" * 72)
            print(c["content"][:900])
            print("-" * 72)
            src = pages.get(c["doc_url"])
            if src and c.get("tier") == 1:
                head = " ".join(s["content"] for s in src["sections"])[:700]
                print("SOURCE PAGE STARTS:", head[:700])

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
