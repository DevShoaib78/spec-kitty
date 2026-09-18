---
schema_version: 1
artifact_type: spec-kitty.analysis-report
command: /spec-kitty.analyze
mission_slug: decide-out-of-matrix-test-dirs-01M2TKC7
mission_id: 01M2TKC7K6JBT3W7RGDZC7SNV1
generated_at: '2026-09-18T17:02:31.496010+00:00'
analyzer_agent: unknown
input_artifacts:
  spec.md:
    path: kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/spec.md
    sha256: 3113e66598a5fff4d8cbf4e18eb0b43e58b4df5667794697cb0920ce8c74829d
  plan.md:
    path: kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/plan.md
    sha256: b843f63d45d647026a86a0ba5a137f7dacef43311c56fb562dc225af23a7f607
  tasks.md:
    path: kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/tasks.md
    sha256: 7e8dffd095b775f4ba620f318dc2d29247b3532cd41f5e07a141c133dd07f178
  charter:
    path: .kittify/charter/charter.yaml
    sha256: b85bcc1cdd9e5d99905b4047f9f45ca2429b8a3e523268ecc10501ef39bfd71d
verdict: ready
issue_counts:
  low: 3
  medium: 1
  high: 0
  critical: 0
  info: 0
findings:
- id: U1
  severity: medium
  category: underspecification
  summary: WP03 T011 auth new-row leaves the row's `roots` source glob (src/specify_cli/<auth-source>/**) to be resolved during implementation; correct-by-design (evidence-driven) but not pinned in the plan.
- id: C1
  severity: low
  category: coverage
  summary: NFR-001..005 and SC-001..008 are traced in tasks.md prose but not carried in any WP `requirement_refs` (the CLI maps FRs only), so NFR/SC coverage is not machine-checkable.
- id: I1
  severity: low
  category: inconsistency
  summary: spec NFR-002 states a <=30-min shard bound while the real CI hard ceiling is timeout-minutes:40; plan.md reconciles this (30 = design budget, 40 = ceiling) but the spec NFR wording alone reads stricter than the enforced gate.
- id: V1
  severity: low
  category: coverage
  summary: WP02 (lift invariants) may resolve to a zero-lift no-op lane depending on the WP01 ledger; documented as expected, but a reviewer could misread the empty lane as an implementation miss.
---

## Specification Analysis Report

Mission: decide-out-of-matrix-test-dirs-01M2TKC7 (#4374). Artifacts analyzed: spec.md, plan.md (incl. post-plan squad amendments), tasks.md, WP01–WP04, contracts/, data-model.md, research.md. The artifacts were hardened by two adversarial squad passes (post-plan, post-tasks) whose findings are already folded, so cross-artifact consistency is high.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification | MEDIUM | WP03 T011 | auth row `roots` source glob resolved at implementation time | Acceptable — WP01 ledger identifies the auth source root; ensure T011 records the concrete `roots` and diffs it verbatim against the scrub group |
| C1 | Coverage | LOW | WP0*.md frontmatter | NFR/SC not in `requirement_refs` (CLI maps FRs only) | tasks.md prose traces them (NFR-001/002→T010, NFR-003→T010/T015, NFR-004→T014, NFR-005→T008/T012/T016/T017, SC-*→acceptance-checks); no action required |
| I1 | Inconsistency | LOW | spec.md NFR-002 vs plan.md | 30-min bound wording vs 40-min CI ceiling | plan.md already reconciles (design budget vs hard ceiling); optional spec footnote |
| V1 | Coverage | LOW | WP02 | possible zero-lift no-op lane | Already documented in WP02 as an expected recorded no-op |

**Coverage Summary (functional requirements):**

| Requirement | Has Task? | WPs | Notes |
|-------------|-----------|-----|-------|
| FR-001 single disposition | yes | WP01 | ledger assigns |
| FR-002 resolve pop-(a) | yes | WP01, WP03 | decide + execute |
| FR-003 resolve pop-(b) | yes | WP01, WP03 | decide + execute |
| FR-004 evidence-backed promotion | yes | WP03, WP04 | execute + permanent guard |
| FR-005 invariant lift | yes | WP02 | |
| FR-006 sharpened reason | yes | WP03, WP04 | execute + guard |
| FR-007 too-slow nightly | yes | WP03 | |
| FR-008 security-first | yes | WP01 | ordering |
| FR-009 honest-red | yes | WP03 | |
| FR-010 preserve exclusions | yes | WP03 | |
| FR-011 traceable | yes | WP01, WP04 | ledger + guard |

**Charter Alignment Issues:** none. Canonical-sources (reuse registry/scrub/timings machinery), honest-red routing, no-version-prescription, and Terminology Canon (no `feature*` identifiers) are all respected by the plan and WPs.

**Unmapped Tasks:** none. Every T001–T019 rolls into a WP tied to >=1 FR.

**Metrics:**
- Total functional requirements: 11 (100% task-covered)
- Non-functional requirements: 5 (all traced in tasks, not in requirement_refs — C1)
- Success criteria: 8
- Total subtasks: 19 across 4 WPs
- Critical issues: 0 · High: 0 · Medium: 1 · Low: 3

## Next Actions

No CRITICAL/HIGH findings → cleared to implement. U1 is an accept-with-note (evidence-driven by design); C1/I1/V1 are informational. Proceed to `/spec-kitty.implement` (or the implement-review loop). The load-bearing verification gaps the post-tasks squad found are already folded into WP03/WP04 as runnable, durable guards.
