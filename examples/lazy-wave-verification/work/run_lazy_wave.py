"""Lazy-wave geometry run - AceEngineer engagement lazy-wave-verification.

Solver: digitalmodel.marine_ops.marine_analysis.catenary.LazyWaveSolver
Inputs verbatim from REQUEST.md; units per FRAME.md A1.
"""
import json
import math

from digitalmodel.marine_ops.marine_analysis.catenary import (
    LazyWaveSolver,
    LazyWaveConfiguration,
    derive_hangoff_bend_radius,
)
import digitalmodel.marine_ops.marine_analysis.catenary as cat

W = 2456.695439714344       # client: "weight without buoyancy" [N/m assumed, FRAME A1]
WB = -2456.695439714344     # client: "weight with buoyancy"    [N/m assumed, FRAME A1]

cfg = LazyWaveConfiguration(
    hangoff_angle=8.0,            # client: hang-off declination, deg from vertical
    hangoff_below_msl=0.0,        # NOT given by client; reporting datum only
    hog_bend_above_seabed=1500.0, # client
    sag_bend_elevation=1200.0,    # client
    weight_without_buoyancy=W,
    weight_with_buoyancy=WB,
    vertical_distance=4000.0,     # client
)

res = LazyWaveSolver().solve(cfg)

print("catenary module version:", cat.__version__)
print("hangoff_vertical_span [m]      :", cfg.hangoff_vertical_span)
print("HANG-OFF BEND RADIUS [m]       :", cfg.hangoff_bend_radius)
print("TOTAL SUSPENDED ARC LENGTH [m] :", res.total_arc_length)
print("total horizontal distance [m]  :", res.total_horizontal_distance)
print("Fh [N]                         :", res.horizontal_force)
print("Fv [N]                         :", res.vertical_force)
print("vertical closure error [m]     :", res.vertical_closure_error)
print()
names = ["hangoff_to_sag", "sag_to_buoyancy", "buoyancy_to_hog",
         "hog_to_buoyancy_end", "buoyancy_to_touchdown"]
print(f"{'segment':24s} {'S [m]':>14s} {'X [m]':>14s} {'d [m]':>10s} {'R [m]':>14s} {'w [N/m]':>16s}")
for n, s in zip(names, res.segments):
    print(f"{n:24s} {s.arc_length:14.4f} {s.horizontal_distance:14.4f} "
          f"{s.vertical_distance:10.4f} {s.bend_radius:14.4f} {s.weight_per_length:16.6f}")
print()
print("summary:", json.dumps(res.summary, indent=2))

# --- independence / sensitivity checks -------------------------------------
print("\n-- check: hangoff_below_msl is inert --")
for hb in (0.0, 300.0, 1500.0):
    c2 = LazyWaveConfiguration(8.0, hb, 1500.0, 1200.0, W, WB, 4000.0)
    r2 = LazyWaveSolver().solve(c2)
    print(f"  hangoff_below_msl={hb:7.1f} -> R={c2.hangoff_bend_radius:.10f} "
          f"S_tot={r2.total_arc_length:.10f}")

print("\n-- check: geometry depends on weights only via the ratio (unit-free) --")
for scale in (1.0, 0.001, 1000.0):   # N/m -> kN/m -> arbitrary rescale
    c3 = LazyWaveConfiguration(8.0, 0.0, 1500.0, 1200.0, W*scale, WB*scale, 4000.0)
    r3 = LazyWaveSolver().solve(c3)
    print(f"  scale={scale:9.4g} -> R={c3.hangoff_bend_radius:.10f} "
          f"S_tot={r3.total_arc_length:.10f} Fh={r3.horizontal_force:.6g}")

print("\n-- sensitivity: total arc length vs buoyancy ratio |w_b|/w --")
for ratio in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
    c4 = LazyWaveConfiguration(8.0, 0.0, 1500.0, 1200.0, W, -W*ratio, 4000.0)
    r4 = LazyWaveSolver().solve(c4)
    print(f"  |w_b|/w={ratio:5.2f} -> S_tot={r4.total_arc_length:12.3f} m "
          f"X_tot={r4.total_horizontal_distance:12.3f} m")

print("\n-- closed-form cross-check of R (independent of the library) --")
th = math.radians(90.0 - 8.0)
R_hand = 2800.0 * math.cos(th) / (1.0 - math.cos(th))
print("  R_hand =", R_hand, " delta =", R_hand - cfg.hangoff_bend_radius)
