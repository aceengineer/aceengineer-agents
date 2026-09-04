#!/usr/bin/env python3
"""AceEngineer tenancy gate — client material must not cross engagements.

PreToolUse hook. Denies file access to a SIBLING engagement's directory.

Why siblings specifically, rather than "everything outside the engagement root":
a gate that blocks every path outside one directory breaks reading the plugin's
own skills, the interpreter, the repo tooling -- and a gate that breaks ordinary
work gets switched off, which protects nobody. Precision here is not
permissiveness; it is what keeps the control alive.

The real exposure is narrow and specific: an agent working engagement A wanders
into engagement B, sitting next to it on disk, and carries B's material into A's
deliverable. That is what this denies.

  engagement_root = /work/engagements/client-a
  parent          = /work/engagements
  -> /work/engagements/client-b/**  DENIED
  -> /work/engagements/client-a/**  allowed
  -> /usr/lib/python3/**            allowed (not a sibling engagement)

Fails CLOSED on a sibling hit. Fails OPEN on its own internal errors: a broken
gate must never block ordinary work, but a genuine cross-tenant read must always
be blocked.
"""
import json
import os
import re
import sys

MARKER = ".ace-engagement"          # optional: marks a directory as an engagement


def deny(reason):
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, sys.stdout)
    sys.exit(0)


def candidate_paths(ev):
    """Every filesystem path this tool call might touch."""
    ti = ev.get("tool_input") or {}
    out = []
    for k in ("file_path", "path", "notebook_path"):
        if ti.get(k):
            out.append(str(ti[k]))
    # Bash: pull absolute-looking paths out of the command string. Coarse by
    # design -- a false positive costs one prompt, a false negative costs a
    # client's confidential material.
    cmd = ti.get("command")
    if cmd:
        out += re.findall(r"(?<![\w:])(/[A-Za-z0-9_./\-]{4,})", str(cmd))
    return out


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    ev = json.loads(raw)

    root = os.environ.get("CLAUDE_PLUGIN_OPTION_ENGAGEMENT_ROOT", "").strip()
    client = os.environ.get("CLAUDE_PLUGIN_OPTION_CLIENT_ID", "").strip() or "(unset)"
    if not root:
        sys.exit(0)                       # nothing declared, nothing to enforce

    root = os.path.realpath(os.path.expanduser(root))
    parent = os.path.dirname(root)
    if not parent or parent == os.sep:
        sys.exit(0)                       # engagement at filesystem root: no siblings

    for p in candidate_paths(ev):
        try:
            ap = os.path.realpath(os.path.expanduser(p)) if os.path.isabs(p) \
                else os.path.realpath(os.path.join(ev.get("cwd") or ".", p))
        except OSError:
            continue
        if ap == root or ap.startswith(root + os.sep):
            continue                       # our own engagement
        if ap == parent or not ap.startswith(parent + os.sep):
            continue                       # not a sibling of this engagement

        sibling = ap[len(parent) + 1:].split(os.sep)[0]
        deny(
            f"AceEngineer tenancy gate: '{sibling}' is a different engagement.\n\n"
            f"This session is scoped to client '{client}' at {root}. "
            f"Reading or writing {ap} would move material between engagements.\n\n"
            "Client corpora never cross engagements. That is a contractual "
            "boundary, not a preference — a plugin that ships one client's "
            "knowledge into another's work is a breach, not a bug.\n\n"
            "If you genuinely need material from another engagement, that is a "
            "question for the client who owns it, not a file read."
        )
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)          # gate faults never block ordinary work
