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
