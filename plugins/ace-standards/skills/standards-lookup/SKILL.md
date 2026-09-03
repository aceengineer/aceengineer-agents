---
name: standards-lookup
description: >
  Resolve which standard governs a piece of offshore or marine engineering work,
  and — critically — which edition. Searches the AceEngineer standards corpus by
  code identifier, publisher, or subject and returns publisher/revision metadata
  and the corpus page. Use whenever a standard is cited, an acceptance criterion
  is set, or an edition is in doubt. Metadata only: this skill resolves the
  citation, it never reproduces clause text.
license: LicenseRef-AceEngineer-Commercial
metadata:
  version: "0.1"
  corpus: llm-wiki / wikis/engineering-standards
---

# standards-lookup

## Why edition, not just standard

"API RP 2SK" is not a citation. Acceptance criteria, safety factors and load
cases move between editions, and a criterion applied from the wrong edition is
wrong in a way that reviews rarely catch — the clause number still resolves, the
method still looks standard, and the number is quietly indefensible.

Every standard this skill returns carries a `revision`. Where the corpus records
no revision, it prints `UNRECORDED <-- edition unconfirmed`. That is a finding,
not a formatting quirk: report it upward rather than assuming the current edition.

## Usage

```bash
scripts/search_standards.py "mooring fatigue"          # free text
scripts/search_standards.py --code api-rp-2sk          # by code identifier
scripts/search_standards.py --publisher DNV --tag riser
scripts/search_standards.py --corpus /path/to/corpus "viv"
```

Corpus path resolves from `--corpus`, then `$ACE_STANDARDS_CORPUS`, then the
plugin's `standards_corpus_path` user config.

Exit codes: `0` matches, `1` no match, `2` no corpus configured or reachable.

## The firewall — read before answering

The corpus is **metadata-first**. It holds publisher facts, revision years,
document identifiers, corpus paths, and authored summaries. It does **not** hold
copied clause text, tables or figures, and neither do you.

When a task needs exact clause text:

1. Resolve the code identifier and edition here.
2. **Stop.** Name the document and clause.
3. Route the client to an authorised standards holder — their own subscription,
   the publisher, or their class society.

Never reconstruct a clause from memory, from the summary, or from an adjacent
standard. A reconstructed clause that is 90% right is more dangerous than no
clause at all, because it reads as authoritative.

## When there is no corpus

Exit code `2` means the corpus is not configured. Say so plainly and stop. Do
not answer editions from recollection — recollection of editions is precisely
the thing that is unreliable, and it is the reason this corpus exists.

## When there is no match

Exit code `1` means *this corpus has no page for it*, which is not the same as
the standard not existing. Report the distinction. Never substitute a
neighbouring standard for the one that was asked about.
