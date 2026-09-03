---
name: engagement-intake
description: >
  Establishes the analysis frame before any offshore/marine engineering work
  begins — asset, analysis class, governing standard and edition, acceptance
  criterion, environment basis, and deliverable. Converts every gap into an
  explicitly stated assumption. Use at the start of every AceEngineer
  engagement and whenever a request arrives underspecified.
license: LicenseRef-AceEngineer-Commercial
metadata:
  version: "0.1"
  status: template
---

# engagement-intake

An underspecified request is the most common root cause of a wrong deliverable.
The frame below is established **before** analysis, and every unresolved item
becomes a recorded assumption rather than a silent default.

## The frame

### 1. Asset and configuration
- Asset type: FPSO / semi / spar / TLP / jacket / subsea / installation vessel
- Water depth, field, and region
- Configuration: mooring pattern, riser arrangement, station-keeping mode
- Design life, and where in it this asset currently sits

### 2. Analysis class
Strength · fatigue · installation · operability · extreme response · modal ·
interference · thermal. Naming the class fixes the method; leaving it implicit
lets the method drift.

### 3. Governing standard — **with edition**
- API RP 2SK / 2SM / 2RD / 16Q, DNV-OS-E301 / RP-F204, ABS, ISO 19901-7 …
- **Edition and year are mandatory.** Criteria move between editions; a clause
  number without an edition is not a citation.
- Where the client's internal spec overrides the standard, capture that too.

### 4. Acceptance criterion
The exact number that decides pass/fail, and its basis:
- Safety factor / utilisation limit, and intact vs damaged case
- Fatigue: SN curve, SCF, design fatigue factor
- Allowable offset, tension, curvature, clearance

If nobody can name the criterion, the engagement is not ready to start.

### 5. Environment basis
- Return period (1-yr / 10-yr / 100-yr / 10 000-yr) and the metocean source
- Sea state basis: Hs/Tp pairs, spectrum and spreading
- Directionality: omni vs directional, and the sectors
- Current profile and wind, including whether they are collinear
- Water level: tide, surge, subsidence

### 6. Deliverable
- What the client hands to whom — internal review, class society, regulator, bid
- Format and the review path it must survive
- Date, and what is downstream of it

## Gap handling

Every item above resolves to one of exactly three states:

| State | Handling |
|---|---|
| **Given** | Record the value and its source document |
| **Derived** | Record the value, the derivation, and the inputs it came from |
| **Assumed** | Record the assumption verbatim, plus which way it is conservative |

An assumption with no stated direction of conservatism is incomplete — the
verifier will test whether it flips the answer, so state it first.

## Output

A frame block that the specialist and the verifier both work from:

```
ASSET:      <type, depth, field>
CLASS:      <analysis class>
STANDARD:   <standard, edition, year, clause>
CRITERION:  <the pass/fail number>
ENVIRONMENT:<return period, source, directionality>
DELIVERABLE:<artifact, recipient, date>
GIVEN:      <list with sources>
DERIVED:    <list with derivations>
ASSUMED:    <list, each with direction of conservatism>
```

This block is reproduced verbatim in the final deliverable. It is the contract
between what was asked and what was answered.
