#!/usr/bin/env python3
"""Verifier's own route. Imports neither the solver nor the oracle.

Route 1: numerical quadrature of the catenary shape (no closed form).
Route 2: global vertical force equilibrium (no catenary formula at all).
Route 3: tangent identity Fv/Fh == tan(90 - declination), which is fixed by
         the INPUT angle alone and cannot depend on any solver internals.
"""
import math

W  = 2456.695439714344
WB = -2456.695439714344

def shape_numeric(d, a, n=4_000_000):
    """Arc length S and horizontal run X for vertical span d on catenary radius a,
    measured from a horizontal-tangent point. Pure quadrature: z(x)=a(cosh(x/a)-1),
    dS = cosh(x/a) dx. No closed form used."""
    X = a * math.acosh(d / a + 1.0)          # invert z(x) only to get the limit
    h = X / n
    tot = 0.0                                 # Simpson on cosh(x/a)
    for i in range(n + 1):
        x = i * h
        wgt = 1 if i in (0, n) else (4 if i % 2 else 2)
        tot += wgt * math.cosh(x / a)
    return tot * h / 3.0, X

def geometry(decl_deg, vdist, sag, hog, w, wb, from_vertical=True):
    theta = (90.0 - decl_deg) if from_vertical else decl_deg   # angle from horizontal
    c = math.cos(math.radians(theta))
    d1 = vdist - sag
    a_w = d1 * c / (1.0 - c)
    a_b = a_w * w / abs(wb)
    span = hog - sag
    k = w / abs(wb)
    d2, d3 = span / (1 + k), span * k / (1 + k)
    d4, d5 = hog * k / (1 + k), hog / (1 + k)
    segs = [(d1, a_w, w), (d2, a_w, w), (d3, a_b, wb), (d4, a_b, wb), (d5, a_w, w)]
    return theta, a_w, a_b, segs, (d1 - d2 - d3 + d4 + d5)

def run(label, decl=8.0, vdist=4000.0, sag=1200.0, hog=1500.0, w=W, wb=WB,
        from_vertical=True, numeric=False):
    theta, a_w, a_b, segs, closure = geometry(decl, vdist, sag, hog, w, wb, from_vertical)
    S, X, Fv_equilib = [], [], 0.0
    for d, a, wt in segs:
        if numeric:
            s, x = shape_numeric(d, a)
        else:
            s = math.sqrt(d * (2 * a + d)); x = a * math.asinh(s / a)
        S.append(s); X.append(x)
        Fv_equilib += wt * s            # ROUTE 2: sum of submerged weights, TDP has V=0
    Fh = w * a_w
    print(f"\n=== {label} ===")
    print(f"  angle-from-horizontal        {theta:.6f} deg")
    print(f"  a_w (hang-off bend radius)   {a_w:.10f} m")
    print(f"  a_b (buoyed radius)          {a_b:.10f} m")
    print(f"  segment S                    {' / '.join(f'{v:.4f}' for v in S)}")
    print(f"  total_S                      {sum(S):.10f} m")
    print(f"  total_X                      {sum(X):.10f} m")
    print(f"  closure residual             {closure - vdist:.3e} m")
    print(f"  Fh = w*a_w                   {Fh:,.3f}")
    print(f"  Fv  ROUTE2 (equilibrium)     {Fv_equilib:,.3f}")
    print(f"  Fv  = w*S1                   {w*S[0]:,.3f}")
    print(f"  Fv  = w*(S1+a_w)  [solver]   {w*(S[0]+a_w):,.3f}")
    print(f"  ROUTE3 required Fv/Fh = tan  {math.tan(math.radians(theta)):.9f}")
    print(f"    equilibrium  Fv/Fh         {Fv_equilib/Fh:.9f}")
    print(f"    solver       Fv/Fh         {w*(S[0]+a_w)/Fh:.9f}"
          f"   -> implied declination {90-math.degrees(math.atan(w*(S[0]+a_w)/Fh)):.4f} deg")
    print(f"  T = sqrt(Fh^2+Fv_eq^2)       {math.hypot(Fh, Fv_equilib):,.3f}")
    print(f"  T = w*(a_w+d1)               {w*(a_w+segs[0][0]):,.3f}")
    return a_w, sum(S), Fv_equilib

# --- ATTACK 1: closed form vs numerical quadrature (independent of any closed form)
run("BASE closed-form", numeric=False)
run("BASE numerical quadrature (Simpson, 4e6 panels)", numeric=True)

# --- ATTACK 2: units invariance on the weights
for scale, name in [(1.0, "N/m"), (1/9.80665, "kgf/m"), (0.06852177, "lbf/ft-ish"), (1e6, "absurd")]:
    a, s, fv = run(f"UNITS x{scale:g} ({name})", w=W*scale, wb=WB*scale)

# --- ATTACK 3: declination convention
run("DECL read from HORIZONTAL instead of vertical", from_vertical=False)

# --- ATTACK 4: is the exact equal-and-opposite pair load-bearing?
for pert in [0.0, 1e-12, 1e-6, 1e-3, 0.01, 0.05, 0.10]:
    wb = -W * (1.0 + pert)
    run(f"WEIGHT PAIR perturbed |wb|/w = {1+pert:.12f}", wb=wb)

# --- ATTACK 5: angle tolerance on the two requested numbers
for d in [7.5, 8.0, 8.5, 7.0, 9.0]:
    run(f"ANGLE {d} deg", decl=d)
