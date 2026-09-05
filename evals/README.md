# Evals — does the agent chain behave, not just the tools

`tests/run_all.sh` proves the **tools** work: gates fire, oracles reproduce
identities, corpora resolve. It says nothing about whether the **agents** reach
the right answer, or refuse the wrong one.

That is what these cases test, and they are written around the failure modes
this product exists to prevent — not around happy paths, which prove little.

## Why this is not `claude plugin eval`

`claude plugin eval` is the right home for these. It reports
*"currently in early access"* on this account, `eval init` produces nothing, and
the `case.yaml` schema is absent from public documentation. Authoring against it
would be guessing at a gated, undocumented format.

So each case is a `case.yaml` in the **schema documented below**, driven by a
local runner. When early access lands the prompts and expectations transfer
directly; only the runner is thrown away.

## Running

```bash
./evals/run_evals.py                 # all cases, with the no-plugin baseline
./evals/run_evals.py --case refuses-unpinned-edition
./evals/run_evals.py --no-baseline   # skip the ablation arm (faster)
```

Each case runs a real headless session with the plugins loaded, so it costs
time and tokens. The suite is deliberately small and high-signal.

## Case schema

```yaml
name: refuses-unpinned-edition
description: what behaviour this pins, and why it matters
prompt: |
  the request put to the agent
plugins: [ace-standards]          # loaded via --plugin-dir
allowed_tools: "Read,Bash,Glob,Grep"
config:                            # plugin userConfig, optional
  standards_corpus_path: ""
expect:
  must_contain:     ["..."]        # case-insensitive substrings
  must_not_contain: ["..."]        # the important half
  must_match:       ["regex"]
baseline:                          # the ablation arm
  should_fail: true                # without the plugin, this SHOULD fall over
```

`must_not_contain` carries most of the weight. It is easy to make an agent say
something; the product claim is that it **declines** to say things it cannot
support.

## The baseline arm matters most

Every case also runs **without the plugins**. If the no-plugin arm passes too,
the plugin did nothing and the case proves nothing. A case is only evidence when
the arms differ — that difference is the entire commercial claim, and it is the
number to put in front of a buyer.
