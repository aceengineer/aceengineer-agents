#!/usr/bin/env python3
"""Lift the OrcaWave skills' intended-but-unbuilt API into digitalmodel specs.

The OrcaWave skills document an API that does not exist (#267). The prose --
when to use it, what to watch for -- is sound engineering. The code blocks are a
specification of capability nobody built.

A specification belongs with the codebase that would implement it, not in an
agent skill corpus where an agent may act on it as though it runs. This lifts the
code blocks into digitalmodel/docs/domains/orcawave/intended-api/ verbatim, with provenance, so
they become a build target instead of a trap.

Verbatim on purpose: these are somebody's intent about an API surface, and
paraphrasing intent loses the part that mattered.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
from check_skill_imports import KNOWN_MISSING  # noqa: E402

SKILLS = os.path.join(HERE, "..", "..", "workspace-hub",
                      ".claude", "skills", "engineering", "marine-offshore", "orcawave")
OUT = os.path.join(HERE, "..", "..", "digitalmodel", "docs", "domains", "orcawave", "intended-api")

NAMES = ["analysis", "aqwa-benchmark", "damping-sweep", "mesh-generation",
         "multi-body", "qtf-analysis", "to-orcaflex"]

BLOCK = re.compile(r"(#{2,4}\s+([^\n]+)\n+)?```python\n(.*?)```", re.S)


def main():
    os.makedirs(OUT, exist_ok=True)
    index = []
    for name in NAMES:
        src = os.path.join(SKILLS, name, "SKILL.md")
        if not os.path.isfile(src):
            print(f"  SKIP {name}: no SKILL.md")
            continue
        text = open(src, encoding="utf-8", errors="replace").read()

        missing = []
        for m in KNOWN_MISSING.findall(text):
            missing.extend(x.strip() for x in m.split(",") if x.strip())
        missing = sorted(set(missing))

        title = "OrcaWave " + name.replace("-", " ")
        blocks = [(h.strip() if h else "Snippet", code.rstrip())
                  for _, h, code in BLOCK.findall(text) if "digitalmodel" in code]
        if not blocks:
            print(f"  SKIP {name}: no digitalmodel snippets")
            continue

        doc = [
            f"# Specification: {title}",
            "",
            "> **Status: NOT IMPLEMENTED.** This is a specification of intended",
            "> capability, lifted verbatim from the AceEngineer marine-offshore skill",
            f"> corpus (`engineering/marine-offshore/orcawave/{name}`). None of the",
            "> API below exists in `digitalmodel` today.",
            ">",
            "> It lives here rather than in the skill corpus because a specification",
            "> belongs with the codebase that would implement it — in a skill corpus an",
            "> agent may act on it as though it runs. Tracked in",
            "> `aceengineer-strategy#267`.",
            "",
            "## Absent API surface",
            "",
        ]
        doc += [f"- `{m}`" for m in missing] or ["- (none recorded)"]
        doc += ["", "## Intended usage (verbatim from the skill)", ""]
        for heading, code in blocks:
            doc += [f"### {heading}", "", "```python", code, "```", ""]
        doc += [
            "## Notes for an implementer",
            "",
            "- The snippets are **intent, not contract**. Names and signatures were",
            "  written against an API that was never built, so treat them as a starting",
            "  point rather than a spec to match exactly.",
            "- The engineering content that surrounded them — when to use this analysis,",
            "  what to watch for — stays in the skill corpus and is unaffected.",
            "- If a capability here is built, remove it from the skill's",
            "  `ace:known-missing` marker so the corpus check reflects reality.",
            "",
        ]
        dest = os.path.join(OUT, f"{name}.md")
        open(dest, "w", encoding="utf-8").write("\n".join(doc))
        index.append((name, title, len(blocks), len(missing)))
        print(f"  {name}.md   {len(blocks)} snippet(s), {len(missing)} absent path(s)")

    idx = [
        "# OrcaWave — specifications for unbuilt capability",
        "",
        "Seven analysis capabilities documented in the AceEngineer marine-offshore",
        "skill corpus against an API that does not exist in `digitalmodel`.",
        "",
        "Discovered when a real engagement followed one of these skills and found the",
        "import missing (`aceengineer-strategy#262`, then `#267`). A sweep showed 134",
        "documented paths across 28 skills did not resolve; most were stale after the",
        "`solvers/` and `hydrodynamics/` reorganisation and were repointed. These seven",
        "were not drift — the capability was never built.",
        "",
        "| Spec | Snippets | Absent paths |",
        "|---|---|---|",
    ]
    idx += [f"| [{t}]({n}.md) | {b} | {m} |" for n, t, b, m in index]
    idx += [
        "",
        "## Why these are here and not in the skill corpus",
        "",
        "A skill that documents a non-existent API is worse than no skill: it reads as",
        "an asset, survives review, and fails at the moment an agent depends on it.",
        "Moving the specification to the repository that would implement it turns a",
        "trap into a build target.",
        "",
        "The skills keep their engineering content and now carry an explicit warning",
        "plus an `ace:known-missing` marker, so the absence is declared rather than",
        "silently carried.",
        "",
    ]
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("\n".join(idx))
    print(f"\nwrote {len(index)} spec(s) + README to docs/domains/orcawave/intended-api/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
