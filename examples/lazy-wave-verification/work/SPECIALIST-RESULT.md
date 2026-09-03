# Specialist result — lazy-wave riser geometry

Engagement: lazy-wave-verification
Specialist: orcaflex-specialist (marine dynamics)
Date: 2026-09-03
Frame: work/FRAME.md (assumptions A1–A5 apply as written; not restated here except A1)

Static geometry only. No OrcaFlex/OrcaWave licence was used and none is required:
this is a closed-form multi-segment catenary construction, not a solver run.

---

## 1. The two requested numbers

| Quantity | Value | Units | Precision I actually believe |
|---|---|---|---|
| Hang-off bend radius (catenary parameter a = H/w at hang-off) | **452.686** | m | **453 ± 33 m** if "8 deg" is rounded to the nearest degree; 452.69 m if 8.000 deg is exact |
| Total suspended length (arc, hang-off to touchdown point) | **6245.26** | m | **6245 ± 100 m** on the same angle tolerance, and see §5.1 — a further ±440 m rides on an unverified weight ratio |

Both numbers are **independent of the units on the two weights** (§4.2). Only the
forces in §2 depend on the unit assumption A1.

Reported arithmetic values are 452.6865 m and 6245.2641 m. I do not believe
those digits; they are given so the run can be reproduced bit-for-bit.

### 1.1 "Bend radius" is ambiguous — read this before using the number

452.686 m is the **catenary parameter** a = H/w at the hang-off section. That is
what the solver computes and what this term means in this code lineage. It is
*not* the radius of curvature of the pipe at the hang-off point.

| Interpretation | Value | Where |
|---|---|---|
| Catenary parameter a = H/w (reported above) | 452.686 m | hang-off section |
| True radius of curvature at the hang-off point, rho = a·sec²(theta), theta = 82 deg from horizontal | 23 372 m | at the hang-off |
| True radius of curvature at the sag bend, hog bend and TDP | 452.686 m | minimum on the line |

If the client's "hang-off bend radius" was meant as an MBR check at the hang-off,
the governing number is 23 372 m, not 452.686 m — a factor of 51.6 apart. The
client did not say which. **This should be put back to the client.** I report the
catenary parameter as the primary answer because that is what the named solver
produces under that name.

Note the coincidence that a = 452.686 m is simultaneously the minimum radius of
curvature at the sag bend, the hog bend and the TDP. That is not general — it
happens here only because |w_buoy| = w exactly (§5.1).

---

## 2. Supporting geometry a reviewer needs

Vertical datum: hang-off point. Seabed 4000 m below it. Horizontal datum: hang-off.

### Segments (5-segment construction, hang-off -> TDP)

| # | Segment | Arc S [m] | Horiz X [m] | Vert span d [m] | Bend radius a [m] | w used [N/m] |
|---|---|---|---|---|---|---|
| 1 | Hang-off -> sag bend (down) | 3221.03 | 1204.28 | 2800.00 | 452.686 | +2456.695 |
| 2 | Sag bend -> buoyancy start (up) | 397.88 | 359.03 | 150.00 | 452.686 | +2456.695 |
| 3 | Buoyancy start -> hog bend (up) | 397.88 | 359.03 | 150.00 | 452.686 | −2456.695 |
| 4 | Hog bend -> buoyancy end (down) | 1114.24 | 739.15 | 750.00 | 452.686 | −2456.695 |
| 5 | Buoyancy end -> TDP (down) | 1114.24 | 739.15 | 750.00 | 452.686 | +2456.695 |
| | **Total** | **6245.26** | **3400.64** | | | |

Grouped as the solver reports them:
- Hang-off to buoyancy start: S = 3618.91 m, X = 1563.32 m
- Buoyed (segments 3+4): S = **1512.12 m**, X = 1098.18 m  — this is the required
  buoyancy-module coverage length
- Buoyancy end to TDP: S = 1114.24 m, X = 739.15 m

### Station table (cumulative)

| Station | Horiz offset from hang-off [m] | Elevation above seabed [m] |
|---|---|---|
| Hang-off | 0 | 4000 |
| Sag bend | 1204.28 | 1200 (client input) |
| Buoyancy start | 1563.32 | 1350 (derived) |
| Hog bend | 1922.35 | 1500 (client input) |
| Buoyancy end | 2661.50 | 750 (derived) |
| Touchdown point (TDP) | 3400.64 | 0 |

Total horizontal reach hang-off to TDP: **3400.64 m**.

### End forces at hang-off (these DO depend on assumption A1: weights in N/m)

| Quantity | Value | Basis |
|---|---|---|
| Horizontal tension Fh = w·a | **1.112 MN** (1 112 113 N) | constant along the whole line |
| Vertical tension component Fv = w·S₁ | **7.913 MN** (7 913 093 N) | w × hang-off arc from sag trough |
| Total effective tension at hang-off T = sqrt(Fh²+Fv²) = w·(a+d₁) | **7.991 MN** (7 990 860 N) | two independent identities agree to 1e-9 rel. |

Check: atan(Fh/Fv) = 8.000000 deg, i.e. the force triangle reproduces the input
declination exactly. That is the check that validates these three numbers.

**I do not adopt the solver's own `vertical_force` output.** See §5.3.

---

## 3. Method

### 3.1 Construction

Five-segment inextensible catenary at constant horizontal tension H, closing on
the seabed by construction. Sag bend, hog bend and TDP are all points of
horizontal tangent. Two catenary radii:

    a_w = H / w        (bare riser, segments 1, 2, 5)
    a_b = H / |w_b|    (buoyed,      segments 3, 4)  = a_w · w / |w_b|

**Hang-off bend radius** — the catenary through a departure angle q from the
vertical, descending a vertical span d₁ from the hang-off to the sag trough:

    theta = 90 deg − q                       (angle from horizontal)
    d1    = vertical_distance − sag_bend_elevation
    a_w   = d1 · cos(theta) / (1 − cos(theta))

This is the standard catenary identity d = a(sec theta − 1). It is *derived*, not
a free input.

**Hang-off segment**

    S1 = a_w · tan(theta)
    X1 = a_w · asinh(tan(theta))

**Remaining segments** — for a segment of vertical span d on a catenary of radius a
measured from its own horizontal-tangent point:

    X = a · acosh(d/a + 1)
    S = a · sinh(X/a)

**Vertical-span split** — the split of (hog − sag) and of hog between the bare and
buoyed catenaries is fixed by slope continuity at the two buoyancy boundaries
(1 + d/a must match across the joint), which gives d_bare/d_buoyed = a_bare/a_buoyed:

    d2 = (hog − sag) · |w_b| / (|w_b| + w)    sag bend -> buoyancy start   (up)
    d3 = (hog − sag) · w    / (|w_b| + w)     buoyancy start -> hog bend   (up)
    d4 = hog · w    / (|w_b| + w)             hog bend -> buoyancy end     (down)
    d5 = hog · |w_b| / (|w_b| + w)            buoyancy end -> TDP          (down)

**Closure** — d1 − d2 − d3 + d4 + d5 = vertical_distance, exact by construction.
The run reports a closure residual of 0.0 m (machine zero).

**Forces** — Fh = w·a_w; Fv = w·S1; T = sqrt(Fh² + Fv²) = w·(a_w + d1).

### 3.2 Solver, version, provenance

- Skill loaded: `catenary-riser` v1.0.0, ace-marine-dynamics plugin
  (`/Users/krishna/Developer/ws/aceengineer-agents/plugins/ace-marine-dynamics/skills/catenary-riser/SKILL.md`)
- Solver actually used: `LazyWaveSolver` in
  `digitalmodel.marine_ops.marine_analysis.catenary`
  - repo: `/Users/krishna/Developer/ws/digitalmodel`, HEAD `bb922b9bf3c77932a148f502c0f339bb9525521a` (clean for this path)
  - module `__version__` = `2.0.0`
  - file `src/digitalmodel/marine_ops/marine_analysis/catenary/lazy_wave.py`,
    md5 `8c2a7717c2d065be52010be9b5085559`, last changed by commit
    `109e7768c5a4a651e03b38e5f66e21b75cb98e19` "fix(catenary): repair three SLWR
    geometry-kernel defects (#1949) (#1951)"
  - digitalmodel package version 0.1.1
- Python 3.13.14 in a throwaway venv at `/tmp/lwenv`
  (deps needed only to satisfy the package import chain: numpy, scipy, pyyaml,
  pandas, matplotlib, plotly, seaborn, openpyxl)

### 3.3 Exact commands

```
uv venv /tmp/lwenv --python 3.13
uv pip install --python /tmp/lwenv/bin/python numpy scipy pyyaml pandas matplotlib plotly seaborn openpyxl

PYTHONPATH=/Users/krishna/Developer/ws/digitalmodel/src \
  /tmp/lwenv/bin/python \
  /Users/krishna/Developer/ws/aceengineer-agents/examples/lazy-wave-verification/work/run_lazy_wave.py
```

Independent closed-form recomputation (imports `math` only, no digitalmodel):

```
/tmp/lwenv/bin/python \
  /Users/krishna/Developer/ws/aceengineer-agents/examples/lazy-wave-verification/work/handcheck_lazy_wave.py
```

The two agree on every segment to the printed precision, and the hang-off radius
agrees with the library to exactly 0.0 m. The hand check is *not* an independent
verification of the method — it is the same equations, coded separately, and only
rules out a transcription error in the library call.

I deliberately did **not** run
`plugins/ace-marine-dynamics/authored-skills/independent-recompute/scripts/lazy_wave_oracle.py`,
so that it remains available to the verifier as a genuinely independent oracle.

---

## 4. Every input, with provenance

### 4.1 Inputs

| Input | Value | Source | Notes |
|---|---|---|---|
| vertical_distance (hang-off to seabed) | 4000 m | **client**, REQUEST.md | no source document cited |
| sag_bend_elevation (above seabed) | 1200 m | **client**, REQUEST.md | |
| hog_bend_above_seabed | 1500 m | **client**, REQUEST.md | |
| hangoff_angle (declination) | 8 deg | **client**, REQUEST.md | **interpreted as degrees from vertical** — see §5.2 |
| weight_without_buoyancy w | 2456.695439714344 | **client**, REQUEST.md | **units ASSUMED N/m** (frame A1) |
| weight_with_buoyancy w_b | −2456.695439714344 | **client**, REQUEST.md | **units ASSUMED N/m** (frame A1); sign negative = net buoyant, required by the solver |
| hangoff_vertical_span d1 | 2800 m | **derived** = 4000 − 1200 | |
| hangoff_below_msl | 0.0 m | **assumed** — not given by client | **inert**: reporting datum only, never read by the solve. Verified: 0 / 300 / 1500 m give bit-identical R and S_tot |
| hangoff_bend_radius | omitted (derived) | — | supplying it is a cross-check, not an input |
| water density, pipe OD/WT, material, current, vessel offset | not used | — | not required by this construction |

### 4.2 The unit assumption on the weights — what it does and does not affect

I assumed N/m per frame A1, and I state that assumption plainly because the client
did not give units.

**It does not affect either requested number.** The geometry depends on the two
weights only through the ratio |w_b|/w. Verified by re-running with the weights
scaled by 0.001 and by 1000: R and S_tot are bit-identical (452.6864612651 m and
6245.2641417055 m in all three runs); only Fh scales, 1.112 kN / 1.112 MN / 1.112 GN.

**It does affect §2's forces linearly.** If the client meant kgf/m, every force in
§2 multiplies by 9.80665 (Fh 10.9 MN, T 78.4 MN). If kN/m, ×1000.

Plausibility argument, offered as support and not as proof: at N/m the bare riser
is 2456.7 N/m ≈ 250 kg/m submerged and the top tension is 7.99 MN ≈ 815 tonnef,
which is a large but credible ultra-deepwater riser. At kgf/m it would be
2.5 tonne/m submerged and 8000 tonnef at the hang-off, which is not credible for
any riser. N/m is the only self-consistent reading. **The client should still
confirm it.**

---

## 5. What troubles me

### 5.1 The two weights are exact negatives — and the answer moves when they are not

`weight_with_buoyancy` = −`weight_without_buoyancy` to all 16 significant figures.
Frame Q1 already flags this as a placeholder signature. I can now quantify why it
matters, because it is not a cosmetic concern:

| |w_b| / w | Total suspended length [m] | Horizontal reach [m] |
|---|---|---|
| 0.25 | 7431.1 | 4837.0 |
| 0.50 | 6687.1 | 3958.9 |
| 0.75 | 6399.6 | 3600.0 |
| **1.00 (as given)** | **6245.3** | **3400.6** |
| 1.50 | 6082.2 | 3183.4 |
| 2.00 | 5996.8 | 3066.4 |

A ratio of 0.5 instead of 1.0 — a wholly ordinary buoyancy design — changes the
total suspended length by +442 m, about 7%. **The requested total suspended length
is not robust to this input and I would not issue it as confirmed until the
riser cross-section / buoyancy-module data sheet is produced.**

The hang-off bend radius is entirely insensitive to both weights, so that number
stands regardless.

A physical reading of the given ratio: the buoyancy modules supply exactly twice
the submerged weight of the bare riser, so the buoyed section is as strongly
buoyant as the bare section is heavy. That is a designable condition, but landing
on it to 16 digits is not a measurement.

### 5.2 "Declination" was not defined

I read 8 deg as the angle **from the vertical**, which is the normal riser
hang-off convention and is what the solver's API expects
(`hangoff_angle`: "Departure angle from the vertical"). If the client meant 8 deg
from the **horizontal** (i.e. 82 deg declination from vertical), every number in
this report is wrong — the hang-off bend radius would become 284 913 m instead of
452.7 m, a factor of 629. The two readings are nowhere near each other and nothing
in the outputs would flag the error. This should be confirmed in writing. I judge
the from-vertical reading near-certain (8 deg from horizontal is not a hang-off
declination anyone would specify), but it is still an interpretation, not a given.

### 5.3 The solver's reported `vertical_force` is wrong; I substituted the correct value

`LazyWaveSolver` computes

    Fv = Fh + w · S_hangoff          -> 9 025 206 N

That is neither the vertical tension component nor the total tension. The correct
vertical component is w·S₁ = 7 913 093 N, which is (a) what the same library's
own general-catenary path uses (`adapter.py:314`, `simplified.py:288`,
`legacy/catenaryMethods.py:87` all use `Fv = w * S`), and (b) the only value that
reproduces the input declination: atan(Fh / 7 913 093) = 8.000000 deg, whereas
atan(Fh / 9 025 206) = 7.025 deg, contradicting the stated 8 deg input.

The defect is inherited verbatim from the legacy lazy-wave routine
(`legacy/catenaryMethods.py:170`), so the same library contains two contradictory
definitions of Fv. This did not affect the geometry — Fh and Fv are computed after
the shape and feed nothing back into it — so §1 and §2's geometry are unaffected.

**§2 reports the corrected Fv = 7.913 MN, not the solver's 9.025 MN.** A verifier
re-running `LazyWaveSolver` will see 9 025 206 N in `results.vertical_force` and
should expect the discrepancy. I have not raised this as a digitalmodel issue;
that is a separate action.

### 5.4 The skill points at a solver that does not exist

`catenary-riser/SKILL.md` documents `digitalmodel.subsea.catenary.lazy_wave_catenary.LazyWaveCatenary`.
That import path does not exist. The nearest real class,
`digitalmodel.subsea.catenary_riser.LazyWaveAnalyzer`, is **quarantined**: per
`tests/subsea/catenary_riser/test_lazy_wave_quarantine.py` it never solved
anything — it returned hardcoded fractions of water depth and buoyancy had no
effect on its output — and it now raises `NotImplementedError`. Following the
skill as written would either fail to import or, before the quarantine, would have
returned fabricated geometry. I used the real solver named in the quarantine
docstring instead. **The skill file needs correcting.** Also, the plugin directory
`plugins/ace-marine-dynamics/skills/catenary-riser/` contains only `SKILL.md` — no
solver script — despite the task brief stating the solver is there.

### 5.5 The configuration itself is unusual

The hog bend sits 1500 m above the seabed but only 300 m above the sag bend. As a
result the buoyed section spends 398 m of arc rising and 1114 m descending, and the
buoyancy modules must cover 1512 m of riser spanning elevations 750 m to 1500 m.
Conventional lazy-wave designs place the buoyed section much lower and much
shorter. This is geometrically valid and closes exactly, but it does not look like
a converged design — it looks like a first-pass or a set of trial numbers. Worth
asking whether these three elevations came from a real configuration.

### 5.6 Precision of the stated inputs

4000 / 1200 / 1500 m and 8 deg are all round numbers with no tolerance. dR/dq is
about 65 m per degree and dS_tot/dq about 194 m per degree, so if "8 deg" is
rounded to the nearest degree the honest bands are R = 453 ± 33 m and
S_tot = 6245 ± 97 m. The 16-digit weights sit oddly next to 1-significant-figure
geometry; that mismatch is itself evidence the inputs are not all from the same
source.

### 5.7 Frame items that remain open (restated, not resolved)

No standard, no acceptance criterion, no environment, no asset identification
(frame A5). Nothing here is a code check and no pass/fail is asserted. The
still-water, no-offset, no-current, zero-bending-stiffness idealisation (A2, A3)
means these are nominal shape numbers only; a real bend stiffener at the hang-off
and any vessel offset will both move them.
