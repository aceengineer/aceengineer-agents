#!/usr/bin/env python3
"""AceEngineer L3 verification gate.

PreToolUse hook. Blocks any write of an AceEngineer deliverable that does not
carry a verification record backed by a real PASS verdict on disk.

This is the mechanical form of the rule the orchestrator states in prose: no
engineering result leaves unverified. Prose can be talked around; this cannot.

Deliverable detection (either is sufficient):
  - the target path sits under a `deliverables/` directory, or
  - the content carries the marker `<!-- ace:deliverable -->`

Acceptance requires all three:
  1. a `## Verification record` section in the content
  2. a `ace:verdict: <path>` reference in that content
  3. that verdict file exists, parses, and reads {"verdict": "PASS"} with a
     non-empty `attempted` list

Fails open on its own internal errors (never blocks work because the gate
itself is broken) but fails closed on a missing or failing verdict.
"""
import json
import os
import re
import sys

MARKER = "<!-- ace:deliverable -->"
VERDICT_RE = re.compile(r"ace:verdict:\s*(\S+)")
RECORD_RE = re.compile(r"^#{1,6}\s*Verification record\b", re.M | re.I)


def deny(reason):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)
    sys.exit(0)


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    ev = json.loads(raw)

    tool = ev.get("tool_name", "")
    ti = ev.get("tool_input") or {}
    path = ti.get("file_path") or ""

    # Write carries the whole file; Edit carries only the replacement text, so a
    # deliverable being edited is judged on the new text plus the file on disk.
    content = ti.get("content") or ti.get("file_text") or ti.get("new_string") or ""
    if tool == "Edit" and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read() + "\n" + content
        except OSError:
            pass

    in_deliverables = f"{os.sep}deliverables{os.sep}" in path
    if not (in_deliverables or MARKER in content):
        sys.exit(0)  # not a deliverable; the gate has no opinion

    if not RECORD_RE.search(content):
        deny(
            "AceEngineer verification gate: this deliverable has no "
            "'## Verification record' section.\n\n"
            "No engineering result is released unverified. Dispatch "
            "ace-independent-verifier on this result in a fresh context, then "
            "record its verdict in the deliverable. If you are not writing a "
            "deliverable, remove the ace:deliverable marker or write outside "
            "deliverables/."
        )

    m = VERDICT_RE.search(content)
    if not m:
        deny(
            "AceEngineer verification gate: the verification record cites no "
            "verdict file.\n\n"
            "Add a line 'ace:verdict: <path>' pointing at the JSON verdict "
            "written by ace-independent-verifier. A verification record with "
            "no verdict artifact behind it is a claim, not a record."
        )

    vpath = m.group(1).strip().strip("`\"'")
    if not os.path.isabs(vpath):
        base = ev.get("cwd") or os.path.dirname(path) or "."
        cand = os.path.join(base, vpath)
        vpath = cand if os.path.exists(cand) else os.path.join(os.path.dirname(path), vpath)

    if not os.path.isfile(vpath):
        deny(
            f"AceEngineer verification gate: verdict file not found at {vpath}.\n\n"
            "The deliverable cites a verification that does not exist on disk. "
            "Run ace-independent-verifier and have it write its verdict before "
            "writing the deliverable."
        )

    try:
        with open(vpath, "r", encoding="utf-8") as fh:
            verdict = json.load(fh)
    except (OSError, ValueError) as exc:
        deny(f"AceEngineer verification gate: verdict at {vpath} is unreadable ({exc}).")

    v = str(verdict.get("verdict", "")).upper()
    if v != "PASS":
        findings = verdict.get("findings") or []
        deny(
            f"AceEngineer verification gate: verdict is {v or 'ABSENT'}, not PASS "
            f"({len(findings)} finding(s) open at {vpath}).\n\n"
            "Return the findings to the specialist, and re-run the verifier's "
            "own reproducer. A fix is accepted when the reproducer passes, not "
            "when it looks right."
        )

    if not verdict.get("attempted"):
        deny(
            f"AceEngineer verification gate: PASS at {vpath} records no "
            "'attempted' list.\n\n"
            "A PASS with no record of what was attempted to refute the result "
            "is void — the client cannot see the shape of the assurance."
        )

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # gate faults never block ordinary work
