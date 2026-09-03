# End-to-end run — findings (issue #262)

First real engagement through the chain: intake → specialist → independent
verification. Run 2026-09-03 in a headless session with the plugins loaded, so
the hook was live.

## Outcome

| Stage | Result |
|---|---|
| Intake | ✅ Frame block produced. Refused to invent a standard or criterion; flagged missing weight units as load-bearing assumption A1 |
| Specialist | ✅ Result produced with full provenance — solver commit, file md5, exact commands |
| Verifier | ✅ Wrote its own independent check (3 routes) and **refuted the producer** |
| Verdict artifact | ❌ Not written — run truncated at the 900 s wall clock |
| Deliverable | ❌ Never reached |
| Gate deny path | ✅ Confirmed separately: blocked a deliverable with no verification record, and the agent refused to strip the marker to get around it |
| Gate admit path | ⬜ Still untested |

## MAJOR — the oracle's own `Fv` was wrong, and the chain caught it

`independent-recompute` reported `Fv = w·(S1 + R)`, matching the reference
fixture to 1e-9. Refuted by three routes that fitting cannot satisfy:

- global vertical force equilibrium → `Fv = w·S1 = 7,913,093 N`
- 4×10⁶-panel Simpson quadrature → geometry confirmed to 1e-10
- tangent identity `Fv/Fh = tan(90−q)`, fixed by the **input** angle → the old
  value implies a 7.025° declination where 8.000° was the input

**Root cause:** the geometry was *derived* from documented invariants and was
correct. `Fv` had no documented invariant, so it was *fitted* to the reference
numbers — and fitting to the artifact under test inherits its defects. The
fixture carries the same error from a legacy routine, so a fixture-only
self-test could never have caught it.

Fixed: `Fv = w·S1`, `T = w·(R + d1)`, plus a derived per-call assertion that the
force triangle reproduces the input declination. `Fv` excluded from the fixture
comparison by name.

## MAJOR — `catenary-riser` skill points at a solver that does not exist

`skills/catenary-riser/SKILL.md` documents
`digitalmodel.subsea.catenary.lazy_wave_catenary.LazyWaveCatenary`. That import
path does not exist. The nearest real class is **quarantined** — it returned
hardcoded fractions of water depth with buoyancy having no effect, and now
raises `NotImplementedError`. Following the skill as written fails to import.

## MAJOR — `LazyWaveSolver.vertical_force` is wrong upstream

`digitalmodel` computes `Fv = Fh + w·S`, while the same library's
general-catenary path uses `Fv = w·S`. Two contradictory definitions coexist.
Geometry is unaffected (forces are computed after the shape and feed nothing
back).

## Engineering findings the specialist raised unprompted

- **"Bend radius" is ambiguous.** The catenary parameter `a = H/w` is 452.7 m;
  the true radius of curvature *at the hang-off* is 23,372 m — a factor of 51.6.
  If the client meant an MBR check, the governing number is the latter.
- **"Declination" undefined.** Read from vertical (correct, and what the solver
  expects). From horizontal it would give 284,913 m — a factor of 629 — and
  nothing in the output would flag it.
- **Total suspended length is not robust.** A buoyancy ratio of 0.5 instead of
  the given 1.0 moves it by +442 m (~7%). Should not be issued as confirmed
  until the buoyancy-module data sheet is produced.

## Process finding

One static geometry check took **>15 minutes** of wall clock and did not finish.
The verification stage is the expensive part. This matters commercially and
should be measured before any turnaround time is promised.
