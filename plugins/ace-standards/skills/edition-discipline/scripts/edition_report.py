#!/usr/bin/env python3
"""Report edition pinning and supersession across the standards corpus (#259).

Reports only what the corpus records. Where supersession appears in prose rather
than in a structured field, that is said explicitly -- a prose mention is a lead,
not an assertion, and presenting it as structured data would manufacture
confidence the corpus does not have.

    edition_report.py --unpinned          standards with no real edition
    edition_report.py --supersession      recorded supersession relationships
    edition_report.py --summary           corpus-wide edition health
"""
import argparse
import os
import re
import sys

REL = os.path.join("wikis", "engineering-standards", "wiki", "standards")
NON_EDITIONS = {"unknown", "latest", "not-on-disk", "n/a", "na", "none",
                "tbd", "current", "-", ""}
# A key that exists and says nothing is not a record. `supersedes: None` reads
# as a relationship in a key count and asserts nothing at all.
EMPTY = {"", "none", "null", "~", "n/a", "na", "-", "tbd", "unknown", "[]", "{}"}
# Supersession proper: one edition or document replacing another.
STRUCTURED = ("supersedes", "superseded_by", "superseded_by_note",
              "edition_status", "current_edition_warning")
# NOT supersession: a publisher rebrand (NACE -> AMPP) changes the code id while
# the document stands. Counting these as supersession overstates how much the
# corpus actually knows, which is the opposite of what this tool is for.
REBRAND = ("legacy_code_id",)
PROSE = re.compile(r"\b(supersede[sd]?|superseding|withdrawn|replaced by)\b", re.I)


def corpus_root(explicit):
    for c in (explicit, os.environ.get("ACE_STANDARDS_CORPUS"),
              os.environ.get("CLAUDE_PLUGIN_OPTION_STANDARDS_CORPUS_PATH")):
        if c:
            return os.path.expanduser(c)
    return None


def read(path):
    meta, body = {}, ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        km = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$", line)
        if km:
            meta[km.group(1)] = km.group(2).strip().strip('"\'')
    return meta, m.group(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--unpinned", action="store_true")
    ap.add_argument("--supersession", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--currency", action="store_true",
                    help="report which standards have had publisher currency checked")
    args = ap.parse_args()

    root = corpus_root(args.corpus)
    sdir = os.path.join(root, REL) if root else None
    if not sdir or not os.path.isdir(sdir):
        print("NO CORPUS: configure standards_corpus_path, or pass --corpus.",
              file=sys.stderr)
        return 2

    pages = []
    for fn in sorted(os.listdir(sdir)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        meta, body = read(os.path.join(sdir, fn))
        code = meta.get("code_id", fn[:-3])
        rev = (meta.get("revision") or "").strip()
        pinned = rev.lower() not in NON_EDITIONS
        cur = (meta.get("currency_status") or "").strip().lower()
        struct = {k: meta[k] for k in STRUCTURED
                  if k in meta and meta[k].strip().lower() not in EMPTY}
        rebrand = {k: meta[k] for k in REBRAND
                   if k in meta and meta[k].strip().lower() not in EMPTY}
        pages.append((code, rev, pinned, struct, bool(PROSE.search(body)), fn, rebrand,
                      cur, meta.get("publisher_current_edition", "")))

    if args.currency:
        checked = [p for p in pages if p[7]]
        print(f"{len(checked)} of {len(pages)} standards have had publisher currency checked\n")
        for code, rev, _, _, _, _, _, cur, pub in checked:
            tag = {"superseded": "SUPERSEDED", "current": "current",
                   "unresolved": "UNRESOLVED"}.get(cur, cur.upper())
            print(f"  {code:20s} held {rev:22s} {tag}"
                  + (f"   publisher-current: {pub}" if pub else ""))
        print(f"\n  {len(pages)-len(checked)} standards have NEVER been currency-checked.")
        print("  For those the corpus records what is on the shelf and is silent")
        print("  about the market -- and silence reads as currency.")
        return 0

    if args.unpinned:
        rows = [p for p in pages if not p[2]]
        print(f"{len(rows)} of {len(pages)} standards have no pinned edition\n")
        for code, rev, *_ in rows:
            print(f"  {code:38s} revision: {rev or '(absent)'}")
        print("\nAn unpinned edition is a finding, not a gap to fill with an assumption.")
        return 0

    if args.supersession:
        s = [p for p in pages if p[3]]
        pr = [p for p in pages if not p[3] and p[4]]
        print(f"{len(s)} standard(s) record supersession in a STRUCTURED field:\n")
        for code, _, _, struct, *_ in s:
            print(f"  {code}")
            for k, v in struct.items():
                print(f"      {k}: {v[:110]}")
        print(f"\n{len(pr)} further standard(s) mention supersession only in PROSE.")
        print("  A prose mention is a lead, not an assertion. Read the page before")
        print("  relying on it, and promote it to a structured field if it holds:")
        for code, *_ in pr[:20]:
            print(f"      {code}")
        if len(pr) > 20:
            print(f"      … and {len(pr)-20} more")
        return 0

    total = len(pages)
    unp = sum(1 for p in pages if not p[2])
    st = sum(1 for p in pages if p[3])
    pro = sum(1 for p in pages if not p[3] and p[4])
    print("Corpus edition health\n")
    print(f"  standards                       {total}")
    print(f"  edition pinned                  {total-unp}  ({100*(total-unp)//total}%)")
    print(f"  edition UNPINNED                {unp}  ({100*unp//total}%)")
    reb = sum(1 for p in pages if p[6])
    print(f"  supersession, structured field  {st}")
    print(f"  supersession, prose only        {pro}")
    print(f"  publisher rebrand recorded      {reb}   (legacy_code_id; not supersession)")
    hollow = sum(1 for p in pages
                 if any(k in read(os.path.join(sdir, p[5]))[0] for k in STRUCTURED)
                 and not p[3])
    print(f"  supersession key present but EMPTY  {hollow}   (e.g. `supersedes: None`)")
    cc = sum(1 for p in pages if p[7])
    sup = sum(1 for p in pages if p[7] == "superseded")
    print(f"  publisher currency checked      {cc}  ({100*cc//total}%)")
    print(f"    of those, SUPERSEDED          {sup}")
    print(f"  edition deltas established      0   <- nobody has checked any yet")
    print("\n  'edition deltas established: 0' means no criterion-level change has")
    print("  been verified against both documents. It does NOT mean nothing moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
