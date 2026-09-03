---
name: independent-recompute
description: >
  Independent closed-form oracle for lazy-wave riser geometry — recompute
  hang-off bend radius, segment arc lengths, horizontal offsets, total suspended
  length and end forces without touching the solver under test. Use when
  verifying a lazy-wave or catenary riser result, when a claimed number needs an
  independent route before release, or when building the reproducer the
  AceEngineer verification gate requires. Pinned by 4 historical solver runs.
license: LicenseRef-AceEngineer-Commercial
metadata:
  version: "0.1"
  role: verification-oracle
  reference: 4 de-identified historical runs, 72 values, agreement to 1e-9 rel
---

# independent-recompute

## What this is for

The verifier's first attack is *"recompute the result to one significant figure
by an independent route."* Without a tool, that instruction produces an estimate
the verifier talks itself into. This gives it a real second route.

**Independence is the property that makes it worth anything.** This oracle does
not import the digitalmodel solver, does not call `OrcFxAPI`, and does not read
a `.sim` file. It implements the geometry from first principles against the
invariants documented in the reference fixture. If it agreed by construction,
agreement would carry no information.

## Verify a claimed result

```bash
scripts/lazy_wave_oracle.py \
  --hangoff-angle 8 --vertical-distance 4000 \
  --sag-bend-elevation 1200 --hog-bend-above-seabed 1500 \
  --weight-without-buoyancy 2456.695439714344 \
  --weight-with-buoyancy -2456.695439714344 \
  --check total_S=6245.264141705511 \
  --check hangoff_bend_radius=452.68646126508355
```

```
  AGREE    total_S: 6245.264141705511  (oracle 6245.264141705511, dev 0.00e+00)
verdict: AGREE — an independent route reproduces the claim
```

Exit `0` agreement · `1` disagreement · `2` refused or bad input.

**This command is the reproducer.** Record it verbatim in the verdict's
`reproducer` field — it is re-runnable by the client, by a reviewer, and by you
against the next fix.

## Confirm the oracle itself before trusting it

```bash
scripts/lazy_wave_oracle.py --self-test
```

Reproduces 4 historical solver runs (72 values) to `1e-9` relative. An oracle
that has not been checked is just a second opinion.

## What it computes

`hangoff_d` · `hangoff_bend_radius` · `buoyancy_to_hog_R` · per-segment `_d`,
`_S`, `_X` for all five segments · `total_S` · `total_X` · `Fh` · `Fv`.

Invariants asserted on every call:

1. `d_hangoff = vertical_distance - sag_bend_elevation`
2. `R = d_hangoff · cos(90−q) / (1 − cos(90−q))` — derived, never supplied
3. `d1 − d2 − d3 + d4 + d5 = vertical_distance` — closure, checked to `1e-6`

A closure failure raises rather than returning a number. An oracle that returns
a plausible wrong answer is worse than one that stops.

## Where it refuses

`weight_with_buoyancy >= 0` — net-downward configurations. The historical sweep
exercised only net-buoyant cases, so that regime is *untested legacy behaviour,
not validated behaviour*. The oracle exits `2` and produces nothing.

Treat a refusal as a finding about the **case**, not a limitation of the tool:
if a specialist produced a number there, ask what validated it, because this
oracle will not.

## Scope

Lazy-wave and simple catenary geometry only. It says nothing about dynamics,
fatigue, VIV, clashing, or soil interaction. Silence from this oracle on those
is not a PASS — reach for a different route and say which one you used.
