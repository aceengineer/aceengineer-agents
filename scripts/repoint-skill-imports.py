#!/usr/bin/env python3
"""Apply the digitalmodel refactor's prefix moves to the skill corpus (#267).

Operates on the UPSTREAM corpus in workspace-hub, never on the vendored copy --
sync-skills.sh wipes the vendored tree, so a fix applied there is lost.

Conservative by construction: a rewrite is applied **only if the rewritten path
actually resolves** against the digitalmodel source. A prefix rule that would
produce another dead path is skipped, leaving the honest breakage in place. A
wrong repoint looks fixed, which is worse than a visible failure.

  repoint-skill-imports.py --dry-run     report what would change
  repoint-skill-imports.py --apply       write the changes
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
from check_skill_imports import resolve  # noqa: E402

# `from <mod> import <sym>, <sym>` on one line -- the symbols a module rewrite
# must still satisfy.
FROM_LINE = re.compile(r"^\s*from\s+(digitalmodel(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s+import\s+([A-Za-z_][A-Za-z0-9_, ]*)",
                       re.M)

UPSTREAM = os.path.join(HERE, "..", "..", "workspace-hub",
                        ".claude", "skills", "engineering", "marine-offshore")

# Ordered: first rule whose rewrite RESOLVES wins.
RULES = [
    ("digitalmodel.orcaflex.",    "digitalmodel.solvers.orcaflex."),
    ("digitalmodel.orcawave.",    "digitalmodel.solvers.orcawave."),
    # NOT orcawave -> bemrosetta. bemrosetta.mesh RESOLVES, but it holds
    # dat/gdf/mesh/stl handlers -- not OrcaWaveMeshGenerator or WaterlineRefiner.
    # Rewriting there would turn an honest "no such module" into a convincing
    # "module exists" that still fails at the symbol. bemrosetta is a BEM
    # file-format tool, not an OrcaWave mesh generator.
    ("digitalmodel.aqwa.",        "digitalmodel.hydrodynamics.aqwa."),
    ("digitalmodel.diffraction.", "digitalmodel.hydrodynamics.diffraction."),
    ("digitalmodel.signal_processing.signal_analysis.",
     "digitalmodel.signal_processing.signal_analysis.core."),
]

# A dotted path, longest-first so we rewrite the full path not a prefix of it.
TOKEN = re.compile(r"\bdigitalmodel(?:\.[A-Za-z_][A-Za-z0-9_]*)+")


def symbols_required(text, module):
    """Symbols that `from <module> import ...` demands, across the whole file."""
    want = set()
    for mod, syms in FROM_LINE.findall(text):
        if mod == module:
            want.update(x.strip() for x in syms.split(",") if x.strip())
    return want


def best_rewrite(path, cache, required=frozenset()):
    key = (path, required)
    if key in cache:
        return cache[key]
    result = None
    if not resolve(path)[0]:
        for frm, to in RULES:
            if path.startswith(frm):
                cand = to + path[len(frm):]
                if not resolve(cand)[0]:
                    continue
                # A module that resolves is not enough: every symbol the skill
                # imports from it must exist there too, or the rewrite merely
                # makes a dead reference look alive.
                if all(resolve(f"{cand}.{sym}")[0] for sym in required):
                    result = cand
                    break
    cache[key] = result
    return result


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(UPSTREAM):
        print(f"FATAL: upstream corpus not found at {UPSTREAM}", file=sys.stderr)
        return 2

    cache, changed_files, total = {}, 0, 0
    for dirpath, _, files in os.walk(UPSTREAM):
        if "_archive" in dirpath:
            continue
        for fn in files:
            if fn != "SKILL.md":
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8", errors="replace").read()

            hits = []

            def sub(m):
                new = best_rewrite(m.group(0), cache,
                                   frozenset(symbols_required(text, m.group(0))))
                if new:
                    hits.append((m.group(0), new))
                    return new
                return m.group(0)

            out = TOKEN.sub(sub, text)
            if not hits:
                continue
            changed_files += 1
            total += len(hits)
            rel = os.path.relpath(path, UPSTREAM)
            print(f"  {rel}   ({len(hits)} rewrite(s))")
            for old, new in sorted(set(hits)):
                print(f"      {old}\n        -> {new}")
            if args.apply:
                open(path, "w", encoding="utf-8").write(out)

    verb = "rewrote" if args.apply else "would rewrite"
    print(f"\n{verb} {total} path(s) across {changed_files} skill(s)")
    if args.dry_run:
        print("(dry run -- nothing written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
