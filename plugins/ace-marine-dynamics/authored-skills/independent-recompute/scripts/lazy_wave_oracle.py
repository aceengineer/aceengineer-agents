#!/usr/bin/env python3
"""Independent closed-form oracle for lazy-wave riser geometry.

The AceEngineer verification gate requires the verifier to recompute a result by
an **independent route** and to build a runnable reproducer. This is that route
for lazy-wave configurations.

Independence is the entire point, so note carefully what this does NOT do:

  * It does not import, call, shell out to, or read the digitalmodel solver.
  * It does not import OrcFxAPI or read a .sim file.
  * It implements the geometry from first principles — circular-arc segments and
    the catenary relations — against the invariants documented in the reference
    fixture, and is pinned by 4 historical solver runs it had no part in
    producing.

If this oracle and the specialist agree, two independent routes agree. If it
imported the thing it is checking, agreement would mean nothing.

Usage
-----
    lazy_wave_oracle.py --self-test
    lazy_wave_oracle.py --hangoff-angle 8 --vertical-distance 4000 \
        --sag-bend-elevation 1200 --hog-bend-above-seabed 1500 \
        --weight-without-buoyancy 2456.695439714344 \
        --weight-with-buoyancy -2456.695439714344
    lazy_wave_oracle.py --check total_S=6245.26 --hangoff-angle 8 ...   # verdict mode

Exit codes: 0 agreement / self-test passed, 1 disagreement, 2 bad input.
"""
import argparse
import math
import os
import re
import sys

# Keys in the reference fixture that are WRONG and must not be asserted against.
# `Fv` there is w*(S1 + R) -- the vertical component plus the horizontal tension.
# Confirmed refuted 2026-09-03 by three independent routes (global vertical force
# equilibrium, 4e6-panel Simpson quadrature, and the tangent identity): the
# fixture's value implies a 7.025 deg declination where 8.000 deg was the input.
# The defect is inherited from the legacy lazy-wave routine, and the same library
# contains a second, correct definition (Fv = w*S) on its general-catenary path.
KNOWN_BAD_REFERENCE = {"Fv"}

REFERENCE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "reference", "lazy_wave_reference_cases.yaml")


# --- geometry -------------------------------------------------------------

def arc_length(d, R):
    """Along-line length of a circular-arc segment of vertical span d, radius R."""
    return math.sqrt(d * (2.0 * R + d))


def horizontal(S, R):
    """Horizontal projection of that segment."""
    return R * math.asinh(S / R)


def solve(hangoff_angle, vertical_distance, sag_bend_elevation,
          hog_bend_above_seabed, weight_without_buoyancy, weight_with_buoyancy):
    """Recompute the full lazy-wave geometry from the stated invariants.

    Invariants (from the reference fixture, asserted by --self-test):
      1. d_hangoff = vertical_distance - sag_bend_elevation
      2. R = d_hangoff * cos(90-q) / (1 - cos(90-q))    [never supplied independently]
      3. d1 - d2 - d3 + d4 + d5 == vertical_distance    [closure by construction]

    The buoyed segments carry a radius scaled by the weight ratio
    k = w_bare / |w_buoyed|; the bare segments reuse R verbatim.
    """
    if weight_with_buoyancy >= 0:
        raise ValueError(
            "weight_with_buoyancy >= 0: net-downward configurations are outside "
            "the validated regime. The reference sweep exercised only net-buoyant "
            "cases, so any answer here is untested legacy behaviour, not "
            "validated behaviour. Refusing to produce a number."
        )
    if not 0.0 < hangoff_angle < 90.0:
        raise ValueError("hangoff_angle must be a declination in (0, 90) degrees")

    c = math.cos(math.radians(90.0 - hangoff_angle))
    d1 = vertical_distance - sag_bend_elevation
    if d1 <= 0:
        raise ValueError("sag_bend_elevation must be below the hang-off datum")
    R = d1 * c / (1.0 - c)

    k = weight_without_buoyancy / abs(weight_with_buoyancy)
    R_buoyed = R * k

    span = hog_bend_above_seabed - sag_bend_elevation
    d2 = span / (1.0 + k)                       # sag  -> buoyancy    (bare R)
    d3 = span * k / (1.0 + k)                   # buoyancy -> hog     (buoyed R)
    d4 = hog_bend_above_seabed * k / (1.0 + k)  # hog  -> buoyancy    (buoyed R)
    d5 = hog_bend_above_seabed / (1.0 + k)      # buoyancy -> touchdown (bare R)

    segs = [("hangoff", d1, R), ("sag_to_buoyancy", d2, R),
            ("buoyancy_to_hog", d3, R_buoyed), ("hog_to_buoyancy", d4, R_buoyed),
            ("buoyancy_to_touchdown", d5, R)]

    out = {"hangoff_d": d1, "hangoff_bend_radius": R, "buoyancy_to_hog_R": R_buoyed}
    total_S = total_X = 0.0
    for name, d, r in segs:
        S = arc_length(d, r)
        X = horizontal(S, r)
        out[f"{name}_d"], out[f"{name}_S"], out[f"{name}_X"] = d, S, X
        total_S += S
        total_X += X

    out["total_S"], out["total_X"] = total_S, total_X

    # Forces. Fv is the VERTICAL COMPONENT of tension: the weight of the
    # suspended hang-off segment, w*S1. Nothing else.
    #
    # The reference fixture and the digitalmodel solver both report
    # w*(S1 + R) here, i.e. Fv + Fh. That is dimensionally a force but is
    # neither the vertical component nor the total tension, and it is
    # refutable without any solver: the force triangle must reproduce the
    # input declination, and only w*S1 does. See ORACLE-FV-CORRECTION below.
    out["Fh"] = weight_without_buoyancy * R
    out["Fv"] = weight_without_buoyancy * out["hangoff_S"]
    out["T"] = weight_without_buoyancy * (R + d1)          # == hypot(Fh, Fv)

    # Derived self-check, not a fitted one: the force triangle must return the
    # declination that was fed in. This is what caught the inherited defect.
    implied = 90.0 - math.degrees(math.atan2(out["Fv"], out["Fh"]))
    if abs(implied - hangoff_angle) > 1e-9:
        raise AssertionError(
            f"force triangle does not reproduce the input declination: implied "
            f"{implied:.6f} deg vs input {hangoff_angle:.6f} deg. Do not use this result."
        )

    closure = d1 - d2 - d3 + d4 + d5
    if abs(closure - vertical_distance) > 1e-6:
        raise AssertionError(
            f"vertical closure violated: {closure} != {vertical_distance}. "
            "The oracle's own geometry is inconsistent; do not use this result."
        )
    return out


# --- reference fixture ----------------------------------------------------

def load_cases(path=REFERENCE):
    """Read the reference fixture without a YAML dependency.

    The fixture has one fixed shape (cases -> id/description/inputs/expected of
    flat scalars), so a targeted reader is safer here than adding a dependency
    that must then exist on every client machine.
    """
    cases, cur, section = [], None, None
    with open(path, "r", encoding="utf-8") as fh:
        in_cases = False
        for line in fh:
            if re.match(r"^cases:\s*$", line):
                in_cases = True
                continue
            if not in_cases:
                continue
            if re.match(r"^[a-z_]+:", line):       # a new top-level key ends cases
                break
            m = re.match(r"^  - id:\s*(\S+)", line)
            if m:
                cur = {"id": m.group(1), "inputs": {}, "expected": {}}
                cases.append(cur)
                section = None
                continue
            if cur is None:
                continue
            if re.match(r"^    inputs:\s*$", line):
                section = "inputs"
                continue
            if re.match(r"^    expected:\s*$", line):
                section = "expected"
                continue
            m = re.match(r"^      ([a-zA-Z_]+):\s*(-?[\d.eE+]+)\s*$", line)
            if m and section:
                cur[section][m.group(1)] = float(m.group(2))
    return cases


def self_test(rtol=1e-9):
    cases = load_cases()
    if not cases:
        print("FAIL: no reference cases loaded", file=sys.stderr)
        return 1
    failures = 0
    for c in cases:
        try:
            got = solve(**{k: c["inputs"][k] for k in (
                "hangoff_angle", "vertical_distance", "sag_bend_elevation",
                "hog_bend_above_seabed", "weight_without_buoyancy",
                "weight_with_buoyancy")})
        except Exception as exc:                       # noqa: BLE001
            print(f"FAIL case {c['id']}: {exc}")
            failures += 1
            continue
        bad = []
        for key, want in c["expected"].items():
            if key not in got or key in KNOWN_BAD_REFERENCE:
                continue
            have = got[key]
            if abs(have - want) > rtol * max(1.0, abs(want)):
                bad.append(f"{key}: oracle {have!r} vs reference {want!r}")
        checked = sum(1 for k in c["expected"] if k in got and k not in KNOWN_BAD_REFERENCE)

        # The fixture's Fv is defective (see KNOWN_BAD_REFERENCE). Assert the
        # corrected value against the tangent identity instead, which is fixed
        # by the INPUT angle and cannot depend on any solver internals.
        want_ratio = math.tan(math.radians(90.0 - c["inputs"]["hangoff_angle"]))
        got_ratio = got["Fv"] / got["Fh"]
        if abs(got_ratio - want_ratio) > 1e-9 * max(1.0, want_ratio):
            bad.append(f"Fv/Fh: {got_ratio!r} vs tan(90-q) {want_ratio!r}")
        else:
            checked += 1
        if bad:
            failures += 1
            print(f"FAIL case {c['id']} ({len(bad)}/{checked} disagree)")
            for b in bad:
                print(f"     {b}")
        else:
            print(f"PASS case {c['id']}  ({checked} values agree to {rtol:g} rel)")
    print()
    if failures:
        print(f"{failures} of {len(cases)} reference cases FAILED")
        return 1
    print(f"all {len(cases)} historical reference cases reproduced independently")
    return 0


# --- cli ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true",
                    help="reproduce the historical reference cases and report")
    ap.add_argument("--hangoff-angle", type=float)
    ap.add_argument("--vertical-distance", type=float)
    ap.add_argument("--sag-bend-elevation", type=float)
    ap.add_argument("--hog-bend-above-seabed", type=float)
    ap.add_argument("--weight-without-buoyancy", type=float)
    ap.add_argument("--weight-with-buoyancy", type=float)
    ap.add_argument("--check", action="append", default=[], metavar="KEY=VALUE",
                    help="assert a claimed result; repeatable. Verdict mode.")
    ap.add_argument("--rtol", type=float, default=1e-6,
                    help="relative tolerance for --check (default 1e-6)")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    need = ["hangoff_angle", "vertical_distance", "sag_bend_elevation",
            "hog_bend_above_seabed", "weight_without_buoyancy", "weight_with_buoyancy"]
    vals = {k: getattr(args, k) for k in need}
    missing = [k for k, v in vals.items() if v is None]
    if missing:
        print(f"missing required input(s): {', '.join('--' + m.replace('_', '-') for m in missing)}",
              file=sys.stderr)
        return 2

    try:
        got = solve(**vals)
    except (ValueError, AssertionError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    if not args.check:
        for k in sorted(got):
            print(f"{k:26s} {got[k]!r}")
        return 0

    rc = 0
    print("Independent recompute vs claimed result:\n")
    for spec in args.check:
        if "=" not in spec:
            print(f"  bad --check spec {spec!r}, expected KEY=VALUE", file=sys.stderr)
            return 2
        key, claimed = spec.split("=", 1)
        key = key.strip()
        if key not in got:
            print(f"  UNKNOWN  {key}: the oracle does not compute this quantity")
            rc = 1
            continue
        try:
            claimed_v = float(claimed)
        except ValueError:
            print(f"  BAD      {key}: {claimed!r} is not a number")
            rc = 1
            continue
        have = got[key]
        dev = abs(have - claimed_v) / max(1.0, abs(have))
        if dev <= args.rtol:
            print(f"  AGREE    {key}: {claimed_v!r}  (oracle {have!r}, dev {dev:.2e})")
        else:
            print(f"  DISAGREE {key}: claimed {claimed_v!r}, oracle {have!r}, dev {dev:.2e}")
            rc = 1
    print()
    print("verdict: AGREE — an independent route reproduces the claim" if rc == 0
          else "verdict: DISAGREE — this is a FINDING. Report the deviation, "
               "state the defect class, and do not release the deliverable.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
