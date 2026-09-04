---
name: edition-discipline
description: >
  Establish whether a standard's edition is actually pinned, find its
  supersession relationships, and record what changed between editions. Use
  whenever an acceptance criterion is set or cited, when a client's spec names a
  standard without an edition, or when existing analysis may rest on a
  superseded edition. Reports edition deltas that are sourced; refuses to
  produce ones that are remembered.
license: LicenseRef-AceEngineer-Commercial
metadata:
  version: "0.1"
  corpus: llm-wiki / wikis/engineering-standards
---

# edition-discipline

## The failure this exists to catch

A criterion applied from a superseded edition **still passes internal review**.
The clause number resolves, the method looks standard, the arithmetic is right,
and the number is quietly indefensible. Nothing in the output flags it.

That is why edition is not a detail of the citation. It *is* the citation.

## Step 1 — is the edition actually pinned?

```bash
../standards-lookup/scripts/search_standards.py --code api-rp-2sk
../standards-lookup/scripts/search_standards.py --unpinned      # the whole list
```

A page can occupy the `revision` field without pinning anything. These are
reported as `UNPINNED` and **must not be cited as an edition**:

| Value | Why it is not an edition |
|---|---|
| `latest` | A promise that expired silently. True when written, unverifiable now, wrong the moment a new edition ships. |
| `unknown` | Honest, and still not a citation. |
| `not-on-disk`, `n/a`, `tbd`, `current` | Placeholders that read as data. |

**65 of 310 corpus pages are currently unpinned.** If the standard governing
your criterion is one of them, that is a finding to report upward — not a gap to
close with an assumption about which edition was meant.

## Step 2 — what supersedes what

The corpus records supersession inconsistently. `scripts/edition_report.py`
surfaces what is there and, more usefully, what only looks like it is there:

```
supersession, structured field      19
supersession, prose only            47
supersession key present but EMPTY  35   (`supersedes: None`, `supersedes: ~`)
publisher rebrand recorded          15   (legacy_code_id; NOT supersession)
```

Read those numbers carefully. A first count of this corpus said **63** standards
recorded supersession structurally. The real figure is **19**. The difference
was publisher rebrands counted as supersession, and keys that exist while
asserting nothing — `supersedes: None` occupies a field and answers no question.

A prose mention is a **lead, not an assertion**. Read the page before relying on
it.

A superseded edition is not automatically wrong for the work in hand. A design
frozen under the 2005 edition is legitimately assessed against the 2005 edition.
What is never legitimate is *not knowing which one applies*.

## Step 3 — the delta, and the rule that governs it

When a criterion has moved between editions, record it as:

```yaml
code_id: api-rp-2sk
from_edition: "2e-1996"
to_edition: "3e-2005-r2008"
criterion: intact factor of safety, dynamic analysis
change: <what moved>
direction: tightened | relaxed | restructured | unchanged
consequence: <what it means for work done under the old edition>
source: <document and clause where this was READ, not recalled>
established_by: <who verified it, when>
```

**`source` is mandatory and cannot be a recollection.**

This skill will not produce edition deltas from memory, and neither should you.
Between-edition changes are exactly the class of fact a language model states
fluently and gets wrong, and a wrong delta is worse than none: it sends an
engineer to re-check work that was fine, or — far worse — reassures them about
work that was not.

To establish a delta you need both editions in front of you. Where the client
holds the documents, that is a legitimate and billable piece of work. Where
nobody holds them, the honest output is *"this criterion may have moved between
these editions; confirming it requires the documents."*

## What to hand back

```
GOVERNING:     <code_id> — <title>
EDITION:       <revision>          [or UNPINNED — state that plainly]
STATUS:        current | superseded by <code_id/edition> | withdrawn | unknown
SENSITIVITY:   <recorded deltas, each with its source>  [or: none established]
UNRESOLVED:    <what could not be confirmed, and what would confirm it>
```

`SENSITIVITY: none established` means nobody has checked. It does **not** mean
nothing moved, and it must never be written as though it did.
