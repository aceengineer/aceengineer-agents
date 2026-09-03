# Roadmap

`0.1.0` is a working skeleton: the marketplace resolves, two plugins install, the
orchestrator routes to a real specialist backed by 60 vendored skills. What is
below is not built.

## Blocking a first paid install

| # | Item | Why it blocks |
|---|---|---|
| 1 | **GitHub org `aceengineer`** | Repos live under the personal `vamseeachanta` account. The install command in the README is aspirational until the org exists. Commercial buyers check this. |
| 2 | **Copyright assignment** | The company licenses content the individual owns. See `NOTICE.md`. |
| 3 | **Corpus exposure decision** | `workspace-hub` is public and unlicensed. Either privatise the corpus or price the orchestration rather than the text. See `NOTICE.md`. |
| 4 | **L3 gate hook** | Until a hook can reject an unverified deliverable, "no result leaves unverified" is a prompt, not a guarantee — and the guarantee is what is being sold. |
| 5 | **Eval suite** (`claude plugin eval`) | No reliability claim survives a technical buyer without one. Seed it from closed engagements with known-correct answers. |

## Next specialists

- **`ace-standards`** — API / DNV / ABS / ISO clause retrieval with edition
  discipline. Backed by the `llm-wiki` standards corpus, served through
  retrieval; the corpus itself is never vendored. Highest-leverage second
  plugin: every other specialist depends on getting the edition right.
- **`ace-knowledge`** — client document ingestion, built on
  `raw-to-knowledge-playbook` (already dual-licensed, already carries
  `AUTHORING-STANDARD.md` and `adversarial-verify-loop`). Natural land-and-expand
  offering: ingest the client's archive, then analyse against it.

## Housekeeping found during the 0.1.0 build

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
