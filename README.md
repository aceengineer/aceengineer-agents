# AceEngineer Agents

Offshore and marine engineering agents for Claude Code, maintained and managed by
**Achanta AceEngineer Inc.** (DBA AceEngineer).

A general agent takes the engagement; domain specialists do the analysis; an
independent verifier is told to refute the result before anything reaches a
client. The verification gate is the product.

## Install

```bash
/plugin marketplace add aceengineer/aceengineer-agents
/plugin install ace-engineer@aceengineer
/plugin install ace-marine-dynamics@aceengineer
```

Then, in any project:

```
/ace 100-yr extreme mooring check on the FPSO, API RP 2SK 3rd ed
```

## What is in here

| Plugin | Contents |
|---|---|
| **ace-engineer** | `ace-engineer` orchestrator, `ace-independent-verifier`, `engagement-intake` skill, `/ace` command |
| **ace-marine-dynamics** | `orcaflex-specialist` + 60 vendored marine-offshore skills — mooring, riser, VIV, fatigue, diffraction, hydrodynamics, ship dynamics, wave theory |

Install `ace-engineer` first. The specialists are written to run under it and do
not carry the verification gate themselves.

## The gate

No engineering result is released unverified. The orchestrator hands the
specialist's output to an independent verifier in a fresh context, with the
producer's reasoning withheld, and instructs it to refute. Findings return to the
specialist; a fix is accepted only when the verifier's own reproducer passes.

This is not a stylistic preference. On this practice's own record, a producer
reviewing its own work returns MINOR findings where an independent reviewer
returns MAJOR ones.

## Deliverable shape

Every output carries: **result** · **basis** (standard, edition, clause, method,
software version) · **inputs with sources** · **stated assumptions** ·
**verification record** · **limits**. A deliverable missing the verification
record is not an AceEngineer deliverable.

## Skills provenance

`ace-marine-dynamics/skills/` is vendored from AceEngineer's internal corpus by
`scripts/sync-skills.sh`, which records the source commit and a tree hash in
`SKILLS-PROVENANCE.md`. Rebuilds are verifiable:

```bash
./scripts/sync-skills.sh --verify
```

Do not hand-edit vendored skills — edit upstream and re-sync.

## Status

`0.1.0` — skeleton. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the
design and [`docs/ROADMAP.md`](docs/ROADMAP.md) for what is not built yet
(`ace-standards`, `ace-knowledge`, the eval suite, and hook-level enforcement of
the gate).

## Licence

Commercial. See [`LICENSE.md`](LICENSE.md).

---
Achanta AceEngineer Inc. · vamsee.achanta@aceengineer.com
