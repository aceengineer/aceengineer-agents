#!/usr/bin/env bash
# Vendor the raw-to-knowledge ingestion methodology into the ace-knowledge plugin.
#
# Source is the dual-licensed raw-to-knowledge-playbook: documentation under
# CC-BY-4.0, which permits commercial use WITH ATTRIBUTION. The attribution is
# recorded in SKILLS-PROVENANCE.md and must not be removed -- it is a licence
# condition, not a courtesy.
#
#   ./scripts/sync-playbook-skills.sh            vendor
#   ./scripts/sync-playbook-skills.sh --verify   assert a byte-identical rebuild
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_REPO="${ACE_PLAYBOOK_SRC:-$REPO_ROOT/../raw-to-knowledge-playbook}"
SRC="$SRC_REPO/skills"
DEST="$REPO_ROOT/plugins/ace-knowledge/skills"
MANIFEST="$REPO_ROOT/plugins/ace-knowledge/SKILLS-PROVENANCE.md"

[ -d "$SRC" ] || { echo "FATAL: playbook skills not found at $SRC" >&2; exit 1; }

vendor_into() {
  local out="$1"; mkdir -p "$out"
  ( cd "$SRC" && find . -type f ! -name ".DS_Store" ! -name "*.alias" -print0 ) \
    | ( cd "$SRC" && tar --null -cf - --files-from=- ) | ( cd "$out" && tar -xf - )
}
tree_hash() { ( cd "$1" && find . -type f | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -d' ' -f1 ); }

if [ "${1:-}" = "--verify" ]; then
  [ -d "$DEST" ] || { echo "FAIL: nothing vendored at $DEST" >&2; exit 1; }
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  vendor_into "$TMP"
  if diff -r "$DEST" "$TMP" >/dev/null 2>&1; then
    echo "VERIFY PASS: playbook skills byte-identical to a fresh build"
    echo "  tree sha256: $(tree_hash "$DEST")"; exit 0
  fi
  echo "VERIFY FAIL" >&2; diff -r "$DEST" "$TMP" >&2 || true; exit 1
fi

rm -rf "$DEST"; vendor_into "$DEST"
SHA="$(git -C "$SRC_REPO" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
COUNT="$(find "$DEST" -name SKILL.md | wc -l | tr -d ' ')"

cat > "$MANIFEST" <<EOF
# Skills provenance — ace-knowledge

## Attribution (CC-BY-4.0 licence condition, not a courtesy)

These skills are adapted from the **raw-to-knowledge playbook** by Vamsee
Achanta, used under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

Source: <$(git -C "$SRC_REPO" remote get-url origin 2>/dev/null || echo "$SRC_REPO")>

Do not remove this section. CC-BY permits commercial use *provided appropriate
credit is given*; stripping the credit removes the permission.

## Build

| Field | Value |
|---|---|
| Source path | \`skills/\` |
| Source commit | \`$SHA\` |
| Uncommitted at sync time | $(git -C "$SRC_REPO" status --porcelain 2>/dev/null | wc -l | tr -d ' ') |
| SKILL.md count | $COUNT |
| Tree sha256 | \`$(tree_hash "$DEST")\` |
| Synced (UTC) | $(date -u +%Y-%m-%dT%H:%M:%SZ) |

\`\`\`bash
./scripts/sync-playbook-skills.sh --verify
\`\`\`
EOF
echo "Vendored $COUNT skills -> $DEST"
