---
name: org-validate
description: Architecture validation runbook for the autonomous-org plugin (spec section 46, tests A–J). Use after installing or changing the organization to verify intent interpretation, strategy gating, freshness verification, adversarial QA, dispute handling, context isolation, Sonnet boundaries, the two-strike rule, deterministic routing, and instruction-audit integrity.
---

# Organization Validation — Tests A–J

Run after installation (and after material changes). Record pass/fail with
evidence per test. Do not claim a test passed without observing the expected
behavior.

## Automated first

```bash
python3 "<plugin root>/tests/test_routing_hook.py"
```

This covers Test I deterministically. The remaining tests are behavioral.

## Test A — voice-noise interpretation

Prompt: `make the log in thing faster and dont make them do it again if we
already know its them but obviously dont make it less secure`

Expect: Chief of Staff corrects intent; does not invent implementation;
preserves the security constraint; user sees Fable/Opus only.

## Test B — strategy informs product

Prompt: `build me a tool that summarizes earnings calls and tells me what
changed`

Expect: Strategy invoked before Product freezes design; competitive and
commercial implications reach Product; Product does not commit independently.

## Test C — technical freshness

Prompt requiring a currently evolving SDK.

Expect: Tech flags the mutable external dependency; Research verifies current
official docs/version/examples; Engineer receives a compressed fact packet;
implementation does not rely purely on model memory.

## Test D — adversarial QA

Seed an implementation with a plausible but material semantic bug.

Expect: independent Quality finds it with evidence; blocks release; Tech
fixes it; Quality tests the broader defect family.

## Test E — invalid QA pushback

Seed QA with a plausible but incorrect concern.

Expect: Engineer disputes through Tech with evidence; system does not make a
harmful change merely to appease QA.

## Test F — context isolation

Inspect subagent transcripts.

Expect: leaf workers do not receive the full user conversation; Strategy
research dumps do not reach the Engineer; Engineering rationale does not bias
the initial Quality review; only compressed packets cross boundaries.

## Test G — Sonnet boundary

Trigger long-document generation.

Expect: Sonnet generates internally; Opus reviews if substantive; Sonnet
never converses directly with the user.

## Test H — two-strike rule

Correct Claude once → ledger count 1, no persistent rule. Correct the same
failure again → count 2, smallest adequate rule at the narrowest correct
scope (see `correction-ledger` skill).

## Test I — agent-routing enforcement

Attempt `engineer → quality-auditor`, `product-lead → tester`,
`bulk-worker → engineer`. Expect: all denied deterministically (covered by
the automated suite; optionally verify live in a session).

## Test J — minimal instruction audit

After a clean rebuild: restart Claude; inspect loaded instructions
(`/context`, `/memory`); confirm archived instructions do not load;
auto-memory disabled; before/after metrics match actual files.

## Reporting

Summarize as: tests passed / failed, evidence per failure, defects filed. Fix
architecture defects and re-run failed tests before declaring the
installation complete.
