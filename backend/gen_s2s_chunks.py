"""
gen_s2s_chunks.py — Generate the server-to-server language-example chunks.

These four code examples (PHP/Java/Python/Node.js) run 5.4k-8.5k characters
each and are the single most copy-paste-sensitive content in the whole
knowledge base — a developer pastes them straight into their backend. They are
extracted programmatically straight from the crawl output rather than retyped,
so the code is guaranteed byte-identical to what Kelkoo publishes.

Each language splits into two chunks along its own two code blocks:
  1. storing the click ID (kelkooId / gclid / msclkid) when a page is visited
  2. calling the Kelkoo Sales Tracking webservice on the confirmation page

Usage:
    python gen_s2s_chunks.py    # writes dataset/08_server_to_server_code.jsonl
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CRAWL = os.path.join(HERE, "..", "crawl_output", "pages.json")
OUT = os.path.join(HERE, "dataset", "08_server_to_server_code.jsonl")

URL = ("https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking"
       "/installation-methods/advanced-setup/server-to-server-integration")

# heading -> (slug, tag, human name)
LANGS = [
    ("PHP (Version 5.5.0 or higher)", "php", "PHP 5.5.0+"),
    ("Java (Version 8)", "java", "Java 8"),
    ("Python (Version 3.x)", "python", "Python 3.x"),
    ("Node.js (version 20.x)", "nodejs", "Node.js 20.x"),
]

QUERIES = {
    "php": ["server to server PHP example", "PHP code for Kelkoo sales tracking",
            "how do I call the Kelkoo webservice from PHP",
            "PHP backend tracking implementation", "store kelkooId in PHP"],
    "java": ["server to server Java example", "Java code for Kelkoo sales tracking",
             "how do I call the Kelkoo webservice from Java",
             "Java backend tracking implementation", "store kelkooId in Java"],
    "python": ["server to server Python example", "Python code for Kelkoo sales tracking",
               "how do I call the Kelkoo webservice from Python",
               "Python backend tracking implementation", "store kelkooId in Python"],
    "nodejs": ["server to server Node.js example", "Node code for Kelkoo sales tracking",
               "how do I call the Kelkoo webservice from Node",
               "javascript backend tracking implementation", "store kelkooId in Node.js"],
}


def extract_code_blocks(text: str) -> list[str]:
    """Return fenced code blocks verbatim, fences included."""
    return re.findall(r"```\n.*?\n```", text, flags=re.S)


def main():
    with open(CRAWL, encoding="utf-8") as f:
        data = json.load(f)

    page = next(p for p in data["pages"] if "server-to-server" in p["slug"])
    body = next(s["content"] for s in page["sections"]
                if s["section_heading"] and "implement" in s["section_heading"].lower())

    # slice the page body per language heading
    starts = {}
    for heading, slug, _ in LANGS:
        idx = body.find("#### " + heading)
        if idx == -1:
            raise SystemExit(f"Language heading not found: {heading}")
        starts[slug] = idx

    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    slices = {}
    for i, (slug, start) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(body)
        slices[slug] = body[start:end]

    rows = []
    for heading, slug, name in LANGS:
        blocks = extract_code_blocks(slices[slug])
        if len(blocks) != 2:
            raise SystemExit(f"{slug}: expected 2 code blocks, got {len(blocks)}")

        store_code, call_code = blocks

        rows.append({
            "id": f"s2s__{slug}-store-click-id",
            "topic": f"Server-to-server ({name}): store the click ID when a page is visited",
            "queries": QUERIES[slug][:3] + [
                f"{name} example storing the click id",
                "how do I save kelkooId and gclid to my database",
            ],
            "content": (
                f"{name} example from Kelkoo Group's documentation, showing how to store "
                f"the tracking click ID (kelkooId / Google Click Id / Microsoft Click ID) "
                f"in the database whenever a page is visited, associating it with the "
                f"current user via login and basket.\n\n{store_code}"
            ),
            "doc_url": URL,
            "page_title": "Server to server integration",
            "section_heading": f"What exactly do you need to implement ? / {heading}",
            "last_modified": None,
            "crawled_at": "2026-09-02",
            "tier": 1,
            "contains_code": True,
            "platform_tags": ["server-to-server"],
        })

        rows.append({
            "id": f"s2s__{slug}-call-webservice",
            "topic": f"Server-to-server ({name}): call the Sales Tracking webservice",
            "queries": QUERIES[slug][2:] + [
                f"{name} example calling the tracking webservice",
                "how do I send the sale to Kelkoo from my backend",
            ],
            "content": (
                f"{name} example from Kelkoo Group's documentation, showing how to "
                f"retrieve the stored click IDs on the confirmation page and call the "
                f"Kelkoo Sales Tracking webservice at https://s.kelkoogroup.net/st for "
                f"each sale.\n\n{call_code}"
            ),
            "doc_url": URL,
            "page_title": "Server to server integration",
            "section_heading": f"What exactly do you need to implement ? / {heading}",
            "last_modified": None,
            "crawled_at": "2026-09-02",
            "tier": 1,
            "contains_code": True,
            "platform_tags": ["server-to-server"],
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} chunks to {OUT}")
    for r in rows:
        print(f"  {len(r['content']):6} chars  {r['id']}")


if __name__ == "__main__":
    main()
