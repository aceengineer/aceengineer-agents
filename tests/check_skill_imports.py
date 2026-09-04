#!/usr/bin/env python3
"""Do the module paths documented in the skill corpus actually resolve?

Found the hard way (#267): catenary-riser/SKILL.md documents
digitalmodel.subsea.catenary.lazy_wave_catenary.LazyWaveCatenary, which does not
exist -- and the nearest real class was quarantined for returning fabricated
geometry. A skill pointing at a missing module fails loudly; one pointing at a
quarantined module failed silently, with plausible numbers.

Resolution is STATIC -- against the source tree, not by importing. digitalmodel
cannot build an env on this machine, and a check that only runs where the env
works is a check that does not run.
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "plugins", "ace-marine-dynamics", "skills")
SRC = os.path.join(HERE, "..", "..", "digitalmodel", "src")

# digitalmodel.a.b.c  /  from digitalmodel.a.b import C
DOTTED = re.compile(r"\bdigitalmodel(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# Symbols only, on the SAME line -- a greedy \s class swallows following lines and
# inflates one bad reference into several bogus ones.
FROM_IMPORT = re.compile(r"from\s+(digitalmodel(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s+import\s+([A-Za-z_][A-Za-z0-9_, ]*)")


def module_file(dotted):
    """Return the file backing a dotted module path, or None."""
    rel = dotted.split(".")
    p = os.path.join(SRC, *rel)
    if os.path.isdir(p) and os.path.isfile(os.path.join(p, "__init__.py")):
        return os.path.join(p, "__init__.py")
    if os.path.isfile(p + ".py"):
        return p + ".py"
    return None


def defines(path, name):
    """Does this file define `name` at module level (class, def, or assignment)?"""
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except (OSError, SyntaxError):
        return False
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return True
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                if (a.asname or a.name.split(".")[0]) == name:
                    return True
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return True
    return False


def resolve(dotted):
    """(ok, detail) for a dotted path that may end in a module or a symbol."""
    if module_file(dotted):
        return True, "module"
    if "." in dotted:
        mod, _, sym = dotted.rpartition(".")
        f = module_file(mod)
        if f:
            return (True, f"symbol in {mod}") if defines(f, sym) else (False, f"module {mod} exists, but does not define {sym}")
    return False, "no such module"


def main():
    # Ratchet, not a cliff. 28 of 31 skills carrying digitalmodel references
    # document paths that do not resolve (#267). Failing the build outright
    # would just mean a permanently red build nobody reads. Instead the count
    # is pinned: it may go down, never up.
    baseline = int(os.environ.get("ACE_SKILL_IMPORT_BASELINE", "134"))

    if not os.path.isdir(SRC):
        print(f"SKIP: digitalmodel source not found at {SRC}")
        return 0

    broken, total_refs, files_with_refs = [], 0, 0
    for root, _, files in os.walk(SKILLS):
        for fn in files:
            if fn != "SKILL.md":
                continue
            path = os.path.join(root, fn)
            text = open(path, encoding="utf-8", errors="replace").read()

            refs = set(DOTTED.findall(text))
            for mod, syms in FROM_IMPORT.findall(text):
                for sym in [s.strip() for s in syms.split(",") if s.strip()]:
                    refs.add(f"{mod}.{sym}")
            if not refs:
                continue
            files_with_refs += 1
            rel = os.path.relpath(path, os.path.join(HERE, ".."))
            for r in sorted(refs):
                total_refs += 1
                ok, detail = resolve(r)
                if not ok:
                    broken.append((rel, r, detail))

    print(f"scanned {files_with_refs} SKILL.md files carrying digitalmodel references")
    print(f"checked {total_refs} documented module/symbol paths\n")
    if not broken:
        print("all documented paths resolve")
        return 0

    by_skill = {}
    for rel, r, detail in broken:
        by_skill.setdefault(rel, []).append((r, detail))
    print(f"{len(broken)} UNRESOLVED path(s) across {len(by_skill)} skill(s)"
          f"   [baseline {baseline}]\n")
    if os.environ.get("ACE_SKILL_IMPORT_VERBOSE"):
        for rel in sorted(by_skill):
            print(f"  {rel}")
            for r, detail in by_skill[rel]:
                print(f"      {r}\n          -> {detail}")
    else:
        for rel in sorted(by_skill):
            print(f"  {len(by_skill[rel]):3d}  {rel}")
        print("\n  (ACE_SKILL_IMPORT_VERBOSE=1 for every path)")

    if len(broken) > baseline:
        print(f"\nFAIL: regressed -- {len(broken)} unresolved vs baseline {baseline}")
        return 1
    if len(broken) < baseline:
        print(f"\nIMPROVED: {baseline} -> {len(broken)}. Lower ACE_SKILL_IMPORT_BASELINE to pin it.")
        return 0
    print(f"\nat baseline ({baseline}) -- tracked in #267, not yet fixed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
