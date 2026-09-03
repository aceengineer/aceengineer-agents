# Verification handoff — lazy-wave riser geometry

You are given the inputs, the method claimed, and the result. Nothing else.

## 1. Inputs (verbatim from client REQUEST.md; no source document was cited)

    vertical distance (hang-off to seabed) : 4000 m
    sag bend elevation (above seabed)      : 1200 m
    hog bend above seabed                  : 1500 m
    hang-off declination                   : 8 deg
    weight without buoyancy                : 2456.695439714344
    weight with buoyancy                   : -2456.695439714344

Units on the two weights were NOT given by the client. The producer assumed N/m.
"Declination" was not defined by the client. The producer read it as degrees
from the vertical.

## 2. Method claimed

Five-segment inextensible catenary at constant horizontal tension H, closing on
a flat seabed by construction. Sag bend, hog bend and touchdown point are all
points of horizontal tangent. Two catenary radii:

    a_w = H / w          (bare riser: segments 1, 2, 5)
    a_b = H / |w_b|      (buoyed:     segments 3, 4)

"Hang-off bend radius" is claimed to mean the catenary parameter a_w = H/w,
derived (not input) from the declination and the hang-off-to-sag vertical span:

    theta = 90 deg - declination                (angle from horizontal)
    d1    = vertical_distance - sag_bend_elevation
    a_w   = d1 * cos(theta) / (1 - cos(theta))

Hang-off segment:

    S1 = a_w * tan(theta)
    X1 = a_w * asinh(tan(theta))

Remaining segments, for vertical span d on a catenary of radius a measured from
its own horizontal-tangent point:

    X = a * acosh(d/a + 1)
    S = a * sinh(X/a)

Vertical-span split, claimed to follow from slope continuity at the two
buoyancy boundaries:

    d2 = (hog - sag) * |w_b| / (|w_b| + w)     sag bend    -> buoyancy start (up)
    d3 = (hog - sag) * w     / (|w_b| + w)     buoy start  -> hog bend       (up)
    d4 = hog * w     / (|w_b| + w)             hog bend    -> buoyancy end   (down)
    d5 = hog * |w_b| / (|w_b| + w)             buoy end    -> TDP            (down)

Closure: d1 - d2 - d3 + d4 + d5 = vertical_distance.

Forces:  Fh = w * a_w ;  Fv = w * S1 ;  T = sqrt(Fh^2 + Fv^2) = w * (a_w + d1).

Software: `LazyWaveSolver` in `digitalmodel.marine_ops.marine_analysis.catenary`,
module version 2.0.0, repo /Users/krishna/Developer/ws/digitalmodel at HEAD
bb922b9bf3c77932a148f502c0f339bb9525521a, file
src/digitalmodel/marine_ops/marine_analysis/catenary/lazy_wave.py md5
8c2a7717c2d065be52010be9b5085559. Python 3.13.14.

Producer's run script: work/run_lazy_wave.py
Producer's own hand recomputation of the same equations: work/handcheck_lazy_wave.py

NOTE: the producer's claimed Fv (below) is NOT the value the named solver's
`vertical_force` field returns. The producer substituted Fv = w*S1. Both values
are stated here so you can attack the discrepancy yourself.
Solver's own `vertical_force` output: 9 025 206 N.

## 3. Result claimed

REQUESTED:
  Hang-off bend radius (catenary parameter a_w) = 452.686 m
      producer's stated believed precision: 453 +/- 33 m if "8 deg" is
      rounded to the nearest degree
  Total suspended length (arc, hang-off to TDP) = 6245.26 m
      producer's stated believed precision: 6245 +/- 100 m on angle tolerance

SUPPORTING:
  Segment arc lengths [m]: 3221.03 / 397.88 / 397.88 / 1114.24 / 1114.24
  Segment horizontal offsets [m]: 1204.28 / 359.03 / 359.03 / 739.15 / 739.15
  Total horizontal reach hang-off -> TDP = 3400.64 m
  Buoyed section arc length = 1512.12 m, spanning elevations 750 m to 1500 m
  Closure residual = 0.0 m

  Station table (horiz offset from hang-off, elevation above seabed):
    hang-off        0        4000
    sag bend     1204.28     1200
    buoy start   1563.32     1350
    hog bend     1922.35     1500
    buoy end     2661.50      750
    TDP          3400.64        0

  Forces at hang-off (depend on the assumed N/m units):
    Fh = 1 112 113 N
    Fv = 7 913 093 N     (producer's value; solver returns 9 025 206 N)
    T  = 7 990 860 N

Full-precision values for bit-comparison: a_w = 452.6864612651 m,
S_tot = 6245.2641417055 m.

## 4. Stated assumptions to load-bearing test

  A1. Weights are distributed submerged weight per unit length in N/m.
  A2. Still water; no current, no vessel offset; static equilibrium.
  A3. Inextensible, no bending stiffness in the shape.
  A4. Flat horizontal seabed 4000 m below the hang-off.
  A5. No standard governs this result; no pass/fail is asserted.
  A6. "Declination" is measured from the vertical.
  A7. hangoff_below_msl = 0.0 m (not given by client).
