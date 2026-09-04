# Lazy-wave riser — hang-off bend radius and total suspended length

Engagement: lazy-wave-verification · Issued 2026-09-04
Class: static geometry (configuration) — not strength, not fatigue, not extreme response

---

## Result

| Quantity | Value | Precision we stand behind |
|---|---|---|
| Hang-off bend radius (catenary parameter a = H/w) | **452.7 m** | **453 ± 33 m** |
| Total suspended length, hang-off to touchdown | **6245 m** | **6245 ± 100 m**, plus an unresolved ±440 m — see Limits L1 |

Supporting geometry: horizontal reach hang-off to TDP **3400.6 m**; buoyancy-module
coverage **1512.1 m** of arc, spanning elevations 750 m to 1500 m above seabed.
Hang-off tensions (units-dependent — see A1): Fh = **1.112 MN**, Fv = **7.913 MN**,
T = **7.991 MN**.

Two cautions attach to the headline numbers and are not optional reading:

- **"Bend radius" is ambiguous.** 452.7 m is the catenary parameter at the hang-off
  section — the quantity the named solver reports under that name, and the minimum
  radius of curvature on the line (at sag bend, hog bend and TDP). The *true radius
  of curvature at the hang-off point* is **23 372 m** (a·sec²82°). If the intent was an
  MBR check at the hang-off, the governing number is 23 372 m, a factor of 51.6 away.
  **Confirm which was meant.**
- **The total suspended length is not robust** to the buoyancy weight ratio as supplied
  (Limits L1). The bend radius is entirely insensitive to it and stands regardless.

Bit-reproducible arithmetic values, for re-running only: 452.6864612651 m and
6245.2641417055 m. We do not believe those digits.

## Basis

Closed-form five-segment inextensible catenary at constant horizontal tension,
closing on a flat seabed by construction. Sag bend, hog bend and TDP are points of
horizontal tangent. Two catenary radii apply: a_w = H/w on the bare segments (1, 2, 5)
and a_b = H/|w_b| on the buoyed segments (3, 4).

Hang-off radius is *derived* from the declination and the sag-bend drop, not supplied:

    theta = 90° − declination;  d1 = 4000 − 1200 = 2800 m
    a_w   = d1·cos(theta) / (1 − cos(theta))          [d = a(sec theta − 1)]
    S1    = a_w·tan(theta);  X1 = a_w·asinh(tan theta)

Per remaining segment of vertical span d: X = a·acosh(d/a + 1), S = a·sinh(X/a). The
split of vertical span across each buoyancy boundary is fixed by slope continuity
(d_bare/d_buoyed = a_bare/a_buoyed), not chosen. Closure d1 − d2 − d3 + d4 + d5 = 4000 m
is exact; the run reports residual 0.0 m.

Forces: Fh = w·a_w, Fv = w·S1, T = √(Fh²+Fv²) = w·(a_w+d1). The force triangle
reproduces the input declination exactly — atan(Fh/Fv) = 8.000000° — which is the
check that validates them.

Solver: `LazyWaveSolver`, `digitalmodel.marine_ops.marine_analysis.catenary`
(module v2.0.0; repo HEAD `bb922b9`; `lazy_wave.py` md5 `8c2a7717c2d065be52010be9b5085559`),
Python 3.13.14. No OrcaFlex or OrcaWave licence was used and none is required.

**One solver output was rejected and replaced.** `LazyWaveSolver` returns
`vertical_force` = 9 025 206 N (= w·(S1+a_w)), which is neither the vertical tension
component nor the total tension and implies a 7.025° declination against the stated
8.000° input. We report the correct Fv = w·S1 = 7 913 093 N, consistent with the same
library's general-catenary path. Geometry is unaffected: forces are computed after
the shape and feed nothing back into it. A re-runner will see 9.025 MN and should
expect the discrepancy.

## Inputs (with sources)

| Input | Value | Source |
|---|---|---|
| Vertical distance, hang-off to seabed | 4000 m | Client, REQUEST.md — no source document cited |
| Sag bend elevation above seabed | 1200 m | Client, REQUEST.md |
| Hog bend above seabed | 1500 m | Client, REQUEST.md |
| Hang-off declination | 8° | Client, REQUEST.md — convention not defined; see A6 |
| Weight without buoyancy, w | 2456.695439714344 | Client, REQUEST.md — **units not given**; see A1 |
| Weight with buoyancy, w_b | −2456.695439714344 | Client, REQUEST.md — **units not given**; see A1 and Limits L1 |
| Hang-off vertical span, d1 | 2800 m | Derived = 4000 − 1200 |
| Hang-off depth below MSL | 0.0 m | Assumed; inert — reporting datum only, never read by the solve |

Water density, pipe OD/WT, material grade, current profile and vessel offset are not
required by this construction and were not used.

## Assumptions

- **A1 — Weights are distributed submerged weight in N/m.** Not stated by the client.
  *Load-bearing for forces only.* Both requested numbers depend on the weights solely
  through the ratio |w_b|/w and are bit-identical when the pair is scaled by 0.001 or
  1000. Every force above scales linearly (×9.80665 if kgf/m, ×1000 if kN/m). N/m is
  the only self-consistent reading — at kgf/m the riser would be 2.5 t/m submerged with
  8000 tonnef at the hang-off, which is not credible. **Client should still confirm.**
- **A2 — Still water.** No current, no vessel offset; static equilibrium.
  *Unconservative for real offsets.*
- **A3 — Inextensible, torsionally free, zero bending stiffness.** The bend radius is
  the elastic-free catenary radius. *Slightly unconservative at the hang-off* — a real
  bend stiffener increases the local radius.
- **A4 — Flat horizontal seabed** 4000 m below the hang-off.
- **A5 — No standard governs this result.** No standard, edition or acceptance
  criterion was named. This is a geometry confirmation, not a code check; **no pass/fail
  is asserted.**
- **A6 — The 8° declination is measured from the vertical.** Not defined by the client.
  This is the normal riser hang-off convention and what the solver's API expects.
  *Load-bearing and unflagged if wrong:* read from the horizontal, the bend radius
  becomes 284 913 m (×629) and the suspended length 99 908 m, and nothing in the output
  would signal the error. We judge the from-vertical reading near-certain but it remains
  an interpretation. **Confirm in writing.**

## Verification record

ace:verdict: .ace/verdicts/lazy-wave-geometry.json

Verdict **PASS**, 1 round, 0 findings, verified 2026-09-04T14:34:05Z by an independent
verifier instructed to refute. Eight attacks were attempted; none refuted either
requested number:

- **Independent first-principles oracle** (imports neither the solver nor OrcFxAPI):
  agrees on both — 452.68646126508 m and 6245.26414170551 m, deviations being the
  rounding of the checked values.
- **Numerical quadrature** of dS = cosh(x/a)dx over 4×10⁶ panels, using no closed-form
  arc length: total agrees to 1×10⁻¹⁰ m. The result is not an artifact of the closed form.
- **Unit invariance (A1):** both numbers identical under ×1, ×1/9.80665, ×0.0685, ×10⁶.
  Confirms the unit assumption reaches the forces only.
- **Declination convention (A6):** confirmed load-bearing (×630 and ×16) and correctly
  declared — a stated dependency, not a defect.
- **Weight-pair perturbation** through 1e-12 to 10%: no knife edge. a_w exactly
  invariant; total_S degrades smoothly (−0.70% for a 10% error). Closure residual
  0.000e+00 throughout.
- **Angle tolerance sweep** 7.0–9.0°: substantiates the stated bands (453 ± 33 m,
  6245 ± 97 m at ±0.5°). Both numbers are far more sensitive to the rounded input angle
  than to any modelling choice tested.
- **Forces by two routes independent of the catenary closed form** (global vertical
  equilibrium; the tangent identity Fv/Fh = tan 82°): both confirm our Fv = 7 913 093 N
  and refute the solver's 9 025 206 N, vindicating the substitution recorded under Basis.
- **Geometric closure:** residual 0.000e+00 m in all 19 configurations run.

Reproducer:

```
plugins/ace-marine-dynamics/authored-skills/independent-recompute/scripts/lazy_wave_oracle.py \
  --hangoff-angle 8 --vertical-distance 4000 --sag-bend-elevation 1200 \
  --hog-bend-above-seabed 1500 --weight-without-buoyancy 2456.695439714344 \
  --weight-with-buoyancy -2456.695439714344 \
  --check hangoff_bend_radius=452.686 --check total_S=6245.26
```

## Limits

**L1 — The total suspended length should not be treated as confirmed.**
`weight_with_buoyancy` is the exact arithmetic negative of `weight_without_buoyancy` to
16 significant figures. That is the signature of a placeholder, not a measured
buoyancy-module property. The number is verified as arithmetic but is only as good as
that input:

| \|w_b\|/w | Suspended length [m] | Horizontal reach [m] |
|---|---|---|
| 0.50 | 6687.1 | 3958.9 |
| 0.75 | 6399.6 | 3600.0 |
| **1.00 (as given)** | **6245.3** | **3400.6** |
| 1.50 | 6082.2 | 3183.4 |

A ratio of 0.5 — a wholly ordinary buoyancy design — adds 442 m (≈7%). **Produce the
riser cross-section / buoyancy-module data sheet before this length is used.** The
hang-off bend radius is unaffected.

**L2 — Input precision.** 4000 / 1200 / 1500 m and 8° are round numbers with no stated
tolerance, sitting oddly beside 16-digit weights — itself evidence the inputs are not
all from one source. dR/dθ ≈ 65 m/deg and dS/dθ ≈ 194 m/deg, which is where the bands
in the Result table come from.

**L3 — The configuration does not look converged.** The hog bend sits 1500 m above the
seabed but only 300 m above the sag bend, so the buoyed section rises 398 m of arc and
descends 1114 m, requiring 1512 m of buoyancy coverage. Geometrically valid and it
closes exactly, but conventional lazy-wave designs place the buoyed section much lower
and shorter. Worth asking whether these three elevations came from a real configuration.

**L4 — Scope.** Still-water, no-offset, no-current, zero-bending-stiffness nominal shape
only (A2, A3). No asset, standard, acceptance criterion or environment was given (A5);
nothing here is a code check. A real bend stiffener at the hang-off and any vessel
offset will both move these numbers.

**Open items for the client:** (i) which "bend radius" was meant (Result); (ii) declination
convention, A6; (iii) weight units, A1; (iv) the buoyancy weight-ratio data sheet, Limits L1.
