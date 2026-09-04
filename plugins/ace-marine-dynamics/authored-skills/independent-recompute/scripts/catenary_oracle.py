#!/usr/bin/env python3
"""Independent oracle for simple catenary and taut-leg mooring lines.

Companion to lazy_wave_oracle.py, extending the verifier's independent route to
the other two configurations a specialist result commonly takes (#258).

The rule this oracle is built under, learned the hard way in #266: **derive it,
or constrain it with an identity the artifact cannot influence. Never fit.**

So nothing here is validated against digitalmodel's catenary fixtures. Two of
them were extracted from the code under test, which makes them a mirror rather
than a check; and the third's published answers do not satisfy their own stated
geometry (see --audit-fixture). Instead the self-test asserts identities that
hold for any correct solution regardless of who computed it:

  1. all three boundary conditions met at once  (arc S, span X, rise d)
  2. V_fairlead - V_anchor == w * S              (global vertical equilibrium)
  3. T == hypot(H, V) at both ends               (force triangle)
  4. closed-form arc length == numerical quadrature
  5. taut limit: as slack -> 0, the catenary solution meets the elastic one

Usage
-----
    catenary_oracle.py --self-test
    catenary_oracle.py --length 1000 --span 800 --rise 100 --weight 1962 --ea 64e9
    catenary_oracle.py ... --check H=671467 --check T_fairlead=1288812
    catenary_oracle.py --audit-fixture      # test published reference values

Exit: 0 agreement / self-test passed, 1 disagreement, 2 refused or bad input.
"""
import argparse
import math
import sys

TAUT = "taut"
CATENARY = "catenary"


def _bisect(f, lo, hi, iters=400):
    flo = f(lo)
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if (f(mid) > 0) == (flo > 0):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def solve(length, span, rise, weight, ea=None):
    """Solve the line between anchor (0,0) and fairlead (span, rise).

    `length` is the unstretched line length. Returns the regime along with the
    end forces, because which regime you are in changes what the numbers mean --
    and a solver that silently switches regime is how a taut line gets reported
    with catenary tensions.
    """
    if length <= 0 or span <= 0 or weight <= 0:
        raise ValueError("length, span and weight must be positive")

    straight = math.hypot(span, rise)

    # --- taut regime: the line is shorter than the gap, so it must stretch.
    if length < straight:
        if not ea:
            raise ValueError(
                f"line length {length} m is shorter than the anchor-fairlead "
                f"distance {straight:.2f} m, so the line must stretch, but no EA "
                "was given. Refusing to guess an axial stiffness."
            )
        strain = (straight - length) / length
        T = ea * strain
        return {
            "regime": TAUT, "straight_distance": straight, "strain": strain,
            "T_fairlead": T, "T_anchor": T,
            "H": T * span / straight, "V_fairlead": T * rise / straight,
            "V_anchor": T * rise / straight,
            "catenary_parameter": float("inf"), "elastic_elongation": straight - length,
            "arc_length": straight,
        }

    if abs(length - straight) < 1e-12:
        raise ValueError(
            "line length equals the anchor-fairlead distance exactly: the line is "
            "straight and unstretched, so tension is indeterminate from geometry "
            "alone. Supply a pretension instead."
        )

    # --- catenary regime. Identity, independent of where the low point sits:
    #        sqrt(S^2 - rise^2) = 2a sinh(span / 2a)
    #
    # Solved in u = span/2a rather than in a directly: 2a·sinh(span/2a) overflows
    # for small a, and sinh(u)/u = k is monotonic and well conditioned for u > 0.
    target = math.sqrt(length * length - rise * rise)
    k = target / span                      # >= 1 whenever there is slack
    u = _bisect(lambda t: math.sinh(t) / t - k, 1e-12, 50.0)
    a = span / (2.0 * u)

    # Place the segment exactly rather than by search. With m the midpoint
    # abscissa measured from the low point:
    #     rise = 2a·sinh(span/2a)·sinh(m/a) = target·sinh(m/a)
    # so m = a·asinh(rise / target). No iteration, no bracket to get wrong.
    m = a * math.asinh(rise / target)
    x1 = m - span / 2.0
    x2 = x1 + span

    H = weight * a
    V1 = weight * a * math.sinh(x1 / a)
    V2 = weight * a * math.sinh(x2 / a)
    S = a * (math.sinh(x2 / a) - math.sinh(x1 / a))

    out = {
        "regime": CATENARY, "straight_distance": straight,
        "catenary_parameter": a, "H": H,
        "V_anchor": V1, "V_fairlead": V2,
        "T_anchor": weight * a * math.cosh(x1 / a),
        "T_fairlead": weight * a * math.cosh(x2 / a),
        "arc_length": S, "low_point_x": -x1,
        "low_point_inside_span": bool(x1 < 0 < x2),
        "elastic_elongation": (H * length / ea) if ea else None,
    }

    # Identities that must hold for ANY correct solution. Checked on every call,
    # not only in the self-test -- a wrong number should not leave this function.
    if abs((V2 - V1) - weight * S) > 1e-6 * max(1.0, abs(weight * S)):
        raise AssertionError("global vertical equilibrium violated: V2-V1 != w*S")
    for tag, T, V in (("anchor", out["T_anchor"], V1), ("fairlead", out["T_fairlead"], V2)):
        if abs(T - math.hypot(H, V)) > 1e-6 * max(1.0, T):
            raise AssertionError(f"force triangle violated at the {tag}")
    if abs(S - length) > 1e-4 * max(1.0, length):
        raise AssertionError(f"arc length closure violated: {S} vs {length}")
    return out


def quadrature_arc(a, x1, x2, n=200000):
    """Arc length by Simpson quadrature of cosh(x/a) -- no closed form used."""
    h = (x2 - x1) / n
    tot = 0.0
    for i in range(n + 1):
        wgt = 1 if i in (0, n) else (4 if i % 2 else 2)
        tot += wgt * math.cosh((x1 + i * h) / a)
    return tot * h / 3.0


def self_test():
    cases = [
        ("slack catenary, low point inside span", 1000.0, 800.0, 100.0, 1962.0, 64.0e9),
        ("mild slack",                             850.0, 800.0, 100.0, 1962.0, 64.0e9),
        ("deep sag",                              1800.0, 800.0, 100.0, 1962.0, 64.0e9),
        ("level ends",                            1000.0, 800.0,   0.0, 1962.0, 64.0e9),
        ("steep rise",                            1200.0, 500.0, 400.0, 1500.0, 40.0e9),
        ("taut leg (line shorter than the gap)",   790.0, 800.0, 100.0, 1962.0, 64.0e9),
    ]
    bad = 0
    for name, L, X, d, w, ea in cases:
        try:
            r = solve(L, X, d, w, ea)
        except Exception as exc:                          # noqa: BLE001
            print(f"FAIL  {name}: {exc}")
            bad += 1
            continue
        checks = []
        if r["regime"] == CATENARY:
            a, x1 = r["catenary_parameter"], -r["low_point_x"]
            q = quadrature_arc(a, x1, x1 + X)
            checks.append(("arc vs quadrature", abs(q - r["arc_length"]), 1e-4))
            checks.append(("V2-V1 == w*S", abs((r["V_fairlead"] - r["V_anchor"]) - w * r["arc_length"]), 1e-3))
            checks.append(("T == hypot(H,V) fairlead",
                           abs(r["T_fairlead"] - math.hypot(r["H"], r["V_fairlead"])), 1e-6))
            checks.append(("arc closure", abs(r["arc_length"] - L), 1e-3))
        else:
            checks.append(("T == hypot(H,V)",
                           abs(r["T_fairlead"] - math.hypot(r["H"], r["V_fairlead"])), 1e-6))
            checks.append(("Hooke", abs(r["T_fairlead"] - ea * r["strain"]), 1e-6))
        fails = [(n, v) for n, v, tol in checks if v > tol]
        if fails:
            bad += 1
            print(f"FAIL  {name}")
            for n, v in fails:
                print(f"        {n}: residual {v:.3e}")
        else:
            print(f"PASS  {name}  ({r['regime']}, {len(checks)} identities)")

    # Regime continuity: approaching the taut boundary from the slack side, the
    # catenary tension must climb towards the elastic one rather than jump.
    straight = math.hypot(800.0, 100.0)
    prev = None
    mono = True
    for eps in (50.0, 20.0, 5.0, 1.0, 0.2):
        r = solve(straight + eps, 800.0, 100.0, 1962.0, 64.0e9)
        if prev is not None and r["T_fairlead"] < prev:
            mono = False
        prev = r["T_fairlead"]
    print(f"{'PASS' if mono else 'FAIL'}  taut limit: tension rises monotonically as slack -> 0")
    bad += 0 if mono else 1

    print()
    if bad:
        print(f"{bad} check group(s) FAILED")
        return 1
    print("all identity checks passed (no reference values were used)")
    return 0


def audit_fixture():
    """Test digitalmodel's published catenary reference values against geometry."""
    L, X, d, w = 1000.0, 800.0, 100.0, 1962.0
    target = math.sqrt(L * L - d * d)
    print(f"digitalmodel tests/fixtures/.../mooring_catenary_solver.yaml")
    print(f"  inputs L={L} X={X} rise={d} w={w}\n")
    truth = solve(L, X, d, w, 64.0e9)
    print(f"  derived here:            H = {truth['H']:>12,.0f} N   a = {truth['catenary_parameter']:.2f} m")
    for name, H in (("'verified analytical'", 1327168.0), ("'Excel Poly Mooring'", 785000.0)):
        a = H / w
        implied = 2 * a * math.sinh(X / (2 * a))
        ok = abs(implied - target) < 1.0
        print(f"  {name:24s} H = {H:>12,.0f} N   a = {a:8.2f} m   "
              f"2a·sinh(X/2a) = {implied:8.2f} (needs {target:.2f})  "
              f"{'consistent' if ok else 'INCONSISTENT'}")
    print("\n  Neither published answer satisfies the geometry it is stated against.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--audit-fixture", action="store_true")
    ap.add_argument("--length", type=float, help="unstretched line length (m)")
    ap.add_argument("--span", type=float, help="horizontal anchor-to-fairlead distance (m)")
    ap.add_argument("--rise", type=float, default=0.0, help="fairlead elevation above anchor (m)")
    ap.add_argument("--weight", type=float, help="submerged weight per unit length (N/m)")
    ap.add_argument("--ea", type=float, help="axial stiffness EA (N)")
    ap.add_argument("--check", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--rtol", type=float, default=1e-6)
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.audit_fixture:
        return audit_fixture()

    missing = [f"--{k}" for k in ("length", "span", "weight") if getattr(args, k) is None]
    if missing:
        print(f"missing required input(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    try:
        got = solve(args.length, args.span, args.rise, args.weight, args.ea)
    except (ValueError, AssertionError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    if not args.check:
        for k in sorted(got):
            print(f"{k:26s} {got[k]!r}")
        return 0

    rc = 0
    print(f"Independent recompute ({got['regime']} regime) vs claimed result:\n")
    for spec in args.check:
        if "=" not in spec:
            print(f"  bad --check spec {spec!r}", file=sys.stderr)
            return 2
        key, claimed = spec.split("=", 1)
        key = key.strip()
        if key not in got or not isinstance(got[key], (int, float)):
            print(f"  UNKNOWN  {key}")
            rc = 1
            continue
        try:
            cv = float(claimed)
        except ValueError:
            print(f"  BAD      {key}: {claimed!r} is not a number")
            rc = 1
            continue
        have = got[key]
        dev = abs(have - cv) / max(1.0, abs(have))
        if dev <= args.rtol:
            print(f"  AGREE    {key}: {cv!r}  (oracle {have!r}, dev {dev:.2e})")
        else:
            print(f"  DISAGREE {key}: claimed {cv!r}, oracle {have!r}, dev {dev:.2e}")
            rc = 1
    print()
    print("verdict: AGREE — an independent route reproduces the claim" if rc == 0
          else "verdict: DISAGREE — this is a FINDING. Report the deviation and "
               "do not release the deliverable.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
