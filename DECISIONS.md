# Decision Log

Use this file for decisions that materially shape architecture, delivery, security, operations, cost, or reversibility. Append records; do not erase history. A later record may supersede an earlier one.

## Record Template

### D-XXX — Title

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded | Rejected
- **Context:** What requires a durable choice?
- **Decision:** What was chosen?
- **Rationale:** Why is this the best fit?
- **Alternatives:** What credible options were considered?
- **Consequences:** What benefits, costs, risks, and follow-up result?
- **Evidence / follow-up:** PRs, work items, revisions, tests, or review records.

## D-001 — GitHub is the permanent source of truth

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** Work needs a durable, auditable collaboration record.
- **Decision:** GitHub history and pull requests or equivalent GitHub-linked records are authoritative. Evidence identifies the exact revision verified and released.
- **Rationale:** One remote source reduces divergence and supports review, recovery, and auditability.
- **Alternatives:** Untracked local work or multiple authoritative copies; rejected because they weaken traceability.
- **Consequences:** Material work uses isolated branches and durable review before `main`.
- **Evidence / follow-up:** `WORKFLOW.md` and `.github/PULL_REQUEST_TEMPLATE.md`.

## D-002 — Independent, evidence-based delivery gates

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** The product owner delegates technical execution and will not inspect or maintain code.
- **Decision:** Different agents implement, independently review, test, and release material work. Triggered Security Review is separately independent. Objective evidence and the shared severity model control approval.
- **Rationale:** Separation and observable evidence reduce blind spots and self-approval.
- **Alternatives:** Self-review or informal claims; rejected as insufficient assurance.
- **Consequences:** Repairs create a new candidate; affected evidence is rerun or independently declared unaffected.
- **Evidence / follow-up:** `AGENTS.md`, `WORKFLOW.md`, `QUALITY.md`, and `SECURITY.md`.

## D-003 — Defer product architecture until requirements exist

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** No product goals, audience, features, or launch requirements are approved.
- **Decision:** Do not select a product stack, infrastructure, vendors, or architecture until requirements justify them.
- **Rationale:** Deferral avoids speculative complexity, cost, and lock-in.
- **Alternatives:** Choose a default stack immediately; rejected because it encodes unvalidated assumptions.
- **Consequences:** Governance CI contains no fake product build or tests. Product quality commands become mandatory with the first material implementation.
- **Evidence / follow-up:** `PRODUCT.md`, `ARCHITECTURE.md`, and `QUALITY.md`.

## D-004 — Layer procedural controls with plan-compatible automation

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** The repository is private on GitHub Free, where the owner reports that private-repository branch protection/rulesets are unavailable.
- **Decision:** Use strict procedural PR/review/release rules plus GitHub Actions, templates, and durable evidence now. Do not claim protected-branch enforcement. Document the future hard-enforcement settings separately so they can be enabled without redesign.
- **Rationale:** This provides the strongest honest control available without weakening the target governance.
- **Alternatives:** Claim unavailable enforcement or omit controls; both rejected.
- **Consequences:** Direct pushes may remain technically possible. Agents must follow the process, and Release must verify evidence completeness. Hard enforcement remains future work when account capabilities permit.
- **Evidence / follow-up:** `.github/GOVERNANCE_ENFORCEMENT.md`.

## D-005 — Pinned, stack-neutral governance CI baseline

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** Governance needs objective checks before a product toolchain exists.
- **Decision:** Add repository-document validation and Gitleaks secret scanning using third-party Actions pinned to full commit SHAs. Configure weekly GitHub Actions dependency updates. Require product-specific quality and SCA jobs with the first relevant implementation.
- **Rationale:** Real governance and secret checks add value now without inventing product tests.
- **Alternatives:** Empty tests or no automation; rejected.
- **Consequences:** CI coverage intentionally expands after stack selection. Scheduled workflows and Dependabot operate from the default branch only after this configuration is merged.
- **Evidence / follow-up:** `.github/workflows/governance.yml`, `.github/dependabot.yml`, and `scripts/validate_governance.py`.

## D-006 — Merge-commit exact-tree integration protocol

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** Final review applies to a candidate SHA, while GitHub integration creates a different main SHA. Release needs deterministic proof that reviewed content is what reaches pre-production and production.
- **Decision:** Synchronize the candidate to a recorded current `main` base, record candidate/base SHAs and candidate tree, verify that candidate, then require separate Release Authorization to Merge. Integrate with a two-parent merge commit only. Verify its base/candidate parents and exact tree equality, run integration CI and staging on the integrated revision, then require separate Authorization to Deploy.
- **Rationale:** Git commit identity changes at merge, but exact tree and parent verification proves content and ancestry without reviewing merge metadata as product code.
- **Alternatives:** Squash/rebase merging loses direct candidate identity; deploying from the candidate bypasses authoritative `main`; both are rejected for governed material work.
- **Consequences:** A moved base, different tree, non-merge integration, or material candidate change blocks deployment and creates renewed verification work. Current GitHub Free controls report but do not hard-block violations.
- **Evidence / follow-up:** `WORKFLOW.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `scripts/verify_integration.py`, and `.github/GOVERNANCE_ENFORCEMENT.md`.

## D-007 — Structured factory policy and agent-published evidence

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** QA-01 proved that prose substring checks, ancestry-based integration checks, and Lead-transcribed review summaries could remain green while critical controls were weakened.
- **Decision:** Make `.github/governance/policy.json` the canonical machine-readable control source; validate its actual values and relationships with negative mutation tests. Formal gate agents publish schema-valid candidate-specific Gate Records directly to the PR. Release creates an immutable exact-tuple authorization commit under a dedicated Git ref, and integration references it by commit trailer.
- **Rationale:** Structured invariants and negative tests detect semantic weakening. Agent publication preserves evidence provenance. Exact SHA/tree equality prevents related-but-unauthorized revisions from passing.
- **Alternatives:** More prose matching, caller-supplied expected SHAs, or PR-body summaries; rejected because Implementation could redefine or transcribe the claimed authority.
- **Consequences:** Candidate changes stale Gate Records and authorizations. Factory tests and exact authorization verification are mandatory CI. GitHub Free still cannot technically prove Codex-thread identity or prevent a repository writer from imitating the Release ref operation, so role provenance remains an explicit procedural limitation.
- **Evidence / follow-up:** QA-01; `.github/governance/`; `scripts/validate_governance.py`; `scripts/validate_gate_records.py`; `scripts/verify_integration.py`; `tests/`.

## D-008 — Exact evidence refs and content-addressed Gate Records

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** REVIEW-05 showed that namespace membership, shallow nested validation, fabricated supersession, and mutable-only PR comments could undermine the intended factory controls.
- **Decision:** Derive authorization and Gate Record refs exactly from PR/candidate/record identity; require exact ref-to-commit equality. Store each Gate Record in an immutable candidate-parent commit and require PR-visible JSON to match it. Validate the full record recursively, enforce reciprocal acyclic supersession, and preserve every open serious finding until a successor carries durable closure/recheck evidence. Embed exact Review/QA/Security evidence commits in Release authorization.
- **Rationale:** Content addressing detects mutation while graph validation prevents history erasure. Exact refs prevent reuse or substitution of related evidence.
- **Alternatives:** Accept any namespace ref, trust non-null supersession strings, or use mutable comments alone; rejected as fail-open.
- **Consequences:** Evidence publication uses both Git objects and PR comments. The test suite mutates every critical policy contract. GitHub Free still cannot cryptographically identify the originating Codex process or stop an authorized repository writer from imitating a procedural role.
- **Evidence / follow-up:** `GATE-REVIEW-05-20260820`, `.github/governance/`, `scripts/`, and `tests/`.

## D-009 — Append-only evidence with live multi-source reconciliation

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** REVIEW-06 showed that immutable predecessors cannot acquire forward links, stored-object self-comparison does not verify PR-visible evidence, and local refs cannot prove a complete remote ledger.
- **Decision:** Use backward-only successor edges, separate repair claims from distinct-agent rechecks, and derive closure from the complete graph. At Release, query current GitHub comments and independently enumerate/fetch the complete `origin` PR namespace; require one-to-one agreement with immutable objects and refs.
- **Rationale:** This preserves immutable history, prevents repair claims from self-closing findings, and detects observable omission or disagreement between independent sources.
- **Alternatives:** Mutable reciprocal links, selected local refs, or a manifest without an externally protected anchor; rejected. A deletable manifest head adds no deletion proof against the same privileged writer.
- **Consequences:** GitHub API and remote access are Release dependencies. Current consistency is strongly verifiable; process authorship and privileged pre-observation deletion remain procedural limits.
- **Evidence / follow-up:** `GATE-REVIEW-06-20260820`, `scripts/validate_evidence.py`, schemas, policy, workflow, and factory tests.

## D-010 — Bind pre-protocol evidence without rewriting it

- **Date:** 2026-08-20
- **Status:** Accepted
- **Decision:** Explicitly allowlisted schema-v1 evidence may enter the modern ledger only through an immutable, provenance-only Legacy Evidence Binding in a separate migration namespace. Live comments remain mandatory. One normalization layer supplies backward successor lineage while keeping gate lineage separate from finding closure.
- **Rationale:** REVIEW-07 showed that REVIEW-05 predates content-addressed publication and cannot honestly acquire a modern declaration or original ref after the fact.
- **Consequences:** Migration proves content observed at binding time, never prior immutability or approval. Both remote namespaces and live comments must reconcile; modern records cannot claim legacy status.
- **Evidence / follow-up:** `GATE-REVIEW-07-20260820`; REVIEW-08 must independently verify the implementation.
