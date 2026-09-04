# Skill corpus triage (#267)

134 documented `digitalmodel` paths across 28 of the 31 skills that reference it
do not resolve. This is the triage of *why*, because the answer differs sharply
by family and so does the fix.

Run it yourself:

```bash
python3 tests/check_skill_imports.py      # the ratchet, pinned at 134
python3 tests/triage_skill_imports.py     # REPOINT vs NO-CANDIDATE
```

## Correction to the first reading

The initial sweep reported that `digitalmodel.aqwa` "does not exist". The *path*
does not — but **`digitalmodel.hydrodynamics.aqwa` does, with 11 modules**, and
`digitalmodel.solvers.orcaflex` likewise.

The corpus is **stale after a package reorganisation**, not fictional. That is a
materially better diagnosis and it changes the remedy: most of this is a rewrite,
not a rebuild.

## The three populations

| Family | Skills | Diagnosis | Fix |
|---|---|---|---|
| **OrcaFlex** | 12 | Stale paths. `digitalmodel.orcaflex.*` moved to `digitalmodel.solvers.orcaflex.*` | Mechanical prefix rewrite |
| **catenary-riser** | 1 | Wrong module names (`lazy_wave_catenary` vs the real `lazy_wave`), and it points at a **quarantined** class that returned fabricated geometry | Repoint by hand, carefully |
| **OrcaWave / AQWA** | 9 | Documents an API that was **never built**. Both `digitalmodel.orcawave` and `digitalmodel.solvers.orcawave` exist; neither has `qtf`, `mesh`, `multibody` or `converters` | Delete or mark reference-only |

## What a mechanical rewrite recovers

Applying the prefix moves the refactor implies:

```
digitalmodel.orcaflex.*    -> digitalmodel.solvers.orcaflex.*
digitalmodel.aqwa.*        -> digitalmodel.hydrodynamics.aqwa.*
digitalmodel.diffraction.* -> digitalmodel.hydrodynamics.diffraction.*
digitalmodel.orcawave.*    -> digitalmodel.solvers.orcawave.* | .hydrodynamics.bemrosetta.*
```

**46 of 134 (34%) resolve.** The OrcaFlex family drops out almost entirely,
which confirms the diagnosis for that population.

The remaining **88** concentrate in OrcaWave (46 across 6 skills),
`catenary-riser` (10), `signal-analysis` (6) and AQWA (6). Those are not path
drift — the named capability is absent from the source tree.

## The rule this establishes

A skill that documents a non-existent API is **worse than no skill**. It reads as
an asset, it survives review, and it fails at the moment an agent depends on it —
in the quarantined-class case, by returning fabricated numbers rather than an
error.

`tests/check_skill_imports.py` runs in `run_all.sh` as a ratchet so this cannot
silently get worse. Nothing enforced it before, which is how 134 accumulated.

## Commercial read

The engineering *content* of the corpus is real and was demonstrably useful in
the first end-to-end run (#262). The **code it tells an agent to call** is a
third stale and a third absent.

That is survivable, but it is not "60 expert skills" — and the claim should be
corrected in the positioning before a technical buyer corrects it for us. It
strengthens rather than weakens the decision in #256: price the orchestration and
the verification gate, not the skill text.
