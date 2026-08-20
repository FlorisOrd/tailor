# Quality Gates

## Evidence Standard

A claim is not verification. Gate results must include the exact revision, command or procedure, result, and relevant artifact (for example logs, screenshots, reports, or browser observations). Use reproducible checks and keep CI aligned with documented local commands.

## Required Gates for Material Changes

1. **Scope:** acceptance criteria are complete and traceable to checks.
2. **Static checks:** formatting, linting, type checking, and dependency validation pass when configured.
3. **Automated tests:** affected unit, integration, and end-to-end suites pass. Bug fixes add regression coverage when practical.
4. **Build:** a clean production-equivalent build succeeds when the project is buildable.
5. **Independent review:** a separate Codex agent has reviewed the complete diff; blocking findings are repaired and rechecked.
6. **QA:** acceptance criteria, edge cases, error handling, and relevant regressions are verified.
7. **Specialist gates:** UX / Accessibility and Security reviews pass when triggered.
8. **Staging and release:** the exact candidate revision is verified in staging or the documented closest equivalent, with rollback readiness.

Any failing required gate blocks completion. Flaky checks are failures until their cause is fixed or a time-bounded exception is documented with owner-visible risk.

## User-Facing Changes

Verify supported browsers at realistic viewport sizes. Exercise happy, loading, empty, error, validation, and recovery states as applicable. Check keyboard navigation, visible focus, semantic structure, labels, alternative text, contrast, zoom/reflow, and reduced motion. Capture screenshots or equivalent evidence for meaningful visual changes.

## Test Design

Tests should be deterministic, isolated, readable, and focused on observable behavior. Mock only external boundaries; prefer realistic integration coverage for critical flows. Never use production secrets or personal data in fixtures.

Coverage percentages inform risk but do not replace meaningful assertions. Once a toolchain exists, document canonical `test`, `lint`, `build`, and browser-test commands here and enforce them in CI.

## Exceptions

The Lead may document a temporary technical exception only when risk, owner impact, compensating controls, responsible agent, and expiry are explicit. Exceptions involving product behavior, privacy, legal/compliance, spending, or public risk require owner approval.
