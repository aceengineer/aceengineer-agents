#!/usr/bin/env bash
# Every check that must pass before a release. No network, no licences, no solver.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
rc=0
step() { echo; echo "=== $1 ==="; }

step "verification gate behaviour"
python3 tests/test_verification_gate.py || rc=1

step "independent oracle vs historical reference runs"
plugins/ace-marine-dynamics/authored-skills/independent-recompute/scripts/lazy_wave_oracle.py --self-test || rc=1

step "vendored skills reproduce byte-identically"
./scripts/sync-skills.sh --verify || rc=1

step "plugin manifests validate"
for p in plugins/*/; do
  out="$(claude plugin validate "$p" 2>&1)" || rc=1
  echo "$(basename "$p"): $(echo "$out" | tail -1)"
done

echo
[ $rc -eq 0 ] && echo "ALL CHECKS PASSED" || echo "CHECKS FAILED"
exit $rc
