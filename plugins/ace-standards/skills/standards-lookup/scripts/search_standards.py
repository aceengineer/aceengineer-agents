#!/usr/bin/env python3
"""Resolve a standard to its code identifier, publisher and revision.

Searches the AceEngineer standards corpus (llm-wiki) frontmatter only and
reports metadata. It deliberately never prints body text: the corpus operates a
vendor-PDF firewall, and this script is the mechanical edge of it.

  search_standards.py "mooring fatigue"
  search_standards.py --code api-rp-2sk
  search_standards.py --publisher DNV --tag fatigue
  search_standards.py --corpus /path/to/llm-wiki "riser"

Corpus path resolution order:
  --corpus, $ACE_STANDARDS_CORPUS, $CLAUDE_PLUGIN_OPTION_STANDARDS_CORPUS_PATH
    (the last is exported automatically from the plugin's standards_corpus_path
     user config; the naming convention is CLAUDE_PLUGIN_OPTION_<KEY uppercased>)
"""
import argparse
import os
import re
import sys

REL = os.path.join("wikis", "engineering-standards", "wiki", "standards")
FIELDS = ("title", "code_id", "publisher", "revision", "jurisdiction",
          "license_status", "visibility", "last_updated")

# Values that occupy the `revision` field without pinning an edition. These are
# worse than a missing field: they read as an answer. "latest" in particular is
# a promise that expires silently -- it was true when written, is unverifiable
# now, and becomes wrong the moment a new edition ships without anyone touching
# the page. All of them are reported as UNPINNED.
NON_EDITIONS = {"unknown", "latest", "not-on-disk", "n/a", "na", "none",
                "tbd", "current", "-", ""}


def edition_of(meta):
    """(display, pinned) for a page's revision field."""
    raw = (meta.get("revision") or "").strip()
    if raw.strip('"\'').lower() in NON_EDITIONS:
        return (f"UNPINNED ({raw})" if raw else "UNPINNED (absent)"), False
    return raw, True


def corpus_root(explicit):
    for cand in (explicit,
                 os.environ.get("ACE_STANDARDS_CORPUS"),
                 os.environ.get("CLAUDE_PLUGIN_OPTION_STANDARDS_CORPUS_PATH")):
        if cand:
            return os.path.expanduser(cand)
    return None


def parse_frontmatter(path):
    """Minimal YAML frontmatter reader — scalars, quoted scalars, and lists.

    Deliberately does not import a YAML library: this ships to client machines
    and must not carry a dependency to read a dozen keys.
    """
    meta, tags = {}, []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            if fh.readline().strip() != "---":
                return meta, tags
            key = None
            for line in fh:
                if line.strip() == "---":
                    break
                if re.match(r"^\s*-\s+", line):
                    val = re.sub(r"^\s*-\s+", "", line).strip().strip('"\'')
                    if key == "tags":
                        tags.append(val)
                    continue
                m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
                if m:
                    key, val = m.group(1), m.group(2).strip().strip('"\'')
                    if val:
                        meta[key] = val
    except OSError:
        pass
    return meta, tags


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="*", help="free-text terms matched against title, code id and tags")
    ap.add_argument("--corpus", help="path to the standards corpus (llm-wiki) root")
    ap.add_argument("--code", help="exact or partial code identifier, e.g. api-rp-2sk")
    ap.add_argument("--publisher", help="filter by publisher, e.g. DNV")
    ap.add_argument("--tag", action="append", default=[], help="filter by tag (repeatable)")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--unpinned", action="store_true",
                    help="list only standards whose edition is not pinned")
    args = ap.parse_args()

    root = corpus_root(args.corpus)
    if not root:
        print("NO CORPUS: standards_corpus_path is not configured.\n"
              "This agent resolves standards from the AceEngineer corpus and does not\n"
              "answer editions from memory. Configure the plugin, or pass --corpus.",
              file=sys.stderr)
        return 2

    sdir = os.path.join(root, REL)
    if not os.path.isdir(sdir):
        print(f"NO CORPUS: {sdir} not found.\n"
              "The configured path is not an AceEngineer standards corpus.", file=sys.stderr)
        return 2

    terms = [t.lower() for t in args.query]
    hits = []
    for name in sorted(os.listdir(sdir)):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        path = os.path.join(sdir, name)
        meta, tags = parse_frontmatter(path)
        hay = " ".join([meta.get("title", ""), meta.get("code_id", name[:-3]),
                        meta.get("publisher", ""), " ".join(tags)]).lower()

        if args.code and args.code.lower() not in meta.get("code_id", name[:-3]).lower():
            continue
        if args.publisher and args.publisher.lower() not in meta.get("publisher", "").lower():
            continue
        if args.tag and not all(t.lower() in [x.lower() for x in tags] for t in args.tag):
            continue
        if terms and not all(t in hay for t in terms):
            continue

        if args.unpinned and edition_of(meta)[1]:
            continue
        meta["_page"] = os.path.relpath(path, root)
        meta["_tags"] = tags
        hits.append(meta)

    if not hits:
        print("No matching standard in the corpus.\n"
              "Absence here is not proof the standard does not exist — it means this\n"
              "corpus has no page for it. Say so; do not substitute recollection.")
        return 1

    print(f"{len(hits)} match(es); showing up to {args.limit}. "
          f"Metadata only — clause text is out of scope by design.\n")
    for m in hits[:args.limit]:
        print(f"  {m.get('code_id', '?')}")
        print(f"    title      : {m.get('title', '(untitled)')}")
        print(f"    publisher  : {m.get('publisher', 'UNRECORDED')}")
        ed, pinned = edition_of(m)
        if pinned:
            # The corpus is a shelf inventory. `revision` is the edition
            # AceEngineer HOLDS -- not necessarily the edition that is current.
            print(f"    edition held: {ed}")
            cs = (m.get("currency_status") or "").strip().lower()
            pub = m.get("publisher_current_edition", "")
            chk = m.get("currency_checked_on", "")
            if cs == "superseded":
                print(f"    currency    : SUPERSEDED  <-- publisher-current is {pub or 'a later edition'}"
                      f" (checked {chk})\n                  the held edition is NOT current;"
                      " existing work against it is edition-sensitive")
            elif cs == "current":
                print(f"    currency    : current as at {chk}")
            elif cs == "unresolved":
                print(f"    currency    : UNRESOLVED (checked {chk}) -- a later edition is"
                      " indicated but\n                  was not confirmed; do not cite the held"
                      " edition as current")
            else:
                v = m.get("verified_on", "")
                print(f"    currency    : NEVER CHECKED"
                      + (f" (holdings recorded {v})" if v else "")
                      + "\n                  the corpus knows the shelf, not the market --"
                      " check the publisher catalogue")
        else:
            print(f"    edition held: {ed}  <-- EDITION NOT PINNED; do not cite this as an edition")
        if m.get("jurisdiction"):
            print(f"    jurisdiction: {m['jurisdiction']}")
        if m.get("_tags"):
            print(f"    tags       : {', '.join(m['_tags'][:8])}")
        print(f"    page       : {m['_page']}")
        print()
    if len(hits) > args.limit:
        print(f"  … {len(hits) - args.limit} further match(es) suppressed; narrow the query.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
