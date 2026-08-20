# Engineering Workflow

## Operating Roles

- **Lead / Engineering Manager:** owns planning, assignments, risk, gate status, and owner communication.
- **Product / Requirements:** converts owner intent into bounded scope and testable acceptance criteria in `PRODUCT.md` or a work item.
- **Architecture:** chooses maintainable technical approaches and records consequential decisions.
- **Implementation:** builds in an isolated branch/worktree, adds tests, and supplies verification notes.
- **Independent Code Review:** a separate Codex thread/agent examines correctness, maintainability, tests, security, and requirement fit. It does not approve its own implementation.
- **QA:** verifies acceptance criteria, regressions, and failure states using objective evidence.
- **UX / Accessibility Review:** checks user-facing flows, responsive behavior, content clarity, keyboard use, focus, semantics, and contrast.
- **Security Review:** evaluates threat boundaries and sensitive changes under `SECURITY.md`.
- **Release:** confirms gates, promotes the exact reviewed revision, documents the release, and preserves rollback capability.
- **Operations / Regression Monitoring:** watches health after release, triages regressions, and initiates rollback or repair.

For material work, Implementation, Independent Code Review, QA, and Release must each be assigned to different Codex threads/agents. This prevents the builder from approving, testing, or releasing its own work and keeps release authorization independent from prior gates. Other compatible roles may be combined only when independence is preserved; any triggered Security Review must also remain separate from Implementation. The Lead records who performed each gate and links its evidence.

## Standard Lifecycle

Product request → acceptance criteria → implementation in isolated work → independent code review → repairs if necessary → automated testing → QA/browser verification where applicable → security review where applicable → staging verification → release → post-release monitoring.

## Gate Rules

1. Product / Requirements defines observable acceptance criteria before material implementation.
2. Architecture records consequential choices before they become expensive to reverse.
3. Implementation remains isolated and never commits secrets.
4. Independent Code Review reports findings by severity. Implementation repairs them; the reviewer rechecks material repairs.
5. QA applies `QUALITY.md`. User-facing work includes real browser evidence and accessibility consideration.
6. Security Review is mandatory for triggers in `SECURITY.md`; unresolved high-risk findings block release.
7. Release verifies the exact candidate revision in staging when a staging environment exists. If it does not, Release documents the missing capability and uses the closest reproducible pre-release environment; public release still requires owner authorization.
8. Operations checks defined health signals after release and records incidents, rollback, and follow-up.

Failed gates return work to the appropriate earlier role. Agents resolve technical failures themselves and ask the owner only when the decision crosses the boundaries in `PRODUCT.md`.

## Required Handoff Record

Each material change records scope and acceptance criteria, branch and revision, implementer, independent reviewer, findings and repairs, commands/checks with results, browser or accessibility evidence, security disposition, staging result, release decision, rollback plan, and post-release observations. Evidence must identify the exact revision tested.
