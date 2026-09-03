"""Closed-form recomputation of the lazy-wave geometry from the equations alone.

Imports nothing but `math`. Exists so the result can be checked without the
digitalmodel package. Equations are stated in SPECIALIST-RESULT.md.
"""
import math

vd, sag, hog, q = 4000.0, 1200.0, 1500.0, 8.0
w, wb = 2456.695439714344, -2456.695439714344
wm, wbm = w, -wb

d1 = vd - sag                                  # 2800 m
th = math.radians(90.0 - q)                    # angle from horizontal at hang-off
a_w = d1 * math.cos(th) / (1.0 - math.cos(th)) # bare-riser catenary radius = H/w
a_b = a_w * wm / wbm                           # buoyed radius = H/|w_b|

S1 = a_w * math.tan(th)
X1 = a_w * math.asinh(math.tan(th))

def seg(a, d):
    X = a * math.acosh(d / a + 1.0)
    return a * math.sinh(X / a), X

d2 = (hog - sag) * wbm / (wbm + wm); S2, X2 = seg(a_w, d2)
d3 = (hog - sag) * wm  / (wbm + wm); S3, X3 = seg(a_b, d3)
d4 = hog * wm  / (wbm + wm);         S4, X4 = seg(a_b, d4)
d5 = hog * wbm / (wbm + wm);         S5, X5 = seg(a_w, d5)

S_tot = S1 + S2 + S3 + S4 + S5
X_tot = X1 + X2 + X3 + X4 + X5
closure = d1 - d2 - d3 + d4 + d5 - vd

Fh = w * a_w
Fv = w * S1                     # vertical tension component at hang-off
T  = math.hypot(Fh, Fv)

print(f"a_w (hang-off bend radius) = {a_w:.4f} m")
print(f"a_b (buoyed bend radius)   = {a_b:.4f} m")
for i,(S,X,d) in enumerate([(S1,X1,d1),(S2,X2,d2),(S3,X3,d3),(S4,X4,d4),(S5,X5,d5)],1):
    print(f"  seg{i}: S={S:10.4f} X={X:10.4f} d={d:9.4f}")
print(f"S_tot = {S_tot:.4f} m   X_tot = {X_tot:.4f} m   closure = {closure:.3e} m")
print(f"Fh = {Fh:.1f} N   Fv = {Fv:.1f} N   T = {T:.1f} N")
print(f"check T = w*(a_w+d1) = {w*(a_w+d1):.1f} N")
print(f"check declination = atan(Fh/Fv) = {math.degrees(math.atan2(Fh,Fv)):.6f} deg")
