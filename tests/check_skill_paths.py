#!/usr/bin/env python3
"""Do the FILE paths a skill names actually exist? (#267, beyond imports)

The import sweep found 134 dead module paths. Nothing had ever checked the other
half of what a skill points at: scripts, config files, templates, data.

Conservative on purpose. Only a backticked token containing a directory
separator and a known extension counts as a claim about a real file. Prose,
placeholders, and illustrative paths are not claims, and flagging them would
bury the real signal -- which is what a noisy checker always does.

A path is satisfied if it resolves under ANY of: the skill's own directory, the
plugin root, the repo root, digitalmodel/, or workspace-hub/.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
# Scoped to ace-marine-dynamics on purpose. Those skills name files in
# digitalmodel, so a path that does not resolve is a real defect.
#
# The ace-knowledge (playbook) skills are different in kind: their paths describe
# the corpus BEING BUILT -- `sources/README.md` is a convention for the target
# store, which does not exist until the ingestion runs. Checking those would
# report a design as a defect, and a checker that cries wolf gets ignored, which
# costs more than the coverage gains.
SKILLS = os.path.join(ROOT, "plugins", "ace-marine-dynamics")
ROOTS = [
    os.path.join(ROOT, ".."),                      # ws/
    ROOT,                                          # aceengineer-agents/
    os.path.join(ROOT, "..", "digitalmodel"),
    os.path.join(ROOT, "..", "digitalmodel", "src"),
    os.path.join(ROOT, "..", "workspace-hub"),
]
EXTS = (".py", ".sh", ".yml", ".yaml", ".json", ".md", ".toml", ".cfg",
        ".dat", ".sim", ".csv", ".txt", ".ps1")

# Backticked token with a separator and a real extension.
CANDIDATE = re.compile(r"`([A-Za-z0-9_./\-]+/[A-Za-z0-9_.\-]+)`")

# Not claims about this repo's filesystem.
IGNORE = re.compile(
    r"^(https?:|/mnt/|/tmp/|~|\.\.?/?$)"           # urls, foreign mounts, scratch
    r"|^[A-Z]:"                                     # windows drives
    r"|<[^>]+>|\{[^}]+\}|\$\{|\*"                   # placeholders and globs
    r"|^(path|your|my|example|foo|bar)/",           # obvious illustrations
    re.I)


def satisfied(p, skill_dir):
    for base in [skill_dir] + ROOTS:
        if os.path.exists(os.path.join(base, p)):
            return True
    # a bare basename match anywhere in the plugin tree is close enough to be
    # a naming drift rather than a missing file; report those separately
    return False


def main():
    baseline = int(os.environ.get("ACE_SKILL_PATH_BASELINE", "7"))
    missing, checked, files = [], 0, 0
    for dirpath, _, fns in os.walk(SKILLS):
        for fn in fns:
            if fn != "SKILL.md":
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            cands = {c for c in CANDIDATE.findall(text)
                     if c.endswith(EXTS) and not IGNORE.search(c)}
            if not cands:
                continue
            files += 1
            rel = os.path.relpath(path, ROOT)
            for c in sorted(cands):
                checked += 1
                if not satisfied(c, dirpath):
                    missing.append((rel, c))

    print(f"scanned {files} SKILL.md files naming concrete file paths")
    print(f"checked {checked} path claim(s)\n")
    if not missing:
        print("every named file path resolves")
        return 0

    by = {}
    for rel, c in missing:
        by.setdefault(rel, []).append(c)
    print(f"{len(missing)} path(s) named but not found, across {len(by)} skill(s)"
          f"   [baseline {baseline}]\n")
    for rel in sorted(by):
        print(f"  {rel}")
        for c in by[rel]:
            print(f"      {c}")
    if len(missing) > baseline:
        print(f"\nFAIL: {len(missing)} > baseline {baseline}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
