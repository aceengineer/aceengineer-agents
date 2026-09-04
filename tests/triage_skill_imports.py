#!/usr/bin/env python3
"""Triage the unresolved skill imports (#267) into REPOINT vs NO-CANDIDATE.

For each documented path that does not resolve, search the digitalmodel source
for a real target:

  exact-symbol   a class/function of that exact name exists somewhere -> repoint
  module-basename the final module component exists under another parent
  no-candidate    nothing plausible -> the skill documents capability that was
                  never built, and should be deleted or marked reference-only

Deliberately conservative: it proposes candidates, it does not rewrite anything.
A wrong auto-repoint would be worse than the current honest breakage, because it
would look fixed.
"""
import ast
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "digitalmodel", "src")
sys.path.insert(0, HERE)
from check_skill_imports import (DOTTED, FROM_IMPORT, SKILLS, module_file, resolve)  # noqa: E402


def index_source():
    """symbol -> [dotted module paths defining it];  module basename -> [dotted]."""
    symbols, modules = defaultdict(list), defaultdict(list)
    root = os.path.abspath(SRC)
    for dirpath, _, files in os.walk(root):
        if "__pycache__" in dirpath:
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)          # root IS src/; do not include it
            dotted = "digitalmodel." + rel[:-3].replace(os.sep, ".")
            dotted = dotted.replace("digitalmodel.digitalmodel.", "digitalmodel.", 1)
            if dotted.endswith(".__init__"):
                dotted = dotted[: -len(".__init__")]
            modules[dotted.rsplit(".", 1)[-1]].append(dotted)
            try:
                tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
            except (OSError, SyntaxError):
                continue
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols[node.name].append(dotted)
    return symbols, modules


def collect_broken():
    out = defaultdict(list)
    for dirpath, _, files in os.walk(SKILLS):
        for fn in files:
            if fn != "SKILL.md":
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            refs = set(DOTTED.findall(text))
            for mod, syms in FROM_IMPORT.findall(text):
                for s in [x.strip() for x in syms.split(",") if x.strip()]:
                    refs.add(f"{mod}.{s}")
            skill = os.path.relpath(dirpath, SKILLS)
            for r in sorted(refs):
                ok, _ = resolve(r)
                if not ok:
                    out[skill].append(r)
    return out


def main():
    symbols, modules = index_source()
    broken = collect_broken()

    verdicts = defaultdict(list)
    for skill in sorted(broken):
        for ref in broken[skill]:
            last = ref.rsplit(".", 1)[-1]
            if last in symbols:
                verdicts["REPOINT"].append((skill, ref, f"{symbols[last][0]}.{last}"
                                            + (f"  (+{len(symbols[last])-1} more)" if len(symbols[last]) > 1 else "")))
            elif last in modules:
                verdicts["REPOINT"].append((skill, ref, modules[last][0] + "  [module]"))
            else:
                verdicts["NO-CANDIDATE"].append((skill, ref, ""))

    per_skill = defaultdict(lambda: [0, 0])
    for kind, rows in verdicts.items():
        for skill, _, _ in rows:
            per_skill[skill][0 if kind == "REPOINT" else 1] += 1

    tot_r = len(verdicts["REPOINT"])
    tot_n = len(verdicts["NO-CANDIDATE"])
    print(f"{tot_r + tot_n} unresolved paths across {len(broken)} skills\n")
    print(f"  REPOINT       {tot_r:4d}   a real target of that name exists")
    print(f"  NO-CANDIDATE  {tot_n:4d}   nothing plausible in the source tree\n")

    print(f"{'skill':44s} {'repoint':>8s} {'none':>6s}  verdict")
    print("-" * 78)
    for skill in sorted(per_skill, key=lambda s: (-per_skill[s][1], s)):
        r, n = per_skill[skill]
        v = "DELETE / reference-only" if r == 0 else ("mostly repointable" if n == 0 else "mixed")
        print(f"{skill:44s} {r:8d} {n:6d}  {v}")

    if os.environ.get("ACE_TRIAGE_VERBOSE"):
        for kind in ("REPOINT", "NO-CANDIDATE"):
            print(f"\n=== {kind} ===")
            for skill, ref, target in verdicts[kind]:
                print(f"  {skill}\n      {ref}" + (f"\n        -> {target}" if target else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
