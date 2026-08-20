# Engineering Workflow

## Operating Roles

- **Lead / Engineering Manager:** plans work, assigns independent roles, tracks risks and gate state, and communicates with the owner. The Lead cannot waive gates or act as Security Review.
- **Product / Requirements:** converts owner intent into bounded scope and testable acceptance criteria.
- **Architecture:** selects maintainable approaches and records consequential decisions.
- **Implementation:** builds on an isolated branch/worktree, adds tests, and identifies the candidate revision.
- **Independent Code Review:** reviews the complete candidate diff for requirements, correctness, maintainability, tests, and risk.
- **QA:** independently tests acceptance criteria, failures, regressions, and applicable browser behavior.
- **UX / Accessibility Review:** independently evaluates user-facing flows, content, responsiveness, keyboard use, focus, semantics, contrast, zoom, and motion.
- **Security Review:** performs the dedicated review required by `SECURITY.md`.
- **Release:** independently confirms the evidence record, authorizes the exact candidate, promotes it, and verifies rollback readiness.
- **Operations / Regression Monitoring:** observes release health, routes alerts, records verification, and initiates rollback or repair.

For material work, Implementation, Independent Code Review, QA, and Release must each be different Codex threads/agents. A triggered Security Review must be separate from Implementation, Lead, QA, and Release. Other roles may combine only when their independence is not required by this governance.

## Material Work Classification

Material work includes, at minimum: application code; configuration; dependencies and lockfiles; database or schema changes; infrastructure; deployment configuration; governance; security behavior; user-facing behavior; APIs; authentication or authorization; data handling; build/test tooling; and release-affecting changes. Ambiguity defaults to material.

Work may be classified non-material only when it cannot affect behavior, risk, verification, release, or governance (for example, a typo-only correction). If that classification bypasses a gate, a non-implementing role must approve it in the durable work record before merge. Classification does not override any non-waivable gate.

## Change Control and Lifecycle

Agents must not routinely commit or push directly to `main`; material work must never do so. Use a feature branch or isolated worktree. A GitHub pull request is the normal durable review record. If GitHub cannot host a PR, use a versioned equivalent record linked from GitHub and explain the limitation.

Product request → acceptance criteria → isolated implementation → independent code review → repairs → automated testing → QA/browser verification where applicable → Security Review where applicable → staging verification → Release authorization → release → post-release monitoring.

The PR record must identify one exact candidate commit SHA. Independent review and checks apply to that SHA. Every repair or other material change creates a new candidate revision and invalidates affected approvals and evidence. Each affected review, automated test, QA/browser/accessibility check, Security Review, and staging result must be rerun; alternatively, an independent owner of that gate may record why it is unaffected. Release rejects missing, stale, or self-attested evidence.

Only Release may authorize a fully verified candidate for release. Approval is not permission to merge or deploy a different revision. `main` changes require a PR or equivalent durable review record before becoming authoritative.

## Shared Finding Severity

- **BLOCKING:** immediate safety, security, data, correctness, compliance, or release-integrity risk; repair is mandatory before approval or release.
- **MAJOR:** material requirement, reliability, maintainability, accessibility, or control failure; repair is mandatory before approval or release.
- **MINOR:** bounded issue that does not block safe use; repair it or record tracked debt with an accountable owner and target date.
- **SUGGESTION:** optional improvement; record its disposition when raised in a formal review.

BLOCKING and MAJOR repairs must be independently rechecked by the role that raised them or an equally independent qualified role. Security-relevant repairs must be rechecked by Security Review.

## Exceptions and Non-Waivable Gates

The following cannot be waived: separation of Implementation and Independent Code Review; triggered Security Review and its independence; secret protection; disposition and independent recheck of BLOCKING/MAJOR findings; exact-candidate verification; Release authorization; and integrity of required evidence.

Any other temporary exception requires a written justification, risk and compensating controls, independent concurrence, relevant specialist concurrence, Release concurrence, expiry date, and durable PR record. The Lead alone cannot waive a gate. Owner approval is additionally required when an exception crosses the decision boundaries in `PRODUCT.md`.

## Staging and Pre-Release Verification

Staging or the pre-release environment must use the exact candidate artifact and materially match production runtime, configuration shape, integrations or faithful test doubles, data/schema version, access boundaries, observability, and deployment path. Differences and their risk must be recorded.

For authentication, authorization, billing/payments, personal data, migrations, infrastructure, or other security-sensitive behavior, a developer machine or simple local substitute does not count as staging. Release must block until a representative isolated environment verifies the relevant boundaries and recovery behavior.

Minimum smoke checks are: deployed revision identity; startup and health; critical route or workflow; configuration and secret injection without disclosure; persistence/migration compatibility where applicable; external-boundary behavior; error and recovery path; authorization boundary where applicable; logging/metrics/alerts; and rollback or roll-forward execution evidence.

## Release, Rollback, and Monitoring

Release readiness is demonstrable, not a statement of intent. Where applicable, the PR record must contain a revision-specific rollback or roll-forward procedure; migration and backward-compatibility assessment; backup/restore compatibility; named health signals and thresholds; observation window; alert route and accountable Operations role; rollback triggers; and post-release verification result.

Failed gates return work to the appropriate role. Agents resolve technical failures themselves and ask the owner only when a decision crosses `PRODUCT.md` boundaries. Incidents follow `INCIDENT_RESPONSE.md`.
