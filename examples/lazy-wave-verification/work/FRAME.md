# Engagement frame — lazy-wave riser geometry

ASSET:       Not stated. Flexible/lazy-wave riser, hang-off to seabed vertical
             distance 4000 m. Host vessel type, field, region: NOT GIVEN.
CLASS:       Static geometry / configuration (shape) analysis. Not strength,
             not fatigue, not extreme response.
STANDARD:    NOT GIVEN. No standard or edition named by the client.
CRITERION:   NONE GIVEN. The request asks to "confirm" two geometric
             quantities; no pass/fail number was supplied.
ENVIRONMENT: NOT GIVEN. No return period, sea state, current profile,
             directionality, or water level. Treated as still-water static.
DELIVERABLE: deliverables/lazy-wave-geometry.md — hang-off bend radius and
             total suspended length, with basis. Recipient/date NOT GIVEN.

GIVEN (source: REQUEST.md, client email body, no source document cited):
  vertical distance (hang-off to seabed) : 4000 m
  sag bend elevation                     : 1200 m
  hog bend above seabed                  : 1500 m
  hang-off declination                   : 8 deg
  weight without buoyancy                : 2456.695439714344   [UNITS NOT GIVEN]
  weight with buoyancy                   : -2456.695439714344  [UNITS NOT GIVEN]

DERIVED: (to be filled by specialist)

ASSUMED:
  A1. Weights are distributed weight per unit length in N/m (submerged).
      Direction of conservatism: none — a unit error scales forces linearly
      and does not cancel. LOAD-BEARING for any force result.
  A2. Still water, no current, no vessel offset; static catenary equilibrium.
      Conservatism: unconservative for real offsets; geometry only.
  A3. Riser is inextensible and torsionally free; no bending stiffness in the
      catenary shape (bend radius is the elastic-free catenary radius).
      Conservatism: slightly unconservative at the hang-off (real bend
      stiffener increases local radius).
  A4. Seabed is flat and horizontal at 4000 m below hang-off.
  A5. No standard governs this result; it is a geometry confirmation, not a
      code check. No pass/fail is asserted.

OPEN QUESTION (flagged to client, not blocking geometry):
  Q1. "weight with buoyancy" is the exact arithmetic negative of "weight
      without buoyancy" to 16 significant figures. That is a suspicious
      pairing — it is the signature of a placeholder/default rather than a
      measured buoyancy-module property. Confirm against the riser cross-
      section data sheet.
