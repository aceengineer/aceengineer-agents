# Notice — corpus provenance and an open licensing question

The marine-offshore skill corpus vendored into `plugins/ace-marine-dynamics/skills/`
is copied from `github.com/vamseeachanta/workspace-hub`, path
`.claude/skills/engineering/marine-offshore`.

**Two facts to resolve before this marketplace is published:**

1. **`workspace-hub` is a public repository with no `LICENSE` file.** Absent a
   licence grant, the content is all-rights-reserved to the copyright holder, so
   vendoring it here is clean. But the corpus is nonetheless publicly readable at
   its source, which undercuts a paid licence for the same content. Decide
   deliberately: move the corpus to a private repository, or accept that the
   commercial value sits in the orchestration, verification gate, and support
   rather than in the skill text.

2. **Copyright holder vs. licensor.** `workspace-hub`, `digitalmodel`,
   `assetutilities` and the rest are owned by the personal GitHub account
   `vamseeachanta`, while this marketplace licenses as Achanta AceEngineer Inc.
   Record an assignment or licence from the individual to the company so the
   entity granting the commercial licence is the entity that holds the rights.

Neither is a code problem. Both are cheap to fix now and expensive to fix after
the first customer.
