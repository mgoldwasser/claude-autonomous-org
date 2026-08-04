---
name: phase0-audit
description: Phase 0 instruction and memory audit: discover every loaded instruction, atomize, test each directive, archive debt (never delete), rebuild minimal stack with reversible before/after report. Use to audit, clean up, or minimize CLAUDE.md, rules, skills, or memory.
---

# Phase 0 — Instruction and Memory Audit

Principle: existing configuration is presumed guilty of accumulated prompt
debt until reviewed. Never permanently delete — archive everything replaced.

## 1. Discover every instruction source

Audit everything Claude may be carrying:

- managed CLAUDE.md instructions (report only — never modify managed policy);
- `~/.claude/CLAUDE.md`; project `CLAUDE.md`; `.claude/CLAUDE.md`; all
  `CLAUDE.local.md`; nested `CLAUDE.md`;
- every user/project `.claude/rules/**/*.md`;
- recursively imported instruction files;
- user/project custom skills and agents (their system prompts impose behavior);
- hooks and hook scripts containing behavioral logic;
- relevant behavioral settings;
- auto-memory: `MEMORY.md` and topic files;
- any other locally discovered persistent source of behavioral instruction.

Determine what ACTUALLY loads — do not rely on assumed locations. Use
instruction-loading observability where available (e.g. `/context`,
`/memory`, debug output) and independently scan known locations. Record per
source: file path, scope, loading reason, imported parent, eager vs
conditional loading.

## 2. Atomize

Break each active source into the smallest meaningful behavioral directives —
one thing Claude is told to do or not do. Headings, explanations, examples,
metadata, and factual project documentation are not rules unless they impose
behavior.

## 3. Audit every directive

- **A. Baseline test** — would the current model probably do this correctly
  without being told? Yes → ARCHIVE.
- **B. Obsolescence test** — was this added to correct a model weakness that
  current models/Claude Code no longer materially exhibit? Judge against
  current behavior and current official documentation, not memory. Yes →
  ARCHIVE.
- **C. Conflict test** — does it conflict with another active instruction,
  system behavior, hook, setting, managed policy, agent responsibility, or
  newer rule? If yes: identify both, determine precedence, archive the
  redundant/lower-authority user-controlled one, flag unmodifiable managed
  conflicts.

For survivors, two practical questions:

- Would failure to retain this create a meaningful recurring error? No →
  ARCHIVE.
- Is it stored in the cheapest correct mechanism? Hard setting/permission for
  deterministic enforcement; hook for lifecycle enforcement; CLAUDE.md for
  universal persistent behavior; path-scoped rule for path-specific behavior;
  skill for a sometimes-needed multi-step procedure; agent prompt for
  role-specific behavior; ordinary docs for on-demand facts. Do not put
  everything in CLAUDE.md.

## 4. Archive (never delete)

Before changing anything: timestamped archive with manifest, original
relative paths preserved, sha256 checksums recorded. Locations:

```
~/.claude/archive/instruction-audit/<timestamp>/        (user scope)
<project>/.claude/archive/instruction-audit/<timestamp>/ (project scope)
```

Keep scopes separate. Get user consent before moving files.

## 5. Rebuild from zero

Do not edit the stack down incrementally. Archive obsolete sources, then
reconstruct the active stack from retained directives only: rewrite each in
the fewest words preserving meaning, eliminate duplicates across mechanisms,
confirm no archived rule still loads through an import.

## 6. Disable automatic behavioral memory

Set `"autoMemoryEnabled": false` (with consent). The organization manages
persistent behavioral learning explicitly via the two-strike rule
(`correction-ledger` skill). Project facts belong in on-demand project docs.

## 7. Report

Produce `instruction-audit-before.md`, `instruction-audit-after.md`, and
`instruction-audit-manifest.json` in the archive directory, containing:

```
INSTRUCTION AUDIT

Before / After
--------------
Files:
Atomic rules:
Active instruction words:
CLAUDE.md rules:  Rules-file rules:  Skill directives:
Agent directives: Hook-enforced behaviors:  Memory directives:

Reduction
---------
Rules removed:  Words removed:  Percent reduction:
```

Then a table of every directive: Source | Original directive | Action
(Kept/Archived/Rewritten) | Reason. The report must be specific enough to
reverse every decision manually. Verify after restart that archived
instructions no longer load and metrics match actual files.
