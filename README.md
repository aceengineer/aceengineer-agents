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
/plugin install ace-standards@aceengineer
```

`ace-standards` requires a licensed standards corpus. Point it at your clone:

```bash
/plugin configure ace-standards@aceengineer     # sets standards_corpus_path
```

Then, in any project:

```
/ace 100-yr extreme mooring check on the FPSO, API RP 2SK 3rd ed
```

## What is in here

| Plugin | Contents |
|---|---|
| **ace-engineer** | `ace-engineer` orchestrator, `ace-independent-verifier`, `engagement-intake` skill, `/ace` command |
| **ace-marine-dynamics** | `orcaflex-specialist` + 60 vendored marine-offshore skills — mooring, riser, VIV, fatigue, diffraction, hydrodynamics, ship dynamics, wave theory — plus `independent-recompute`, the verifier's closed-form oracle |
| **ace-standards** | `ace-standards` + `standards-lookup` over 354 corpus pages — resolves governing document, publisher and **edition**. Metadata only; never reproduces clause text. |

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

**It is enforced by a hook, not by a prompt.** A `PreToolUse` hook in
`ace-engineer` rejects any write to `deliverables/` — or any file marked
`<!-- ace:deliverable -->` — whose verification record does not cite a verdict
file that exists on disk, reads `PASS`, and records what was attempted to refute
it. Behaviour is covered by `tests/test_verification_gate.py`.

The verifier is also given something to verify *with*. `independent-recompute`
is a closed-form lazy-wave oracle that shares no code with the solver under test
and reproduces 4 historical solver runs — 72 values — to `1e-9`. Its `--check`
invocation is the runnable reproducer the verdict records.

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

Do not hand-edit vendored skills — edit upstream and re-sync. Skills authored in
this repo live in `authored-skills/`, declared separately in `plugin.json`, and
are never in the sync's blast radius.

## Tests

```bash
./tests/run_all.sh
```

Gate behaviour · oracle vs historical runs · byte-identical skill rebuild ·
manifest validation. No network, no licences, no solver.

## Status

`0.3.0` — three plugins, gate enforced in a hook, verifier armed with an independent oracle. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design and
[`docs/ROADMAP.md`](docs/ROADMAP.md) for what is not built yet (`ace-knowledge`,
the `claude plugin eval` suite, and the org/licensing preconditions).

## Licence

Commercial. See [`LICENSE.md`](LICENSE.md).

---
Achanta AceEngineer Inc. · vamsee.achanta@aceengineer.com
