# Roadmap

Tracked in `aceengineer-strategy` (private) under
[#249 — Epic: AceEngineer agent product](https://github.com/vamseeachanta/aceengineer-strategy/issues/249).
Issue numbers below are in that repo.

`0.3.0`: the marketplace resolves, two plugins install, the
orchestrator routes to a real specialist backed by 60 vendored skills. What is
below is not built.

## Blocking a first paid install

| # | Item | Why it blocks |
|---|---|---|
| 1 | **Push to the `aceengineer` org** ([#254](https://github.com/vamseeachanta/aceengineer-strategy/issues/254)) | The org **already exists** with 4 repos and we hold admin — this is cheaper than first assessed. The README install command stays aspirational until the repo is pushed and reachable. |
| 2 | **Copyright assignment** ([#255](https://github.com/vamseeachanta/aceengineer-strategy/issues/255)) | The company licenses content the individual owns. See `NOTICE.md`. |
| 3 | **Corpus exposure decision** ([#256](https://github.com/vamseeachanta/aceengineer-strategy/issues/256)) | `workspace-hub` is public and unlicensed. Either privatise the corpus or price the orchestration rather than the text. Gates the public/private call in #254. See `NOTICE.md`. |
| ~~4~~ | ~~**L3 gate hook**~~ | ✅ Done in 0.2.0. `PreToolUse` hook + 9 behavioural tests. |
| 5 | **Eval suite** (`claude plugin eval`) ([#257](https://github.com/vamseeachanta/aceengineer-strategy/issues/257)) | No reliability claim survives a technical buyer without one. **Blocked, not skipped:** `claude plugin eval` reports *"currently in early access"* on this account and `eval init` produces nothing, and the `case.yaml` schema is absent from public docs — so authoring the suite now would be guessing at an undocumented gated format. Ground truth is already in hand (`authored-skills/independent-recompute/reference/`, 4 runs × 18 values); wrap it in cases as soon as access lands. |

## Next specialists

- ~~**`ace-standards`**~~ — ✅ Done in 0.2.0 ([#252](https://github.com/vamseeachanta/aceengineer-strategy/issues/252)). Edition-delta table tracked as [#259](https://github.com/vamseeachanta/aceengineer-strategy/issues/259). 354 corpus pages reachable by code
  id, publisher, subject or tag; returns publisher and revision; refuses to
  answer without a corpus. Still to add: an edition-delta table for the criteria
  that actually moved (API RP 2SK 2e→3e and similar), which is the part clients
  will pay attention to.
- **`ace-knowledge`** ([#260](https://github.com/vamseeachanta/aceengineer-strategy/issues/260)) — client document ingestion, built on
  `raw-to-knowledge-playbook` (already dual-licensed, already carries
  `AUTHORING-STANDARD.md` and `adversarial-verify-loop`). Natural land-and-expand
  offering: ingest the client's archive, then analyse against it.

## Housekeeping found during the 0.1.0 build

Tracked as [#261](https://github.com/vamseeachanta/aceengineer-strategy/issues/261).

- `digitalmodel/.claude/skills/` holds 20 macOS **Finder alias files** named
  `orcaflex-*` / `orcawave-*` pointing at `ws/.claude/skills/engineering/…`,
  which does not exist. They are not skills and resolve to nothing. Delete them
  or replace with real symlinks.
- `digitalmodel/.claude/skills/skills-catalog.json` is an empty stub whose
  `generated` field is `/mnt/local-analysis/digitalmodel` — produced on the Linux
  box, never regenerated on the Mac.
- `workspace-hub/.claude/agents/orcaflex-specialist.md` hard-codes
  `/mnt/local-analysis/workspace-hub/...`. The vendored copy in this repo has the
  absolute paths removed; upstream still has them.
- `aceengineer-strategy/.claude/agents/*.md` have no YAML frontmatter, so they
  are documents rather than loadable agents.


## Added in 0.3.0

- `independent-recompute` — closed-form lazy-wave oracle, 72 reference values
  reproduced to `1e-9`, wired into the verifier's first attack. Next: extend
  coverage to simple catenary and taut-leg mooring ([#258](https://github.com/vamseeachanta/aceengineer-strategy/issues/258)), which are the other two
  places a specialist result currently has no second route.
- `tests/run_all.sh` — gate behaviour, oracle self-test, byte-identical skill
  rebuild, manifest validation.
- `authored-skills/` split, so the vendoring sync can no longer delete
  repo-authored work.
