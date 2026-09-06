#!/usr/bin/env python3
"""Run the AceEngineer agent evals (#257).

Stands in for `claude plugin eval`, which is in early access on this account and
whose case schema is undocumented. Each case runs a real headless session with
the plugins loaded and grades the transcript.

Every case also runs WITHOUT the plugins. If the no-plugin arm passes too, the
plugin did nothing and the case proves nothing. Only the difference between the
arms is evidence.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CASES = os.path.join(HERE, "cases")


def load_yaml(path):
    """Minimal reader for this suite's fixed case shape (no dependency)."""
    d, key, stack = {}, None, []
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.strip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\w[\w_]*):\s*(.*)$", ln)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val in ("|", ">"):
                buf, i = [], i + 1
                while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                    buf.append(lines[i][2:])
                    i += 1
                d[key] = "\n".join(buf).strip()
                continue
            if val.startswith("[") and val.endswith("]"):
                d[key] = [x.strip().strip('"\'') for x in val[1:-1].split(",") if x.strip()]
            elif val:
                d[key] = val.strip('"\'')
            else:
                d[key] = {}
                stack = [(key, d[key])]
            i += 1
            continue
        sm = re.match(r"^  (\w[\w_]*):\s*(.*)$", ln)
        if sm and stack:
            k2, v2 = sm.group(1), sm.group(2).strip()
            if v2:
                stack[0][1][k2] = v2.strip('"\'')
            else:
                stack[0][1][k2] = []
                stack = [stack[0], (k2, stack[0][1][k2])]
            i += 1
            continue
        lm = re.match(r"^    - (.*)$", ln)
        if lm and len(stack) > 1:
            stack[1][1].append(lm.group(1).strip().strip('"\''))
            i += 1
            continue
        i += 1
    return d


RUNS = os.path.join(HERE, "runs")


def save(name, arm, text):
    """Keep every transcript. A failing eval you cannot read is not a result --
    it is a rumour, and re-running to find out costs more than the disk."""
    os.makedirs(RUNS, exist_ok=True)
    path = os.path.join(RUNS, f"{name}.{arm}.txt")
    open(path, "w", encoding="utf-8").write(text)
    return path


def run_case(case, with_plugins, timeout):
    cmd = ["claude", "-p", case["prompt"]]
    if with_plugins:
        for p in case.get("plugins", []):
            cmd += ["--plugin-dir", os.path.join(ROOT, "plugins", p)]
    cmd += ["--allowedTools", case.get("allowed_tools", "Read,Bash")]
    env = dict(os.environ)
    for k, v in (case.get("config") or {}).items():
        env[f"CLAUDE_PLUGIN_OPTION_{k.upper()}"] = v
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               cwd=tmp, env=env, stdin=subprocess.DEVNULL)
            return r.stdout + "\n" + r.stderr
        except subprocess.TimeoutExpired:
            return "__TIMEOUT__"


def grade(case, out):
    exp = case.get("expect", {}) or {}
    fails = []
    if out == "__TIMEOUT__":
        return ["run timed out"]
    for s in exp.get("must_contain", []):
        if s.lower() not in out.lower():
            fails.append(f"missing required text: {s!r}")
    for s in exp.get("must_not_contain", []):
        if s.lower() in out.lower():
            fails.append(f"contains forbidden text: {s!r}")
    for pat in exp.get("must_match", []):
        if not re.search(pat, out):
            fails.append(f"no match for pattern: {pat!r}")
    for pat in exp.get("must_not_match", []):
        m = re.search(pat, out)
        if m:
            fails.append(f"matched forbidden pattern {pat!r} at {m.group(0)!r}")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--timeout", type=int, default=240)
    args = ap.parse_args()

    names = sorted(os.listdir(CASES))
    if args.case:
        names = [n for n in names if n == args.case]
    if not names:
        print("no matching cases", file=sys.stderr)
        return 2

    rows, hard_fail = [], False
    for n in names:
        path = os.path.join(CASES, n, "case.yaml")
        if not os.path.isfile(path):
            continue
        case = load_yaml(path)
        print(f"\n=== {case.get('name', n)} ===")

        out = run_case(case, True, args.timeout)
        p1 = save(case.get("name", n), "plugin", out)
        fails = grade(case, out)
        arm = "PASS" if not fails else "FAIL"
        print(f"  with plugins:   {arm}")
        for f in fails:
            print(f"      {f}")
        if fails:
            print(f"      transcript: {os.path.relpath(p1, ROOT)}")
        if fails:
            hard_fail = True

        base = "-"
        if not args.no_baseline:
            bout = run_case(case, False, args.timeout)
            save(case.get("name", n), "baseline", bout)
            bfails = grade(case, bout)
            base = "PASS" if not bfails else "FAIL"
            print(f"  without plugins: {base}"
                  + ("   <- plugin made no difference on this case" if base == "PASS" else ""))
        rows.append((case.get("name", n), arm, base))

    print("\n" + "=" * 62)
    print(f"{'case':34s} {'plugin':>8s} {'baseline':>9s}  delta")
    print("-" * 62)
    for name, a, b in rows:
        delta = "yes" if (a == "PASS" and b == "FAIL") else ("—" if b == "-" else "NO")
        print(f"{name:34s} {a:>8s} {b:>9s}  {delta}")
    print("\n'delta: yes' is the only row that is evidence. A case passing in both")
    print("arms shows the plugin changed nothing.")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
