# Quality Gates

Critical controls are defined by `.github/governance/policy.json`; prose cannot override that canonical policy.

## Evidence and Candidate Identity

A claim is not verification. Evidence must identify the recorded base SHA, exact candidate SHA and tree hash, command or procedure, result, environment, and relevant artifact or observation. After integration it must also identify the main integration SHA/tree, parent/base verification, and candidate/integration tree equality. Store the durable summary in the GitHub PR using `.github/PULL_REQUEST_TEMPLATE.md`; chat may assist but is not the record.

Every repair creates a new candidate. The implementer publishes an append-only repair claim; it never closes a finding. A distinct qualified agent publishes the recheck. Formal proof is matching live PR JSON and an immutable Gate Record object; Release validates both plus the complete remote ledger using `scripts/validate_evidence.py`. Stale, missing, selected-subset, or disagreeing evidence fails.

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

Add the commands to this file and `README.md` when the product toolchain is chosen. Do not create fake commands or empty tests. A genuinely inapplicable gate requires a written N/A rationale and approval by a non-implementing role in the PR record. The initial workflow, `.github/workflows/governance.yml`, validates repository governance, runs secret scanning, and runs deterministic factory self-tests under `tests/`; it does not claim to test a product that does not exist. Factory tests cover structured-policy mutations, Gate Record integrity/supersession/staleness, and exact-ref authorized integration positive and negative cases.

Factory learning rule: every technically testable defect found by Review, QA, Security, or Release normally receives a permanent security-property regression test before repair is complete.

## Required Gates for Material Changes

1. Acceptance criteria are complete and traceable to checks.
2. All configured format, lint, static/type, test, build, browser, accessibility, secret, and dependency/security checks pass or have an approved N/A disposition.
3. Independent Code Review covers the complete candidate diff.
4. QA verifies acceptance criteria, edge cases, failures, and relevant regressions. Implementation, Independent Code Review, QA, and Release are four different threads/agents.
5. UX / Accessibility and Security gates pass when triggered.
6. Release validates candidate/base/tree identity and issues Authorization to Merge; deterministic merge-commit integration then passes integration tree/parent checks and CI.
7. The integrated revision passes applicable staging checks. High-risk work passes representative non-local isolated pre-production verification.
8. Release validates evidence completeness and rollback/monitoring readiness and separately issues Authorization to Deploy for the exact integration revision.

Any failing applicable gate blocks completion. Flaky checks are failures until fixed. The canonical non-waivable list in `WORKFLOW.md` applies in full: no exception can combine Implementation, Independent Code Review, QA, or Release; relax triggered Security independence/recheck; bypass high-risk non-local pre-production verification; or bypass the other listed integrity and authorization controls.

## Integration Evidence

Final candidate evidence is valid only for the recorded candidate SHA/tree against the recorded current `main` base. Governed material changes use merge-commit-only integration under `WORKFLOW.md`. After merge, CI verifies the integration commit, its parents, and exact tree equality with the candidate. If the base moved, identities differ, or evidence became stale, deployment is blocked until a new candidate and affected verification are complete. Release records separate Authorization to Merge and Authorization to Deploy decisions.

## User-Facing and Accessibility Gate

Every visual or user-flow change requires UX / Accessibility Review, browser verification at representative viewport sizes, keyboard-only operation, visible focus, semantic structure and labels, contrast, zoom/reflow and responsiveness, reduced-motion behavior where relevant, and an appropriate automated accessibility scan. Exercise happy, loading, empty, validation, error, and recovery states as applicable.

N/A is allowed only when the change has no visual or user-flow effect. The PR must record the reasoning and a non-implementer must concur. Meaningful visual changes include screenshots or recordings linked in the PR.

## Test Design

Tests must be deterministic, isolated, readable, and focused on observable behavior. Mock only external boundaries; prefer realistic integration coverage for critical flows. Bug fixes add regression coverage when practical. Never use production secrets or personal data in fixtures. Coverage percentages inform risk but do not replace meaningful assertions.

## Review Disposition

Use the shared BLOCKING / MAJOR / MINOR / SUGGESTION taxonomy in `WORKFLOW.md`. BLOCKING and MAJOR findings require repair and independent recheck. MINOR findings require repair or tracked debt with owner and target date. Formal-review SUGGESTION dispositions are recorded.

For allowlisted legacy evidence, validation enumerates the remote migration namespace and reconciles the live historical comment, immutable snapshot, hashes, and normalized mixed-version graph. Ledger integrity and release-gate satisfaction are separate results.
