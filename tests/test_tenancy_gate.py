#!/usr/bin/env python3
"""Behavioural tests for the AceEngineer tenancy gate.

The contractual claim is "client corpora never cross engagements". That claim
gets tested like a control: every path that must block, and -- just as
important -- every path that must NOT, because a gate that blocks ordinary work
gets switched off and then protects nobody.
"""
import json
import os
import subprocess
import sys
import tempfile

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "plugins", "ace-knowledge", "scripts", "tenancy_gate.py")


def run(event, root, client="client-a"):
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_OPTION_ENGAGEMENT_ROOT"] = root
    env["CLAUDE_PLUGIN_OPTION_CLIENT_ID"] = client
    p = subprocess.run([sys.executable, GATE], input=json.dumps(event),
                       capture_output=True, text=True, env=env)
    out = p.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


def ev(tool, **ti):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti}


def main():
    fails = []

    def check(name, got, want):
        ok = got == want
        print(f"{'PASS' if ok else 'FAIL'}  {name}  (got {got!r}, want {want!r})")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        eng = os.path.join(tmp, "engagements")
        a = os.path.join(eng, "client-a")
        b = os.path.join(eng, "client-b")
        for d in (a, b):
            os.makedirs(os.path.join(d, "docs"), exist_ok=True)
            open(os.path.join(d, "docs", "report.md"), "w").write("x")

        # must ALLOW
        check("read inside our own engagement",
              run(ev("Read", file_path=os.path.join(a, "docs/report.md")), a), None)
        check("write inside our own engagement",
              run(ev("Write", file_path=os.path.join(a, "out.md"), content="x"), a), None)
        check("read an unrelated system path",
              run(ev("Read", file_path="/usr/lib/python3.9/os.py"), a), None)
        check("read the plugin's own files",
              run(ev("Read", file_path=GATE), a), None)
        check("no engagement configured -> gate is inert",
              run(ev("Read", file_path=os.path.join(b, "docs/report.md")), ""), None)

        # must DENY
        check("read a sibling engagement",
              run(ev("Read", file_path=os.path.join(b, "docs/report.md")), a), "deny")
        check("write into a sibling engagement",
              run(ev("Write", file_path=os.path.join(b, "leak.md"), content="x"), a), "deny")
        check("grep across a sibling engagement",
              run(ev("Grep", path=b), a), "deny")
        check("bash cp out of a sibling engagement",
              run(ev("Bash", command=f"cp {b}/docs/report.md ."), a), "deny")
        check("bash cat of a sibling path",
              run(ev("Bash", command=f"cat {b}/docs/report.md | head"), a), "deny")

        # relative paths resolved against cwd still count
        e = ev("Read", file_path="../client-b/docs/report.md")
        e["cwd"] = a
        check("relative path escaping into a sibling", run(e, a), "deny")

        # robustness
        check("malformed input does not block", run({"tool_name": "Read"}, a), None)

    print()
    if fails:
        print(f"{len(fails)} FAILED: {', '.join(fails)}")
        return 1
    print("all tenancy tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
