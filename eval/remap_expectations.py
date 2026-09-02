"""
remap_expectations.py — Point the eval set's expect_chunk_ids at the rebuilt
knowledge base.

The knowledge base moved from 25 hand-written whole-page chunks to 104
section-level chunks with new ids, so every expect_chunk_ids in questions.json
referenced ids that no longer exist. Rather than hand-editing 47 questions,
the mapping lives here, per question id, so it is reviewable in one place and
can be re-run if the eval set changes.

Several questions list MORE than one acceptable chunk: retrieval scoring
counts a hit if ANY expected id is retrieved, and the finer-grained chunks
often split one old topic across two or three legitimate answers (e.g. a
Shopify install question is correctly served by the lead-tag OR the
conversion-tag chunk).

Usage:
    python eval/remap_expectations.py --check   # show what would change
    python eval/remap_expectations.py           # write questions.json
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = os.path.join(HERE, "questions.json")
JSONL = os.path.join(HERE, "..", "backend", "knowledge_chunks.jsonl")

# question id -> acceptable chunk ids in the rebuilt knowledge base
MAPPING = {
    "c01": ["kst-overview__what-is-kst"],
    "c02": ["understanding-kst__attribution-model", "synth__why-numbers-differ-from-ga"],
    "c03": ["gdpr__data-processing-details", "gdpr__first-party-cookies", "gdpr__overview"],
    "c04": ["merchant-id__how-to-find"],
    "c05": ["country-codes__full-list", "synth__country-code-gotchas"],
    "c06": ["manual__remove-previous-installations", "magento__overview-and-cleanup"],
    "c07": ["gtm__overview"],
    "c08": ["gtm__step1-identify-datalayer"],
    "c09": ["gtm__step4-install-conversion-tag", "gtm__step5-install-lead-tag"],
    "c10": ["manual__overview"],
    "c11": ["shopify__before-you-begin", "shopify__lead-tag", "shopify__conversion-tag"],
    "c12": ["woocommerce__install-plugin"],
    "c13": ["prestashop-8__prerequisites", "prestashop-8__conversion-tag",
            "prestashop-8__lead-tag", "synth__prestashop-version-differences"],
    "c14": ["prestashop-16__prerequisites", "prestashop-16__conversion-tag",
            "prestashop-16__lead-tag", "synth__prestashop-version-differences"],
    "c15": ["magento2__lead-tag", "magento2__conversion-tag-module"],
    "c16": ["magento1__conversion-tag", "magento1__lead-tag"],
    "c17": ["lightspeed__install"],
    "c18": ["unas__install-plugin"],
    "c19": ["s2s__when-to-use-and-limitations", "s2s__how-it-works",
            "synth__choosing-gtm-vs-manual-vs-s2s"],
    "c20": ["testing__how-to-test", "testing__verify-sales-processed"],
    "c21": ["troubleshooting__start-here", "synth__general-troubleshooting-checklist"],
    "c22": ["ts-gtm__undefined-order-fields"],
    "c23": ["ts-shopify__currency-and-comma"],
    "c24": ["ts-prestashop__common-issues"],
    "c25": ["install-methods__performance-impact",
            "understanding-kst__spa-and-performance-faq"],
    "c26": ["gdpr__first-party-cookies", "gdpr__data-processing-details",
            "merchant-id__how-to-find", "gdpr__overview"],
    "c27": ["troubleshooting__start-here", "synth__general-troubleshooting-checklist"],

    "adv03": ["merchant-id__how-to-find"],
    # Deliberately absurd multi-platform question — any platform install or
    # method-selection chunk is a legitimate hit, so the list is broad.
    "adv06": ["kst-overview__what-is-kst", "install-methods__choosing-a-method",
              "synth__choosing-gtm-vs-manual-vs-s2s", "shopify__before-you-begin",
              "shopify__lead-tag", "shopify__conversion-tag",
              "shopify__multiple-campaigns", "woocommerce__install-plugin",
              "woocommerce__multiple-campaigns", "magento2__lead-tag",
              "magento2__conversion-tag-module", "synth__where-the-tags-go-by-platform",
              "synth__multi-campaign-across-platforms"],
    "adv09": ["troubleshooting__start-here", "synth__general-troubleshooting-checklist"],
    "adv10": ["shopify__before-you-begin", "shopify__lead-tag", "shopify__conversion-tag"],

    "ml01": ["shopify__before-you-begin", "shopify__lead-tag", "shopify__conversion-tag"],
    "ml02": ["troubleshooting__start-here", "synth__general-troubleshooting-checklist"],
    "ml03": ["merchant-id__how-to-find"],
    "ml04": ["gdpr__overview", "gdpr__first-party-cookies", "gdpr__data-processing-details"],
    "ml05": ["testing__how-to-test", "testing__verify-sales-processed"],

    "mt01": ["shopify__conversion-tag", "shopify__lead-tag", "shopify__before-you-begin"],
    "mt02": ["woocommerce__install-plugin", "woocommerce__configure-plugin"],
    "mt03": ["troubleshooting__start-here", "synth__general-troubleshooting-checklist",
             "ts-shopify__device-specific-sections", "testing__verify-sales-processed"],
    "mt04": ["manual__conversion-tag", "manual__conversion-tag-parameters",
             "manual__multiple-campaigns"],
    "mt05": ["manual__overview", "s2s__when-to-use-and-limitations",
             "synth__choosing-gtm-vs-manual-vs-s2s"],
}

# doc_url expectations that changed because the old dataset cited a dead or
# wrong-version URL
DOC_URL_FIXES = {
    "c13": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/prestashop-8",
    "c14": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/installation-guides-for-ecommerce-platforms/prestashop-1-6x",
    "c19": "https://docs.kelkoogroup.com/for-advertisers/kelkoo-sales-tracking/installation-methods/advanced-setup/server-to-server-integration",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, don't write")
    args = ap.parse_args()

    valid_ids = set()
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                valid_ids.add(json.loads(line)["id"])

    with open(QUESTIONS, encoding="utf-8") as f:
        data = json.load(f)

    problems, changed = [], 0
    for q in data["questions"]:
        qid = q["id"]
        if qid in MAPPING:
            new_ids = MAPPING[qid]
            missing = [i for i in new_ids if i not in valid_ids]
            if missing:
                problems.append(f"{qid}: unknown chunk id(s) {missing}")
                continue
            if q.get("expect_chunk_ids") != new_ids:
                q["expect_chunk_ids"] = new_ids
                changed += 1
        elif q.get("expect_chunk_ids"):
            problems.append(f"{qid}: has expect_chunk_ids but no mapping entry")

        if qid in DOC_URL_FIXES:
            q["expect_doc_url"] = DOC_URL_FIXES[qid]

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print(f"Remapped {changed} question(s) onto {len(valid_ids)} known chunk ids.")
    if args.check:
        print("--check: not writing.")
        return

    with open(QUESTIONS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {QUESTIONS}")


if __name__ == "__main__":
    main()
