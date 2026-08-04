# Architecture

The plugin turns Claude Code into a small autonomous organization. The user
talks to one interface; work flows through specialized agents with bounded
context; quality judgment is independent of implementation.

## Hierarchy

```
USER
 │
 ▼
FABLE — CHIEF OF STAFF / INTENT INTERPRETER   (main session)
 │
 ▼
FABLE — CEO / ORCHESTRATOR                    (depth 1)
 │
 ├── FABLE — STRATEGY                         (depth 2)
 │        └── OPUS — RESEARCHER               (depth 3)
 │
 ├── OPUS — PRODUCT LEAD
 │        ├── OPUS — UX DESIGNER
 │        └── OPUS — PRODUCT INNOVATION
 │
 ├── OPUS — TECH LEAD
 │        ├── OPUS — RESEARCHER
 │        ├── OPUS — ENGINEER
 │        ├── OPUS — MECHANICAL ANALYST
 │        ├── SONNET — KNOWLEDGE MAINTAINER
 │        └── SONNET — BULK WORKER
 │
 └── FABLE — QUALITY / AUDIT
          ├── OPUS — TESTER
          └── OPUS — RESEARCHER
```

Leaf workers cannot spawn further agents (enforced by the routing hook AND by
`disallowedTools: [Agent]` in each leaf's frontmatter).

## Model policy

| Role | Model |
|---|---|
| Chief of Staff, CEO, Strategy, Quality | Fable |
| Product Lead, Tech Lead, UX, Innovation, Engineer, Researcher, Tester, Mechanical Analyst | Opus |
| Knowledge Maintainer, Bulk Worker | Sonnet |

Sonnet is an internal production service, never a decision-maker, and never
user-facing. Fable-designated work falls back to Opus when Fable is
unavailable — never to Sonnet. If neither Fable nor Opus is available for a
user-facing turn, fail visibly.

## Decision rights

| Decision | Owner |
|---|---|
| Recover what the user meant | Chief of Staff |
| Overall outcome | CEO |
| Whether strategy is sound | CEO informed by Strategy |
| Competitive/strategic recommendation | Strategy |
| What the product should do / UX behavior / acceptance criteria | Product Lead |
| Architecture / implementation / technical diagnosis | Tech Lead |
| Whether evidence supports release / evidence of observed failure | Quality |
| Product/Tech/Quality deadlock | CEO |
| Consequential unknowable user preference | User |

Agents may challenge another domain; they may not silently seize its decision
rights. No agent wins because of hierarchy alone — evidence decides.

## Information flow

Context is a scarce organizational resource. Transcripts are never forwarded
by default; information crosses boundaries as compressed contracts.

Downward (delegation packet):

```
MISSION / CONTEXT / INPUTS / CONSTRAINTS / SUCCESS / AUTHORITY / ESCALATE
```

Upward (report packet):

```
CONCLUSION / EVIDENCE / ARTIFACTS / RISKS / UNRESOLVED
```

Only sections that matter. No status-report theater.

## End-to-end workflow (substantial product request)

```
USER → Chief of Staff → clean intent brief → CEO
→ parallel discovery (Strategy ∥ Product ∥ Tech feasibility)
→ Strategy Gate → Strategic Product Brief
→ Product commits design → ACCEPTANCE.md frozen
→ Tech architecture → Freshness Gate → Research where required
→ bounded implementation → internal engineering tests
→ independent Quality (blind review) → adversarial testing
→ FAIL: repair loop / PASS: continue
→ Sonnet doc updates (Opus-reviewed) → CEO synthesis → Chief of Staff → USER
```

Gates:

- **Strategy Gate** — Strategy runs only when direction, market, monetization,
  positioning, or prioritization is meaningfully uncertain. Product cannot
  freeze requirements before relevant Strategy conclusions are incorporated.
- **Acceptance freeze** — Product writes `.claude/work/<task-id>/ACCEPTANCE.md`
  (externally observable success criteria) before broad implementation; frozen
  once Engineering begins; changes require CHANGE/WHY/REQUESTED BY/IMPACT.
- **Technical Freshness Gate** — no implementation may rely on an unverified
  externally mutable technical fact (versions, APIs, schemas, endpoints…)
  when current verification is reasonably available. Research verifies against
  current official sources and returns a compressed fact packet. Optional
  cache: `docs/DEPENDENCIES.md` (evidence of the previous decision, not proof
  it remains current).
- **Blind review** — Quality forms an independent view from intent, the
  strategy brief, frozen acceptance criteria, and the running artifact —
  before hearing Engineering's narrative.

## Defect flow

```
Tester → Quality → Product Lead (intended behavior)
       → Tech Lead (technical cause) → Engineer (fix or dispute)
```

Defect format: DEFECT ID / EXPECTED / OBSERVED / EVIDENCE / SEVERITY /
REPRODUCTION / ACCEPTANCE CRITERIA AFFECTED. Valid defects expand into
defect-family testing. Engineers dispute with evidence through the Tech Lead;
the CEO resolves cross-domain deadlock. Quality never modifies implementation.

## Routing enforcement

`hooks/enforce-agent-routing.py` (PreToolUse on the Agent tool) allows only
the edges drawn in the hierarchy above, denies everything else with a message
naming the owning manager, lets non-org agents/plugins pass through
untouched, and fails open on malformed input. Deterministic code — no LLM in
the decision path. See `docs/ENFORCEMENT.md` for what is and isn't
deterministically enforced.
