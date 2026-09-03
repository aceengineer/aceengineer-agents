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
       ├──────────────► ace-standards            (ace-standards)        ⬜ not built
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
| L3 | A hook rejects a delivery lacking a verification record | ⬜ not built |

L1 and L2 are prompt- and structure-level and can in principle be talked around.
**L3 is what makes the claim contractual** and is the highest-value next build:
a `hooks/hooks.json` in `ace-engineer` that blocks a deliverable write when no
verifier verdict is present in the session.

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
| `llm-wiki-*` | Per-client knowledge. **Never vendored.** Served through an agent, never shipped. |

The last line is a hard boundary. Client corpora — Sonardyne, DORIS, Risers
Intl, HD — sit behind the agent. A plugin that ships one client's knowledge to
another client's machine is a breach, not a bug.
