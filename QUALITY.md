# Quality Gates

## Evidence and Candidate Identity

A claim is not verification. Evidence must identify the exact candidate SHA, command or procedure, result, environment, and relevant artifact or observation. Store the durable summary in the GitHub PR using `.github/PULL_REQUEST_TEMPLATE.md`; chat may assist but is not the record.

Every repair or other material change creates a new candidate. Affected automated tests, review, QA, browser, accessibility, security, and staging evidence must be rerun or explicitly marked unaffected by an independent owner of that gate. Release rejects stale evidence.

## Automated Quality Baseline

Before the first material product implementation can be complete, the project must expose documented canonical commands and run applicable commands in CI for:

- formatting and linting;
- static analysis and type checking;
- unit and integration tests;
- a production build;
- end-to-end or real-browser tests;
- automated accessibility scanning;
- secret scanning;
- dependency/software-composition and vulnerability scanning.

Add the commands to this file and `README.md` when the product toolchain is chosen. Do not create fake commands or empty tests. A genuinely inapplicable gate requires a written N/A rationale and approval by a non-implementing role in the PR record. The initial workflow, `.github/workflows/governance.yml`, currently validates repository governance and runs secret scanning; it does not claim to test a product that does not exist.

## Required Gates for Material Changes

1. Acceptance criteria are complete and traceable to checks.
2. All configured format, lint, static/type, test, build, browser, accessibility, secret, and dependency/security checks pass or have an approved N/A disposition.
3. Independent Code Review covers the complete candidate diff.
4. QA verifies acceptance criteria, edge cases, failures, and relevant regressions.
5. UX / Accessibility and Security gates pass when triggered.
6. The exact candidate passes representative pre-release verification.
7. Release validates evidence completeness and rollback/monitoring readiness.

Any failing applicable gate blocks completion. Flaky checks are failures until fixed. Non-waivable gates and exception requirements are defined in `WORKFLOW.md`.

## User-Facing and Accessibility Gate

Every visual or user-flow change requires UX / Accessibility Review, browser verification at representative viewport sizes, keyboard-only operation, visible focus, semantic structure and labels, contrast, zoom/reflow and responsiveness, reduced-motion behavior where relevant, and an appropriate automated accessibility scan. Exercise happy, loading, empty, validation, error, and recovery states as applicable.

N/A is allowed only when the change has no visual or user-flow effect. The PR must record the reasoning and a non-implementer must concur. Meaningful visual changes include screenshots or recordings linked in the PR.

## Test Design

Tests must be deterministic, isolated, readable, and focused on observable behavior. Mock only external boundaries; prefer realistic integration coverage for critical flows. Bug fixes add regression coverage when practical. Never use production secrets or personal data in fixtures. Coverage percentages inform risk but do not replace meaningful assertions.

## Review Disposition

Use the shared BLOCKING / MAJOR / MINOR / SUGGESTION taxonomy in `WORKFLOW.md`. BLOCKING and MAJOR findings require repair and independent recheck. MINOR findings require repair or tracked debt with owner and target date. Formal-review SUGGESTION dispositions are recorded.
