"""
build_dataset.py — Validate and merge the authored chunk batches into the
single knowledge_chunks.jsonl that ingest.py consumes.

Chunks are authored in small per-topic batch files under backend/dataset/ so
they stay reviewable in diffs, then merged here with validation:
  - ids unique
  - required fields present
  - doc_url present and well-formed
  - tier-2 rows carry source_urls + derived
  - `queries` non-empty (retrieval depends entirely on topic+queries — a chunk
    with no queries is effectively unretrievable, see ingest.py)

Usage:
    python build_dataset.py            # validate + merge
    python build_dataset.py --check    # validate only, don't write
"""

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH_DIR = os.path.join(HERE, "dataset")
OUT_FILE = os.path.join(HERE, "knowledge_chunks.jsonl")

REQUIRED = ["id", "topic", "queries", "content", "doc_url", "tier"]


def load_batches() -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    chunks: list[dict] = []
    files = sorted(glob.glob(os.path.join(BATCH_DIR, "*.jsonl")))
    if not files:
        errors.append(f"No batch files found in {BATCH_DIR}")
    for path in files:
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{name}:{lineno} invalid JSON: {exc}")
                    continue
                obj["_source_batch"] = name
                obj["_lineno"] = lineno
                chunks.append(obj)
    return chunks, errors


def validate(chunks: list[dict]) -> list[str]:
    errors = []
    seen_ids: dict[str, str] = {}

    for c in chunks:
        where = f"{c.get('_source_batch')}:{c.get('_lineno')}"
        cid = c.get("id", "<missing id>")

        for field in REQUIRED:
            if field not in c or c[field] in (None, "", []):
                errors.append(f"{where} [{cid}] missing/empty required field: {field}")

        if cid in seen_ids:
            errors.append(f"{where} [{cid}] duplicate id (also in {seen_ids[cid]})")
        else:
            seen_ids[cid] = where

        url = c.get("doc_url", "")
        if url and not url.startswith("https://"):
            errors.append(f"{where} [{cid}] doc_url is not https: {url!r}")

        qs = c.get("queries") or []
        if isinstance(qs, list) and 0 < len(qs) < 3:
            errors.append(f"{where} [{cid}] only {len(qs)} queries — aim for 4+ "
                          f"(retrieval embeds topic+queries only)")

        if c.get("tier") == 2:
            if not c.get("derived"):
                errors.append(f"{where} [{cid}] tier 2 must set derived: true")
            if not c.get("source_urls"):
                errors.append(f"{where} [{cid}] tier 2 must list source_urls")

        content = c.get("content", "")
        if content and len(content) > 6000:
            errors.append(f"{where} [{cid}] content is {len(content)} chars — "
                          f"consider splitting")

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only")
    args = ap.parse_args()

    chunks, errors = load_batches()
    errors += validate(chunks)

    if errors:
        print(f"VALIDATION FAILED ({len(errors)} problem(s)):\n")
        for e in errors[:60]:
            print(f"  - {e}")
        if len(errors) > 60:
            print(f"  ... and {len(errors) - 60} more")
        sys.exit(1)

    # strip bookkeeping fields before writing
    clean = []
    for c in chunks:
        c.pop("_source_batch", None)
        c.pop("_lineno", None)
        clean.append(c)

    t1 = [c for c in clean if c.get("tier") == 1]
    t2 = [c for c in clean if c.get("tier") == 2]
    with_code = [c for c in clean if c.get("contains_code")]
    n_vectors = sum(1 + len(c.get("queries", [])) for c in clean)

    print(f"Validation passed.")
    print(f"  Tier 1 chunks : {len(t1)}")
    print(f"  Tier 2 chunks : {len(t2)}")
    print(f"  Total         : {len(clean)}")
    print(f"  With code     : {len(with_code)}")
    print(f"  Query vectors : {n_vectors} (topic + each query, see ingest.py)")

    if args.check:
        print("\n--check: not writing output.")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for c in clean:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"\nWrote {OUT_FILE}")
    print("Next: python ingest.py")


if __name__ == "__main__":
    main()
