#!/usr/bin/env python3
"""Mark skills whose documented API does not exist (#267, population 3).

For every upstream SKILL.md still carrying unresolvable digitalmodel paths,
insert a warning the reader cannot miss and an `ace:known-missing` marker
listing exactly which paths are fiction.

Annotates rather than deletes, deliberately. The engineering content in these
skills -- method, conventions, what to watch for -- is sound and was useful in a
real engagement; only the imports are absent. Deleting code blocks wholesale
risks destroying the method along with the fiction, and cannot be recovered from
the vendored copy. A reader who sees the warning cannot act on the fiction, which
is the actual requirement.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
from check_skill_imports import DOTTED, FROM_IMPORT, KNOWN_MISSING, resolve  # noqa: E402

UPSTREAM = os.path.join(HERE, "..", "..", "workspace-hub",
                        ".claude", "skills", "engineering", "marine-offshore")

BANNER = "<!-- ace:api-missing-warning -->"


def unresolved_in(text):
    ack = set()
    for m in KNOWN_MISSING.findall(text):
        ack.update(x.strip() for x in m.split(",") if x.strip())
    refs = set(DOTTED.findall(text))
    for mod, syms in FROM_IMPORT.findall(text):
        for s in [x.strip() for x in syms.split(",") if x.strip()]:
            refs.add(f"{mod}.{s}")
    return sorted(r for r in refs - ack if not resolve(r)[0])


def main():
    apply = "--apply" in sys.argv
    touched = 0
    for dirpath, _, files in os.walk(UPSTREAM):
        if "_archive" in dirpath:
            continue
        for fn in files:
            if fn != "SKILL.md":
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            if BANNER in text:
                continue
            missing = unresolved_in(text)
            if not missing:
                continue

            rel = os.path.relpath(path, UPSTREAM)
            modules = sorted({m for m in missing if m.rsplit(".", 1)[-1][:1].islower()})
            block = (
                f"\n{BANNER}\n"
                "> [!WARNING]\n"
                "> **Part of the Python API documented below does not exist in\n"
                "> `digitalmodel`.** These snippets are a *specification* of intended\n"
                "> capability, not runnable code. Do not import them, and do not report\n"
                "> a result obtained by pretending they ran.\n"
                ">\n"
                "> Absent as of this revision:\n"
                + "".join(f">   - `{m}`\n" for m in missing[:12])
                + (f">   - …and {len(missing) - 12} more\n" if len(missing) > 12 else "")
                + ">\n"
                "> The surrounding engineering content — method, conventions, what to\n"
                "> watch for — is unaffected and remains usable. Tracked in\n"
                "> aceengineer-strategy#267.\n\n"
                "<!-- ace:known-missing: " + ", ".join(missing) + " -->\n"
            )

            # after the frontmatter, before the first body heading
            m = re.match(r"^---\n.*?\n---\n", text, re.S)
            pos = m.end() if m else 0
            out = text[:pos] + block + text[pos:]

            print(f"  {rel}   ({len(missing)} absent, {len(modules)} module(s))")
            touched += 1
            if apply:
                open(path, "w", encoding="utf-8").write(out)

    print(f"\n{'annotated' if apply else 'would annotate'} {touched} skill(s)")
    if not apply:
        print("(dry run -- pass --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
