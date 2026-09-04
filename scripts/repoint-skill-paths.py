#!/usr/bin/env python3
"""Repoint dead FILE paths in the skill corpus (#267, second sweep).

The import sweep fixed dead module paths. This fixes the other half: scripts,
configs and docs a skill names that have moved. Same root cause -- digitalmodel
flattened src/digitalmodel/modules/ into solvers/, marine_ops/, structural/ and
the corpus never followed.

Resolves by BASENAME rather than by prefix rules, and only when the basename is
UNIQUE in the target tree. A basename with two candidates is reported, never
guessed: picking one at random would produce a path that resolves and is wrong,
which is worse than the honest breakage it replaces.

Operates on the upstream corpus in workspace-hub, never the vendored copy.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = os.path.join(HERE, "..", "..", "workspace-hub",
                        ".claude", "skills", "engineering", "marine-offshore")
DM = os.path.join(HERE, "..", "..", "digitalmodel")
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
from check_skill_paths import CANDIDATE, EXTS, IGNORE, satisfied  # noqa: E402


def index_basenames(root):
    idx = defaultdict(list)
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in
                   (".git", "__pycache__", "node_modules", ".venv")]
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            idx[fn].append(rel)
    return idx


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    idx = index_basenames(DM)
    fixed = ambiguous = absent = 0

    for dirpath, _, fns in os.walk(UPSTREAM):
        if "_archive" in dirpath:
            continue
        for fn in fns:
            if fn != "SKILL.md":
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            cands = {c for c in CANDIDATE.findall(text)
                     if c.endswith(EXTS) and not IGNORE.search(c)}
            hits = []
            for c in sorted(cands):
                if satisfied(c, dirpath):
                    continue
                matches = idx.get(os.path.basename(c), [])
                if len(matches) == 1:
                    hits.append((c, matches[0]))
                elif len(matches) > 1:
                    print(f"  AMBIGUOUS {c}\n      {len(matches)} candidates, not guessing")
                    ambiguous += 1
                else:
                    print(f"  ABSENT    {c}")
                    absent += 1
            if not hits:
                continue
            out = text
            rel = os.path.relpath(path, UPSTREAM)
            print(f"  {rel}")
            for old, new in hits:
                print(f"      {old}\n        -> {new}")
                out = out.replace(f"`{old}`", f"`{new}`")
                fixed += 1
            if args.apply:
                open(path, "w", encoding="utf-8").write(out)

    verb = "repointed" if args.apply else "would repoint"
    print(f"\n{verb} {fixed}   ambiguous {ambiguous}   absent {absent}")
    if args.dry_run:
        print("(dry run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
