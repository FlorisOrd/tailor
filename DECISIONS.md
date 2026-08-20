# Decision Log

Use this file for decisions that materially shape architecture, delivery, security, operations, cost, or future reversibility. Append new records; do not erase prior decisions. A later record may supersede an earlier one.

## Record Template

### D-XXX — Title

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded | Rejected
- **Context:** What requires a durable choice?
- **Decision:** What was chosen?
- **Rationale:** Why is this the best fit?
- **Alternatives:** What credible options were considered?
- **Consequences:** What benefits, costs, risks, and follow-up result?
- **Evidence / follow-up:** Links to work items, revisions, tests, or review records.

## D-001 — GitHub is the permanent source of truth

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** Work needs a durable, auditable collaboration record.
- **Decision:** GitHub history and reviewed branches are authoritative. Agents use isolated work and preserve traceability to the exact revision verified and released.
- **Rationale:** A single remote source reduces divergence and supports review, recovery, and auditability.
- **Alternatives:** Untracked local work or multiple authoritative copies; rejected because they weaken traceability.
- **Consequences:** Work is not safely shared until pushed. Releases must identify a Git revision.
- **Evidence / follow-up:** Repository governance bootstrap on `bootstrap/agent-company`.

## D-002 — Independent, evidence-based delivery gates

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** The product owner delegates technical execution and will not inspect or maintain code.
- **Decision:** Material implementation requires review by a separate Codex agent plus applicable automated, QA, browser, accessibility, security, staging, and monitoring evidence before completion.
- **Rationale:** Separation of duties and observable evidence reduce blind spots and make technical claims verifiable.
- **Alternatives:** Self-review alone or informal claims; rejected because neither provides sufficient assurance.
- **Consequences:** Lead agents must schedule independent review and cannot bypass failed gates. Lightweight documentation-only changes may use proportionate checks but still require independent review when material.
- **Evidence / follow-up:** `AGENTS.md`, `WORKFLOW.md`, `QUALITY.md`, and `SECURITY.md`.

## D-003 — Defer product architecture until requirements exist

- **Date:** 2026-08-20
- **Status:** Accepted
- **Context:** No product goals, audience, features, or launch requirements have been approved.
- **Decision:** Do not select a product stack, infrastructure, vendors, or architecture until requirements justify them.
- **Rationale:** Deferral avoids speculative complexity, cost, and lock-in.
- **Alternatives:** Choose a default stack immediately; rejected because it would encode unvalidated assumptions.
- **Consequences:** `ARCHITECTURE.md` defines principles only. A future decision record will select the stack after product clarification.
- **Evidence / follow-up:** `PRODUCT.md` and `ARCHITECTURE.md`.
