"""
crawl_docs.py — Fetch the Kelkoo KST documentation and split each page into
heading-delimited sections, ready to be turned into RAG chunks.

The docs site is server-rendered (Confluence-backed), so plain HTTP is enough —
no JS rendering, no third-party crawl API, no cost.

Sections are split on <h2>, with <h3>/<h4> kept as sub-headings inside their
parent section. Headings are the natural retrieval boundary here: a question
about Shopify currency formatting should pull exactly that section, not a
token window straddling two unrelated topics.

Code blocks (<pre>/<code>) are preserved VERBATIM and fenced, because those are
what a developer pastes into their own site. Prose is emitted as-is here and
condensed later when chunks are authored — this script does extraction only,
no rewriting, so the raw source stays auditable.

Usage:
    python crawl_docs.py                  # crawl all pages -> crawl_output/
    python crawl_docs.py --url <URL>      # single page (debugging)
"""

import argparse
import json
import os
import re
import time
from datetime import date

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

BASE = "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking"
SITEMAP = "https://docs.kelkoogroup.com/__sitemaps/b2bc439a-b145-40ad-9900-5e976cf423a2/sitemap.xml"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "crawl_output")

# Elements that carry no answerable content
DROP_SELECTORS = [
    "nav", "header", "footer", "script", "style", "noscript",
    "[role=navigation]", "[aria-label*=breadcrumb i]",
]


def discover_urls(client: httpx.Client) -> list[str]:
    """Pull the KST page list from the sitemap rather than trusting a hardcoded
    list — the page tree can change between runs."""
    resp = client.get(SITEMAP)
    resp.raise_for_status()
    urls = re.findall(r"<loc>([^<]+)</loc>", resp.text)
    kst = sorted({u for u in urls if "kelkoo-sales-tracking" in u})
    return kst


def _clean_text(el: Tag) -> str:
    txt = el.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", txt).strip()


def _render_block(el: Tag) -> str:
    """Render one block-level element to markdown-ish text.

    Code is fenced and kept byte-for-byte; everything else becomes plain text
    (condensing happens later, by hand, when chunks are authored).
    """
    name = el.name

    if name == "pre":
        code = el.get_text()  # NOT stripped - preserve internal formatting
        return "```\n" + code.strip("\n") + "\n```"

    if name in ("ul", "ol"):
        lines = []
        for i, li in enumerate(el.find_all("li", recursive=False), 1):
            # a <li> can itself contain a <pre>; keep that fenced
            pre = li.find("pre")
            if pre:
                before = _clean_text(li).replace(pre.get_text(" ", strip=True), "").strip()
                bullet = f"{i}." if name == "ol" else "-"
                if before:
                    lines.append(f"{bullet} {before}")
                lines.append("```\n" + pre.get_text().strip("\n") + "\n```")
            else:
                text = _clean_text(li)
                if text:
                    lines.append(f"{'%d.' % i if name == 'ol' else '-'} {text}")
        return "\n".join(lines)

    if name == "table":
        rows = []
        for tr in el.find_all("tr"):
            cells = [_clean_text(td) for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(" | ".join(cells))
        return "\n".join(rows)

    if name == "img":
        alt = el.get("alt") or ""
        src = el.get("src") or ""
        return f"[image: {alt}]" if alt else f"[image: {src}]"

    text = _clean_text(el)
    return text


def parse_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    for sel in DROP_SELECTORS:
        for el in soup.select(sel):
            el.decompose()

    # Page title: prefer the <h1>, fall back to <title> minus the site suffix
    h1 = soup.find("h1")
    if h1:
        page_title = _clean_text(h1)
    else:
        raw = soup.title.get_text(strip=True) if soup.title else url.rsplit("/", 1)[-1]
        page_title = raw.split("|")[0].strip()

    # Confluence-style "last updated" if the theme renders one
    last_modified = None
    for pat in [r"Last updated[:\s]+([A-Za-z0-9,\s\-/]+)",
                r"Last modified[:\s]+([A-Za-z0-9,\s\-/]+)"]:
        m = re.search(pat, soup.get_text(" ", strip=True))
        if m:
            last_modified = m.group(1).strip()[:40]
            break

    # Main content root: the article body if the theme marks one, else <body>
    root = (soup.find("article") or soup.find("main")
            or soup.find(attrs={"data-page-template": True}) or soup.body or soup)

    sections = []
    current = {"heading": None, "level": None, "blocks": []}

    def flush():
        if current["blocks"] or current["heading"]:
            body = "\n\n".join(b for b in current["blocks"] if b.strip())
            if body.strip() or current["heading"]:
                sections.append({
                    "section_heading": current["heading"],
                    "heading_level": current["level"],
                    "content": body.strip(),
                })

    for el in root.find_all(
        ["h1", "h2", "h3", "h4", "p", "pre", "ul", "ol", "table", "img", "blockquote"]
    ):
        # skip nodes nested inside a block we already rendered (e.g. <pre> in <li>)
        if el.find_parent(["li", "pre", "table"]) and el.name not in ("h1", "h2", "h3", "h4"):
            continue

        if el.name == "h1":
            continue  # page title, already captured

        if el.name == "h2":
            flush()
            current = {"heading": _clean_text(el), "level": 2, "blocks": []}
            continue

        if el.name in ("h3", "h4"):
            # keep sub-headings inline so their context isn't lost, but also
            # record them so chunk authoring can split further if a section is large
            level = int(el.name[1])
            current["blocks"].append(f"{'#' * level} {_clean_text(el)}")
            continue

        block = _render_block(el)
        if block and block.strip():
            current["blocks"].append(block)

    flush()

    # Drop empty leading section that holds nothing
    sections = [s for s in sections
                if s["content"].strip() or s["section_heading"]]

    return {
        "source_url": url,
        "page_title": page_title,
        "last_modified": last_modified,
        "crawled_at": date.today().isoformat(),
        "sections": sections,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=None, help="crawl a single URL (debugging)")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between requests (be polite)")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    headers = {"User-Agent": "KST-Chatbot-DocIngest/1.0 (internal RAG dataset build)"}

    failures = []
    pages = []

    with httpx.Client(timeout=45, follow_redirects=True, headers=headers) as client:
        urls = [args.url] if args.url else discover_urls(client)
        print(f"Crawling {len(urls)} page(s)\n")

        for i, url in enumerate(urls, 1):
            slug = url.replace(BASE, "").strip("/") or "index"
            slug = slug.replace("/", "__")
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    print(f"  [{i}/{len(urls)}] FAILED {resp.status_code}  {slug}")
                    failures.append({"url": url, "status": resp.status_code})
                    continue
                page = parse_page(resp.text, url)
                page["slug"] = slug
                pages.append(page)
                n_sec = len(page["sections"])
                n_chars = sum(len(s["content"]) for s in page["sections"])
                flag = "  <-- THIN" if n_chars < 400 else ""
                print(f"  [{i}/{len(urls)}] {slug[:62]:64} {n_sec:2} sec, {n_chars:6} chars{flag}")
            except Exception as exc:
                print(f"  [{i}/{len(urls)}] ERROR  {slug}: {type(exc).__name__}: {exc}")
                failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            time.sleep(args.delay)

    out = os.path.join(OUT_DIR, "pages.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"crawled_at": date.today().isoformat(),
                   "pages": pages, "failures": failures}, f, indent=2, ensure_ascii=False)

    print(f"\n{len(pages)} page(s) parsed, {len(failures)} failure(s)")
    print(f"Total sections: {sum(len(p['sections']) for p in pages)}")
    print(f"Wrote {out}")
    if failures:
        print("\nFailures:")
        for f_ in failures:
            print(f"  {f_}")


if __name__ == "__main__":
    main()
