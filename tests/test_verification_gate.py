#!/usr/bin/env python3
"""Behavioural tests for the AceEngineer L3 verification gate.

The gate is the product claim in mechanical form, so it gets tested like one:
every path that must block, and every path that must not.
"""
import json
import os
import subprocess
import sys
import tempfile

GATE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "plugins", "ace-engineer", "scripts", "verification_gate.py",
)
MARKER = "<!-- ace:deliverable -->"


def run(event):
    p = subprocess.run(
        [sys.executable, GATE], input=json.dumps(event),
        capture_output=True, text=True,
    )
    out = p.stdout.strip()
    if not out:
        return None
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


def write_verdict(d, name, payload):
    path = os.path.join(d, name)
    with open(path, "w") as fh:
        json.dump(payload, fh)
    return path


def event(tmp, content, path=None):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "cwd": tmp,
        "tool_input": {"file_path": path or os.path.join(tmp, "out.md"), "content": content},
    }


def main():
    failures = []

    def check(name, got, want):
        ok = got == want
        print(f"{'PASS' if ok else 'FAIL'}  {name}  (got {got!r}, want {want!r})")
        if not ok:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        # 1. Ordinary file: the gate has no opinion.
        check("ordinary write is untouched",
              run(event(tmp, "# notes\nsome working notes")), None)

        # 2. Marked deliverable, no verification record.
        check("deliverable without verification record is denied",
              run(event(tmp, MARKER + "\n# Mooring check\nUtilisation 0.82, PASS")), "deny")

        # 3. Path-based detection: deliverables/ directory.
        dpath = os.path.join(tmp, "deliverables", "mooring.md")
        os.makedirs(os.path.dirname(dpath), exist_ok=True)
        check("deliverables/ path without record is denied",
              run(event(tmp, "# Mooring check\nUtilisation 0.82", path=dpath)), "deny")

        # 4. Record present, but no verdict artifact cited.
        check("verification record citing no verdict file is denied",
              run(event(tmp, MARKER + "\n## Verification record\nVerified, looks fine.")), "deny")

        # 5. Verdict cited but absent from disk.
        check("cited verdict that does not exist is denied",
              run(event(tmp, MARKER + "\n## Verification record\nace:verdict: missing.json")), "deny")

        # 6. Verdict exists but is FINDINGS.
        write_verdict(tmp, "findings.json", {
            "verdict": "FINDINGS",
            "attempted": ["units"],
            "findings": [{"severity": "MAJOR", "class": "unit-conversion"}],
        })
        check("FINDINGS verdict is denied",
              run(event(tmp, MARKER + "\n## Verification record\nace:verdict: findings.json")), "deny")

        # 7. PASS verdict with no record of what was attempted.
        write_verdict(tmp, "hollow.json", {"verdict": "PASS", "attempted": []})
        check("PASS with empty attempted list is denied",
              run(event(tmp, MARKER + "\n## Verification record\nace:verdict: hollow.json")), "deny")

        # 8. The one accepted path.
        write_verdict(tmp, "pass.json", {
            "verdict": "PASS",
            "attempted": ["units and magnitude", "input provenance", "criterion edition"],
            "reproducer": "python3 check_mooring.py --case 100yr",
            "rounds": 2,
        })
        check("PASS verdict with attempted record is allowed",
              run(event(tmp, MARKER + "\n## Verification record\nace:verdict: pass.json")), None)

        # 9. Malformed input must never block ordinary work.
        check("garbage stdin does not block",
              run({"tool_name": "Write"}), None)

    print()
    if failures:
        print(f"{len(failures)} FAILED: {', '.join(failures)}")
        sys.exit(1)
    print("all gate tests passed")


if __name__ == "__main__":
    main()
