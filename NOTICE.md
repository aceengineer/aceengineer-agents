# Notice — provenance of the vendored skill corpus

The marine-offshore skill corpus in `plugins/ace-marine-dynamics/skills/` is
vendored from `github.com/vamseeachanta/workspace-hub`, path
`.claude/skills/engineering/marine-offshore`, by `scripts/sync-skills.sh`. The
source commit and a tree hash are recorded in
`plugins/ace-marine-dynamics/SKILLS-PROVENANCE.md`, and
`./scripts/sync-skills.sh --verify` asserts a byte-identical rebuild.

## The corpus is public, deliberately

The source repository is public. That is a decision, not an oversight: what is
licensed here is the orchestration, the independent-verification gate, the audit
trail it produces, and the maintenance behind them — not the skill text. Skills
are copyable; an assurance chain that cannot emit an unverified number is the
part that is not.

## Known limits of the corpus

Some skills document a `digitalmodel` API that does not exist. Those carry an
explicit warning and an `ace:known-missing` marker naming every absent path, and
their intended API is specified in `digitalmodel` under
`docs/domains/orcawave/intended-api/`. `tests/check_skill_imports.py` runs in
`tests/run_all.sh` and fails on any new unresolved path, so this cannot silently
get worse.

We would rather ship a corpus that tells you where it is thin than one that reads
as complete and fails when an agent depends on it.

## Third-party standards content

`ace-standards` ships **no corpus**. It reads a separately licensed standards
corpus from a path you configure, and resolves metadata only — publisher,
document identifier, revision — never clause text. See that plugin's skill
documentation for the boundary.
