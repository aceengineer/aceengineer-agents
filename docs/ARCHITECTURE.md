# Architecture

## Shape

```
client request
      │
      ▼
┌─────────────────────┐
│  ace-engineer       │  general agent — the only agent the client talks to
│  (orchestrator)     │  intake → route → verify → deliver
└──────┬──────────────┘
       │ routes to
       ├──────────────► orcaflex-specialist      (ace-marine-dynamics)  ✅ built
       ├──────────────► ace-standards            (ace-standards)        ✅ built
       └──────────────► ace-knowledge            (ace-knowledge)        ⬜ not built
       │
       │ every result, without exception
       ▼
┌─────────────────────┐
│ ace-independent-    │  fresh context, producer's reasoning withheld,
│ verifier            │  instructed to refute, builds runnable reproducers
└──────┬──────────────┘
       │ PASS
       ▼
   deliverable (6 sections, verification record mandatory)
```

## Why the gate is the architecture, not a feature

Skills are copyable. A competitor can write mooring skills; a client's in-house
team can wrap an LLM around OrcaFlex. What is not trivially copyable is a chain
that *cannot* emit an unverified number.

The design constraints follow from that:

- **The verifier runs in a fresh context.** If it inherits the producer's
  reasoning, it converges on the producer's conclusion.
- **The verifier is instructed to refute, not to review.** "Looks correct" is not
  a verification outcome and is rejected as a verdict.
- **Fixes are gated on the verifier's own reproducer**, not on inspection. A fix
  narrower than the named defect class is not accepted.
- **The specialist cannot deliver.** Specialists have no route to the client;
  only the orchestrator delivers, and it carries the gate.

Basis: on this practice's record, self-review returns MINOR where independent
review returns MAJOR, repeatedly. The pattern is drawn from
`raw-to-knowledge-playbook/skills/adversarial-verify-loop`.

## Enforcement level

| Level | Mechanism | Status |
|---|---|---|
| L1 | Orchestrator prompt states the gate is non-negotiable | ✅ |
| L2 | Specialists have no client-facing route; the verifier's verdict is structured | ✅ |
| L3 | A `PreToolUse` hook rejects a delivery lacking a verification record | ✅ |

L1 and L2 are prompt- and structure-level and can in principle be talked around.
**L3 is what makes the claim contractual.** `plugins/ace-engineer/hooks/hooks.json`
runs `scripts/verification_gate.py` before every `Write` and `Edit`.

A write is treated as a deliverable when its path sits under `deliverables/` or
its content carries `<!-- ace:deliverable -->`. It is denied unless all of:

1. a `## Verification record` heading is present;
2. the record carries `ace:verdict: <path>`;
3. that file exists, parses, reads `"verdict": "PASS"`, and has a non-empty
   `attempted` list.

The verifier writes that artifact to `.ace/verdicts/<slug>.json`. The gate fails
**closed** on a missing or failing verdict and **open** on its own internal
errors — a broken gate must never block ordinary work, but a missing
verification must always block a deliverable.

Behaviour is pinned by `tests/test_verification_gate.py` (9 cases: every deny
path, the single allow path, and malformed input).

### The obvious hole, stated plainly

An agent that never writes the marker and never writes under `deliverables/`
is not gated. The hook raises the cost of bypassing the gate from "ignore a
sentence in a prompt" to "deliberately mislabel a deliverable", which is the
realistic ceiling for a client-side control. Contractual assurance comes from
this plus the audit trail in `.ace/verdicts/`, not from the hook alone.

## Skill sourcing

Skills are **vendored, not referenced**. A plugin installed on a client machine
cannot reach `workspace-hub`, so the corpus is copied in by
`scripts/sync-skills.sh`, which records the source commit and a tree hash.
`--verify` asserts a rebuild is byte-identical, so drift between the shipped
plugin and the internal corpus is detectable rather than assumed.

## Repository boundaries

| Repo | Role |
|---|---|
| `aceengineer-agents` (this) | The **product**: marketplace + plugins. Client-installable. |
| `workspace-hub` | Source of truth for the skill corpus. Internal. |
| `aceengineer-strategy` | The **commercial plan**: pricing, packaging, go-to-market. |
| `aceengineer-admin` | Downstream ops once it sells: licence invoicing. Never the product. |
| `llm-wiki` | Standards corpus behind `ace-standards`. **Referenced by path, never vendored** — see below. |
| `llm-wiki-*` (client wikis) | Per-client knowledge. **Never vendored.** Served through an agent, never shipped. |

The last line is a hard boundary. Client corpora — Sonardyne, DORIS, Risers
Intl, HD — sit behind the agent. A plugin that ships one client's knowledge to
another client's machine is a breach, not a bug.


## Standards corpus: referenced, not vendored

`ace-standards` is the one plugin that ships **no corpus at all**. It declares a
required `standards_corpus_path` user config and reads the corpus from the
client's own licensed clone, resolved in order: `--corpus`,
`$ACE_STANDARDS_CORPUS`, `$CLAUDE_PLUGIN_OPTION_STANDARDS_CORPUS_PATH`.

Three reasons this differs from the marine-offshore skills, which *are* vendored:

1. **Licence.** The skill corpus is our own authored content. The standards
   corpus derives from third-party publisher documents; shipping it would
   distribute derived material we have no right to redistribute.
2. **The vendor-PDF firewall.** The corpus is metadata-first by construction —
   publisher, document id, revision year, authored summary — and holds no clause
   text, tables or figures. `standards-lookup` reads **frontmatter only** and
   prints metadata, making the firewall mechanical rather than advisory. Raw
   vendor PDFs stay on the private mount and are never touched.
3. **Failure mode.** With no corpus, the agent returns exit code `2` and stops.
   It does not fall back to recollection. Recollection of editions is precisely
   the thing that is unreliable, which is why the corpus exists.

`api-rp-2sk` resolving to revision `3e-2005-r2008` rather than "API RP 2SK" is
the whole product of this plugin. Criteria move between editions; a criterion
applied from the wrong edition still passes review because the clause number
resolves and the method looks standard.


## Arming the verifier

A verifier instructed to "recompute by an independent route" with no tool to do
it produces an estimate it talks itself into. The instruction is only as good as
the second route behind it.

`independent-recompute` (in `ace-marine-dynamics/authored-skills/`) is that
route for lazy-wave and catenary geometry. Its value rests entirely on one
property:

> It does not import the solver, does not call `OrcFxAPI`, and does not read a
> `.sim`. It implements the geometry from first principles against documented
> invariants, and is pinned by 4 historical solver runs it had no part in
> producing.

If it shared code with the thing it checks, agreement would carry no
information. Independence *is* the mechanism.

Three properties matter more than coverage:

1. **It self-tests.** `--self-test` reproduces 72 reference values to `1e-9`.
   An unchecked oracle is a second opinion, not a verification.
2. **It refuses outside its validated regime.** Net-downward configurations were
   never exercised by the historical sweep, so it exits `2` and produces
   nothing. A tool that returns a plausible number outside its validation is
   more dangerous than one that stops.
3. **Its invocation is the reproducer.** `--check key=value` is re-runnable by
   the client, by a reviewer, and by the verifier against the next fix — which
   is what makes "a fix is accepted when the reproducer passes" enforceable
   rather than aspirational.

Coverage is deliberately narrow: lazy-wave geometry only. The skill says
explicitly that silence on dynamics, fatigue, VIV or clashing is **not** a PASS.
An oracle that pretended to broad coverage would launder unverified results.

## Vendored vs authored skills

`plugins/ace-marine-dynamics/` carries both, and the distinction is structural,
not conventional:

| Directory | Owner | Lifecycle |
|---|---|---|
| `skills/` | `scripts/sync-skills.sh` | Wiped and rebuilt on every sync; hand edits are lost by design |
| `authored-skills/` | This repo | Declared via `plugin.json` `"skills"`, never touched by the sync |

Claude Code merges both into one skill namespace, so the split costs nothing at
runtime and removes a whole class of "the sync ate my work" failure.
